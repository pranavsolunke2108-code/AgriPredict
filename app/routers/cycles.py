"""Crop cycles router: start cycle, close cycle, cycle details, and audit log."""

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
import mysql.connector

from app import db
from app.db import DatabaseProcedureError
from app.dependencies import get_current_farmer
from app.routers.soil_tests import verify_farm_ownership
from app.schemas import (
    CropCalendarItem,
    CycleCloseRequest,
    CycleExpenseCategorySummary,
    CycleLogItem,
    CycleResponse,
    CycleStartRequest,
)

logger = logging.getLogger("agripredict.cycles")
router = APIRouter(tags=["Crop Cycles"])


def verify_cycle_ownership(cycle_id: int, farmer_id: int) -> Dict[str, Any]:
    """Helper to verify that a crop cycle exists and belongs to a farm owned by the farmer."""
    query = """
        SELECT
            c.cycle_id,
            c.farm_id,
            c.crop_id,
            c.prediction_id,
            c.sowing_date,
            c.expected_harvest,
            c.actual_harvest,
            c.status,
            c.yield_kg,
            c.selling_price_per_quintal,
            f.farmer_id,
            f.farm_name,
            cr.crop_name
        FROM crop_cycles c
        JOIN farms f ON c.farm_id = f.farm_id
        JOIN crops cr ON c.crop_id = cr.crop_id
        WHERE c.cycle_id = %s
    """
    row = db.fetch_one(query, (cycle_id,))
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop cycle with ID {cycle_id} not found",
        )
    if row["farmer_id"] != farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access or modify this crop cycle",
        )
    return row


@router.post(
    "/farms/{farm_id}/cycles",
    response_model=CycleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new crop cycle for a farm",
)
def start_cycle(
    farm_id: int,
    payload: CycleStartRequest,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Start a crop cycle using CALL start_crop_cycle(farm_id, crop_id, prediction_id, sowing_date).

    - Verifies farm ownership by the authenticated farmer.
    - If prediction_id is provided, links the cycle to the recommendation run.
    - If another active cycle exists on this farm, trigger trg_cycle_bi raises SQLSTATE 45000,
      which is caught and mapped to HTTP 400 Bad Request.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    # Validate that crop exists
    crop = db.fetch_one("SELECT crop_id FROM crops WHERE crop_id = %s", (payload.crop_id,))
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop with ID {payload.crop_id} not found",
        )

    # Call procedure: start_crop_cycle(farm_id, crop_id, prediction_id, sowing_date)
    try:
        results = db.call_procedure(
            "start_crop_cycle",
            (farm_id, payload.crop_id, payload.prediction_id, payload.sowing_date),
        )
        cycle_id = None
        if results and isinstance(results[0], dict) and "cycle_id" in results[0]:
            cycle_id = results[0]["cycle_id"]
        elif results and isinstance(results[0], (list, tuple)) and len(results[0]) > 0:
            cycle_id = results[0][0]

        if not cycle_id:
            # Fallback to query latest cycle on this farm
            latest = db.fetch_one(
                "SELECT cycle_id FROM crop_cycles WHERE farm_id = %s ORDER BY cycle_id DESC LIMIT 1",
                (farm_id,),
            )
            cycle_id = latest["cycle_id"] if latest else None

    except DatabaseProcedureError as exc:
        if exc.sqlstate == "45000" or "already has an active" in str(exc.message):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.message,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )
    except mysql.connector.Error as exc:
        if getattr(exc, "sqlstate", None) == "45000" or "already has an active" in str(exc.msg):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.msg,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while starting crop cycle: {exc}",
        )

    # Fetch and return created cycle
    cycle_data = verify_cycle_ownership(cycle_id, farmer_id)
    return CycleResponse(
        cycle_id=cycle_data["cycle_id"],
        farm_id=cycle_data["farm_id"],
        crop_id=cycle_data["crop_id"],
        crop_name=cycle_data["crop_name"],
        farm_name=cycle_data["farm_name"],
        prediction_id=cycle_data.get("prediction_id"),
        sowing_date=cycle_data.get("sowing_date"),
        expected_harvest=cycle_data.get("expected_harvest"),
        actual_harvest=cycle_data.get("actual_harvest"),
        status=cycle_data["status"],
        yield_kg=float(cycle_data["yield_kg"]) if cycle_data.get("yield_kg") is not None else None,
        selling_price_per_quintal=float(cycle_data["selling_price_per_quintal"]) if cycle_data.get("selling_price_per_quintal") is not None else None,
    )


@router.post(
    "/cycles/{cycle_id}/close",
    response_model=CycleResponse,
    summary="Close an active crop cycle as Harvested or Failed",
)
def close_cycle(
    cycle_id: int,
    payload: CycleCloseRequest,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Close a crop cycle using CALL close_crop_cycle(cycle_id, status, yield_kg, price_per_quintal).

    - Verifies ownership through cycle -> farm -> farmer_id.
    - Maps procedure SQLSTATE 45000 errors directly to HTTP 400 Bad Request.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_cycle_ownership(cycle_id, farmer_id)

    # Call procedure: close_crop_cycle(cycle_id, status, yield_kg, price_per_quintal)
    try:
        db.call_procedure(
            "close_crop_cycle",
            (cycle_id, payload.status, payload.yield_kg, payload.price_per_quintal),
        )
    except DatabaseProcedureError as exc:
        if exc.sqlstate == "45000":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.message,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )
    except mysql.connector.Error as exc:
        if getattr(exc, "sqlstate", None) == "45000":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.msg,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while closing crop cycle: {exc}",
        )

    # Fetch updated details
    cycle_data = verify_cycle_ownership(cycle_id, farmer_id)
    return CycleResponse(
        cycle_id=cycle_data["cycle_id"],
        farm_id=cycle_data["farm_id"],
        crop_id=cycle_data["crop_id"],
        crop_name=cycle_data["crop_name"],
        farm_name=cycle_data["farm_name"],
        prediction_id=cycle_data.get("prediction_id"),
        sowing_date=cycle_data.get("sowing_date"),
        expected_harvest=cycle_data.get("expected_harvest"),
        actual_harvest=cycle_data.get("actual_harvest"),
        status=cycle_data["status"],
        yield_kg=float(cycle_data["yield_kg"]) if cycle_data.get("yield_kg") is not None else None,
        selling_price_per_quintal=float(cycle_data["selling_price_per_quintal"]) if cycle_data.get("selling_price_per_quintal") is not None else None,
    )


@router.get(
    "/cycles/{cycle_id}",
    response_model=CycleResponse,
    summary="Get details of a crop cycle",
)
def get_cycle_details(
    cycle_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve details for a single crop cycle owned by the authenticated farmer."""
    farmer_id = current_farmer["farmer_id"]
    cycle_data = verify_cycle_ownership(cycle_id, farmer_id)

    return CycleResponse(
        cycle_id=cycle_data["cycle_id"],
        farm_id=cycle_data["farm_id"],
        crop_id=cycle_data["crop_id"],
        crop_name=cycle_data["crop_name"],
        farm_name=cycle_data["farm_name"],
        prediction_id=cycle_data.get("prediction_id"),
        sowing_date=cycle_data.get("sowing_date"),
        expected_harvest=cycle_data.get("expected_harvest"),
        actual_harvest=cycle_data.get("actual_harvest"),
        status=cycle_data["status"],
        yield_kg=float(cycle_data["yield_kg"]) if cycle_data.get("yield_kg") is not None else None,
        selling_price_per_quintal=float(cycle_data["selling_price_per_quintal"]) if cycle_data.get("selling_price_per_quintal") is not None else None,
    )


@router.get(
    "/cycles/{cycle_id}/log",
    response_model=List[CycleLogItem],
    summary="Get status change audit trail for a crop cycle",
)
def get_cycle_audit_log(
    cycle_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve audit history from crop_cycle_log for a cycle.

    Ownership is validated by verifying that the cycle belongs to the authenticated farmer.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_cycle_ownership(cycle_id, farmer_id)

    query = """
        SELECT log_id, cycle_id, old_status, new_status, changed_at
        FROM crop_cycle_log
        WHERE cycle_id = %s
        ORDER BY changed_at ASC, log_id ASC
    """
    rows = db.fetch_all(query, (cycle_id,))

    return [
        CycleLogItem(
            log_id=int(r["log_id"]),
            cycle_id=int(r["cycle_id"]),
            old_status=r.get("old_status"),
            new_status=r["new_status"],
            changed_at=r["changed_at"],
        )
        for r in rows
    ]


@router.get(
    "/cycles/{cycle_id}/calendar",
    response_model=List[CropCalendarItem],
    summary="Get growth stages calendar timeline for a crop cycle",
)
def get_cycle_calendar(
    cycle_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve growth stage timeline from crop_calendar_view for a cycle.

    Ownership is checked via cycle -> farm -> farmer_id.
    Ordered by start_day / start_date.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_cycle_ownership(cycle_id, farmer_id)

    query = """
        SELECT
            cycle_id,
            farm_id,
            crop_id,
            crop_name,
            stage_id,
            stage_name,
            start_day,
            end_day,
            start_date,
            end_date,
            stage_status,
            task
        FROM crop_calendar_view
        WHERE cycle_id = %s
        ORDER BY start_day ASC, stage_id ASC
    """
    rows = db.fetch_all(query, (cycle_id,))

    return [
        CropCalendarItem(
            cycle_id=int(r["cycle_id"]),
            farm_id=int(r["farm_id"]),
            crop_id=int(r["crop_id"]),
            crop_name=r["crop_name"],
            stage_id=int(r["stage_id"]),
            stage_name=r["stage_name"],
            start_day=int(r["start_day"]),
            end_day=int(r["end_day"]),
            start_date=r.get("start_date"),
            end_date=r.get("end_date"),
            stage_status=r.get("stage_status", "Upcoming"),
            task=r.get("task"),
        )
        for r in rows
    ]


@router.get(
    "/cycles/{cycle_id}/expense-summary",
    response_model=List[CycleExpenseCategorySummary],
    summary="Get cost breakdown by category for a specific cycle from cycle_expense_summary_view",
)
def get_cycle_expense_summary(
    cycle_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve expense categories, category totals, and percentage of cycle cost.

    Queries cycle_expense_summary_view filtered by cycle_id and farmer_id for strict ownership.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_cycle_ownership(cycle_id, farmer_id)

    query = """
        SELECT category, category_total, pct_of_cycle
        FROM cycle_expense_summary_view
        WHERE cycle_id = %s AND farmer_id = %s
        ORDER BY category_total DESC
    """
    rows = db.fetch_all(query, (cycle_id, farmer_id))

    return [
        CycleExpenseCategorySummary(
            category=r["category"],
            category_total=float(r["category_total"]),
            pct_of_cycle=float(r["pct_of_cycle"]) if r.get("pct_of_cycle") is not None else None,
        )
        for r in rows
    ]


