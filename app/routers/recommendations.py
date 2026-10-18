"""Recommendation and prediction history router."""

from collections import OrderedDict
import logging
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import db
from app.db import DatabaseProcedureError
from app.dependencies import get_current_farmer
from app.routers.soil_tests import verify_farm_ownership
from app.schemas import (
    CropScoreBreakdown,
    PredictionGroupResponse,
    PredictionItem,
    RecommendationRequest,
    RecommendationResponse,
    WhyCropResponse,
)
from app.services.weather_service import is_weather_fresh, sync_farm_weather
from app.services.why_service import build_why_crop_response

logger = logging.getLogger("agripredict.recommendations")
router = APIRouter(tags=["Crop Recommendations"])


@router.post(
    "/farms/{farm_id}/recommend",
    response_model=RecommendationResponse,
    summary="Generate top-3 crop recommendations for a farm",
)
def get_crop_recommendations(
    farm_id: int,
    payload: RecommendationRequest = RecommendationRequest(),
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Generate top 3 crop recommendations using the MySQL recommend_crops stored procedure.

    - Automatically resolves test_id to the latest soil test if omitted.
    - If weather records are older than 6 hours, automatically refreshes weather from Open-Meteo.
    - Executes 'CALL recommend_crops(%s, %s, %s)' with parameters.
    - Maps procedure SQLSTATE 45000 errors directly to HTTP 400 Bad Request.
    """
    farmer_id = current_farmer["farmer_id"]
    farm = verify_farm_ownership(farm_id, farmer_id)

    # 1. Resolve soil test ID (default to latest test for this farm)
    test_id = payload.test_id
    if test_id is None:
        latest_test_query = """
            SELECT test_id
            FROM soil_tests
            WHERE farm_id = %s
            ORDER BY test_date DESC, test_id DESC
            LIMIT 1
        """
        latest_test = db.fetch_one(latest_test_query, (farm_id,))
        if not latest_test:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No soil test records found for this farm. Please record a soil test first.",
            )
        test_id = latest_test["test_id"]
    else:
        # Verify provided test_id belongs to this farm
        check_test = db.fetch_one(
            "SELECT test_id FROM soil_tests WHERE test_id = %s AND farm_id = %s",
            (test_id, farm_id),
        )
        if not check_test:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Soil test with ID {test_id} does not exist for this farm",
            )

    # 2. Check and refresh weather if older than 6 hours
    weather_status = "cached"
    if not is_weather_fresh(farm_id):
        # Attempt to refresh if coordinates exist
        if farm.get("latitude") is not None and farm.get("longitude") is not None:
            try:
                sync_farm_weather(farm_id, force=False)
                weather_status = "refreshed"
            except Exception as e:
                logger.warning("Could not refresh Open-Meteo weather for farm %d: %s", farm_id, e)
                # Check if we have existing weather data in DB
                existing_weather = db.fetch_one(
                    "SELECT COUNT(*) AS cnt FROM weather_records WHERE farm_id = %s",
                    (farm_id,),
                )
                cnt = existing_weather["cnt"] if existing_weather else 0
                if cnt < 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unable to fetch weather data from API and no local records exist: {e}",
                    )
                weather_status = "existing_offline"
        else:
            weather_status = "manual"

    # 3. Resolve season parameter (None will cause the stored procedure to call get_season(CURDATE()))
    season_param = None if (not payload.season or payload.season == "auto") else payload.season

    # 4. Call the stored procedure: CALL recommend_crops(%s, %s, %s)
    try:
        raw_recommendations = db.call_procedure(
            "recommend_crops",
            (farm_id, test_id, season_param),
        )
    except DatabaseProcedureError as proc_err:
        if proc_err.sqlstate == "45000":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=proc_err.message,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation procedure failed: {proc_err.message}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute recommendation engine: {exc}",
        )

    # 5. Look up crop_id and prediction_id from predictions table for these recommendations
    pred_map = {}
    try:
        recent_preds = db.fetch_all(
            """
            SELECT p.prediction_id, p.crop_id, p.rank_no, c.crop_name
            FROM predictions p
            JOIN crops c ON p.crop_id = c.crop_id
            WHERE p.farm_id = %s AND p.test_id = %s
            ORDER BY p.predicted_on DESC, p.prediction_id DESC
            LIMIT 3
            """,
            (farm_id, test_id),
        )
        for rp in recent_preds:
            pred_map[rp["crop_name"]] = (rp["prediction_id"], rp["crop_id"])
    except Exception:
        pass

    crops = []
    for r in raw_recommendations:
        c_name = r["crop_name"]
        p_id, c_id = pred_map.get(c_name, (None, None))
        if not c_id:
            c_info = db.fetch_one("SELECT crop_id, econ_source, econ_year FROM crops WHERE crop_name = %s", (c_name,))
            econ_src = None
            econ_yr = None
            if c_info:
                if not c_id:
                    c_id = c_info["crop_id"]
                econ_src = c_info.get("econ_source")
                econ_yr = c_info.get("econ_year")
        else:
            c_info = db.fetch_one("SELECT econ_source, econ_year FROM crops WHERE crop_id = %s", (c_id,))
            econ_src = c_info.get("econ_source") if c_info else None
            econ_yr = c_info.get("econ_year") if c_info else None

        crops.append(
            CropScoreBreakdown(
                rank_no=int(r["rank_no"]),
                crop_id=c_id,
                crop_name=c_name,
                season=r["season"],
                suitability=round(float(r["suitability"]), 1),
                ph_score=round(float(r["ph_score"]), 1),
                temp_score=round(float(r["temp_score"]), 1),
                humidity_score=round(float(r["humidity_score"]), 1),
                rain_score=round(float(r["rain_score"]), 1),
                n_score=round(float(r["n_score"]), 1),
                p_score=round(float(r["p_score"]), 1),
                k_score=round(float(r["k_score"]), 1),
                prediction_id=p_id,
                econ_source=econ_src,
                econ_year=econ_yr,
            )
        )

    return RecommendationResponse(
        farm_id=farm_id,
        test_id=test_id,
        season=season_param or "auto (detected)",
        weather_status=weather_status,
        recommendations=crops,
    )


@router.get(
    "/farms/{farm_id}/predictions",
    response_model=List[PredictionGroupResponse],
    summary="Get past recommendation history for a farm",
)
def get_prediction_history(
    farm_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve historical crop recommendations for a farm.

    Results are grouped by recommendation timestamp (predicted_on), newest run first.
    Each group contains the top 3 crops recommended in that run.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    query = """
        SELECT
            p.prediction_id,
            p.farm_id,
            p.test_id,
            p.weather_id,
            p.crop_id,
            c.crop_name,
            c.season,
            p.suitability_score,
            p.rank_no,
            p.predicted_on
        FROM predictions p
        JOIN crops c ON p.crop_id = c.crop_id
        WHERE p.farm_id = %s
        ORDER BY p.predicted_on DESC, p.rank_no ASC
    """
    rows = db.fetch_all(query, (farm_id,))

    # Group by predicted_on timestamp
    grouped: Dict[Any, List[Dict[str, Any]]] = OrderedDict()
    for row in rows:
        key = row["predicted_on"]
        grouped.setdefault(key, []).append(row)

    history: List[PredictionGroupResponse] = []
    for pred_time, items in grouped.items():
        first = items[0]
        history.append(
            PredictionGroupResponse(
                predicted_on=pred_time,
                farm_id=first["farm_id"],
                test_id=first["test_id"],
                weather_id=first.get("weather_id"),
                crops=[
                    PredictionItem(
                        prediction_id=item.get("prediction_id"),
                        rank_no=item["rank_no"],
                        crop_id=item["crop_id"],
                        crop_name=item["crop_name"],
                        season=item["season"],
                        suitability_score=round(float(item["suitability_score"]), 1),
                    )
                    for item in items
                ],
            )
        )

    return history


@router.get(
    "/farms/{farm_id}/recommendations/{crop_id}/why",
    response_model=WhyCropResponse,
    summary="Explain why a crop is recommended for a farm",
)
def get_why_crop_explanation(
    farm_id: int,
    crop_id: int,
    test_id: Optional[int] = Query(None, description="Soil test ID; defaults to latest test"),
    lang: Optional[Literal["en", "mr", "hi"]] = Query(None, description="Output language"),
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Return detailed parameter-by-parameter explanation of why a crop fits a farm.

    - Verifies farm ownership.
    - Resolves test_id to the farm's latest soil test if omitted.
    - Executes explain_crop_for_farm(farm_id, test_id, crop_id).
    - Maps procedure errors (SQLSTATE 45000) directly to HTTP 400 Bad Request.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    crop = db.fetch_one("SELECT crop_id, crop_name FROM crops WHERE crop_id = %s", (crop_id,))
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Crop #{crop_id} not found")

    if test_id is None:
        latest_test = db.fetch_one(
            "SELECT test_id FROM soil_tests WHERE farm_id = %s ORDER BY test_date DESC, test_id DESC LIMIT 1",
            (farm_id,),
        )
        if not latest_test:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No soil test records found for this farm",
            )
        resolved_test_id = int(latest_test["test_id"])
    else:
        test_row = db.fetch_one(
            "SELECT test_id FROM soil_tests WHERE test_id = %s AND farm_id = %s",
            (test_id, farm_id),
        )
        if not test_row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Soil test #{test_id} not found for farm #{farm_id}",
            )
        resolved_test_id = test_id

    try:
        raw_rows = db.call_procedure(
            "explain_crop_for_farm",
            (farm_id, resolved_test_id, crop_id),
        )
    except DatabaseProcedureError as proc_err:
        if proc_err.sqlstate == "45000" or "45000" in str(proc_err) or "weather" in str(proc_err).lower() or "soil" in str(proc_err).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=proc_err.message,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Procedure failed: {proc_err.message}",
        )
    except Exception as exc:
        if "45000" in str(exc) or "weather" in str(exc).lower() or "soil" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain crop fit: {exc}",
        )

    user_lang = lang or current_farmer.get("language") or "en"
    return build_why_crop_response(
        crop_id=crop_id,
        crop_name=crop["crop_name"],
        raw_rows=raw_rows,
        lang=user_lang,
    )

