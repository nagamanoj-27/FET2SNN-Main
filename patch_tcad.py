import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Add preserveDrawingBuffer
content = content.replace(
    'const renderer = new THREE.WebGLRenderer({ antialias: true });',
    'const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });'
)

# 2. Add GLTFExporter import and expose scene and exporter globally so we can use them in the DOM
import_patch = """    import * as THREE from 'three';
    import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
    import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
    import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
"""
content = content.replace("""    import * as THREE from 'three';
    import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
    import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';""", import_patch)

# Expose globals so regular DOM buttons can access them
expose_patch = """      const scene = new THREE.Scene();
      window.tcadScene = scene;
      window.tcadGLTFExporter = new GLTFExporter();
"""
content = content.replace("      const scene = new THREE.Scene();", expose_patch)

# 3. Add buttons to tcadPanel
# tcadPanel ends with:
#       <div style="text-align:center; display:flex; flex-wrap:wrap; justify-content:center; gap:0.5rem;">
#         ... badges ...
#       </div>
#     </div>

# Let's find the closing of tcadPanel.
# The badges div is the last child.
badges_html = '<span class="bdg" style="color:#8b4513; border-color:#8b4513; background:transparent;"><i class="fas fa-square" style="color:#8b4513"></i> Substrate</span>\n      </div>'

buttons_html = badges_html + """
      <!-- Export Tools -->
      <div style="display:flex; justify-content:center; gap:0.5rem; margin-top:1rem; flex-wrap:wrap;">
        <button class="btn ba" id="tcad-btn-png"><i class="fas fa-image"></i> Download PNG</button>
        <button class="btn ba" id="tcad-btn-csv"><i class="fas fa-file-csv"></i> Download CSV</button>
        <button class="btn ba" id="tcad-btn-gltf"><i class="fas fa-cube"></i> Export 3D GLTF</button>
      </div>
"""
content = content.replace(badges_html, buttons_html)

# 4. Add the Javascript logic for the buttons at the end of the file, before </body>
js_logic = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // TCAD Export Hooks
    document.getElementById('tcad-btn-png').addEventListener('click', () => {
        const canvas = document.querySelector('#threeCanvas canvas');
        if(!canvas) return alert("3D Canvas not found!");
        const link = document.createElement('a');
        link.download = 'TCAD_Structure.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    });

    document.getElementById('tcad-btn-gltf').addEventListener('click', () => {
        if(!window.tcadGLTFExporter || !window.tcadScene) {
            return alert('GLTFExporter library not loaded yet!');
        }
        window.tcadGLTFExporter.parse(window.tcadScene, function(gltf) {
            const output = JSON.stringify(gltf, null, 2);
            const blob = new Blob([output], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.style.display = 'none';
            link.href = url;
            link.download = 'TCAD_Structure.gltf';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }, { binary: false });
    });

    document.getElementById('tcad-btn-csv').addEventListener('click', () => {
        let csv = "Parameter,Value,Unit\\n";
        const inputs = ['Lg', 'Wns', 'Tns', 'Nstacks', 'Tox', 'Nsub', 'Nch', 'Nsd'];
        inputs.forEach(id => {
            let el = document.getElementById('n'+id);
            if(el) {
                let val = el.value;
                let unit = 'nm';
                if(id.startsWith('N') && id !== 'Nstacks') unit = 'cm^-3';
                if(id === 'Nstacks') unit = '';
                csv += `${id},${val},${unit}\\n`;
            }
        });
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'TCAD_Parameters.csv';
        link.click();
    });
});
</script>
</body>
"""
content = content.replace('</body>', js_logic)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected TCAD Export Buttons and Logic!")
