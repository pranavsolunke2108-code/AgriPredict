"""AgriPredict Public Endpoints.

Provides public, unauthenticated access to:
1. POST /public/quick-recommend - Instant crop recommendation using quick_recommend stored procedure.
2. GET /public/season - Current agricultural season and suitable crops.
3. GET /public/stats - Aggregate platform statistics (no personal farmer data).
"""

from collections import defaultdict
import logging
import time
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app import db
from app.db import DatabaseProcedureError
from app.i18n_defaults import DEFAULT_TRANSLATIONS

logger = logging.getLogger("agripredict.public")

router = APIRouter(prefix="/public", tags=["Public"])


def _is_valid_devanagari(text: str) -> bool:
    if not text:
        return False
    s = text.strip()
    if not s:
        return False
    h = s.encode("utf-8")[:2].hex().upper()
    return h in ("E0A4", "E0A5")


def _get_localized_crop_name(crop_name: str, raw_localized: Optional[str], lang: str) -> str:
    """Return localized crop name, falling back to clean dictionary if DB value is corrupted."""
    if lang in ("mr", "hi"):
        if raw_localized and _is_valid_devanagari(raw_localized):
            return raw_localized
        # Use clean default dictionary
        k = f"crop_{crop_name.lower().replace(' ', '_')}"
        clean = DEFAULT_TRANSLATIONS.get(lang, {}).get(k)
        if clean:
            return clean
    return raw_localized or crop_name


# In-memory IP-based rate limiting: 20 requests per minute
_RATE_LIMIT_MAX_REQUESTS = 20
_RATE_LIMIT_WINDOW_SECONDS = 60
_ip_request_history = defaultdict(list)


def check_ip_rate_limit(client_ip: str) -> None:
    """Enforce rate limit of 20 requests per minute per IP address."""
    now = time.time()
    history = _ip_request_history[client_ip]
    # Prune timestamps older than window
    _ip_request_history[client_ip] = [t for t in history if now - t < _RATE_LIMIT_WINDOW_SECONDS]
    
    if len(_ip_request_history[client_ip]) >= _RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {_RATE_LIMIT_MAX_REQUESTS} requests per minute.",
        )
    _ip_request_history[client_ip].append(now)


def reset_rate_limit() -> None:
    """Clear rate limit history (primarily for automated testing)."""
    _ip_request_history.clear()


class QuickRecommendRequest(BaseModel):
    ph: float = Field(..., description="Soil pH value (0.0 - 14.0)")
    n: float = Field(..., description="Soil Nitrogen (kg/ha >= 0)")
    p: float = Field(..., description="Soil Phosphorus (kg/ha >= 0)")
    k: float = Field(..., description="Soil Potassium (kg/ha >= 0)")
    temperature: float = Field(..., description="Ambient Temperature in °C (-10 to 60)")
    humidity: float = Field(..., description="Relative Humidity percentage (0 - 100)")
    rainfall: float = Field(..., description="30-day rainfall in mm (>= 0)")
    season: Optional[str] = Field(None, description="Agricultural season: 'ALL', 'Kharif', 'Rabi', 'Zaid', or null for auto")
    lang: Optional[Literal["en", "mr", "hi"]] = Field("en", description="Output language for crop names")


class QuickCropScore(BaseModel):
    rank_no: int
    crop_id: int
    crop_name: str
    localized_name: str
    season: str
    suitability: float
    ph_score: float
    temp_score: float
    humidity_score: float
    rain_score: float
    n_score: float
    p_score: float
    k_score: float


@router.post(
    "/quick-recommend",
    response_model=List[QuickCropScore],
    summary="Get instant top-3 crop recommendations without saving data",
)
def quick_recommend(payload: QuickRecommendRequest, request: Request):
    """Calculate the top 3 recommended crops for user-provided parameters.

    - Server-side validates ranges for all parameters.
    - Rate-limits to 20 requests per minute per IP.
    - Parameterized execution of stored procedure quick_recommend.
    - Rounds all score percentages to 1 decimal place.
    - Localizes crop names to requested language.
    - Maps procedure errors (SQLSTATE 45000) to HTTP 400.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    check_ip_rate_limit(client_ip)

    # Server-side Range Validations
    if not (0.0 <= payload.ph <= 14.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pH must be between 0 and 14",
        )
    if payload.n < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nitrogen (N) must be greater than or equal to 0",
        )
    if payload.p < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phosphorus (P) must be greater than or equal to 0",
        )
    if payload.k < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Potassium (K) must be greater than or equal to 0",
        )
    if not (-10.0 <= payload.temperature <= 60.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temperature must be between -10°C and 60°C",
        )
    if not (0.0 <= payload.humidity <= 100.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Humidity must be between 0% and 100%",
        )
    if payload.rainfall < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rainfall must be greater than or equal to 0 mm",
        )

    # Validate season if provided
    season_val = payload.season
    if season_val is not None:
        season_clean = season_val.strip()
        if season_clean.upper() == "ALL":
            season_val = "ALL"
        elif season_clean in ("Kharif", "Rabi", "Zaid"):
            season_val = season_clean
        elif season_clean == "":
            season_val = None
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid season. Allowed values are 'ALL', 'Kharif', 'Rabi', 'Zaid', or null for auto.",
            )

    try:
        # Parameterized CALL quick_recommend(ph, n, p, k, temp, humidity, rain_30d_mm, season)
        raw_results = db.call_procedure(
            "quick_recommend",
            (
                payload.ph,
                payload.n,
                payload.p,
                payload.k,
                payload.temperature,
                payload.humidity,
                payload.rainfall,
                season_val,
            ),
        )
    except DatabaseProcedureError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    except Exception as exc:
        logger.error("Error executing quick_recommend procedure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if not raw_results:
        return []

    # Fetch crop localization mappings
    target_lang = payload.lang or "en"
    localized_map: Dict[int, str] = {}
    try:
        loc_rows = db.fetch_all(
            "SELECT crop_id, localized_name FROM crop_localized_view WHERE lang = %s",
            (target_lang,),
        )
        for r in loc_rows:
            localized_map[r["crop_id"]] = r["localized_name"]
    except Exception as e:
        logger.warning("Could not query crop_localized_view: %s", e)

    output: List[QuickCropScore] = []
    for row in raw_results[:3]:
        crop_id = int(row.get("crop_id", 0))
        crop_name = str(row.get("crop_name", ""))
        raw_loc = localized_map.get(crop_id)
        loc_name = _get_localized_crop_name(crop_name, raw_loc, target_lang)

        output.append(
            QuickCropScore(
                rank_no=int(row.get("rank_no", len(output) + 1)),
                crop_id=crop_id,
                crop_name=crop_name,
                localized_name=loc_name,
                season=str(row.get("season", "")),
                suitability=round(float(row.get("suitability", 0.0)), 1),
                ph_score=round(float(row.get("ph_score", 0.0)), 1),
                temp_score=round(float(row.get("temp_score", 0.0)), 1),
                humidity_score=round(float(row.get("humidity_score", 0.0)), 1),
                rain_score=round(float(row.get("rain_score", 0.0)), 1),
                n_score=round(float(row.get("n_score", 0.0)), 1),
                p_score=round(float(row.get("p_score", 0.0)), 1),
                k_score=round(float(row.get("k_score", 0.0)), 1),
            )
        )

    return output


@router.get(
    "/season",
    summary="Get current agricultural season and crops suitable for sowing now",
)
def get_current_season_crops(lang: Literal["en", "mr", "hi"] = "en"):
    """Return the current season and suitable crops (current season + Annual crops).

    Includes localized names via crop_localized_view.
    """
    # 1. Determine current agricultural season via database function get_season
    season_name = "Kharif"
    try:
        season_row = db.fetch_one("SELECT get_season(CURDATE()) AS season")
        if season_row and season_row.get("season"):
            season_name = season_row["season"]
    except Exception as exc:
        logger.warning("Failed calling get_season function: %s", exc)

    # 2. Fetch crops suitable for sowing now (season_name or 'Annual')
    crops: List[Dict[str, Any]] = []
    try:
        rows = db.fetch_all(
            """
            SELECT c.crop_id, c.crop_name, c.season, c.duration_days,
                   COALESCE(cl.localized_name, c.crop_name) AS localized_name
            FROM crops c
            LEFT JOIN crop_localized_view cl ON c.crop_id = cl.crop_id AND cl.lang = %s
            WHERE c.season = %s OR c.season = 'Annual'
            ORDER BY c.crop_name ASC
            """,
            (lang, season_name),
        )
        for r in rows:
            loc = _get_localized_crop_name(r["crop_name"], r.get("localized_name"), lang)
            crops.append({
                "crop_id": r["crop_id"],
                "crop_name": r["crop_name"],
                "localized_name": loc,
                "season": r["season"],
                "duration_days": r["duration_days"],
            })
    except Exception as exc:
        logger.error("Failed fetching season crops: %s", exc)

    return {
        "season": season_name,
        "crops": crops,
    }


@router.get(
    "/stats",
    summary="Public aggregate statistics counter (no personal data)",
)
def get_public_stats():
    """Return platform aggregate statistics for public display.

    Never exposes personal data or identifiers.
    """
    # Total supported crops
    total_crops = 0
    try:
        c_row = db.fetch_one("SELECT COUNT(*) AS total FROM crops")
        if c_row:
            total_crops = int(c_row.get("total", 0) if isinstance(c_row, dict) else c_row[0])
    except Exception as e:
        logger.warning("Error querying crops count: %s", e)

    # Total recommendations made (from predictions table)
    total_recommendations = 0
    try:
        p_row = db.fetch_one("SELECT COUNT(*) AS total FROM predictions")
        if p_row:
            total_recommendations = int(p_row.get("total", 0) if isinstance(p_row, dict) else p_row[0])
    except Exception as e:
        logger.warning("Error querying predictions count: %s", e)

    # Number of supported languages
    languages_count = 3  # English, Marathi, Hindi

    return {
        "crops_supported": total_crops,
        "languages_supported": languages_count,
        "recommendations_made": total_recommendations,
    }
