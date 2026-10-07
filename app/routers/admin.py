"""Admin management router: full CRUD for agronomic master data, users, and audit log."""

import csv
from datetime import date, datetime
import io
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app import db
from app.dependencies import require_admin
from app.schemas import (
    AuditLogItem,
    CropCreateUpdateRequest,
    CropDetailResponse,
    CropStageCreateUpdateRequest,
    CropStageDetailResponse,
    CsvUploadResponse,
    FarmerProfileResponse,
    FertilizerCreateUpdateRequest,
    FertilizerDetailResponse,
    MarketPriceCreateRequest,
    MarketPriceHistoryPoint,
    RotationRuleCreateUpdateRequest,
    RotationRuleDetailResponse,
    TranslationCreateUpdateRequest,
    TranslationItem,
    UserActiveUpdateRequest,
)

logger = logging.getLogger("agripredict.admin")
router = APIRouter(prefix="/admin", tags=["Admin Management"])


# =============================================================================
# 1. Crops Master Data CRUD
# =============================================================================

@router.get("/crops", response_model=List[CropDetailResponse], summary="List all crops with full parameters")
def list_crops(_: Dict[str, Any] = Depends(require_admin)):
    """Retrieve full catalog of crops including yield and cost estimates."""
    rows = db.fetch_all("""
        SELECT
            crop_id, crop_name, season, duration_days,
            min_ph, max_ph, min_temp, max_temp, min_humidity, max_humidity,
            min_rainfall, max_rainfall, n_required, p_required, k_required,
            avg_yield_q_per_acre, est_cost_per_acre
        FROM crops
        ORDER BY crop_name ASC
    """)
    return [
        CropDetailResponse(
            crop_id=int(r["crop_id"]),
            crop_name=r["crop_name"],
            season=r["season"],
            duration_days=int(r["duration_days"]),
            min_ph=float(r["min_ph"]) if r.get("min_ph") is not None else None,
            max_ph=float(r["max_ph"]) if r.get("max_ph") is not None else None,
            min_temp=float(r["min_temp"]) if r.get("min_temp") is not None else None,
            max_temp=float(r["max_temp"]) if r.get("max_temp") is not None else None,
            min_humidity=float(r["min_humidity"]) if r.get("min_humidity") is not None else None,
            max_humidity=float(r["max_humidity"]) if r.get("max_humidity") is not None else None,
            min_rainfall=float(r["min_rainfall"]) if r.get("min_rainfall") is not None else None,
            max_rainfall=float(r["max_rainfall"]) if r.get("max_rainfall") is not None else None,
            n_required=int(r["n_required"]) if r.get("n_required") is not None else None,
            p_required=int(r["p_required"]) if r.get("p_required") is not None else None,
            k_required=int(r["k_required"]) if r.get("k_required") is not None else None,
            avg_yield_q_per_acre=float(r["avg_yield_q_per_acre"]) if r.get("avg_yield_q_per_acre") is not None else None,
            est_cost_per_acre=float(r["est_cost_per_acre"]) if r.get("est_cost_per_acre") is not None else None,
        )
        for r in rows
    ]


@router.get("/crops/{crop_id}", response_model=CropDetailResponse, summary="Get single crop details")
def get_crop(crop_id: int, _: Dict[str, Any] = Depends(require_admin)):
    """Retrieve details for a single crop."""
    row = db.fetch_one("""
        SELECT
            crop_id, crop_name, season, duration_days,
            min_ph, max_ph, min_temp, max_temp, min_humidity, max_humidity,
            min_rainfall, max_rainfall, n_required, p_required, k_required,
            avg_yield_q_per_acre, est_cost_per_acre
        FROM crops
        WHERE crop_id = %s
    """, (crop_id,))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Crop #{crop_id} not found")

    return CropDetailResponse(
        crop_id=int(row["crop_id"]),
        crop_name=row["crop_name"],
        season=row["season"],
        duration_days=int(row["duration_days"]),
        min_ph=float(row["min_ph"]) if row.get("min_ph") is not None else None,
        max_ph=float(row["max_ph"]) if row.get("max_ph") is not None else None,
        min_temp=float(row["min_temp"]) if row.get("min_temp") is not None else None,
        max_temp=float(row["max_temp"]) if row.get("max_temp") is not None else None,
        min_humidity=float(row["min_humidity"]) if row.get("min_humidity") is not None else None,
        max_humidity=float(row["max_humidity"]) if row.get("max_humidity") is not None else None,
        min_rainfall=float(row["min_rainfall"]) if row.get("min_rainfall") is not None else None,
        max_rainfall=float(row["max_rainfall"]) if row.get("max_rainfall") is not None else None,
        n_required=int(row["n_required"]) if row.get("n_required") is not None else None,
        p_required=int(row["p_required"]) if row.get("p_required") is not None else None,
        k_required=int(row["k_required"]) if row.get("k_required") is not None else None,
        avg_yield_q_per_acre=float(row["avg_yield_q_per_acre"]) if row.get("avg_yield_q_per_acre") is not None else None,
        est_cost_per_acre=float(row["est_cost_per_acre"]) if row.get("est_cost_per_acre") is not None else None,
    )


@router.post("/crops", response_model=CropDetailResponse, status_code=status.HTTP_201_CREATED, summary="Create a new crop")
def create_crop(payload: CropCreateUpdateRequest, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Create a new crop with validation on soil, climate, yield, and cost."""
    existing = db.fetch_one("SELECT crop_id FROM crops WHERE LOWER(crop_name) = LOWER(%s)", (payload.crop_name.strip(),))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Crop '{payload.crop_name}' already exists")

    admin_id = current_admin["farmer_id"]
    query = """
        INSERT INTO crops (
            crop_name, season, duration_days, min_ph, max_ph, min_temp, max_temp,
            min_humidity, max_humidity, min_rainfall, max_rainfall,
            n_required, p_required, k_required, avg_yield_q_per_acre, est_cost_per_acre
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        payload.crop_name.strip(), payload.season, payload.duration_days,
        payload.min_ph, payload.max_ph, payload.min_temp, payload.max_temp,
        payload.min_humidity, payload.max_humidity, payload.min_rainfall, payload.max_rainfall,
        payload.n_required, payload.p_required, payload.k_required,
        payload.avg_yield_q_per_acre, payload.est_cost_per_acre,
    )
    new_id, _ = db.execute_admin_query(query, params, admin_farmer_id=admin_id)
    return get_crop(new_id, current_admin)


@router.put("/crops/{crop_id}", response_model=CropDetailResponse, summary="Update crop details")
def update_crop(crop_id: int, payload: CropCreateUpdateRequest, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Update existing crop parameters. Automatically logs changes to admin_audit_log via triggers."""
    existing = db.fetch_one("SELECT crop_id FROM crops WHERE crop_id = %s", (crop_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Crop #{crop_id} not found")

    admin_id = current_admin["farmer_id"]
    query = """
        UPDATE crops SET
            crop_name = %s, season = %s, duration_days = %s,
            min_ph = %s, max_ph = %s, min_temp = %s, max_temp = %s,
            min_humidity = %s, max_humidity = %s, min_rainfall = %s, max_rainfall = %s,
            n_required = %s, p_required = %s, k_required = %s,
            avg_yield_q_per_acre = %s, est_cost_per_acre = %s
        WHERE crop_id = %s
    """
    params = (
        payload.crop_name.strip(), payload.season, payload.duration_days,
        payload.min_ph, payload.max_ph, payload.min_temp, payload.max_temp,
        payload.min_humidity, payload.max_humidity, payload.min_rainfall, payload.max_rainfall,
        payload.n_required, payload.p_required, payload.k_required,
        payload.avg_yield_q_per_acre, payload.est_cost_per_acre,
        crop_id,
    )
    db.execute_admin_query(query, params, admin_farmer_id=admin_id)
    return get_crop(crop_id, current_admin)


@router.delete("/crops/{crop_id}", summary="Delete a crop")
def delete_crop(crop_id: int, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Delete a crop from the catalog.

    If referenced by crop cycles or predictions, rejects with HTTP 409 Conflict.
    """
    crop = db.fetch_one("SELECT crop_id, crop_name FROM crops WHERE crop_id = %s", (crop_id,))
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Crop #{crop_id} not found")

    cycles_ref = db.fetch_one("SELECT COUNT(*) AS cnt FROM crop_cycles WHERE crop_id = %s", (crop_id,))
    predictions_ref = db.fetch_one("SELECT COUNT(*) AS cnt FROM predictions WHERE crop_id = %s", (crop_id,))

    cycles_count = cycles_ref["cnt"] if cycles_ref else 0
    predictions_count = predictions_ref["cnt"] if predictions_ref else 0

    if cycles_count > 0 or predictions_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete crop '{crop['crop_name']}': it is referenced by {cycles_count} crop cycle(s) and {predictions_count} recommendation(s).",
        )

    admin_id = current_admin["farmer_id"]
    db.execute_admin_query("DELETE FROM crops WHERE crop_id = %s", (crop_id,), admin_farmer_id=admin_id)
    return {"message": f"Crop '{crop['crop_name']}' deleted successfully"}


# =============================================================================
# 2. Crop Growth Stages CRUD
# =============================================================================

@router.get("/crop-stages", response_model=List[CropStageDetailResponse], summary="List crop growth stages")
def list_crop_stages(crop_id: Optional[int] = Query(None), _: Dict[str, Any] = Depends(require_admin)):
    """List growth stages, optionally filtered by crop_id."""
    query = """
        SELECT cs.stage_id, cs.crop_id, c.crop_name, cs.stage_name, cs.start_day, cs.end_day, cs.task
        FROM crop_stages cs
        JOIN crops c ON cs.crop_id = c.crop_id
    """
    params = []
    if crop_id is not None:
        query += " WHERE cs.crop_id = %s"
        params.append(crop_id)
    query += " ORDER BY c.crop_name ASC, cs.start_day ASC"

    rows = db.fetch_all(query, tuple(params))
    return [
        CropStageDetailResponse(
            stage_id=int(r["stage_id"]),
            crop_id=int(r["crop_id"]),
            crop_name=r.get("crop_name"),
            stage_name=r["stage_name"],
            start_day=int(r["start_day"]),
            end_day=int(r["end_day"]),
            task=r.get("task"),
        )
        for r in rows
    ]


@router.post("/crop-stages", response_model=CropStageDetailResponse, status_code=status.HTTP_201_CREATED, summary="Create a crop stage")
def create_crop_stage(payload: CropStageCreateUpdateRequest, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Add a growth stage to a crop."""
    crop = db.fetch_one("SELECT crop_id, crop_name FROM crops WHERE crop_id = %s", (payload.crop_id,))
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Crop #{payload.crop_id} not found")

    admin_id = current_admin["farmer_id"]
    query = "INSERT INTO crop_stages (crop_id, stage_name, start_day, end_day, task) VALUES (%s, %s, %s, %s, %s)"
    params = (payload.crop_id, payload.stage_name.strip(), payload.start_day, payload.end_day, payload.task)
    new_id, _ = db.execute_admin_query(query, params, admin_farmer_id=admin_id)

    return CropStageDetailResponse(
        stage_id=new_id,
        crop_id=payload.crop_id,
        crop_name=crop["crop_name"],
        stage_name=payload.stage_name.strip(),
        start_day=payload.start_day,
        end_day=payload.end_day,
        task=payload.task,
    )


@router.put("/crop-stages/{stage_id}", response_model=CropStageDetailResponse, summary="Update a crop stage")
def update_crop_stage(stage_id: int, payload: CropStageCreateUpdateRequest, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Update growth stage days and task advisory."""
    stage = db.fetch_one("SELECT stage_id FROM crop_stages WHERE stage_id = %s", (stage_id,))
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Growth stage #{stage_id} not found")

    crop = db.fetch_one("SELECT crop_id, crop_name FROM crops WHERE crop_id = %s", (payload.crop_id,))
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Crop #{payload.crop_id} not found")

    admin_id = current_admin["farmer_id"]
    query = """
        UPDATE crop_stages
        SET crop_id = %s, stage_name = %s, start_day = %s, end_day = %s, task = %s
        WHERE stage_id = %s
    """
    params = (payload.crop_id, payload.stage_name.strip(), payload.start_day, payload.end_day, payload.task, stage_id)
    db.execute_admin_query(query, params, admin_farmer_id=admin_id)

    return CropStageDetailResponse(
        stage_id=stage_id,
        crop_id=payload.crop_id,
        crop_name=crop["crop_name"],
        stage_name=payload.stage_name.strip(),
        start_day=payload.start_day,
        end_day=payload.end_day,
        task=payload.task,
    )


@router.delete("/crop-stages/{stage_id}", summary="Delete a crop stage")
def delete_crop_stage(stage_id: int, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Remove a growth stage."""
    stage = db.fetch_one("SELECT stage_id FROM crop_stages WHERE stage_id = %s", (stage_id,))
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Growth stage #{stage_id} not found")

    admin_id = current_admin["farmer_id"]
    db.execute_admin_query("DELETE FROM crop_stages WHERE stage_id = %s", (stage_id,), admin_farmer_id=admin_id)
    return {"message": f"Growth stage #{stage_id} deleted successfully"}


# =============================================================================
# 3. Fertilizers Master Data CRUD
# =============================================================================

@router.get("/fertilizers", response_model=List[FertilizerDetailResponse], summary="List all fertilizers")
def list_fertilizers(_: Dict[str, Any] = Depends(require_admin)):
    """Retrieve catalog of available fertilizers with NPK content and rates."""
    rows = db.fetch_all("SELECT fert_id, name, n_pct, p_pct, k_pct, price_per_kg FROM fertilizers ORDER BY name ASC")
    return [
        FertilizerDetailResponse(
            fert_id=int(r["fert_id"]),
            name=r["name"],
            n_pct=float(r["n_pct"]),
            p_pct=float(r["p_pct"]),
            k_pct=float(r["k_pct"]),
            price_per_kg=float(r["price_per_kg"]) if r.get("price_per_kg") is not None else None,
        )
        for r in rows
    ]


@router.post("/fertilizers", response_model=FertilizerDetailResponse, status_code=status.HTTP_201_CREATED, summary="Create a fertilizer")
def create_fertilizer(payload: FertilizerCreateUpdateRequest, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Add a new fertilizer with N-P-K percentages and cost."""
    existing = db.fetch_one("SELECT fert_id FROM fertilizers WHERE LOWER(name) = LOWER(%s)", (payload.name.strip(),))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Fertilizer '{payload.name}' already exists")

    admin_id = current_admin["farmer_id"]
    query = "INSERT INTO fertilizers (name, n_pct, p_pct, k_pct, price_per_kg) VALUES (%s, %s, %s, %s, %s)"
    params = (payload.name.strip(), payload.n_pct, payload.p_pct, payload.k_pct, payload.price_per_kg)
    new_id, _ = db.execute_admin_query(query, params, admin_farmer_id=admin_id)

    return FertilizerDetailResponse(
        fert_id=new_id,
        name=payload.name.strip(),
        n_pct=payload.n_pct,
        p_pct=payload.p_pct,
        k_pct=payload.k_pct,
        price_per_kg=payload.price_per_kg,
    )


@router.put("/fertilizers/{fert_id}", response_model=FertilizerDetailResponse, summary="Update a fertilizer")
def update_fertilizer(fert_id: int, payload: FertilizerCreateUpdateRequest, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Update fertilizer NPK percentages and market price per kg."""
    fert = db.fetch_one("SELECT fert_id FROM fertilizers WHERE fert_id = %s", (fert_id,))
    if not fert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fertilizer #{fert_id} not found")

    admin_id = current_admin["farmer_id"]
    query = "UPDATE fertilizers SET name = %s, n_pct = %s, p_pct = %s, k_pct = %s, price_per_kg = %s WHERE fert_id = %s"
    params = (payload.name.strip(), payload.n_pct, payload.p_pct, payload.k_pct, payload.price_per_kg, fert_id)
    db.execute_admin_query(query, params, admin_farmer_id=admin_id)

    return FertilizerDetailResponse(
        fert_id=fert_id,
        name=payload.name.strip(),
        n_pct=payload.n_pct,
        p_pct=payload.p_pct,
        k_pct=payload.k_pct,
        price_per_kg=payload.price_per_kg,
    )


@router.delete("/fertilizers/{fert_id}", summary="Delete a fertilizer")
def delete_fertilizer(fert_id: int, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Delete a fertilizer."""
    fert = db.fetch_one("SELECT fert_id, name FROM fertilizers WHERE fert_id = %s", (fert_id,))
    if not fert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fertilizer #{fert_id} not found")

    admin_id = current_admin["farmer_id"]
    db.execute_admin_query("DELETE FROM fertilizers WHERE fert_id = %s", (fert_id,), admin_farmer_id=admin_id)
    return {"message": f"Fertilizer '{fert['name']}' deleted successfully"}


# =============================================================================
# 4. Crop Rotation Rules CRUD
# =============================================================================

@router.get("/rotation-rules", response_model=List[RotationRuleDetailResponse], summary="List crop rotation rules")
def list_rotation_rules(_: Dict[str, Any] = Depends(require_admin)):
    """Retrieve succession crop rules."""
    query = """
        SELECT
            r.rule_id,
            r.previous_crop_id,
            cp.crop_name AS previous_crop_name,
            r.recommended_crop_id,
            cr.crop_name AS recommended_crop_name,
            r.reason
        FROM crop_rotation_rules r
        JOIN crops cp ON r.previous_crop_id = cp.crop_id
        JOIN crops cr ON r.recommended_crop_id = cr.crop_id
        ORDER BY cp.crop_name ASC, cr.crop_name ASC
    """
    rows = db.fetch_all(query)
    return [
        RotationRuleDetailResponse(
            rule_id=int(r["rule_id"]),
            previous_crop_id=int(r["previous_crop_id"]),
            previous_crop_name=r["previous_crop_name"],
            recommended_crop_id=int(r["recommended_crop_id"]),
            recommended_crop_name=r["recommended_crop_name"],
            reason=r.get("reason"),
        )
        for r in rows
    ]


@router.post("/rotation-rules", response_model=RotationRuleDetailResponse, status_code=status.HTTP_201_CREATED, summary="Create a rotation rule")
def create_rotation_rule(payload: RotationRuleCreateUpdateRequest, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Add a new crop succession rule."""
    cp = db.fetch_one("SELECT crop_id, crop_name FROM crops WHERE crop_id = %s", (payload.previous_crop_id,))
    cr = db.fetch_one("SELECT crop_id, crop_name FROM crops WHERE crop_id = %s", (payload.recommended_crop_id,))
    if not cp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Previous crop #{payload.previous_crop_id} not found")
    if not cr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recommended crop #{payload.recommended_crop_id} not found")

    admin_id = current_admin["farmer_id"]
    query = "INSERT INTO crop_rotation_rules (previous_crop_id, recommended_crop_id, reason) VALUES (%s, %s, %s)"
    params = (payload.previous_crop_id, payload.recommended_crop_id, payload.reason)
    new_id, _ = db.execute_admin_query(query, params, admin_farmer_id=admin_id)

    return RotationRuleDetailResponse(
        rule_id=new_id,
        previous_crop_id=payload.previous_crop_id,
        previous_crop_name=cp["crop_name"],
        recommended_crop_id=payload.recommended_crop_id,
        recommended_crop_name=cr["crop_name"],
        reason=payload.reason,
    )


@router.put("/rotation-rules/{rule_id}", response_model=RotationRuleDetailResponse, summary="Update a rotation rule")
def update_rotation_rule(rule_id: int, payload: RotationRuleCreateUpdateRequest, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Update rotation rule crops or reason."""
    rule = db.fetch_one("SELECT rule_id FROM crop_rotation_rules WHERE rule_id = %s", (rule_id,))
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rotation rule #{rule_id} not found")

    cp = db.fetch_one("SELECT crop_id, crop_name FROM crops WHERE crop_id = %s", (payload.previous_crop_id,))
    cr = db.fetch_one("SELECT crop_id, crop_name FROM crops WHERE crop_id = %s", (payload.recommended_crop_id,))
    if not cp or not cr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified crops not found")

    admin_id = current_admin["farmer_id"]
    query = """
        UPDATE crop_rotation_rules
        SET previous_crop_id = %s, recommended_crop_id = %s, reason = %s
        WHERE rule_id = %s
    """
    params = (payload.previous_crop_id, payload.recommended_crop_id, payload.reason, rule_id)
    db.execute_admin_query(query, params, admin_farmer_id=admin_id)

    return RotationRuleDetailResponse(
        rule_id=rule_id,
        previous_crop_id=payload.previous_crop_id,
        previous_crop_name=cp["crop_name"],
        recommended_crop_id=payload.recommended_crop_id,
        recommended_crop_name=cr["crop_name"],
        reason=payload.reason,
    )


@router.delete("/rotation-rules/{rule_id}", summary="Delete a rotation rule")
def delete_rotation_rule(rule_id: int, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Remove a crop rotation rule."""
    rule = db.fetch_one("SELECT rule_id FROM crop_rotation_rules WHERE rule_id = %s", (rule_id,))
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rotation rule #{rule_id} not found")

    admin_id = current_admin["farmer_id"]
    db.execute_admin_query("DELETE FROM crop_rotation_rules WHERE rule_id = %s", (rule_id,), admin_farmer_id=admin_id)
    return {"message": f"Rotation rule #{rule_id} deleted successfully"}


# =============================================================================
# 5. Market Prices Admin & Upsert
# =============================================================================

@router.get("/market-prices", response_model=List[MarketPriceHistoryPoint], summary="List market prices")
def list_admin_market_prices(
    crop_id: Optional[int] = Query(None),
    district: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: Dict[str, Any] = Depends(require_admin),
):
    """Retrieve market prices with pagination and optional filters."""
    where_clauses = []
    params = []
    if crop_id is not None:
        where_clauses.append("mp.crop_id = %s")
        params.append(crop_id)
    if district and district.lower() != "all":
        where_clauses.append("mp.district = %s")
        params.append(district)

    query = """
        SELECT mp.price_id, mp.crop_id, c.crop_name, mp.district, mp.price_per_quintal, mp.price_date
        FROM market_prices mp
        JOIN crops c ON mp.crop_id = c.crop_id
    """
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY mp.price_date DESC, mp.price_id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

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


@router.post("/market-prices", summary="Insert or update mandi market price")
def upsert_market_price(payload: MarketPriceCreateRequest, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Upsert market price using INSERT ... ON DUPLICATE KEY UPDATE.

    Guarantees no duplicates on (crop_id, district, price_date).
    Triggers automatic price surge alert if price increased >= 10%.
    """
    crop = db.fetch_one("SELECT crop_id FROM crops WHERE crop_id = %s", (payload.crop_id,))
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Crop #{payload.crop_id} not found")

    admin_id = current_admin["farmer_id"]
    query = """
        INSERT INTO market_prices (crop_id, district, price_per_quintal, price_date)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            price_per_quintal = VALUES(price_per_quintal)
    """
    params = (payload.crop_id, payload.district.strip(), payload.price_per_quintal, payload.price_date)
    last_id, row_count = db.execute_admin_query(query, params, admin_farmer_id=admin_id)

    return {
        "message": "Market price recorded successfully",
        "crop_id": payload.crop_id,
        "district": payload.district.strip(),
        "price_per_quintal": payload.price_per_quintal,
        "price_date": payload.price_date,
    }


@router.delete("/market-prices/{price_id}", summary="Delete a market price entry")
def delete_market_price(price_id: int, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Delete a price entry by price_id."""
    existing = db.fetch_one("SELECT price_id FROM market_prices WHERE price_id = %s", (price_id,))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Market price record #{price_id} not found")

    admin_id = current_admin["farmer_id"]
    db.execute_admin_query("DELETE FROM market_prices WHERE price_id = %s", (price_id,), admin_farmer_id=admin_id)
    return {"message": f"Market price #{price_id} deleted successfully"}


# =============================================================================
# 6. Translations CRUD
# =============================================================================

@router.get("/translations", response_model=List[TranslationItem], summary="List UI translations")
def list_translations(
    lang: Optional[str] = Query(None),
    key: Optional[str] = Query(None),
    _: Dict[str, Any] = Depends(require_admin),
):
    """List localized strings."""
    where_clauses = []
    params = []
    if lang:
        where_clauses.append("lang = %s")
        params.append(lang)
    if key:
        where_clauses.append("text_key LIKE %s")
        params.append(f"%{key}%")

    query = "SELECT text_key, lang, text FROM translations"
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY text_key ASC, lang ASC"

    rows = db.fetch_all(query, tuple(params))
    return [
        TranslationItem(
            text_key=r["text_key"],
            lang=r["lang"],
            text=r["text"],
        )
        for r in rows
    ]


@router.post("/translations", response_model=TranslationItem, summary="Create or upsert translation")
def upsert_translation(payload: TranslationCreateUpdateRequest, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Create or update a localized text string."""
    admin_id = current_admin["farmer_id"]
    query = """
        INSERT INTO translations (text_key, lang, text)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE text = VALUES(text)
    """
    params = (payload.text_key.strip(), payload.lang, payload.text.strip())
    db.execute_admin_query(query, params, admin_farmer_id=admin_id)

    return TranslationItem(
        text_key=payload.text_key.strip(),
        lang=payload.lang,
        text=payload.text.strip(),
    )


@router.delete("/translations/{text_key}/{lang}", summary="Delete translation")
def delete_translation(text_key: str, lang: str, current_admin: Dict[str, Any] = Depends(require_admin)):
    """Remove a translation key."""
    admin_id = current_admin["farmer_id"]
    deleted = db.execute_admin_query(
        "DELETE FROM translations WHERE text_key = %s AND lang = %s",
        (text_key, lang),
        admin_farmer_id=admin_id,
    )[1]
    if deleted == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation key not found")
    return {"message": f"Translation for '{text_key}' ({lang}) deleted"}


# =============================================================================
# 7. Audit Log Viewer
# =============================================================================

@router.get("/audit-log", response_model=List[AuditLogItem], summary="View admin audit trail")
def get_audit_log(
    table: Optional[str] = Query(None, description="Filter by table name (e.g. crops, market_prices)"),
    record_id: Optional[int] = Query(None, description="Filter by primary key record ID"),
    limit: int = Query(50, ge=1, le=200, description="Max entries to return"),
    _: Dict[str, Any] = Depends(require_admin),
):
    """Retrieve audit log rows generated automatically by database triggers.

    Ordered newest first.
    """
    where_clauses = []
    params = []
    if table:
        where_clauses.append("table_name = %s")
        params.append(table.strip())
    if record_id is not None:
        where_clauses.append("record_id = %s")
        params.append(record_id)

    query = """
        SELECT log_id, table_name, record_id, action, old_data, new_data, changed_by, changed_at
        FROM admin_audit_log
    """
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY changed_at DESC, log_id DESC LIMIT %s"
    params.append(limit)

    rows = db.fetch_all(query, tuple(params))
    items = []
    for r in rows:
        old_val = r.get("old_data")
        new_val = r.get("new_data")
        if isinstance(old_val, str):
            try:
                old_val = json.loads(old_val)
            except Exception:
                pass
        if isinstance(new_val, str):
            try:
                new_val = json.loads(new_val)
            except Exception:
                pass

        items.append(
            AuditLogItem(
                log_id=int(r["log_id"]),
                table_name=r["table_name"],
                record_id=int(r["record_id"]),
                action=r["action"],
                old_data=old_val,
                new_data=new_val,
                changed_by=r["changed_by"],
                changed_at=r["changed_at"],
            )
        )
    return items


# =============================================================================
# 8. User Management (Active Toggle & User Listing)
# =============================================================================

@router.get("/users", response_model=List[FarmerProfileResponse], summary="List all registered farmers")
def list_users(_: Dict[str, Any] = Depends(require_admin)):
    """List all farmer accounts, including active status, role, and last login timestamp."""
    rows = db.fetch_all("""
        SELECT farmer_id, name, phone, email, district, village, language, role, is_active, created_at, last_login
        FROM farmers
        ORDER BY created_at DESC
    """)
    return [
        FarmerProfileResponse(
            farmer_id=int(r["farmer_id"]),
            name=r["name"],
            phone=r["phone"],
            email=r["email"],
            district=r["district"],
            village=r.get("village"),
            language=r.get("language") or "en",
            role=r.get("role") or "farmer",
            is_active=bool(r.get("is_active", True)),
            created_at=r["created_at"],
            last_login=r.get("last_login"),
        )
        for r in rows
    ]


@router.patch("/users/{user_id}/active", summary="Enable or disable a user account")
def update_user_status(
    user_id: int,
    payload: UserActiveUpdateRequest,
    current_admin: Dict[str, Any] = Depends(require_admin),
):
    """Enable or disable a farmer's login access."""
    user = db.fetch_one("SELECT farmer_id, name FROM farmers WHERE farmer_id = %s", (user_id,))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User #{user_id} not found")

    if user_id == current_admin["farmer_id"] and not payload.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate your own admin account")

    admin_id = current_admin["farmer_id"]
    query = "UPDATE farmers SET is_active = %s WHERE farmer_id = %s"
    db.execute_admin_query(query, (1 if payload.is_active else 0, user_id), admin_farmer_id=admin_id)

    status_str = "activated" if payload.is_active else "deactivated"
    return {"message": f"User '{user['name']}' #{user_id} successfully {status_str}", "is_active": payload.is_active}


# =============================================================================
# 9. CSV Bulk Upload for Market Prices
# =============================================================================

@router.post("/market-prices/upload-csv", response_model=CsvUploadResponse, summary="Bulk upload mandi market prices via CSV")
async def upload_market_prices_csv(
    file: UploadFile = File(...),
    current_admin: Dict[str, Any] = Depends(require_admin),
):
    """Bulk import market prices from CSV with row-by-row error reporting.

    Expected CSV columns: crop_name, district, price_per_quintal, price_date
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must be a CSV (.csv)")

    content_bytes = await file.read()
    try:
        content_text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        content_text = content_bytes.decode("latin-1")

    reader = csv.DictReader(io.StringIO(content_text))
    if not reader.fieldnames:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is empty or missing header")

    # Normalize header names
    field_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
    required = ["crop_name", "district", "price_per_quintal", "price_date"]
    for req in required:
        if req not in field_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV missing required column: '{req}'. Found columns: {reader.fieldnames}",
            )

    # Build crop lookup cache: lowercase crop_name -> crop_id
    crop_rows = db.fetch_all("SELECT crop_id, LOWER(crop_name) AS crop_name_lower FROM crops")
    crops_map = {r["crop_name_lower"]: int(r["crop_id"]) for r in crop_rows}

    total_rows = 0
    imported = 0
    errors: List[Dict[str, Any]] = []
    admin_id = current_admin["farmer_id"]

    for row_idx, row in enumerate(reader, start=2):  # line 2 is first data row
        total_rows += 1
        crop_name_val = (row.get(field_map["crop_name"]) or "").strip()
        district_val = (row.get(field_map["district"]) or "").strip()
        price_str = (row.get(field_map["price_per_quintal"]) or "").strip()
        date_str = (row.get(field_map["price_date"]) or "").strip()

        if not crop_name_val or not district_val or not price_str or not date_str:
            errors.append({"row": row_idx, "error": "Missing one or more required fields"})
            continue

        crop_id = crops_map.get(crop_name_val.lower())
        if not crop_id:
            errors.append({"row": row_idx, "error": f"Crop '{crop_name_val}' not found in database"})
            continue

        try:
            price_val = float(price_str)
            if price_val <= 0:
                errors.append({"row": row_idx, "error": f"Price must be positive, got {price_val}"})
                continue
        except ValueError:
            errors.append({"row": row_idx, "error": f"Invalid price format: '{price_str}'"})
            continue

        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            errors.append({"row": row_idx, "error": f"Invalid date format: '{date_str}' (expected YYYY-MM-DD)"})
            continue

        # Execute Upsert
        query = """
            INSERT INTO market_prices (crop_id, district, price_per_quintal, price_date)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE price_per_quintal = VALUES(price_per_quintal)
        """
        try:
            db.execute_admin_query(query, (crop_id, district_val, price_val, parsed_date), admin_farmer_id=admin_id)
            imported += 1
        except Exception as exc:
            errors.append({"row": row_idx, "error": str(exc)})

    return CsvUploadResponse(
        total_rows=total_rows,
        imported=imported,
        errors=errors,
    )
