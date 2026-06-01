import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Define debouncedComputeAll right before `function wire(`
wire_target = "function wire(slId,nmId,key){"
debounce_code = """let computeAllTimeout = null;
function debouncedComputeAll() {
    if (computeAllTimeout) clearTimeout(computeAllTimeout);
    computeAllTimeout = setTimeout(() => {
        computeAll();
    }, 150);
}

function wire(slId,nmId,key){"""

if wire_target in content and 'debouncedComputeAll' not in content:
    content = content.replace(wire_target, debounce_code)

# 2. Replace computeAll() calls in wire() and wireLog() and event listeners with debouncedComputeAll()
# We need to replace exactly the ones inside the input/change event listeners for sliders.
# We will do a generic replacement for all `computeAll();` in that block.
# Actually, replacing all `computeAll();` with `debouncedComputeAll();` inside the DOMContentLoaded block might be safe, except we might want an initial un-debounced computeAll() at the end.
# Let's just replace `computeAll();` inside the wire and wireLog functions, and the dropdown listeners.

# In wire:
old_wire = """  sl.addEventListener('input',()=>{ S[key]=parseFloat(sl.value); if(nm)nm.value=S[key]; computeAll(); });
  if(nm) nm.addEventListener('change',()=>{ S[key]=parseFloat(nm.value); sl.value=S[key]; computeAll(); });"""
new_wire = """  sl.addEventListener('input',()=>{ S[key]=parseFloat(sl.value); if(nm)nm.value=S[key]; debouncedComputeAll(); });
  if(nm) nm.addEventListener('change',()=>{ S[key]=parseFloat(nm.value); sl.value=S[key]; debouncedComputeAll(); });"""
content = content.replace(old_wire, new_wire)

old_wireLog = """  sl.addEventListener('input',()=>{
    const v=Math.pow(10,minExp+parseFloat(sl.value)*(maxExp-minExp));
    S[key]=v;
    if(nm)nm.innerText=v.toExponential(2);
    computeAll();
  });"""
new_wireLog = """  sl.addEventListener('input',()=>{
    const v=Math.pow(10,minExp+parseFloat(sl.value)*(maxExp-minExp));
    S[key]=v;
    if(nm)nm.innerText=v.toExponential(2);
    debouncedComputeAll();
  });"""
content = content.replace(old_wireLog, new_wireLog)

# Also dropdowns
dropdowns_old = [
    "S.ChMat = e.target.value;\n      computeAll();",
    "S.SpArch = e.target.value;\n      computeAll();",
    "S.Corner = e.target.value;\n      computeAll();",
    "else{ ckw.style.display='none'; S.kSpacer=parseFloat(sel.value); computeAll(); }",
    "if(v>=1&&v<=44){ S.kSpacer=v; computeAll(); }"
]
dropdowns_new = [
    "S.ChMat = e.target.value;\n      debouncedComputeAll();",
    "S.SpArch = e.target.value;\n      debouncedComputeAll();",
    "S.Corner = e.target.value;\n      debouncedComputeAll();",
    "else{ ckw.style.display='none'; S.kSpacer=parseFloat(sel.value); debouncedComputeAll(); }",
    "if(v>=1&&v<=44){ S.kSpacer=v; debouncedComputeAll(); }"
]

for o, n in zip(dropdowns_old, dropdowns_new):
    content = content.replace(o, n)
    
# Aging sliders
aging_old1 = "if(typeof fallbackComputeAll === 'function') fallbackComputeAll();"
aging_new1 = "if(typeof debouncedComputeAll === 'function') debouncedComputeAll(); else if(typeof fallbackComputeAll === 'function') fallbackComputeAll();"
content = content.replace(aging_old1, aging_new1)


with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Debounce logic injected.")
