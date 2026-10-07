"""Agronomic advisory router: fertilizer dosage recommendations and crop rotation advice."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app import db
from app.db import DatabaseProcedureError
from app.dependencies import get_current_farmer
from app.routers.soil_tests import verify_farm_ownership
from app.schemas import (
    CropProfitEstimateResponse,
    FertilizerAdviceRequest,
    FertilizerAdviceResponse,
    FertilizerItem,
    RecommendationProfitItem,
    RecommendationProfitResponse,
    RotationAdviceItem,
    RotationAdviceResponse,
)

logger = logging.getLogger("agripredict.advisory")
router = APIRouter(tags=["Agronomic Advisory"])


@router.post(
    "/farms/{farm_id}/fertilizer-advice",
    response_model=FertilizerAdviceResponse,
    summary="Get tailored fertilizer dosage plan for a crop and soil test",
)
def get_fertilizer_advice(
    farm_id: int,
    payload: FertilizerAdviceRequest,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Generate fertilizer application advice using CALL recommend_fertilizer(farm_id, test_id, crop_id).

    - Verifies farm ownership.
    - Resolves test_id to the latest soil test on this farm if omitted.
    - If nutrients are already sufficient (empty procedure result), returns a clear message.
    - Amounts are computed per acre and scaled to the total farm area.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    # 1. Resolve soil test ID
    test_id = payload.test_id
    if test_id is None:
        latest_test = db.fetch_one(
            """
            SELECT test_id
            FROM soil_tests
            WHERE farm_id = %s
            ORDER BY test_date DESC, test_id DESC
            LIMIT 1
            """,
            (farm_id,),
        )
        if not latest_test:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No soil test found for this farm. Please record a soil test first.",
            )
        test_id = latest_test["test_id"]
    else:
        check_test = db.fetch_one(
            "SELECT test_id FROM soil_tests WHERE test_id = %s AND farm_id = %s",
            (test_id, farm_id),
        )
        if not check_test:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Soil test with ID {test_id} not found for this farm",
            )

    # 2. Check crop exists
    crop = db.fetch_one("SELECT crop_id, crop_name FROM crops WHERE crop_id = %s", (payload.crop_id,))
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop with ID {payload.crop_id} not found",
        )

    # 3. Call stored procedure: recommend_fertilizer(farm_id, test_id, crop_id)
    try:
        rows = db.call_procedure(
            "recommend_fertilizer",
            (farm_id, test_id, payload.crop_id),
        )
    except DatabaseProcedureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    # Filter out empty or null rows
    valid_rows = [
        r for r in rows
        if isinstance(r, dict) and r.get("fertilizer") and float(r.get("kg_per_acre") or 0) > 0
    ]

    if not valid_rows:
        return FertilizerAdviceResponse(
            message="Soil nutrient levels are sufficient. No additional chemical fertilizer is needed.",
            farm_id=farm_id,
            crop_id=payload.crop_id,
            test_id=test_id,
            fertilizers=[],
        )

    items = [
        FertilizerItem(
            fertilizer=r["fertilizer"],
            kg_per_acre=float(r["kg_per_acre"]),
            kg_for_farm=float(r["kg_for_farm"]),
            estimated_cost=float(r["estimated_cost"]),
        )
        for r in valid_rows
    ]

    return FertilizerAdviceResponse(
        message=f"Fertilizer plan generated for {crop['crop_name']} based on soil test #{test_id}.",
        farm_id=farm_id,
        crop_id=payload.crop_id,
        test_id=test_id,
        fertilizers=items,
    )


@router.get(
    "/farms/{farm_id}/rotation-advice",
    response_model=RotationAdviceResponse,
    summary="Get crop rotation recommendations based on previously harvested crop",
)
def get_rotation_advice(
    farm_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Generate crop rotation suggestions using CALL rotation_advice(farm_id).

    - Verifies farm ownership.
    - Inspects previous harvested/failed cycle to find compatible succession crops (e.g. legume after cereal).
    - Sorts in-season crops first.
    - If no closed cycle exists yet, returns a friendly message.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    try:
        rows = db.call_procedure(
            "rotation_advice",
            (farm_id,),
        )
    except DatabaseProcedureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    valid_rows = [
        r for r in rows
        if isinstance(r, dict) and r.get("crop_id") is not None
    ]

    if not valid_rows:
        return RotationAdviceResponse(
            message="No completed crop cycle found for this farm. Record a harvested or closed cycle to receive crop rotation advice.",
            farm_id=farm_id,
            advice=[],
        )

    advice_items = [
        RotationAdviceItem(
            crop_id=int(r["crop_id"]),
            crop_name=r["crop_name"],
            season=r["season"],
            is_in_season=bool(r.get("is_in_season", 0)),
            duration_days=int(r["duration_days"]),
            reason=r.get("reason"),
        )
        for r in valid_rows
    ]

    return RotationAdviceResponse(
        message="Recommended succession crops based on previous harvest and current season.",
        farm_id=farm_id,
        advice=advice_items,
    )


@router.get(
    "/farms/{farm_id}/profit-estimates",
    response_model=RecommendationProfitResponse,
    summary="Get economics and profit estimates for the farm's recommended crops",
)
def get_recommendation_profit_estimates(
    farm_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve financial forecasts for the farm's latest crop recommendations.

    Executes CALL profit_for_recommendations(farm_id).
    If no recommendations have been generated yet, returns an empty list with a friendly message.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    try:
        rows = db.call_procedure("profit_for_recommendations", (farm_id,))
    except DatabaseProcedureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    valid_rows = [
        r for r in rows
        if isinstance(r, dict) and r.get("crop_id") is not None
    ]

    if not valid_rows:
        return RecommendationProfitResponse(
            farm_id=farm_id,
            message="No crop recommendations found for this farm yet. Run crop recommendations first to see profit estimates.",
            estimates=[],
        )

    estimates = []
    for r in valid_rows:
        price_val = r.get("market_price_per_q") if r.get("market_price_per_q") is not None else r.get("price_per_quintal")
        estimates.append(
            RecommendationProfitItem(
                prediction_id=r.get("prediction_id"),
                rank_no=int(r.get("rank_order") or r.get("rank_no") or 1),
                suitability_score=float(r.get("confidence_score") or r.get("suitability_score") or 0.0),
                crop_id=int(r["crop_id"]),
                crop_name=str(r["crop_name"]),
                price_district=r.get("district") or r.get("price_district"),
                price_per_quintal=float(price_val) if price_val is not None else None,
                price_date=r.get("price_date"),
                avg_yield_q_per_acre=float(r["avg_yield_q_per_acre"]) if r.get("avg_yield_q_per_acre") is not None else None,
                est_cost_per_acre=float(r["est_cost_per_acre"]) if r.get("est_cost_per_acre") is not None else None,
                revenue_per_acre=float(r["gross_revenue_per_acre"]) if r.get("gross_revenue_per_acre") is not None else (float(r["revenue_per_acre"]) if r.get("revenue_per_acre") is not None else None),
                profit_per_acre=float(r["net_profit_per_acre"]) if r.get("net_profit_per_acre") is not None else (float(r["profit_per_acre"]) if r.get("profit_per_acre") is not None else None),
                profit_per_acre_per_month=float(r["profit_per_acre_per_month"]) if r.get("profit_per_acre_per_month") is not None else None,
                profit_for_farm=float(r["total_farm_profit"]) if r.get("total_farm_profit") is not None else (float(r["profit_for_farm"]) if r.get("profit_for_farm") is not None else None),
            )
        )

    return RecommendationProfitResponse(
        farm_id=farm_id,
        message="Profit estimates retrieved successfully.",
        estimates=estimates,
    )


@router.get(
    "/farms/{farm_id}/crops/{crop_id}/profit",
    response_model=CropProfitEstimateResponse,
    summary="Estimate profit, revenue, and expenses for any crop on a specific farm",
)
def get_crop_profit_estimate(
    farm_id: int,
    crop_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Calculate projected revenue, cost, and net profit for a given crop on a farm.

    Calls CALL estimate_crop_profit(farm_id, crop_id).
    If market prices have not yet been recorded for this crop, returns 'no price data available'.
    """
    farmer_id = current_farmer["farmer_id"]
    farm = verify_farm_ownership(farm_id, farmer_id)

    crop = db.fetch_one("SELECT crop_id, crop_name, duration_days FROM crops WHERE crop_id = %s", (crop_id,))
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop with ID {crop_id} not found",
        )

    try:
        rows = db.call_procedure("estimate_crop_profit", (farm_id, crop_id))
    except DatabaseProcedureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    row = rows[0] if rows and isinstance(rows[0], dict) else {}

    price_val = row.get("market_price_per_q") if row.get("market_price_per_q") is not None else row.get("price_per_quintal")
    has_price = price_val is not None and row.get("price_date") is not None
    msg = "Profit estimated successfully" if has_price else "no price data available"

    return CropProfitEstimateResponse(
        crop_id=crop_id,
        crop_name=str(crop["crop_name"]),
        farm_id=farm_id,
        farm_area_acres=float(farm.get("area_acres") or row.get("area_acres") or 0.0),
        duration_days=int(row.get("duration_days") or crop["duration_days"]),
        price_district=row.get("district") or row.get("price_district"),
        price_per_quintal=float(price_val) if price_val is not None else None,
        price_date=row.get("price_date"),
        avg_yield_q_per_acre=float(row["avg_yield_q_per_acre"]) if row.get("avg_yield_q_per_acre") is not None else None,
        est_cost_per_acre=float(row["est_cost_per_acre"]) if row.get("est_cost_per_acre") is not None else None,
        revenue_per_acre=float(row["gross_revenue_per_acre"]) if row.get("gross_revenue_per_acre") is not None else (float(row["revenue_per_acre"]) if row.get("revenue_per_acre") is not None else None),
        profit_per_acre=float(row["net_profit_per_acre"]) if row.get("net_profit_per_acre") is not None else (float(row["profit_per_acre"]) if row.get("profit_per_acre") is not None else None),
        profit_per_acre_per_month=float(row["profit_per_acre_per_month"]) if row.get("profit_per_acre_per_month") is not None else None,
        profit_for_farm=float(row["total_farm_profit"]) if row.get("total_farm_profit") is not None else (float(row["profit_for_farm"]) if row.get("profit_for_farm") is not None else None),
        message=msg,
    )
