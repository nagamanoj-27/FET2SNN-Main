import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# Pattern to capture everything from <!-- LIF Wrap --> to the end of snnSimCard
# snnSimCard ends with a div. We can match up to:
#      </div>
#      <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.5rem;">
#        <button class="btn ba" id="snn-btn-csv-raster" style="flex:1"><i class="fas fa-file-csv"></i> Raster CSV</button>
#        <button class="btn ba" id="snn-btn-csv-weights" style="flex:1"><i class="fas fa-file-csv"></i> Weights CSV</button>
#      </div>
#    </div>

pattern = r'(    <!-- LIF Wrap -->.*?<!-- SNN Simulator Module -->.*?id="snn-btn-csv-weights".*?</div>\s*</div>)'

match = re.search(pattern, content, re.DOTALL)
if match:
    snn_block = match.group(1)
    
    # Remove from original location
    content = content[:match.start()] + content[match.end():]
    
    # Insert after </div><!-- /mg -->
    mg_pattern = r'</div><!-- /mg -->'
    mg_match = re.search(mg_pattern, content)
    if mg_match:
        content = content[:mg_match.end()] + '\n\n' + snn_block + '\n' + content[mg_match.end():]
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully moved LIF and SNN modules outside the main grid!")
    else:
        print("Could not find <!-- /mg -->")
else:
    print("Could not find the LIF/SNN block pattern!")
