import re

with open('snn-simulator.js', encoding='utf-8') as f:
    content = f.read()

modal_logic = """
// --- Matrix Editor Modal Logic ---
let tempMatrix = null;

function openMatrixModal() {
    const N = snnSimState.N;
    tempMatrix = new Float64Array(snnSimState.W);
    const container = document.getElementById('snnMatrixContainer');
    if(!container) return;
    
    let html = '<table style="border-collapse:collapse; text-align:center; color:#fff; font-family:monospace; font-size:0.8rem;">';
    // Header
    html += '<tr><th style="padding:5px; border:1px solid #444; background:#222;">Pre \\\\ Post</th>';
    for(let i=0; i<N; i++) html += `<th style="padding:5px; border:1px solid #444; background:#222;">${i}</th>`;
    html += '</tr>';
    
    // Body
    for(let i=0; i<N; i++) {
        html += `<tr><th style="padding:5px; border:1px solid #444; background:#222;">${i}</th>`;
        for(let j=0; j<N; j++) {
            let val = tempMatrix[i*N + j];
            let bg = i===j ? '#333' : (val > 0 ? `rgba(16, 185, 129, ${Math.min(1, val/5)})` : 'transparent');
            html += `<td style="padding:2px; border:1px solid #444; background:${bg};">
                        <input type="number" step="0.1" data-r="${i}" data-c="${j}" value="${val.toFixed(2)}" ${i===j?'disabled':''} style="width:50px; background:transparent; border:none; color:#fff; text-align:center;">
                     </td>`;
        }
        html += '</tr>';
    }
    html += '</table>';
    container.innerHTML = html;
    
    // Inputs change listener
    container.querySelectorAll('input').forEach(inp => {
        inp.addEventListener('change', e => {
            let r = parseInt(e.target.dataset.r);
            let c = parseInt(e.target.dataset.c);
            let val = parseFloat(e.target.value);
            if(!isNaN(val)) tempMatrix[r*N + c] = val;
            let bg = r===c ? '#333' : (val > 0 ? `rgba(16, 185, 129, ${Math.min(1, val/5)})` : 'transparent');
            e.target.parentElement.style.background = bg;
        });
    });
    
    document.getElementById('snnMatrixModal').style.display = 'flex';
}

function closeMatrixModal() {
    document.getElementById('snnMatrixModal').style.display = 'none';
}

function saveMatrixModal() {
    if(tempMatrix) {
        snnSimState.W.set(tempMatrix);
        renderHeatmap();
    }
    closeMatrixModal();
}

// Hook up modal buttons
document.addEventListener('DOMContentLoaded', () => {
    // These might be injected late, so we use document-level delegation or wait for init
});
"""

# Append to end
content += "\n" + modal_logic

# Find the startSNNSimulator function to hook the buttons
hook_code = """
    document.getElementById('snn-btn-edit-matrix').addEventListener('click', openMatrixModal);
    document.getElementById('snn-btn-close-modal').addEventListener('click', closeMatrixModal);
    document.getElementById('snn-btn-cancel-matrix').addEventListener('click', closeMatrixModal);
    document.getElementById('snn-btn-save-matrix').addEventListener('click', saveMatrixModal);
    
    document.getElementById('snn-init-method').addEventListener('change', e => {
        initWeights(e.target.value, 1, 5, 30);
    });
"""

content = content.replace("initSNNChart();", "initSNNChart();\n" + hook_code)

with open('snn-simulator.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched snn-simulator.js!")
