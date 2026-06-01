// snn-tornado.js
// Live Sensitivity Analysis (Tornado Chart)

window.tornadoChart = null;
window.tempOverrideParams = null;
window.tornadoEnabled = true;

const sensitivityParams = [
    { key: 'Lg', label: 'Gate Length' },
    { key: 'Vdd', label: 'Vdd' },
    { key: 'EOT', label: 'Oxide Thk.' },
    { key: 'T', label: 'Temperature' },
    { key: 'Wns', label: 'Channel Width' }
];

let debounceTimer = null;

window.initTornadoChart = function() {
    const ctx = document.getElementById('chSnnTornado');
    if (!ctx) return;
    
    window.tornadoChart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: sensitivityParams.map(p => p.label),
            datasets: [
                {
                    label: '-10% Variation',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 1,
                    barPercentage: 0.8
                },
                {
                    label: '+10% Variation',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 1,
                    barPercentage: 0.8
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { 
                    title: { display: true, text: 'Change in Accuracy (%)', color: '#888' },
                    grid: { color: '#2a2a3a' },
                    ticks: { color: '#888' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#888', font: { size: 13 } }
                }
            },
            plugins: {
                legend: { labels: { color: '#888' } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let val = context.raw;
                            let sign = val >= 0 ? '+' : '';
                            return `${context.dataset.label}  ${sign}${val.toFixed(2)}% Acc`;
                        }
                    }
                }
            },
            onHover: (e, activeElements) => {
                if (!activeElements || activeElements.length === 0) {
                    if (window.tempOverrideParams !== null) {
                        window.tempOverrideParams = null;
                        if(typeof fallbackComputeAll === 'function') fallbackComputeAll(true); // true means isPreview
                        let hl = document.getElementById('snn-acc-highlight');
                        if (hl) hl.style.opacity = "0";
                    }
                    return;
                }
                
                const el = activeElements[0];
                const datasetIndex = el.datasetIndex; // 0 for -10%, 1 for +10%
                const dataIndex = el.index;           // parameter index
                
                const param = sensitivityParams[dataIndex];
                const mult = datasetIndex === 0 ? 0.9 : 1.1;
                
                // Set temporary override
                let overrides = JSON.parse(JSON.stringify(window.currentS || {})); 
                // Wait, S is global in index.html. We can access it directly via S.
                overrides = JSON.parse(JSON.stringify(typeof S !== 'undefined' ? S : {}));
                
                overrides[param.key] = overrides[param.key] * mult;
                window.tempOverrideParams = overrides;
                
                if(typeof fallbackComputeAll === 'function') fallbackComputeAll(true);
                
                let hl = document.getElementById('snn-acc-highlight');
                if (hl) {
                    hl.innerText = `Preview: ${datasetIndex===0?'-10%':'+10%'} ${param.label}`;
                    hl.style.opacity = "1";
                }
            }
        }
    });
    
    // Add mouseleave just to be safe
    document.getElementById('chSnnTornado').addEventListener('mouseleave', () => {
        if (window.tempOverrideParams !== null) {
            window.tempOverrideParams = null;
            if(typeof fallbackComputeAll === 'function') fallbackComputeAll(true);
            let hl = document.getElementById('snn-acc-highlight');
            if (hl) hl.style.opacity = "0";
        }
    });
};

window.triggerTornadoCompute = function() {
    if (!window.tornadoEnabled || !window.tornadoChart) return;
    
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        window.computeSensitivity();
    }, 250); // 250ms debounce
};

window.computeSensitivity = function() {
    if (!window.tornadoChart) return;
    
    // We need the base accuracy.
    const baseS = typeof S !== 'undefined' ? S : {};
    let baseD = computeDevice(baseS);
    if(window.agingEnabled && window.applyAging) baseD = window.applyAging(baseD, window.agingYears);
    let baseSnn = computeSNN(baseD, baseS);
    let baseAcc = baseSnn.A;
    if (isNaN(baseAcc)) baseAcc = 50;
    
    let leftData = [];
    let rightData = [];
    
    let maxChange = 0;
    let mostSensitiveParam = "None";
    let mostSensitiveDir = "";
    
    sensitivityParams.forEach(param => {
        // -10%
        let sLeft = JSON.parse(JSON.stringify(baseS));
        sLeft[param.key] = sLeft[param.key] * 0.9;
        let dLeft = computeDevice(sLeft);
        if(window.agingEnabled && window.applyAging) dLeft = window.applyAging(dLeft, window.agingYears);
        let accLeft = computeSNN(dLeft, sLeft).A;
        let deltaLeft = accLeft - baseAcc;
        if (isNaN(deltaLeft)) deltaLeft = 0;
        leftData.push(deltaLeft);
        
        if (Math.abs(deltaLeft) > Math.abs(maxChange)) {
            maxChange = deltaLeft;
            mostSensitiveParam = param.label;
            mostSensitiveDir = "-10%";
        }
        
        // +10%
        let sRight = JSON.parse(JSON.stringify(baseS));
        sRight[param.key] = sRight[param.key] * 1.1;
        let dRight = computeDevice(sRight);
        if(window.agingEnabled && window.applyAging) dRight = window.applyAging(dRight, window.agingYears);
        let accRight = computeSNN(dRight, sRight).A;
        let deltaRight = accRight - baseAcc;
        if (isNaN(deltaRight)) deltaRight = 0;
        rightData.push(deltaRight);
        
        if (Math.abs(deltaRight) > Math.abs(maxChange)) {
            maxChange = deltaRight;
            mostSensitiveParam = param.label;
            mostSensitiveDir = "+10%";
        }
    });
    
    window.tornadoChart.data.datasets[0].data = leftData;
    window.tornadoChart.data.datasets[1].data = rightData;
    window.tornadoChart.update();
    
    let baseLab = document.getElementById('tornado-base-acc');
    if (baseLab) baseLab.innerText = baseAcc.toFixed(1) + "%";
    
    let mstLab = document.getElementById('tornado-most-sensitive');
    if (mstLab) {
        let sign = maxChange >= 0 ? '+' : '';
        mstLab.innerText = `${mostSensitiveParam} (${mostSensitiveDir}  ${sign}${maxChange.toFixed(2)}% Acc)`;
    }
};

window.resetTornadoHighlight = function() {
    window.tempOverrideParams = null;
    if(typeof fallbackComputeAll === 'function') fallbackComputeAll(true);
    let hl = document.getElementById('snn-acc-highlight');
    if (hl) hl.style.opacity = "0";
};
