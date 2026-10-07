"""FastAPI dependencies for authentication and authorization."""

from typing import Any, Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app import db
from app.security import decode_access_token

# OAuth2 bearer token extractor
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_farmer(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Dependency that extracts and validates the JWT from Authorization header.

    Queries the database using parameterized SQL to fetch the current active farmer.
    Raises 401 Unauthorized if token is missing or invalid.
    Raises 403 Forbidden if account is inactive.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        farmer_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = """
        SELECT farmer_id, name, phone, email, district, village, language, role, is_active, created_at, last_login
        FROM farmers
        WHERE farmer_id = %s
        LIMIT 1
    """
    farmer = db.fetch_one(query, (farmer_id,))

    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Farmer account associated with this token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check active status
    if not farmer.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmer account is inactive. Please contact system administrator.",
        )

    return farmer


def require_admin(current_farmer: Dict[str, Any] = Depends(get_current_farmer)) -> Dict[str, Any]:
    """Dependency that ensures the authenticated farmer has the 'admin' role.

    Raises 403 Forbidden if the user is not an administrator.
    """
    if current_farmer.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Administrator privileges required",
        )
    return current_farmer
