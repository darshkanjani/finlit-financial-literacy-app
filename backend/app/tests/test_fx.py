from app.services import fx_service


def test_fx_rates_returns_live_payload_when_provider_succeeds(monkeypatch):
    monkeypatch.setattr(
        fx_service,
        "_fetch_live_payload",
        lambda: {
            "base": "USD",
            "source": "open.er-api.com",
            "as_of": "2026-03-13",
            "live": True,
            "error": None,
            "usd_per_currency": {"USD": 1.0, "GBP": 1.28, "AED": 0.2723},
        },
    )
    fx_service._cache_payload = None
    fx_service._cache_expires_at = None

    payload = fx_service.get_rates(force_refresh=True)

    assert payload["live"] is True
    assert payload["source"] == "open.er-api.com"
    assert payload["usd_per_currency"]["GBP"] == 1.28


def test_fx_rates_fall_back_when_live_fetch_fails(monkeypatch):
    monkeypatch.setattr(fx_service, "_fetch_live_payload", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    fx_service._cache_payload = None
    fx_service._cache_expires_at = None

    payload = fx_service.get_rates(force_refresh=True)

    assert payload["live"] is False
    assert payload["source"] == "fallback-static"
    assert "boom" in str(payload["error"])
    assert payload["usd_per_currency"]["AED"] == fx_service._FALLBACK_USD_PER["AED"]
