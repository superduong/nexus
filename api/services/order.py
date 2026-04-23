from sqlalchemy.orm import Session, selectinload

from api.db.models import Order
from api.services.exchange import get_exchange


class OrderService:
    @staticmethod
    def place_order(db: Session, user_id: int, data: dict) -> Order:
        ex = get_exchange(data["exchange"])
        symbol = data["symbol"]
        side = data["side"]
        order_type = data["order_type"]
        quantity = float(data["quantity"])
        price = float(data["price"]) if data.get("price") is not None else None

        if order_type == "market":
            raw = ex.create_order(symbol, "market", side, quantity)
        elif order_type == "limit":
            raw = ex.create_order(symbol, "limit", side, quantity, price)
        else:
            raw = ex.create_order(symbol, "limit", side, quantity, price)

        order = Order(
            user_id=user_id,
            exchange=data["exchange"],
            exchange_id=raw.get("id", "") or "",
            symbol=symbol,
            side=side,
            order_type=order_type,
            status=raw.get("status", "open") or "open",
            price=price,
            quantity=quantity,
            filled_qty=raw.get("filled", 0) or 0,
            avg_price=raw.get("average"),
            total=raw.get("cost"),
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def cancel_order(db: Session, user_id: int, order_id: int) -> Order:
        order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).one_or_none()
        if not order:
            raise ValueError("Order not found")
        ex = get_exchange(order.exchange)
        ex.cancel_order(order.exchange_id, order.symbol)
        order.status = "cancelled"
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def sync_order(db: Session, order: Order) -> Order:
        ex = get_exchange(order.exchange)
        raw = ex.fetch_order(order.exchange_id, order.symbol)
        order.status = raw.get("status", order.status)
        order.filled_qty = raw.get("filled", order.filled_qty)
        order.avg_price = raw.get("average", order.avg_price)
        order.total = raw.get("cost", order.total)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def get_order_with_trades(db: Session, order_id: int, user_id: int) -> Order | None:
        return (
            db.query(Order)
            .options(selectinload(Order.trades))
            .filter(Order.id == order_id, Order.user_id == user_id)
            .first()
        )
