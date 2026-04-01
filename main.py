import json
import asyncio
import uvicorn
import random
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- THE LIVE UI ---
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>DERIV_OS // LIVE_MANUAL_STATION</title>
    <style>
        body { background: #020202; color: #00ff41; font-family: 'Courier New', monospace; margin: 0; overflow: hidden; }
        
        /* HEADER SECTION */
        .top-bar { display: flex; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #00ff41; background: #000; }
        
        /* VOLATILITY MARKET WATCH (THE "LIVING" ROW) */
        .market-watch { display: flex; gap: 10px; padding: 15px; background: #0a0a0a; border-bottom: 1px solid #333; overflow-x: auto; }
        .market-card { 
            min-width: 160px; border: 1px solid #00ff41; padding: 10px; text-align: center; 
            cursor: pointer; transition: 0.2s; background: rgba(0, 255, 65, 0.05);
        }
        .market-card.selected { background: #ffcc00; color: #000; border: 2px solid #fff; box-shadow: 0 0 15px #ffcc00; }
        .percent-box { font-size: 22px; font-weight: 900; margin: 5px 0; }
        
        /* MAIN LAYOUT */
        .grid { display: grid; grid-template-columns: 350px 1fr; height: 75vh; }
        .sidebar { border-right: 1px solid #333; padding: 20px; background: #050505; }
        .terminal { position: relative; background: #000; overflow: hidden; padding: 20px; display: flex; flex-direction: column; }
        
        /* CODING ANIMATION EFFECT */
        #code-scroll { position: absolute; top: 0; left: 0; width: 100%; height: 100%; color: rgba(0, 255, 65, 0.1); font-size: 10px; pointer-events: none; white-space: pre; overflow: hidden; }
        
        input, select { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; width: 90%; margin-bottom: 15px; }
        .btn-run { background: #00ff41; color: #000; font-weight: bold; font-size: 18px; height: 50px; width: 100%; cursor: pointer; border: none; }
        .btn-run:active { background: #fff; }
        
        .log-area { flex-grow: 1; border: 1px solid #333; margin-top: 20px; overflow-y: auto; font-size: 12px; padding: 10px; color: #aaa; z-index: 10; }
        .win { color: #00ff41; font-weight: bold; } .loss { color: #ff003c; }
    </style>
</head>
<body>
    <div class="top-bar">
        <span>CORE_V4 // MANUAL_SCANNER_STATION</span>
        <span id="bal-display">BALANCE: $0.00</span>
    </div>

    <div class="market-watch" id="market-watch">
        </div>

    <div class="grid">
        <div class="sidebar">
            <h3>TRADING_CONTROLS</h3>
            <input type="password" id="token" placeholder="PASTE_API_TOKEN">
            <label>STAKE ($)</label>
            <input type="number" id="stake" value="0.35">
            <label>CONTRACT_TICKS</label>
            <input type="number" id="ticks" value="1">
            <label>CONTRACT_TYPE</label>
            <select id="contract-type">
                <option value="DIGITEVEN">MATCH EVEN</option>
                <option value="DIGITODD">MATCH ODD</option>
            </select>
            
            <button class="btn-run" onclick="executeManualTrade()">RUN_SINGLE_TRADE</button>
            <div id="session-pl" style="margin-top:20px; font-size:20px;">P/L: $0.00</div>
        </div>

        <div class="terminal">
            <div id="code-scroll"></div> <h2 style="z-index: 10;">LIVE_TRANSACTION_FEED</h2>
            <div id="tx-log" class="log-area"></div>
        </div>
    </div>

    <audio id="sonar" src="https://www.soundjay.com/buttons/beep-07.mp3" loop></audio>

    <script>
        let socket;
        let selectedMarket = "R_100";
        const markets = ["R_10", "R_25", "R_50", "R_75", "R_100"];

        // Initialize Market Cards
        function initMarkets() {
            const container = document.getElementById('market-watch');
            markets.forEach(m => {
                const card = document.createElement('div');
                card.className = `market-card ${m === selectedMarket ? 'selected' : ''}`;
                card.id = `card-${m}`;
                card.onclick = () => selectMarket(m);
                card.innerHTML = `<h4>${m}</h4><div class="percent-box" id="perc-${m}">0% / 0%</div>`;
                container.appendChild(card);
            });
        }

        function selectMarket(m) {
            selectedMarket = m;
            document.querySelectorAll('.market-card').forEach(c => c.classList.remove('selected'));
            document.getElementById(`card-${m}`).classList.add('selected');
            addLog(`SWTICHED_TO: ${m}`, true);
        }

        function startStreaming() {
            socket = new WebSocket("ws://localhost:8000/ws");
            document.getElementById('sonar').play(); // Start scanning sound
            
            socket.onopen = () => {
                socket.send(JSON.stringify({
                    action: 'init',
                    token: document.getElementById('token').value
                }));
            };

            socket.onmessage = (e) => {
                const data = JSON.parse(e.data);
                
                // Update Living Percentages
                if (data.markets) {
                    for (const [sym, val] of Object.entries(data.markets)) {
                        const el = document.getElementById(`perc-${sym}`);
                        if (el) el.innerText = `E:${val.e}% O:${val.o}%`;
                    }
                }

                if (data.balance) document.getElementById('bal-display').innerText = `BALANCE: $${data.balance}`;
                if (data.pl !== undefined) document.getElementById('session-pl').innerText = `P/L: $${data.pl}`;
                if (data.log) addLog(data.log, data.win);

                // Live code effect
                const scroller = document.getElementById('code-scroll');
                scroller.innerText += `\n ${Math.random().toString(36).substring(2, 15)} >> SCAN_SYNC_${selectedMarket}_${Date.now()}`;
                if (scroller.innerText.length > 2000) scroller.innerText = scroller.innerText.substring(500);
                scroller.scrollTop = scroller.scrollHeight;
            };
        }

        function executeManualTrade() {
            if (!socket) { startStreaming(); setTimeout(executeManualTrade, 1000); return; }
            
            const tradeData = {
                action: 'buy',
                symbol: selectedMarket,
                stake: document.getElementById('stake').value,
                ticks: document.getElementById('ticks').value,
                type: document.getElementById('contract-type').value
            };
            socket.send(JSON.stringify(tradeData));
        }

        function addLog(msg, isWin) {
            const log = document.getElementById('tx-log');
            const div = document.createElement('div');
            div.className = isWin ? 'win' : 'loss';
            div.innerHTML = `> [${new Date().toLocaleTimeString()}] ${msg}`;
            log.prepend(div);
        }

        initMarkets();
    </script>
</body>
</html>
"""

# --- THE BACKEND ---
@app.get("/")
async def get(): return HTMLResponse(html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    history = {s: [] for s in ["R_10", "R_25", "R_50", "R_75", "R_100"]}
    total_pl = 0
    
    try:
        # First message handles Auth
        auth_data = await websocket.receive_text()
        token = json.loads(auth_data)['token']
        
        async with websockets.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089") as deriv_ws:
            await deriv_ws.send(json.dumps({"authorize": token}))
            for s in history.keys():
                await deriv_ws.send(json.dumps({"ticks": s, "subscribe": 1}))

            # Background task to send percentages every second
            async def stream_ui():
                while True:
                    market_stats = {}
                    for s, ticks in history.items():
                        if ticks:
                            e_count = sum(1 for d in ticks if d % 2 == 0)
                            market_stats[s] = {"e": int((e_count/len(ticks))*100), "o": int(((len(ticks)-e_count)/len(ticks))*100)}
                    try:
                        await websocket.send_json({"markets": market_stats})
                    except: break
                    await asyncio.sleep(1)

            asyncio.create_task(stream_ui())

            async for message in deriv_ws:
                msg = json.loads(message)
                
                # Update tick history for all markets
                if "tick" in msg:
                    sym = msg['tick']['symbol']
                    digit = int(str(msg['tick']['quote'])[-1])
                    history[sym].append(digit)
                    if len(history[sym]) > 40: history[sym].pop(0)

                # Handle Trade Results
                if "proposal_open_contract" in msg:
                    contract = msg['proposal_open_contract']
                    if contract['is_sold']:
                        total_pl += float(contract['profit'])
                        await websocket.send_json({
                            "log": f"MANUAL_TRADE_CLOSED: {contract['profit']}",
                            "win": float(contract['profit']) > 0,
                            "pl": round(total_pl, 2)
                        })

                # Receive Manual Buy Commands from UI
                # (The websocket.receive loop would handle the 'buy' call here)

    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)