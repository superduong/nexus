from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from api.core.deps import get_current_user
from api.db.models import Order, User
from api.db.session import get_db
from api.schemas.orders import OrderOut, PaginatedOrders, PlaceOrderIn
from api.services.order import OrderService

router = APIRouter()
PAGE_SIZE = 50


def _order_filters(user_id: int, st: str | None, sym: str | None):
    conds = [Order.user_id == user_id]
    if st:
        conds.append(Order.status == st)
    if sym:
        conds.append(Order.symbol == sym)
    return conds


@router.get("/", response_model=PaginatedOrders)
def list_orders(
    request: Request,
    page: int = Query(1, ge=1),
    order_status: str | None = Query(None, alias="status"),
    symbol: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conds = _order_filters(user.id, order_status, symbol)
    total = db.scalar(select(func.count(Order.id)).where(*conds)) or 0
    offset = (page - 1) * PAGE_SIZE
    rows = db.scalars(
        select(Order)
        .options(selectinload(Order.trades))
        .where(*conds)
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(PAGE_SIZE)
    ).all()

    base = str(request.url).split("?")[0]
    qparams: dict[str, str] = {}
    if order_status:
        qparams["status"] = order_status
    if symbol:
        qparams["symbol"] = symbol

    def page_url(p: int) -> str:
        qp = {**qparams, "page": str(p)}
        return f"{base}?{urlencode(qp)}"

    next_url = page_url(page + 1) if offset + PAGE_SIZE < total else None
    prev_url = page_url(page - 1) if page > 1 else None

    return PaginatedOrders(
        count=total,
        next=next_url,
        previous=prev_url,
        results=[OrderOut.model_validate(r) for r in rows],
    )


@router.post("/place/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def place_order(
    body: PlaceOrderIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        order = OrderService.place_order(db, user.id, body.model_dump())
        order = OrderService.get_order_with_trades(db, order.id, user.id)
        return OrderOut.model_validate(order)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{pk}/cancel/", response_model=OrderOut)
def cancel_order(pk: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        order = OrderService.cancel_order(db, user.id, pk)
        order = OrderService.get_order_with_trades(db, order.id, user.id)
        return OrderOut.model_validate(order)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{pk}/", response_model=OrderOut)
def order_detail(pk: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = OrderService.get_order_with_trades(db, pk, user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return OrderOut.model_validate(order)
