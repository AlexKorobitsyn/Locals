import hashlib
import json
import logging
from datetime import timedelta
from math import ceil
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException
from sqlalchemy import func, select
from starlette.concurrency import run_in_threadpool

from APP.core.constants import DESCRIPTION_MAX_LENGTH
from APP.models.geocoding_cache import GeocodingCache
from APP.schemas.geocoding import ReverseAddress

logger = logging.getLogger(__name__)
COORDINATE_PRECISION = 5
MAX_RESPONSE_BYTES = 64 * 1024
GEOCODING_LOCK = "locals:geocoding:nominatim"


def fetch_address(settings, lat, lng):
    params = urlencode(
        {
            "format": "jsonv2",
            "lat": lat,
            "lon": lng,
            "addressdetails": 1,
            "accept-language": "ru",
            "zoom": 18,
            "layer": "address",
        }
    )
    endpoint = str(settings.geocoding_reverse_url)
    request = Request(
        endpoint + ("&" if "?" in endpoint else "?") + params,
        headers={
            "User-Agent": settings.geocoding_user_agent,
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=settings.geocoding_timeout_seconds) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("Geocoding response is too large")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Invalid geocoding response")
    if data.get("error"):
        return None
    parts = data.get("address") or {}
    if not isinstance(parts, dict):
        raise ValueError("Invalid geocoding address")
    city = next(
        (
            parts[key]
            for key in ("city", "town", "village", "municipality")
            if parts.get(key)
        ),
        None,
    )
    road = next(
        (
            parts[key]
            for key in ("road", "pedestrian", "residential", "footway", "path")
            if parts.get(key)
        ),
        None,
    )
    address = (
        ", ".join(
            str(value) for value in (city, road, parts.get("house_number")) if value
        )
        if road
        else data.get("display_name")
    )
    return str(address)[:DESCRIPTION_MAX_LENGTH] if address else None


def cached_address(cached, now):
    if cached is None or cached.expires_at <= now:
        return None
    if cached.failed:
        raise HTTPException(
            status_code=503,
            detail="Address provider unavailable; enter the address manually",
        )
    return ReverseAddress(address=cached.address)


async def reverse_address(session, settings, lat, lng):
    if settings.geocoding_reverse_url is None:
        raise HTTPException(status_code=503, detail="Address lookup is not configured")
    lat, lng = round(lat, COORDINATE_PRECISION), round(lng, COORDINATE_PRECISION)
    cache_key = hashlib.sha256(
        f"{settings.geocoding_reverse_url}|ru|{lat:.5f}|{lng:.5f}".encode()
    ).hexdigest()
    async with session.begin():
        now = await session.scalar(select(func.clock_timestamp()))
        cached = await session.get(GeocodingCache, cache_key)
        result = cached_address(cached, now)
        if result is not None:
            return result
        # Короткая блокировка объединяет лимит всех реплик backend.
        locked = await session.scalar(
            select(func.pg_try_advisory_xact_lock(func.hashtext(GEOCODING_LOCK)))
        )
        if not locked:
            raise HTTPException(
                status_code=429,
                detail="Address lookup is busy; retry shortly",
                headers={"Retry-After": "2"},
            )
        now = await session.scalar(select(func.clock_timestamp()))
        cached = await session.get(GeocodingCache, cache_key, populate_existing=True)
        result = cached_address(cached, now)
        if result is not None:
            return result
        last = await session.scalar(
            select(GeocodingCache.requested_at)
            .order_by(GeocodingCache.requested_at.desc())
            .limit(1)
        )
        remaining = (
            settings.geocoding_request_interval_seconds - (now - last).total_seconds()
            if last
            else 0
        )
        if remaining > 0:
            raise HTTPException(
                status_code=429,
                detail="Address lookup is rate limited",
                headers={"Retry-After": str(ceil(remaining))},
            )
        if cached is None:
            cached = GeocodingCache(cache_key=cache_key)
            session.add(cached)
        # Фиксируем попытку до HTTP: сбой или отмена не должны обходить лимит.
        cached.requested_at = now
        cached.expires_at = now + timedelta(
            seconds=settings.geocoding_failure_ttl_seconds
        )
        cached.address, cached.failed = None, True
        requested_at = now
    failed = False
    try:
        address = await run_in_threadpool(fetch_address, settings, lat, lng)
    except (URLError, TimeoutError, OSError, ValueError):
        logger.warning("Address provider unavailable")
        address, failed = None, True
    async with session.begin():
        cached = await session.scalar(
            select(GeocodingCache)
            .where(GeocodingCache.cache_key == cache_key)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if cached is not None and cached.requested_at == requested_at:
            ttl = (
                settings.geocoding_cache_ttl_seconds
                if address
                else settings.geocoding_failure_ttl_seconds
            )
            cached.expires_at = requested_at + timedelta(seconds=ttl)
            cached.address, cached.failed = address, failed
    if failed:
        raise HTTPException(
            status_code=503,
            detail="Address provider unavailable; enter the address manually",
        )
    return ReverseAddress(address=address)
