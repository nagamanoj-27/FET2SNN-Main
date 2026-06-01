import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Inject script tag for snn-monte-carlo.js
if 'snn-monte-carlo.js' not in content:
    content = content.replace('<script src="snn-tornado.js"></script>', '<script src="snn-tornado.js"></script>\n<script src="snn-monte-carlo.js"></script>')

# 2. Inject UI Card
ui_html = """
    <!-- Monte Carlo Variability & Yield Analyzer Card -->
    <div class="card" id="snnMonteCarloCard" style="margin-bottom:1.5rem;">
      <div class="ct" style="display:flex; justify-content:space-between; align-items:center;">
        <span><i class="fas fa-dice"></i> Monte Carlo Variability & Yield Analyzer <span class="ttip" style="margin-left:5px; font-size:0.85rem; font-weight:normal;">ⓘ<span class="ttip-text">Simulates manufacturing process variations to compute robust neuromorphic yield. Used for research publication plots.</span></span></span>
        <span id="mc-stale-warning" style="color:#ef4444; font-size:0.8rem; font-weight:bold; display:none;"><i class="fas fa-exclamation-triangle"></i> Parameters changed - Re-run required</span>
      </div>
      
      <div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-bottom:1rem; background:var(--bg); padding:1rem; border-radius:8px; border:1px solid var(--border);">
        <div style="flex:1; min-width:200px;">
          <div style="font-weight:bold; margin-bottom:0.5rem; font-size:0.85rem; color:var(--text);">Parameters to Vary:</div>
          <div style="display:flex; flex-wrap:wrap; gap:10px; font-size:0.85rem;">
            <label><input type="checkbox" class="mc-param-chk" value="Lg" checked> Gate Length</label>
            <label><input type="checkbox" class="mc-param-chk" value="Vdd" checked> Vdd</label>
            <label><input type="checkbox" class="mc-param-chk" value="EOT" checked> Oxide Thk.</label>
            <label><input type="checkbox" class="mc-param-chk" value="T"> Temp</label>
            <label><input type="checkbox" class="mc-param-chk" value="Wns"> Width</label>
          </div>
        </div>
        
        <div style="flex:1; min-width:150px;">
          <div style="font-weight:bold; margin-bottom:0.5rem; font-size:0.85rem; color:var(--text);">Variation Amount:</div>
          <div style="display:flex; gap:10px; font-size:0.85rem; margin-bottom:5px;">
            <label><input type="radio" name="mc-var-type" value="abs"> Absolute</label>
            <label><input type="radio" name="mc-var-type" value="rel" checked> Relative (±%)</label>
          </div>
          <input type="number" id="mc-var-amount" value="5" style="width:80px; padding:2px; font-size:0.85rem; background:#111; color:#fff; border:1px solid #444; border-radius:4px;"> 
        </div>
        
        <div style="flex:1; min-width:150px;">
          <div style="font-weight:bold; margin-bottom:0.5rem; font-size:0.85rem; color:var(--text);">Distribution:</div>
          <div style="display:flex; flex-direction:column; gap:5px; font-size:0.85rem;">
            <label><input type="radio" name="mc-var-dist" value="norm" checked> Normal (Gaussian)</label>
            <label><input type="radio" name="mc-var-dist" value="unif"> Uniform</label>
          </div>
        </div>
        
        <div style="flex:1; min-width:150px;">
          <div style="display:flex; flex-direction:column; gap:10px;">
            <div>
              <span style="font-size:0.85rem;">Samples: </span>
              <input type="number" id="mc-samples" value="200" min="50" max="1000" style="width:60px; padding:2px; font-size:0.85rem; background:#111; color:#fff; border:1px solid #444; border-radius:4px;">
            </div>
            <div>
              <span style="font-size:0.85rem;">Target Acc (%): </span>
              <input type="number" id="mc-threshold" value="80" min="1" max="100" style="width:60px; padding:2px; font-size:0.85rem; background:#111; color:#fff; border:1px solid #444; border-radius:4px;">
            </div>
          </div>
        </div>
      </div>
      
      <div style="display:flex; gap:10px; align-items:center; margin-bottom:1rem;">
        <button class="btn" style="background:var(--purp); border:none;" onclick="if(window.startMonteCarlo) window.startMonteCarlo()"><i class="fas fa-play"></i> Run Monte Carlo</button>
        <button class="btn bb" onclick="if(window.cancelMonteCarlo) window.cancelMonteCarlo()"><i class="fas fa-stop"></i> Cancel</button>
        <div style="flex:1; margin-left:1rem; height:12px; background:#2a2a3a; border-radius:6px; overflow:hidden; position:relative;">
          <div id="mc-progress-bar" style="height:100%; width:0%; background:#10b981; transition:width 0.1s;"></div>
          <div id="mc-progress-text" style="position:absolute; top:0; left:50%; transform:translateX(-50%); font-size:0.6rem; color:#fff; line-height:12px; font-weight:bold;">0%</div>
        </div>
      </div>
      
      <div style="display:flex; gap:1.5rem; flex-wrap:wrap;">
        <div style="flex:2; min-width:350px; height:250px;">
          <canvas id="chSnnMC"></canvas>
        </div>
        <div style="flex:1; min-width:200px; display:flex; flex-direction:column; gap:0.5rem; font-size:0.85rem;">
          <div style="background:var(--bg); border:1px solid var(--border); padding:0.75rem; border-radius:8px;">
            <div style="font-weight:bold; margin-bottom:0.5rem; border-bottom:1px solid var(--border); padding-bottom:0.25rem;">Statistics</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>Mean:</span> <strong id="mc-stat-mean">-</strong></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>StdDev:</span> <strong id="mc-stat-std">-</strong></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>Worst:</span> <strong id="mc-stat-worst">-</strong></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>Best:</span> <strong id="mc-stat-best">-</strong></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>Failures:</span> <strong id="mc-stat-fail">-</strong></div>
            <div style="display:flex; justify-content:space-between; margin-top:0.5rem; padding-top:0.5rem; border-top:1px dashed var(--border);">
              <span style="font-weight:bold;">Yield:</span> <strong id="mc-stat-yield" style="font-size:1.1rem;">-</strong>
            </div>
          </div>
          <div style="display:flex; gap:5px; margin-top:auto;">
            <button class="btn bb" style="flex:1; font-size:0.75rem; padding:0.4rem;" onclick="if(window.exportMonteCarloCSV) window.exportMonteCarloCSV()"><i class="fas fa-file-csv"></i> CSV</button>
            <button class="btn bb" style="flex:1; font-size:0.75rem; padding:0.4rem;" onclick="if(window.copyLatexTable) window.copyLatexTable()"><i class="fas fa-file-code"></i> LaTeX</button>
          </div>
        </div>
      </div>
      
    </div>
"""

# Insert under Aging Card / Tornado wrapper. We wrapped them in a div.two earlier.
if 'id="snnMonteCarloCard"' not in content:
    # find where the <div class="two"> ends. Actually just place it before <!-- SNN Energy Settings Modal -->
    content = content.replace('<!-- SNN Energy Settings Modal -->', ui_html + '\n<!-- SNN Energy Settings Modal -->')


# 3. Hook fallbackComputeAll to show "stale" warning if base changes.
# In fallbackComputeAll, we just need to add: if (document.getElementById('mc-stale-warning') && window.mcResults && window.mcResults.length > 0) document.getElementById('mc-stale-warning').style.display = 'inline';
# Let's add it right at the end of fallbackComputeAll.
hook_target = """  if(!isPreview && window.triggerTornadoCompute) window.triggerTornadoCompute();
}"""

hook_new = """  if(!isPreview && window.triggerTornadoCompute) window.triggerTornadoCompute();
  if(!isPreview && document.getElementById('mc-stale-warning') && window.mcResults && window.mcResults.length > 0) {
      document.getElementById('mc-stale-warning').style.display = 'inline';
  }
}"""
if hook_target in content:
    content = content.replace(hook_target, hook_new)

# 4. Export PDF modification
pdf_end_old = "pdf.save('FET2SNN_Report.pdf');"
pdf_end_new = """
    if (window.mcChart && window.mcResults && window.mcResults.length > 0) {
        let mcImg = window.mcChart.toBase64Image();
        pdf.addPage();
        pdf.setFont('helvetica','bold'); pdf.setFontSize(16); pdf.setTextColor(30,30,47);
        pdf.text('Monte Carlo Variability & Yield Analysis', 15, 20);
        pdf.setFont('helvetica','normal'); pdf.setFontSize(10); pdf.setTextColor(100,100,100);
        pdf.text('Simulated manufacturing variations to estimate robust neuromorphic yield.', 15, 28);
        pdf.addImage(mcImg, 'PNG', 15, 35, 180, 100);
        
        pdf.setFont('helvetica','bold'); pdf.setTextColor(30,30,47);
        pdf.text('Statistical Summary', 15, 145);
        pdf.setFont('helvetica','normal');
        let m = document.getElementById('mc-stat-mean').innerText;
        let s = document.getElementById('mc-stat-std').innerText;
        let yld = document.getElementById('mc-stat-yield').innerText;
        let w = document.getElementById('mc-stat-worst').innerText;
        pdf.text(`Mean Accuracy: ${m} (StdDev: ${s})`, 15, 153);
        pdf.text(`Worst Case: ${w}`, 15, 159);
        
        pdf.setFont('helvetica','bold');
        if(parseFloat(yld) >= 90) pdf.setTextColor(16,185,129); // green
        else if(parseFloat(yld) >= 70) pdf.setTextColor(251,191,36); // yellow
        else pdf.setTextColor(239,68,68); // red
        pdf.text(`Manufacturing Yield: ${yld}`, 15, 167);
    }
    pdf.save('FET2SNN_Report.pdf');"""

if pdf_end_old in content:
    content = content.replace(pdf_end_old, pdf_end_new)


# 5. Initialization logic
ui_init_js = """
// Monte Carlo Initialization
document.addEventListener('DOMContentLoaded', () => {
    if(window.initMCChart) window.initMCChart();
});
"""
content = content.replace('</body>', f'<script>{ui_init_js}</script>\n</body>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched.")
