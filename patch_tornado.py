import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Inject script tag for snn-tornado.js
if 'snn-tornado.js' not in content:
    content = content.replace('<script src="snn-aging.js"></script>', '<script src="snn-aging.js"></script>\n<script src="snn-tornado.js"></script>')

# 2. Inject UI Card
ui_html = """
    <!-- Sensitivity Analysis (Tornado Chart) Card -->
    <div class="card" id="snnTornadoCard" style="margin-bottom:1.5rem;">
      <div class="ct" style="display:flex; justify-content:space-between; align-items:center;">
        <span><i class="fas fa-wind"></i> Sensitivity Analysis (Tornado Chart) <span class="ttip" style="margin-left:5px; font-size:0.85rem; font-weight:normal;">ⓘ<span class="ttip-text">Shows how ±10% change in each parameter affects SNN accuracy. Hover over a bar to preview the effect across the dashboard.</span></span></span>
        <label style="display:flex; align-items:center; gap:5px; font-size:0.9rem; font-weight:bold; cursor:pointer;">
          <input type="checkbox" id="tornado-enable" checked style="width:16px; height:16px;"> Auto-refresh
        </label>
      </div>
      
      <div style="display:flex; gap:1.5rem; flex-wrap:wrap; align-items:center;">
        <div style="flex:1; min-width:250px;">
          <div style="font-size:0.9rem; margin-bottom:1rem; color:var(--text); display:flex; justify-content:space-between;">
            <span>Baseline Accuracy: <strong id="tornado-base-acc" style="color:#10b981;">0.0%</strong></span>
            <button id="tornado-reset-btn" class="btn bb" style="padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="if(window.resetTornadoHighlight) window.resetTornadoHighlight()"><i class="fas fa-undo"></i> Reset Highlight</button>
          </div>
          <div style="background:var(--bg); border:1px solid var(--border); padding:1rem; border-radius:8px; font-size:0.9rem;">
            <div style="font-weight:bold; margin-bottom:0.3rem;"><i class="fas fa-exclamation-triangle" style="color:#f97316;"></i> Most Sensitive Parameter:</div>
            <div id="tornado-most-sensitive" style="color:#66ccff; font-weight:bold;">Calculating...</div>
          </div>
        </div>
        
        <div style="flex:2; min-width:300px; height: 250px;">
          <canvas id="chSnnTornado"></canvas>
        </div>
      </div>
    </div>
"""

# Insert under SNN Performance vs Device Parameters or near Aging
if 'id="snnTornadoCard"' not in content:
    content = content.replace('<!-- Device Aging & Reliability Projector Card -->', ui_html + '\n<!-- Device Aging & Reliability Projector Card -->')


# 3. Modify fallbackComputeAll
old_compute = """function fallbackComputeAll() {
  let d=computeDevice(S);
  if(window.updateAgingCurve) window.updateAgingCurve(d, S);
  if(window.agingEnabled) d = window.applyAging(d, window.agingYears);"""

new_compute = """function fallbackComputeAll(isPreview = false) {
  let activeS = window.tempOverrideParams || S;
  let d=computeDevice(activeS);
  if(!isPreview && window.updateAgingCurve) window.updateAgingCurve(d, activeS);
  if(window.agingEnabled) d = window.applyAging(d, window.agingYears);"""

if old_compute in content:
    content = content.replace(old_compute, new_compute)

old_compute_snn = """  const snn=computeSNN(d,S);
  if(window.updateAgingUI) window.updateAgingUI(d.health || "Excellent", snn);"""

new_compute_snn = """  const snn=computeSNN(d,activeS);
  if(window.updateAgingUI) window.updateAgingUI(d.health || "Excellent", snn);"""

if old_compute_snn in content:
    content = content.replace(old_compute_snn, new_compute_snn)

old_hooks = """  updParams(d);
  updSNN(snn);
    if(typeof window.updateLIFModule === 'function') window.updateLIFModule(d, S);
    if(typeof window.updateSNNSimulator === 'function') window.updateSNNSimulator(d, S);
  updTransfer(d);
  updOutput(d);
  updSpacer();
  updExtraCharts();
  if(document.getElementById('cbParetoCurrent')?.checked && charts.par.data.datasets[0].data.length>0) runPareto();
  if(netVis) updNetlist(d);
  if(typeof window.update3DModel === 'function') window.update3DModel();
  if(typeof window.updateBandDiagram === 'function') window.updateBandDiagram(d.Vth, S.Vdd);
  if(typeof window.updateRasterParams === 'function') window.updateRasterParams(snn.E, snn.L);
}"""

new_hooks = """  updParams(d);
  updSNN(snn);
    if(typeof window.updateLIFModule === 'function') window.updateLIFModule(d, activeS);
    if(typeof window.updateSNNSimulator === 'function') window.updateSNNSimulator(d, activeS);
  updTransfer(d);
  updOutput(d);
  updSpacer();
  updExtraCharts();
  if(document.getElementById('cbParetoCurrent')?.checked && charts.par.data.datasets[0].data.length>0) runPareto();
  if(netVis) updNetlist(d);
  if(typeof window.update3DModel === 'function') window.update3DModel();
  if(typeof window.updateBandDiagram === 'function') window.updateBandDiagram(d.Vth, activeS.Vdd);
  if(typeof window.updateRasterParams === 'function') window.updateRasterParams(snn.E, snn.L);
  
  if(!isPreview && window.triggerTornadoCompute) window.triggerTornadoCompute();
}"""

if old_hooks in content:
    content = content.replace(old_hooks, new_hooks)

# 4. Modify HTML in SNN accuracy card to support highlight text
snn_acc_old = """<div class="sc"><i class="fas fa-bullseye" style="color:var(--purp)"></i> <span>SNN Accuracy</span><span class="sv" id="oSnnAc" style="color:var(--purp)">0 %</span></div>"""
snn_acc_new = """<div class="sc" style="position:relative;">
            <i class="fas fa-bullseye" style="color:var(--purp)"></i> <span>SNN Accuracy</span><span class="sv" id="oSnnAc" style="color:var(--purp)">0 %</span>
            <div id="snn-acc-highlight" style="position:absolute; top:-25px; right:0; background:rgba(231,76,60,0.9); color:#fff; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:bold; opacity:0; transition:opacity 0.2s; pointer-events:none; white-space:nowrap;">Preview</div>
          </div>"""
if snn_acc_old in content:
    content = content.replace(snn_acc_old, snn_acc_new)

# 5. Export PDF modification
pdf_end_old = "pdf.save('FET2SNN_Report.pdf');"
pdf_end_new = """
    if (window.tornadoChart) {
        let tImg = window.tornadoChart.toBase64Image();
        pdf.addPage();
        pdf.setFont('helvetica','bold'); pdf.setFontSize(16); pdf.setTextColor(30,30,47);
        pdf.text('Sensitivity Analysis (Tornado Chart)', 15, 20);
        pdf.setFont('helvetica','normal'); pdf.setFontSize(10); pdf.setTextColor(100,100,100);
        pdf.text('Shows how +/-10% change in each device parameter affects SNN accuracy.', 15, 28);
        pdf.addImage(tImg, 'PNG', 15, 35, 180, 100);
        
        let mst = document.getElementById('tornado-most-sensitive');
        if (mst) {
            pdf.setFont('helvetica','bold'); pdf.setTextColor(231, 76, 60);
            pdf.text('Most Sensitive Parameter: ' + mst.innerText, 15, 145);
        }
    }
    pdf.save('FET2SNN_Report.pdf');"""

if pdf_end_old in content:
    content = content.replace(pdf_end_old, pdf_end_new)


# 6. Initialization logic
ui_init_js = """
// Tornado Initialization
document.addEventListener('DOMContentLoaded', () => {
    if(window.initTornadoChart) window.initTornadoChart();
    const chk = document.getElementById('tornado-enable');
    if (chk) {
        chk.addEventListener('change', (e) => {
            window.tornadoEnabled = e.target.checked;
            if(window.tornadoEnabled && typeof fallbackComputeAll === 'function') fallbackComputeAll();
        });
    }
});
"""
content = content.replace('</body>', f'<script>{ui_init_js}</script>\n</body>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched.")
