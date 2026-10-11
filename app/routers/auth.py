"""Authentication router: registration, login, and profile retrieval."""

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app import db
from app.dependencies import get_current_farmer
from app.schemas import (
    FarmerAddressUpdateRequest,
    FarmerLoginRequest,
    FarmerRegisterRequest,
    FarmerResponse,
    LanguageUpdateRequest,
    TokenResponse,
)
from app.security import create_access_token, hash_password, verify_password

logger = logging.getLogger("agripredict.auth")
router = APIRouter(tags=["Authentication"])


@router.post(
    "/auth/register",
    response_model=FarmerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new farmer",
)
def register_farmer(payload: FarmerRegisterRequest):
    """Register a new farmer account.

    - Validates name, phone, optional email, password, district, village, and language.
    - Rejects duplicate phone or email addresses.
    - Hashes password using bcrypt.
    - Inserts new record into 'farmers' table via parameterized query.
    """
    # 1. Check for duplicate phone number
    check_phone_query = "SELECT farmer_id FROM farmers WHERE phone = %s LIMIT 1"
    existing_phone = db.fetch_one(check_phone_query, (payload.phone,))
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Phone number '{payload.phone}' is already registered",
        )

    # 2. Check for duplicate email if provided
    if payload.email:
        check_email_query = "SELECT farmer_id FROM farmers WHERE email = %s LIMIT 1"
        existing_email = db.fetch_one(check_email_query, (payload.email,))
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email address '{payload.email}' is already registered",
            )

    # 3. Hash password with bcrypt
    hashed_pw = hash_password(payload.password)

    # 4. Parameterized INSERT into farmers table
    insert_query = """
        INSERT INTO farmers (
            name, phone, email, password_hash, district, village, language, role, is_active
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, 'farmer', 1
        )
    """
    farmer_id = db.execute_insert(
        insert_query,
        (
            payload.name,
            payload.phone,
            payload.email,
            hashed_pw,
            payload.district,
            payload.village,
            payload.language,
        ),
    )

    # 5. Fetch and return created farmer profile
    fetch_query = """
        SELECT farmer_id, name, phone, email, district, village, language, role, is_active, created_at, last_login
        FROM farmers
        WHERE farmer_id = %s
    """
    created_farmer = db.fetch_one(fetch_query, (farmer_id,))
    if not created_farmer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account created but failed to retrieve profile",
        )

    return created_farmer


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Farmer / Admin login",
)
def login(payload: FarmerLoginRequest, response: Response):
    """Authenticate with phone or email and password.

    - Verifies credentials against bcrypt hash.
    - Rejects inactive accounts.
    - Updates farmers.last_login timestamp.
    - Returns a signed JWT access token and sets agri_token cookie.
    """
    identifier = payload.identifier

    # Parameterized query matching either phone or email
    lookup_query = """
        SELECT farmer_id, name, phone, email, password_hash, district, village, language, role, is_active, created_at, last_login
        FROM farmers
        WHERE phone = %s OR email = %s
        LIMIT 1
    """
    farmer = db.fetch_one(lookup_query, (identifier, identifier))

    # Reject if farmer not found or password does not match
    if not farmer or not verify_password(payload.password, farmer["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reject inactive accounts
    if not farmer.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact system administrator.",
        )

    # Update farmers.last_login timestamp
    update_login_query = "UPDATE farmers SET last_login = CURRENT_TIMESTAMP WHERE farmer_id = %s"
    db.execute_update(update_login_query, (farmer["farmer_id"],))

    # Generate JWT token
    token_payload = {
        "sub": str(farmer["farmer_id"]),
        "role": farmer["role"],
        "phone": farmer["phone"],
    }
    access_token = create_access_token(token_payload)

    # Set auth cookie for same-site browser navigation
    response.set_cookie(
        key="agri_token",
        value=access_token,
        path="/",
        samesite="lax",
        httponly=False,
    )

    # Prepare farmer profile without password_hash
    farmer_profile = dict(farmer)
    farmer_profile.pop("password_hash", None)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        farmer=FarmerResponse.model_validate(farmer_profile),
    )


@router.post("/logout", summary="Clear authentication session cookie")
def logout_endpoint(response: Response):
    """Clear the agri_token authentication cookie."""
    response.delete_cookie("agri_token", path="/")
    return {"message": "Logged out successfully"}



@router.get(
    "/me",
    response_model=FarmerResponse,
    summary="Get current farmer profile",
)
@router.get(
    "/auth/me",
    response_model=FarmerResponse,
    include_in_schema=False,
)
def get_my_profile(current_farmer: Dict[str, Any] = Depends(get_current_farmer)):
    """Return the profile of the currently authenticated farmer (requires JWT)."""
    return current_farmer


@router.patch(
    "/me/language",
    response_model=FarmerResponse,
    summary="Save farmer's preferred language",
)
def update_my_language(
    payload: LanguageUpdateRequest,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Save the farmer's language choice in farmers.language."""
    farmer_id = current_farmer["farmer_id"]
    db.execute_update(
        "UPDATE farmers SET language = %s WHERE farmer_id = %s",
        (payload.language, farmer_id),
    )
    updated_farmer = db.fetch_one(
        "SELECT farmer_id, name, phone, email, district, village, language, role, is_active, created_at, last_login "
        "FROM farmers WHERE farmer_id = %s",
        (farmer_id,),
    )
    return FarmerResponse.model_validate(updated_farmer or current_farmer)


@router.patch(
    "/me/address",
    response_model=FarmerResponse,
    summary="Update farmer district and village from location",
)
def update_my_address(
    payload: FarmerAddressUpdateRequest,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Save the farmer's district and village in farmers table."""
    farmer_id = current_farmer["farmer_id"]
    district = payload.district if payload.district is not None else current_farmer.get("district")
    village = payload.village if payload.village is not None else current_farmer.get("village")
    db.execute_update(
        "UPDATE farmers SET district = %s, village = %s WHERE farmer_id = %s",
        (district, village, farmer_id),
    )
    updated_farmer = db.fetch_one(
        "SELECT farmer_id, name, phone, email, district, village, language, role, is_active, created_at, last_login "
        "FROM farmers WHERE farmer_id = %s",
        (farmer_id,),
    )
    return FarmerResponse.model_validate(updated_farmer or current_farmer)

