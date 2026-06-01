import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Inject jspdf-autotable script
if 'jspdf.plugin.autotable' not in content:
    jspdf_script = '<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>'
    autotable_script = jspdf_script + '\n<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js"></script>'
    content = content.replace(jspdf_script, autotable_script)


# 2. Replace the exportPDF function
# We need to find the existing exportPDF function block.
# Since it might be quite long, we'll use a regex that captures everything from `async function exportPDF(){` to the end of the function.
# The function ends around line 3130, right before `// ============================================================ //  BENCHMARK TABLE`

old_pdf_regex = re.compile(r'async function exportPDF\(\)\{.*?(?=\s*// ============================================================\s*//  BENCHMARK TABLE)', re.DOTALL)

new_pdf_func = """async function exportPDF(){
  const btn = event.target.closest('button');
  const originalHTML = btn.innerHTML;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
  
  // Give UI time to update spinner
  await new Promise(r => setTimeout(r, 100));

  try {
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    const d = computeDevice(S);
    const snn = computeSNN(d, S);
    const Wum = d.Wm * 1e6;

    // Wait for all canvases to be ready and captured
    const getCanvasImg = (id) => {
      const cvs = document.getElementById(id);
      return cvs ? cvs.toDataURL('image/png') : null;
    };
    
    // 3D canvas is generated dynamically inside #tc3d
    const get3DCanvasImg = () => {
      const cvs = document.querySelector('#tc3d canvas');
      return cvs ? cvs.toDataURL('image/png') : null;
    };

    const [img3D, imgTr, imgOut, imgPar] = await Promise.all([
      Promise.resolve(get3DCanvasImg()),
      Promise.resolve(getCanvasImg('chTr')),
      Promise.resolve(getCanvasImg('chOut')),
      Promise.resolve(getCanvasImg('chPar'))
    ]);

    // --- Page 1: Headers and Tables ---
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(22);
    pdf.setTextColor(124, 58, 237);
    pdf.text('FET2SNN - Pre-TCAD Simulation Report', 105, 20, { align: 'center' });

    pdf.setFontSize(10);
    pdf.setTextColor(100, 100, 150);
    pdf.text('One Click, One Inference  |  GAA Nanosheet FET SNN Accelerator', 105, 28, { align: 'center' });
    pdf.setFontSize(8);
    pdf.text(`Generated: ${new Date().toLocaleString()}`, 105, 34, { align: 'center' });

    pdf.setDrawColor(200, 180, 255);
    pdf.line(15, 37, 195, 37);

    // Device Inputs Table
    pdf.autoTable({
      startY: 45,
      head: [['Parameter', 'Value', 'Parameter', 'Value']],
      body: [
        ['Gate Length (Lg)', `${S.Lg} nm`, 'Channel Width (Wns)', `${S.Wns} nm`],
        ['Channel Thick. (Tns)', `${S.Tns} nm`, 'Nanosheet Stacks', `${S.Nstacks}`],
        ['Spacer k (k_spacer)', `${S.kSpacer}`, 'EOT', `${S.EOT} nm`],
        ['Channel Doping', `${S.Nch.toExponential(2)} cm⁻³`, 'S/D Doping', `${S.NSD.toExponential(2)} cm⁻³`],
        ['Supply Vdd', `${S.Vdd} V`, 'Temperature', `${S.T} °C`]
      ],
      theme: 'grid',
      headStyles: { fillColor: [124, 58, 237], textColor: 255 },
      margin: { left: 15, right: 15 }
    });

    // Electrical Parameters Table
    pdf.autoTable({
      startY: pdf.lastAutoTable.finalY + 10,
      head: [['Parameter', 'Value', 'Parameter', 'Value']],
      body: [
        ['Weff', `${d.Weff.toFixed(0)} nm`, 'Threshold Voltage (Vth)', `${d.Vth.toFixed(3)} V`],
        ['Cox', `${d.Cox.toFixed(3)} fF/µm²`, 'Subthreshold Swing (SS)', `${d.SS.toFixed(1)} mV/dec`],
        ['DIBL', `${d.DIBL.toFixed(1)} mV/V`, 'Effective Mobility', `${d.muEff.toFixed(1)} cm²/Vs`],
        ['On-Current (Ion)', `${(d.Ion * 1e6 / Wum).toFixed(1)} µA/µm`, 'Off-Current (Ioff)', `${(d.Ioff * 1e12 / Wum).toFixed(4)} pA/µm`],
        ['Transconductance (gm)', `${(d.gm * 1e3 / Wum).toFixed(3)} mS/µm`, 'Output Cond. (gds)', `${(d.gds * 1e6 / Wum).toFixed(2)} µS/µm`]
      ],
      theme: 'grid',
      headStyles: { fillColor: [14, 165, 233], textColor: 255 },
      margin: { left: 15, right: 15 }
    });

    // SNN Predictions
    let y = pdf.lastAutoTable.finalY + 15;
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(14);
    pdf.setTextColor(30, 30, 47);
    pdf.text('SNN Performance Prediction', 15, y);
    
    y += 10;
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(12);
    pdf.setTextColor(14, 165, 233);
    pdf.text(`Energy / Spike: ${snn.E.toFixed(3)} fJ`, 20, y); y += 8;
    pdf.setTextColor(16, 185, 129);
    pdf.text(`Inference Latency: ${snn.L.toFixed(2)} ms`, 20, y); y += 8;
    
    // Check for error bars in UI
    let accEl = document.getElementById('oSnnAc');
    let accText = accEl ? accEl.innerText.replace('\\n', ' ') : snn.A.toFixed(1) + ' %';
    pdf.setTextColor(124, 58, 237);
    pdf.text(`SNN Accuracy: ${accText}`, 20, y); y += 15;

    // --- Page 2: Visualizations ---
    pdf.addPage();
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(16);
    pdf.setTextColor(30, 30, 47);
    pdf.text('Device Visualizations & Output Characteristics', 15, 20);

    // 3D Model
    if (img3D) {
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(10);
      pdf.setTextColor(100, 100, 100);
      pdf.text('TCAD 3D Device Structure (WebGL)', 15, 30);
      pdf.addImage(img3D, 'PNG', 45, 35, 120, 80);
    }
    
    // Transfer and Output
    if (imgTr && imgOut) {
      pdf.text('Transfer (Id-Vg) & Output (Id-Vd) Characteristics', 15, 130);
      pdf.addImage(imgTr, 'PNG', 15, 135, 90, 60);
      pdf.addImage(imgOut, 'PNG', 110, 135, 90, 60);
    }
    
    // Pareto Chart
    if (imgPar) {
      pdf.text('SNN Pareto Optimization (Energy vs Latency)', 15, 210);
      pdf.addImage(imgPar, 'PNG', 55, 215, 100, 70);
    }

    // --- Optional Advanced Charts ---
    if (window.tornadoChart) {
      pdf.addPage();
      pdf.setFont('helvetica', 'bold'); pdf.setFontSize(16); pdf.setTextColor(30, 30, 47);
      pdf.text('Sensitivity Analysis', 15, 20);
      pdf.addImage(window.tornadoChart.toBase64Image(), 'PNG', 15, 30, 180, 100);
    }
    if (window.mcChart && window.mcResults) {
      pdf.addPage();
      pdf.setFont('helvetica', 'bold'); pdf.setFontSize(16); pdf.setTextColor(30, 30, 47);
      pdf.text('Monte Carlo Variability & Yield Analysis', 15, 20);
      pdf.addImage(window.mcChart.toBase64Image(), 'PNG', 15, 30, 180, 100);
    }
    if (window.validationScatterChart) {
      pdf.addPage();
      pdf.setFont('helvetica', 'bold'); pdf.setFontSize(16); pdf.setTextColor(30, 30, 47);
      pdf.text('Model Validation Suite', 15, 20);
      pdf.addImage(window.validationScatterChart.toBase64Image(), 'PNG', 15, 30, 140, 80);
      if (window.validationResidualChart) {
          pdf.addImage(window.validationResidualChart.toBase64Image(), 'PNG', 15, 120, 140, 80);
      }
    }

    pdf.save('FET2SNN_Report.pdf');

  } catch (error) {
    console.error("PDF Generation Error:", error);
    alert('PDF Generation Failed: ' + error.message + '. Please try again or check console for details.');
  } finally {
    btn.innerHTML = originalHTML;
  }
}"""

content = re.sub(old_pdf_regex, new_pdf_func, content)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("index.html patched with fixed PDF export.")
