import asyncio
import random
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.core.config import get_settings
from api.routers import auth, markets, orders, portfolio

BASE_DIR = Path(__file__).resolve().parent.parent
settings = get_settings()
app = FastAPI(title="Nexus API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(markets.router, prefix="/api/markets", tags=["markets"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates" / "terminal"))


async def _stream_tickers(websocket: WebSocket):
    base_prices = {
        "BTC/USDT": 67800.0,
        "ETH/USDT": 3400.0,
        "SOL/USDT": 182.0,
        "BNB/USDT": 588.0,
        "DOGE/USDT": 0.178,
        "ADA/USDT": 0.481,
    }
    while True:
        tickers = []
        for symbol, base in base_prices.items():
            delta = (random.random() - 0.495) * base * 0.0008
            base_prices[symbol] = max(0.0001, base + delta)
            tickers.append(
                {
                    "symbol": symbol,
                    "price": round(base_prices[symbol], 6),
                    "bid": round(base_prices[symbol] * 0.9998, 6),
                    "ask": round(base_prices[symbol] * 1.0002, 6),
                    "change": round(random.uniform(-5, 5), 2),
                    "volume": round(random.uniform(1e6, 1e9), 2),
                    "ts": int(time.time() * 1000),
                }
            )
        await websocket.send_json({"type": "tickers", "data": tickers})
        await asyncio.sleep(1)


@app.websocket("/ws/ticker/{exchange}/")
async def ws_ticker(websocket: WebSocket, exchange: str):
    await websocket.accept()
    try:
        await _stream_tickers(websocket)
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass


@app.websocket("/ws/orderbook/{exchange}/{symbol}/")
async def ws_orderbook(websocket: WebSocket, exchange: str, symbol: str):
    sym = symbol.replace("_", "/")
    await websocket.accept()
    base = 67800.0
    try:
        while True:
            spread = base * 0.0002
            asks = sorted(
                [
                    [
                        round(base + spread / 2 + i * base * 0.0001 + random.random() * 5, 2),
                        round(random.uniform(0.01, 3.0), 4),
                    ]
                    for i in range(15)
                ]
            )
            bids = sorted(
                [
                    [
                        round(base - spread / 2 - i * base * 0.0001 - random.random() * 5, 2),
                        round(random.uniform(0.01, 3.0), 4),
                    ]
                    for i in range(15)
                ],
                reverse=True,
            )
            base += (random.random() - 0.499) * base * 0.0003
            await websocket.send_json(
                {"type": "orderbook", "symbol": sym, "bids": bids, "asks": asks, "ts": int(time.time() * 1000)}
            )
            await asyncio.sleep(0.5)
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass


@app.websocket("/ws/trades/{exchange}/{symbol}/")
async def ws_trades(websocket: WebSocket, exchange: str, symbol: str):
    sym = symbol.replace("_", "/")
    await websocket.accept()
    base = 67800.0
    try:
        while True:
            count = random.randint(1, 5)
            trades = []
            for _ in range(count):
                price = base + (random.random() - 0.5) * 50
                trades.append(
                    {
                        "price": round(price, 2),
                        "qty": round(random.uniform(0.001, 2.0), 4),
                        "side": "buy" if random.random() > 0.48 else "sell",
                        "ts": int(time.time() * 1000),
                    }
                )
            await websocket.send_json({"type": "trades", "data": trades})
            await asyncio.sleep(0.8)
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass


@app.get("/api/health/")
def health():
    return {"status": "ok"}


@app.get("/login/")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/")
def terminal_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/{full_path:path}")
def terminal_spa(request: Request, full_path: str):
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("index.html", {"request": request})
