import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Update button UI
old_btn = '<button class="btn bb" onclick="dlBsimCard()"><i class="fas fa-download"></i> Download .mod</button>'
new_btn = '<button class="btn bb" onclick="dlBsimCard()"><i class="fas fa-file-pdf"></i> Download .pdf</button>'

if old_btn in content:
    content = content.replace(old_btn, new_btn)

# 2. Update dlBsimCard() function
old_fn = """function dlBsimCard(){
  dl(document.getElementById('bsimCard').textContent,'bsimcmg_model.mod','text/plain');
}"""

new_fn = """function dlBsimCard(){
  try {
    const {jsPDF} = window.jspdf;
    const doc = new jsPDF({orientation:'portrait', unit:'mm', format:'a4'});
    const text = document.getElementById('bsimCard').textContent;
    doc.setFont("courier", "normal");
    doc.setFontSize(10);
    // Split text so it wraps nicely
    const lines = doc.splitTextToSize(text, 180);
    
    // Check if it fits on one page, if not, jsPDF handles it automatically or we add pages manually
    let y = 15;
    for (let i = 0; i < lines.length; i++) {
        if (y > 280) {
            doc.addPage();
            y = 15;
        }
        doc.text(lines[i], 15, y);
        y += 4;
    }
    
    doc.save('bsimcmg_model.pdf');
  } catch(e) {
    alert("Error generating PDF: " + e.message);
  }
}"""

if old_fn in content:
    content = content.replace(old_fn, new_fn)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched.")
