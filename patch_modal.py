import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Modify the Validation Card to be a modal
target = """    <!-- Complete Model Validation Suite Card -->
    <div class="card" id="snnValidationCard" style="margin-bottom:1.5rem;">"""
    
new = """    <!-- Complete Model Validation Suite Modal -->
<div id="snnValidationModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:9999; justify-content:center; align-items:center;">
    <div class="card" id="snnValidationCard" style="width:90%; max-width:1000px; max-height:90vh; overflow-y:auto; padding:1.5rem; margin-bottom:0;">"""

if target in content:
    content = content.replace(target, new)
    
# We also need to close the modal div at the end of the validation card.
# The validation card ends right before `<!-- SNN Energy Settings Modal -->`
end_target = """        </div>
        
      </div>
    </div>

<!-- SNN Energy Settings Modal -->"""

end_new = """        </div>
        
      </div>
    </div>
</div>

<!-- SNN Energy Settings Modal -->"""

if end_target in content:
    content = content.replace(end_target, end_new)

# Add a close button to the modal header
header_target = """        <span><i class="fas fa-check-double"></i> Model Validation Suite <span class="ttip" style="margin-left:5px; font-size:0.85rem; font-weight:normal;">ⓘ<span class="ttip-text">Validation against 17 benchmark devices. R² and MAE reflect the accuracy of the analytical proxy model vs rigorous TCAD physics.</span></span></span>
        <span style="font-size:0.85rem; color:#888;">Electrical model validation (Vth, SS, Ion) | SNN predictor residuals</span>
      </div>"""
      
header_new = """        <span><i class="fas fa-check-double"></i> Model Validation Suite <span class="ttip" style="margin-left:5px; font-size:0.85rem; font-weight:normal;">ⓘ<span class="ttip-text">Validation against 17 benchmark devices. R² and MAE reflect the accuracy of the analytical proxy model vs rigorous TCAD physics.</span></span></span>
        <div>
            <span style="font-size:0.85rem; color:#888; margin-right:1rem;">Electrical model validation (Vth, SS, Ion) | SNN predictor residuals</span>
            <button class="btn bb" onclick="document.getElementById('snnValidationModal').style.display='none'" style="padding:0.2rem 0.6rem; font-size:0.8rem;"><i class="fas fa-times"></i> Close</button>
        </div>
      </div>"""

# NOTE: python string replace can be tricky with unicode 'ⓘ' or '²'. We will use re.sub for safety, or just standard replace if it works (it should, utf-8).
if "Model Validation Suite" in content:
    content = content.replace(
        '<span style="font-size:0.85rem; color:#888;">Electrical model validation (Vth, SS, Ion) | SNN predictor residuals</span>\n      </div>',
        '<div><span style="font-size:0.85rem; color:#888; margin-right:1rem;">Electrical model validation (Vth, SS, Ion) | SNN predictor residuals</span><button class="btn bb" onclick="document.getElementById(\'snnValidationModal\').style.display=\'none\'" style="padding:0.2rem 0.6rem; font-size:0.8rem;"><i class="fas fa-times"></i> Close</button></div>\n      </div>'
    )

# 2. Add the button to open it next to "Export PDF"
btn_target = '<button class="btn bb" onclick="exportPDF()"><i class="fas fa-file-pdf"></i> Export PDF</button>'
btn_new = '<button class="btn bb" onclick="exportPDF()"><i class="fas fa-file-pdf"></i> Export PDF</button>\n    <button class="btn" style="background:var(--purp); border:none;" onclick="document.getElementById(\'snnValidationModal\').style.display=\'flex\'"><i class="fas fa-check-double"></i> Validation Suite</button>'

if btn_target in content:
    content = content.replace(btn_target, btn_new)


with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched.")
