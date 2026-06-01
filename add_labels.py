import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

labels_old = """          // Dimension Labels
          const topY = startY + Nstacks * (Tns + spacing) + 0.5;
          const lgLabel = createLabel(`Lg = ${document.getElementById('nLg').value} nm`, '#88aaff', new THREE.Vector3(0, topY, 0), '12px');
          const wnsLabel = createLabel(`Wns = ${document.getElementById('nWns').value} nm`, '#88aaff', new THREE.Vector3(Wns/2 + 1, topY - 0.5, 0), '12px');
          const tnsLabel = createLabel(`Tns = ${document.getElementById('nTns').value} nm`, '#88aaff', new THREE.Vector3(-Wns/2 - 1, startY, 0), '12px');
          labelGroup.add(lgLabel, wnsLabel, tnsLabel);"""

labels_new = """          // Dimension Labels
          const topY = startY + Nstacks * (Tns + spacing) + 0.5;
          const lgLabel = createLabel(`Lg = ${document.getElementById('nLg').value} nm`, '#88aaff', new THREE.Vector3(0, topY, 0), '12px');
          const wnsLabel = createLabel(`Wns = ${document.getElementById('nWns').value} nm`, '#88aaff', new THREE.Vector3(Wns/2 + 1, topY - 0.5, 0), '12px');
          const tnsLabel = createLabel(`Tns = ${document.getElementById('nTns').value} nm`, '#88aaff', new THREE.Vector3(-Wns/2 - 1, startY, 0), '12px');
          
          const gateLabel = createLabel('GATE', '#ffd700', new THREE.Vector3(0, topY - 0.8, Lg/2 + 0.8), '11px');
          const sourceLabel = createLabel('SOURCE', '#ff6347', new THREE.Vector3(0, startY + (Tns + spacing)*(Math.max(0, Nstacks-2)), -Lg/2 - sdExt/2), '11px');
          const drainLabel = createLabel('DRAIN', '#ff6347', new THREE.Vector3(0, startY + (Tns + spacing)*(Math.max(0, Nstacks-2)), Lg/2 + sdExt/2), '11px');
          const subLabel = createLabel('SUBSTRATE', '#5577aa', new THREE.Vector3(Wns/2 + 0.5, -0.5, Lg/2 + 0.5), '10px');

          labelGroup.add(lgLabel, wnsLabel, tnsLabel, gateLabel, sourceLabel, drainLabel, subLabel);"""

content = content.replace(labels_old, labels_new)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added component labels to 3D Viewer!")
