from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import requests

SUPPORTED = ("USD", "GBP", "EUR", "CAD", "AUD", "INR", "JPY", "AED")
BASE = "USD"
_CACHE_TTL_LIVE = timedelta(minutes=60)
_CACHE_TTL_FALLBACK = timedelta(minutes=2)

# Approximate fallback rates (USD per unit of currency)
_FALLBACK_USD_PER = {
    "USD": 1.0,
    "GBP": 1.28,
    "EUR": 1.09,
    "CAD": 0.74,
    "AUD": 0.66,
    "INR": 0.012,
    "JPY": 0.0067,
    "AED": 0.2723,
}

_cache_payload: dict | None = None
_cache_expires_at: datetime | None = None


def _fallback_payload(*, error: str | None = None) -> dict:
    return {
        "base": BASE,
        "source": "fallback-static",
        "as_of": datetime.now(timezone.utc).date().isoformat(),
        "live": False,
        "error": error,
        "usd_per_currency": _FALLBACK_USD_PER.copy(),
    }


def _to_usd_per_currency_from_per_usd(rates: dict[str, Any]) -> dict[str, float]:
    usd_per = {BASE: 1.0}
    for code in SUPPORTED:
        if code == BASE:
            continue
        per_usd = float(rates.get(code, 0) or 0)  # units of code per 1 USD
        if per_usd > 0:
            usd_per[code] = 1.0 / per_usd
    return usd_per


def _with_fallback_for_missing(usd_per_partial: dict[str, float], *, source: str, as_of: str) -> dict:
    merged = _FALLBACK_USD_PER.copy()
    merged.update(usd_per_partial)
    missing = [c for c in SUPPORTED if c not in usd_per_partial]
    return {
        "base": BASE,
        "source": source,
        "as_of": as_of,
        "live": True,
        "error": (
            f"Live rates loaded, but used fallback values for: {', '.join(missing)}."
            if missing
            else None
        ),
        "usd_per_currency": merged,
    }


def _fetch_live_payload_frankfurter() -> dict:
    # Frankfurter provides free no-key FX data (base=USD requested).
    symbols = ",".join(c for c in SUPPORTED if c != BASE)
    url = f"https://api.frankfurter.app/latest?from={BASE}&to={symbols}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    body = response.json()
    as_of = str(body.get("date") or datetime.now(timezone.utc).date().isoformat())
    usd_per = _to_usd_per_currency_from_per_usd(body.get("rates", {}))
    if len(usd_per) <= 1:
        raise ValueError("No usable live rates returned")
    return _with_fallback_for_missing(usd_per, source="frankfurter.app", as_of=as_of)


def _fetch_live_payload_exchangerate_host() -> dict:
    symbols = ",".join(c for c in SUPPORTED if c != BASE)
    url = f"https://api.exchangerate.host/latest?base={BASE}&symbols={symbols}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    body = response.json()
    as_of = str(body.get("date") or datetime.now(timezone.utc).date().isoformat())
    usd_per = _to_usd_per_currency_from_per_usd(body.get("rates", {}))
    if len(usd_per) <= 1:
        raise ValueError("No usable live rates returned")
    return _with_fallback_for_missing(usd_per, source="exchangerate.host", as_of=as_of)


def _fetch_live_payload_open_er_api() -> dict:
    # Free, no-key endpoint with broad currency coverage.
    url = f"https://open.er-api.com/v6/latest/{BASE}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    body = response.json()
    if body.get("result") != "success":
        raise ValueError(f"Provider status not successful: {body.get('result')}")
    as_of = str(body.get("time_last_update_utc") or datetime.now(timezone.utc).date().isoformat())
    usd_per = _to_usd_per_currency_from_per_usd(body.get("rates", {}))
    if len(usd_per) <= 1:
        raise ValueError("No usable live rates returned")
    return _with_fallback_for_missing(usd_per, source="open.er-api.com", as_of=as_of)


def _fetch_live_payload() -> dict:
    errors: list[str] = []
    for provider in (
        _fetch_live_payload_open_er_api,
        _fetch_live_payload_frankfurter,
        _fetch_live_payload_exchangerate_host,
    ):
        try:
            return provider()
        except Exception as exc:
            errors.append(f"{provider.__name__}: {exc}")
    raise RuntimeError(" | ".join(errors))


def get_rates(*, force_refresh: bool = False) -> dict:
    global _cache_payload, _cache_expires_at

    now = datetime.now(timezone.utc)
    if (
        not force_refresh
        and _cache_payload is not None
        and _cache_expires_at is not None
        and now < _cache_expires_at
    ):
        return _cache_payload

    try:
        payload = _fetch_live_payload()
        ttl = _CACHE_TTL_LIVE
    except Exception as exc:
        payload = _fallback_payload(error=f"Live FX fetch failed; using fallback rates. Details: {exc}")
        ttl = _CACHE_TTL_FALLBACK

    _cache_payload = payload
    _cache_expires_at = now + ttl
    return payload
