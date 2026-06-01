import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Remove jspdf-autotable script
autotable_script = '<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>\n<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js"></script>'
jspdf_script = '<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>'

if autotable_script in content:
    content = content.replace(autotable_script, jspdf_script)

# 2. Restore exportPDF
old_pdf_func = """async function exportPDF(){
  const btn=event.target.closest('button');
  btn.innerHTML='<i class="fas fa-spinner fa-spin"></i> Generating.';
  try{
    const{jsPDF}=window.jspdf;
    const pdf=new jsPDF({orientation:'portrait',unit:'mm',format:'a4'});
    const d=computeDevice(S), snn=computeSNN(d,S);
    const Wum=d.Wm*1e6;

    pdf.setFont('helvetica','bold'); pdf.setFontSize(22);
    pdf.setTextColor(124,58,237);
    pdf.text('FET2SNN - Pre-TCAD Simulation Report',105,20,{align:'center'});

    pdf.setFontSize(10); pdf.setTextColor(100,100,150);
    pdf.text('One Click, One Inference  |  GAA Nanosheet FET   SNN Accelerator',105,28,{align:'center'});
    pdf.setFontSize(8); pdf.text(`Generated: ${new Date().toLocaleString()}`,105,34,{align:'center'});

    pdf.setDrawColor(200,180,255); pdf.line(15,37,195,37);

    let y=45;
    const sec=(title)=>{
      pdf.setFont('helvetica','bold'); pdf.setFontSize(13); pdf.setTextColor(30,30,47);
      pdf.text(title,15,y); y+=7;
    };
    const row=(l1,v1,l2,v2)=>{
      pdf.setFont('helvetica','normal'); pdf.setFontSize(10);
      pdf.setTextColor(100,80,150); pdf.text(l1+':',20,y);
      pdf.setTextColor(30,30,47); pdf.text(String(v1),60,y);
      if(l2){ pdf.setTextColor(100,80,150); pdf.text(l2+':',110,y);
        pdf.setTextColor(30,30,47); pdf.text(String(v2),150,y); }
      y+=7;
    };

    sec('Device Design Inputs');
    row('Lg',S.Lg+' nm','Wns',S.Wns+' nm');
    row('Tns',S.Tns+' nm','Nstacks',S.Nstacks);
    row('\u03ba_spacer',S.kSpacer,'EOT',S.EOT+' nm');
    row('Nch',S.Nch.toExponential(2)+' cm\u207B\u00B3','NSD',S.NSD.toExponential(2)+' cm\u207B\u00B3');
    row('Vdd',S.Vdd+' V','Temperature',S.T+' \u00B0C');

    pdf.line(15,y,195,y); y+=8;
    sec('Computed Electrical Parameters');
    row('Weff',d.Weff.toFixed(0)+' nm','Vth',d.Vth.toFixed(3)+' V');
    row('Cox',d.Cox.toFixed(3)+' fF/\u00B5m\u00B2','SS',d.SS.toFixed(1)+' mV/dec');
    row('DIBL',d.DIBL.toFixed(1)+' mV/V','\u00B5_eff',d.muEff.toFixed(1)+' cm\u00B2/Vs');
    row('Ion',(d.Ion*1e6/Wum).toFixed(1)+' \u00B5A/\u00B5m','Ioff',(d.Ioff*1e12/Wum).toFixed(4)+' pA/\u00B5m');
    row('gm',(d.gm*1e3/Wum).toFixed(3)+' mS/\u00B5m','gds',(d.gds*1e6/Wum).toFixed(2)+' \u00B5S/\u00B5m');

    pdf.line(15,y,195,y); y+=8;
    sec('SNN Performance Prediction (LightGBM-Derived)');
    pdf.setFont('helvetica','normal'); pdf.setFontSize(12);
    pdf.setTextColor(14,165,233); pdf.text(`Energy / Spike:      ${snn.E.toFixed(3)} fJ`,20,y); y+=8;
    pdf.setTextColor(16,185,129); pdf.text(`Inference Latency:   ${snn.L.toFixed(2)} ms`,20,y); y+=8;
    pdf.setTextColor(124,58,237); pdf.text(`SNN Accuracy:        ${snn.A.toFixed(1)} %`,20,y); y+=12;
    if (window.agingEnabled) {
      pdf.setFont('helvetica','bold'); pdf.setTextColor(239,68,68); pdf.text('Reliability Projection (Aged ' + window.agingYears.toFixed(1) + ' Years)', 15, y); y+=8;
      pdf.setFont('helvetica','normal'); pdf.setTextColor(100,100,100);
      let a_rul = document.getElementById('aging-rul') ? document.getElementById('aging-rul').innerText : 'N/A';
      pdf.text(`Estimated RUL (Time to 70% Acc): ${a_rul}`, 20, y); y+=12;
    }

    pdf.setTextColor(150,150,180); pdf.setFontSize(8);
    pdf.text('Calibrated: Loubet 2017 | Lee 2025 | Kaur 2025 | Lakshmana 2026 | Dixit 2025 | Yeung 2018 | Aruna Kumari 2025 | Dewangan 2025',15,y);

    
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
    
    if (window.validationScatterChart) {
        let scImg = window.validationScatterChart.toBase64Image();
        
        pdf.addPage();
        pdf.setFont('helvetica','bold'); pdf.setFontSize(16); pdf.setTextColor(30,30,47);
        pdf.text('Complete Model Validation Suite', 15, 20);
        pdf.setFont('helvetica','normal'); pdf.setFontSize(10); pdf.setTextColor(100,100,100);
        pdf.text('Validation of analytical proxy model against 17 rigorously simulated TCAD benchmark devices.', 15, 28);
        
        pdf.setFont('helvetica','bold'); pdf.setTextColor(30,30,47);
        pdf.text('Model vs TCAD Scatter Plot (Vth, SS, Ion)', 15, 40);
        pdf.addImage(scImg, 'PNG', 15, 45, 140, 80);
        
        if (window.validationResidualChart) {
            pdf.text('SNN Predictor Accuracy Residuals', 15, 140);
            pdf.addImage(window.validationResidualChart.toBase64Image(), 'PNG', 15, 145, 140, 80);
            
            pdf.setFont('helvetica','normal'); pdf.setFontSize(10);
            let ci = document.getElementById('val-res-ci') ? document.getElementById('val-res-ci').innerText : '';
            let r2 = document.getElementById('val-r2').innerText;
            let mae = document.getElementById('val-mae').innerText;
            pdf.text(`Current Metric -> R2: ${r2} | MAE: ${mae}`, 160, 85, {maxWidth: 40});
            if (ci) pdf.text(`95% Confidence Interval: ${ci}`, 160, 185, {maxWidth: 40});
        }
    }
    pdf.save('FET2SNN_Report.pdf');
  }catch(e){ alert('PDF error: '+e.message); }
  btn.innerHTML='<i class="fas fa-file-pdf"></i> Export PDF';
}"""

pdf_regex = re.compile(r'async function exportPDF\(\)\{.*?(?=\s*// ============================================================\s*//  BENCHMARK TABLE)', re.DOTALL)
content = re.sub(pdf_regex, old_pdf_func, content)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("index.html restored to previous PDF export.")
