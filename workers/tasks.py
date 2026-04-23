from datetime import datetime, timezone

from sqlalchemy import select

from api.db.models import Market, Order, Ticker
from api.db.session import SessionLocal
from api.services.exchange import MarketService, get_exchange
from api.services.order import OrderService
from workers.celery_app import app


@app.task
def sync_all_tickers():
    db = SessionLocal()
    try:
        exchanges = list(db.scalars(select(Market.exchange).distinct()))
        for exchange_name in exchanges:
            try:
                tickers = MarketService.get_tickers(exchange_name)
                for symbol, data in tickers.items():
                    market = db.scalar(
                        select(Market).where(Market.exchange == exchange_name, Market.symbol == symbol)
                    )
                    if not market:
                        continue
                    row = db.scalar(
                        select(Ticker).where(Ticker.market_id == market.id).order_by(Ticker.id.desc()).limit(1)
                    )
                    vals = {
                        "price": data.get("last", 0) or 0,
                        "bid": data.get("bid"),
                        "ask": data.get("ask"),
                        "volume_24h": data.get("quoteVolume"),
                        "change_24h": data.get("percentage"),
                        "high_24h": data.get("high"),
                        "low_24h": data.get("low"),
                    }
                    ts = datetime.now(timezone.utc)
                    if row:
                        for k, v in vals.items():
                            setattr(row, k, v)
                        row.timestamp = ts
                    else:
                        db.add(
                            Ticker(
                                market_id=market.id,
                                timestamp=ts,
                                **vals,
                            )
                        )
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"[sync_tickers] {exchange_name}: {e}")
    finally:
        db.close()


@app.task
def sync_open_orders():
    db = SessionLocal()
    try:
        open_orders = db.scalars(select(Order).where(Order.status.in_(["open", "partial"]))).all()
        for order in open_orders:
            try:
                OrderService.sync_order(db, order)
            except Exception as e:
                print(f"[sync_orders] order {order.id}: {e}")
    finally:
        db.close()


@app.task
def sync_markets():
    db = SessionLocal()
    try:
        for exchange_name in ["binance", "okx"]:
            try:
                ex = get_exchange(exchange_name)
                markets = ex.load_markets()
                now = datetime.now(timezone.utc)
                for symbol, info in markets.items():
                    if "/USDT" not in symbol:
                        continue
                    limits = info.get("limits", {}) or {}
                    amount_min = (limits.get("amount") or {}).get("min") or 0
                    prec = info.get("precision", {}) or {}
                    price_prec = prec.get("price") or 0
                    row = db.scalar(
                        select(Market).where(
                            Market.exchange == exchange_name,
                            Market.symbol == symbol,
                            Market.market_type == "spot",
                        )
                    )
                    defaults = {
                        "base": info.get("base", "") or "",
                        "quote": info.get("quote", "") or "",
                        "is_active": info.get("active", True),
                        "min_qty": amount_min or 0,
                        "tick_size": price_prec or 0,
                        "updated_at": now,
                    }
                    if row:
                        for k, v in defaults.items():
                            setattr(row, k, v)
                    else:
                        db.add(
                            Market(
                                exchange=exchange_name,
                                symbol=symbol,
                                market_type="spot",
                                created_at=now,
                                **defaults,
                            )
                        )
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"[sync_markets] {exchange_name}: {e}")
    finally:
        db.close()
