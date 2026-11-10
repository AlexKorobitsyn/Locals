import asyncio
import io
import json
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker

import APP.services.geocoding as geocoding


def test_provider_formats_russian_address_and_identifies_application(
    settings, monkeypatch
):
    settings.geocoding_reverse_url = "https://example.com/reverse"
    calls = []

    def open_request(request, **kwargs):
        calls.append(request)
        return io.BytesIO(
            json.dumps(
                {
                    "address": {
                        "city": "Екатеринбург",
                        "road": "улица Малышева",
                        "house_number": "1",
                    }
                }
            ).encode()
        )

    monkeypatch.setattr(geocoding, "urlopen", open_request)
    assert (
        geocoding.fetch_address(settings, 56.84, 60.61)
        == "Екатеринбург, улица Малышева, 1"
    )
    params = parse_qs(urlsplit(calls[0].full_url).query)
    assert params["accept-language"] == ["ru"]
    assert params["lat"] == ["56.84"] and params["lon"] == ["60.61"]
    assert calls[0].get_header("User-agent") == settings.geocoding_user_agent


@pytest.fixture
def provider(api_client, monkeypatch):
    api_client.app.state.settings.geocoding_reverse_url = "https://example.com/reverse"
    calls = []

    def fetch(settings, lat, lng):
        calls.append((lat, lng))
        return "Екатеринбург, улица Малышева, 1"

    monkeypatch.setattr(geocoding, "fetch_address", fetch)
    return calls


def lookup(client, headers=None, lat=56.84, lng=60.61):
    return client.get(
        "/api/v1/geocoding/reverse", headers=headers, params={"lat": lat, "lng": lng}
    )


@pytest.mark.integration
def test_cache_is_shared_across_users_and_requests(api_client, account, provider):
    _, first = account("first")
    _, second = account("second")
    result = lookup(api_client, first)
    assert result.status_code == 200
    assert result.json() == {"address": "Екатеринбург, улица Малышева, 1"}
    assert lookup(api_client, second).json() == result.json()
    assert len(provider) == 1
    assert result.headers["cache-control"] == "no-store"


@pytest.mark.integration
def test_global_rate_limit_and_validation(api_client, account, provider, catalog_db):
    _, headers = account()
    assert lookup(api_client).status_code == 401
    for lat, lng in [(91, 60), (56, 181), ("nan", 60)]:
        assert lookup(api_client, headers, lat, lng).status_code == 422
    assert not provider
    assert lookup(api_client, headers).status_code == 200
    limited = lookup(api_client, headers, lat=57)
    assert limited.status_code == 429
    assert int(limited.headers["retry-after"]) >= 1
    assert len(provider) == 1
    catalog_db.execute(
        "UPDATE geocoding_cache SET requested_at=requested_at-interval '2 seconds'"
    )
    assert lookup(api_client, headers, lat=57).status_code == 200
    assert len(provider) == 2


@pytest.mark.integration
def test_failure_is_cached_and_does_not_bypass_rate_limit(
    api_client, account, provider, monkeypatch
):
    _, headers = account()
    calls = []

    def fail(*args):
        calls.append(1)
        raise URLError("offline")

    monkeypatch.setattr(geocoding, "fetch_address", fail)
    assert lookup(api_client, headers).status_code == 503
    assert lookup(api_client, headers).status_code == 503
    assert len(calls) == 1
    assert lookup(api_client, headers, lat=57).status_code == 429


@pytest.mark.integration
def test_missing_address_is_a_cached_valid_response(
    api_client, account, provider, monkeypatch
):
    _, headers = account()
    calls = []

    def missing(*args):
        calls.append(1)
        return None

    monkeypatch.setattr(geocoding, "fetch_address", missing)
    for _ in range(2):
        response = lookup(api_client, headers)
        assert response.status_code == 200 and response.json() == {"address": None}
    assert len(calls) == 1


@pytest.mark.integration
def test_separate_sessions_cannot_call_provider_simultaneously(catalog_db, monkeypatch):
    catalog_db.settings.geocoding_reverse_url = "https://example.com/reverse"
    calls = []

    def fetch(*args):
        calls.append(1)
        return "Address"

    monkeypatch.setattr(geocoding, "fetch_address", fetch)

    async def run():
        factory = async_sessionmaker(catalog_db.engine, expire_on_commit=False)

        async def lookup(lat):
            async with factory() as session:
                return await geocoding.reverse_address(
                    session, catalog_db.settings, lat, 60
                )

        return await asyncio.gather(lookup(56), lookup(57), return_exceptions=True)

    results = asyncio.run(run())
    assert len(calls) == 1
    assert (
        sum(
            isinstance(item, HTTPException) and item.status_code == 429
            for item in results
        )
        == 1
    )
    assert sum(getattr(item, "address", None) == "Address" for item in results) == 1


@pytest.mark.integration
def test_unexpected_failure_still_records_request_attempt(
    api_client, account, provider, monkeypatch, catalog_db
):
    _, headers = account()

    def crash(*args):
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(geocoding, "fetch_address", crash)
    with pytest.raises(RuntimeError, match="unexpected failure"):
        lookup(api_client, headers)
    assert (
        catalog_db.execute("SELECT count(*) AS total FROM geocoding_cache")[0]["total"]
        == 1
    )
    assert lookup(api_client, headers).status_code == 503
