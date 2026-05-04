from enum import StrEnum


class SignalType(StrEnum):
    BUY     = "BUY"
    SELL    = "SELL"
    NEUTRAL = "NEUTRAL"


class IndicatorType(StrEnum):
    RSI       = "rsi"
    MACD      = "macd"
    BOLLINGER = "bollinger"
    SMA       = "sma"
    EMA       = "ema"