with open('index.html', encoding='utf-8') as f:
    lines = f.readlines()
v_start, v_end, js_start, js_end = -1, -1, -1, -1
for i, line in enumerate(lines):
    if 'id="videoPanel"' in line: v_start = i
    if v_start != -1 and v_end == -1 and '</div><!-- /pw -->' in line: v_end = i - 1
    if 'let playing1 = false;' in line: js_start = i - 2
    if 'function localVideoLoop()' in line: js_end = i + 5
print(f"Video HTML: {v_start+1} to {v_end+1}")
print(f"JS: {js_start+1} to {js_end+1}")
