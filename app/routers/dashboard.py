"""Dashboard router: views for summary, active crop status, and harvest history."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app import db
from app.dependencies import get_current_farmer
from app.schemas import (
    CurrentStatusItem,
    DashboardSummaryResponse,
    FarmerCategoryExpenseSummary,
    HistoryItem,
)

logger = logging.getLogger("agripredict.dashboard")
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get aggregated summary for logged-in farmer",
)
def get_dashboard_summary(
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve overall KPI statistics from farmer_summary_view.

    Always filters by the authenticated farmer's ID from the JWT.
    """
    farmer_id = current_farmer["farmer_id"]

    query = """
        SELECT
            farmer_id,
            name,
            total_farms,
            active_cycles,
            completed_cycles,
            total_revenue,
            total_expenses,
            net_profit
        FROM farmer_summary_view
        WHERE farmer_id = %s
        LIMIT 1
    """
    row = db.fetch_one(query, (farmer_id,))

    if row:
        return DashboardSummaryResponse(
            farmer_id=int(row["farmer_id"]),
            name=row["name"],
            total_farms=int(row.get("total_farms") or 0),
            active_cycles=int(row.get("active_cycles") or 0),
            completed_cycles=int(row.get("completed_cycles") or 0),
            total_revenue=float(row.get("total_revenue") or 0.0),
            total_expenses=float(row.get("total_expenses") or 0.0),
            net_profit=float(row.get("net_profit") or 0.0),
        )

    # Fallback if view doesn't return a row (e.g. for non-farmer accounts or clean DB)
    farms_count_row = db.fetch_one(
        "SELECT COUNT(*) AS total FROM farms WHERE farmer_id = %s",
        (farmer_id,),
    )
    total_farms = farms_count_row["total"] if farms_count_row else 0

    return DashboardSummaryResponse(
        farmer_id=farmer_id,
        name=current_farmer.get("name", "Farmer"),
        total_farms=total_farms,
        active_cycles=0,
        completed_cycles=0,
        total_revenue=0.0,
        total_expenses=0.0,
        net_profit=0.0,
    )


@router.get(
    "/current",
    response_model=List[CurrentStatusItem],
    summary="Get active crop cycles with progress and stage tracking",
)
def get_current_status(
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve all active cycles ('Planned', 'Growing') from current_status_view.

    Strictly filtered by the authenticated farmer_id.
    """
    farmer_id = current_farmer["farmer_id"]

    query = """
        SELECT
            farmer_id,
            farm_id,
            farm_name,
            cycle_id,
            crop_name,
            status,
            sowing_date,
            expected_harvest,
            days_since_sowing,
            days_until_sowing,
            days_to_harvest,
            progress_pct,
            current_stage,
            current_task,
            expenses_so_far
        FROM current_status_view
        WHERE farmer_id = %s
        ORDER BY cycle_id DESC
    """
    rows = db.fetch_all(query, (farmer_id,))

    results: List[CurrentStatusItem] = []
    for r in rows:
        results.append(
            CurrentStatusItem(
                farmer_id=int(r["farmer_id"]),
                farm_id=int(r["farm_id"]),
                farm_name=r["farm_name"],
                cycle_id=int(r["cycle_id"]),
                crop_name=r["crop_name"],
                status=r["status"],
                sowing_date=r.get("sowing_date"),
                expected_harvest=r.get("expected_harvest"),
                days_since_sowing=r.get("days_since_sowing"),
                days_until_sowing=r.get("days_until_sowing"),
                days_to_harvest=r.get("days_to_harvest"),
                progress_pct=float(r.get("progress_pct") or 0.0),
                current_stage=r.get("current_stage") or "No stage data",
                current_task=r.get("current_task"),
                expenses_so_far=float(r.get("expenses_so_far") or 0.0),
            )
        )
    return results


@router.get(
    "/history",
    response_model=List[HistoryItem],
    summary="Get completed cycle history with revenue and profit",
)
def get_farmer_history(
    farm_id: Optional[int] = Query(None, description="Filter by specific farm ID"),
    crop: Optional[str] = Query(None, description="Filter by crop name (partial match)"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve historical completed cycles ('Harvested', 'Failed') from farmer_history_view.

    Ordered newest harvest first with optional farm and crop filters and pagination.
    """
    farmer_id = current_farmer["farmer_id"]

    query = """
        SELECT
            farmer_id,
            farm_id,
            farm_name,
            cycle_id,
            crop_name,
            status,
            sowing_date,
            actual_harvest,
            yield_kg,
            selling_price_per_quintal,
            revenue,
            total_expenses,
            profit
        FROM farmer_history_view
        WHERE farmer_id = %s
    """
    params: List[Any] = [farmer_id]

    if farm_id is not None:
        query += " AND farm_id = %s"
        params.append(farm_id)

    if crop and crop.strip():
        query += " AND crop_name LIKE %s"
        params.append(f"%{crop.strip()}%")

    query += " ORDER BY actual_harvest DESC, cycle_id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    rows = db.fetch_all(query, tuple(params))

    history: List[HistoryItem] = []
    for r in rows:
        history.append(
            HistoryItem(
                farmer_id=int(r["farmer_id"]),
                farm_id=int(r["farm_id"]),
                farm_name=r["farm_name"],
                cycle_id=int(r["cycle_id"]),
                crop_name=r["crop_name"],
                status=r["status"],
                sowing_date=r.get("sowing_date"),
                actual_harvest=r.get("actual_harvest"),
                yield_kg=float(r["yield_kg"]) if r.get("yield_kg") is not None else None,
                selling_price_per_quintal=float(r["selling_price_per_quintal"]) if r.get("selling_price_per_quintal") is not None else None,
                revenue=float(r.get("revenue") or 0.0),
                total_expenses=float(r.get("total_expenses") or 0.0),
                profit=float(r.get("profit") or 0.0),
            )
        )
    return history


@router.get(
    "/expenses-by-category",
    response_model=List[FarmerCategoryExpenseSummary],
    summary="Get aggregated expense totals by category across all cycles for the logged-in farmer",
)
def get_farmer_expenses_by_category(
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Aggregates all cycle expenses grouped by category for the farmer.

    Queries cycle_expense_summary_view grouped by category and filtered by farmer_id.
    """
    farmer_id = current_farmer["farmer_id"]

    query = """
        SELECT category, ROUND(SUM(category_total), 2) AS total_amount
        FROM cycle_expense_summary_view
        WHERE farmer_id = %s
        GROUP BY category
        ORDER BY total_amount DESC
    """
    rows = db.fetch_all(query, (farmer_id,))

    return [
        FarmerCategoryExpenseSummary(
            category=r["category"],
            total_amount=float(r["total_amount"]),
        )
        for r in rows
    ]

