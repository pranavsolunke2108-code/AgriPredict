"""Farms router: CRUD operations strictly scoped to the authenticated farmer."""

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from app import db
from app.dependencies import get_current_farmer
from app.schemas import FarmCreateRequest, FarmResponse, FarmUpdateRequest, MessageResponse

logger = logging.getLogger("agripredict.farms")
router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new farm",
)
def create_farm(
    payload: FarmCreateRequest,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Create a new farm belonging to the logged-in farmer.

    The farmer_id is strictly derived from the JWT session.
    """
    farmer_id = current_farmer["farmer_id"]

    insert_query = """
        INSERT INTO farms (
            farmer_id, farm_name, area_acres, latitude, longitude, soil_type, irrigation
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
    """
    farm_id = db.execute_insert(
        insert_query,
        (
            farmer_id,
            payload.farm_name,
            payload.area_acres,
            payload.latitude,
            payload.longitude,
            payload.soil_type,
            payload.irrigation,
        ),
    )

    fetch_query = """
        SELECT farm_id, farmer_id, farm_name, area_acres, latitude, longitude, soil_type, irrigation
        FROM farms
        WHERE farm_id = %s
    """
    created_farm = db.fetch_one(fetch_query, (farm_id,))
    if not created_farm:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Farm was created but could not be retrieved",
        )

    return created_farm


@router.get(
    "",
    response_model=List[FarmResponse],
    summary="List all farms owned by the authenticated farmer",
)
def list_farms(
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve all farms registered under the logged-in farmer's account."""
    farmer_id = current_farmer["farmer_id"]
    query = """
        SELECT farm_id, farmer_id, farm_name, area_acres, latitude, longitude, soil_type, irrigation
        FROM farms
        WHERE farmer_id = %s
        ORDER BY farm_id ASC
    """
    return db.fetch_all(query, (farmer_id,))


@router.get(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Get details of a specific farm",
)
def get_farm(
    farm_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Fetch details of a single farm.

    Rejects requests if the farm belongs to a different farmer.
    """
    farmer_id = current_farmer["farmer_id"]

    query = """
        SELECT farm_id, farmer_id, farm_name, area_acres, latitude, longitude, soil_type, irrigation
        FROM farms
        WHERE farm_id = %s
    """
    farm = db.fetch_one(query, (farm_id,))

    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with ID {farm_id} not found",
        )

    if farm["farmer_id"] != farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this farm",
        )

    return farm


@router.put(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Update a farm",
)
def update_farm(
    farm_id: int,
    payload: FarmUpdateRequest,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Update details of a farm owned by the authenticated farmer."""
    farmer_id = current_farmer["farmer_id"]

    # Verify existence and ownership
    query = """
        SELECT farm_id, farmer_id, farm_name, area_acres, latitude, longitude, soil_type, irrigation
        FROM farms
        WHERE farm_id = %s
    """
    existing = db.fetch_one(query, (farm_id,))

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with ID {farm_id} not found",
        )

    if existing["farmer_id"] != farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this farm",
        )

    # Merge updated fields
    farm_name = payload.farm_name if payload.farm_name is not None else existing["farm_name"]
    area_acres = payload.area_acres if payload.area_acres is not None else existing["area_acres"]
    latitude = payload.latitude if payload.latitude is not None else existing["latitude"]
    longitude = payload.longitude if payload.longitude is not None else existing["longitude"]
    soil_type = payload.soil_type if payload.soil_type is not None else existing["soil_type"]
    irrigation = payload.irrigation if payload.irrigation is not None else existing["irrigation"]

    update_query = """
        UPDATE farms
        SET farm_name = %s,
            area_acres = %s,
            latitude = %s,
            longitude = %s,
            soil_type = %s,
            irrigation = %s
        WHERE farm_id = %s AND farmer_id = %s
    """
    db.execute_update(
        update_query,
        (farm_name, area_acres, latitude, longitude, soil_type, irrigation, farm_id, farmer_id),
    )

    updated_farm = db.fetch_one(query, (farm_id,))
    return updated_farm


@router.delete(
    "/{farm_id}",
    response_model=MessageResponse,
    summary="Delete a farm",
)
def delete_farm(
    farm_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Delete a farm belonging to the authenticated farmer."""
    farmer_id = current_farmer["farmer_id"]

    # Verify existence and ownership
    check_query = "SELECT farm_id, farmer_id FROM farms WHERE farm_id = %s"
    existing = db.fetch_one(check_query, (farm_id,))

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with ID {farm_id} not found",
        )

    if existing["farmer_id"] != farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this farm",
        )

    delete_query = "DELETE FROM farms WHERE farm_id = %s AND farmer_id = %s"
    db.execute_update(delete_query, (farm_id, farmer_id))

    return MessageResponse(detail=f"Farm with ID {farm_id} deleted successfully")
