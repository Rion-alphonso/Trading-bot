const ohlc = [{"time": "2026-05-29T16:20:00Z", "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15}, {"time": "2026-05-29T16:25:00Z", "open": 1.15, "high": 1.25, "low": 1.1, "close": 1.2}];
const trades = [{"entry_time": "2026-05-29T16:20:00Z", "exit_time": "2026-05-29T16:20:00Z", "direction": "BUY", "result": "SL"}];

const formattedOhlc = ohlc.map(item => {
    let ts = 0;
    if (typeof item.time === 'number') { ts = item.time; }
    else { ts = Math.floor(new Date(item.time).getTime() / 1000); }
    return { time: ts, open: item.open, high: item.high, low: item.low, close: item.close };
}).filter(item => !isNaN(item.time) && item.time > 0).sort((a, b) => a.time - b.time);

const uniqueOhlc = [];
let lastTime = 0;
formattedOhlc.forEach(item => { if (item.time !== lastTime) { uniqueOhlc.push(item); lastTime = item.time; } });

console.log("uniqueOhlc:", uniqueOhlc);

const markers = [];
trades.forEach(t => {
    if (t.entry_time) {
        let ts = Math.floor(new Date(t.entry_time).getTime() / 1000);
        if (!isNaN(ts)) {
            markers.push({ time: ts, position: t.direction === 'BUY' ? 'belowBar' : 'aboveBar', color: t.direction === 'BUY' ? '#0ECB81' : '#F6465D', shape: t.direction === 'BUY' ? 'arrowUp' : 'arrowDown', text: t.direction });
        }
    }
    if (t.exit_time) {
        let ts = Math.floor(new Date(t.exit_time).getTime() / 1000);
        if (!isNaN(ts)) {
            markers.push({ time: ts, position: t.result === 'TP' ? 'aboveBar' : 'belowBar', color: t.result === 'TP' ? '#0ECB81' : '#F6465D', shape: 'circle', text: t.result });
        }
    }
});
markers.sort((a, b) => a.time - b.time);
console.log("markers:", markers);
