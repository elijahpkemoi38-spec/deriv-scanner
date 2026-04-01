import json
import asyncio
import uvicorn
import websockets
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- THE ENHANCED UI ---
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>DERIV_OS // V100_SPECIALIST</title>
    <style>
        body { background: #020202; color: #00ff41; font-family: 'Courier New', monospace; margin: 0; overflow: hidden; }
        .top-bar { display: flex; justify-content: space-between; padding: 10px 20px; border-bottom: 1px solid #00ff41; background: #000; z-index: 100; position: relative; }
        
        /* MARKET DISPLAY - SINGLE LINE */
        .market-watch { display: flex; justify-content: center; gap: 40px; padding: 20px; background: rgba(0, 255, 65, 0.02); border-bottom: 1px solid #111; }
        .market-card { min-width: 250px; border: 1px solid #333; padding: 15px; text-align: center; background: #050505; position: relative; }
        .market-card.selected { border-color: #00ff41; box-shadow: 0 0 10px rgba(0, 255, 65, 0.2); }
        .market-title { font-size: 14px; color: #888; margin-bottom: 10px; }
        
        /* PROGRESS BAR EFFECT */
        .balance-bar { height: 10px; background: #1a1a1a; display: flex; border-radius: 5px; overflow: hidden; margin: 10px 0; }
        .even-fill { background: #00ff41; transition: width 0.3s; }
        .odd-fill { background: #ff003c; transition: width 0.3s; }
        
        .grid { display: grid; grid-template-columns: 350px 1fr; height: 75vh; }
        .sidebar { border-right: 1px solid #333; padding: 20px; background: #050505; }
        .terminal { position: relative; background: #000; overflow: hidden; padding: 20px; display: flex; flex-direction: column; }
        
        #code-scroll { position: absolute; top: 0; left: 0; width: 100%; height: 100%; color: rgba(0, 255, 65, 0.07); font-size: 11px; pointer-events: none; white-space: pre; overflow: hidden; }
        input { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; width: 90%; margin-bottom: 15px; }
        .btn-run { background: #00ff41; color: #000; font-weight: bold; padding: 15px; width: 100%; cursor: pointer; border: none; margin-bottom: 10px; }
        .log-area { flex-grow: 1; border: 1px solid #111; margin-top: 20px; overflow-y: auto; font-size: 12px; padding: 10px; z-index: 10; }
    </style>
</head>
<body>
    <div class="top-bar">
        <span>VOLATILITY_100_SCANNER // PRO_V1</span>
        <span id="bal-display" style="color: #fff; font-weight: bold;">BALANCE: $WAITING...</span>
    </div>

    <div class="market-watch">
        <div class="market-card selected" id="card-R_100">
            <div class="market-title">VOLATILITY 100 INDEX</div>
            <div id="perc-R_100" style="font-size: 20px;">E: 50% | O: 50%</div>
            <div class="balance-bar"><div id="bar-e-R_100" class="even-fill" style="width:50%"></div><div id="bar-o-R_100" class="odd-fill" style="width:50%"></div></div>
        </div>
        <div class="market-card" id="card-1S100">
            <div class="market-title">VOLATILITY 100 (1S) INDEX</div>
            <div id="perc-1S100" style="font-size: 20px;">E: 50% | O: 50%</div>
            <div class="balance-bar"><div id="bar-e-1S100" class="even-fill" style="width:50%"></div><div id="bar-o-1S100" class="odd-fill" style="width:50%"></div></div>
        </div>
    </div>

    <div class="grid">
        <div class="sidebar">
            <input type="password" id="token" placeholder="ENTER_DERIV_API_TOKEN">
            <button class="btn-run" style="background: #444; color: #fff;" onclick="startStreaming()">INITIALIZE_SYSTEM</button>
            <hr border="1" color="#222">
            <label>STAKE</label><input type="number" id="stake" value="0.35">
            <button class="btn-run" onclick="executeTrade()">EXECUTE_TRADE</button>
            <div id="session-pl">P/L: $0.00</div>
        </div>
        <div class="terminal">
            <div id="code-scroll"></div>
            <div id="tx-log" class="log-area"></div>
        </div>
    </div>

    <audio id="sonar" src="https://www.soundjay.com/buttons/beep-07.mp3" loop></audio>

    <script>
        let socket;
        function startStreaming() {
            const token = document.getElementById('token').value;
            if(!token) return alert("Paste Token First");
            
            socket = new WebSocket("ws://" + window.location.host + "/ws");
            document.getElementById('sonar').play();
            
            socket.onopen = () => socket.send(JSON.stringify({action: 'init', token: token}));
            
            socket.onmessage = (e) => {
                const data = JSON.parse(e.data);
                if (data.markets) {
                    for (const [sym, val] of Object.entries(data.markets)) {
                        const cleanSym = sym.replace('R_', 'R_').replace('1S', '1S');
                        document.getElementById(`perc-${sym}`).innerText = `EVEN: ${val.e}% | ODD: ${val.o}%`;
                        document.getElementById(`bar-e-${sym}`).style.width = val.e + "%";
                        document.getElementById(`bar-o-${sym}`).style.width = val.o + "%";
                    }
                }
                if (data.balance) document.getElementById('bal-display').innerText = `BALANCE: $${data.balance}`;
                if (data.log) {
                    const log = document.getElementById('tx-log');
                    log.innerHTML = `<div style="color:${data.win ? '#00ff41' : '#ff003c'}">> ${data.log}</div>` + log.innerHTML;
                }
                
                // Coding Movement Effect
                const scroller = document.getElementById('code-scroll');
                scroller.innerText += `\\n AUTH_ID_${Math.random().toString(36).substr(2,9)} >> PACKET_RECEIVE_STREAM_SUCCESS`;
                if(scroller.innerText.length > 1500) scroller.innerText = scroller.innerText.substring(500);
                scroller.scrollTop = scroller.scrollHeight;
            };
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
        raw_auth = await websocket.receive_text()
        token = json.loads(raw_auth)['token']
        
        async with websockets.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089") as deriv_ws:
            # 1. Authorize & Get Balance
            await deriv_ws.send(json.dumps({"authorize": token}))
            
            # 2. Subscribe to the two Volatility indices
            await deriv_ws.send(json.dumps({"ticks": "R_100", "subscribe": 1}))
            await deriv_ws.send(json.dumps({"ticks": "1S100", "subscribe": 1}))

            async for message in deriv_ws:
                msg = json.loads(message)
                
                # Update Balance Display
                if "authorize" in msg:
                    await websocket.send_json({"balance": msg['authorize']['balance']})

                # Process Ticks for Percentages
                if "tick" in msg:
                    sym = msg['tick']['symbol']
                    if sym in history:
                        digit = int(str(msg['tick']['quote'])[-1])
                        history[sym].append(digit)
                        if len(history[sym]) > 50: history[sym].pop(0)
                        
                        e_count = sum(1 for d in history[sym] if d % 2 == 0)
                        e_perc = int((e_count/len(history[sym]))*100)
                        
                        await websocket.send_json({
                            "markets": {
                                sym: {"e": e_perc, "o": 100 - e_perc}
                            }
                        })

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
