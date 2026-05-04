class TechnicalAnalysisError(Exception):
    """Базовое исключение сервиса."""


class InsufficientDataError(TechnicalAnalysisError):
    """Недостаточно свечей для расчёта индикатора."""

    def __init__(self, indicator: str, required: int, got: int) -> None:
        super().__init__(
            f"{indicator} requires at least {required} bars, got {got}"
        )
        self.indicator = indicator
        self.required  = required
        self.got       = got


class UnknownIndicatorError(TechnicalAnalysisError):
    """Запрошен неизвестный тип индикатора."""

    def __init__(self, indicator_type: str) -> None:
        super().__init__(f"Unknown indicator type: {indicator_type!r}")
        self.indicator_type = indicator_type


class GrpcClientError(TechnicalAnalysisError):
    """Ошибка при обращении к market-service через gRPC."""
