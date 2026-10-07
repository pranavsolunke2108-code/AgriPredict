"""Weather caching service interfacing with Open-Meteo API and weather_records table."""

from datetime import date, datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
import httpx

from app import db

logger = logging.getLogger("agripredict.weather")

# In-memory tracking of when a farm's weather was last fetched from the API
_last_fetch_cache: Dict[int, datetime] = {}
CACHE_TTL_HOURS = 6


def get_last_fetch_time(farm_id: int) -> Optional[datetime]:
    """Return the UTC datetime of the last successful Open-Meteo API fetch for a farm."""
    return _last_fetch_cache.get(farm_id)


def set_last_fetch_time(farm_id: int, dt: Optional[datetime] = None) -> None:
    """Set or reset the last API fetch timestamp for a farm."""
    _last_fetch_cache[farm_id] = dt or datetime.now(timezone.utc)


def is_weather_fresh(farm_id: int) -> bool:
    """Check if weather for this farm was fetched from Open-Meteo within the last 6 hours."""
    last_time = _last_fetch_cache.get(farm_id)
    if not last_time:
        return False
    age = datetime.now(timezone.utc) - last_time
    if age.total_seconds() > CACHE_TTL_HOURS * 3600:
        return False

    # Also verify that today's record exists in the database
    today_rec = db.fetch_one(
        "SELECT weather_id FROM weather_records WHERE farm_id = %s AND record_date = CURRENT_DATE LIMIT 1",
        (farm_id,),
    )
    return today_rec is not None


def fetch_open_meteo_weather(
    latitude: float,
    longitude: float,
    past_days: int = 30
) -> List[Dict[str, Any]]:
    """Fetch past 30 days of weather records from Open-Meteo API.

    Queries daily mean temperature and total precipitation.
    Averages hourly relative humidity to calculate daily mean relative humidity.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "past_days": past_days,
        "forecast_days": 1,
        "daily": ["temperature_2m_mean", "precipitation_sum"],
        "hourly": ["relative_humidity_2m"],
        "timezone": "auto",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("Failed to fetch weather from Open-Meteo API: %s", exc)
        raise RuntimeError(f"Open-Meteo API error: {exc}") from exc

    daily = data.get("daily", {})
    hourly = data.get("hourly", {})
    daily_dates = daily.get("time", [])
    daily_temps = daily.get("temperature_2m_mean", [])
    daily_rains = daily.get("precipitation_sum", [])

    hourly_times = hourly.get("time", [])
    hourly_hums = hourly.get("relative_humidity_2m", [])

    # Group and average hourly humidity by day
    humidity_by_day: Dict[str, List[float]] = {}
    for t_str, h_val in zip(hourly_times, hourly_hums):
        d_key = t_str.split("T")[0]
        if h_val is not None:
            humidity_by_day.setdefault(d_key, []).append(float(h_val))

    records: List[Dict[str, Any]] = []
    for i, d_str in enumerate(daily_dates):
        temp = daily_temps[i] if i < len(daily_temps) else None
        rain = daily_rains[i] if i < len(daily_rains) else None
        h_list = humidity_by_day.get(d_str, [])
        avg_hum = round(sum(h_list) / len(h_list), 2) if h_list else None

        records.append({
            "record_date": d_str,
            "temperature": float(temp) if temp is not None else None,
            "humidity": avg_hum,
            "rainfall_mm": float(rain) if rain is not None else 0.0,
        })

    return records


def upsert_weather_records(
    farm_id: int,
    records: List[Dict[str, Any]],
    source: str = "api"
) -> int:
    """Upsert weather records into weather_records table.

    Uses parameterized INSERT ... ON DUPLICATE KEY UPDATE on (farm_id, record_date).
    """
    upsert_query = """
        INSERT INTO weather_records (farm_id, record_date, temperature, humidity, rainfall_mm, source)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            temperature = VALUES(temperature),
            humidity = VALUES(humidity),
            rainfall_mm = VALUES(rainfall_mm),
            source = VALUES(source)
    """

    count = 0
    with db.get_db_cursor(commit=True) as cursor:
        for r in records:
            cursor.execute(
                upsert_query,
                (
                    farm_id,
                    r["record_date"],
                    r.get("temperature"),
                    r.get("humidity"),
                    r.get("rainfall_mm"),
                    source,
                ),
            )
            count += 1

    if source == "api":
        set_last_fetch_time(farm_id)

    return count


def sync_farm_weather(farm_id: int, force: bool = False) -> Dict[str, Any]:
    """Sync weather for a farm from Open-Meteo.

    Checks coordinates and the 6-hour caching rule.
    """
    # 1. Fetch farm details
    farm = db.fetch_one("SELECT farm_id, latitude, longitude FROM farms WHERE farm_id = %s", (farm_id,))
    if not farm:
        raise ValueError(f"Farm with ID {farm_id} does not exist.")

    lat = farm.get("latitude")
    lon = farm.get("longitude")

    if lat is None or lon is None:
        raise ValueError(
            "Farm has no latitude/longitude coordinates configured. "
            "Please update farm coordinates or submit weather data manually via POST /farms/{farm_id}/weather/manual."
        )

    # 2. Check 6-hour cache
    if not force and is_weather_fresh(farm_id):
        logger.info("Skipping Open-Meteo API call for farm %d: weather is fresh (< 6 hours)", farm_id)
        return {
            "message": "Weather data is already up-to-date (fetched within the last 6 hours)",
            "records_synced": 0,
            "cached": True,
            "farm_id": farm_id,
        }

    # 3. Fetch from API
    logger.info("Fetching Open-Meteo weather for farm %d (lat=%s, lon=%s)", farm_id, lat, lon)
    records = fetch_open_meteo_weather(float(lat), float(lon), past_days=30)

    # 4. Upsert into database
    synced_count = upsert_weather_records(farm_id, records, source="api")

    return {
        "message": f"Successfully synchronized {synced_count} daily weather records from Open-Meteo API",
        "records_synced": synced_count,
        "cached": False,
        "farm_id": farm_id,
    }
