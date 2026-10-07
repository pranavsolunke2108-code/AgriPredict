"""AgriPredict FastAPI Main Application Entry Point."""

import asyncio
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import Any, Dict, Literal
from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import mysql.connector

from app import db
from app.db import DatabaseProcedureError
from app.dependencies import require_admin
from app.routers import (
    admin,
    advisory,
    alerts,
    auth,
    cycles,
    dashboard,
    expenses,
    farms,
    prices,
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


@app.get("/i18n/{lang}", tags=["General"], summary="Fetch translation dictionary with English fallback")
def get_i18n_translations(lang: Literal["en", "mr", "hi"] = "en"):
    """Fetch all keys as a JSON object, falling back to English for any missing key."""
    try:
        # 1. Baseline: fetch all English translations
        en_rows = db.fetch_all("SELECT text_key, text FROM translations WHERE lang = 'en'")
        result = {r["text_key"]: r["text"] for r in en_rows}

        # 2. Overlay target language translations
        if lang != "en":
            target_rows = db.fetch_all("SELECT text_key, text FROM translations WHERE lang = %s", (lang,))
            for r in target_rows:
                if r.get("text"):
                    result[r["text_key"]] = r["text"]

        return result
    except Exception as e:
        logger.warning("Could not fetch i18n translations: %s", e)
        return {}


@app.get("/translations", tags=["General"], summary="Fetch translations dictionary for UI (alias)")
def get_translations(lang: Literal["en", "mr", "hi"] = "en"):
    """Fetch multilingual translation dictionary delegating to i18n."""
    return get_i18n_translations(lang)


@app.get("/crops/localized", tags=["General"], summary="List crops with localized names from crop_localized_view")
def get_localized_crops(lang: Literal["en", "mr", "hi"] = "en"):
    """Fetch localized crop names using crop_localized_view with fallback to English."""
    try:
        rows = db.fetch_all("""
            SELECT crop_id, crop_name, lang, localized_name
            FROM crop_localized_view
            WHERE lang = %s
            ORDER BY localized_name ASC
        """, (lang,))
        if not rows and lang != "en":
            rows = db.fetch_all("""
                SELECT crop_id, crop_name, lang, localized_name
                FROM crop_localized_view
                WHERE lang = 'en'
                ORDER BY crop_name ASC
            """)
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
    """Root info endpoint: redirects browsers to UI dashboard, or returns API metadata."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse(url="/ui/dashboard")
    return {
        "project": "AgriPredict",
        "description": "Smart Agriculture Recommendation Engine & Farm Management",
        "version": "5.0.0",
        "docs_url": "/docs",
        "ui_url": "/ui/dashboard",
        "status": "online",
    }


@app.get("/ui/login", tags=["Frontend"])
def ui_login():
    """Serve Login Page."""
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/ui/register", tags=["Frontend"])
def ui_register():
    """Serve Register Page."""
    return FileResponse(STATIC_DIR / "register.html")


@app.get("/ui/dashboard", tags=["Frontend"])
def ui_dashboard():
    """Serve Dashboard Page."""
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/ui/farms", tags=["Frontend"])
def ui_farms():
    """Serve Farms Management Page."""
    return FileResponse(STATIC_DIR / "farms.html")


@app.get("/ui/cycle-detail", tags=["Frontend"])
def ui_cycle_detail():
    """Serve Cycle Detail Page."""
    return FileResponse(STATIC_DIR / "cycle_detail.html")


@app.get("/ui/alerts", tags=["Frontend"])
def ui_alerts():
    """Serve Notifications / Alerts Page."""
    return FileResponse(STATIC_DIR / "alerts.html")


@app.get("/ui/prices", tags=["Frontend"])
def ui_prices():
    """Serve Market Prices & Trends Page."""
    return FileResponse(STATIC_DIR / "prices.html")


@app.get("/ui/admin", tags=["Frontend"])
def ui_admin():
    """Serve Admin Management Control Center Page."""
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint to test API and database pool availability."""
    db_status = "unknown"
    try:
        row = db.fetch_one("SELECT 1 AS ok")
        if row and (row.get("ok") == 1 or row[0] == 1):
            db_status = "connected"
    except Exception as e:
        db_status = f"disconnected ({e})"

    return {
        "status": "healthy" if "connected" in db_status else "degraded",
        "database": db_status,
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
