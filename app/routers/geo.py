"""Geolocation and Nominatim proxy router for AgriPredict.

Provides backend proxies for OpenStreetMap Nominatim search and reverse geocoding.
Adheres strictly to the Nominatim usage policy:
- Valid User-Agent with contact info
- Max 1 request per second rate limiting
- Result caching
- Countrycodes=in filter and limit=5
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
import httpx

from app.schemas import GeoReverseResponse, GeoSuggestion

logger = logging.getLogger("agripredict.geo")
router = APIRouter(prefix="/geo", tags=["Geolocation"])

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "AgriPredict/1.0 (contact: admin@agripredict.in)"

_rate_limit_lock = threading.Lock()
_last_request_time = 0.0

# In-memory caches
_search_cache: Dict[str, List[Dict[str, Any]]] = {}
_reverse_cache: Dict[str, Dict[str, Any]] = {}


def _wait_for_rate_limit() -> None:
    """Enforce maximum 1 request per second to OpenStreetMap Nominatim."""
    global _last_request_time
    with _rate_limit_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        _last_request_time = time.time()


def clear_geo_cache() -> None:
    """Helper for tests to reset cached geocoding results."""
    _search_cache.clear()
    _reverse_cache.clear()


def _format_label(item: Dict[str, Any]) -> str:
    """Extract a concise, farmer-friendly location label from Nominatim result."""
    addr = item.get("address") or {}
    place = (
        addr.get("village")
        or addr.get("hamlet")
        or addr.get("suburb")
        or addr.get("neighbourhood")
        or addr.get("town")
        or addr.get("city")
        or item.get("name")
    )
    city_or_town = addr.get("city") or addr.get("town")
    district = addr.get("state_district") or addr.get("district") or addr.get("county")
    state = addr.get("state")

    parts: List[str] = []
    for comp in (place, city_or_town, district, state):
        if comp and str(comp).strip() and str(comp).strip() not in parts:
            parts.append(str(comp).strip())

    if parts:
        label = ", ".join(parts)
    else:
        raw = item.get("display_name", "")
        label = ", ".join([p.strip() for p in raw.split(",")[:3]])

    return label[:150]


@router.get(
    "/search",
    response_model=List[GeoSuggestion],
    summary="Search location suggestions from Nominatim (India only)",
)
def search_location(
    q: str = Query(..., min_length=1, description="Location search query (e.g. Pune, Baramati)"),
):
    """Proxy query to Nominatim search with countrycodes=in, limit=5, and caching."""
    query = q.strip().lower()
    if not query:
        return []

    # Check cache
    if query in _search_cache:
        return [GeoSuggestion(**item) for item in _search_cache[query]]

    # Respect rate limit
    _wait_for_rate_limit()

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(
                f"{NOMINATIM_BASE_URL}/search",
                params={
                    "q": q,
                    "format": "jsonv2",
                    "countrycodes": "in",
                    "limit": 5,
                    "addressdetails": 1,
                },
                headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code != 200:
                logger.warning("Nominatim search returned HTTP %s", resp.status_code)
                return []
            raw_results = resp.json()
    except Exception as err:
        logger.warning("Nominatim search request error: %s", err)
        return []

    results: List[Dict[str, Any]] = []
    if isinstance(raw_results, list):
        for it in raw_results:
            try:
                lat = float(it["lat"])
                lon = float(it["lon"])
                label = _format_label(it)
                results.append({
                    "display_name": it.get("display_name", ""),
                    "label": label,
                    "lat": lat,
                    "lon": lon,
                    "address": it.get("address") or {},
                })
            except (KeyError, ValueError, TypeError):
                continue

    _search_cache[query] = results
    return [GeoSuggestion(**r) for r in results]


@router.get(
    "/reverse",
    response_model=GeoReverseResponse,
    summary="Reverse geocode coordinates to location label",
)
def reverse_geocode(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude (-90 to 90)"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude (-180 to 180)"),
):
    """Reverse geocode latitude and longitude to a human-readable location label.

    Validates coordinates and provides a soft warning if coordinates are outside India (lat 6-38, lon 68-98).
    """
    if lat < -90.0 or lat > 90.0 or lon < -180.0 or lon > 180.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coordinates out of valid range (-90..90, -180..180)",
        )

    # Soft warning for coordinates outside India (lat 6-38, lon 68-98)
    warning = None
    if lat < 6.0 or lat > 38.0 or lon < 68.0 or lon > 98.0:
        warning = "Coordinates appear to be outside India (expected lat 6-38, lon 68-98)"

    cache_key = f"{round(lat, 4)},{round(lon, 4)}"
    if cache_key in _reverse_cache:
        cached = dict(_reverse_cache[cache_key])
        cached["warning"] = warning
        return GeoReverseResponse(**cached)

    _wait_for_rate_limit()

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(
                f"{NOMINATIM_BASE_URL}/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "jsonv2",
                    "addressdetails": 1,
                },
                headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code != 200:
                fallback_label = f"Location ({lat:.4f}, {lon:.4f})"
                return GeoReverseResponse(
                    display_name=fallback_label,
                    label=fallback_label,
                    lat=lat,
                    lon=lon,
                    address={},
                    warning=warning,
                )
            data = resp.json()
    except Exception as err:
        logger.warning("Nominatim reverse geocode error: %s", err)
        fallback_label = f"Location ({lat:.4f}, {lon:.4f})"
        return GeoReverseResponse(
            display_name=fallback_label,
            label=fallback_label,
            lat=lat,
            lon=lon,
            address={},
            warning=warning,
        )

    label = _format_label(data)
    result_data = {
        "display_name": data.get("display_name", f"Location ({lat:.4f}, {lon:.4f})"),
        "label": label,
        "lat": lat,
        "lon": lon,
        "address": data.get("address") or {},
    }
    _reverse_cache[cache_key] = result_data
    result_data["warning"] = warning
    return GeoReverseResponse(**result_data)
