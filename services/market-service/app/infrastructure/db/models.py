from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String, Boolean, Numeric, BigInteger,
    Text, Date, ForeignKey, UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import TIMESTAMP

class Base(DeclarativeBase, AsyncAttrs):

    __abstract__ = True


class SecurityModel(Base):
    __tablename__ = "securities"

    ticker:     Mapped[str]           = mapped_column(String(20), primary_key=True)
    name:       Mapped[str]           = mapped_column(String(200), nullable=False)
    exchange:   Mapped[Optional[str]] = mapped_column(String(50))
    sector:     Mapped[Optional[str]] = mapped_column(String(100))
    is_active:  Mapped[bool]          = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime]      = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    price_bars: Mapped[list["PriceHistoryModel"]] = relationship(back_populates="security")
    dividends:  Mapped[list["DividendModel"]]     = relationship(back_populates="security")


class PriceHistoryModel(Base):
    __tablename__ = "price_history"

    time:   Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), primary_key=True)
    ticker: Mapped[str]           = mapped_column(String(20), ForeignKey("securities.ticker"), primary_key=True)
    open:   Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4))
    high:   Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4))
    low:    Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4))
    close:  Mapped[Decimal]           = mapped_column(Numeric(14, 4), nullable=False)
    volume: Mapped[Optional[int]]     = mapped_column(BigInteger)
    source: Mapped[Optional[str]]     = mapped_column(String(50))

    security: Mapped["SecurityModel"] = relationship(back_populates="price_bars")


class DividendModel(Base):
    __tablename__ = "dividends"
    __table_args__ = (
        UniqueConstraint("ticker", "ex_date", name="uq_dividends_ticker_exdate"),
    )

    id:       Mapped[int]            = mapped_column(primary_key=True, autoincrement=True)
    ticker:   Mapped[str]            = mapped_column(String(20), ForeignKey("securities.ticker"), nullable=False)
    ex_date:  Mapped[date]           = mapped_column(Date, nullable=False)
    pay_date: Mapped[Optional[date]] = mapped_column(Date)
    amount:   Mapped[Decimal]        = mapped_column(Numeric(12, 6), nullable=False)
    currency: Mapped[str]            = mapped_column(String(3), server_default="USD")

    security: Mapped["SecurityModel"] = relationship(back_populates="dividends")


class MarketIndexModel(Base):
    __tablename__ = "market_indices"

    id:          Mapped[int]            = mapped_column(primary_key=True, autoincrement=True)
    index_code:  Mapped[str]            = mapped_column(String(20), nullable=False, unique=True)
    name:        Mapped[str]            = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]]  = mapped_column(Text)
    is_active:   Mapped[bool]           = mapped_column(Boolean, server_default="true")