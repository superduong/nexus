from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class MarketOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    exchange: str
    symbol: str
    base: str
    quote: str
    market_type: str
    is_active: bool
    min_qty: Decimal
    tick_size: Decimal
    created_at: datetime
    updated_at: datetime

    @field_serializer("min_qty", "tick_size")
    def dec(self, v: Decimal):
        return float(v)


class TickerOut(BaseModel):
    model_config = {"from_attributes": True}

    symbol: str
    exchange: str
    price: Decimal
    bid: Decimal | None
    ask: Decimal | None
    volume_24h: Decimal | None
    change_24h: Decimal | None
    high_24h: Decimal | None
    low_24h: Decimal | None
    timestamp: datetime

    @field_serializer("price", "bid", "ask", "volume_24h", "change_24h", "high_24h", "low_24h")
    def dec_opt(self, v: Decimal | None):
        return float(v) if v is not None else None
