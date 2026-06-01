import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# I want to add the Energy Breakdown Pie chart right next to the Single Neuron Trace
# Let's wrap the Single Neuron Trace in a flex container so they sit side by side.
# Current single neuron trace HTML:
#         <!-- Single Neuron Trace -->
#         <div style="flex:1; display:flex; flex-direction:column; margin-bottom:1rem;">
#           <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
#               <label style="font-weight:bold; font-size:0.9rem;">Membrane Potential</label>
#               <select id="snn-sel-neuron" style="padding:2px 5px; border-radius:4px; border:1px solid var(--border); background:var(--bg); color:var(--text);"></select>
#           </div>
#           <div style="flex:1; min-height:120px; background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:5px;">
#               <canvas id="chSnnTrace"></canvas>
#           </div>
#         </div>

# We will replace that with a grid containing both Trace and Pie Chart.
trace_html = """        <!-- Single Neuron Trace -->
        <div style="flex:1; display:flex; flex-direction:column; margin-bottom:1rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
              <label style="font-weight:bold; font-size:0.9rem;">Membrane Potential</label>
              <select id="snn-sel-neuron" style="padding:2px 5px; border-radius:4px; border:1px solid var(--border); background:var(--bg); color:var(--text);"></select>
          </div>
          <div style="flex:1; min-height:120px; background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:5px;">
              <canvas id="chSnnTrace"></canvas>
          </div>
        </div>"""

new_trace_and_pie_html = """        <!-- Trace and Energy Row -->
        <div style="display:flex; gap:1rem; margin-bottom:1rem; flex-wrap:wrap;">
          
          <!-- Single Neuron Trace -->
          <div style="flex:2; display:flex; flex-direction:column; min-width:250px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                <label style="font-weight:bold; font-size:0.9rem;">Membrane Potential</label>
                <select id="snn-sel-neuron" style="padding:2px 5px; border-radius:4px; border:1px solid var(--border); background:var(--bg); color:var(--text);"></select>
            </div>
            <div style="flex:1; min-height:120px; background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:5px;">
                <canvas id="chSnnTrace"></canvas>
            </div>
          </div>
          
          <!-- Energy Breakdown -->
          <div style="flex:1; display:flex; flex-direction:column; min-width:200px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                <label style="font-weight:bold; font-size:0.9rem;">Energy Breakdown <span class="ttip">ⓘ<span class="ttip-text">Total energy accumulated across the network over the time window.</span></span></label>
                <button id="snn-btn-energy-settings" style="background:transparent; border:none; color:var(--text); cursor:pointer;"><i class="fas fa-cog"></i></button>
            </div>
            <div style="flex:1; min-height:120px; background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:5px; position:relative; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                <canvas id="chSnnEnergy"></canvas>
                <div id="snn-energy-total" style="position:absolute; bottom:5px; font-size:0.8rem; font-weight:bold; color:var(--text);">0.00 pJ</div>
            </div>
          </div>

        </div>"""

if trace_html in content:
    content = content.replace(trace_html, new_trace_and_pie_html)
    print("Injected Pie Chart HTML into Trace row.")
else:
    print("Could not find the Single Neuron Trace block!")


# Inject Energy Settings Modal
modal_html = """
<!-- SNN Energy Settings Modal -->
<div id="snnEnergyModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:9999; justify-content:center; align-items:center;">
  <div class="card" style="width:300px; padding:1.5rem;">
    <div class="ct" style="margin-bottom:1rem;"><i class="fas fa-bolt"></i> Energy Model Settings</div>
    
    <div class="isg" style="margin-bottom:1rem;">
      <div class="ig">
        <label>Synaptic coefficient (pJ/spike)</label>
        <div class="sr"><input type="range" id="energy-syn" min="0" max="0.5" step="0.01" value="0.1"><span class="lv" id="energy-syn-val">0.10</span></div>
      </div>
      <div class="ig">
        <label>Overhead (pJ/spike)</label>
        <div class="sr"><input type="range" id="energy-overhead" min="0" max="0.2" step="0.01" value="0.05"><span class="lv" id="energy-overhead-val">0.05</span></div>
      </div>
      <div class="ig">
        <label>Averaging window (ms)</label>
        <div class="sr"><input type="range" id="energy-twin" min="100" max="1000" step="50" value="200"><span class="lv" id="energy-twin-val">200</span></div>
      </div>
    </div>
    
    <div style="display:flex; justify-content:flex-end; gap:0.5rem;">
      <button class="btn bb" id="snn-btn-close-energy"><i class="fas fa-check"></i> Done</button>
    </div>
  </div>
</div>
"""
# insert before </body>
content = content.replace('</body>', modal_html + '\n</body>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
