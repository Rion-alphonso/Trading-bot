const fs = require('fs');
const data = JSON.parse(fs.readFileSync('api_res.json', 'utf-8'));

let runningCapital = 1000;
try {
    data.trades.forEach((t, i) => {
        runningCapital += t.profit;
        const profitClass = t.profit >= 0 ? 'text-buy' : 'text-sell';
        const profitText = t.profit > 0 ? '+' + t.profit.toFixed(2) : t.profit.toFixed(2);
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
        
        const html = `
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
    });
    console.log("SUCCESS");
} catch(e) {
    console.log("CRASH:", e.message, e.stack);
}
