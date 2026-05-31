// SPA Navigation Logic
const navBtns = document.querySelectorAll('.nav-btn');
const views = document.querySelectorAll('.view');

navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        navBtns.forEach(b => b.classList.remove('active'));
        views.forEach(v => v.classList.replace('active', 'hidden'));
        
        btn.classList.add('active');
        const viewId = btn.getAttribute('data-view');
        document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
    
        if (viewId === 'leaderboard') {
            const targetView = document.getElementById('leaderboard');
            if (targetView) targetView.classList.replace('hidden', 'active');
            loadLeaderboard();
            return;
        }

        const map = {
            'view-dashboard': 'view-dashboard',
            'view-trades': 'view-trades',
            'simulator': 'view-analytics',
            'live-activity': 'view-strategies',
            'view-settings': 'view-settings'
        };
        const targetView = document.getElementById(map[viewId] || viewId);
        if (targetView) targetView.classList.replace('hidden', 'active');
        
        if (viewId === 'view-trades') loadTradesHistory('month');
    });
});

// Trades History Filtering
const filterBtns = document.querySelectorAll('.filter-btn');
filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        loadTradesHistory(btn.getAttribute('data-filter'));
    });
});

async function loadTradesHistory(filter) {
    try {
        const res = await fetch(`/api/trades?filter=${filter}`);
        const data = await res.json();
        const tbody = document.getElementById('history-tbody');
        tbody.innerHTML = '';
        data.forEach(trade => {
            const tr = document.createElement('tr');
            const profitClass = trade.profit >= 0 ? 'text-buy' : 'text-sell';
            const profitText = trade.profit > 0 ? `+${trade.profit.toFixed(2)}` : trade.profit.toFixed(2);
            tr.innerHTML = `
                <td>${trade.ticket}</td>
                <td class="${trade.type.toLowerCase() === 'buy' ? 'text-buy' : 'text-sell'}">${trade.type}</td>
                <td>L${trade.level}</td>
                <td>${trade.open_time}</td>
                <td>${trade.close_time}</td>
                <td class="${profitClass}">${profitText}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) { console.error(e); }
}

// GUI Backtest
const runBtBtn = document.getElementById('run-bt-btn');
const exportBtBtn = document.getElementById('export-bt-btn');
const optimizeBtBtn = document.getElementById('optimize-bt-btn');
const btLoading = document.getElementById('bt-loading');
const btResults = document.getElementById('bt-results');
const btKpiGrid = document.getElementById('bt-kpi-grid');
let btChartInstance = null;
let btPnlChartInstance = null;
let btCandlesChart = null;
let lastTrades = [];
let currentStrategyName = 'default';

const btDurationMode = document.getElementById('bt-duration-mode');
if (btDurationMode) {
    btDurationMode.addEventListener('change', (e) => {
        const val = e.target.value;
        const label = document.getElementById('bt-duration-label');
        if (val === 'days') label.textContent = 'Days Back';
        else if (val === 'candles') label.textContent = 'Number of Candles';
        else if (val === 'trades') label.textContent = 'Number of Trades';
    });
}

// ==========================================
// LEADERBOARD LOGIC
// ==========================================
const refreshLeaderboardBtn = document.getElementById('refresh-leaderboard');
if (refreshLeaderboardBtn) {
    refreshLeaderboardBtn.addEventListener('click', loadLeaderboard);
}

async function loadLeaderboard() {
    const tbody = document.getElementById('leaderboard-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">Loading...</td></tr>';
    
    try {
        const res = await fetch('/api/leaderboard');
        const data = await res.json();
        if (data.status === 'success') {
            tbody.innerHTML = '';
            if (data.leaderboard.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">No runs saved yet. Go backtest!</td></tr>';
                return;
            }
            
            data.leaderboard.forEach((r, idx) => {
                const tr = document.createElement('tr');
                if (idx === 0) tr.style.backgroundColor = 'rgba(76, 175, 80, 0.1)';
                tr.innerHTML = `
                    <td>${r.timestamp}</td>
                    <td><strong style="color: #64B5F6;">${r.symbol}</strong></td>
                    <td>${r.strategy}</td>
                    <td>${r.duration}</td>
                    <td>$${r.capital}</td>
                    <td style="color: ${r.profit >= 0 ? 'var(--profit-color)' : 'var(--loss-color)'}">
                        $${r.profit}
                    </td>
                    <td>${r.trades}</td>
                    <td style="color: ${r.win_rate >= 50 ? 'var(--profit-color)' : 'var(--loss-color)'}">${r.win_rate}%</td>
                    <td style="color: ${r.blowups > 0 ? 'var(--loss-color)' : 'var(--text-muted)'}">${r.blowups}</td>
                    <td>
                        <button class="terminal-btn outline copy-live-btn" data-config='${JSON.stringify(r.raw_config || {}).replace(/'/g, "&apos;")}'>Copy</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            
            // Bind click events for copy buttons
            document.querySelectorAll('.copy-live-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const rawConfig = JSON.parse(e.target.getAttribute('data-config'));
                    copyToLiveEnvironment("Leaderboard Strategy", rawConfig);
                });
            });
        }
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:red;">Error loading leaderboard</td></tr>';
    }
}

// ==========================================
// TRADES HISTORY
// ==========================================

const btStrategySelector = document.getElementById('bt-strategy');
const btCustomConfig = document.getElementById('bt-custom-config');
const btAccountType = document.getElementById('bt-account-type');

if (btAccountType) {
    btAccountType.addEventListener('change', (e) => {
        const val = e.target.value;
        const customParams = document.querySelectorAll('.custom-account-param');
        if (val === 'custom') {
            customParams.forEach(el => el.style.display = 'block');
        } else {
            customParams.forEach(el => el.style.display = 'none');
        }
    });
}

if (btStrategySelector) {
    btStrategySelector.addEventListener('change', (e) => {
        const val = e.target.value;
        const dirEl = document.getElementById('bt-custom-dir');
        const daysEl = document.getElementById('bt-custom-days');
        const riskEl = document.getElementById('bt-custom-risk');
        const tpEl = document.getElementById('bt-custom-tp');
        const slEl = document.getElementById('bt-custom-sl');
        const sessEl = document.getElementById('bt-custom-sessions');

        // Reset to defaults first
        dirEl.value = 'BOTH';
        daysEl.value = '24_5';
        riskEl.value = '0.1';
        tpEl.value = '10000';
        slEl.value = '1000';
        sessEl.value = '10:00-17:30,20:00-22:30';

        switch(val) {
            case 'buy_back':
                dirEl.value = 'BUY';
                break;
            case 'sell_back':
                dirEl.value = 'SELL';
                break;
            case '24_7':
                daysEl.value = '24_7';
                sessEl.value = ''; // 24h
                break;
            case 'advanced_grow':
                riskEl.value = '1.0';
                break;
            case 'custom':
                // Leave as default for them to customize
                break;
        }
    });
}

const btStrategySelect = document.getElementById('bt-strategy');
const customConfigDiv = document.getElementById('bt-custom-config');
if (btStrategySelect && customConfigDiv) {
    btStrategySelect.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
            customConfigDiv.style.opacity = '1';
            customConfigDiv.style.pointerEvents = 'auto';
        } else {
            customConfigDiv.style.opacity = '0.5';
            customConfigDiv.style.pointerEvents = 'none';
        }
    });
    // Trigger on load
    btStrategySelect.dispatchEvent(new Event('change'));
}

runBtBtn.addEventListener('click', async () => {
    const durationMode = document.getElementById('bt-duration-mode') ? document.getElementById('bt-duration-mode').value : 'days';
    const durationVal = document.getElementById('bt-duration-val').value;
    const capital = document.getElementById('bt-capital').value;
    const symbol = document.getElementById('bt-symbol') ? document.getElementById('bt-symbol').value : 'XAUUSDm';
    const timeframe = document.getElementById('bt-timeframe') ? document.getElementById('bt-timeframe').value : 'M5';
    
    let spread = 200.0;
    let comm = 0.0;
    const accountType = document.getElementById('bt-account-type') ? document.getElementById('bt-account-type').value : 'standard';
    if (accountType === 'standard') { spread = 200.0; comm = 0.0; }
    else if (accountType === 'pro') { spread = 112.0; comm = 0.0; }
    else if (accountType === 'raw') { spread = 37.0; comm = 7.0; }
    else if (accountType === 'zero') { spread = 0.0; comm = 11.0; }
    else if (accountType === 'custom') {
        spread = parseFloat(document.getElementById('bt-spread').value || 10.0);
        comm = parseFloat(document.getElementById('bt-comm').value || 0.0);
    }
    
    const strategy = document.getElementById('bt-strategy') ? document.getElementById('bt-strategy').value : 'default';
    currentStrategyName = strategy;
    const customParams = {
        direction: document.getElementById('bt-custom-dir') ? document.getElementById('bt-custom-dir').value : 'BOTH',
        days_mode: document.getElementById('bt-custom-days') ? document.getElementById('bt-custom-days').value : '24_5',
        risk: parseFloat(document.getElementById('bt-custom-risk') ? document.getElementById('bt-custom-risk').value : 0.1),
        tp: parseInt(document.getElementById('bt-custom-tp') ? document.getElementById('bt-custom-tp').value : 10000),
        sl: parseInt(document.getElementById('bt-custom-sl') ? document.getElementById('bt-custom-sl').value : 1000),
        sessions: document.getElementById('bt-custom-sessions') ? document.getElementById('bt-custom-sessions').value : ''
    };
    
    btLoading.classList.remove('hidden');
    btResults.classList.add('hidden');
    if (exportBtBtn) exportBtBtn.classList.add('hidden');
    
    try {
        const res = await fetch('/api/backtest/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ duration_mode: durationMode, duration_val: durationVal, capital, spread, comm, strategy, symbol, timeframe, custom_params: customParams })
        });
        const data = await res.json();
        
        if(data.status === 'error') {
            alert(data.message);
            btLoading.classList.add('hidden');
            return;
        }
        
        // Populate KPIs
        btKpiGrid.innerHTML = `
            <div class="analytic-item"><span class="label">Initial Capital</span><span class="value">$${data.kpis.initial_capital}</span></div>
            <div class="analytic-item"><span class="label">Final Capital</span><span class="value">$${data.kpis.final_capital.toFixed(2)}</span></div>
            <div class="analytic-item"><span class="label">Total Profit</span><span class="value ${data.kpis.total_profit >= 0 ? 'text-buy' : 'text-sell'}">$${data.kpis.total_profit.toFixed(2)}</span></div>
            <div class="analytic-item"><span class="label">Win Rate</span><span class="value">${data.kpis.win_rate}%</span></div>
            <div class="analytic-item"><span class="label">Total Trades</span><span class="value">${data.kpis.total_trades}</span></div>
            <div class="analytic-item"><span class="label">Account Blowups</span><span class="value text-sell">${data.kpis.blowups}</span></div>
        `;
        
        // Draw Chart
        const labels = [];
        const chartData = [];
        const dailyPnL = {};
        let cumPnl = 0;
        data.trades.forEach((t, i) => {
            cumPnl += t.profit;
            labels.push(`Trade ${i+1}`);
            chartData.push(cumPnl);
            
            if (t.entry_time) {
                // Parse date regardless of format
                const d = new Date(t.entry_time);
                if (!isNaN(d.getTime())) {
                    const day = d.toISOString().split('T')[0];
                    if (!dailyPnL[day]) dailyPnL[day] = 0;
                    dailyPnL[day] += t.profit;
                }
            }
        });
        
        let periodicLabels = Object.keys(dailyPnL).sort();
        let periodicData = [];
        if (periodicLabels.length > 60) {
            const monthlyPnL = {};
            periodicLabels.forEach(d => {
                const m = d.substring(0, 7);
                if (!monthlyPnL[m]) monthlyPnL[m] = 0;
                monthlyPnL[m] += dailyPnL[d];
            });
            periodicLabels = Object.keys(monthlyPnL).sort();
            periodicData = periodicLabels.map(m => monthlyPnL[m]);
            const title = document.getElementById('pnl-chart-title');
            if (title) title.innerText = 'Monthly Returns';
        } else {
            periodicData = periodicLabels.map(d => dailyPnL[d]);
            const title = document.getElementById('pnl-chart-title');
            if (title) title.innerText = 'Daily Returns';
        }
        const pnlBarColors = periodicData.map(v => v >= 0 ? 'rgba(14, 203, 129, 0.8)' : 'rgba(246, 70, 93, 0.8)');
        
        if (btChartInstance) btChartInstance.destroy();
        const ctx2 = document.getElementById('btChart').getContext('2d');
        btChartInstance = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Simulation PnL',
                    data: chartData,
                    borderColor: '#0ECB81',
                    backgroundColor: 'rgba(14, 203, 129, 0.1)',
                    borderWidth: 2, tension: 0.1, fill: true, pointRadius: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { position: 'right' }, x: { display: false } }, animation: { duration: 1000 } }
        });

        if (btPnlChartInstance) btPnlChartInstance.destroy();
        const ctxPnl = document.getElementById('btPnlChart').getContext('2d');
        btPnlChartInstance = new Chart(ctxPnl, {
            type: 'bar',
            data: {
                labels: periodicLabels,
                datasets: [{
                    label: 'Periodic PnL',
                    data: periodicData,
                    backgroundColor: pnlBarColors,
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { position: 'right' }, x: { display: true } }, animation: { duration: 1000 } }
        });

        // Render advanced charts
        lastTrades = data.trades;
        
        try {
            renderHeatmap(data.trades);
        } catch (err) {
            console.error("Heatmap render error:", err);
        }
        if (exportBtBtn) exportBtBtn.classList.remove('hidden');

        
        const btTbody = document.getElementById('bt-trades-tbody');
        if (btTbody) {
            btTbody.innerHTML = '';
            let runningCapital = parseFloat(capital) || 1000;
            data.trades.forEach((t, i) => {
                runningCapital += t.profit;
                const tr = document.createElement('tr');
                const profitClass = t.profit >= 0 ? 'text-buy' : 'text-sell';
                const profitText = t.profit > 0 ? `+${t.profit.toFixed(2)}` : t.profit.toFixed(2);
                let entryDateStr = "-";
                let entryTimeStr = "-";
                if (t.entry_time) {
                    let et = t.entry_time.replace('Z', '');
                    const parts = et.split('T');
                    if (parts.length === 2) {
                        entryDateStr = parts[0];
                        entryTimeStr = parts[1].substring(0, 8);
                    } else {
                        const spaceParts = et.split(' ');
                        entryDateStr = spaceParts[0] || "-";
                        entryTimeStr = (spaceParts[1] || "-").substring(0, 8);
                    }
                }
                
                let exitDateStr = "-";
                let exitTimeStr = "-";
                if (t.exit_time) {
                    let ex = t.exit_time.replace('Z', '');
                    const parts = ex.split('T');
                    if (parts.length === 2) {
                        exitDateStr = parts[0];
                        exitTimeStr = parts[1].substring(0, 8);
                    } else {
                        const spaceParts = ex.split(' ');
                        exitDateStr = spaceParts[0] || "-";
                        exitTimeStr = (spaceParts[1] || "-").substring(0, 8);
                    }
                }
                
                tr.innerHTML = `
                    <td>${entryDateStr}</td>
                    <td>${entryTimeStr}</td>
                    <td class="${t.direction === 'BUY' ? 'text-buy' : 'text-sell'}">${t.direction}</td>
                    <td>${exitDateStr}</td>
                    <td>${exitTimeStr}</td>
                    <td>${t.entry_price ? t.entry_price.toFixed(2) : '-'}</td>
                    <td>${t.exit_price ? t.exit_price.toFixed(2) : '-'}</td>
                    <td>${t.sl_price ? t.sl_price.toFixed(2) : '-'}</td>
                    <td>${t.tp_price ? t.tp_price.toFixed(2) : '-'}</td>
                    <td class="${profitClass}">${profitText}</td>
                    <td class="${profitClass}">${t.result}</td>
                    <td>$${runningCapital.toFixed(2)}</td>
                `;
                btTbody.appendChild(tr);
            });
        }
        
        btLoading.classList.add('hidden');
        btResults.classList.remove('hidden');
        
        try {
            if (data.ohlc && data.trades) renderCandlesticks(data.ohlc, data.trades);
        } catch (e) {
            console.error("Candlestick render error", e);
        }
        
        // Refresh leaderboard with new run
        if(typeof loadLeaderboard === 'function') loadLeaderboard();

        
    } catch(e) {
        alert("Simulation failed: " + e.stack);
        btLoading.classList.add('hidden');
    }
});


function renderHeatmap(trades) {
    const container = document.getElementById('btHeatmap');
    const matrix = {};
    for(let d=1; d<=5; d++) {
        matrix[d] = {};
        for(let h=0; h<24; h++) matrix[d][h] = { wins: 0, total: 0 };
    }
    
    trades.forEach(t => {
        if(!t.entry_time) return;
        const d = new Date(t.entry_time);
        const day = d.getDay();
        const hour = d.getHours();
        
        if(matrix[day] && matrix[day][hour]) {
            matrix[day][hour].total++;
            if(t.profit >= 0) matrix[day][hour].wins++;
        }
    });
    
    let html = `<table class="terminal-table" style="width:100%; border-collapse:collapse; text-align:center;">`;
    html += `<thead><tr><th>Hour / Day</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th></tr></thead><tbody>`;
    for(let h=0; h<24; h++) {
        html += `<tr><td style="color:#a9a9b3;">${h.toString().padStart(2, '0')}:00</td>`;
        for(let d=1; d<=5; d++) {
            const cell = matrix[d][h];
            let color = 'transparent';
            let txt = '-';
            if(cell.total > 0) {
                const wr = cell.wins / cell.total;
                if(wr >= 0.7) color = 'rgba(14, 203, 129, 0.4)';
                else if (wr <= 0.4) color = 'rgba(246, 70, 93, 0.4)';
                else color = 'rgba(255, 255, 255, 0.1)';
                txt = `${(wr*100).toFixed(0)}%<br><small>(${cell.total}t)</small>`;
            }
            html += `<td style="background-color: ${color}; padding:5px; border:1px solid #333; min-width:60px;">${txt}</td>`;
        }
        html += `</tr>`;
    }
    html += `</tbody></table>`;
    container.innerHTML = html;
}

if(optimizeBtBtn) {
    optimizeBtBtn.addEventListener('click', async () => {
        const durationMode = document.getElementById('bt-duration-mode') ? document.getElementById('bt-duration-mode').value : 'days';
        const durationVal = document.getElementById('bt-duration-val').value;
        const capital = document.getElementById('bt-capital').value;
        const symbol = document.getElementById('bt-symbol') ? document.getElementById('bt-symbol').value : 'XAUUSDm';
        const timeframe = document.getElementById('bt-timeframe') ? document.getElementById('bt-timeframe').value : 'M5';
        
        let spread = 200.0;
        let comm = 0.0;
        const accountType = document.getElementById('bt-account-type') ? document.getElementById('bt-account-type').value : 'standard';
        if (accountType === 'standard') { spread = 200.0; comm = 0.0; }
        else if (accountType === 'pro') { spread = 112.0; comm = 0.0; }
        else if (accountType === 'raw') { spread = 37.0; comm = 7.0; }
        else if (accountType === 'zero') { spread = 0.0; comm = 11.0; }
        else if (accountType === 'custom') {
            spread = parseFloat(document.getElementById('bt-spread').value || 10.0);
            comm = parseFloat(document.getElementById('bt-comm').value || 0.0);
        }
        
        const strategy = document.getElementById('bt-strategy') ? document.getElementById('bt-strategy').value : 'default';
        currentStrategyName = strategy;
        const customParams = {
            direction: document.getElementById('bt-custom-dir') ? document.getElementById('bt-custom-dir').value : 'BOTH',
            days_mode: document.getElementById('bt-custom-days') ? document.getElementById('bt-custom-days').value : '24_5',
            risk: parseFloat(document.getElementById('bt-custom-risk') ? document.getElementById('bt-custom-risk').value : 0.1),
            tp: parseInt(document.getElementById('bt-custom-tp') ? document.getElementById('bt-custom-tp').value : 10000),
            sl: parseInt(document.getElementById('bt-custom-sl') ? document.getElementById('bt-custom-sl').value : 1000),
            sessions: document.getElementById('bt-custom-sessions') ? document.getElementById('bt-custom-sessions').value : ''
        };
        
        btLoading.textContent = "Running AI Strategy Optimization... (This may take up to 30 seconds)";
        btLoading.classList.remove('hidden');
        btResults.classList.add('hidden');
        if (exportBtBtn) exportBtBtn.classList.add('hidden');
        
        try {
            const res = await fetch('/api/backtest/optimize', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ duration_mode: durationMode, duration_val: durationVal, capital, spread, comm, strategy, symbol, timeframe, custom_params: customParams })
            });
            const data = await res.json();
            if(data.status === 'error') {
                alert(data.message);
                btLoading.classList.add('hidden');
                return;
            }
            
            btLoading.classList.add('hidden');
            btResults.classList.remove('hidden');
            
            btKpiGrid.innerHTML = `
                <div style="grid-column: span 3;">
                    <h3 style="color:var(--accent-color); margin-bottom:10px;">Optimization Complete - Top 5 Parameters Found</h3>
                    <table class="terminal-table" style="width:100%; text-align:left;">
                        <tr><th>Rank</th><th>TP Multiplier</th><th>SL Multiplier</th><th>Win Rate</th><th>Trades</th><th>Net Profit</th></tr>
                        ${data.results.slice(0, 5).map((r, i) => `<tr>
                            <td>#${i+1}</td>
                            <td>${r.tp_mult}x</td>
                            <td>${r.sl_mult}x</td>
                            <td>${r.win_rate.toFixed(1)}%</td>
                            <td>${r.trades_count}</td>
                            <td class="${r.profit >= 0 ? 'text-buy' : 'text-sell'}">$${r.profit.toFixed(2)}</td>
                        </tr>`).join('')}
                    </table>
                </div>
            `;
            
            lastTrades = data.best_trades;
            try {
                if (data.best_ohlc && data.best_trades) renderCandlesticks(data.best_ohlc, data.best_trades);
            } catch (err) {
                console.error("Optimize Candlesticks render error:", err);
            }
            try {
                renderHeatmap(data.best_trades);
            } catch (err) {
                console.error("Optimize Heatmap render error:", err);
            }
            if (exportBtBtn) exportBtBtn.classList.remove('hidden');
            
            const labels = [];
            const chartData = [];
            const dailyPnL = {};
            let cumPnl = 0;
            data.best_trades.forEach((t, i) => {
                cumPnl += t.profit;
                labels.push(`Trade ${i+1}`);
                chartData.push(cumPnl);
                
                if (t.entry_time) {
                    const d = new Date(t.entry_time);
                    if (!isNaN(d.getTime())) {
                        const day = d.toISOString().split('T')[0];
                        if (!dailyPnL[day]) dailyPnL[day] = 0;
                        dailyPnL[day] += t.profit;
                    }
                }
            });
            
            let periodicLabels = Object.keys(dailyPnL).sort();
            let periodicData = [];
            if (periodicLabels.length > 60) {
                const monthlyPnL = {};
                periodicLabels.forEach(d => {
                    const m = d.substring(0, 7);
                    if (!monthlyPnL[m]) monthlyPnL[m] = 0;
                    monthlyPnL[m] += dailyPnL[d];
                });
                periodicLabels = Object.keys(monthlyPnL).sort();
                periodicData = periodicLabels.map(m => monthlyPnL[m]);
                const title = document.getElementById('pnl-chart-title');
                if (title) title.innerText = 'Monthly Returns';
            } else {
                periodicData = periodicLabels.map(d => dailyPnL[d]);
                const title = document.getElementById('pnl-chart-title');
                if (title) title.innerText = 'Daily Returns';
            }
            const pnlBarColors = periodicData.map(v => v >= 0 ? 'rgba(14, 203, 129, 0.8)' : 'rgba(246, 70, 93, 0.8)');

            if (btChartInstance) btChartInstance.destroy();
            const ctx2 = document.getElementById('btChart').getContext('2d');
            btChartInstance = new Chart(ctx2, {
                type: 'line',
                data: { labels: labels, datasets: [{ label: 'Opt PnL', data: chartData, borderColor: '#0ECB81', backgroundColor: 'rgba(14, 203, 129, 0.1)', borderWidth: 2, tension: 0.1, fill: true, pointRadius: 0 }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { position: 'right' }, x: { display: false } }, animation: { duration: 1000 } }
            });

            if (btPnlChartInstance) btPnlChartInstance.destroy();
            const ctxPnl = document.getElementById('btPnlChart').getContext('2d');
            btPnlChartInstance = new Chart(ctxPnl, {
                type: 'bar',
                data: { labels: periodicLabels, datasets: [{ label: 'Periodic PnL', data: periodicData, backgroundColor: pnlBarColors, borderWidth: 0 }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { position: 'right' }, x: { display: true } }, animation: { duration: 1000 } }
            });
            
            const btTbody = document.getElementById('bt-trades-tbody');
            if (btTbody) btTbody.innerHTML = '<tr><td colspan="12" style="text-align:center;">Check exported CSV for full trade list</td></tr>';
            
        } catch(e) {
            alert("Simulation failed: " + e.stack);
            btLoading.classList.add('hidden');
        }
    });
}

if(exportBtBtn) {
    exportBtBtn.addEventListener('click', () => {
        if(!lastTrades || lastTrades.length === 0) return;
        let csv = "Ticket,Direction,Level,Entry Time,Exit Time,Entry Price,Exit Price,Volume,Profit,Result\n";
        lastTrades.forEach(t => {
            csv += `${t.ticket || ''},${t.direction},${t.level},${t.entry_time},${t.exit_time},${t.entry_price},${t.exit_price},${t.volume},${t.profit.toFixed(2)},${t.result}\n`;
        });
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `backtest_trades_${currentStrategyName}_${Date.now()}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    });
}

// Original DOM Elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const balanceDisplay = document.getElementById('balance-display');
const equityDisplay = document.getElementById('equity-display');
const levelDisplay = document.getElementById('level-display');
const directionDisplay = document.getElementById('direction-display');
const tradesTbody = document.getElementById('trades-tbody');
const strategySelector = document.getElementById('strategy-selector');
const applyStrategyBtn = document.getElementById('apply-strategy-btn');
const deleteStrategyBtn = document.getElementById('delete-strategy-btn');
const editStrategyBtn = document.getElementById('edit-strategy-btn');
const duplicateStrategyBtn = document.getElementById('duplicate-strategy-btn');

// Modal Elements
const modal = document.getElementById('strategy-modal');
const openModalBtn = document.getElementById('open-builder-btn');
const closeModalBtn = document.getElementById('close-modal-btn');
const saveStratBtn = document.getElementById('save-strat-btn');

// Chart Setup
const ctx = document.getElementById('pnlChart').getContext('2d');
Chart.defaults.color = '#787B86';
Chart.defaults.font.family = "'Inter', sans-serif";

const pnlChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Cumulative PnL',
            data: [],
            borderColor: '#2962FF',
            backgroundColor: 'rgba(41, 98, 255, 0.1)',
            borderWidth: 2,
            tension: 0.1, // Less curved, more professional
            fill: true,
            pointRadius: 0, // Hide points unless hovered
            pointHoverRadius: 4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            y: { grid: { color: '#2A2E39' }, position: 'right' }, // Right-side axis typical of trading
            x: { grid: { display: false } }
        },
        animation: { duration: 0 }
    }
});

// Flash Animation helper
function animateValue(element, newValue) {
    if (element.textContent !== newValue) {
        const oldVal = parseFloat(element.textContent);
        const newVal = parseFloat(newValue);
        element.textContent = newValue;
        
        if (!isNaN(oldVal) && !isNaN(newVal)) {
            element.classList.remove('flash-up', 'flash-down');
            void element.offsetWidth; // Trigger reflow
            element.classList.add(newVal > oldVal ? 'flash-up' : 'flash-down');
            setTimeout(() => {
                element.classList.remove('flash-up', 'flash-down');
            }, 300);
        }
    }
}

let loadedStrategies = {};
// Fetch Strategies
async function fetchStrategies() {
    try {
        const res = await fetch('/api/strategies');
        loadedStrategies = await res.json();
        const data = loadedStrategies;
        
        const currentSelection = strategySelector.value;
        strategySelector.innerHTML = '';
        Object.keys(data).forEach(key => {
            const opt = document.createElement('option');
            opt.value = key;
            opt.textContent = key;
            strategySelector.appendChild(opt);
        });
        if (currentSelection && data[currentSelection]) {
            strategySelector.value = currentSelection;
        }
    } catch (e) {
        console.error("Failed to load strategies", e);
    }
}

// Modal Logic
function addStratSessionRow(start = '', end = '') {
    const container = document.getElementById('strat-sessions-container');
    const row = document.createElement('div');
    row.style.display = 'flex';
    row.style.gap = '10px';
    row.style.alignItems = 'center';
    row.innerHTML = `
        <span style="color:var(--text-muted);">Start</span>
        <input type="time" class="terminal-input session-start" style="width:120px;" value="${start}">
        <span style="color:var(--text-muted);">End</span>
        <input type="time" class="terminal-input session-end" style="width:120px;" value="${end}">
        <button type="button" class="terminal-btn outline remove-session" style="padding: 8px; border-color: var(--error-color); color: var(--error-color);"><i class="fas fa-times"></i></button>
    `;
    row.querySelector('.remove-session').addEventListener('click', () => row.remove());
    container.appendChild(row);
}

document.getElementById('strat-add-session-btn').addEventListener('click', () => addStratSessionRow());

function populateStrategyModal(name, config, isDuplicate) {
    document.getElementById('strat-name').value = isDuplicate ? `Copy of ${name}` : name;
    document.getElementById('strat-name').readOnly = !isDuplicate;
    document.getElementById('strat-symbol').value = config.symbol || 'XAUUSDm';
    document.getElementById('strat-tf').value = config.timeframe || (config.timeframe_minutes ? `M${config.timeframe_minutes}` : 'M5');
    document.getElementById('strat-cap').value = config.initial_capital || 1110.0;
    if (config.indicators) {
        document.getElementById('ema-enabled').checked = config.indicators.ema_enabled || false;
        document.getElementById('ema-fast').value = config.indicators.ema_fast || 9;
        document.getElementById('ema-slow').value = config.indicators.ema_slow || 21;
    }
    document.getElementById('strat-dir').value = config.direction || 'BOTH';
    document.getElementById('strat-days').value = config.days_mode || '24_5';
    document.getElementById('strat-risk').value = config.risk_percent || 1.0;
    document.getElementById('strat-tp').value = config.tp_points || 10000;
    document.getElementById('strat-sl').value = config.sl_points || 1000;
    
    const sessionsContainer = document.getElementById('strat-sessions-container');
    sessionsContainer.innerHTML = '';
    if (config.sessions_ist) {
        if (Array.isArray(config.sessions_ist)) {
            config.sessions_ist.forEach(s => addStratSessionRow(s.start, s.end));
        } else {
            // Backwards compatibility with dict
            Object.values(config.sessions_ist).forEach(s => addStratSessionRow(s.start, s.end));
        }
    }

    modal.classList.remove('hidden');
}

openModalBtn.addEventListener('click', () => {
    document.getElementById('strategy-form').reset();
    document.getElementById('strat-name').readOnly = false;
    document.getElementById('strat-sessions-container').innerHTML = '';
    modal.classList.remove('hidden');
});
closeModalBtn.addEventListener('click', () => modal.classList.add('hidden'));
window.addEventListener('click', (e) => { if (e.target === modal) modal.classList.add('hidden'); });

saveStratBtn.addEventListener('click', async () => {
    const name = document.getElementById('strat-name').value;
    if (!name) return alert("Strategy name required");

    // Parse dynamic sessions
    const sessionRows = document.querySelectorAll('#strat-sessions-container > div');
    const sessions_ist = [];
    sessionRows.forEach(row => {
        const start = row.querySelector('.session-start').value;
        const end = row.querySelector('.session-end').value;
        if (start && end) {
            sessions_ist.push({ start, end });
        }
    });

    const config = {
        symbol: document.getElementById('strat-symbol').value,
        timeframe: document.getElementById('strat-tf').value,
        initial_capital: parseFloat(document.getElementById('strat-cap').value),
        indicators: {
            ema_enabled: document.getElementById('ema-enabled').checked,
            ema_fast: parseInt(document.getElementById('ema-fast').value),
            ema_slow: parseInt(document.getElementById('ema-slow').value)
        },
        sessions_ist: sessions_ist,
        direction: document.getElementById('strat-dir') ? document.getElementById('strat-dir').value : 'BOTH',
        days_mode: document.getElementById('strat-days') ? document.getElementById('strat-days').value : '24_5',
        risk_percent: parseFloat(document.getElementById('strat-risk').value),
        tp_points: parseInt(document.getElementById('strat-tp').value),
        sl_points: parseInt(document.getElementById('strat-sl').value)
    };

    try {
        await fetch('/api/strategies/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, config })
        });
        modal.classList.add('hidden');
        fetchStrategies();
    } catch (e) {
        alert("Failed to save strategy");
    }
});

applyStrategyBtn.addEventListener('click', async () => {
    const name = strategySelector.value;
    if(!name) return;
    
    applyStrategyBtn.textContent = '...';
    try {
        await fetch('/api/strategies/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        setTimeout(() => { applyStrategyBtn.textContent = 'Apply'; }, 500);
    } catch (e) {
        alert("Failed to apply");
    }
});

if (editStrategyBtn) {
    editStrategyBtn.addEventListener('click', () => {
        const name = strategySelector.value;
        if(!name || !loadedStrategies[name]) return;
        populateStrategyModal(name, loadedStrategies[name], false);
    });
}

if (duplicateStrategyBtn) {
    duplicateStrategyBtn.addEventListener('click', () => {
        const name = strategySelector.value;
        if(!name || !loadedStrategies[name]) return;
        populateStrategyModal(name, loadedStrategies[name], true);
    });
}

deleteStrategyBtn.addEventListener('click', async () => {
    const name = strategySelector.value;
    if(!name) return;
    if(!confirm(`Delete strategy ${name}?`)) return;
    
    try {
        await fetch('/api/strategies/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        fetchStrategies();
    } catch (e) {
        alert("Failed to delete");
    }
});

// Start/Stop Bot
startBtn.addEventListener('click', async () => {
    try {
        const res = await fetch('/api/bot/start', { method: 'POST' });
        const data = await res.json();
        if(data.status === 'error') alert(data.message);
    } catch (e) { console.error(e); }
    fetchState();
});

stopBtn.addEventListener('click', async () => {
    try {
        const res = await fetch('/api/bot/stop', { method: 'POST' });
        const data = await res.json();
        if(data.status === 'error') alert(data.message);
    } catch (e) { console.error(e); }
    fetchState();
});

// Polling State
async function fetchState() {
    try {
        const res = await fetch('/api/state');
        const state = await res.json();

        // Status
        if (state.status === 'RUNNING') {
            statusDot.className = 'dot running';
            statusText.textContent = 'RUNNING';
            startBtn.disabled = true; startBtn.style.opacity = '0.5';
            stopBtn.disabled = false; stopBtn.style.opacity = '1';
        } else {
            statusDot.className = 'dot stopped';
            statusText.textContent = 'STOPPED';
            startBtn.disabled = false; startBtn.style.opacity = '1';
            stopBtn.disabled = true; stopBtn.style.opacity = '0.5';
        }

        // Topbar Animations
        animateValue(balanceDisplay, state.balance.toFixed(2));
        animateValue(equityDisplay, state.equity.toFixed(2));
        
        levelDisplay.textContent = state.current_level;
        directionDisplay.textContent = state.next_direction;
        directionDisplay.className = 'value ' + state.next_direction.toLowerCase();

        // KPI Updates
        if (state.kpis) {
            animateValue(document.getElementById('kpi-net-profit'), state.kpis.net_profit.toFixed(2));
            document.getElementById('kpi-win-rate').textContent = state.kpis.win_rate.toFixed(1) + '%';
            animateValue(document.getElementById('kpi-total-trades'), state.kpis.total_trades);
            animateValue(document.getElementById('kpi-profit-factor'), state.kpis.profit_factor.toFixed(2));
            
            const avgWinLoss = `${state.kpis.avg_win.toFixed(2)} / ${state.kpis.avg_loss.toFixed(2)}`;
            document.getElementById('kpi-avg-win-loss').textContent = avgWinLoss;
            
            animateValue(document.getElementById('kpi-drawdown'), state.kpis.drawdown.toFixed(2));
            
            const marginFree = `${state.margin.toFixed(2)} / ${state.free_margin.toFixed(2)}`;
            document.getElementById('kpi-margin').textContent = marginFree;
            
            animateValue(document.getElementById('kpi-recovery'), state.kpis.recovery_count);
            
            // Color code Net Profit
            document.getElementById('kpi-net-profit').style.color = state.kpis.net_profit >= 0 ? '#0ECB81' : '#F6465D';
        }

        // Update Table
        tradesTbody.innerHTML = '';
        let cumulativePnl = 0;
        const chartLabels = [];
        const chartData = [];

        // Reverse to show oldest first in chart, newest first in table
        const reversedTrades = [...state.recent_trades].reverse();
        
        reversedTrades.forEach((trade, index) => {
            cumulativePnl += (trade.profit || 0);
            chartLabels.push(`#${trade.ticket}`);
            chartData.push(cumulativePnl);
        });

        // Populate Table (newest first)
        state.recent_trades.forEach(trade => {
            const tr = document.createElement('tr');
            const profitClass = trade.profit >= 0 ? 'text-buy' : 'text-sell';
            const profitText = trade.profit > 0 ? `+${trade.profit.toFixed(2)}` : trade.profit.toFixed(2);
            
            tr.innerHTML = `
                <td>${trade.ticket}</td>
                <td class="${trade.type.toLowerCase() === 'buy' ? 'text-buy' : 'text-sell'}">${trade.type}</td>
                <td>L${trade.level}</td>
                <td>${trade.close_time}</td>
                <td class="${profitClass}">${profitText}</td>
            `;
            tradesTbody.appendChild(tr);
        });

        // Update Chart
        pnlChart.data.labels = chartLabels;
        pnlChart.data.datasets[0].data = chartData;
        pnlChart.update();

    } catch(e) {
        console.error("State poll failed", e);
    }
}

// Settings UI Logic
async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        document.getElementById('auto-on-enabled').checked = data.auto_on_enabled || false;
        document.getElementById('auto-off-enabled').checked = data.auto_off_enabled || false;
        document.getElementById('auditor-enabled').checked = data.auditor_enabled || false;
        document.getElementById('set-telegram-enabled').checked = data.telegram_enabled || false;
        document.getElementById('set-telegram-bot-token').value = data.telegram_bot_token || '';
        document.getElementById('set-telegram-chat-id').value = data.telegram_chat_id || '';
        const container = document.getElementById('sessions-container');
        container.innerHTML = '';
        (data.sessions_ist || []).forEach(session => {
            addSessionRow(session.start, session.end);
        });
    } catch(e) { console.error("Failed to load settings", e); }
}

function addSessionRow(start = "09:00", end = "17:00") {
    const container = document.getElementById('sessions-container');
    const div = document.createElement('div');
    div.style.display = 'flex'; div.style.gap = '10px';
    div.innerHTML = `
        <input type="time" class="session-start" value="${start}" style="background:var(--bg-lighter); color:#fff; border:1px solid var(--border-color); padding:5px; border-radius:4px;">
        <span style="color:var(--text-muted); align-self:center;">to</span>
        <input type="time" class="session-end" value="${end}" style="background:var(--bg-lighter); color:#fff; border:1px solid var(--border-color); padding:5px; border-radius:4px;">
        <button class="delete-session-btn" style="background:transparent; color:var(--sell-color); border:1px solid var(--sell-color); padding:5px 10px; border-radius:4px; cursor:pointer;">X</button>
    `;
    div.querySelector('.delete-session-btn').addEventListener('click', () => div.remove());
    container.appendChild(div);
}

document.getElementById('add-session-btn').addEventListener('click', () => addSessionRow());

document.getElementById('save-settings-btn').addEventListener('click', async () => {
    const rows = document.querySelectorAll('#sessions-container > div');
    const sessions_ist = [];
    rows.forEach(row => {
        sessions_ist.push({
            start: row.querySelector('.session-start').value,
            end: row.querySelector('.session-end').value
        });
    });
    const auto_on_enabled = document.getElementById('auto-on-enabled').checked;
    const auto_off_enabled = document.getElementById('auto-off-enabled').checked;
    const auditor_enabled = document.getElementById('auditor-enabled').checked;
    const telegram_enabled = document.getElementById('set-telegram-enabled').checked;
    const telegram_bot_token = document.getElementById('set-telegram-bot-token').value;
    const telegram_chat_id = document.getElementById('set-telegram-chat-id').value;
    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ sessions_ist, auto_on_enabled, auto_off_enabled, auditor_enabled, telegram_enabled, telegram_bot_token, telegram_chat_id })
        });
        alert("Settings saved successfully! OS Scheduler Updated.");
    } catch(e) { alert("Failed to save settings."); }
});

// Init
fetchStrategies();
fetchState();
loadSettings();
setInterval(fetchState, 1500); // Faster polling for professional feel

// COPY TO LIVE Logic
function copyToLiveEnvironment(sourceName, configObj) {
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.getElementById('view-settings').classList.remove('hidden');
    
    populateStrategyModal(sourceName, configObj, true);
}

const copyLiveBtBtn = document.getElementById('copy-live-bt-btn');
if (copyLiveBtBtn) {
    copyLiveBtBtn.addEventListener('click', () => {
        const isCustom = document.getElementById('bt-strategy').value === 'custom';
        const timeframeStr = document.getElementById('bt-timeframe').value;
        
        const rawSessions = document.getElementById('bt-custom-sessions').value;
        const sessions_ist = [];
        if (rawSessions) {
            rawSessions.split(',').forEach(s => {
                const parts = s.split('-');
                if (parts.length === 2) {
                    sessions_ist.push({ start: parts[0].trim(), end: parts[1].trim() });
                }
            });
        }

        const configObj = {
            symbol: document.getElementById('bt-symbol').value.replace('m', ''),
            timeframe: timeframeStr,
            initial_capital: parseFloat(document.getElementById('bt-capital').value),
            direction: document.getElementById('bt-custom-dir').value,
            days_mode: document.getElementById('bt-custom-days').value,
            risk_percent: parseFloat(document.getElementById('bt-custom-risk').value),
            tp_points: parseInt(document.getElementById('bt-custom-tp').value),
            sl_points: parseInt(document.getElementById('bt-custom-sl').value),
            sessions_ist: sessions_ist
        };
        
        copyToLiveEnvironment("Simulator Strategy", configObj);
    });
}

function renderCandlesticks(ohlc, trades) {
    const container = document.getElementById('btCandleChart');
    if (!container) return;
    
    container.innerHTML = '';
    container.style.position = 'relative'; // For tooltip
    if (window.btCandlestickChartInstance) {
        window.btCandlestickChartInstance.remove();
    }
    
    const chartOptions = { 
        layout: { background: { type: 'solid', color: '#1E222D' }, textColor: '#D9D9D9' },
        grid: { vertLines: { color: '#2B2F3A' }, horzLines: { color: '#2B2F3A' } },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        rightPriceScale: { borderColor: '#2B2F3A' },
        timeScale: { borderColor: '#2B2F3A', timeVisible: true, secondsVisible: false },
        watermark: { color: 'rgba(255, 255, 255, 0.04)', visible: true, text: 'ALGORITHMIC BACKTEST', fontSize: 48, horzAlign: 'center', vertAlign: 'center' }
    };
    
    const chart = LightweightCharts.createChart(container, chartOptions);
    window.btCandlestickChartInstance = chart;
    
    const candleSeries = chart.addCandlestickSeries({
        upColor: '#0ECB81', downColor: '#F6465D', borderDownColor: '#F6465D', borderUpColor: '#0ECB81', wickDownColor: '#F6465D', wickUpColor: '#0ECB81'
    });
    
    const volumeSeries = chart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: { type: 'volume' },
        priceScaleId: '', 
        scaleMargins: { top: 0.8, bottom: 0 }
    });
    
    const ema9Series = chart.addLineSeries({ color: 'rgba(41, 98, 255, 0.7)', lineWidth: 2, title: 'EMA 9', crosshairMarkerVisible: false });
    const ema21Series = chart.addLineSeries({ color: 'rgba(255, 109, 0, 0.7)', lineWidth: 2, title: 'EMA 21', crosshairMarkerVisible: false });
    
    const formattedOhlc = ohlc.map(item => {
        let ts = 0;
        if (typeof item.time === 'number') { ts = item.time; }
        else { ts = Math.floor(new Date(item.time).getTime() / 1000); }
        return { time: ts, open: item.open, high: item.high, low: item.low, close: item.close, volume: item.volume || 0 };
    }).filter(item => !isNaN(item.time) && item.time > 0).sort((a, b) => a.time - b.time);
    
    const uniqueOhlc = [];
    const volumeData = [];
    let lastTime = 0;
    
    formattedOhlc.forEach(item => { 
        if (item.time !== lastTime) { 
            uniqueOhlc.push(item); 
            volumeData.push({ time: item.time, value: item.volume, color: item.close >= item.open ? 'rgba(14, 203, 129, 0.3)' : 'rgba(246, 70, 93, 0.3)' });
            lastTime = item.time; 
        } 
    });
    
    const calcEMA = (data, period) => {
        const k = 2 / (period + 1);
        let ema = data[0].close;
        const res = [];
        data.forEach(d => {
            ema = (d.close - ema) * k + ema;
            res.push({ time: d.time, value: ema });
        });
        return res;
    };
    
    if (uniqueOhlc.length > 0) {
        candleSeries.setData(uniqueOhlc);
        volumeSeries.setData(volumeData);
        if(uniqueOhlc.length > 21) {
            ema9Series.setData(calcEMA(uniqueOhlc, 9));
            ema21Series.setData(calcEMA(uniqueOhlc, 21));
        }
    }
    
    const markers = [];
    trades.forEach(t => {
        if (t.entry_time) {
            let ts = Math.floor(new Date(t.entry_time).getTime() / 1000);
            if (!isNaN(ts)) markers.push({ time: ts, position: t.direction === 'BUY' ? 'belowBar' : 'aboveBar', color: t.direction === 'BUY' ? '#0ECB81' : '#F6465D', shape: t.direction === 'BUY' ? 'arrowUp' : 'arrowDown', text: t.direction });
        }
        if (t.exit_time) {
            let ts = Math.floor(new Date(t.exit_time).getTime() / 1000);
            if (!isNaN(ts)) markers.push({ time: ts, position: t.result === 'TP' ? 'aboveBar' : 'belowBar', color: t.result === 'TP' ? '#0ECB81' : '#F6465D', shape: 'circle', text: t.result });
        }
    });
    markers.sort((a, b) => a.time - b.time);
    
    const uniqueMarkers = [];
    for (let i = 0; i < markers.length; i++) {
        if (uniqueMarkers.length > 0 && uniqueMarkers[uniqueMarkers.length - 1].time === markers[i].time) {
            uniqueMarkers[uniqueMarkers.length - 1].text += ' / ' + markers[i].text;
        } else {
            uniqueMarkers.push(markers[i]);
        }
    }
    
    try {
        if (uniqueMarkers.length > 0) candleSeries.setMarkers(uniqueMarkers);
    } catch (e) {
        console.error("Error setting markers:", e);
    }
    
    // Tooltip logic
    let tooltip = document.getElementById('bt-chart-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'bt-chart-tooltip';
        tooltip.style = 'position: absolute; display: none; padding: 8px; box-sizing: border-box; font-size: 13px; font-family: "Roboto Mono", monospace; color: #D9D9D9; background-color: rgba(30, 34, 45, 0.8); text-align: left; z-index: 1000; pointer-events: none; border: 1px solid #3B4050; border-radius: 4px; left: 12px; top: 12px;';
        container.appendChild(tooltip);
    }
    
    chart.subscribeCrosshairMove(param => {
        if (param.point === undefined || !param.time || param.point.x < 0 || param.point.x > container.clientWidth || param.point.y < 0 || param.point.y > container.clientHeight) {
            tooltip.style.display = 'none';
        } else {
            const dateStr = new Date(param.time * 1000).toISOString().replace('T', ' ').substring(0, 19);
            const data = param.seriesData.get(candleSeries);
            const volData = param.seriesData.get(volumeSeries);
            if (data) {
                const color = data.close >= data.open ? '#0ECB81' : '#F6465D';
                tooltip.style.display = 'block';
                tooltip.innerHTML = `
                    <div style="font-weight: 600; margin-bottom: 6px; color: #8F98AD;">${dateStr} (UTC)</div>
                    <div>O: <span style="color:${color}">${data.open.toFixed(2)}</span> H: <span style="color:${color}">${data.high.toFixed(2)}</span></div>
                    <div>L: <span style="color:${color}">${data.low.toFixed(2)}</span> C: <span style="color:${color}">${data.close.toFixed(2)}</span></div>
                    ${volData ? `<div style="margin-top:4px; color:#8F98AD;">Vol: ${volData.value.toFixed(0)}</div>` : ''}
                `;
            }
        }
    });
    
    chart.timeScale().fitContent();
    
    // --- Custom TP/SL Trade Zones Overlay ---
    let overlayCanvas = document.getElementById('trade-zones-overlay');
    if (!overlayCanvas) {
        overlayCanvas = document.createElement('canvas');
        overlayCanvas.id = 'trade-zones-overlay';
        overlayCanvas.style.position = 'absolute';
        overlayCanvas.style.top = '0';
        overlayCanvas.style.left = '0';
        overlayCanvas.style.width = '100%';
        overlayCanvas.style.height = '100%';
        overlayCanvas.style.pointerEvents = 'none';
        overlayCanvas.style.zIndex = '500';
        container.appendChild(overlayCanvas);
    }
    
    if (window.btTradeOverlayReq) cancelAnimationFrame(window.btTradeOverlayReq);
    
    let overlayActive = true;
    window.btTradeOverlayState = '';
    
    const drawOverlay = () => {
        if (!overlayActive || !document.getElementById('trade-zones-overlay')) return;
        
        const canvas = document.getElementById('trade-zones-overlay');
        const checkbox = document.getElementById('show-trade-zones');
        
        if (canvas.width !== container.clientWidth || canvas.height !== container.clientHeight) {
            canvas.width = container.clientWidth;
            canvas.height = container.clientHeight;
            window.btTradeOverlayState = ''; // force redraw on resize
        }
        
        const isChecked = checkbox ? checkbox.checked : true;
        const logicalRange = chart.timeScale().getVisibleLogicalRange();
        const priceRef = candleSeries.priceToCoordinate(uniqueOhlc[0]?.close || 0);
        const stateHash = logicalRange ? `${logicalRange.from}_${logicalRange.to}_${priceRef}_${canvas.width}_${isChecked}` : '';
        
        if (stateHash === window.btTradeOverlayState) {
            window.btTradeOverlayReq = requestAnimationFrame(drawOverlay);
            return;
        }
        window.btTradeOverlayState = stateHash;
        
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (isChecked && logicalRange) {
            const paneWidth = chart.timeScale().width() || canvas.width - 55; 
            ctx.save();
            ctx.beginPath();
            ctx.rect(0, 0, paneWidth, canvas.height - 25);
            ctx.clip();
            
            trades.forEach(t => {
                if (!t.entry_time || !t.exit_time || !t.tp_price || !t.sl_price) return;
                
                const tsEntry = Math.floor(new Date(t.entry_time).getTime() / 1000);
                const tsExit = Math.floor(new Date(t.exit_time).getTime() / 1000);
                
                let xEntry = chart.timeScale().timeToCoordinate(tsEntry);
                let xExit = chart.timeScale().timeToCoordinate(tsExit);
                
                if (xEntry === null || xExit === null) return;
                
                // If trade opened and closed very quickly, give it a min width so the box is visible
                if (xExit - xEntry < 6) xExit = xEntry + 6; 
                
                // Don't render if it's completely off the screen horizontally
                if (Math.max(xEntry, xExit) < 0 || Math.min(xEntry, xExit) > paneWidth) return;
                
                const yEntry = candleSeries.priceToCoordinate(t.entry_price);
                const yTP = candleSeries.priceToCoordinate(t.tp_price);
                const ySL = candleSeries.priceToCoordinate(t.sl_price);
                const yExitReal = candleSeries.priceToCoordinate(t.exit_price);
                
                if (yEntry === null || yTP === null || ySL === null || yExitReal === null) return;
                
                // TP Zone (Green Shade)
                ctx.fillStyle = 'rgba(14, 203, 129, 0.15)';
                ctx.fillRect(xEntry, Math.min(yEntry, yTP), xExit - xEntry, Math.abs(yEntry - yTP));
                
                // SL Zone (Red Shade)
                ctx.fillStyle = 'rgba(246, 70, 93, 0.15)';
                ctx.fillRect(xEntry, Math.min(yEntry, ySL), xExit - xEntry, Math.abs(yEntry - ySL));
                
                // Entry Line (Dashed)
                ctx.beginPath();
                ctx.moveTo(xEntry, yEntry);
                ctx.lineTo(xExit, yEntry);
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 4]);
                ctx.stroke();
                
                // Trade Journey Line (Solid pointer from Entry to actual Exit)
                ctx.beginPath();
                ctx.moveTo(xEntry, yEntry);
                ctx.lineTo(xExit, yExitReal);
                ctx.strokeStyle = t.profit > 0 ? '#0ECB81' : '#F6465D';
                ctx.lineWidth = 2;
                ctx.setLineDash([]);
                ctx.stroke();
                
                // End Dot
                ctx.beginPath();
                ctx.arc(xExit, yExitReal, 3, 0, 2 * Math.PI);
                ctx.fillStyle = t.profit > 0 ? '#0ECB81' : '#F6465D';
                ctx.fill();
            });
            ctx.restore();
        }
        
        window.btTradeOverlayReq = requestAnimationFrame(drawOverlay);
    };
    
    drawOverlay();
}
