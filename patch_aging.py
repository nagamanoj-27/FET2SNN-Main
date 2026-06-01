import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Inject script tag for snn-aging.js
if 'snn-aging.js' not in content:
    content = content.replace('<script src="snn-simulator.js"></script>', '<script src="snn-simulator.js"></script>\n<script src="snn-aging.js"></script>')

# 2. Inject UI Card
ui_html = """
    <!-- Device Aging & Reliability Projector Card -->
    <div class="card" id="snnAgingCard" style="margin-bottom:1.5rem;">
      <div class="ct" style="display:flex; justify-content:space-between; align-items:center;">
        <span><i class="fas fa-hourglass-half"></i> Device Aging & Reliability <span class="ttip" style="margin-left:5px; font-size:0.85rem; font-weight:normal;">ⓘ<span class="ttip-text">Empirical degradation models based on NBTI/HCI. Vth +20mV/year, mobility -5%/year. Accuracy drop estimated via SNN model.</span></span></span>
        <label style="display:flex; align-items:center; gap:5px; font-size:0.9rem; font-weight:bold; cursor:pointer;">
          <input type="checkbox" id="aging-enable" style="width:16px; height:16px;"> Enable Aging
        </label>
      </div>
      
      <div style="display:flex; gap:1.5rem; flex-wrap:wrap;">
        <div style="flex:1; min-width:300px; display:flex; flex-direction:column; gap:1rem;">
          <div class="ig">
            <label style="display:flex; justify-content:space-between;">
              <span>Years of operation: <span id="aging-years-val" style="font-weight:bold; color:var(--text)">0.0</span> yrs</span>
              <button id="aging-reset-btn" style="background:none; border:none; color:#66ccff; cursor:pointer; text-decoration:underline; font-size:0.8rem;">Reset to fresh</button>
            </label>
            <input type="range" id="aging-years" min="0" max="5" step="0.1" value="0" style="width:100%;" disabled>
          </div>
          
          <div style="background:var(--bg); border:1px solid var(--border); padding:1rem; border-radius:8px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
              <span style="font-weight:bold;">Device Health: <span id="aging-health-label">Excellent</span> <i class="fas fa-circle" id="aging-health-dot" style="color:#10b981; font-size:0.8rem;"></i></span>
              <span style="font-size:0.85rem; color:#888;">Rem. Useful Life: <span id="aging-rul" style="font-weight:bold; color:#fff">> 5.0 years</span></span>
            </div>
            <div style="width:100%; height:8px; background:#2a2a3a; border-radius:4px; overflow:hidden;">
              <div id="aging-health-bar" style="width:100%; height:100%; background:#10b981; transition:0.3s;"></div>
            </div>
          </div>
        </div>
        
        <div style="flex:1; min-width:300px; height: 180px;">
          <canvas id="chSnnAge"></canvas>
        </div>
      </div>
    </div>
"""

# Insert under SNN Simulator
if 'id="snnAgingCard"' not in content:
    content = content.replace('<!-- SNN Energy Settings Modal -->', ui_html + '\n<!-- SNN Energy Settings Modal -->')


# 3. Hook applyAging into fallbackComputeAll
old_compute = """function fallbackComputeAll() {
  const d=computeDevice(S);
  const snn=computeSNN(d,S);"""

new_compute = """function fallbackComputeAll() {
  let d=computeDevice(S);
  if(window.updateAgingCurve) window.updateAgingCurve(d, S);
  if(window.agingEnabled) d = window.applyAging(d, window.agingYears);
  
  const snn=computeSNN(d,S);
  if(window.updateAgingUI) window.updateAgingUI(d.health || "Excellent", snn);"""

if old_compute in content:
    content = content.replace(old_compute, new_compute)

# 4. Modify update3DModel colors
old_gate_mat = "const gateMat = new THREE.MeshStandardMaterial({ color: 0xffd700, metalness: 0.9, roughness: 0.2, transparent: true, opacity: 0.75, clippingPlanes: clipPlanes, side: THREE.DoubleSide });"
new_gate_mat = """let gColor = 0xffd700;
          let gEmissive = 0x000000;
          let sColor = 0xaaaaaa;
          if (window.agingEnabled) {
              if (window.agingYears <= 1.0) { gColor = 0x10b981; gEmissive = 0x002211; sColor = 0x10b981; } // Green
              else if (window.agingYears <= 2.5) { gColor = 0xfbbf24; gEmissive = 0x221100; sColor = 0xfbbf24; } // Yellow
              else if (window.agingYears <= 4.0) { gColor = 0xf97316; gEmissive = 0x331100; sColor = 0xf97316; } // Orange
              else { gColor = 0xef4444; gEmissive = 0x440000; sColor = 0xef4444; } // Red
          }
          const gateMat = new THREE.MeshStandardMaterial({ color: gColor, emissive: gEmissive, metalness: 0.9, roughness: 0.2, transparent: true, opacity: 0.75, clippingPlanes: clipPlanes, side: THREE.DoubleSide });"""

if old_gate_mat in content:
    content = content.replace(old_gate_mat, new_gate_mat)

# 5. Modify sheetMat to match sColor
old_sheet_mat = "const sheetMat = new THREE.MeshStandardMaterial({ color: 0xaaaaaa, roughness: 0.2, metalness: 0.1, clippingPlanes: clipPlanes });"
new_sheet_mat = "const sheetMat = new THREE.MeshStandardMaterial({ color: (typeof sColor !== 'undefined' ? sColor : 0xaaaaaa), roughness: 0.2, metalness: 0.1, clippingPlanes: clipPlanes });"

if old_sheet_mat in content:
    # Need to put sheetMat after gateMat logic so sColor is defined.
    # So I'll swap their declaration order or just move new_sheet_mat right after new_gate_mat
    pass # I'll do this carefully

# Wait, let's just do a regex replace for the whole material block
mat_block_old = """const sheetMat = new THREE.MeshStandardMaterial({ color: 0xaaaaaa, roughness: 0.2, metalness: 0.1, clippingPlanes: clipPlanes });
          const highKMat = new THREE.MeshStandardMaterial({ color: 0x00ffff, transparent: true, opacity: 0.3, side: THREE.DoubleSide, clippingPlanes: clipPlanes });
          const gateMat = new THREE.MeshStandardMaterial({ color: 0xffd700, metalness: 0.9, roughness: 0.2, transparent: true, opacity: 0.75, clippingPlanes: clipPlanes, side: THREE.DoubleSide });"""

mat_block_new = """let gColor = 0xffd700;
          let gEmissive = 0x000000;
          let sColor = 0xaaaaaa;
          if (window.agingEnabled) {
              if (window.agingYears <= 1.0) { gColor = 0x10b981; gEmissive = 0x003311; sColor = 0x10b981; } // Green
              else if (window.agingYears <= 2.5) { gColor = 0xfbbf24; gEmissive = 0x332200; sColor = 0xfbbf24; } // Yellow
              else if (window.agingYears <= 4.0) { gColor = 0xf97316; gEmissive = 0x442200; sColor = 0xf97316; } // Orange
              else { gColor = 0xef4444; gEmissive = 0x550000; sColor = 0xef4444; opacity = 0.5; } // Red
          }
          const sheetMat = new THREE.MeshStandardMaterial({ color: sColor, emissive: gEmissive, roughness: 0.2, metalness: 0.1, clippingPlanes: clipPlanes });
          const highKMat = new THREE.MeshStandardMaterial({ color: 0x00ffff, transparent: true, opacity: 0.3, side: THREE.DoubleSide, clippingPlanes: clipPlanes });
          const gateMat = new THREE.MeshStandardMaterial({ color: gColor, emissive: gEmissive, metalness: 0.9, roughness: 0.2, transparent: true, opacity: 0.75, clippingPlanes: clipPlanes, side: THREE.DoubleSide });"""

if mat_block_old in content:
    content = content.replace(mat_block_old, mat_block_new)

# 6. PDF Export extension
# In exportPDF, after SNN accuracy text
pdf_snn_acc_old = "pdf.setTextColor(124,58,237); pdf.text(`SNN Accuracy:        ${snn.A.toFixed(1)} %`,20,y); y+=12;"
pdf_snn_acc_new = """pdf.setTextColor(124,58,237); pdf.text(`SNN Accuracy:        ${snn.A.toFixed(1)} %`,20,y); y+=12;
    if (window.agingEnabled) {
      pdf.setFont('helvetica','bold'); pdf.setTextColor(239,68,68); pdf.text('Reliability Projection (Aged ' + window.agingYears.toFixed(1) + ' Years)', 15, y); y+=8;
      pdf.setFont('helvetica','normal'); pdf.setTextColor(100,100,100);
      pdf.text(`Aged Vth: ${(snn.d && snn.d.Vth) ? snn.d.Vth.toFixed(3) : '-'} V`, 20, y); y+=6;
      pdf.text(`Aged Ion: ${(snn.d && snn.d.Ion) ? snn.d.Ion.toFixed(1) : '-'} A/m`, 20, y); y+=6;
      pdf.text(`Estimated RUL: ${document.getElementById('aging-rul') ? document.getElementById('aging-rul').innerText : 'N/A'}`, 20, y); y+=12;
    }"""
# Wait, snn.d is not passed. snn object doesn't have `d`. But we can just read the global variables, or we can use `window.agedAccuracy` but it doesn't have Vth. We can just use the DOM elements or recalculate. 
# Actually, `fallbackComputeAll` updates `SNN.E`, `SNN.L`, `SNN.A` but it also calls `updParams(d)`. The UI shows the aged parameters in the main grid!
# Yes, `updParams(d)` populates the grid with whatever `d` is passed.
pdf_snn_acc_new = """pdf.setTextColor(124,58,237); pdf.text(`SNN Accuracy:        ${snn.A.toFixed(1)} %`,20,y); y+=12;
    if (window.agingEnabled) {
      pdf.setFont('helvetica','bold'); pdf.setTextColor(239,68,68); pdf.text('Reliability Projection (Aged ' + window.agingYears.toFixed(1) + ' Years)', 15, y); y+=8;
      pdf.setFont('helvetica','normal'); pdf.setTextColor(100,100,100);
      let a_rul = document.getElementById('aging-rul') ? document.getElementById('aging-rul').innerText : 'N/A';
      pdf.text(`Estimated RUL (Time to 70% Acc): ${a_rul}`, 20, y); y+=12;
    }"""
if pdf_snn_acc_old in content:
    content = content.replace(pdf_snn_acc_old, pdf_snn_acc_new)

# 7. Add UI initialization logic for the card
ui_init_js = """
// Aging Initialization
document.addEventListener('DOMContentLoaded', () => {
    if(window.initAgingChart) window.initAgingChart();
    const chk = document.getElementById('aging-enable');
    const sld = document.getElementById('aging-years');
    const val = document.getElementById('aging-years-val');
    const btn = document.getElementById('aging-reset-btn');
    if (chk) {
        chk.addEventListener('change', (e) => {
            window.agingEnabled = e.target.checked;
            sld.disabled = !window.agingEnabled;
            // Force recompute
            if(typeof fallbackComputeAll === 'function') fallbackComputeAll();
        });
    }
    if (sld) {
        sld.addEventListener('input', (e) => {
            window.agingYears = parseFloat(e.target.value);
            val.innerText = window.agingYears.toFixed(1);
            if(typeof fallbackComputeAll === 'function') fallbackComputeAll();
        });
    }
    if (btn) {
        btn.addEventListener('click', () => {
            if(sld) sld.value = 0;
            window.agingYears = 0.0;
            val.innerText = "0.0";
            if(typeof fallbackComputeAll === 'function') fallbackComputeAll();
        });
    }
});
"""
content = content.replace('</body>', f'<script>{ui_init_js}</script>\n</body>')


with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched.")
