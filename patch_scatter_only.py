import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# Remove Residual Plot Panel
residual_panel_pattern = re.compile(r'<!-- Residual Plot Panel -->\s*<div style="flex:1; min-width:300px; display:flex; flex-direction:column; background:var\(--bg\); padding:1rem; border-radius:8px; border:1px solid var\(--border\);">.*?</div>\s*</div>\s*</div>\s*</div>', re.DOTALL)

# Let's do it carefully.
# We want to replace the flex container containing both panels with just the scatter plot panel.
scatter_panel = """      <div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-bottom:0.5rem;">
        
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
          <div style="height:300px; width:100%;">
            <canvas id="validation-scatter-chart"></canvas>
          </div>
        </div>
        
      </div>
    </div>
</div>"""

# I'll just find the start of the panels: `<div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-bottom:0.5rem;">` and end it after scatter plot panel.
target_pattern = re.compile(r'<div style="display:flex; gap:1\.5rem; flex-wrap:wrap; margin-bottom:0\.5rem;">(.*?)</div>\s*</div>\s*</div>\s*</div>', re.DOTALL)
if re.search(target_pattern, content):
    content = re.sub(target_pattern, scatter_panel[70:], content)

# Remove PDF export residual code
pdf_old = """        pdf.text('SNN Predictor Accuracy Residuals', 15, 140);
        pdf.addImage(rsImg, 'PNG', 15, 145, 140, 80);
        
        pdf.setFont('helvetica','normal'); pdf.setFontSize(10);
        let ci = document.getElementById('val-res-ci').innerText;
        let r2 = document.getElementById('val-r2').innerText;
        let mae = document.getElementById('val-mae').innerText;
        pdf.text(`Current Metric -> R2: ${r2} | MAE: ${mae}`, 160, 85, {maxWidth: 40});
        pdf.text(`95% Confidence Interval: ${ci}`, 160, 185, {maxWidth: 40});"""
        
pdf_new = """        pdf.setFont('helvetica','normal'); pdf.setFontSize(10);
        let r2 = document.getElementById('val-r2').innerText;
        let mae = document.getElementById('val-mae').innerText;
        pdf.text(`Current Metric -> R2: ${r2} | MAE: ${mae}`, 160, 85, {maxWidth: 40});"""
if pdf_old in content:
    content = content.replace(pdf_old, pdf_new)

if 'let rsImg = window.validationResidualChart.toBase64Image();' in content:
    content = content.replace('let rsImg = window.validationResidualChart.toBase64Image();', '')

# Remove hook for injectAccuracyErrorBars
if 'if(window.injectAccuracyErrorBars) window.injectAccuracyErrorBars();' in content:
    content = content.replace('if(window.injectAccuracyErrorBars) window.injectAccuracyErrorBars();', '')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("index.html patched.")
