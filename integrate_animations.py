import re

with open('index.html', encoding='utf-8') as f:
    index_lines = f.readlines()

with open('educational_animations.html', encoding='utf-8') as f:
    edu_content = f.read()

# 1. Extract HTML
html_match = re.search(r'<div class="cards-container">(.*?)<footer>', edu_content, re.DOTALL)
edu_html = '<div class="cards-container">' + html_match.group(1) + '<!-- /cards-container -->'

# 2. Extract JS
js_match = re.search(r'<script>(.*?)</script>', edu_content, re.DOTALL)
edu_js = js_match.group(1)

# 3. Extract CSS (only specific classes)
css_match = re.search(r'<style>(.*?)</style>', edu_content, re.DOTALL)
css_full = css_match.group(1)
# Keep only relevant classes
edu_css = ""
for block in css_full.split('}'):
    if any(k in block for k in ['.cards-container', '.canvas-container', '.controls', 'input[type="range"]', '.description', '.badge', '.speed-control']):
        if '.card' in block and '.card h2' not in block and ':hover' not in block:
            pass # index.html already has .card, let's just keep the specifics
        else:
            edu_css += block + "}\n"

# 4. Find </style> in index.html
style_end_idx = -1
for i, line in enumerate(index_lines):
    if '</style>' in line:
        style_end_idx = i
        break

# 5. Build new index.html
new_index = []
new_index.extend(index_lines[:style_end_idx])
new_index.append(edu_css + '\n')
new_index.extend(index_lines[style_end_idx:1054])
new_index.append(edu_html + '\n')
new_index.extend(index_lines[1091:3474])
new_index.append(edu_js + '\n')
new_index.extend(index_lines[4008:])

with open('index.html', 'w', encoding='utf-8') as f:
    f.writelines(new_index)

print("Integration complete!")
