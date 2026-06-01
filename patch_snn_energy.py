import re

with open('snn-simulator.js', encoding='utf-8') as f:
    content = f.read()

# 1. Update snnSimState
old_state = """    // STDP Parameters
    STDP: { Ap: 0.01, Am: 0.012, tauP: 20, tauM: 20, wMin: 0, wMax: 10, excOnly: false },
    
    rafId: null,
    lastTs: 0
};"""

new_state = """    // STDP Parameters
    STDP: { Ap: 0.01, Am: 0.012, tauP: 20, tauM: 20, wMin: 0, wMax: 10, excOnly: false },
    
    // Energy Breakdown Parameters
    energyParams: { e_syn_coeff: 0.1, e_spike_overhead: 0.05, timeWindow: 200 },
    energyBuffer: [],
    
    rafId: null,
    lastTs: 0,
    lastEnergyUpdate: 0
};

let snnEnergyChart = null;"""

content = content.replace(old_state, new_state)

# 2. Add accumulateEnergy logic in stepSNNSim
# Find the end of stepSNNSim
old_step_end = """    // Record trace
    if(snnSimState.selectedNeuron >= 0 && snnSimState.selectedNeuron < N) {
        snnSimState.trace.push({x: t, y: V[snnSimState.selectedNeuron]});
    }
    
    snnSimState.time += dt;
}"""

new_step_end = """    // Record trace
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
        for(let k=0; k<currentSpikes.length; k++) {
            let i = currentSpikes[k];
            for(let j=0; j<N; j++) {
                if(i !== j && W[i*N + j] !== 0) syn_events++;
            }
        }
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
}"""

content = content.replace(old_step_end, new_step_end)

# 3. Add updateEnergyChart in snnLoop
old_snn_loop = """    renderRaster();
    renderTrace();
    if(snnSimState.mode === 'stdp' && snnSimState.plasticityEvents % 50 === 0) {
        renderHeatmap();
    }
    updateSNNUI();
    
    snnSimState.rafId = requestAnimationFrame(snnLoop);"""

new_snn_loop = """    renderRaster();
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
    
    snnSimState.rafId = requestAnimationFrame(snnLoop);"""

content = content.replace(old_snn_loop, new_snn_loop)

# 4. Add initEnergyChart, updateEnergyChart, and UI hooks
old_init_snn_chart = """function initSNNChart() {
    const ctx = document.getElementById('chSnnTrace').getContext('2d');"""

new_energy_charts = """function initEnergyChart() {
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
    const ctx = document.getElementById('chSnnTrace').getContext('2d');"""

content = content.replace(old_init_snn_chart, new_energy_charts)

# 5. Reset Energy buffer
old_reset = """function resetSNNSim() {
    snnSimState.isRunning = false;
    if(snnSimState.rafId) { cancelAnimationFrame(snnSimState.rafId); snnSimState.rafId = null; }
    const N = snnSimState.N;
    snnSimState.time = 0;
    snnSimState.raster = [];
    snnSimState.trace = [];
    snnSimState.plasticityEvents = 0;"""

new_reset = """function resetSNNSim() {
    snnSimState.isRunning = false;
    if(snnSimState.rafId) { cancelAnimationFrame(snnSimState.rafId); snnSimState.rafId = null; }
    const N = snnSimState.N;
    snnSimState.time = 0;
    snnSimState.raster = [];
    snnSimState.trace = [];
    snnSimState.plasticityEvents = 0;
    snnSimState.energyBuffer = [];
    if(snnEnergyChart) {
        snnEnergyChart.data.datasets[0].data = [0,0,0,0];
        snnEnergyChart.update();
        document.getElementById('snn-energy-total').innerText = '0.00 pJ';
    }"""

content = content.replace(old_reset, new_reset)

# 6. Hook up Init and Modal
old_start_snn = """window.startSNNSimulator = function() {
    initSNNArrays();
    initWeights('uniform', 1, 5, 30);
    initSNNChart();"""

new_start_snn = """window.startSNNSimulator = function() {
    initSNNArrays();
    initWeights('uniform', 1, 5, 30);
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
    }"""

content = content.replace(old_start_snn, new_start_snn)

with open('snn-simulator.js', 'w', encoding='utf-8') as f:
    f.write(content)
