import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# =========================================================
# 1. Inject Advanced Manufacturing Parameters UI
# =========================================================
ui_injection = """
    <!-- MANUFACTURING PARAMETERS (BSIM-CMG) -->
    <details class="isg" style="margin-bottom: 1rem; border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem; background: var(--bg-card);">
      <summary style="cursor: pointer; font-weight: 600; color: var(--accent); user-select: none;">
        <i class="fas fa-industry"></i> Manufacturing Parameters (BSIM-CMG)
      </summary>
      <div style="padding-top: 0.8rem;">
        
        <!-- Geometry -->
        <div class="sg" style="margin-top:0;">Nanosheet Geometry</div>
        <div class="ig">
          <label>Sheet Spacing (nm)</label>
          <div class="sr"><input type="range" id="slNspace" min="5" max="30" step="1" value="20"><input type="number" id="nNspace" class="nf" value="20" min="5" max="30"></div>
        </div>
        <div class="ig">
          <label>Corner Radius (nm)</label>
          <div class="sr"><input type="range" id="slCornerR" min="1" max="10" step="0.5" value="5"><input type="number" id="nCornerR" class="nf" value="5" min="1" max="10" step="0.5"></div>
        </div>

        <!-- Quantum -->
        <div class="sg">Quantum Confinement</div>
        <div class="ig">
          <label>QC Scale Factor</label>
          <div class="sr"><input type="range" id="slQcScale" min="0" max="5" step="0.1" value="1.0"><input type="number" id="nQcScale" class="nf" value="1.0" min="0" max="5" step="0.1"></div>
        </div>

        <!-- Thermal -->
        <div class="sg">Self-Heating</div>
        <div class="ig">
          <label>Enable Self-Heating</label>
          <select id="selShmod" class="sel">
            <option value="1">Enabled (SHMOD=1)</option>
            <option value="0">Disabled (SHMOD=0)</option>
          </select>
        </div>
        <div class="ig">
          <label>Thermal Resistance RTH0 (K/W)</label>
          <div class="sr"><input type="range" id="slRth0" min="1000" max="50000" step="1000" value="15000"><input type="number" id="nRth0" class="nf" value="15000" min="1000" max="50000"></div>
        </div>

        <!-- Parasitics -->
        <div class="sg">Parasitic RC</div>
        <div class="ig">
          <label>Contact R (RDC/RSC) (Ohm)</label>
          <div class="sr"><input type="range" id="slRdc" min="10" max="200" step="10" value="50"><input type="number" id="nRdc" class="nf" value="50" min="10" max="200"></div>
        </div>
        <div class="ig">
          <label>Overlap C (CGSO) (fF/um)</label>
          <div class="sr"><input type="range" id="slCgso" min="0.01" max="1.0" step="0.01" value="0.1"><input type="number" id="nCgso" class="nf" value="0.1" min="0.01" max="1.0" step="0.01"></div>
        </div>

        <!-- Variation -->
        <div class="sg">Process Variation</div>
        <div class="ig">
          <label>Vth Sigma (VTH0_DFT) (mV)</label>
          <div class="sr"><input type="range" id="slVthDft" min="0" max="20" step="0.5" value="2.5"><input type="number" id="nVthDft" class="nf" value="2.5" min="0" max="20" step="0.5"></div>
        </div>

      </div>
    </details>
"""
target_ui = '<p class="mn"><i class="fas fa-info-circle"></i> Analytical models calibrated'
content = content.replace(target_ui, ui_injection + '\n    ' + target_ui)

# =========================================================
# 2. Add defaults to S object and add wire logic
# =========================================================
old_S = "const S={Lg:12,Wns:45,Tns:5,Nstacks:3,kSpacer:7,EOT:0.8,Nch:1e16,NSD:1e20,Vdd:0.7,T:25,ChMat:'Si',SpArch:'gaa',Corner:'TT'};"
new_S = "const S={Lg:12,Wns:45,Tns:5,Nstacks:3,kSpacer:7,EOT:0.8,Nch:1e16,NSD:1e20,Vdd:0.7,T:25,ChMat:'Si',SpArch:'gaa',Corner:'TT',NSHEET_SPACE:20,CORNER_RAD:5,QCSCALE:1.0,SHMOD:1,RTH0:15000,RDC:50,CGSO:0.1,VTH0_DFT:2.5};"
content = content.replace(old_S, new_S)

wire_logic = """
  wire('slLg','nLg','Lg');
"""
new_wire_logic = """
  wire('slLg','nLg','Lg');
  wire('slNspace','nNspace','NSHEET_SPACE');
  wire('slCornerR','nCornerR','CORNER_RAD');
  wire('slQcScale','nQcScale','QCSCALE');
  wire('slRth0','nRth0','RTH0');
  wire('slRdc','nRdc','RDC');
  wire('slCgso','nCgso','CGSO');
  wire('slVthDft','nVthDft','VTH0_DFT');
  
  const selShmod = document.getElementById('selShmod');
  if(selShmod) selShmod.addEventListener('change', (e)=>{ S.SHMOD=parseInt(e.target.value); if(typeof debouncedComputeAll==='function') debouncedComputeAll(); });
"""
content = content.replace(wire_logic, new_wire_logic)

# =========================================================
# 3. Update computeDevice()
# =========================================================
# Inject into computeDevice(s):
old_vth = "let Vth_25 = (Vth0+dVqm+dVroll+dVsp) * cornerScale.Vth;"
new_vth = """
  const QCSCALE = s.QCSCALE !== undefined ? s.QCSCALE : 1.0;
  const qc_vth_shift = (Lg < 15) ? 0.03 * QCSCALE : 0.01 * QCSCALE;
  let Vth_25 = (Vth0+dVqm+dVroll+dVsp+qc_vth_shift) * cornerScale.Vth;
"""
content = content.replace(old_vth, new_vth)

old_ion = "const Ion=beta*Vov*Vov/(1+Vov/(Esat*Lm));  // A"
new_ion = """let Ion_raw=beta*Vov*Vov/(1+Vov/(Esat*Lm));  // A
  const RTH0 = s.RTH0 !== undefined ? s.RTH0 : 15000;
  const SHMOD = s.SHMOD !== undefined ? s.SHMOD : 1;
  const power = Ion_raw * Vdd;
  const deltaT = SHMOD ? (power * RTH0) : 0;
  let ion_deg = 1 - 0.0005 * deltaT;
  if(ion_deg < 0.5) ion_deg = 0.5;
  const Ion = Ion_raw * ion_deg;
"""
content = content.replace(old_ion, new_ion)

# =========================================================
# 4. Rewrite genBsimCard()
# =========================================================
old_genBsim = re.compile(r'function genBsimCard\(\)\{.*?document\.getElementById\(\'bsimCard\'\)\.textContent=card;\s*\}', re.DOTALL)
new_genBsim = """function genBsimCard(){
  const H=parseFloat(document.getElementById('nHfin').value)||40;
  const T_fin=parseFloat(document.getElementById('nTfin').value)||8;
  const DF=parseFloat(document.getElementById('nDelfin').value)||0;
  const N=parseFloat(document.getElementById('nNfinB').value)||10;
  const D=parseFloat(document.getElementById('nDiam').value)||8;
  const BULKMOD=parseInt(document.getElementById('selBulk').value);
  const weff=bsimWeff();
  const d=computeDevice(S);
  const Wum=d.Wm*1e6;

  const VTH0=d.Vth.toFixed(4);
  const U0=d.muEff.toFixed(2);
  const VSAT=Math.round(0.5*d.muEff*1e-4*1e7);
  const ETA0=(d.DIBL/1000).toFixed(4);
  const TOXE=(S.EOT*1e-9).toExponential(3);
  const TOXP=(S.EOT*.85e-9).toExponential(3);
  const CDSC=((d.SS/60-1)*2.4e-4).toExponential(2);
  const TEMP=(S.T+273.15).toFixed(2);
  const gNames={1:'Double-Gate',3:'Triple-Gate FinFET',6:'GAA Rect. Nanosheet',7:'GAA Cylindrical NW'};

  let finBlock='';
  if(bGeomod===6){ // Nanosheet
    finBlock=`+ L       = ${(S.Lg*1e-9).toExponential(3)}\n+ W       = ${(S.Wns*1e-9).toExponential(3)}\n+ NSHEETS = ${S.Nstacks}\n+ NSHEET_SPACE = ${(S.NSHEET_SPACE*1e-9).toExponential(3)}\n+ CORNER  = ${(S.CORNER_RAD*1e-9).toExponential(3)}\n+ THICK   = ${(S.Tns*1e-9).toExponential(3)}`;
  } else {
    finBlock=`+ HFIN    = ${(H*1e-9).toExponential(3)}\n+ TFIN    = ${(T_fin*1e-9).toExponential(3)}\n+ NFIN    = ${N}`;
  }

  const card=
`* ================================================================
*  FET2SNN Manufacturing-Ready BSIM-CMG Model
*  Date    : ${new Date().toLocaleString()}
*  Device  : ${gNames[bGeomod]} (GEOMOD=${bGeomod})
*  Corner  : ${S.Corner}
* ================================================================

.MODEL FET2SNN_NMOS NMOS (
+ LEVEL   = 72
+ VERSION = 112.0
+ BULKMOD = ${BULKMOD}

* ----- GEOMETRY -----
${finBlock}

* ----- CORE ELECTRICAL -----
+ VTH0    = ${VTH0}
+ U0      = ${U0}
+ VSAT    = ${VSAT}
+ ETA0    = ${ETA0}
+ CDSC    = ${CDSC}

* ----- GATE DIELECTRIC -----
+ TOXE    = ${TOXE}
+ TOXP    = ${TOXP}
+ EPSROX  = 22.0

* ----- QUANTUM CONFINEMENT -----
+ QCSCALE = ${S.QCSCALE.toFixed(2)}
+ QMFACTOR= 0.8
+ VQIM    = 0.05

* ----- SELF-HEATING -----
+ SHMOD   = ${S.SHMOD}
+ RTH0    = ${S.RTH0}
+ CTH0    = 1.0E-11

* ----- PARASITICS -----
+ RDSMOD  = 1
+ RDC     = ${S.RDC}
+ RSC     = ${S.RDC}
+ CGSO    = ${(S.CGSO*1e-9).toExponential(2)}
+ CGDO    = ${(S.CGSO*1e-9).toExponential(2)}
+ CIT     = 0.0

* ----- PROCESS VARIATION (Monte Carlo) -----
+ VTH0_DFT = ${(S.VTH0_DFT/1000).toExponential(3)}
+ U0_DFT   = 0.002
+ XL       = 0.0
+ XW       = 0.0

* ----- NOISE -----
+ NOIA     = 1.0E37
+ NOIB     = 5.0E6
+ NOIC     = 0.0

* ----- TEMPERATURE -----
+ TNOM    = 298.15
+ TEMP    = ${TEMP}
+ TCVTH0  = -0.002
+ TCU0    = 1.5
+ TVSAT   = -0.5
)`

  document.getElementById('bsimCard').textContent=card;
}"""
content = re.sub(old_genBsim, new_genBsim, content)

# =========================================================
# 5. Add generateCornerLibrary and Corner UI button
# =========================================================
# Inject button next to Export SPICE Netlist
old_spice_btn = """<button class="btn bb" style="flex:1;" onclick="dlBsimCard()"><i class="fas fa-download"></i> Download .MODEL</button>"""
new_spice_btn = """<button class="btn bb" style="flex:1;" onclick="dlBsimCard()"><i class="fas fa-download"></i> Download .MODEL</button>
          <button class="btn bb" style="flex:1;" onclick="dlCornerLibrary()"><i class="fas fa-book"></i> Export Corner Library (.lib)</button>"""
content = content.replace(old_spice_btn, new_spice_btn)

# Add the functions
corner_funcs = """
function dlCornerLibrary() {
  const baseCard = document.getElementById('bsimCard').textContent;
  if(!baseCard || !baseCard.includes('.MODEL')) {
    alert("Please generate a BSIM card first.");
    return;
  }
  
  // Extract base model text from .MODEL to the end
  const modelMatch = baseCard.match(/\\.MODEL FET2SNN_NMOS NMOS \\([\\s\\S]*?\\)/);
  if(!modelMatch) return alert("Could not parse base model.");
  const baseModel = modelMatch[0].replace('.MODEL FET2SNN_NMOS NMOS (', '');
  
  // Extract base VTH0 and U0
  const vthMatch = baseModel.match(/\\+\\s*VTH0\\s*=\\s*([0-9.\\-eE]+)/);
  const u0Match = baseModel.match(/\\+\\s*U0\\s*=\\s*([0-9.\\-eE]+)/);
  
  let baseVth = vthMatch ? parseFloat(vthMatch[1]) : 0.3;
  let baseU0 = u0Match ? parseFloat(u0Match[1]) : 200;

  const corners = ['TT', 'FF', 'SS', 'FS', 'SF'];
  let lib = `* FET2SNN Corner Library (Manufacturing-Ready)\\n`;
  lib += `.LIB FET2SNN_Corners\\n\\n`;
  
  for (const corner of corners) {
    let vthFactor = 1.0, u0Factor = 1.0;
    switch (corner) {
      case 'FF': vthFactor = 0.90; u0Factor = 1.10; break;
      case 'SS': vthFactor = 1.10; u0Factor = 0.90; break;
      case 'FS': vthFactor = 0.95; u0Factor = 0.95; break;
      case 'SF': vthFactor = 1.05; u0Factor = 1.05; break;
    }
    
    let newVth = (baseVth * vthFactor).toFixed(4);
    let newU0 = (baseU0 * u0Factor).toFixed(2);
    
    let cornerModel = baseModel
      .replace(/(\\+\\s*VTH0\\s*=\\s*)[0-9.\\-eE]+/, `$1${newVth}`)
      .replace(/(\\+\\s*U0\\s*=\\s*)[0-9.\\-eE]+/, `$1${newU0}`);
      
    lib += `.MODEL ${corner}_NMOS NMOS (\\n* Corner specific scaling: VTH0 x ${vthFactor}, U0 x ${u0Factor}\\n`;
    lib += cornerModel + `\\n\\n`;
  }
  lib += `.ENDL FET2SNN_Corners\\n`;

  const blob = new Blob([lib], {type:'text/plain'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'FET2SNN_Corners.lib';
  a.click();
  URL.revokeObjectURL(url);
}
"""
content = content.replace("function dlBsimCard(){", corner_funcs + "\nfunction dlBsimCard(){")

# =========================================================
# 6. Update exportPDF()
# =========================================================
# I'll find where it prints "Calibrated: Loubet 2017..." and append the BSIM Summary
old_pdf_text = "pdf.text('Calibrated: Loubet 2017 | Lee 2025 | Kaur 2025 | Lakshmana 2026 | Dixit 2025 | Yeung 2018 | Aruna Kumari 2025 | Dewangan 2025',15,y);"
new_pdf_text = """pdf.text('Calibrated: Loubet 2017 | Lee 2025 | Kaur 2025 | Lakshmana 2026 | Dixit 2025 | Yeung 2018 | Aruna Kumari 2025 | Dewangan 2025',15,y);

    y+=15;
    sec('BSIM-CMG Manufacturing Parameters');
    row('Nanosheet Stack',S.Nstacks,'Sheet Spacing',S.NSHEET_SPACE+' nm');
    row('Corner Radius',S.CORNER_RAD+' nm','QC Scale',S.QCSCALE.toFixed(2));
    row('Self-Heating',S.SHMOD?'Enabled':'Disabled','Thermal Res. RTH0',S.RTH0+' K/W');
    row('Contact Res.',S.RDC+' Ohm','Overlap Cap.',S.CGSO+' fF/um');
    row('Vth Sigma',S.VTH0_DFT+' mV','','');
"""
content = content.replace(old_pdf_text, new_pdf_text)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("BSIM-CMG Enhancements successfully applied.")
