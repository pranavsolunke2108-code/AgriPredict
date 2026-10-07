"""Market prices router: mandi rates from latest_prices_view and historical price trends."""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query

from app import db
from app.dependencies import get_current_farmer
from app.schemas import MarketPriceHistoryPoint, MarketPriceItem

router = APIRouter(prefix="/prices", tags=["Market Prices"])


@router.get(
    "",
    response_model=List[MarketPriceItem],
    summary="Get latest mandi crop prices (defaults to farmer's own district)",
)
def get_latest_prices(
    crop_id: Optional[int] = Query(None, description="Optional crop filter"),
    district: Optional[str] = Query(None, description="District name (defaults to farmer's district)"),
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve latest crop market prices from latest_prices_view.

    If district is omitted, defaults to the logged-in farmer's district.
    """
    target_district = district if district is not None else current_farmer.get("district")

    where_clauses = []
    params = []

    if target_district and target_district.lower() != "all":
        where_clauses.append("district = %s")
        params.append(target_district)

    if crop_id is not None:
        where_clauses.append("crop_id = %s")
        params.append(crop_id)

    query = """
        SELECT price_id, crop_id, crop_name, district, price_per_quintal, price_date
        FROM latest_prices_view
    """
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY crop_name ASC, district ASC"

    rows = db.fetch_all(query, tuple(params))
    return [
        MarketPriceItem(
            price_id=r.get("price_id"),
            crop_id=int(r["crop_id"]),
            crop_name=r.get("crop_name"),
            district=r["district"],
            price_per_quintal=float(r["price_per_quintal"]),
            price_date=r["price_date"],
        )
        for r in rows
    ]


@router.get(
    "/history",
    response_model=List[MarketPriceHistoryPoint],
    summary="Get historical price trend for a crop and district",
)
def get_price_history(
    crop_id: Optional[int] = Query(None, description="Crop ID filter"),
    district: Optional[str] = Query(None, description="District name filter"),
    days: int = Query(90, ge=1, le=730, description="Number of days in past to look back"),
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve historical price records from market_prices for charting trends."""
    target_district = district if district is not None else current_farmer.get("district")
    cutoff_date = date.today() - timedelta(days=days)

    where_clauses = ["mp.price_date >= %s"]
    params = [cutoff_date]

    if target_district and target_district.lower() != "all":
        where_clauses.append("mp.district = %s")
        params.append(target_district)

    if crop_id is not None:
        where_clauses.append("mp.crop_id = %s")
        params.append(crop_id)

    query = f"""
        SELECT mp.price_id, mp.crop_id, c.crop_name, mp.district, mp.price_per_quintal, mp.price_date
        FROM market_prices mp
        JOIN crops c ON mp.crop_id = c.crop_id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY mp.price_date ASC, c.crop_name ASC
    """
    rows = db.fetch_all(query, tuple(params))
    return [
        MarketPriceHistoryPoint(
            price_id=int(r["price_id"]),
            crop_id=int(r["crop_id"]),
            crop_name=r.get("crop_name"),
            district=r["district"],
            price_per_quintal=float(r["price_per_quintal"]),
            price_date=r["price_date"],
        )
        for r in rows
    ]
