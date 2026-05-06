class PortfolioNotFound(Exception):
    def __init__(self, portfolio_id: str) -> None:
        super().__init__(f"Portfolio {portfolio_id} not found")


class PortfolioAccessDenied(Exception):
    def __init__(self, portfolio_id: str) -> None:
        super().__init__(f"Access denied to portfolio {portfolio_id}")


class InsufficientPosition(Exception):
    def __init__(self, ticker: str, available: str, requested: str) -> None:
        super().__init__(
            f"Insufficient position for {ticker}: "
            f"available={available}, requested={requested}"
        )


class WatchlistNotFound(Exception):
    def __init__(self, watchlist_id: str) -> None:
        super().__init__(f"Watchlist {watchlist_id} not found")


class WatchlistAccessDenied(Exception):
    def __init__(self, watchlist_id: str) -> None:
        super().__init__(f"Access denied to watchlist {watchlist_id}")


class AlertNotFound(Exception):
    def __init__(self, alert_id: str) -> None:
        super().__init__(f"Alert {alert_id} not found")


class DuplicateWatchlistItem(Exception):
    def __init__(self, ticker: str, watchlist_id: str) -> None:
        super().__init__(f"Ticker {ticker} already in watchlist {watchlist_id}")