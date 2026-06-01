// snn-monte-carlo.js
// Monte Carlo Variability & Yield Analyzer

window.mcChart = null;
window.mcAbortController = null;
window.mcResults = []; // array of {iteration, params, accuracy}

const mcParamsList = [
    { key: 'Lg', label: 'Gate Length' },
    { key: 'Vdd', label: 'Vdd' },
    { key: 'EOT', label: 'Oxide Thk.' },
    { key: 'T', label: 'Temperature' },
    { key: 'Wns', label: 'Channel Width' }
];

// Math Utilities
function randomGaussian() {
    let u = 0, v = 0;
    while(u === 0) u = Math.random();
    while(v === 0) v = Math.random();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

function randomUniform(min, max) {
    return Math.random() * (max - min) + min;
}

window.initMCChart = function() {
    const ctx = document.getElementById('chSnnMC');
    if (!ctx) return;
    window.mcChart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Frequency',
                data: [],
                backgroundColor: 'rgba(124, 58, 237, 0.6)',
                borderColor: 'rgba(124, 58, 237, 1)',
                borderWidth: 1,
                barPercentage: 1.0,
                categoryPercentage: 1.0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { 
                    title: { display: true, text: 'SNN Accuracy (%)', color:'#888' },
                    grid: { display: false },
                    ticks: { color:'#888' }
                },
                y: {
                    title: { display: true, text: 'Count', color:'#888' },
                    grid: { color:'#2a2a3a' },
                    ticks: { color:'#888', beginAtZero: true }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
};

window.startMonteCarlo = function() {
    if (window.mcAbortController) {
        window.mcAbortController.abort();
    }
    
    // Read Settings
    const activeParams = [];
    document.querySelectorAll('.mc-param-chk').forEach(el => {
        if(el.checked) activeParams.push(el.value);
    });
    
    if (activeParams.length === 0) {
        alert("Please select at least one parameter to vary.");
        return;
    }
    
    const varType = document.querySelector('input[name="mc-var-type"]:checked').value; // 'abs' or 'rel'
    const varDist = document.querySelector('input[name="mc-var-dist"]:checked').value; // 'norm' or 'unif'
    const varAmt = parseFloat(document.getElementById('mc-var-amount').value);
    const numSamples = parseInt(document.getElementById('mc-samples').value);
    const threshold = parseFloat(document.getElementById('mc-threshold').value);
    
    if (isNaN(varAmt) || isNaN(numSamples) || isNaN(threshold)) return;
    
    // UI Reset
    document.getElementById('mc-stale-warning').style.display = 'none';
    document.getElementById('mc-progress-bar').style.width = '0%';
    document.getElementById('mc-progress-text').innerText = '0% (0/' + numSamples + ')';
    
    window.mcResults = [];
    window.mcAbortController = new AbortController();
    const signal = window.mcAbortController.signal;
    
    // Setup baseline
    const baseS = typeof S !== 'undefined' ? S : {};
    
    let currentIteration = 0;
    const batchSize = 50;
    
    function runBatch() {
        if (signal.aborted) return;
        
        let batchEnd = Math.min(currentIteration + batchSize, numSamples);
        
        for (let i = currentIteration; i < batchEnd; i++) {
            // Generate Random Parameters
            let sVaried = JSON.parse(JSON.stringify(baseS));
            
            activeParams.forEach(p => {
                let baseVal = sVaried[p];
                let stdDevOrHalfRange = varType === 'rel' ? (baseVal * (varAmt / 100)) : varAmt;
                
                let sampleVal;
                if (varDist === 'norm') {
                    // Normal: sigma = stdDevOrHalfRange
                    sampleVal = baseVal + (randomGaussian() * stdDevOrHalfRange);
                } else {
                    // Uniform: min = base - halfRange, max = base + halfRange
                    sampleVal = randomUniform(baseVal - stdDevOrHalfRange, baseVal + stdDevOrHalfRange);
                }
                
                // Clamping (hard limits based on physics so engine doesn't crash)
                if (p === 'Lg') sampleVal = Math.max(5, sampleVal);
                if (p === 'EOT') sampleVal = Math.max(0.2, sampleVal);
                if (p === 'T') sampleVal = Math.max(10, sampleVal);
                if (p === 'Vdd') sampleVal = Math.max(0.1, sampleVal);
                
                sVaried[p] = sampleVal;
            });
            
            // Recompute
            let dVaried = computeDevice(sVaried);
            if(window.agingEnabled && window.applyAging) dVaried = window.applyAging(dVaried, window.agingYears);
            let accVaried = computeSNN(dVaried, sVaried).A;
            if (isNaN(accVaried)) accVaried = 0;
            
            window.mcResults.push({
                iteration: i + 1,
                params: sVaried,
                accuracy: accVaried
            });
        }
        
        currentIteration = batchEnd;
        
        // Update Progress UI
        let pct = Math.round((currentIteration / numSamples) * 100);
        document.getElementById('mc-progress-bar').style.width = pct + '%';
        document.getElementById('mc-progress-text').innerText = `${pct}% (${currentIteration}/${numSamples})`;
        
        if (currentIteration < numSamples) {
            setTimeout(runBatch, 5); // yield to main thread
        } else {
            finalizeMonteCarlo(threshold);
        }
    }
    
    // Start first batch
    setTimeout(runBatch, 10);
};

window.cancelMonteCarlo = function() {
    if (window.mcAbortController) {
        window.mcAbortController.abort();
        window.mcAbortController = null;
        document.getElementById('mc-progress-text').innerText = 'Cancelled.';
    }
};

function finalizeMonteCarlo(threshold) {
    window.mcAbortController = null;
    
    if (window.mcResults.length === 0) return;
    
    // Extract accuracies
    const accs = window.mcResults.map(r => r.accuracy);
    
    // Stats
    let minAcc = Math.min(...accs);
    let maxAcc = Math.max(...accs);
    
    // Calculate Mean & Std Dev
    let sum = accs.reduce((a, b) => a + b, 0);
    let mean = sum / accs.length;
    let variance = accs.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / accs.length;
    let std = Math.sqrt(variance);
    
    // Calculate Yield
    let passed = accs.filter(a => a >= threshold).length;
    let yieldPct = (passed / accs.length) * 100;
    
    // Update UI Stats
    document.getElementById('mc-stat-mean').innerText = mean.toFixed(2) + '%';
    document.getElementById('mc-stat-std').innerText = std.toFixed(2) + '%';
    document.getElementById('mc-stat-worst').innerText = minAcc.toFixed(2) + '%';
    document.getElementById('mc-stat-best').innerText = maxAcc.toFixed(2) + '%';
    document.getElementById('mc-stat-fail').innerText = (accs.length - passed).toString();
    
    let yieldEl = document.getElementById('mc-stat-yield');
    yieldEl.innerText = yieldPct.toFixed(1) + '%';
    if (yieldPct >= 90) yieldEl.style.color = '#10b981'; // green
    else if (yieldPct >= 70) yieldEl.style.color = '#fbbf24'; // yellow
    else yieldEl.style.color = '#ef4444'; // red
    
    // Generate Histogram Bins
    let numBins = 20;
    // Edge case: if min == max, pad a bit
    if (maxAcc - minAcc < 0.1) {
        minAcc -= 1;
        maxAcc += 1;
    }
    
    let binSize = (maxAcc - minAcc) / numBins;
    let bins = new Array(numBins).fill(0);
    let binLabels = new Array(numBins);
    
    for(let i=0; i<numBins; i++) {
        binLabels[i] = (minAcc + (i + 0.5) * binSize).toFixed(1);
    }
    
    accs.forEach(a => {
        let binIdx = Math.floor((a - minAcc) / binSize);
        if (binIdx >= numBins) binIdx = numBins - 1; // clamp max
        bins[binIdx]++;
    });
    
    // Plot Histogram
    if (window.mcChart) {
        window.mcChart.data.labels = binLabels;
        window.mcChart.data.datasets[0].data = bins;
        
        // Color bins below threshold red, above threshold green/purple
        let bgColors = binLabels.map(l => {
            if (parseFloat(l) < threshold) return 'rgba(239, 68, 68, 0.7)'; // red
            return 'rgba(124, 58, 237, 0.7)'; // purple
        });
        window.mcChart.data.datasets[0].backgroundColor = bgColors;
        window.mcChart.data.datasets[0].borderColor = bgColors.map(c => c.replace('0.7', '1'));
        
        window.mcChart.update();
    }
}

window.exportMonteCarloCSV = function() {
    if (!window.mcResults || window.mcResults.length === 0) {
        alert("No results to export. Run the simulation first.");
        return;
    }
    
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Headers
    let paramsKeys = Object.keys(window.mcResults[0].params);
    csvContent += "Iteration," + paramsKeys.join(",") + ",Accuracy\n";
    
    // Rows
    window.mcResults.forEach(r => {
        let row = [r.iteration];
        paramsKeys.forEach(k => {
            row.push(r.params[k]);
        });
        row.push(r.accuracy.toFixed(4));
        csvContent += row.join(",") + "\n";
    });
    
    let encodedUri = encodeURI(csvContent);
    let link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "FET2SNN_MonteCarlo_Yield.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

window.copyLatexTable = function() {
    let mean = document.getElementById('mc-stat-mean').innerText;
    let std = document.getElementById('mc-stat-std').innerText;
    let yld = document.getElementById('mc-stat-yield').innerText;
    let w = document.getElementById('mc-stat-worst').innerText;
    let b = document.getElementById('mc-stat-best').innerText;
    
    if (mean === '-' || !mean) return;
    
    let latex = `\\begin{table}[htbp]
\\centering
\\caption{Monte Carlo Variability & Yield Analysis}
\\begin{tabular}{lc}
\\hline
\\textbf{Statistic} & \\textbf{Value} \\\\
\\hline
Mean Accuracy & ${mean} \\\\
Std. Deviation & ${std} \\\\
Worst Case & ${w} \\\\
Best Case & ${b} \\\\
\\hline
\\textbf{Manufacturing Yield} & \\textbf{${yld}} \\\\
\\hline
\\end{tabular}
\\label{tab:yield}
\\end{table}`;
    
    navigator.clipboard.writeText(latex).then(() => {
        alert("LaTeX table copied to clipboard!");
    });
};
