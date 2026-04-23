from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class BalanceOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    exchange: str
    currency: str
    total: Decimal
    available: Decimal
    locked: Decimal
    updated_at: datetime

    @field_serializer("total", "available", "locked")
    def dec(self, v: Decimal):
        return float(v)


class PositionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    exchange: str
    symbol: str
    side: str
    size: Decimal
    entry_price: Decimal
    mark_price: Decimal | None
    unrealized_pnl: Decimal
    leverage: int
    is_open: bool
    opened_at: datetime
    updated_at: datetime

    @field_serializer("size", "entry_price", "mark_price", "unrealized_pnl")
    def dec(self, v: Decimal | None):
        return float(v) if v is not None else None
