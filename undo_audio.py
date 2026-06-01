import re
import os

# 1. index.html
try:
    with open('index.html', encoding='utf-8') as f:
        content = f.read()

    # Remove script tag
    content = content.replace('<script src="snn-simulator.js"></script>\n<script src="audio-synesthesia.js"></script>', '<script src="snn-simulator.js"></script>')

    # Remove UI Card
    # Let's use regex to find and remove it
    pattern_card = re.compile(r'<!-- Neural Synesthesia Audio Card -->.*?<!-- SNN Energy Settings Modal -->', re.DOTALL)
    content = re.sub(pattern_card, '<!-- SNN Energy Settings Modal -->', content)

    # Remove init script
    content = content.replace('<script>if(window.initAudioSynesthesiaUI) window.initAudioSynesthesiaUI();</script>\n</body>', '</body>')

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("index.html reverted.")
except Exception as e:
    print(f"Error in index.html: {e}")

# 2. snn-simulator.js
try:
    with open('snn-simulator.js', 'r', encoding='utf-8') as f:
        sjs = f.read()

    old_spike_snn = """        if(V[i] >= P.Vth) {
            currentSpikes.push(i);
            V[i] = P.Vreset;
            ls[i] = t;
            snnSimState.raster.push({t: t, n: i});
        }"""
    
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
    
    sjs = sjs.replace(new_spike_snn, old_spike_snn)
    sjs = sjs.replace("snnSimState.plasticityEvents = 0;\n    if(window.clearMidiBuffer) window.clearMidiBuffer();", "snnSimState.plasticityEvents = 0;")

    with open('snn-simulator.js', 'w', encoding='utf-8') as f:
        f.write(sjs)
    print("snn-simulator.js reverted.")
except Exception as e:
    print(f"Error in snn-simulator.js: {e}")

# 3. lif-neuron.js
try:
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

    ljs = ljs.replace(new_spike_lif, old_spike_lif)
    ljs = ljs.replace("lifState.time = 0;\n    if(window.clearMidiBuffer) window.clearMidiBuffer();", "lifState.time = 0;")

    with open('lif-neuron.js', 'w', encoding='utf-8') as f:
        f.write(ljs)
    print("lif-neuron.js reverted.")
except Exception as e:
    print(f"Error in lif-neuron.js: {e}")

# 4. Delete audio-synesthesia.js
if os.path.exists('audio-synesthesia.js'):
    os.remove('audio-synesthesia.js')
    print("audio-synesthesia.js deleted.")
