from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class SecurityDto:
    ticker:   str
    name:     str
    exchange: Optional[str]
    sector:   Optional[str]
    is_active: bool


@dataclass(frozen=True)
class PriceBarDto:
    time:   datetime
    ticker: str
    open:   Optional[Decimal]
    high:   Optional[Decimal]
    low:    Optional[Decimal]
    close:  Decimal
    volume: Optional[int]
    source: Optional[str]


@dataclass(frozen=True)
class OHLCVDto:
    ticker:   str
    interval: str
    bars:     tuple[PriceBarDto, ...]


@dataclass(frozen=True)
class DividendDto:
    ticker:   str
    ex_date:  date
    pay_date: Optional[date]
    amount:   Decimal
    currency: str


@dataclass(frozen=True)
class MarketIndexDto:
    index_code:  str
    name:        str
    description: Optional[str]
    is_active:   bool