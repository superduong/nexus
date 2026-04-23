from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, field_serializer


class TradeOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    order_id: int
    exchange_trade_id: str
    price: Decimal
    quantity: Decimal
    fee: Decimal | None
    fee_currency: str
    timestamp: datetime
    created_at: datetime

    @field_serializer("price", "quantity", "fee")
    def dec(self, v: Decimal | None):
        return float(v) if v is not None else None


class OrderOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    exchange: str
    exchange_id: str
    symbol: str
    side: str
    order_type: str
    status: str
    price: Decimal | None
    stop_price: Decimal | None
    quantity: Decimal
    filled_qty: Decimal
    avg_price: Decimal | None
    total: Decimal | None
    fee: Decimal | None
    fee_currency: str
    note: str
    created_at: datetime
    updated_at: datetime
    trades: list[TradeOut] = []

    @field_serializer(
        "price",
        "stop_price",
        "quantity",
        "filled_qty",
        "avg_price",
        "total",
        "fee",
    )
    def dec(self, v: Decimal | None):
        return float(v) if v is not None else None


class PlaceOrderIn(BaseModel):
    exchange: str
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["limit", "market", "stop_limit", "stop_market"]
    quantity: Decimal
    price: Decimal | None = None
    stop_price: Decimal | None = None


class PaginatedOrders(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[OrderOut]
