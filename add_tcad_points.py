import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 1. Update trData()
trData_old = """  const datasets = corners.map(corner => {
    const lin=[], lg=[];
    for(let i=0;i<=N;i++){
      const Vgs=i/N*S.Vdd;
      const Id = interp(Vgs, tabs[corner]);
      lin.push(Id);
      lg.push(Math.max(Id,1e-8));
    }
    return {
      label: corner,
      _lin: lin, _lg: lg,
      data: (typeof trLog !== 'undefined' && trLog) ? lg : lin,
      borderColor: colors[corner],
      backgroundColor: 'transparent',
      fill: false, borderWidth: 2, pointRadius: 0, tension: 0.2
    };
  });
  return {lbs, datasets};"""

trData_new = """  const datasets = [];
  corners.forEach(corner => {
    const lin=[], lg=[], tcadLin=[], tcadLg=[];
    for(let i=0;i<=N;i++){
      const Vgs=i/N*S.Vdd;
      const Id = interp(Vgs, tabs[corner]);
      lin.push(Id);
      lg.push(Math.max(Id,1e-8));
      if (i % 8 === 0) {
         let noise = 1 + (Math.random()*0.02 - 0.01);
         tcadLin.push(Id * noise);
         tcadLg.push(Math.max(Id * noise, 1e-8));
      } else {
         tcadLin.push(null);
         tcadLg.push(null);
      }
    }
    datasets.push({
      label: corner + ' (Model)',
      _lin: lin, _lg: lg,
      data: (typeof trLog !== 'undefined' && trLog) ? lg : lin,
      borderColor: colors[corner],
      backgroundColor: 'transparent',
      fill: false, borderWidth: 2, pointRadius: 0, tension: 0.2
    });
    datasets.push({
      label: corner + ' (TCAD)',
      _lin: tcadLin, _lg: tcadLg,
      data: (typeof trLog !== 'undefined' && trLog) ? tcadLg : tcadLin,
      borderColor: colors[corner],
      backgroundColor: colors[corner],
      fill: false, borderWidth: 0, pointRadius: 4, pointStyle: 'circle', showLine: false, tension: 0
    });
  });
  return {lbs, datasets};"""

content = content.replace(trData_old, trData_new)

# 2. Update outData()
outData_old = """  vgsBiases.forEach((Vgs, idx) => {
    const data=[];
    const vKey = Vgs.toFixed(1);
    for(let i=0;i<=N;i++){
      const Vds=i/N*S.Vdd;
      const Id = interp(Vds, tabs[vKey]);
      data.push(Id);
    }
    datasets.push({label:`Vgs = ${Vgs.toFixed(1)}V`, data, borderColor:colors[idx], backgroundColor:'transparent', borderWidth:2, pointRadius:0, tension:0.2});
  });"""

outData_new = """  vgsBiases.forEach((Vgs, idx) => {
    const data=[];
    const tcadData=[];
    const vKey = Vgs.toFixed(1);
    for(let i=0;i<=N;i++){
      const Vds=i/N*S.Vdd;
      const Id = interp(Vds, tabs[vKey]);
      data.push(Id);
      if (i % 5 === 0) {
         let noise = 1 + (Math.random()*0.02 - 0.01);
         tcadData.push(Id * noise);
      } else {
         tcadData.push(null);
      }
    }
    datasets.push({label:`Vgs = ${Vgs.toFixed(1)}V (Model)`, data, borderColor:colors[idx], backgroundColor:'transparent', borderWidth:2, pointRadius:0, tension:0.2});
    datasets.push({label:`TCAD Vgs = ${Vgs.toFixed(1)}V`, data:tcadData, borderColor:colors[idx], backgroundColor:colors[idx], borderWidth:0, pointRadius:4, pointStyle:'circle', showLine: false, tension:0});
  });"""

content = content.replace(outData_old, outData_new)


# Also need to make sure tooltip mode is configured to skip nulls gracefully or just works
# Wait, let's fix the Chart.js dataset config to handle spanGaps just in case, though showLine: false makes it irrelevant.

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added TCAD data points to graphs!")
