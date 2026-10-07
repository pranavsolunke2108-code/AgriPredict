"""Weather caching and retrieval router."""

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import db
from app.dependencies import get_current_farmer
from app.routers.soil_tests import verify_farm_ownership
from app.schemas import (
    ManualWeatherCreateRequest,
    WeatherRecordResponse,
    WeatherSyncResponse,
)
from app.services.weather_service import sync_farm_weather

logger = logging.getLogger("agripredict.weather_router")
router = APIRouter(tags=["Weather Records"])


@router.post(
    "/farms/{farm_id}/weather/refresh",
    response_model=WeatherSyncResponse,
    summary="Refresh past 30 days of weather from Open-Meteo API",
)
def refresh_farm_weather(
    farm_id: int,
    force: bool = Query(False, description="Force refresh even if updated within the last 6 hours"),
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Synchronize past 30 days of daily weather records for a farm using the Open-Meteo API.

    Skips the API request if weather was already synced within the last 6 hours.
    Upserts into weather_records with source='api'.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    try:
        result = sync_farm_weather(farm_id, force=force)
        return WeatherSyncResponse(**result)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except RuntimeError as api_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Weather synchronization failed: {api_err}",
        )


@router.get(
    "/farms/{farm_id}/weather",
    response_model=List[WeatherRecordResponse],
    summary="Get cached weather history for a farm",
)
def get_farm_weather(
    farm_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of past days to retrieve"),
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve weather records for a farm over the specified number of days (default: 30), newest first."""
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    query = """
        SELECT weather_id, farm_id, record_date, temperature, humidity, rainfall_mm, source
        FROM weather_records
        WHERE farm_id = %s
          AND record_date >= DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)
        ORDER BY record_date DESC
    """
    records = db.fetch_all(query, (farm_id, days))
    return records


@router.post(
    "/farms/{farm_id}/weather/manual",
    response_model=WeatherRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually record daily weather for a farm",
)
def add_manual_weather(
    farm_id: int,
    payload: ManualWeatherCreateRequest,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Manually enter daily weather data for a farm (source='manual').

    Useful for farms with no GPS coordinates or for manual weather station logging.
    Upserts if a record for the specified farm_id and record_date already exists.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    upsert_query = """
        INSERT INTO weather_records (
            farm_id, record_date, temperature, humidity, rainfall_mm, source
        ) VALUES (
            %s, %s, %s, %s, %s, 'manual'
        )
        ON DUPLICATE KEY UPDATE
            temperature = VALUES(temperature),
            humidity = VALUES(humidity),
            rainfall_mm = VALUES(rainfall_mm),
            source = 'manual'
    """
    db.execute_update(
        upsert_query,
        (
            farm_id,
            payload.record_date,
            payload.temperature,
            payload.humidity,
            payload.rainfall_mm,
        ),
    )

    fetch_query = """
        SELECT weather_id, farm_id, record_date, temperature, humidity, rainfall_mm, source
        FROM weather_records
        WHERE farm_id = %s AND record_date = %s
    """
    record = db.fetch_one(fetch_query, (farm_id, payload.record_date))
    if not record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve saved manual weather record",
        )

    return record
