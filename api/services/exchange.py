import ccxt

from api.core.config import get_settings


def get_exchange(name: str):
    s = get_settings()
    if name == "binance":
        return ccxt.binance(
            {"apiKey": s.binance_api_key, "secret": s.binance_secret, "enableRateLimit": True}
        )
    if name == "okx":
        return ccxt.okx(
            {
                "apiKey": s.okx_api_key,
                "secret": s.okx_secret,
                "password": s.okx_password,
                "enableRateLimit": True,
            }
        )
    raise ValueError(f"Exchange {name} not supported")


class MarketService:
    @staticmethod
    def get_ohlcv(exchange_name: str, symbol: str, timeframe: str = "1h", limit: int = 200):
        ex = get_exchange(exchange_name)
        raw = ex.fetch_ohlcv(symbol, timeframe, limit=limit)
        return [{"t": c[0], "o": c[1], "h": c[2], "l": c[3], "c": c[4], "v": c[5]} for c in raw]

    @staticmethod
    def get_orderbook(exchange_name: str, symbol: str, limit: int = 20):
        ex = get_exchange(exchange_name)
        ob = ex.fetch_order_book(symbol, limit)
        return {"bids": ob["bids"], "asks": ob["asks"], "timestamp": ob.get("timestamp")}

    @staticmethod
    def get_tickers(exchange_name: str):
        ex = get_exchange(exchange_name)
        return ex.fetch_tickers()
