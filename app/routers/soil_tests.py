"""Soil tests router: CRUD endpoints strictly scoped to farm ownership."""

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from app import db
from app.dependencies import get_current_farmer
from app.schemas import MessageResponse, SoilTestCreateRequest, SoilTestResponse

logger = logging.getLogger("agripredict.soil_tests")
router = APIRouter(tags=["Soil Tests"])


def verify_farm_ownership(farm_id: int, farmer_id: int) -> Dict[str, Any]:
    """Helper to verify that a farm exists and belongs to the authenticated farmer."""
    query = "SELECT farm_id, farmer_id, farm_name, area_acres FROM farms WHERE farm_id = %s"
    farm = db.fetch_one(query, (farm_id,))
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with ID {farm_id} not found",
        )
    if farm["farmer_id"] != farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access or modify this farm's data",
        )
    return farm


@router.post(
    "/farms/{farm_id}/soil-tests",
    response_model=SoilTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new soil test for a farm",
)
def create_soil_test(
    farm_id: int,
    payload: SoilTestCreateRequest,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Add a soil test result for a farm owned by the authenticated farmer.

    Validates:
    - pH: 0.0 to 14.0
    - moisture: 0.0 to 100.0%
    - N, P, K: >= 0
    """
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    insert_query = """
        INSERT INTO soil_tests (
            farm_id, test_date, nitrogen, phosphorus, potassium, ph, moisture, organic_carbon
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    test_id = db.execute_insert(
        insert_query,
        (
            farm_id,
            payload.test_date,
            payload.nitrogen,
            payload.phosphorus,
            payload.potassium,
            payload.ph,
            payload.moisture,
            payload.organic_carbon,
        ),
    )

    fetch_query = """
        SELECT test_id, farm_id, test_date, nitrogen, phosphorus, potassium, ph, moisture, organic_carbon
        FROM soil_tests
        WHERE test_id = %s
    """
    created_test = db.fetch_one(fetch_query, (test_id,))
    if not created_test:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Soil test record created but could not be retrieved",
        )

    return created_test


@router.get(
    "/farms/{farm_id}/soil-tests",
    response_model=List[SoilTestResponse],
    summary="List soil tests for a farm (latest first)",
)
def list_farm_soil_tests(
    farm_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve all soil tests for a farm owned by the authenticated farmer, newest first."""
    farmer_id = current_farmer["farmer_id"]
    verify_farm_ownership(farm_id, farmer_id)

    query = """
        SELECT test_id, farm_id, test_date, nitrogen, phosphorus, potassium, ph, moisture, organic_carbon
        FROM soil_tests
        WHERE farm_id = %s
        ORDER BY test_date DESC, test_id DESC
    """
    return db.fetch_all(query, (farm_id,))


@router.get(
    "/soil-tests/{test_id}",
    response_model=SoilTestResponse,
    summary="Get details of a specific soil test",
)
def get_soil_test(
    test_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve a specific soil test by ID.

    Ensures the soil test belongs to a farm owned by the calling farmer.
    """
    farmer_id = current_farmer["farmer_id"]

    query = """
        SELECT s.test_id, s.farm_id, s.test_date, s.nitrogen, s.phosphorus, s.potassium,
               s.ph, s.moisture, s.organic_carbon, f.farmer_id
        FROM soil_tests s
        JOIN farms f ON s.farm_id = f.farm_id
        WHERE s.test_id = %s
    """
    test_record = db.fetch_one(query, (test_id,))

    if not test_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil test with ID {test_id} not found",
        )

    if test_record["farmer_id"] != farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this soil test record",
        )

    return test_record


@router.delete(
    "/soil-tests/{test_id}",
    response_model=MessageResponse,
    summary="Delete a soil test",
)
def delete_soil_test(
    test_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Delete a soil test.

    Ensures the soil test belongs to a farm owned by the calling farmer.
    """
    farmer_id = current_farmer["farmer_id"]

    query = """
        SELECT s.test_id, f.farmer_id
        FROM soil_tests s
        JOIN farms f ON s.farm_id = f.farm_id
        WHERE s.test_id = %s
    """
    test_record = db.fetch_one(query, (test_id,))

    if not test_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil test with ID {test_id} not found",
        )

    if test_record["farmer_id"] != farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this soil test record",
        )

    db.execute_update("DELETE FROM soil_tests WHERE test_id = %s", (test_id,))
    return MessageResponse(detail=f"Soil test {test_id} deleted successfully")
