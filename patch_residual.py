import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# Let's find the scatter plot panel to append the residual plot panel after it
scatter_panel = """        <!-- Scatter Plot Panel -->
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
        </div>"""

residual_panel = """
        <!-- Residual Plot Panel -->
        <div style="flex:1; min-width:300px; display:flex; flex-direction:column; background:var(--bg); padding:1rem; border-radius:8px; border:1px solid var(--border);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <span style="font-size:0.85rem; font-weight:bold;">SNN Accuracy Residuals</span>
            <div style="font-size:0.75rem; text-align:right;">
              <div style="color:#888;">Mean: <span id="val-res-mean" style="color:#fff;">0.0%</span> | StdDev: <span id="val-res-std" style="color:#fff;">0.0%</span></div>
              <div style="color:#10b981;">95% CI: <span id="val-res-ci">± 0.0%</span></div>
            </div>
          </div>
          <div style="height:300px; width:100%;">
            <canvas id="validation-residual-chart"></canvas>
          </div>
        </div>"""

if scatter_panel in content:
    content = content.replace(scatter_panel, scatter_panel + '\n' + residual_panel)


# Re-add PDF export lines
pdf_old = """        pdf.setFont('helvetica','normal'); pdf.setFontSize(10);
        let r2 = document.getElementById('val-r2').innerText;
        let mae = document.getElementById('val-mae').innerText;
        pdf.text(`Current Metric -> R2: ${r2} | MAE: ${mae}`, 160, 85, {maxWidth: 40});"""
        
pdf_new = """        pdf.text('SNN Predictor Accuracy Residuals', 15, 140);
        pdf.addImage(window.validationResidualChart.toBase64Image(), 'PNG', 15, 145, 140, 80);
        
        pdf.setFont('helvetica','normal'); pdf.setFontSize(10);
        let ci = document.getElementById('val-res-ci') ? document.getElementById('val-res-ci').innerText : '';
        let r2 = document.getElementById('val-r2').innerText;
        let mae = document.getElementById('val-mae').innerText;
        pdf.text(`Current Metric -> R2: ${r2} | MAE: ${mae}`, 160, 85, {maxWidth: 40});
        if (ci) pdf.text(`95% Confidence Interval: ${ci}`, 160, 185, {maxWidth: 40});"""
        
if pdf_old in content:
    content = content.replace(pdf_old, pdf_new)


with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("index.html patched with residual panel.")
