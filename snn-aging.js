// snn-aging.js
// Device Aging & Reliability Projector

window.agingEnabled = false;
window.agingYears = 0.0;
window.agingChart = null;
window.baselineAccuracy = 0;
window.agedAccuracy = 0;

window.applyAging = function(baseDeviceParams, years) {
    if (!window.agingEnabled || years === 0) return baseDeviceParams;
    
    // Deep copy to avoid mutating base params
    let d = JSON.parse(JSON.stringify(baseDeviceParams));
    
    // Empirical Formulas
    d.Vth = Math.min(1.0, d.Vth + (0.020 * years));
    d.SS = Math.min(0.150, d.SS + (0.003 * years)); // SS typically in V/dec or mV/dec? In code it's V/dec (like 0.065)
    
    // Ensure SS doesn't go below physical limit just in case
    d.muEff = Math.max(d.muEff * 0.10, d.muEff * (1.0 - 0.05 * years));
    d.gm = d.gm * (1.0 - 0.04 * years);
    d.Ion = d.Ion * (1.0 - 0.06 * years);
    d.Ioff = d.Ioff * (1.0 + 0.10 * years); // Ioff increases with age
    
    // Mark health
    d.health = "Excellent";
    if (years >= 1.0) d.health = "Good";
    if (years >= 2.5) d.health = "Worn";
    if (years >= 4.0) d.health = "Failed";
    
    if (d.Vth >= 1.0 || d.muEff <= d.muEff * 0.15) {
        d.health = "Failed";
    }
    
    return d;
};

window.initAgingChart = function() {
    const ctx = document.getElementById('chSnnAge');
    if(!ctx) return;
    window.agingChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: [0, 1, 2, 3, 4, 5],
            datasets: [{
                label: 'SNN Accuracy (%)',
                data: [100, 100, 100, 100, 100, 100],
                borderColor: '#e4405f',
                backgroundColor: 'rgba(228, 64, 95, 0.2)',
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Years', color:'#888' }, grid: { color:'#2a2a3a' }, ticks:{color:'#888'} },
                y: { title: { display: true, text: 'Accuracy (%)', color:'#888' }, grid: { color:'#2a2a3a' }, ticks:{color:'#888'}, min: 50, max: 100 }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
};

// Called when base parameters change to redraw the projection curve
window.updateAgingCurve = function(baseParams, S) {
    if (!window.agingChart) return;
    
    let accData = [];
    for(let y = 0; y <= 5; y++) {
        let aged_d = window.applyAging(baseParams, y);
        let snn = computeSNN(aged_d, S);
        let acc = Math.max(50, snn.A);
        if (isNaN(acc)) acc = 50;
        accData.push(acc);
    }
    
    window.baselineAccuracy = accData[0];
    
    window.agingChart.data.datasets[0].data = accData;
    
    // Highlight current year point
    let pointColors = accData.map((_, i) => i === Math.round(window.agingYears) ? '#66ccff' : '#e4405f');
    let pointRadii = accData.map((_, i) => i === Math.round(window.agingYears) ? 8 : 4);
    
    window.agingChart.data.datasets[0].pointBackgroundColor = pointColors;
    window.agingChart.data.datasets[0].pointRadius = pointRadii;
    
    window.agingChart.update();
    
    // Calc RUL
    let rul = "0.0";
    for(let i=0; i<accData.length; i++) {
        if (accData[i] < 70) {
            // linear interpolate roughly
            let drop = accData[i-1] - accData[i];
            let diff = accData[i-1] - 70;
            rul = ((i - 1) + (diff / drop)).toFixed(1);
            break;
        }
        if (i === accData.length - 1) rul = "> 5.0";
    }
    let rulEl = document.getElementById('aging-rul');
    if (rulEl) rulEl.innerText = rul + ' years';
};

window.updateAgingUI = function(health, agedSnn) {
    let hl = document.getElementById('aging-health-label');
    let hb = document.getElementById('aging-health-bar');
    let dot = document.getElementById('aging-health-dot');
    if (!hl || !hb || !dot) return;
    
    window.agedAccuracy = agedSnn.A;
    
    hl.innerText = health;
    if (health === "Excellent") {
        dot.style.color = "#10b981";
        hb.style.background = "#10b981";
        hb.style.width = "100%";
    } else if (health === "Good") {
        dot.style.color = "#fbbf24";
        hb.style.background = "#fbbf24";
        hb.style.width = "75%";
    } else if (health === "Worn") {
        dot.style.color = "#f97316";
        hb.style.background = "#f97316";
        hb.style.width = "40%";
    } else {
        dot.style.color = "#ef4444";
        hb.style.background = "#ef4444";
        hb.style.width = "10%";
    }
};
