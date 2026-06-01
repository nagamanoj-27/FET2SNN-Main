import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Inject script tag for snn-validation.js
if 'snn-validation.js' not in content:
    content = content.replace('<script src="snn-monte-carlo.js"></script>', '<script src="snn-monte-carlo.js"></script>\n<script src="snn-validation.js"></script>')

# 2. Inject UI Card
ui_html = """
    <!-- Complete Model Validation Suite Card -->
    <div class="card" id="snnValidationCard" style="margin-bottom:1.5rem;">
      <div class="ct" style="display:flex; justify-content:space-between; align-items:center;">
        <span><i class="fas fa-check-double"></i> Model Validation Suite <span class="ttip" style="margin-left:5px; font-size:0.85rem; font-weight:normal;">ⓘ<span class="ttip-text">Validation against 17 benchmark devices. R² and MAE reflect the accuracy of the analytical proxy model vs rigorous TCAD physics.</span></span></span>
        <span style="font-size:0.85rem; color:#888;">Electrical model validation (Vth, SS, Ion) | SNN predictor residuals</span>
      </div>
      
      <div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-bottom:0.5rem;">
        
        <!-- Scatter Plot Panel -->
        <div style="flex:1; min-width:300px; display:flex; flex-direction:column; background:var(--bg); padding:1rem; border-radius:8px; border:1px solid var(--border);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <select id="val-param-sel" onchange="if(window.updateValidationScatter) window.updateValidationScatter(this.value)" style="background:#111; color:#fff; border:1px solid #444; padding:2px 5px; border-radius:4px; font-size:0.85rem;">
              <option value="vth">Vth Scatter Plot</option>
              <option value="ss">Subthreshold Swing (SS)</option>
              <option value="ion">Ion (Drive Current)</option>
            </select>
            <div style="font-size:0.8rem;">
              <span style="margin-right:10px;">R²: <strong id="val-r2" style="color:#10b981;">0.00</strong></span>
              <span>MAE: <strong id="val-mae" style="color:#f97316;">0.00</strong></span>
            </div>
          </div>
          <div style="height:200px; width:100%;">
            <canvas id="validation-scatter-chart"></canvas>
          </div>
        </div>
        
        <!-- Residual Plot Panel -->
        <div style="flex:1; min-width:300px; display:flex; flex-direction:column; background:var(--bg); padding:1rem; border-radius:8px; border:1px solid var(--border);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <span style="font-size:0.85rem; font-weight:bold;">SNN Accuracy Residuals</span>
            <div style="font-size:0.75rem; text-align:right;">
              <div style="color:#888;">Mean: <span id="val-res-mean" style="color:#fff;">0.0%</span> | StdDev: <span id="val-res-std" style="color:#fff;">0.0%</span></div>
              <div style="color:#10b981;">95% CI: <span id="val-res-ci">± 0.0%</span></div>
            </div>
          </div>
          <div style="height:200px; width:100%;">
            <canvas id="validation-residual-chart"></canvas>
          </div>
        </div>
        
      </div>
    </div>
"""

# Find benchmark table insertion point. The benchmark table starts with `<div class="card" style="margin-bottom:1rem">` and contains `id="bTbody"`.
# There is a block `<!-- Export Data & Logs -->` followed by benchmark table? Actually let's just insert it right after `<!-- Monte Carlo Variability & Yield Analyzer Card -->` and its closing `</div>`.
if 'id="snnValidationCard"' not in content:
    # Look for SNN Energy Settings Modal to insert right above it (this is where we put MC Analyzer).
    # Wait, we already inserted MC Analyzer above SNN Energy Settings Modal. Let's insert Validation above SNN Energy Settings Modal as well.
    content = content.replace('<!-- SNN Energy Settings Modal -->', ui_html + '\n<!-- SNN Energy Settings Modal -->')


# 3. Hook fallbackComputeAll
# We need to call `if(window.injectAccuracyErrorBars) window.injectAccuracyErrorBars();` inside fallbackComputeAll
hook_target = """  if(!isPreview && window.triggerTornadoCompute) window.triggerTornadoCompute();
  if(!isPreview && document.getElementById('mc-stale-warning') && window.mcResults && window.mcResults.length > 0) {
      document.getElementById('mc-stale-warning').style.display = 'inline';
  }
}"""

hook_new = """  if(!isPreview && window.triggerTornadoCompute) window.triggerTornadoCompute();
  if(!isPreview && document.getElementById('mc-stale-warning') && window.mcResults && window.mcResults.length > 0) {
      document.getElementById('mc-stale-warning').style.display = 'inline';
  }
  if(window.injectAccuracyErrorBars) window.injectAccuracyErrorBars();
}"""
if hook_target in content:
    content = content.replace(hook_target, hook_new)


# 4. Modify HTML in SNN accuracy card to ensure we don't duplicate the error bars
# The SNN accuracy HTML is currently:
# <span class="sv" id="oSnnAc" style="color:var(--purp)">0 %</span>
# Wait, my snn-validation.js replaces the innerHTML: `accEl.innerHTML = ${val} <span...>± ${ci}%</span>;`
# That should work fine.

# 5. Export PDF modification
pdf_end_old = "pdf.save('FET2SNN_Report.pdf');"
pdf_end_new = """
    if (window.validationScatterChart && window.validationResidualChart) {
        let scImg = window.validationScatterChart.toBase64Image();
        let rsImg = window.validationResidualChart.toBase64Image();
        pdf.addPage();
        pdf.setFont('helvetica','bold'); pdf.setFontSize(16); pdf.setTextColor(30,30,47);
        pdf.text('Complete Model Validation Suite', 15, 20);
        pdf.setFont('helvetica','normal'); pdf.setFontSize(10); pdf.setTextColor(100,100,100);
        pdf.text('Validation of analytical proxy model against 17 rigorously simulated TCAD benchmark devices.', 15, 28);
        
        pdf.setFont('helvetica','bold'); pdf.setTextColor(30,30,47);
        pdf.text('Model vs TCAD Scatter Plot (Vth, SS, Ion)', 15, 40);
        pdf.addImage(scImg, 'PNG', 15, 45, 140, 80);
        
        pdf.text('SNN Predictor Accuracy Residuals', 15, 140);
        pdf.addImage(rsImg, 'PNG', 15, 145, 140, 80);
        
        pdf.setFont('helvetica','normal'); pdf.setFontSize(10);
        let ci = document.getElementById('val-res-ci').innerText;
        let r2 = document.getElementById('val-r2').innerText;
        let mae = document.getElementById('val-mae').innerText;
        pdf.text(`Current Metric -> R2: ${r2} | MAE: ${mae}`, 160, 85, {maxWidth: 40});
        pdf.text(`95% Confidence Interval: ${ci}`, 160, 185, {maxWidth: 40});
    }
    pdf.save('FET2SNN_Report.pdf');"""

if pdf_end_old in content:
    content = content.replace(pdf_end_old, pdf_end_new)

# 6. Initialization logic
ui_init_js = """
// Validation Suite Initialization
document.addEventListener('DOMContentLoaded', () => {
    if(window.initValidationCharts) window.initValidationCharts();
});
"""
content = content.replace('</body>', f'<script>{ui_init_js}</script>\n</body>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched.")
