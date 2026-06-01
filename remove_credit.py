import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# We want to remove:
# <!-- Founder / Creator Credit -->
# <div class="founder-credit">
# ...
# </div>

pattern = re.compile(r'<!-- Founder / Creator Credit -->\s*<div class="founder-credit">.*?</div>', re.DOTALL)
content = re.sub(pattern, '', content)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Credit block removed.")
