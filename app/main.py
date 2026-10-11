"""AgriPredict FastAPI Main Application Entry Point."""

import asyncio
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional
from urllib.parse import quote
from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import mysql.connector

from app import db
from app.db import DatabaseProcedureError
from app.dependencies import require_admin
from app.i18n_defaults import DEFAULT_TRANSLATIONS
from app.security import decode_access_token, get_safe_redirect_url
from app.routers import (
    admin,
    advisory,
    alerts,
    auth,
    cycles,
    dashboard,
    expenses,
    farms,
    geo,
    prices,
    public,
    recommendations,
    soil_tests,
    weather,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agripredict")


def check_translation_encoding() -> Dict[str, Any]:
    """Check if any mr/hi translation text has a hex value that does not begin with E0A4 or E0A5.

    Valid UTF-8 Devanagari characters start with hex prefix E0A4 or E0A5.
    Corrupted imports (e.g. windows-1252 to UTF-8 mojibake) start with C393 or other bytes.
    """
    try:
        query = """
            SELECT COUNT(*) AS cnt
            FROM translations
            WHERE lang IN ('mr', 'hi')
              AND text IS NOT NULL
              AND TRIM(text) != ''
              AND HEX(SUBSTR(TRIM(text), 1, 1)) NOT LIKE 'E0A4%'
              AND HEX(SUBSTR(TRIM(text), 1, 1)) NOT LIKE 'E0A5%'
        """
        row = db.fetch_one(query)
        corrupted_count = 0
        if row:
            corrupted_count = int(row.get("cnt", 0) if isinstance(row, dict) else row[0])

        is_corrupted = corrupted_count > 0
        return {
            "status": "corrupted" if is_corrupted else "valid",
            "corrupted_count": corrupted_count,
        }
    except Exception as exc:
        logger.warning("Could not verify translation encoding: %s", exc)
        return {
            "status": "unknown",
            "corrupted_count": 0,
            "error": str(exc),
        }


async def run_daily_task_alerts_job():
    """Background task calling generate_task_alerts(2) once a day as a fallback.

    Ensures farmers receive upcoming task notifications even if the MySQL event scheduler is off.
    """
    while True:
        try:
            logger.info("Executing background task alerts generator (fallback job)...")
            db.call_procedure("generate_task_alerts", (2,))
        except Exception as e:
            logger.warning("Background task alerts generator encountered an issue: %s", e)

        # Wait 24 hours (86,400 seconds)
        await asyncio.sleep(86400)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown background tasks."""
    # Check translation encoding integrity at startup
    encoding_info = check_translation_encoding()
    if encoding_info.get("status") == "corrupted":
        logger.warning(
            "WARNING: Detected %d mr/hi translations with invalid Devanagari encoding (hex does not begin with E0A4 or E0A5). A re-import with utf8mb4 encoding is required.",
            encoding_info.get("corrupted_count", 0),
        )

    bg_task = asyncio.create_task(run_daily_task_alerts_job())
    yield
    bg_task.cancel()
    try:
        await bg_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="AgriPredict API",
    description="Smart Agriculture Management, Crop Recommendation, Advisory & Alerts Backend (DBMS Project)",
    version="4.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers for SQLSTATE 45000 errors
@app.exception_handler(DatabaseProcedureError)
def db_procedure_error_handler(request: Request, exc: DatabaseProcedureError):
    """Map SQLSTATE 45000 errors from procedures and triggers to HTTP 400 Bad Request."""
    if exc.sqlstate == "45000" or getattr(exc, "sqlstate", None) == "45000":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.message},
    )


@app.exception_handler(mysql.connector.Error)
def mysql_error_handler(request: Request, exc: mysql.connector.Error):
    """Map MySQL trigger/procedure SQLSTATE 45000 errors to HTTP 400 Bad Request."""
    if getattr(exc, "sqlstate", None) == "45000":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.msg},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


# Include Routers
app.include_router(auth.router)
app.include_router(farms.router)
app.include_router(soil_tests.router)
app.include_router(weather.router)
app.include_router(recommendations.router)
app.include_router(dashboard.router)
app.include_router(cycles.router)
app.include_router(expenses.router)
app.include_router(advisory.router)
app.include_router(alerts.router)
app.include_router(prices.router)
app.include_router(admin.router)
app.include_router(geo.router)
app.include_router(public.router)


def _is_valid_devanagari_prefix(text: str) -> bool:
    """Check if the text begins with valid Devanagari bytes (E0A4 or E0A5)."""
    if not text:
        return False
    s = text.strip()
    if not s:
        return False
    h = s.encode("utf-8")[:2].hex().upper()
    return h in ("E0A4", "E0A5")


@app.get("/i18n/{lang}", tags=["General"], summary="Fetch translation dictionary with English fallback")
def get_i18n_translations(lang: Literal["en", "mr", "hi"] = "en"):
    """Fetch all keys as a JSON object, falling back to English for any missing key."""
    try:
        # 1. Baseline: seed from default translations dictionary
        result = DEFAULT_TRANSLATIONS.get("en", {}).copy()
        if lang != "en":
            result.update(DEFAULT_TRANSLATIONS.get(lang, {}))

        # 2. Overlay English translations from DB
        en_rows = db.fetch_all("SELECT text_key, text FROM translations WHERE lang = 'en'")
        for r in en_rows:
            if r.get("text"):
                result[r["text_key"]] = r["text"]

        # 3. Overlay target language translations from DB
        if lang != "en":
            target_rows = db.fetch_all("SELECT text_key, text FROM translations WHERE lang = %s", (lang,))
            for r in target_rows:
                txt = r.get("text")
                if txt:
                    # Only accept from DB if it is valid Devanagari (not corrupted mojibake like C393)
                    if _is_valid_devanagari_prefix(txt):
                        result[r["text_key"]] = txt
                    else:
                        # Ensure clean default is preserved
                        clean_default = DEFAULT_TRANSLATIONS.get(lang, {}).get(r["text_key"])
                        if clean_default:
                            result[r["text_key"]] = clean_default

        return result
    except Exception as e:
        logger.warning("Could not fetch i18n translations: %s", e)
        fallback = DEFAULT_TRANSLATIONS.get("en", {}).copy()
        if lang != "en":
            fallback.update(DEFAULT_TRANSLATIONS.get(lang, {}))
        return fallback


@app.get("/translations", tags=["General"], summary="Fetch translations dictionary for UI (alias)")
def get_translations(lang: Literal["en", "mr", "hi"] = "en"):
    """Fetch multilingual translation dictionary delegating to i18n."""
    return get_i18n_translations(lang)


@app.get("/crops/localized", tags=["General"], summary="List crops with localized names from crop_localized_view")
def get_localized_crops(lang: Literal["en", "mr", "hi"] = "en"):
    """Fetch localized crop names using crop_localized_view with fallback to English."""
    try:
        rows = db.fetch_all("""
            SELECT cl.crop_id, cl.crop_name, cl.lang, cl.localized_name, c.duration_days
            FROM crop_localized_view cl
            JOIN crops c ON cl.crop_id = c.crop_id
            WHERE cl.lang = %s
            ORDER BY cl.localized_name ASC
        """, (lang,))
        if not rows and lang != "en":
            rows = db.fetch_all("""
                SELECT cl.crop_id, cl.crop_name, cl.lang, cl.localized_name, c.duration_days
                FROM crop_localized_view cl
                JOIN crops c ON cl.crop_id = c.crop_id
                WHERE cl.lang = 'en'
                ORDER BY cl.crop_name ASC
            """)
        # Ensure Devanagari encoding integrity for mr/hi
        if lang in ("mr", "hi"):
            for r in rows:
                if not _is_valid_devanagari_prefix(r.get("localized_name", "")):
                    k = f"crop_{r['crop_name'].lower().replace(' ', '_')}"
                    clean = DEFAULT_TRANSLATIONS.get(lang, {}).get(k)
                    if clean:
                        r["localized_name"] = clean
        return rows
    except Exception as e:
        logger.warning("Could not fetch localized crops: %s", e)
        return []


# Mount Static Files and UI Pages
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", tags=["General"])
def root_info(request: Request):
    """Serve public home page (static/index.html) or return JSON metadata if requested."""
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return {
            "project": "AgriPredict",
            "description": "Smart Agriculture Recommendation Engine & Farm Management",
            "version": "5.0.0",
            "docs_url": "/docs",
            "ui_url": "/ui/dashboard",
            "status": "online",
        }
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file, media_type="text/html; charset=utf-8")
    return RedirectResponse(url="/ui/dashboard")


def check_ui_auth(request: Request) -> Optional[RedirectResponse]:
    """Check if the incoming request has a valid session token (in Authorization header or cookie).

    If missing, invalid, or expired, returns a 302 redirect to /ui/login?next=<path>.
    """
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = request.cookies.get("agri_token") or request.cookies.get("access_token")

    path = request.url.path
    if request.url.query:
        path += f"?{request.url.query}"

    if not token:
        return RedirectResponse(
            url=f"/ui/login?next={quote(path, safe='')}",
            status_code=status.HTTP_302_FOUND,
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        response = RedirectResponse(
            url=f"/ui/login?next={quote(path, safe='')}",
            status_code=status.HTTP_302_FOUND,
        )
        response.delete_cookie("agri_token", path="/")
        return response

    return None


@app.get("/ui/login", tags=["Frontend"])
def ui_login(request: Request):
    """Serve Login Page, or redirect if already authenticated."""
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = request.cookies.get("agri_token") or request.cookies.get("access_token")

    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            next_url = request.query_params.get("next")
            safe_target = get_safe_redirect_url(next_url, default="/ui/dashboard")
            return RedirectResponse(url=safe_target, status_code=status.HTTP_302_FOUND)

    return FileResponse(STATIC_DIR / "login.html")


@app.get("/ui/register", tags=["Frontend"])
def ui_register(request: Request):
    """Serve Register Page, or redirect if already authenticated."""
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = request.cookies.get("agri_token") or request.cookies.get("access_token")

    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            next_url = request.query_params.get("next")
            safe_target = get_safe_redirect_url(next_url, default="/ui/dashboard")
            return RedirectResponse(url=safe_target, status_code=status.HTTP_302_FOUND)

    return FileResponse(STATIC_DIR / "register.html")


@app.get("/ui/dashboard", tags=["Frontend"])
def ui_dashboard(request: Request):
    """Serve Dashboard Page with auth verification."""
    auth_redirect = check_ui_auth(request)
    if auth_redirect:
        return auth_redirect
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/ui/farms", tags=["Frontend"])
def ui_farms(request: Request):
    """Serve Farms Management Page with auth verification."""
    auth_redirect = check_ui_auth(request)
    if auth_redirect:
        return auth_redirect
    return FileResponse(STATIC_DIR / "farms.html")


@app.get("/ui/cycle-detail", tags=["Frontend"])
def ui_cycle_detail(request: Request):
    """Serve Cycle Detail Page with auth verification."""
    auth_redirect = check_ui_auth(request)
    if auth_redirect:
        return auth_redirect
    return FileResponse(STATIC_DIR / "cycle_detail.html")


@app.get("/ui/alerts", tags=["Frontend"])
def ui_alerts(request: Request):
    """Serve Notifications / Alerts Page with auth verification."""
    auth_redirect = check_ui_auth(request)
    if auth_redirect:
        return auth_redirect
    return FileResponse(STATIC_DIR / "alerts.html")


@app.get("/ui/prices", tags=["Frontend"])
def ui_prices(request: Request):
    """Serve Market Prices & Trends Page with auth verification."""
    auth_redirect = check_ui_auth(request)
    if auth_redirect:
        return auth_redirect
    return FileResponse(STATIC_DIR / "prices.html")


@app.get("/ui/admin", tags=["Frontend"])
def ui_admin(request: Request):
    """Serve Admin Management Control Center Page with auth verification."""
    auth_redirect = check_ui_auth(request)
    if auth_redirect:
        return auth_redirect
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint to test API, database pool availability, and translation encoding."""
    db_status = "unknown"
    try:
        row = db.fetch_one("SELECT 1 AS ok")
        if row and (row.get("ok") == 1 or row[0] == 1):
            db_status = "connected"
    except Exception as e:
        db_status = f"disconnected ({e})"

    encoding_info = check_translation_encoding()

    return {
        "status": "healthy" if "connected" in db_status else "degraded",
        "database": db_status,
        "translation_encoding": encoding_info["status"],
        "corrupted_translations": encoding_info["corrupted_count"],
    }


@app.get(
    "/admin/overview",
    tags=["Admin"],
    summary="Admin-only system overview",
)
def admin_overview(admin_farmer: Dict[str, Any] = Depends(require_admin)):
    """Admin-protected endpoint demonstrating the require_admin role check.

    Returns summary counts of registered farmers and farms.
    """
    farmer_count_row = db.fetch_one("SELECT COUNT(*) AS total FROM farmers")
    farm_count_row = db.fetch_one("SELECT COUNT(*) AS total FROM farms")

    total_farmers = farmer_count_row.get("total") if isinstance(farmer_count_row, dict) else farmer_count_row[0]
    total_farms = farm_count_row.get("total") if isinstance(farm_count_row, dict) else farm_count_row[0]

    return {
        "message": "Welcome to the AgriPredict Administrator Panel",
        "admin": {
            "farmer_id": admin_farmer["farmer_id"],
            "name": admin_farmer["name"],
            "role": admin_farmer["role"],
        },
        "statistics": {
            "total_farmers": total_farmers,
            "total_farms": total_farms,
        },
    }
