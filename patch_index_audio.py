import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Inject script tag for audio-synesthesia.js
if 'audio-synesthesia.js' not in content:
    content = content.replace('<script src="snn-simulator.js"></script>', '<script src="snn-simulator.js"></script>\n<script src="audio-synesthesia.js"></script>')

# 2. Inject UI Card
ui_html = """
    <!-- Neural Synesthesia Audio Card -->
    <div class="card" id="snnAudioCard" style="margin-bottom:1.5rem;">
      <div class="ct" style="display:flex; justify-content:space-between; align-items:center;">
        <span><i class="fas fa-headphones"></i> Neural Synesthesia <span class="ttip" style="margin-left:5px; font-size:0.85rem; font-weight:normal;">ⓘ<span class="ttip-text">Auditory spike sonification. Listen to the network's rhythm.</span></span></span>
        <label style="display:flex; align-items:center; gap:5px; font-size:0.9rem; font-weight:bold; cursor:pointer;">
          <input type="checkbox" id="audio-enable" style="width:16px; height:16px;"> Enable Audio
        </label>
      </div>
      
      <div style="display:flex; gap:1rem; flex-wrap:wrap;">
        <div class="isg" style="flex:1; min-width:250px;">
          <div class="ig"><label>Master Volume</label><div class="sr"><input type="range" id="audio-volume" min="0" max="1" step="0.05" value="0.5"><span class="lv" id="audio-volume-val">0.5</span></div></div>
          <div class="ig"><label>Note Duration <span class="u">ms</span></label><div class="sr"><input type="range" id="audio-duration" min="10" max="500" step="10" value="100"><span class="lv" id="audio-duration-val">100</span></div></div>
          <div class="ig" style="flex-direction:row; justify-content:space-between; align-items:center;">
            <label>Waveform</label>
            <select id="audio-waveform" style="padding:2px 5px; background:var(--bg); color:var(--text); border:1px solid var(--border); border-radius:4px;">
              <option value="sine">Sine</option>
              <option value="square">Square</option>
              <option value="sawtooth">Sawtooth</option>
              <option value="triangle">Triangle</option>
            </select>
          </div>
        </div>
        
        <div class="isg" style="flex:1; min-width:250px;">
          <div class="ig" style="flex-direction:row; justify-content:space-between; align-items:center; margin-bottom:5px;">
            <label>Note Mapping</label>
            <select id="audio-mapping" style="padding:2px 5px; background:var(--bg); color:var(--text); border:1px solid var(--border); border-radius:4px;">
              <option value="chromatic">Chromatic Scale</option>
              <option value="pentatonic">Pentatonic Scale</option>
              <option value="major">Major Scale</option>
              <option value="minor">Minor Scale</option>
              <option value="fixed">Fixed Pitch</option>
            </select>
          </div>
          <div class="ig"><label>Base Frequency <span class="u">Hz</span></label><div class="sr"><input type="range" id="audio-baseFreq" min="100" max="1000" step="10" value="440"><span class="lv" id="audio-baseFreq-val">440</span></div></div>
          <div class="ig" style="flex-direction:row; justify-content:space-between; align-items:center;">
            <label>Volume Dynamics</label>
            <select id="audio-volDynamics" style="padding:2px 5px; background:var(--bg); color:var(--text); border:1px solid var(--border); border-radius:4px;">
              <option value="constant">Constant</option>
              <option value="rate">Proportional to Firing Rate</option>
            </select>
          </div>
        </div>
        
        <div style="flex:1; min-width:200px; display:flex; flex-direction:column; gap:0.5rem;">
          <label style="font-weight:bold; font-size:0.9rem;">Spike Visualizer</label>
          <div style="flex:1; background:#0a0a1a; border:1px solid var(--border); border-radius:8px; overflow:hidden;">
            <canvas id="chSynesthesiaViz" width="300" height="60" style="width:100%; height:100%;"></canvas>
          </div>
          <div style="display:flex; gap:0.5rem; justify-content:flex-end;">
            <button class="btn bb" id="audio-btn-midi"><i class="fas fa-file-audio"></i> Export MIDI</button>
            <button class="btn ba" id="audio-btn-stop"><i class="fas fa-volume-mute"></i> Stop</button>
          </div>
        </div>
      </div>
    </div>
"""

# Insert after SNN Simulator Wrap
snn_wrap_end = "        </div>\n      </div>\n    </div>"
if 'id="snnAudioCard"' not in content:
    # Need a robust way to find the end of SNN wrap.
    # The wrap starts with <!-- SNN Simulator Wrap -->
    # We can inject right before <!-- SNN Simulator Modal --> or <!-- SNN Matrix Editor Modal --> if it exists.
    # Or just inject right before <!-- SNN Energy Settings Modal --> which I added earlier.
    content = content.replace('<!-- SNN Energy Settings Modal -->', ui_html + '\n<!-- SNN Energy Settings Modal -->')


# Initialize UI on load
init_hook = "if(window.initAudioSynesthesiaUI) window.initAudioSynesthesiaUI();"
if 'initAudioSynesthesiaUI' not in content:
    # put it at the end of window.onload or DOMContentLoaded
    # let's put it right after startSNNSimulator() call if present in index.html, or in a script tag.
    content = content.replace('</body>', f'<script>{init_hook}</script>\n</body>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
