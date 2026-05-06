from pydantic import BaseModel


class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details."""
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str | None = None