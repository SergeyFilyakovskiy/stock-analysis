from dataclasses import dataclass

@dataclass
class AlertTriggeredEvent:
    event_id: str
    alert_id: str
    portfolio_id: str
    user_id: str
    ticker: str
    condition: str       # "above" | "below"
    target_price: str
    current_price: str
    occurred_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "AlertTriggeredEvent":
        return cls(
            event_id=data["event_id"],
            alert_id=data["alert_id"],
            portfolio_id=data["portfolio_id"],
            user_id=data["user_id"],
            ticker=data["ticker"],
            condition=data["condition"],
            target_price=str(data["target_price"]),
            current_price=str(data["current_price"]),
            occurred_at=data["occurred_at"],
        )

@dataclass
class ReportPublishedEvent:
    event_id: str
    user_id: str
    portfolio_id: str
    report_type: str     # "daily" | "weekly" | "monthly"
    report_url: str
    generated_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "ReportPublishedEvent":
        return cls(
            event_id=data["event_id"],
            user_id=data["user_id"],
            portfolio_id=data["portfolio_id"],
            report_type=data["report_type"],
            report_url=data["report_url"],
            generated_at=data["generated_at"],
        )