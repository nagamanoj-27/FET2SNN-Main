import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. UI Inject: Delay Controls in index.html
# After <div id="snn-manual-controls" ...>
old_manual_controls = """        <!-- Manual Controls -->
        <div id="snn-manual-controls" style="margin-bottom:1rem;">
          <div style="display:flex; gap:10px; align-items:center;">
            <select id="snn-init-method" style="padding:5px; border-radius:4px; border:1px solid var(--border); background:var(--bg); color:var(--text);">
              <option value="uniform">Uniform random</option>
              <option value="constant">Constant</option>
              <option value="sparse">Random sparse</option>
            </select>
            <button class="btn bb" id="snn-btn-edit-matrix"><i class="fas fa-edit"></i> Edit matrix</button>
          </div>
        </div>"""

new_delay_controls = old_manual_controls + """
        
        <!-- Delay Controls -->
        <div style="margin-bottom:1rem; padding:10px; background:var(--card-h); border:1px solid var(--border); border-radius:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
            <label style="font-weight:bold;">Synaptic Delays <span class="ttip">ⓘ<span class="ttip-text">Synaptic delays mimic axonal propagation time. Delays affect spike timing and STDP learning. 'FET-derived' delay scales with gate length.</span></span></label>
            <select id="snn-delay-mode" style="padding:3px; border-radius:4px; background:var(--bg); color:var(--text); border:1px solid var(--border);">
              <option value="none">No delay</option>
              <option value="constant">Constant delay</option>
              <option value="uniform">Uniform random</option>
              <option value="fet">FET-derived</option>
            </select>
          </div>
          <div id="snn-delay-params" class="isg" style="display:none;">
            <div class="ig" id="d-param-const" style="display:none;"><label>Delay <span class="u">ms</span></label><div class="sr"><input type="range" id="snn-delay-const" min="0" max="10" step="0.5" value="1.0"><span class="lv" id="snn-delay-const-val">1.0</span></div></div>
            <div class="ig" id="d-param-unimin" style="display:none;"><label>Min <span class="u">ms</span></label><div class="sr"><input type="range" id="snn-delay-min" min="0" max="10" step="0.5" value="0.5"><span class="lv" id="snn-delay-min-val">0.5</span></div></div>
            <div class="ig" id="d-param-unimax" style="display:none;"><label>Max <span class="u">ms</span></label><div class="sr"><input type="range" id="snn-delay-max" min="0" max="10" step="0.5" value="2.5"><span class="lv" id="snn-delay-max-val">2.5</span></div></div>
            <div class="ig" id="d-param-fetk" style="display:none;"><label>k-factor <span class="u">ms/nm</span></label><div class="sr"><input type="range" id="snn-delay-k" min="0.01" max="0.2" step="0.01" value="0.05"><span class="lv" id="snn-delay-k-val">0.05</span></div></div>
          </div>
        </div>"""

if "id=\"snn-delay-mode\"" not in content:
    content = content.replace(old_manual_controls, new_delay_controls)

# 2. UI Inject: Heatmap Toggle
old_heatmap_label = """<label style="font-weight:bold; font-size:0.9rem;">Weight Matrix</label>"""
new_heatmap_label = """<div style="display:flex; justify-content:space-between; align-items:center;">
              <label style="font-weight:bold; font-size:0.9rem;">Matrix View</label>
              <select id="snn-heatmap-view" style="font-size:0.75rem; padding:1px; background:var(--bg); color:var(--text); border:1px solid var(--border); border-radius:4px;">
                <option value="weights">Weights</option>
                <option value="delays">Delays (ms)</option>
              </select>
            </div>"""
if 'id="snn-heatmap-view"' not in content:
    content = content.replace(old_heatmap_label, new_heatmap_label)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

# Now snn-simulator.js
with open('snn-simulator.js', 'r', encoding='utf-8') as f:
    sjs = f.read()

# State
sjs = sjs.replace("""    energyParams: { e_syn_coeff: 0.1, e_spike_overhead: 0.05, timeWindow: 200 },
    energyBuffer: [],
    
    rafId: null,""", """    energyParams: { e_syn_coeff: 0.1, e_spike_overhead: 0.05, timeWindow: 200 },
    energyBuffer: [],
    
    // Delays
    delayMode: 'none',
    delayParams: { c: 1.0, min: 0.5, max: 2.5, k: 0.05 },
    D: null,
    eventRing: null, // array of length 1000
    
    heatmapView: 'weights',
    rafId: null,""")

# Array init
old_init_arrays = """function initSNNArrays() {
    const N = snnSimState.N;
    snnSimState.V = new Float64Array(N);
    snnSimState.ref = new Float64Array(N);
    snnSimState.lastSpike = new Float64Array(N).fill(-9999);
    snnSimState.W = new Float64Array(N * N);
    snnSimState.I_ext = new Float64Array(N);
    
    // Initialize external input: first half gets 2 nA
    for(let i=0; i<N; i++) {
        snnSimState.V[i] = snnSimState.P.Vrest;
        snnSimState.I_ext[i] = (i < N/2) ? 2.0 : 0.0; 
    }
}"""

new_init_arrays = """function initSNNArrays() {
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
}"""

sjs = sjs.replace(old_init_arrays, new_init_arrays)

# Add initDelays() into startSNNSimulator()
sjs = sjs.replace("    initWeights('uniform', 1, 5, 30);\n    initSNNChart();", "    initWeights('uniform', 1, 5, 30);\n    initDelays();\n    initSNNChart();")
sjs = sjs.replace("initWeights('uniform', 1, 5, 30);\n                    resetSNNSim();", "initWeights('uniform', 1, 5, 30);\n                    initDelays();\n                    resetSNNSim();")

# Modify stepSNNSim
old_step_loop = """    for(let i=0; i<N; i++) {
        if(t - ls[i] < P.tRef) {
            V[i] = P.Vreset;
            continue;
        }
        
        let I_syn = 0;
        // Check incoming spikes from previous step (we assume instant transmission for simplicity, or 1 step delay)
        // Actually, we check if other neurons spiked recently. In a dt step, we just sum weights of those who fired.
        
        // Calculate total input current
        let I_tot = snnSimState.I_ext[i] + I_syn; // + noise if we wanted
        
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
                // simple delta-synapse: instantly add to V_mem (w in nS mapped to mV jump roughly)
                // or just add to V directly
                V[j] += w * Rm_mV_per_nA * 0.1; // scale factor
            }
            
            // STDP: pre-synaptic fires (t_pre = t). Check post-synaptic history
            if(snnSimState.mode === 'stdp' && w !== 0) {
                let dt_spike = ls[j] - t; // t_post - t_pre. Since t_post is past, dt_spike < 0
                if(dt_spike > -50 && dt_spike < 0) {
                    // Depression
                    let dw = -snnSimState.STDP.Am * Math.exp(dt_spike / snnSimState.STDP.tauM);
                    W[i*N + j] = Math.max(snnSimState.STDP.wMin, Math.min(snnSimState.STDP.wMax, w + dw));
                    snnSimState.plasticityEvents++;
                }
            }
        }"""

new_step_loop = """    // Process Delayed Synaptic Events arriving at this step
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
        }"""

sjs = sjs.replace(old_step_loop, new_step_loop)

# Fix energy calculation for synaptic events to use syn_events_count
sjs = sjs.replace("""        for(let k=0; k<currentSpikes.length; k++) {
            let i = currentSpikes[k];
            for(let j=0; j<N; j++) {
                if(i !== j && W[i*N + j] !== 0) syn_events++;
            }
        }""", "        syn_events = syn_events_count;")

# Update resetSNNSim for eventRing
old_reset = """    snnSimState.energyBuffer = [];"""
new_reset = """    snnSimState.energyBuffer = [];
    if(snnSimState.eventRing) {
        for(let i=0; i<1000; i++) snnSimState.eventRing[i].length = 0;
    }"""
sjs = sjs.replace(old_reset, new_reset)

# Update Heatmap render
old_hm = """    for(let i=0; i<N; i++) {
        for(let j=0; j<N; j++) {
            let w = snnSimState.W[i*N + j];
            if(w === 0) continue;
            let intensity = Math.min(1, w / maxW);
            // Color map: dark to bright green
            ctx.fillStyle = `rgba(16, 185, 129, ${intensity})`;
            ctx.fillRect(j*cellW, i*cellH, cellW, cellH);
        }
    }"""

new_hm = """    for(let i=0; i<N; i++) {
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
    }"""
sjs = sjs.replace(old_hm, new_hm)

# Hook up the new UI events
new_hooks = """
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
    }"""

sjs = sjs.replace("    // Mode switcher\n    document.querySelectorAll('input[name=\"snnMode\"]')", new_hooks + "\n    // Mode switcher\n    document.querySelectorAll('input[name=\"snnMode\"]')")

# Add global delay update trigger to global hook
sjs = sjs.replace("""    // Auto reset for friendliness
    resetSNNSim();
};""", """    if(snnSimState.delayMode === 'fet') initDelays();
    // Auto reset for friendliness
    resetSNNSim();
};""")


with open('snn-simulator.js', 'w', encoding='utf-8') as f:
    f.write(sjs)
