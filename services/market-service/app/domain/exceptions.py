class MarketDataError(Exception):
    """Базовое исключение сервиса."""

class ProviderUnavailableError(MarketDataError):
    """Внешний провайдер недоступен."""
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"Provider '{provider}' is unavailable")

class TickerNotFoundError(MarketDataError):
    """Тикер не найден в справочнике."""
    def __init__(self, ticker: str):
        self.ticker = ticker
        super().__init__(f"Ticker '{ticker}' not found")

class InvalidIntervalError(MarketDataError):
    """Неподдерживаемый интервал свечей."""
    def __init__(self, interval: str):
        self.interval = interval
        super().__init__(f"Interval '{interval}' is not supported")