from pydantic import BaseModel


class FxRatesOut(BaseModel):
    base: str
    source: str
    as_of: str
    live: bool
    error: str | None = None
    usd_per_currency: dict[str, float]
