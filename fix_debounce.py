import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

debounce_func = """let computeAllTimeout = null;
function debouncedComputeAll() {
    if (computeAllTimeout) clearTimeout(computeAllTimeout);
    computeAllTimeout = setTimeout(() => {
        if(typeof computeAll === 'function') computeAll();
    }, 150);
}

function wire(slId,"""

if 'function debouncedComputeAll' not in content:
    content = content.replace('function wire(slId,', debounce_func)

# Fix the wireLog function missing debouncer
old_wireLog_regex = re.compile(r'function wireLog\([^)]+\)\{.*?computeAll\(\);\s*\}\);', re.DOTALL)
match = re.search(old_wireLog_regex, content)
if match:
    old_match = match.group(0)
    new_match = old_match.replace('computeAll();', 'if(typeof debouncedComputeAll === \'function\') debouncedComputeAll();')
    content = content.replace(old_match, new_match)

# And fix the Bsim sliders which have `genBsimCard();`
# Wait, they just call genBsimCard, which is fine, it doesn't do ML inference.

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Debounce function properly defined.")
