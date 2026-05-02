from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional


@dataclass
class Security:
    ticker:    str
    name:      str
    exchange:  Optional[str] = None
    sector:    Optional[str] = None
    is_active: bool = True


@dataclass
class PriceBar:
    time:   datetime
    ticker: str
    open:   Optional[Decimal] = None
    high:   Optional[Decimal] = None
    low:    Optional[Decimal] = None
    close:  Decimal = Decimal("0")
    volume: Optional[int] = None
    source: Optional[str] = None


@dataclass
class Dividend:
    ticker:   str
    ex_date:  date
    amount:   Decimal
    pay_date: Optional[date] = None
    currency: str = "USD"


@dataclass
class MarketIndex:
    index_code:  str
    name:        str
    description: Optional[str] = None
    is_active:   bool = True