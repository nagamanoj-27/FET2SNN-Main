import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Insert HTML for lifCard
lif_html = """    <!-- LIF Neuron Module -->
    <div class="card" id="lifCard">
      <div class="ct"><i class="fas fa-wave-square"></i> LIF Neuron Dynamics <span class="ttip" style="margin-left:auto; font-size:0.85rem;">ⓘ<span class="ttip-text">Simulates a single LIF neuron using the FET-derived membrane capacitance, leak conductance, and threshold voltage.</span></span></div>
      
      <!-- Derived Parameters -->
      <div class="pg" style="margin-bottom:1rem;">
        <div class="pi"><div class="pn">C<sub>m</sub></div><div class="pv" id="lif-cm">-</div><div class="pu">fF</div></div>
        <div class="pi"><div class="pn">G<sub>leak</sub></div><div class="pv" id="lif-gleak">-</div><div class="pu">nS</div></div>
        <div class="pi"><div class="pn">τ<sub>m</sub></div><div class="pv" id="lif-taum">-</div><div class="pu">ms</div></div>
        <div class="pi"><div class="pn">t<sub>refractory</sub></div><div class="pv" id="lif-tref">-</div><div class="pu">ms</div></div>
        <div class="pi"><div class="pn">V<sub>th</sub></div><div class="pv" id="lif-vth">-</div><div class="pu">mV</div></div>
        <div class="pi"><div class="pn">Rate</div><div class="pv" id="lif-rate" style="color:var(--green)">-</div><div class="pu">Hz</div></div>
        <div class="pi"><div class="pn">Energy</div><div class="pv" id="lif-espike" style="color:var(--blue)">-</div><div class="pu">fJ/spike</div></div>
      </div>
      
      <!-- Chart -->
      <div style="height:150px; background:var(--bg); border:1px solid var(--border); border-radius:8px; margin-bottom:1rem; padding:5px;">
        <canvas id="chLif"></canvas>
      </div>
      
      <!-- Controls -->
      <div class="isg" style="margin-bottom:1rem;">
        <div class="ig">
          <label>Input Current <span class="u">nA</span></label>
          <div class="sr"><input type="range" id="lif-Iamp" min="0" max="10" step="0.1" value="2"><span class="lv" id="lif-Iamp-val">2</span></div>
        </div>
        <div class="ig">
          <label>Stimulus Duration <span class="u">ms</span></label>
          <div class="sr"><input type="range" id="lif-Idur" min="10" max="500" step="10" value="100"><span class="lv" id="lif-Idur-val">100</span></div>
        </div>
        <div class="ig">
          <label>Noise (StdDev) <span class="u">nA</span></label>
          <div class="sr"><input type="range" id="lif-noise" min="0" max="2" step="0.05" value="0"><span class="lv" id="lif-noise-val">0.00</span></div>
        </div>
        <div class="ig">
          <label>Time Window <span class="u">ms</span></label>
          <div class="sr"><input type="range" id="lif-twin" min="50" max="500" step="10" value="200"><span class="lv" id="lif-twin-val">200</span></div>
        </div>
      </div>
      
      <!-- Buttons -->
      <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
        <button class="btn bb" id="lif-btn-run" style="flex:1"><i class="fas fa-play"></i> Run</button>
        <button class="btn ba" id="lif-btn-pause" style="flex:1"><i class="fas fa-pause"></i> Pause</button>
        <button class="btn bb" id="lif-btn-reset" style="flex:1"><i class="fas fa-undo"></i> Reset</button>
        <button class="btn bb" id="lif-btn-csv" style="flex:1"><i class="fas fa-file-csv"></i> Export CSV</button>
      </div>
    </div>
"""

# Find where to insert (after snnCard closing div)
# We know the structure from earlier:
#      <div class="sent-note" style="margin-top:0.75rem"><i class="fas fa-check-circle" style="color:var(--green)"></i> <strong>Recalibrated (2026):</strong> Analytical models & LightGBM SNN coefficients are now exactly calibrated to the 17-device benchmark dataset using Sentaurus TCAD (MLDA + Lombardi confinement).</div>
#    </div>
#  </div>
# </div><!-- /mg -->

snn_closing_pattern = r'(<div class="sent-note".*?</div>\s*</div>)'
match = re.search(snn_closing_pattern, content)
if match:
    content = content[:match.end()] + "\n" + lif_html + content[match.end():]
else:
    print("Could not find snnCard closing div!")

# 2. Hook into computeAll() and fallbackComputeAll()
hook_code = "if(typeof window.updateLIFModule === 'function') window.updateLIFModule(d, S);"
content = content.replace('updSNN(snn);', 'updSNN(snn);\n    ' + hook_code)

# 3. Add script tag at the end of body, and startLIFSystem() on DOMContentLoaded
script_injection = """
<script src="lif-neuron.js"></script>
<script>
document.addEventListener('DOMContentLoaded', () => {
    if(typeof window.startLIFSystem === 'function') {
        window.startLIFSystem();
    }
});
</script>
</body>
"""
content = content.replace('</body>', script_injection)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected LIF UI and JS hooks!")
