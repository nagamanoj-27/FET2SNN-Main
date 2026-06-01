import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# Add CSS for .chart-dl-side
if '.chart-dl-side' not in content:
    css_patch = """
.chart-dl-side { display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 1rem; height: 100%; }
.chart-dl-side .btn { font-size: 0.85rem; padding: 0.5rem 1.2rem; width: 140px; justify-content: center; }
"""
    content = content.replace('/* INPUTS */', css_patch + '\n/* INPUTS */')

# Find the SNN PERFORMANCE section and replace chart-dl-row with chart-dl-side
section_start = content.find('<!-- SNN PERFORMANCE VS DEVICE PARAMETERS -->')
section_end = content.find('<!-- TOOLS & EXPORT -->', section_start)

if section_start != -1 and section_end != -1:
    section_content = content[section_start:section_end]
    new_section = section_content.replace('class="chart-dl-row"', 'class="chart-dl-side"')
    content = content[:section_start] + new_section + content[section_end:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched.")
