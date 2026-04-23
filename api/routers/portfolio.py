from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.core.deps import get_current_user
from api.db.models import Balance, Order, Position, User
from api.db.session import get_db
from api.schemas.portfolio import BalanceOut, PositionOut
from api.services.exchange import get_exchange

router = APIRouter()


@router.get("/balance/", response_model=list[BalanceOut])
def balance(
    exchange: str = "binance",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        ex = get_exchange(exchange)
        raw = ex.fetch_balance()
        out: list[Balance] = []
        for currency, info in raw.get("total", {}).items():
            if info and float(info) > 0:
                total = raw["total"].get(currency, 0) or 0
                free = raw["free"].get(currency, 0) or 0
                used = raw["used"].get(currency, 0) or 0
                row = db.scalar(
                    select(Balance).where(
                        Balance.user_id == user.id,
                        Balance.exchange == exchange,
                        Balance.currency == currency,
                    )
                )
                now = datetime.now(timezone.utc)
                if row:
                    row.total = float(total)
                    row.available = float(free)
                    row.locked = float(used)
                    row.updated_at = now
                else:
                    row = Balance(
                        user_id=user.id,
                        exchange=exchange,
                        currency=currency,
                        total=float(total),
                        available=float(free),
                        locked=float(used),
                        updated_at=now,
                    )
                    db.add(row)
                out.append(row)
        db.commit()
        for r in out:
            db.refresh(r)
        return out
    except Exception:
        db.rollback()
        rows = db.scalars(select(Balance).where(Balance.user_id == user.id, Balance.exchange == exchange)).all()
        return list(rows)


@router.get("/positions/", response_model=list[PositionOut])
def positions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Position).where(Position.user_id == user.id, Position.is_open.is_(True))).all()
    return list(rows)


@router.get("/summary/")
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_orders = db.scalar(select(func.count(Order.id)).where(Order.user_id == user.id)) or 0
    filled_orders = (
        db.scalar(select(func.count(Order.id)).where(Order.user_id == user.id, Order.status == "filled")) or 0
    )
    open_positions = (
        db.scalar(
            select(func.count(Position.id)).where(Position.user_id == user.id, Position.is_open.is_(True))
        )
        or 0
    )
    return {
        "total_orders": total_orders,
        "filled_orders": filled_orders,
        "open_positions": open_positions,
    }
