"""Comprehensive tests for bug fixes: Wheat cycle calendar, status card harvest date,

fertilizer advice, protected page redirects, safe next URL validation, and 1-decimal score rounding.
"""

from datetime import date, timedelta
from typing import Dict
import pytest
from fastapi.testclient import TestClient

from app.security import get_safe_redirect_url, is_safe_redirect_url


def get_authenticated_farmer(client: TestClient, phone: str = "9876599991", email: str = "wheat_farmer@example.com") -> Dict[str, str]:
    """Helper to register and login a farmer, returning auth headers."""
    client.post("/auth/register", json={
        "name": "Ramesh Patil",
        "phone": phone,
        "email": email,
        "password": "password123",
        "district": "Pune",
        "village": "Baramati",
    })
    login_resp = client.post("/auth/login", json={
        "identifier": phone,
        "password": "password123",
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. Wheat cycle sown 10 days ago: calendar, status card harvest date, fertilizer
# =============================================================================

def test_wheat_cycle_calendar_and_status(client: TestClient):
    """Create a farm, soil test with low NPK, and a Wheat cycle sown 10 days ago.

    - Calendar returns 5 stages with exactly one 'Current' stage (Germination, days 0-20).
    - Status card on dashboard has a computed expected harvest date and days to harvest.
    - Fertilizer advice returns rows for low-NPK soil.
    """
    headers = get_authenticated_farmer(client, phone="9876599901", email="wheat_test1@example.com")

    # 1. Create a farm
    farm_resp = client.post("/farms", json={
        "farm_name": "Wheat Acre",
        "area_acres": 5.0,
        "soil_type": "Black",
        "irrigation": "Canal",
    }, headers=headers)
    assert farm_resp.status_code == 201
    farm_id = farm_resp.json()["farm_id"]

    # 2. Record a soil test with low NPK (Wheat needs N=120, P=60, K=40)
    soil_resp = client.post(f"/farms/{farm_id}/soil-tests", json={
        "nitrogen": 30.0,
        "phosphorus": 20.0,
        "potassium": 25.0,
        "ph": 6.8,
        "moisture": 50.0,
        "organic_carbon": 0.55,
        "test_date": date.today().isoformat(),
    }, headers=headers)
    assert soil_resp.status_code == 201
    test_id = soil_resp.json()["test_id"]

    # 3. Start a Wheat cycle (crop_id=3, duration=120 days) sown 10 days ago
    sowing_date = (date.today() - timedelta(days=10)).isoformat()
    expected_harvest = (date.today() - timedelta(days=10) + timedelta(days=120)).isoformat()

    cycle_resp = client.post(f"/farms/{farm_id}/cycles", json={
        "crop_id": 3,
        "sowing_date": sowing_date,
    }, headers=headers)
    assert cycle_resp.status_code == 201
    cycle_id = cycle_resp.json()["cycle_id"]

    # 4. Check Crop Calendar: GET /cycles/{cycle_id}/calendar
    # Wheat has 5 stages in crop_stages:
    # 1: Germination (0-20) -> Day 10 is within 0-20, so 'Current'
    # 2: Crown root initiation (21-40) -> 'Upcoming'
    # 3: Tillering (41-65) -> 'Upcoming'
    # 4: Flowering (66-90) -> 'Upcoming'
    # 5: Grain filling and harvest (91-120) -> 'Upcoming'
    cal_resp = client.get(f"/cycles/{cycle_id}/calendar", headers=headers)
    assert cal_resp.status_code == 200, cal_resp.text
    stages = cal_resp.json()
    assert len(stages) == 5, f"Expected 5 stages for Wheat, got {len(stages)}"

    current_stages = [s for s in stages if s["stage_status"] == "Current"]
    assert len(current_stages) == 1, f"Expected exactly one 'Current' stage, got {len(current_stages)}"
    assert "germination" in current_stages[0]["stage_name"].lower()

    upcoming_stages = [s for s in stages if s["stage_status"] == "Upcoming"]
    assert len(upcoming_stages) == 4, f"Expected 4 upcoming stages, got {len(upcoming_stages)}"

    # 5. Check Current Status Card on dashboard: GET /dashboard/current
    current_resp = client.get("/dashboard/current", headers=headers)
    assert current_resp.status_code == 200
    cycles = current_resp.json()
    assert len(cycles) >= 1
    wheat_cycle = next((c for c in cycles if c["cycle_id"] == cycle_id), None)
    assert wheat_cycle is not None
    assert wheat_cycle["crop_name"] == "Wheat"
    assert wheat_cycle["expected_harvest"] == expected_harvest
    assert wheat_cycle["days_to_harvest"] in (109, 110)
    assert wheat_cycle["days_since_sowing"] in (9, 10)
    assert wheat_cycle["status"] == "Growing"
    assert "Germination" in wheat_cycle["current_stage"]

    # 6. Check Fertilizer Advice: POST /farms/{farm_id}/fertilizer-advice
    fert_resp = client.post(f"/farms/{farm_id}/fertilizer-advice", json={
        "crop_id": 3,
        "test_id": test_id,
    }, headers=headers)
    assert fert_resp.status_code == 200
    fert_data = fert_resp.json()
    assert len(fert_data["fertilizers"]) > 0, "Low-NPK soil must return fertilizer dosage recommendations"

    fert_names = [f["fertilizer"] for f in fert_data["fertilizers"]]
    assert any("Urea" in name or "DAP" in name or "MOP" in name for name in fert_names)
    for f in fert_data["fertilizers"]:
        assert f["kg_per_acre"] > 0
        assert f["kg_for_farm"] > 0
        assert f["estimated_cost"] > 0


# =============================================================================
# 2. Protected pages redirect when logged out
# =============================================================================

def test_protected_pages_redirect_when_logged_out(client: TestClient):
    """Unauthenticated requests to protected UI pages must return 302 redirect to /ui/login?next=<path>."""
    from urllib.parse import unquote

    protected_paths = [
        "/ui/dashboard",
        "/ui/farms",
        "/ui/cycle-detail",
        "/ui/alerts",
        "/ui/prices",
        "/ui/admin",
    ]

    for path in protected_paths:
        resp = client.get(path, follow_redirects=False)
        assert resp.status_code == 302, f"Expected 302 for {path}, got {resp.status_code}"
        location = resp.headers.get("Location")
        assert location is not None
        assert location.startswith("/ui/login?next=")
        assert path in unquote(location)

    # Authenticated access to protected UI pages must return 200 OK
    headers = get_authenticated_farmer(client, phone="9876599902", email="wheat_test2@example.com")
    for path in protected_paths:
        auth_resp = client.get(path, headers=headers, follow_redirects=False)
        assert auth_resp.status_code == 200, f"Expected 200 for authenticated {path}, got {auth_resp.status_code}"


# =============================================================================
# 3. Next-redirect works and rejects external URLs
# =============================================================================

def test_next_redirect_works_and_rejects_external_urls(client: TestClient):
    """Validate that ?next= redirection allows safe relative paths and rejects open redirect attempts."""
    headers = get_authenticated_farmer(client, phone="9876599903", email="wheat_test3@example.com")

    # 1. Safe relative paths should be honored
    safe_paths = ["/ui/farms", "/ui/dashboard", "/ui/alerts", "/ui/prices"]
    for safe_path in safe_paths:
        resp = client.get(f"/ui/login?next={safe_path}", headers=headers, follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers.get("Location") == safe_path

    # 2. Malicious external URLs must be rejected and defaulted to /ui/dashboard
    unsafe_urls = [
        "https://evil.com",
        "http://malicious.org/phish",
        "//evil.com",
        "//attacker.com/bypass",
        r"\evil.com",
        r"\\evil.com",
        "javascript:alert(1)",
        "data:text/html,evil",
    ]
    for unsafe_url in unsafe_urls:
        resp = client.get(f"/ui/login?next={unsafe_url}", headers=headers, follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers.get("Location") == "/ui/dashboard", f"Expected /ui/dashboard for unsafe URL {unsafe_url}"

    # 3. Direct helper assertions for comprehensive security validation
    assert is_safe_redirect_url("/ui/dashboard") is True
    assert is_safe_redirect_url("/ui/farms") is True
    assert is_safe_redirect_url("/ui/cycle-detail?id=1") is True
    assert is_safe_redirect_url("https://google.com") is False
    assert is_safe_redirect_url("http://google.com") is False
    assert is_safe_redirect_url("//google.com") is False
    assert is_safe_redirect_url(r"\google.com") is False
    assert is_safe_redirect_url(r"\\google.com") is False
    assert is_safe_redirect_url(None) is False
    assert is_safe_redirect_url("") is False

    assert get_safe_redirect_url("/ui/farms") == "/ui/farms"
    assert get_safe_redirect_url("https://evil.com") == "/ui/dashboard"
    assert get_safe_redirect_url("//evil.com") == "/ui/dashboard"
    assert get_safe_redirect_url(None) == "/ui/dashboard"


# =============================================================================
# 4. Recommendation scores rounded to 1 decimal place
# =============================================================================

def test_recommendation_scores_rounded_to_one_decimal(client: TestClient):
    """Recommendation endpoint scores must be rounded to 1 decimal place."""
    headers = get_authenticated_farmer(client, phone="9876599904", email="wheat_test4@example.com")

    # Create farm and soil test
    farm_resp = client.post("/farms", json={"farm_name": "Score Farm", "area_acres": 4.0}, headers=headers)
    farm_id = farm_resp.json()["farm_id"]

    client.post(f"/farms/{farm_id}/soil-tests", json={
        "nitrogen": 75.0,
        "phosphorus": 45.0,
        "potassium": 35.0,
        "ph": 6.5,
        "moisture": 60.0,
        "test_date": date.today().isoformat(),
    }, headers=headers)

    # Insert 30 days of weather records
    today = date.today()
    for i in range(30):
        d_str = (today - timedelta(days=i)).isoformat()
        client.post(f"/farms/{farm_id}/weather/manual", json={
            "record_date": d_str,
            "temperature": 26.5,
            "humidity": 65.0,
            "rainfall_mm": 5.0,
        }, headers=headers)

    rec_resp = client.post(f"/farms/{farm_id}/recommend", json={"season": "Kharif"}, headers=headers)
    assert rec_resp.status_code == 200
    recs = rec_resp.json()["recommendations"]
    assert len(recs) > 0

    for r in recs:
        # Check suitability score rounded to 1 decimal place
        suit_str = str(r["suitability"])
        if "." in suit_str:
            assert len(suit_str.split(".")[1]) <= 1, f"Suitability {r['suitability']} exceeds 1 decimal place"

        # Check breakdown scores
        for score_key in ["ph_score", "temp_score", "humidity_score", "rain_score", "n_score", "p_score", "k_score"]:
            val = r[score_key]
            val_str = str(val)
            if "." in val_str:
                assert len(val_str.split(".")[1]) <= 1, f"{score_key} {val} exceeds 1 decimal place"
