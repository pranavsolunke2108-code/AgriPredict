"""Security utilities: Bcrypt password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt with a secure random salt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generate a signed JWT access token containing arbitrary payload data."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token.

    Returns payload dict if valid, or None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def is_safe_redirect_url(url: Optional[str]) -> bool:
    """Validate that a redirect target is a safe, same-site relative path.

    Rejects external URLs (with schemes like http://, https://), protocol-relative URLs (//example.com),
    and backslashes (\\example.com) that could lead to open redirection vulnerabilities.
    """
    if not url or not isinstance(url, str):
        return False
    # Must start with a single slash and not protocol-relative
    if not url.startswith("/") or url.startswith("//"):
        return False
    # Disallow protocol schemes and backslashes
    if "://" in url or "\\" in url:
        return False
    return True


def get_safe_redirect_url(next_url: Optional[str], default: str = "/ui/dashboard") -> str:
    """Return next_url if it is a safe same-site path, otherwise fallback to default."""
    if next_url and is_safe_redirect_url(next_url):
        return next_url
    return default

