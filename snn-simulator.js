// snn-simulator.js
// Multi-neuron SNN Simulator with STDP and Manual Weight Modes

let snnSimState = {
    N: 10,
    time: 0,
    dt: 0.5,
    speed: 1,
    isRunning: false,
    mode: 'manual', // 'manual' or 'stdp'
    t_window: 200,
    
    // TypedArrays for performance
    V: null,
    ref: null,
    lastSpike: null,
    W: null, // N x N Float64Array
    I_ext: null, // external input current per neuron
    
    // History
    raster: [], // array of {t, n}
    trace: [], // {t, V} for selected neuron
    selectedNeuron: 0,
    plasticityEvents: 0,
    
    // Derived LIF Parameters
    P: { Cm: 10, Gleak: 100, Vth: 300, Vreset: 100, Vrest: 0, tauM: 0.1, tRef: 2 },
    
    // STDP Parameters
    STDP: { Ap: 0.01, Am: 0.012, tauP: 20, tauM: 20, wMin: 0, wMax: 10, excOnly: false },
    
    // Energy Breakdown Parameters
    energyParams: { e_syn_coeff: 0.1, e_spike_overhead: 0.05, timeWindow: 200 },
    energyBuffer: [],
    
    // Delays
    delayMode: 'none',
    delayParams: { c: 1.0, min: 0.5, max: 2.5, k: 0.05 },
    D: null,
    eventRing: null, // array of length 1000
    
    heatmapView: 'weights',
    rafId: null,
    lastTs: 0,
    lastEnergyUpdate: 0
};

let snnEnergyChart = null;

let snnTraceChart = null;

function initSNNArrays() {
    const N = snnSimState.N;
    snnSimState.V = new Float64Array(N);
    snnSimState.ref = new Float64Array(N);
    snnSimState.lastSpike = new Float64Array(N).fill(-9999);
    snnSimState.W = new Float64Array(N * N);
    snnSimState.D = new Float64Array(N * N);
    snnSimState.I_ext = new Float64Array(N);
    
    // Initialize external input: first half gets 2 nA
    for(let i=0; i<N; i++) {
        snnSimState.V[i] = snnSimState.P.Vrest;
        snnSimState.I_ext[i] = (i < N/2) ? 2.0 : 0.0; 
    }
    
    snnSimState.eventRing = new Array(1000).fill(0).map(() => []);
}

function initDelays() {
    if(!snnSimState.D) return;
    const N = snnSimState.N;
    snnSimState.D.fill(0);
    if(snnSimState.delayMode === 'none') {
        renderHeatmap();
        return;
    }
    
    for(let i=0; i<N; i++) {
        for(let j=0; j<N; j++) {
            if(i === j) continue;
            let val = 0;
            if(snnSimState.delayMode === 'constant') {
                val = snnSimState.delayParams.c;
            } else if(snnSimState.delayMode === 'uniform') {
                val = snnSimState.delayParams.min + Math.random()*(snnSimState.delayParams.max - snnSimState.delayParams.min);
            } else if(snnSimState.delayMode === 'fet') {
                let Lg = 12; // default
                const nLg = document.getElementById('nLg');
                if(nLg) Lg = parseFloat(nLg.value);
                val = Lg * snnSimState.delayParams.k;
            }
            snnSimState.D[i*N + j] = Math.max(0, val);
        }
    }
    renderHeatmap();
}

function initWeights(method, minW, maxW, sparsity) {
    const N = snnSimState.N;
    snnSimState.W.fill(0);
    for(let i=0; i<N; i++) {
        for(let j=0; j<N; j++) {
            if(i === j) continue; // no self-connections
            if(Math.random() > sparsity/100) continue;
            
            if(method === 'constant') {
                snnSimState.W[i*N + j] = maxW;
            } else if(method === 'uniform') {
                snnSimState.W[i*N + j] = minW + Math.random()*(maxW - minW);
            }
        }
    }
    renderHeatmap();
}

function resetSNNSim() {
    snnSimState.isRunning = false;
    if(snnSimState.rafId) { cancelAnimationFrame(snnSimState.rafId); snnSimState.rafId = null; }
    const N = snnSimState.N;
    snnSimState.time = 0;
    snnSimState.raster = [];
    snnSimState.trace = [];
    snnSimState.plasticityEvents = 0;
    snnSimState.energyBuffer = [];
    if(snnSimState.eventRing) {
        for(let i=0; i<1000; i++) snnSimState.eventRing[i].length = 0;
    }
    if(snnEnergyChart) {
        snnEnergyChart.data.datasets[0].data = [0,0,0,0];
        snnEnergyChart.update();
        document.getElementById('snn-energy-total').innerText = '0.00 pJ';
    }
    if(snnSimState.V) snnSimState.V.fill(snnSimState.P.Vrest);
    if(snnSimState.ref) snnSimState.ref.fill(0);
    if(snnSimState.lastSpike) snnSimState.lastSpike.fill(-9999);
    
    if(snnTraceChart) {
        snnTraceChart.data.datasets[0].data = [];
        snnTraceChart.update();
    }
    updateSNNUI();
    renderRaster();
}

window.updateSNNSimulator = function(d, S) {
    // Re-derive parameters from global device state
    if(typeof deriveLIFparams === 'function') {
        snnSimState.P = deriveLIFparams(d, S);
    }
    // Pause and alert reset needed
    snnSimState.isRunning = false;
    if(snnSimState.rafId) cancelAnimationFrame(snnSimState.rafId);
    snnSimState.rafId = null;
    document.getElementById('snn-btn-run').innerHTML = '<i class="fas fa-play"></i> Run';
    
    if(snnSimState.delayMode === 'fet') initDelays();
    // Auto reset for friendliness
    resetSNNSim();
};

function stepSNNSim(dt) {
    const N = snnSimState.N;
    const P = snnSimState.P;
    const W = snnSimState.W;
    const V = snnSimState.V;
    const ls = snnSimState.lastSpike;
    const t = snnSimState.time;
    
    let currentSpikes = []; // indices of neurons that spike this step
    
    const Rm_mV_per_nA = 1000 / P.Gleak; 
    
    // Process Delayed Synaptic Events arriving at this step
    let syn_events_count = 0;
    if(snnSimState.delayMode !== 'none') {
        let bucketIdx = Math.floor(t / dt) % 1000;
        let bucket = snnSimState.eventRing[bucketIdx];
        for(let q=0; q<bucket.length; q++) {
            let ev = bucket[q];
            // dynamic weight lookup for STDP
            let w = W[ev.i*N + ev.j]; 
            if(w !== 0) {
                V[ev.j] += w * Rm_mV_per_nA * 0.1;
                syn_events_count++;
            }
        }
        // clear bucket
        bucket.length = 0;
    }

    for(let i=0; i<N; i++) {
        if(t - ls[i] < P.tRef) {
            V[i] = P.Vreset;
            continue;
        }
        
        let I_syn = 0;
        let I_tot = snnSimState.I_ext[i] + I_syn;
        
        let dV = ( -(V[i] - P.Vrest) + I_tot * Rm_mV_per_nA ) * (dt / P.tauM);
        V[i] += dV;
        
        if(V[i] >= P.Vth) {
            currentSpikes.push(i);
            V[i] = P.Vreset;
            ls[i] = t;
            snnSimState.raster.push({t: t, n: i});
        }
    }
    
    // Synaptic transmission & STDP
    for(let k=0; k<currentSpikes.length; k++) {
        let i = currentSpikes[k]; // pre-synaptic neuron that just fired
        
        // Deliver synaptic current/voltage jump to post-synaptic neurons
        for(let j=0; j<N; j++) {
            if(i === j) continue;
            let w = W[i*N + j];
            if(w !== 0) {
                if(snnSimState.delayMode === 'none') {
                    // Instant delivery
                    V[j] += w * Rm_mV_per_nA * 0.1;
                    syn_events_count++;
                } else {
                    // Queue delivery
                    let delay = snnSimState.D[i*N + j];
                    let t_arrive = t + delay;
                    let bIdx = Math.floor(t_arrive / dt) % 1000;
                    snnSimState.eventRing[bIdx].push({i: i, j: j});
                }
            }
            
            // STDP: pre-synaptic fires (t_pre = t). Check post-synaptic history (instant logic)
            if(snnSimState.mode === 'stdp' && w !== 0) {
                let dt_spike = ls[j] - t; // t_post - t_pre. Since t_post is past, dt_spike < 0
                if(dt_spike > -50 && dt_spike < 0) {
                    let dw = -snnSimState.STDP.Am * Math.exp(dt_spike / snnSimState.STDP.tauM);
                    W[i*N + j] = Math.max(snnSimState.STDP.wMin, Math.min(snnSimState.STDP.wMax, w + dw));
                    snnSimState.plasticityEvents++;
                }
            }
        }
        
        // STDP: post-synaptic fires (t_post = t). i is post here.
        if(snnSimState.mode === 'stdp') {
            let j = i; // j is post-synaptic
            for(let pre=0; pre<N; pre++) {
                if(pre === j) continue;
                let w = W[pre*N + j];
                if(w !== 0) {
                    let dt_spike = t - ls[pre]; // t_post - t_pre. dt_spike > 0
                    if(dt_spike > 0 && dt_spike < 50) {
                        // Potentiation
                        let dw = snnSimState.STDP.Ap * Math.exp(-dt_spike / snnSimState.STDP.tauP);
                        W[pre*N + j] = Math.max(snnSimState.STDP.wMin, Math.min(snnSimState.STDP.wMax, w + dw));
                        snnSimState.plasticityEvents++;
                    }
                }
            }
        }
    }
    
    // Record trace
    if(snnSimState.selectedNeuron >= 0 && snnSimState.selectedNeuron < N) {
        snnSimState.trace.push({x: t, y: V[snnSimState.selectedNeuron]});
    }
    
    // Accumulate Energy for this dt step
    // 1. Charging Energy: 0.5 * C_m * (V_th - V_reset)^2 * spikes (in pJ)
    // C_m is in fF. V is in mV. E = 0.5 * C_m(1e-15) * V^2(1e-6) = J. 
    // To get pJ (1e-12 J), multiply by 1e-9.
    let dV = P.Vth - P.Vreset;
    let e_charge = 0.5 * P.Cm * (dV * dV) * currentSpikes.length * 1e-9;
    
    // 2. Leakage Energy: G_leak * (V - V_rest)^2 * dt (in pJ)
    // G_leak in nS (1e-9 S). V in mV (1e-3 V). dt in ms (1e-3 s).
    // E = G_leak * V^2 * dt = 1e-9 * 1e-6 * 1e-3 = 1e-18 J.
    // To get pJ (1e-12 J), multiply by 1e-6.
    let e_leak = 0;
    for(let i=0; i<N; i++) {
        let v_diff = V[i] - P.Vrest;
        e_leak += P.Gleak * (v_diff * v_diff) * dt * 1e-6;
    }
    
    // 3. Synaptic Energy: proportional to number of active synapses transmitted
    let e_syn = 0;
    if(snnSimState.mode === 'stdp' || snnSimState.mode === 'manual') {
        let syn_events = 0;
        syn_events = syn_events_count;
        e_syn = syn_events * snnSimState.energyParams.e_syn_coeff;
    }
    
    // 4. Overhead Energy
    let e_overhead = currentSpikes.length * snnSimState.energyParams.e_spike_overhead;
    
    snnSimState.energyBuffer.push({
        t: t,
        charge: e_charge,
        leak: e_leak,
        syn: e_syn,
        overhead: e_overhead
    });
    
    snnSimState.time += dt;
}

function snnLoop(timestamp) {
    if(!snnSimState.isRunning) return;
    
    if(!snnSimState.lastTs) snnSimState.lastTs = timestamp;
    let dt_wall = timestamp - snnSimState.lastTs;
    snnSimState.lastTs = timestamp;
    
    if(dt_wall > 100) dt_wall = 16;
    
    // Real time passed * speed
    let time_to_sim = dt_wall * snnSimState.speed;
    let steps = Math.floor(time_to_sim / snnSimState.dt);
    
    for(let i=0; i<steps; i++) {
        stepSNNSim(snnSimState.dt);
    }
    
    renderRaster();
    renderTrace();
    if(snnSimState.mode === 'stdp' && snnSimState.plasticityEvents % 50 === 0) {
        renderHeatmap();
    }
    updateSNNUI();
    
    // Update Energy Chart every ~200ms of real time
    if(timestamp - snnSimState.lastEnergyUpdate > 200) {
        updateEnergyChart();
        snnSimState.lastEnergyUpdate = timestamp;
    }
    
    snnSimState.rafId = requestAnimationFrame(snnLoop);
}

// Rendering
function renderRaster() {
    const canvas = document.getElementById('snnCanvasRaster');
    if(!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    
    ctx.clearRect(0,0,W,H);
    ctx.fillStyle = '#d946ef'; // trace color
    
    const t_end = Math.max(snnSimState.t_window, snnSimState.time);
    const t_start = Math.max(0, t_end - snnSimState.t_window);
    
    // Prune raster
    if(snnSimState.raster.length > 10000) {
        snnSimState.raster = snnSimState.raster.filter(s => s.t > t_start - 50);
    }
    
    const rowH = H / snnSimState.N;
    
    ctx.beginPath();
    for(let i=0; i<snnSimState.raster.length; i++) {
        let sp = snnSimState.raster[i];
        if(sp.t >= t_start && sp.t <= t_end) {
            let x = ((sp.t - t_start) / snnSimState.t_window) * W;
            let y = sp.n * rowH;
            ctx.moveTo(x, y);
            ctx.lineTo(x, y + rowH - 1);
        }
    }
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = '#d946ef';
    ctx.stroke();
}

function renderHeatmap() {
    const canvas = document.getElementById('snnCanvasHeatmap');
    if(!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    
    const N = snnSimState.N;
    const cellW = W / N;
    const cellH = H / N;
    
    ctx.clearRect(0,0,W,H);
    
    let maxW = snnSimState.mode==='stdp' ? snnSimState.STDP.wMax : 10;
    
    for(let i=0; i<N; i++) {
        for(let j=0; j<N; j++) {
            if(i === j) continue;
            if(snnSimState.heatmapView === 'weights') {
                let w = snnSimState.W[i*N + j];
                if(w === 0) continue;
                let intensity = Math.min(1, w / maxW);
                ctx.fillStyle = `rgba(16, 185, 129, ${intensity})`;
                ctx.fillRect(j*cellW, i*cellH, cellW, cellH);
            } else {
                // Delays mode
                if(snnSimState.delayMode === 'none') continue;
                let d = snnSimState.D[i*N + j];
                let maxD = 10;
                let intensity = Math.min(1, d / maxD);
                // Color map for delays: dark to bright purple (#8b5cf6)
                ctx.fillStyle = `rgba(139, 92, 246, ${intensity})`;
                ctx.fillRect(j*cellW, i*cellH, cellW, cellH);
            }
        }
    }
}

function renderTrace() {
    if(!snnTraceChart) return;
    const t_end = Math.max(snnSimState.t_window, snnSimState.time);
    const t_start = Math.max(0, t_end - snnSimState.t_window);
    
    if(snnSimState.trace.length > 5000) {
        snnSimState.trace = snnSimState.trace.filter(pt => pt.x > t_start - 50);
    }
    
    snnTraceChart.data.datasets[0].data = snnSimState.trace;
    snnTraceChart.options.scales.x.min = t_start;
    snnTraceChart.options.scales.x.max = t_end;
    snnTraceChart.update();
}

function updateSNNUI() {
    const recent = snnSimState.raster.filter(s => s.t > snnSimState.time - 100);
    const hz = (recent.length / snnSimState.N) * 10;
    document.getElementById('snn-rate').innerText = hz.toFixed(1);
    
    if(snnSimState.mode === 'stdp') {
        document.getElementById('snn-plast-events').innerText = snnSimState.plasticityEvents;
    }
}

function initEnergyChart() {
    const ctx = document.getElementById('chSnnEnergy');
    if(!ctx) return;
    snnEnergyChart = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Charging', 'Leakage', 'Synaptic', 'Overhead'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: ['#3b82f6', '#f97316', '#10b981', '#ef4444'],
                borderWidth: 1,
                borderColor: '#1e1e2d'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
            plugins: {
                legend: { position: 'right', labels: { color: '#ccc', boxWidth: 12, font: {size: 10} } },
                tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed.toFixed(2)} pJ` } }
            },
            cutout: '60%'
        }
    });
}

function updateEnergyChart() {
    if(!snnEnergyChart) return;
    const t_end = snnSimState.time;
    const t_start = t_end - snnSimState.energyParams.timeWindow;
    
    // Prune buffer
    snnSimState.energyBuffer = snnSimState.energyBuffer.filter(e => e.t >= Math.max(0, t_start));
    
    let sum = { charge: 0, leak: 0, syn: 0, overhead: 0 };
    for(let i=0; i<snnSimState.energyBuffer.length; i++) {
        let e = snnSimState.energyBuffer[i];
        sum.charge += e.charge;
        sum.leak += e.leak;
        sum.syn += e.syn;
        sum.overhead += e.overhead;
    }
    
    let total = sum.charge + sum.leak + sum.syn + sum.overhead;
    snnEnergyChart.data.datasets[0].data = [sum.charge, sum.leak, sum.syn, sum.overhead];
    snnEnergyChart.update();
    
    let totalEl = document.getElementById('snn-energy-total');
    if(totalEl) totalEl.innerText = `${total.toFixed(2)} pJ`;
}

function initSNNChart() {
    const ctx = document.getElementById('chSnnTrace').getContext('2d');
    snnTraceChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'V_mem (mV)',
                data: [],
                borderColor: '#10b981',
                borderWidth: 1.5,
                pointRadius: 0,
                showLine: true
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, animation: false,
            scales: {
                x: { min: 0, max: snnSimState.t_window, grid:{color:'#333'}, ticks:{color:'#aaa'} },
                y: { suggestedMin: -20, suggestedMax: 400, grid:{color:'#333'}, ticks:{color:'#aaa'} }
            },
            plugins: { legend: {display: false} }
        }
    });
}

// Setup Hooks
window.startSNNSimulator = function() {
    initSNNArrays();
    initWeights('uniform', 1, 5, 30);
    initDelays();
    initSNNChart();
    initEnergyChart();
    
    // Energy Modal Hooks
    const emodal = document.getElementById('snnEnergyModal');
    if(emodal) {
        document.getElementById('snn-btn-energy-settings').addEventListener('click', () => emodal.style.display='flex');
        document.getElementById('snn-btn-close-energy').addEventListener('click', () => emodal.style.display='none');
        
        ['energy-syn', 'energy-overhead', 'energy-twin'].forEach(id => {
            const el = document.getElementById(id);
            if(el) {
                el.addEventListener('input', e => {
                    let v = parseFloat(e.target.value);
                    if(id === 'energy-syn') {
                        snnSimState.energyParams.e_syn_coeff = v;
                        document.getElementById(id+'-val').innerText = v.toFixed(2);
                    }
                    if(id === 'energy-overhead') {
                        snnSimState.energyParams.e_spike_overhead = v;
                        document.getElementById(id+'-val').innerText = v.toFixed(2);
                    }
                    if(id === 'energy-twin') {
                        snnSimState.energyParams.timeWindow = v;
                        document.getElementById(id+'-val').innerText = v;
                    }
                });
            }
        });
    }

    document.getElementById('snn-btn-edit-matrix').addEventListener('click', openMatrixModal);
    document.getElementById('snn-btn-close-modal').addEventListener('click', closeMatrixModal);
    document.getElementById('snn-btn-cancel-matrix').addEventListener('click', closeMatrixModal);
    document.getElementById('snn-btn-save-matrix').addEventListener('click', saveMatrixModal);
    
    document.getElementById('snn-init-method').addEventListener('change', e => {
        initWeights(e.target.value, 1, 5, 30);
    });

    
    // UI listeners
    document.getElementById('snn-btn-run').addEventListener('click', () => {
        snnSimState.isRunning = true;
        snnSimState.lastTs = 0;
        if(!snnSimState.rafId) snnSimState.rafId = requestAnimationFrame(snnLoop);
    });
    document.getElementById('snn-btn-pause').addEventListener('click', () => {
        snnSimState.isRunning = false;
        if(snnSimState.rafId) { cancelAnimationFrame(snnSimState.rafId); snnSimState.rafId = null; }
    });
    document.getElementById('snn-btn-reset').addEventListener('click', resetSNNSim);
    
    // Inputs
    const binds = [
        ['snn-n', 'N'], ['snn-twin', 't_window'], ['snn-dt', 'dt'], ['snn-speed', 'speed']
    ];
    binds.forEach(b => {
        const el = document.getElementById(b[0]);
        if(el) {
            el.addEventListener('input', e => {
                let v = parseFloat(e.target.value);
                snnSimState[b[1]] = v;
                document.getElementById(b[0]+'-val').innerText = v;
                if(b[1] === 'N') {
                    snnSimState.isRunning = false;
                    initSNNArrays();
                    initWeights('uniform', 1, 5, 30);
                    initDelays();
                    resetSNNSim();
                    populateNeuronDropdown();
                }
            });
        }
    });
    
    document.getElementById('snn-sel-neuron').addEventListener('change', e => {
        snnSimState.selectedNeuron = parseInt(e.target.value);
        snnSimState.trace = [];
    });
    

    // Delay Controls UI
    const dm = document.getElementById('snn-delay-mode');
    if(dm) {
        dm.addEventListener('change', e => {
            snnSimState.delayMode = e.target.value;
            ['const', 'unimin', 'unimax', 'fetk'].forEach(id => document.getElementById('d-param-'+id).style.display = 'none');
            
            if(snnSimState.delayMode === 'constant') document.getElementById('d-param-const').style.display = 'flex';
            if(snnSimState.delayMode === 'uniform') {
                document.getElementById('d-param-unimin').style.display = 'flex';
                document.getElementById('d-param-unimax').style.display = 'flex';
            }
            if(snnSimState.delayMode === 'fet') document.getElementById('d-param-fetk').style.display = 'flex';
            
            initDelays();
            resetSNNSim();
        });
        
        ['snn-delay-const', 'snn-delay-min', 'snn-delay-max', 'snn-delay-k'].forEach(id => {
            const el = document.getElementById(id);
            if(el) {
                el.addEventListener('input', e => {
                    let v = parseFloat(e.target.value);
                    document.getElementById(id+'-val').innerText = v.toFixed(2);
                    if(id === 'snn-delay-const') snnSimState.delayParams.c = v;
                    if(id === 'snn-delay-min') snnSimState.delayParams.min = v;
                    if(id === 'snn-delay-max') snnSimState.delayParams.max = v;
                    if(id === 'snn-delay-k') snnSimState.delayParams.k = v;
                    
                    initDelays();
                });
            }
        });
    }
    
    const hv = document.getElementById('snn-heatmap-view');
    if(hv) {
        hv.addEventListener('change', e => {
            snnSimState.heatmapView = e.target.value;
            renderHeatmap();
        });
    }
    // Mode switcher
    document.querySelectorAll('input[name="snnMode"]').forEach(r => {
        r.addEventListener('change', e => {
            snnSimState.mode = e.target.value;
            document.getElementById('snn-manual-controls').style.display = snnSimState.mode === 'manual' ? 'block' : 'none';
            document.getElementById('snn-stdp-controls').style.display = snnSimState.mode === 'stdp' ? 'block' : 'none';
            document.getElementById('snn-stdp-stats').style.display = snnSimState.mode === 'stdp' ? 'block' : 'none';
            resetSNNSim();
            initWeights('uniform', 1, 5, 30);
            renderHeatmap();
        });
    });
    
    populateNeuronDropdown();
    
    // CSV Exports
    document.getElementById('snn-btn-csv-raster').addEventListener('click', () => {
        let csv = "Time(ms),NeuronID\\n";
        snnSimState.raster.forEach(r => csv += `${r.t.toFixed(2)},${r.n}\\n`);
        downloadCSV(csv, 'SNN_Raster.csv');
    });
    
    document.getElementById('snn-btn-csv-weights').addEventListener('click', () => {
        let csv = "Pre\\\\Post,";
        const N = snnSimState.N;
        for(let i=0; i<N; i++) csv += `${i},`;
        csv += "\\n";
        for(let i=0; i<N; i++) {
            csv += `${i},`;
            for(let j=0; j<N; j++) {
                csv += `${snnSimState.W[i*N+j].toFixed(4)},`;
            }
            csv += "\\n";
        }
        downloadCSV(csv, 'SNN_Weights.csv');
    });
};

function populateNeuronDropdown() {
    const sel = document.getElementById('snn-sel-neuron');
    if(!sel) return;
    sel.innerHTML = '';
    for(let i=0; i<snnSimState.N; i++) {
        let opt = document.createElement('option');
        opt.value = i; opt.innerText = `Neuron ${i}`;
        sel.appendChild(opt);
    }
}

function downloadCSV(csvStr, filename) {
    const blob = new Blob([csvStr], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
}


// --- Matrix Editor Modal Logic ---
let tempMatrix = null;

function openMatrixModal() {
    const N = snnSimState.N;
    tempMatrix = new Float64Array(snnSimState.W);
    const container = document.getElementById('snnMatrixContainer');
    if(!container) return;
    
    let html = '<table style="border-collapse:collapse; text-align:center; color:#fff; font-family:monospace; font-size:0.8rem;">';
    // Header
    html += '<tr><th style="padding:5px; border:1px solid #444; background:#222;">Pre \\ Post</th>';
    for(let i=0; i<N; i++) html += `<th style="padding:5px; border:1px solid #444; background:#222;">${i}</th>`;
    html += '</tr>';
    
    // Body
    for(let i=0; i<N; i++) {
        html += `<tr><th style="padding:5px; border:1px solid #444; background:#222;">${i}</th>`;
        for(let j=0; j<N; j++) {
            let val = tempMatrix[i*N + j];
            let bg = i===j ? '#333' : (val > 0 ? `rgba(16, 185, 129, ${Math.min(1, val/5)})` : 'transparent');
            html += `<td style="padding:2px; border:1px solid #444; background:${bg};">
                        <input type="number" step="0.1" data-r="${i}" data-c="${j}" value="${val.toFixed(2)}" ${i===j?'disabled':''} style="width:50px; background:transparent; border:none; color:#fff; text-align:center;">
                     </td>`;
        }
        html += '</tr>';
    }
    html += '</table>';
    container.innerHTML = html;
    
    // Inputs change listener
    container.querySelectorAll('input').forEach(inp => {
        inp.addEventListener('change', e => {
            let r = parseInt(e.target.dataset.r);
            let c = parseInt(e.target.dataset.c);
            let val = parseFloat(e.target.value);
            if(!isNaN(val)) tempMatrix[r*N + c] = val;
            let bg = r===c ? '#333' : (val > 0 ? `rgba(16, 185, 129, ${Math.min(1, val/5)})` : 'transparent');
            e.target.parentElement.style.background = bg;
        });
    });
    
    document.getElementById('snnMatrixModal').style.display = 'flex';
}

function closeMatrixModal() {
    document.getElementById('snnMatrixModal').style.display = 'none';
}

function saveMatrixModal() {
    if(tempMatrix) {
        snnSimState.W.set(tempMatrix);
        renderHeatmap();
    }
    closeMatrixModal();
}

// Hook up modal buttons
document.addEventListener('DOMContentLoaded', () => {
    // These might be injected late, so we use document-level delegation or wait for init
});
