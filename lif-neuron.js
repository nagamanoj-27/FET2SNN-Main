// lif-neuron.js
// Leaky Integrate-and-Fire (LIF) Neuron Module for FET2SNN

let lifChart = null;
let lifRafId = null;
let lifState = {
    V: 0,
    time: 0,
    spikes: [],
    lastSpikeTime: -999,
    isRunning: false,
    history: [], // {t, V}
};

let lifParams = {
    Cm: 10,       // fF
    Gleak: 100,   // nS
    Vth: 300,     // mV
    Vreset: 100,  // mV
    Vrest: 0,     // mV
    tauM: 0.1,    // ms
    tRefractory: 2 // ms
};

let userControls = {
    I_amp: 2,       // nA
    I_dur: 100,     // ms
    noise: 0,       // nA
    t_window: 200   // ms
};

function deriveLIFparams(d, S) {
    try {
        // Cm proportional to gate capacitance (approx from Cox and area)
        // Cox is in fF/µm^2. Area approx Lg * Weff in µm^2.
        const Lg_um = S.Lg / 1000;
        const Weff_um = (S.Wns * 2 + S.Tns * 2) * S.Nstacks / 1000;
        const gateCap = d.Cox * Lg_um * Weff_um; // fF
        let Cm = Math.max(1, gateCap * 100); // Scale up for biophysical realism (e.g. 5-20 fF)
        
        // Gleak inversely related to SS (lower SS -> lower leak -> higher resistance)
        let Gleak = Math.max(1, (d.SS / 60) * 50); // nS
        
        let Vth = d.Vth * 1000; // mV
        let Vreset = S.Vdd * 300; // mV
        let tauM = Cm / Gleak; // ms (fF / nS = ms)
        let tRefractory = 2 + 5 * Math.exp(-S.Lg / 10);
        
        if (isNaN(tauM) || tauM <= 0) tauM = 0.1;
        
        return { Cm, Gleak, Vth, Vreset, Vrest: 0, tauM, tRefractory };
    } catch(e) {
        console.warn("LIF derivation failed, using safe defaults", e);
        return { Cm: 10, Gleak: 100, Vth: 300, Vreset: 100, Vrest: 0, tauM: 0.1, tRefractory: 2 };
    }
}

function updateLIFUI() {
    document.getElementById('lif-cm').innerText = lifParams.Cm.toFixed(2);
    document.getElementById('lif-gleak').innerText = lifParams.Gleak.toFixed(2);
    document.getElementById('lif-taum').innerText = lifParams.tauM.toFixed(3);
    document.getElementById('lif-tref').innerText = lifParams.tRefractory.toFixed(2);
    document.getElementById('lif-vth').innerText = lifParams.Vth.toFixed(0);
}

// Global Hook to receive updates
window.updateLIFModule = function(d, S) {
    lifParams = deriveLIFparams(d, S);
    updateLIFUI();
    
    // Auto-update f-I estimates based on new params
    // (We could auto-reset simulation, but let's just let it run smoothly with new parameters)
};

function initLIFChart() {
    const ctx = document.getElementById('chLif').getContext('2d');
    lifChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Membrane Potential (mV)',
                data: [],
                borderColor: '#7c3aed',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.1,
                fill: false,
                showLine: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: {
                    title: { display: true, text: 'Time (ms)', color: '#aaa', font: { family: 'Inter', size: 10 } },
                    grid: { color: '#333' },
                    ticks: { color: '#aaa' },
                    min: 0,
                    max: userControls.t_window
                },
                y: {
                    title: { display: true, text: 'Voltage (mV)', color: '#aaa', font: { family: 'Inter', size: 10 } },
                    grid: { color: '#333' },
                    ticks: { color: '#aaa' },
                    suggestedMin: -50,
                    suggestedMax: 600
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// User controls
function hookLIFControls() {
    const ids = ['lif-Iamp', 'lif-Idur', 'lif-noise', 'lif-twin'];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if(el) {
            el.addEventListener('input', (e) => {
                const val = parseFloat(e.target.value);
                document.getElementById(id + '-val').innerText = val.toFixed(id==='lif-noise'?2:0);
                if (id === 'lif-Iamp') userControls.I_amp = val;
                if (id === 'lif-Idur') userControls.I_dur = val;
                if (id === 'lif-noise') userControls.noise = val;
                if (id === 'lif-twin') {
                    userControls.t_window = val;
                    if (lifChart) {
                        lifChart.options.scales.x.max = val;
                        lifChart.update();
                    }
                }
            });
        }
    });

    document.getElementById('lif-btn-run').addEventListener('click', () => {
        lifState.isRunning = true;
        if (!lifRafId) lifRafId = requestAnimationFrame(lifLoop);
    });
    document.getElementById('lif-btn-pause').addEventListener('click', () => {
        lifState.isRunning = false;
        if (lifRafId) { cancelAnimationFrame(lifRafId); lifRafId = null; }
    });
    document.getElementById('lif-btn-reset').addEventListener('click', () => {
        resetLIF();
    });
    
    
    // Export PNG
    const btnPng = document.getElementById('lif-btn-png');
    if(btnPng) {
        btnPng.addEventListener('click', () => {
            const canvas = document.getElementById('chLif');
            if(!canvas) return;
            // Create a temporary canvas with a solid background to avoid transparency issues
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = canvas.width;
            tempCanvas.height = canvas.height;
            const tCtx = tempCanvas.getContext('2d');
            tCtx.fillStyle = '#1e1e2f'; // Dashboard bg color
            tCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
            tCtx.drawImage(canvas, 0, 0);
            
            const link = document.createElement('a');
            link.download = 'LIF_Membrane_Potential.png';
            link.href = tempCanvas.toDataURL('image/png');
            link.click();
        });
    }

    // Export CSV
    document.getElementById('lif-btn-csv').addEventListener('click', () => {
        if(lifState.history.length === 0) return alert("No data to export!");
        let csv = "Time(ms),Voltage(mV)\\n";
        lifState.history.forEach(pt => csv += `${pt.x.toFixed(2)},${pt.y.toFixed(2)}\\n`);
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'LIF_Trace.csv';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
    });
}

function resetLIF() {
    lifState.isRunning = false;
    if (lifRafId) { cancelAnimationFrame(lifRafId); lifRafId = null; }
    lifState.V = lifParams.Vrest;
    lifState.time = 0;
    lifState.spikes = [];
    lifState.lastSpikeTime = -999;
    lifState.history = [];
    if (lifChart) {
        lifChart.data.datasets[0].data = [];
        lifChart.options.scales.x.min = 0;
        lifChart.options.scales.x.max = userControls.t_window;
        lifChart.update();
    }
    updateLIFReadouts();
}

let lastTimestamp = 0;
function lifLoop(timestamp) {
    if (!lifState.isRunning) return;
    
    if (!lastTimestamp) lastTimestamp = timestamp;
    let dt_wall = (timestamp - lastTimestamp); // ms
    lastTimestamp = timestamp;
    
    // Cap dt to prevent massive jumps if tab is inactive
    if (dt_wall > 50) dt_wall = 16;
    
    // Simulation steps (sub-sampling for stability)
    const simSteps = 5;
    const dt = dt_wall / simSteps;
    
    for (let i = 0; i < simSteps; i++) {
        stepLIF(dt);
    }
    
    updateLIFChart();
    updateLIFReadouts();
    
    lifRafId = requestAnimationFrame(lifLoop);
}

function stepLIF(dt) {
    lifState.time += dt;
    
    // Check refractory
    if (lifState.time - lifState.lastSpikeTime < lifParams.tRefractory) {
        lifState.V = lifParams.Vreset;
    } else {
        // Calculate Input Current
        let I_in = 0;
        if (lifState.time < userControls.I_dur || lifState.time % (userControls.I_dur*2) < userControls.I_dur) {
             // Pulsed input for demonstration, or continuous if duration is high
             I_in = userControls.I_amp; 
        }
        
        // Add noise
        if (userControls.noise > 0) {
            I_in += (Math.random() * 2 - 1) * userControls.noise;
        }
        
        // LIF ODE: tau_m * dV/dt = -(V - Vrest) + I_in * R_m
        // Rm = 1 / Gleak
        // dV = (-(V - Vrest) + I_in * (1/Gleak)) * (dt / tau_m)
        // Unit check: I_in (nA), Gleak (nS) -> nA / nS = V (1000 mV).
        // Let's explicitly compute: I_in * (1000 / Gleak) -> mV
        
        const Rm_mV_per_nA = 1000 / lifParams.Gleak; 
        let dV = ( -(lifState.V - lifParams.Vrest) + I_in * Rm_mV_per_nA ) * (dt / lifParams.tauM);
        
        lifState.V += dV;
        
        // Spike condition
        if (lifState.V >= lifParams.Vth) {
            lifState.spikes.push(lifState.time);
            lifState.lastSpikeTime = lifState.time;
            
            // Add a visual spike peak to history
            lifState.history.push({x: lifState.time, y: lifParams.Vth + 150});
            lifState.V = lifParams.Vreset;
        }
    }
    
    // Record history
    lifState.history.push({x: lifState.time, y: lifState.V});
}

function updateLIFChart() {
    if (!lifChart) return;
    
    // Keep window sliding
    const windowStart = Math.max(0, lifState.time - userControls.t_window);
    const windowEnd = Math.max(userControls.t_window, lifState.time);
    
    // Prune old history for performance
    if (lifState.history.length > 5000) {
        const cutoff = lifState.time - userControls.t_window - 50;
        lifState.history = lifState.history.filter(pt => pt.x > cutoff);
    }
    
    lifChart.data.datasets[0].data = lifState.history;
    lifChart.options.scales.x.min = windowStart;
    lifChart.options.scales.x.max = windowEnd;
    lifChart.update();
}

function updateLIFReadouts() {
    // Instantaneous firing rate (Hz) over last 100ms
    const recentSpikes = lifState.spikes.filter(t => t > lifState.time - 100);
    const rateHz = recentSpikes.length * 10; // (spikes / 100ms) * 10 = spikes / sec
    
    document.getElementById('lif-rate').innerText = rateHz.toFixed(1);
    
    // Energy per spike = C_m * (Vth - Vreset)^2 
    // Cm in fF (1e-15 F). V in mV (1e-3 V). 
    // E = fF * (mV)^2 = 1e-15 * 1e-6 = 1e-21 J = 1e-9 pJ = 1e-6 fJ.
    const vDiff = (lifParams.Vth - lifParams.Vreset);
    const e_spike_fJ = lifParams.Cm * Math.pow(vDiff, 2) * 1e-6; 
    
    document.getElementById('lif-espike').innerText = e_spike_fJ.toFixed(2);
}

document.addEventListener('DOMContentLoaded', () => {
    // We will initialize when HTML is injected
});

// Explicit Init for the HTML injection script
window.startLIFSystem = function() {
    initLIFChart();
    hookLIFControls();
    // Default params call
    if (typeof S !== 'undefined' && typeof computeDevice === 'function') {
        window.updateLIFModule(computeDevice(S), S);
    }
    resetLIF();
};
