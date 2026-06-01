import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

html_patch = """
<!-- Founder / Creator Credit -->
<div class="founder-credit">
  <span>🔬 FET2SNN Dashboard — </span>
  <strong>M.Manoj</strong>
  <span> (ECE 3rd year) | Founder, Creator & Developer | </span>
  <a href="https://instagram.com/nagamanoj_27" target="_blank" class="insta-link">📷 @nagamanoj_27</a>
</div>
"""

css_patch = """
.founder-credit {
  position: fixed;
  bottom: 12px;
  right: 12px;
  font-size: 0.75rem;
  font-family: monospace;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(6px);
  padding: 6px 14px;
  border-radius: 40px;
  color: #cccccc;
  z-index: 1000;
  opacity: 0.45;
  transition: opacity 0.2s ease;
  pointer-events: auto;
}

.founder-credit:hover {
  opacity: 1;
}

.founder-credit strong {
  color: #66ccff;
  font-weight: 600;
}

.insta-link {
  color: #e4405f;
  text-decoration: none;
  margin-left: 4px;
}

.insta-link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .founder-credit {
    bottom: 8px;
    right: auto;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.65rem;
    white-space: nowrap;
  }
}
"""

if 'founder-credit' not in content:
    # Inject CSS
    content = content.replace('/* INPUTS */', css_patch + '\n/* INPUTS */')
    # Inject HTML
    content = content.replace('</body>', html_patch + '\n</body>')
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched.")
else:
    print("Already patched.")
