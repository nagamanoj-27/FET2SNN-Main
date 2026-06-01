import re

# 1. Patch snn-simulator.js
with open('snn-simulator.js', 'r', encoding='utf-8') as f:
    sjs = f.read()

# Inside stepSNNSim, where spike happens:
#         if(V[i] >= P.Vth) {
#             currentSpikes.push(i);
#             V[i] = P.Vreset;
#             ls[i] = t;
#             snnSimState.raster.push({t: t, n: i});
#         }

old_spike_snn = """        if(V[i] >= P.Vth) {
            currentSpikes.push(i);
            V[i] = P.Vreset;
            ls[i] = t;
            snnSimState.raster.push({t: t, n: i});
        }"""

# Calculate a rough global rate to pass to audio
new_spike_snn = """        if(V[i] >= P.Vth) {
            currentSpikes.push(i);
            V[i] = P.Vreset;
            ls[i] = t;
            snnSimState.raster.push({t: t, n: i});
            if(window.playSpikeSound) {
                // Approximate global rate by spike count in raster
                let rate = snnSimState.raster.length > 50 ? 50 : snnSimState.raster.length;
                window.playSpikeSound(i, t, rate);
            }
        }"""

sjs = sjs.replace(old_spike_snn, new_spike_snn)

# Add clearMidiBuffer to resetSNNSim
sjs = sjs.replace("snnSimState.plasticityEvents = 0;", "snnSimState.plasticityEvents = 0;\n    if(window.clearMidiBuffer) window.clearMidiBuffer();")

with open('snn-simulator.js', 'w', encoding='utf-8') as f:
    f.write(sjs)


# 2. Patch lif-neuron.js
with open('lif-neuron.js', 'r', encoding='utf-8') as f:
    ljs = f.read()

old_spike_lif = """    if (lifState.V >= lifParams.Vth) {
        lifState.V = lifParams.Vth; // For visualization
        lifState.lastSpikeTime = lifState.time;
        
        let t_spike = lifState.time;"""

new_spike_lif = """    if (lifState.V >= lifParams.Vth) {
        lifState.V = lifParams.Vth; // For visualization
        lifState.lastSpikeTime = lifState.time;
        
        if(window.playSpikeSound) window.playSpikeSound(0, lifState.time, 10);
        
        let t_spike = lifState.time;"""

ljs = ljs.replace(old_spike_lif, new_spike_lif)

# Add clearMidiBuffer to resetLIF
ljs = ljs.replace("lifState.time = 0;", "lifState.time = 0;\n    if(window.clearMidiBuffer) window.clearMidiBuffer();")

with open('lif-neuron.js', 'w', encoding='utf-8') as f:
    f.write(ljs)
