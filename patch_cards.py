import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# We need to wrap both cards in <div class="two">
# They look like this:
# <!-- Sensitivity Analysis (Tornado Chart) Card -->
# <div class="card" id="snnTornadoCard" style="margin-bottom:1.5rem;">
# ...
# </div>
# <!-- Device Aging & Reliability Projector Card -->
# <div class="card" id="snnAgingCard" style="margin-bottom:1.5rem;">
# ...
# </div>

# Find the start of the Tornado Card
tornado_start = content.find('<!-- Sensitivity Analysis (Tornado Chart) Card -->')
# Find the end of Aging Card
aging_start = content.find('<!-- Device Aging & Reliability Projector Card -->')
if tornado_start != -1 and aging_start != -1:
    # Need to find the end of the aging card. It ends right before <!-- SNN Energy Settings Modal -->
    aging_end = content.find('<!-- SNN Energy Settings Modal -->', aging_start)
    if aging_end != -1:
        # Extract the block
        block = content[tornado_start:aging_end]
        
        # Modify the cards to have height: 100% and margin-bottom: 0 instead of 1.5rem so they align nicely inside the grid
        block = block.replace('style="margin-bottom:1.5rem;"', 'style="height:100%; display:flex; flex-direction:column; justify-content:flex-start;"')
        
        # Wrap the block
        new_block = '<div class="two" style="margin-bottom:1.5rem; align-items:stretch;">\n' + block + '</div>\n'
        
        # We need to make sure we don't accidentally wrap it twice if the script is run multiple times
        if '<div class="two" style="margin-bottom:1.5rem; align-items:stretch;">' not in content:
            content = content[:tornado_start] + new_block + content[aging_end:]
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("Patched.")
        else:
            print("Already patched.")
    else:
        print("Could not find SNN Energy Settings Modal")
else:
    print("Could not find cards")
