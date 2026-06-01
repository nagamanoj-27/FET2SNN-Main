import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Inject Advanced Manufacturing Parameters UI
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
# Find the exact string using regex
ui_regex = re.compile(r'<p class="mn"><i class="fas fa-info-circle"></i> Analytical models calibrated')
if 'MANUFACTURING PARAMETERS (BSIM-CMG)' not in content:
    content = re.sub(ui_regex, ui_injection + r'\n    \g<0>', content)

# 2. Add defaults to S object and add wire logic
old_S_regex = re.compile(r"const S=\{Lg:12,Wns:20,Tns:5,Nstacks:3,kSpacer:7,EOT:\.8,Nch:1e16,NSD:1e20,Vdd:\.7,T:25,ChMat:'Si',SpArch:'single',Corner:'TT'\};")
new_S = "const S={Lg:12,Wns:20,Tns:5,Nstacks:3,kSpacer:7,EOT:.8,Nch:1e16,NSD:1e20,Vdd:.7,T:25,ChMat:'Si',SpArch:'single',Corner:'TT',NSHEET_SPACE:20,CORNER_RAD:5,QCSCALE:1.0,SHMOD:1,RTH0:15000,RDC:50,CGSO:0.1,VTH0_DFT:2.5};"
if 'NSHEET_SPACE:20' not in content:
    content = re.sub(old_S_regex, new_S, content)

# Wire logic
wire_regex = re.compile(r"wire\('slLg','nLg','Lg'\);")
new_wire_logic = """wire('slLg','nLg','Lg');
  wire('slNspace','nNspace','NSHEET_SPACE');
  wire('slCornerR','nCornerR','CORNER_RAD');
  wire('slQcScale','nQcScale','QCSCALE');
  wire('slRth0','nRth0','RTH0');
  wire('slRdc','nRdc','RDC');
  wire('slCgso','nCgso','CGSO');
  wire('slVthDft','nVthDft','VTH0_DFT');
  
  const selShmod = document.getElementById('selShmod');
  if(selShmod) selShmod.addEventListener('change', (e)=>{ S.SHMOD=parseInt(e.target.value); if(typeof debouncedComputeAll==='function') debouncedComputeAll(); });"""
if "wire('slNspace','nNspace','NSHEET_SPACE');" not in content:
    content = re.sub(wire_regex, new_wire_logic, content)

# 3. Fix genBsimCard referencing undefined variables if somehow S still doesn't have them
# We already did this in patch_bsim.py, but let's make sure it handles undefined S.NSHEET_SPACE in genBsimCard.
genBsim_regex = re.compile(r'function genBsimCard\(\)\{.*?document\.getElementById\(\'bsimCard\'\)\.textContent=card;\s*\}', re.DOTALL)
new_genBsim = """function genBsimCard(){
  const H=parseFloat(document.getElementById('nHfin').value)||40;
  const T_fin=parseFloat(document.getElementById('nTfin').value)||8;
  const DF=parseFloat(document.getElementById('nDelfin').value)||0;
  const N=parseFloat(document.getElementById('nNfinB').value)||10;
  const D=parseFloat(document.getElementById('nDiam').value)||8;
  const BULKMOD=document.getElementById('selBulk') ? parseInt(document.getElementById('selBulk').value) : 1;
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

  // Defaults fallback
  const _NSPACE = S.NSHEET_SPACE || 20;
  const _CORNER = S.CORNER_RAD || 5;
  const _QCSCALE = S.QCSCALE !== undefined ? S.QCSCALE : 1.0;
  const _SHMOD = S.SHMOD !== undefined ? S.SHMOD : 1;
  const _RTH0 = S.RTH0 || 15000;
  const _RDC = S.RDC || 50;
  const _CGSO = S.CGSO || 0.1;
  const _VTH0_DFT = S.VTH0_DFT || 2.5;

  let finBlock='';
  if(bGeomod===6){ // Nanosheet
    finBlock=`+ L       = ${(S.Lg*1e-9).toExponential(3)}\\n+ W       = ${(S.Wns*1e-9).toExponential(3)}\\n+ NSHEETS = ${S.Nstacks}\\n+ NSHEET_SPACE = ${(_NSPACE*1e-9).toExponential(3)}\\n+ CORNER  = ${(_CORNER*1e-9).toExponential(3)}\\n+ THICK   = ${(S.Tns*1e-9).toExponential(3)}`;
  } else {
    finBlock=`+ HFIN    = ${(H*1e-9).toExponential(3)}\\n+ TFIN    = ${(T_fin*1e-9).toExponential(3)}\\n+ NFIN    = ${N}`;
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
+ QCSCALE = ${_QCSCALE.toFixed(2)}
+ QMFACTOR= 0.8
+ VQIM    = 0.05

* ----- SELF-HEATING -----
+ SHMOD   = ${_SHMOD}
+ RTH0    = ${_RTH0}
+ CTH0    = 1.0E-11

* ----- PARASITICS -----
+ RDSMOD  = 1
+ RDC     = ${_RDC}
+ RSC     = ${_RDC}
+ CGSO    = ${(_CGSO*1e-9).toExponential(2)}
+ CGDO    = ${(_CGSO*1e-9).toExponential(2)}
+ CIT     = 0.0

* ----- PROCESS VARIATION (Monte Carlo) -----
+ VTH0_DFT = ${(_VTH0_DFT/1000).toExponential(3)}
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
content = re.sub(genBsim_regex, new_genBsim, content)

# 4. Corner UI Button
# Find: <button class="btn bb" onclick="dlBsimCard()"><i class="fas fa-file-pdf"></i> Download .pdf</button>
spice_btn_regex = re.compile(r'<button class="btn bb" onclick="dlBsimCard\(\)"><i class="fas fa-file-pdf"></i> Download \.pdf</button>')
new_spice_btn = """<button class="btn bb" onclick="dlBsimCard()"><i class="fas fa-download"></i> Download .MODEL</button>
          <button class="btn bb" onclick="dlCornerLibrary()"><i class="fas fa-book"></i> Export Corner Lib</button>"""
if "Export Corner Lib" not in content:
    content = re.sub(spice_btn_regex, new_spice_btn, content)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch 2 successfully applied.")
