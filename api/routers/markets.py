from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from api.core.deps import get_current_user
from api.core.redis_client import cache_get_json, cache_set_json
from api.db.models import Market, Ticker, User
from api.db.session import get_db
from api.schemas.markets import MarketOut, TickerOut
from api.services.exchange import MarketService

router = APIRouter()


@router.get("/", response_model=list[MarketOut])
def list_markets(
    exchange: str | None = None,
    type: str = Query("spot", alias="type"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Market).where(Market.is_active.is_(True), Market.market_type == type)
    if exchange:
        q = q.where(Market.exchange == exchange)
    return list(db.scalars(q).all())


@router.get("/tickers/", response_model=list[TickerOut])
def list_tickers(
    exchange: str = "binance",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cache_key = f"tickers:{exchange}"
    cached = cache_get_json(cache_key)
    if cached:
        return [TickerOut(**row) for row in cached]
    rows = db.scalars(
        select(Ticker).options(joinedload(Ticker.market)).join(Market).where(Market.exchange == exchange)
    ).all()
    out = [
        TickerOut(
            symbol=t.market.symbol,
            exchange=t.market.exchange,
            price=t.price,
            bid=t.bid,
            ask=t.ask,
            volume_24h=t.volume_24h,
            change_24h=t.change_24h,
            high_24h=t.high_24h,
            low_24h=t.low_24h,
            timestamp=t.timestamp,
        )
        for t in rows
    ]
    cache_set_json(cache_key, [m.model_dump(mode="json") for m in out], 5)
    return out


@router.get("/{symbol}/ohlcv/")
def ohlcv(
    symbol: str,
    exchange: str = "binance",
    tf: str = "1h",
    limit: int = 200,
    _: User = Depends(get_current_user),
):
    cache_key = f"ohlcv:{exchange}:{symbol}:{tf}"
    cached = cache_get_json(cache_key)
    if cached:
        return cached
    data = MarketService.get_ohlcv(exchange, symbol, tf, limit)
    cache_set_json(cache_key, data, 30)
    return data


@router.get("/{symbol}/book/")
def orderbook(
    symbol: str,
    exchange: str = "binance",
    limit: int = 20,
    _: User = Depends(get_current_user),
):
    return MarketService.get_orderbook(exchange, symbol, limit)
