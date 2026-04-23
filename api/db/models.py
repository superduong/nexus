from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "accounts_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    password: Mapped[str] = mapped_column(String(128))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    username: Mapped[str] = mapped_column(String(150), unique=True)
    first_name: Mapped[str] = mapped_column(String(150), default="")
    last_name: Mapped[str] = mapped_column(String(150), default="")
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    date_joined: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    avatar: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ExchangeAPIKey(Base):
    __tablename__ = "accounts_exchangeapikey"
    __table_args__ = (UniqueConstraint("user_id", "exchange", "label"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("accounts_user.id", ondelete="CASCADE"))
    exchange: Mapped[str] = mapped_column(String(20))
    label: Mapped[str] = mapped_column(String(100), default="")
    api_key: Mapped[str] = mapped_column(String(256))
    api_secret: Mapped[str] = mapped_column(String(256))
    api_password: Mapped[str] = mapped_column(String(256), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    testnet: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Market(Base):
    __tablename__ = "markets_market"
    __table_args__ = (
        UniqueConstraint("exchange", "symbol", "market_type", name="markets_market_exchange_symbol_market_type_uniq"),
        Index("markets_mar_exchang_3370be_idx", "exchange", "symbol"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(20))
    symbol: Mapped[str] = mapped_column(String(30))
    base: Mapped[str] = mapped_column(String(15))
    quote: Mapped[str] = mapped_column(String(15))
    market_type: Mapped[str] = mapped_column(String(10), default="spot")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    min_qty: Mapped[float] = mapped_column(Numeric(20, 10), default=0)
    tick_size: Mapped[float] = mapped_column(Numeric(20, 10), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    tickers: Mapped[list["Ticker"]] = relationship(back_populates="market")


class Ticker(Base):
    __tablename__ = "markets_ticker"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets_market.id", ondelete="CASCADE"))
    price: Mapped[float] = mapped_column(Numeric(25, 10))
    bid: Mapped[float | None] = mapped_column(Numeric(25, 10), nullable=True)
    ask: Mapped[float | None] = mapped_column(Numeric(25, 10), nullable=True)
    volume_24h: Mapped[float | None] = mapped_column(Numeric(30, 10), nullable=True)
    change_24h: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    high_24h: Mapped[float | None] = mapped_column(Numeric(25, 10), nullable=True)
    low_24h: Mapped[float | None] = mapped_column(Numeric(25, 10), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    market: Mapped["Market"] = relationship(back_populates="tickers")


class Order(Base):
    __tablename__ = "orders_order"
    __table_args__ = (
        Index("orders_orde_user_id_c30c7b_idx", "user_id", "symbol", "status"),
        Index("orders_orde_created_0e92de_idx", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("accounts_user.id", ondelete="CASCADE"))
    exchange: Mapped[str] = mapped_column(String(20))
    exchange_id: Mapped[str] = mapped_column(String(128), default="")
    symbol: Mapped[str] = mapped_column(String(30))
    side: Mapped[str] = mapped_column(String(5))
    order_type: Mapped[str] = mapped_column(String(15))
    status: Mapped[str] = mapped_column(String(15), default="open")
    price: Mapped[float | None] = mapped_column(Numeric(25, 10), nullable=True)
    stop_price: Mapped[float | None] = mapped_column(Numeric(25, 10), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(20, 10))
    filled_qty: Mapped[float] = mapped_column(Numeric(20, 10), default=0)
    avg_price: Mapped[float | None] = mapped_column(Numeric(25, 10), nullable=True)
    total: Mapped[float | None] = mapped_column(Numeric(25, 10), nullable=True)
    fee: Mapped[float | None] = mapped_column(Numeric(20, 10), nullable=True)
    fee_currency: Mapped[str] = mapped_column(String(15), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    trades: Mapped[list["Trade"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class Trade(Base):
    __tablename__ = "orders_trade"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders_order.id", ondelete="CASCADE"))
    exchange_trade_id: Mapped[str] = mapped_column(String(128), default="")
    price: Mapped[float] = mapped_column(Numeric(25, 10))
    quantity: Mapped[float] = mapped_column(Numeric(20, 10))
    fee: Mapped[float | None] = mapped_column(Numeric(20, 10), nullable=True)
    fee_currency: Mapped[str] = mapped_column(String(15), default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    order: Mapped["Order"] = relationship(back_populates="trades")


class Balance(Base):
    __tablename__ = "portfolio_balance"
    __table_args__ = (UniqueConstraint("user_id", "exchange", "currency"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("accounts_user.id", ondelete="CASCADE"))
    exchange: Mapped[str] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(15))
    total: Mapped[float] = mapped_column(Numeric(30, 10), default=0)
    available: Mapped[float] = mapped_column(Numeric(30, 10), default=0)
    locked: Mapped[float] = mapped_column(Numeric(30, 10), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Position(Base):
    __tablename__ = "portfolio_position"
    __table_args__ = (Index("portfolio_p_user_id_e851c0_idx", "user_id", "exchange", "symbol", "is_open"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("accounts_user.id", ondelete="CASCADE"))
    exchange: Mapped[str] = mapped_column(String(20))
    symbol: Mapped[str] = mapped_column(String(30))
    side: Mapped[str] = mapped_column(String(5))
    size: Mapped[float] = mapped_column(Numeric(20, 10))
    entry_price: Mapped[float] = mapped_column(Numeric(25, 10))
    mark_price: Mapped[float | None] = mapped_column(Numeric(25, 10), nullable=True)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric(25, 10), default=0)
    leverage: Mapped[int] = mapped_column(Integer, default=1)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
