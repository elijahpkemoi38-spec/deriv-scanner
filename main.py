import json
import asyncio
import uvicorn
import websockets
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>DERIV_OS // SENTINEL_V1</title>
    <style>
        body { background: #020202; color: #00ff41; font-family: 'Courier New', monospace; margin: 0; overflow: hidden; }
        .top-bar { display: flex; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #00ff41; background: #000; }
        .market-watch { display: flex; justify-content: center; gap: 40px; padding: 20px; background: rgba(0, 255, 65, 0.05); border-bottom: 1px solid #111; }
        .market-card { min-width: 250px; border: 1px solid #333; padding: 15px; text-align: center; background: #050505; cursor: pointer; transition: 0.3s; }
        .market-card.selected { border-color: #00ff41; box-shadow: 0 0 15px #00ff41; background: #0a1a0a; }
        .balance-bar { height: 8px; background: #1a1a1a; display: flex; border-radius: 4px; overflow: hidden; margin: 10px 0; }
        .even-fill { background: #00ff41; transition: width 0.3s; }
        .odd-fill { background: #ff003c; transition: width 0.3s; }
        .grid { display: grid; grid-template-columns: 320px 1fr; height: 80vh; }
        .sidebar { border-right: 1px solid #333; padding: 20px; background: #050505; z-index: 20; }
        .terminal { position: relative; background: #000; overflow: hidden; display: flex; flex-direction: column; }
        #matrix-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; color: rgba(0, 255, 65, 0.1); font-size: 10px; line-height: 12px; pointer-events: none; overflow: hidden; padding: 10px; white-space: pre-wrap; }
        input, select { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; width: 90%; margin-bottom: 15px; font-family: inherit; }
        .btn-run { background: #00ff41; color: #000; font-weight: bold; padding: 15px; width: 100%; cursor: pointer; border: none; margin-bottom: 10px; }
        .btn-init { background: #222; color: #fff; border: 1px solid #444; }
        .log-area { flex-grow: 1; margin: 20px; z-index: 10; overflow-y: auto; background: rgba(0,0,0,0.8); border: 1px solid #111; padding: 10px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="top-bar">
        <span>[ SCANNER_ACTIVE ] SYNC_MODE: REAL_TIME</span>
        <span id="bal-display" style="color: #fff;">BALANCE: $WAITING...</span>
    </div>

    <div class="market-watch">
        <div class="market-card selected" id="card-R_100" onclick="selectMarket('R_100')">
            <div style="font-size: 11px; color: #888;">VOLATILITY 100 INDEX</div>
            <div id="perc-R_100" style="font-size: 22px; font-weight: bold;">E: --% | O: --%</div>
            <div class="balance-bar"><div id="bar-e-R_100" class="even-fill" style="width:50%"></div><div id="bar-o-R_100" class="odd-fill" style="width:50%"></div></div>
        </div>
        <div class="market-card" id="card-1S100" onclick="selectMarket('1S100')">
            <div style="font-size: 11px; color: #888;">VOLATILITY 100 (1S) INDEX</div>
            <div id="perc-1S100" style="font-size: 22px; font-weight: bold;">E: --% | O: --%</div>
            <div class="balance-bar"><div id="bar-e-1S100" class="even-fill" style="width:50%"></div><div id="bar-o-1S100" class="odd-fill" style="width:50%"></div></div>
        </div>
    </div>

    <div class="grid">
        <div class="sidebar">
            <input type="password" id="token" placeholder="API_TOKEN_KEY">
            <button class="btn-run btn-init" id="init-btn" onclick="connectSystem()">CONNECT_SYSTEM</button>
            <hr border="1" color="#222" style="margin: 20px 0;">
            <label style="font-size: 10px;">STAKE_AMOUNT</label>
            <input type="number" id="stake" value="0.35" step="0.01">
            <label style="font-size: 10px;">PREDICTION_TYPE</label>
            <select id="contract_type">
                <option value="DIGITEVEN">DIGIT_EVEN</option>
                <option value="DIGITODD">DIGIT_ODD</option>
            </select>
            <button class="btn-run" onclick="sendTrade()">EXECUTE_SINGLE_RUN</button>
        </div>
        <div class="terminal">
            <div id="matrix-bg"></div>
            <div id="tx-log" class="log-area"></div>
        </div>
    </div>

    <audio id="sonar" src="https://assets.mixkit.co/active_storage/sfx/2861/2861-preview.mp3"></audio>

    <script>
        let ws;
        let selectedMarket = "R_100";
        const sonar = document.getElementById('sonar');

        function selectMarket(sym) {
            selectedMarket = sym;
            document.querySelectorAll('.market-card').forEach(c => c.classList.remove('selected'));
            document.getElementById(`card-${sym}`).classList.add('selected');
        }

        function connectSystem() {
            const token = document.getElementById('token').value;
            if(!token) return alert("Enter Token!");
            
            const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            ws = new WebSocket(protocol + window.location.host + "/ws");

            ws.onopen = () => {
                ws.send(JSON.stringify({action: 'init', token: token}));
                document.getElementById('init-btn').innerText = "SYSTEM_ONLINE";
                document.getElementById('init-btn').style.background = "#004411";
            };

            ws.onmessage = (e) => {
                const data = JSON.parse(e.data);
                if (data.balance) document.getElementById('bal-display').innerText = `BALANCE: $${data.balance}`;
                if (data.markets) {
                    sonar.play(); // Play sonar beep on every packet update
                    for (const [sym, val] of Object.entries(data.markets)) {
                        document.getElementById(`perc-${sym}`).innerText = `E: ${val.e}% | O: ${val.o}%`;
                        document.getElementById(`bar-e-${sym}`).style.width = val.e + "%";
                        document.getElementById(`bar-o-${sym}`).style.width = val.o + "%";
                        updateMatrix(sym, val.e, val.o);
                    }
                }
                if (data.log) log(data.log, data.win ? "#00ff41" : "#ff003c");
            };
        }

        function updateMatrix(sym, e, o) {
            const m = document.getElementById('matrix-bg');
            const codeLine = `HEX_DATA_${sym}_SIG: [${Math.random().toString(16).slice(2,8)}] >> E:${e}% O:${o}% \\n`;
            m.innerText = codeLine + m.innerText;
            if(m.innerText.length > 2000) m.innerText = m.innerText.substring(0, 1500);
        }

        function sendTrade() {
            if(!ws || ws.readyState !== 1) return alert("Connect First!");
            ws.send(JSON.stringify({
                action: 'trade',
                symbol: selectedMarket,
                stake: document.getElementById('stake').value,
                type: document.getElementById('contract_type').value
            }));
        }

        function log(msg, color) {
            const l = document.getElementById('tx-log');
            l.innerHTML = `<div style="color:${color}">> [${new Date().toLocaleTimeString()}] ${msg}</div>` + l.innerHTML;
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get(): return HTMLResponse(html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    history = {"R_100": [], "1S100": []}
    
    try:
        init_data = await websocket.receive_json()
        token = init_data.get('token')
        
        async with websockets.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089") as deriv_ws:
            await deriv_ws.send(json.dumps({"authorize": token}))
            await deriv_ws.send(json.dumps({"ticks": "R_100", "subscribe": 1}))
            await deriv_ws.send(json.dumps({"ticks": "1S100", "subscribe": 1}))

            async def listen_deriv():
                async for message in deriv_ws:
                    msg = json.loads(message)
                    if "authorize" in msg:
                        await websocket.send_json({"balance": msg['authorize']['balance']})
                    if "tick" in msg:
                        sym = msg['tick']['symbol']
                        digit = int(str(msg['tick']['quote'])[-1])
                        history[sym].append(digit)
                        if len(history[sym]) > 50: history[sym].pop(0)
                        e_perc = int((sum(1 for d in history[sym] if d % 2 == 0)/len(history[sym]))*100)
                        await websocket.send_json({"markets": {sym: {"e": e_perc, "o": 100 - e_perc}}})
                    if "buy" in msg:
                        await websocket.send_json({"log": f"MANUAL_TRADE_EXECUTED: {msg['buy']['contract_id']}", "win": True})
                    if "error" in msg:
                        await websocket.send_json({"log": f"FAILED: {msg['error']['message']}", "win": False})

            async def listen_frontend():
                while True:
                    data = await websocket.receive_json()
                    if data.get('action') == 'trade':
                        await deriv_ws.send(json.dumps({
                            "buy": 1, "price": float(data['stake']),
                            "parameters": {
                                "amount": float(data['stake']), "basis": "stake",
                                "contract_type": data['type'], "currency": "USD",
                                "duration": 1, "duration_unit": "t", "symbol": data['symbol']
                            }
                        }))

            await asyncio.gather(listen_deriv(), listen_frontend())
    except Exception: pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
