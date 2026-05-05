class FundamentalServiceError(Exception):
    """Base exception for fundamental-analysis-service."""


class CompanyNotFoundError(FundamentalServiceError):
    def __init__(self, ticker: str) -> None:
        super().__init__(f"Company not found: {ticker}")
        self.ticker = ticker


class ReportNotFoundError(FundamentalServiceError):
    def __init__(self, ticker: str, period: str | None = None) -> None:
        msg = f"Financial report not found for {ticker}"
        if period:
            msg += f" period={period}"
        super().__init__(msg)
        self.ticker = ticker
        self.period = period


class MetricsNotFoundError(FundamentalServiceError):
    def __init__(self, ticker: str) -> None:
        super().__init__(f"Financial metrics not found for {ticker}")
        self.ticker = ticker


class ValuationError(FundamentalServiceError):
    """Raised when a valuation model cannot compute an estimate."""


class InsufficientDataError(ValuationError):
    def __init__(self, model: str, missing: list[str]) -> None:
        super().__init__(
            f"[{model}] Insufficient data. Missing fields: {', '.join(missing)}"
        )
        self.model = model
        self.missing = missing


class ExternalAPIError(FundamentalServiceError):
    def __init__(self, provider: str, detail: str) -> None:
        super().__init__(f"[{provider}] External API error: {detail}")
        self.provider = provider


class MarketServiceError(FundamentalServiceError):
    def __init__(self, method: str, detail: str) -> None:
        super().__init__(f"[market-service::{method}] {detail}")
        self.method = method