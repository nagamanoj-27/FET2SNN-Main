import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# Pattern to capture everything from <!-- SNN Simulator Module --> to the end of snnSimCard
pattern = r'(    <!-- SNN Simulator Module -->\s*<div class="card" id="snnSimCard">.*?<button class="btn ba" id="snn-btn-csv-weights".*?</div>\s*</div>)'

match = re.search(pattern, content, re.DOTALL)
if match:
    old_snn_card = match.group(1)
    
    new_html = """
    <!-- SNN Simulator Wrap -->
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.5rem;">
      <!-- Left Card: SNN Controls and Settings -->
      <div class="card" id="snnSimCard" style="flex:1; min-width:300px; margin-bottom:0;">
        <div class="ct"><i class="fas fa-network-wired"></i> SNN Simulator <span class="ttip" style="margin-left:auto; font-size:0.85rem;">ⓘ<span class="ttip-text">Multi-neuron spiking simulator derived from FET biophysics.</span></span></div>
        
        <!-- Stats -->
        <div class="pg" style="margin-bottom:1rem;">
          <div class="pi"><div class="pn">Network Rate</div><div class="pv" id="snn-rate" style="color:var(--green)">0.0</div><div class="pu">Hz</div></div>
          <div class="pi" id="snn-stdp-stats" style="display:none;"><div class="pn">Plasticity Events</div><div class="pv" id="snn-plast-events" style="color:var(--violet)">0</div></div>
        </div>

        <!-- Core Controls -->
        <div class="isg" style="margin-bottom:1rem;">
          <div class="ig">
            <label>Number of Neurons</label>
            <div class="sr"><input type="range" id="snn-n" min="2" max="50" step="1" value="10"><span class="lv" id="snn-n-val">10</span></div>
          </div>
          <div class="ig">
            <label>Sim Time Window <span class="u">ms</span></label>
            <div class="sr"><input type="range" id="snn-twin" min="100" max="1000" step="10" value="200"><span class="lv" id="snn-twin-val">200</span></div>
          </div>
          <div class="ig">
            <label>Time step (dt) <span class="u">ms</span></label>
            <div class="sr"><input type="range" id="snn-dt" min="0.1" max="1.0" step="0.1" value="0.5"><span class="lv" id="snn-dt-val">0.5</span></div>
          </div>
          <div class="ig">
            <label>Speed Multiplier</label>
            <div class="sr"><input type="range" id="snn-speed" min="0.5" max="2" step="0.5" value="1"><span class="lv" id="snn-speed-val">1</span></div>
          </div>
        </div>
        
        <!-- Mode Switcher -->
        <div style="margin-bottom:1rem; padding:10px; background:var(--card-h); border:1px solid var(--border); border-radius:8px;">
          <label style="font-weight:bold; margin-right:15px;">Weight mode:</label>
          <label style="margin-right:15px;"><input type="radio" name="snnMode" value="manual" checked> Manual</label>
          <label><input type="radio" name="snnMode" value="stdp"> STDP</label>
        </div>
        
        <!-- Manual Controls -->
        <div id="snn-manual-controls" style="margin-bottom:1rem;">
          <div style="display:flex; gap:10px; align-items:center;">
            <select id="snn-init-method" style="padding:5px; border-radius:4px; border:1px solid var(--border); background:var(--bg); color:var(--text);">
              <option value="uniform">Uniform random</option>
              <option value="constant">Constant</option>
              <option value="sparse">Random sparse</option>
            </select>
            <button class="btn bb" id="snn-btn-edit-matrix"><i class="fas fa-edit"></i> Edit matrix</button>
          </div>
        </div>
        
        <!-- STDP Controls -->
        <div id="snn-stdp-controls" class="isg" style="display:none; margin-bottom:1rem;">
          <div class="ig"><label>A+ <span class="u">L.R.</span></label><div class="sr"><input type="range" id="snn-ap" min="0" max="0.1" step="0.001" value="0.01"><span class="lv" id="snn-ap-val">0.010</span></div></div>
          <div class="ig"><label>A- <span class="u">L.R.</span></label><div class="sr"><input type="range" id="snn-am" min="0" max="0.1" step="0.001" value="0.012"><span class="lv" id="snn-am-val">0.012</span></div></div>
          <div class="ig"><label>τ+ <span class="u">ms</span></label><div class="sr"><input type="range" id="snn-taup" min="5" max="50" step="1" value="20"><span class="lv" id="snn-taup-val">20</span></div></div>
          <div class="ig"><label>τ- <span class="u">ms</span></label><div class="sr"><input type="range" id="snn-taum" min="5" max="50" step="1" value="20"><span class="lv" id="snn-taum-val">20</span></div></div>
        </div>

        <!-- Action Buttons -->
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:auto;">
          <button class="btn bb" id="snn-btn-run" style="flex:1"><i class="fas fa-play"></i> Run</button>
          <button class="btn ba" id="snn-btn-pause" style="flex:1"><i class="fas fa-pause"></i> Pause</button>
          <button class="btn bb" id="snn-btn-reset" style="flex:1"><i class="fas fa-undo"></i> Reset</button>
        </div>
      </div>
      
      <!-- Right Card: SNN Visuals -->
      <div class="card" id="snnVisualsCard" style="flex:1; min-width:300px; margin-bottom:0; display:flex; flex-direction:column;">
        <div class="ct"><i class="fas fa-chart-area"></i> Network Visualizations</div>
        
        <!-- Visuals Grid -->
        <div style="display:flex; gap:1rem; margin-bottom:1rem; flex-wrap:wrap;">
          <!-- Spike Raster -->
          <div style="flex:2; min-width:250px;">
            <label style="font-weight:bold; font-size:0.9rem;">Spike Raster</label>
            <div style="height:150px; background:var(--bg); border:1px solid var(--border); border-radius:8px;">
              <canvas id="snnCanvasRaster" width="500" height="150" style="width:100%; height:100%;"></canvas>
            </div>
          </div>
          <!-- Weight Matrix -->
          <div style="flex:1; min-width:150px;">
            <label style="font-weight:bold; font-size:0.9rem;">Weight Matrix</label>
            <div style="aspect-ratio:1/1; background:var(--bg); border:1px solid var(--border); border-radius:8px; display:flex; align-items:center; justify-content:center;">
              <canvas id="snnCanvasHeatmap" width="100" height="100" style="width:90%; height:90%; image-rendering:pixelated;"></canvas>
            </div>
          </div>
        </div>
        
        <!-- Single Neuron Trace -->
        <div style="flex:1; display:flex; flex-direction:column; margin-bottom:1rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
              <label style="font-weight:bold; font-size:0.9rem;">Membrane Potential</label>
              <select id="snn-sel-neuron" style="padding:2px 5px; border-radius:4px; border:1px solid var(--border); background:var(--bg); color:var(--text);"></select>
          </div>
          <div style="flex:1; min-height:120px; background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:5px;">
              <canvas id="chSnnTrace"></canvas>
          </div>
        </div>
        
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:auto;">
          <button class="btn ba" id="snn-btn-csv-raster" style="flex:1"><i class="fas fa-file-csv"></i> Raster CSV</button>
          <button class="btn ba" id="snn-btn-csv-weights" style="flex:1"><i class="fas fa-file-csv"></i> Weights CSV</button>
        </div>
      </div>
    </div>
    """
    
    new_content = content[:match.start()] + new_html + content[match.end():]
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully split SNN Simulator into two columns!")
else:
    print("Could not find the SNN Simulator block pattern!")
