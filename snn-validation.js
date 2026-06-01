// snn-validation.js
// Model Validation Scatter Plots & Residual Plots

window.validationScatterChart = null;
window.validationResidualChart = null;
window.validationMetrics = { vth: { r2:0, mae:0 }, ss: { r2:0, mae:0 }, ion: { r2:0, mae:0 } };
window.validationPoints = { vth: [], ss: [], ion: [] };
window.residualsArray = []; // { predicted, actual, residual, label }
window.stdResidual = 0;
window.meanResidual = 0;

window.computeValidationData = function() {
    if (typeof BD === 'undefined') return;
    
    // For R2 calculations
    let sumTcadVth = 0, sumTcadSS = 0, sumTcadIon = 0;
    let sumRes = 0;
    
    BD.forEach(device => {
        // Construct nominal S configuration based on benchmark dataset
        const S_bench = {
            Lg: device.Lg,
            Wns: device.Wns,
            Tns: device.Tns,
            Nstacks: device.N || 3,
            kSpacer: device.k,
            EOT: 1.5,
            Vdd: 0.7, // Typical Vdd
            T: 300,
            ChMat: (device.ref.includes('Ge') ? 'Ge' : 'Si'),
            SpArch: 'Single',
            Corner: 'TT'
        };
        
        // Compute predicted electricals using analytical model
        const d_pred = computeDevice(S_bench);
        const predVth = d_pred.Vth;
        const predSS = d_pred.SS * 1000; // convert to mV/dec
        
        let Weff_nm = S_bench.Nstacks * 2 * (S_bench.Wns + S_bench.Tns);
        let predIon_uA_um = (d_pred.Ion * 1000) / (Weff_nm * 1e-3);
        
        // Add benchmark name for tooltip
        let devLabel = device.ref;
        
        window.validationPoints.vth.push({ x: predVth, y: device.Vth, label: devLabel });
        window.validationPoints.ss.push({ x: predSS, y: device.SS, label: devLabel });
        window.validationPoints.ion.push({ x: predIon_uA_um, y: device.Ion, label: devLabel });
        
        sumTcadVth += device.Vth;
        sumTcadSS += device.SS;
        sumTcadIon += device.Ion;
        
        // SNN Prediction Validation
        let d_tcad = JSON.parse(JSON.stringify(d_pred)); 
        d_tcad.Vth = device.Vth;
        d_tcad.SS = device.SS / 1000;
        d_tcad.Ion = device.Ion; 
        
        let acc_tcad = computeSNN(d_tcad, S_bench).A;
        if(isNaN(acc_tcad)) acc_tcad = 90;
        
        let acc_pred = computeSNN(d_pred, S_bench).A;
        if(isNaN(acc_pred)) acc_pred = 90;
        
        let residual = acc_tcad - acc_pred;
        window.residualsArray.push({ predicted: acc_pred, actual: acc_tcad, residual: residual, label: devLabel });
        sumRes += residual;
    });
    
    // Stats Calculations
    let n = BD.length;
    let meanTcadVth = sumTcadVth / n;
    let meanTcadSS = sumTcadSS / n;
    let meanTcadIon = sumTcadIon / n;
    
    window.validationMetrics.vth = calcMetrics(window.validationPoints.vth, meanTcadVth);
    window.validationMetrics.ss = calcMetrics(window.validationPoints.ss, meanTcadSS);
    window.validationMetrics.ion = calcMetrics(window.validationPoints.ion, meanTcadIon);
    
    window.meanResidual = sumRes / n;
    let sumSqRes = 0;
    window.residualsArray.forEach(r => {
        sumSqRes += Math.pow(r.residual - window.meanResidual, 2);
    });
    window.stdResidual = Math.sqrt(sumSqRes / n);
};

function calcMetrics(points, meanTcad) {
    let sst = 0;
    let ssr = 0;
    let sumAbsErr = 0;
    points.forEach(p => {
        sst += Math.pow(p.y - meanTcad, 2);
        ssr += Math.pow(p.y - p.x, 2);
        sumAbsErr += Math.abs(p.y - p.x);
    });
    return {
        r2: 1 - (ssr / (sst || 1)),
        mae: sumAbsErr / points.length
    };
}

window.initValidationCharts = function() {
    window.computeValidationData();
    
    const ctxScatter = document.getElementById('validation-scatter-chart');
    const ctxRes = document.getElementById('validation-residual-chart');
    
    if (ctxScatter) {
        // Initialize Scatter
        window.validationScatterChart = new Chart(ctxScatter.getContext('2d'), {
            type: 'scatter',
            data: {
                datasets: [
                    {
                        label: 'Model vs TCAD',
                        data: window.validationPoints.vth, // default Vth
                        backgroundColor: 'rgba(56, 189, 248, 0.7)', // sky blue
                        borderColor: 'rgba(56, 189, 248, 1)',
                        pointRadius: 5,
                        pointHoverRadius: 7
                    },
                    {
                        label: 'Perfect Agreement',
                        data: [], // populated dynamically
                        type: 'line',
                        borderColor: 'rgba(255,255,255,0.2)',
                        borderDash: [5, 5],
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: 'Model Predicted', color:'#888' }, grid: { color:'#2a2a3a' }, ticks: { color:'#888' } },
                    y: { title: { display: true, text: 'TCAD Benchmark', color:'#888' }, grid: { color:'#2a2a3a' }, ticks: { color:'#888' } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { 
                                let pt = ctx.raw;
                                return `${pt.label} | Pred: ${pt.x.toFixed(2)}, TCAD: ${pt.y.toFixed(2)}`;
                            }
                        }
                    }
                }
            }
        });
        window.updateValidationScatter('vth');
    }
    
    if (ctxRes) {
        // Initialize Residual
        let resData = window.residualsArray.map(r => ({ x: r.predicted, y: r.residual, label: r.label, actual: r.actual }));
        
        window.validationResidualChart = new Chart(ctxRes.getContext('2d'), {
            type: 'scatter',
            data: {
                datasets: [
                    {
                        label: 'Residuals',
                        data: resData,
                        backgroundColor: 'rgba(231, 76, 60, 0.7)',
                        borderColor: 'rgba(231, 76, 60, 1)',
                        pointRadius: 5,
                        pointHoverRadius: 7
                    },
                    {
                        label: 'Zero Line',
                        data: [],
                        type: 'line',
                        borderColor: 'rgba(255,255,255,0.3)',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: '+1.96σ',
                        data: [],
                        type: 'line',
                        borderColor: 'rgba(124, 58, 237, 0.5)',
                        borderDash: [5, 5],
                        borderWidth: 1,
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: '-1.96σ',
                        data: [],
                        type: 'line',
                        borderColor: 'rgba(124, 58, 237, 0.5)',
                        borderDash: [5, 5],
                        borderWidth: 1,
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: 'Predicted SNN Accuracy (%)', color:'#888' }, grid: { color:'#2a2a3a' }, ticks: { color:'#888' } },
                    y: { title: { display: true, text: 'Residual (Actual - Pred) (%)', color:'#888' }, grid: { color:'#2a2a3a' }, ticks: { color:'#888' } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { 
                                let pt = ctx.raw;
                                if(pt.label) {
                                    return `${pt.label} | Pred: ${pt.x.toFixed(2)}%, Act: ${pt.actual.toFixed(2)}% | Res: ${pt.y.toFixed(2)}%`;
                                }
                                return '';
                            }
                        }
                    }
                }
            }
        });
        
        window.updateResidualLines();
        
        // Update Stats UI
        if(document.getElementById('val-res-mean')) document.getElementById('val-res-mean').innerText = window.meanResidual.toFixed(2) + '%';
        if(document.getElementById('val-res-std')) document.getElementById('val-res-std').innerText = window.stdResidual.toFixed(2) + '%';
        if(document.getElementById('val-res-ci')) document.getElementById('val-res-ci').innerText = '± ' + (1.96 * window.stdResidual).toFixed(2) + '%';
    }
};

window.updateValidationScatter = function(paramKey) {
    if (!window.validationScatterChart) return;
    
    let pts = window.validationPoints[paramKey];
    window.validationScatterChart.data.datasets[0].data = pts;
    
    // Diagonal line
    let minVal = Math.min(...pts.map(p=>p.x), ...pts.map(p=>p.y));
    let maxVal = Math.max(...pts.map(p=>p.x), ...pts.map(p=>p.y));
    
    let pad = (maxVal - minVal) * 0.1;
    minVal -= pad;
    maxVal += pad;
    
    window.validationScatterChart.data.datasets[1].data = [
        {x: minVal, y: minVal},
        {x: maxVal, y: maxVal}
    ];
    
    window.validationScatterChart.update();
    
    // Update metrics UI
    let met = window.validationMetrics[paramKey];
    if(document.getElementById('val-r2')) document.getElementById('val-r2').innerText = met.r2.toFixed(3);
    if(document.getElementById('val-mae')) document.getElementById('val-mae').innerText = met.mae.toFixed(3);
};

window.updateResidualLines = function() {
    if (!window.validationResidualChart) return;
    
    let pts = window.residualsArray.map(r => r.predicted);
    let minX = Math.min(...pts) - 1;
    let maxX = Math.max(...pts) + 1;
    
    let std95 = 1.96 * window.stdResidual;
    
    window.validationResidualChart.data.datasets[1].data = [ {x: minX, y: 0}, {x: maxX, y: 0} ];
    window.validationResidualChart.data.datasets[2].data = [ {x: minX, y: std95}, {x: maxX, y: std95} ];
    window.validationResidualChart.data.datasets[3].data = [ {x: minX, y: -std95}, {x: maxX, y: -std95} ];
    
    window.validationResidualChart.update();
};
