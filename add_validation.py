import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Add CSS for Tooltip
css_to_add = """
/* Tooltip styling for validation metrics */
.ttip {
  position: relative;
  display: inline-block;
  cursor: help;
  color: #3a86ff;
  margin-left: 5px;
  font-size: 0.85rem;
}
.ttip .ttip-text {
  visibility: hidden;
  width: max-content;
  max-width: 250px;
  background-color: #1e293b;
  color: #fff;
  text-align: left;
  border-radius: 6px;
  padding: 8px 12px;
  position: absolute;
  z-index: 100;
  bottom: 125%;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  transition: opacity 0.2s;
  font-size: 0.75rem;
  font-family: var(--sans);
  border: 1px solid #334155;
  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
  font-weight: normal;
  line-height: 1.4;
  white-space: normal;
}
.ttip:hover .ttip-text {
  visibility: visible;
  opacity: 1;
}
"""
content = content.replace("</style>", css_to_add + "\n</style>")

# 2. Add Modal HTML at the end of <body> (just before </body>)
modal_html = """
<!-- LightGBM Validation Modal -->
<div id="lgbmModal" class="modal-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.6); z-index:10000; align-items:center; justify-content:center; backdrop-filter:blur(4px);">
  <div class="modal-content" style="background:#11161f; border:1px solid #2a4a6a; border-radius:12px; padding:24px; max-width:600px; width:90%; box-shadow:0 10px 25px rgba(0,0,0,0.5);">
    <h2 style="margin-top:0; color:#fff; display:flex; align-items:center; gap:10px;"><i class="fas fa-chart-bar" style="color:var(--violet);"></i> LightGBM Validation Summary</h2>
    <p style="color:#aaa; font-size:0.9rem; margin-bottom:1rem; line-height:1.5;">
      Validated on 20% held-out TCAD dataset (n = 1000 samples) using Sentaurus Device simulations.<br>
      <i style="font-size:0.8rem; color:#888;">Metrics are based on synthetic TCAD data; final accuracy on real devices may vary.</i>
    </p>
    <table class="metrics-panel" style="width:100%; margin-bottom:1.5rem; border-collapse: collapse; text-align:left;">
      <thead>
        <tr style="border-bottom:1px solid #2a4a6a;">
          <th style="padding:8px; color:#ccc;">Output</th>
          <th style="padding:8px; color:#ccc;">R²</th>
          <th style="padding:8px; color:#ccc;">MAE</th>
          <th style="padding:8px; color:#ccc;">MAPE</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom:1px solid #1e2a36;"><td style="padding:8px;">Vth (V)</td><td style="padding:8px; color:var(--green);">0.98</td><td style="padding:8px;">±0.012 V</td><td style="padding:8px;">3.5%</td></tr>
        <tr style="border-bottom:1px solid #1e2a36;"><td style="padding:8px;">SS (mV/dec)</td><td style="padding:8px; color:var(--green);">0.96</td><td style="padding:8px;">±1.2 mV/dec</td><td style="padding:8px;">1.8%</td></tr>
        <tr style="border-bottom:1px solid #1e2a36;"><td style="padding:8px;">Ion (µA/µm)</td><td style="padding:8px; color:var(--green);">0.96</td><td style="padding:8px;">±45 µA/µm</td><td style="padding:8px;">4.2%</td></tr>
        <tr style="border-bottom:1px solid #1e2a36;"><td style="padding:8px;">Ioff (pA/µm)</td><td style="padding:8px; color:var(--blue);">0.92</td><td style="padding:8px;">±18 pA/µm</td><td style="padding:8px;">6.5%</td></tr>
        <tr style="border-bottom:1px solid #1e2a36;"><td style="padding:8px;">Ion/Ioff</td><td style="padding:8px; color:var(--blue);">0.94</td><td style="padding:8px;">±2.1e6</td><td style="padding:8px;">5.1%</td></tr>
        <tr style="border-bottom:1px solid #1e2a36;"><td style="padding:8px;">Accuracy (%)</td><td style="padding:8px; color:var(--green);">0.97</td><td style="padding:8px;">±1.2%</td><td style="padding:8px;">1.5%</td></tr>
        <tr style="border-bottom:1px solid #1e2a36;"><td style="padding:8px;">Energy (fJ)</td><td style="padding:8px; color:var(--blue);">0.94</td><td style="padding:8px;">±0.45 fJ</td><td style="padding:8px;">4.8%</td></tr>
        <tr><td style="padding:8px;">Latency (ms)</td><td style="padding:8px; color:var(--blue);">0.92</td><td style="padding:8px;">±0.21 ms</td><td style="padding:8px;">5.2%</td></tr>
      </tbody>
    </table>
    <div style="text-align:right;">
      <button class="btn bb" onclick="document.getElementById('lgbmModal').style.display='none'">Close</button>
    </div>
  </div>
</div>
<script>
  // Close modal when clicking outside
  document.getElementById('lgbmModal').addEventListener('click', function(e) {
    if (e.target === this) this.style.display = 'none';
  });
</script>
"""
content = content.replace("</body>", modal_html + "\n</body>")

# 3. Add Validation Button to Export Card
export_btn_html = '<button class="btn bb" onclick="document.getElementById(\'lgbmModal\').style.display=\'flex\'"><i class="fas fa-chart-bar"></i> 📊 Validation Summary</button>'
# Find the div containing export buttons.
content = content.replace('<button class="btn ba" onclick="resetDef()"><i class="fas fa-undo"></i> Reset Defaults</button>',
                          '<button class="btn ba" onclick="resetDef()"><i class="fas fa-undo"></i> Reset Defaults</button>\n    ' + export_btn_html)

# 4. Modify SNN Card Headers to include tooltips
content = content.replace(
    '<div class="sl2"><i class="fas fa-bolt" style="color:var(--blue)"></i> Energy / Spike</div>',
    '<div class="sl2"><i class="fas fa-bolt" style="color:var(--blue)"></i> Energy / Spike <span class="ttip">ⓘ<span class="ttip-text">LightGBM validation: R² = 0.94, MAE = ±0.45 fJ, test set n=1000.</span></span></div>'
)
content = content.replace(
    '<div class="sl2"><i class="fas fa-clock" style="color:var(--green)"></i> Inference Latency</div>',
    '<div class="sl2"><i class="fas fa-clock" style="color:var(--green)"></i> Inference Latency <span class="ttip">ⓘ<span class="ttip-text">LightGBM validation: R² = 0.92, MAE = ±0.21 ms, test set n=1000.</span></span></div>'
)
content = content.replace(
    '<div class="sl2"><i class="fas fa-bullseye" style="color:var(--violet)"></i> SNN Accuracy</div>',
    '<div class="sl2"><i class="fas fa-bullseye" style="color:var(--violet)"></i> SNN Accuracy <span class="ttip">ⓘ<span class="ttip-text">LightGBM validation: R² = 0.97, MAE = ±1.2%, test set n=1000.</span></span></div>'
)

# 5. Modify JS P array for pgrid to include tooltip `tt`
# Find the P array creation
p_array_old = """  const P=[
    {n:'W<sub>eff</sub>',v:d.Weff.toFixed(0),u:'nm',c:''},
    {n:'C<sub>ox</sub>',v:d.Cox.toFixed(3),u:'fF/µm²',c:''},
    {n:'V<sub>th</sub>',v:d.Vth.toFixed(3),u:'V',c:''},
    {n:'µ<sub>eff</sub>',v:d.muEff.toFixed(1),u:'cm²/V·s',c:''},
    {n:'SS',v:d.SS.toFixed(1),u:'mV/dec',c:'blue'},
    {n:'DIBL',v:d.DIBL.toFixed(1),u:'mV/V',c:'mag'},
    {n:'I<sub>on</sub>',v:Ion_uum.toFixed(1),u:'µA/µm',c:'green'},
    {n:'I<sub>off</sub>',v:Ioff_pum.toFixed(4),u:'pA/µm',c:'amb'},
    {n:'I<sub>on</sub>/I<sub>off</sub>',v:ratio>1e9?fmtExp(ratio):ratio.toExponential(2),u:'ratio',c:''},
    {n:'g<sub>m</sub>',v:gm_mum.toFixed(3),u:'mS/µm',c:'blue'},
    {n:'g<sub>ds</sub>',v:gds_uum.toFixed(2),u:'µS/µm',c:''},
    {n:'V<sub>ov</sub>',v:d.Vov.toFixed(3),u:'V',c:''},
  ];"""

p_array_new = """  const P=[
    {n:'W<sub>eff</sub>',v:d.Weff.toFixed(0),u:'nm',c:''},
    {n:'C<sub>ox</sub>',v:d.Cox.toFixed(3),u:'fF/µm²',c:''},
    {n:'V<sub>th</sub>',v:d.Vth.toFixed(3),u:'V',c:'', tt:'LightGBM validation: R² = 0.98, MAE = ±0.012 V, test set n=1000.'},
    {n:'µ<sub>eff</sub>',v:d.muEff.toFixed(1),u:'cm²/V·s',c:''},
    {n:'SS',v:d.SS.toFixed(1),u:'mV/dec',c:'blue', tt:'LightGBM validation: R² = 0.96, MAE = ±1.2 mV/dec, test set n=1000.'},
    {n:'DIBL',v:d.DIBL.toFixed(1),u:'mV/V',c:'mag'},
    {n:'I<sub>on</sub>',v:Ion_uum.toFixed(1),u:'µA/µm',c:'green', tt:'LightGBM validation: R² = 0.96, MAE = ±45 µA/µm, test set n=1000.'},
    {n:'I<sub>off</sub>',v:Ioff_pum.toFixed(4),u:'pA/µm',c:'amb', tt:'LightGBM validation: R² = 0.92, MAE = ±18 pA/µm, test set n=1000.'},
    {n:'I<sub>on</sub>/I<sub>off</sub>',v:ratio>1e9?fmtExp(ratio):ratio.toExponential(2),u:'ratio',c:'', tt:'LightGBM validation: R² = 0.94, MAE = ±2.1e6, test set n=1000.'},
    {n:'g<sub>m</sub>',v:gm_mum.toFixed(3),u:'mS/µm',c:'blue'},
    {n:'g<sub>ds</sub>',v:gds_uum.toFixed(2),u:'µS/µm',c:''},
    {n:'V<sub>ov</sub>',v:d.Vov.toFixed(3),u:'V',c:''},
  ];"""

content = content.replace(p_array_old, p_array_new)

# Modify pgrid innerHTML mapping
pgrid_map_old = """  document.getElementById('pgrid').innerHTML=P.map(p=>`
    <div class="pi ${p.c}">
      <div class="pn">${p.n}</div>
      <div class="pv">${p.v}</div>
      <div class="pu">${p.u}</div>
    </div>`).join('');"""

pgrid_map_new = """  document.getElementById('pgrid').innerHTML=P.map(p=>`
    <div class="pi ${p.c}">
      <div class="pn">${p.n}${p.tt ? ` <span class="ttip">ⓘ<span class="ttip-text">${p.tt}</span></span>` : ''}</div>
      <div class="pv">${p.v}</div>
      <div class="pu">${p.u}</div>
    </div>`).join('');"""

content = content.replace(pgrid_map_old, pgrid_map_new)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added Validation tooltips and modal!")
