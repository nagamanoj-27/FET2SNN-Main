import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

modal_html = """
<!-- SNN Matrix Editor Modal -->
<div id="snnMatrixModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:9999; align-items:center; justify-content:center;">
    <div style="background:var(--card); border:1px solid var(--border); border-radius:12px; padding:20px; max-width:90%; max-height:90%; overflow:auto; display:flex; flex-direction:column;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
            <h3 style="margin:0;"><i class="fas fa-th"></i> Edit Weight Matrix</h3>
            <button id="snn-btn-close-modal" style="background:none; border:none; color:var(--text); cursor:pointer; font-size:1.2rem;"><i class="fas fa-times"></i></button>
        </div>
        <p style="font-size:0.9rem; color:#aaa; margin-bottom:15px;">Click a cell to edit its synaptic weight (nS) from Pre (Row) to Post (Column).</p>
        <div id="snnMatrixContainer" style="overflow:auto; max-height:500px; border:1px solid var(--border);"></div>
        <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:15px;">
            <button class="btn ba" id="snn-btn-cancel-matrix">Cancel</button>
            <button class="btn bb" id="snn-btn-save-matrix">Save Matrix</button>
        </div>
    </div>
</div>
"""

# Insert modal before </body>
content = content.replace('</body>', modal_html + '\n</body>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected SNN Modal HTML!")
