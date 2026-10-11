"""Automated Tests for AgriPredict Public Home Page and i18n Fixes.

Covers:
1. i18n endpoint and English fallback.
2. Language persistence via PATCH /me/language and farmers.language.
3. GET /health translation encoding verification (valid vs corrupted).
4. POST /public/quick-recommend server validation and rate limiting.
5. Public endpoints (season, stats) return no personal farmer data.
6. Root endpoint GET / serves static/index.html with UTF-8 encoding and responsive structure.
"""

import pytest
from fastapi.testclient import TestClient

from app import db
from app.routers.public import reset_rate_limit


# Helper fixture for registering and logging in a test farmer
@pytest.fixture
def auth_farmer_token(client: TestClient):
    """Register and authenticate a test farmer, returning a valid Bearer token."""
    phone = "9876543299"
    email = "i18ntest@agripredict.in"
    password = "SecurePassword123"

    # Register
    reg_res = client.post(
        "/auth/register",
        json={
            "name": "Prashant Patil",
            "phone": phone,
            "email": email,
            "password": password,
            "district": "Pune",
            "village": "Baramati",
            "language": "en",
        },
    )
    assert reg_res.status_code in (200, 201)

    # Login
    login_res = client.post(
        "/auth/login",
        json={"identifier": phone, "password": password},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return token


# ============================================================================
# 1. i18n Endpoint & English Fallback Tests
# ============================================================================

def test_i18n_dictionary_and_english_fallback(client: TestClient):
    """Verify GET /i18n/{lang} returns translations, falling back to English for missing keys."""
    # 1. Fetch English dictionary
    res_en = client.get("/i18n/en")
    assert res_en.status_code == 200
    dict_en = res_en.json()
    assert isinstance(dict_en, dict)
    assert "current_status" in dict_en
    assert dict_en["current_status"] == "Current Status"

    # 2. Insert a temporary English-only key
    unique_key = "unique_fallback_test_key"
    english_val = "English Only Unique String"
    db.execute_update(
        "INSERT INTO translations (text_key, lang, text) VALUES (%s, %s, %s)",
        (unique_key, "en", english_val),
    )

    try:
        # 3. Request Marathi dictionary (where unique_key is missing)
        res_mr = client.get("/i18n/mr")
        assert res_mr.status_code == 200
        dict_mr = res_mr.json()
        assert unique_key in dict_mr
        assert dict_mr[unique_key] == english_val  # Fell back to English

        # 4. Request Hindi dictionary (where unique_key is missing)
        res_hi = client.get("/i18n/hi")
        assert res_hi.status_code == 200
        dict_hi = res_hi.json()
        assert unique_key in dict_hi
        assert dict_hi[unique_key] == english_val  # Fell back to English
    finally:
        db.execute_update("DELETE FROM translations WHERE text_key = %s", (unique_key,))


# ============================================================================
# 2. Language Persistence Tests
# ============================================================================

def test_farmer_language_persistence(client: TestClient, auth_farmer_token: str):
    """Verify farmer language preference persists in farmers.language and can be retrieved via /me."""
    headers = {"Authorization": f"Bearer {auth_farmer_token}"}

    # Verify initial language
    me_res = client.get("/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["language"] == "en"

    # Update to Marathi
    patch_mr = client.patch("/me/language", json={"language": "mr"}, headers=headers)
    assert patch_mr.status_code == 200
    assert patch_mr.json()["language"] == "mr"

    # Verify retrieval
    me_res2 = client.get("/me", headers=headers)
    assert me_res2.status_code == 200
    assert me_res2.json()["language"] == "mr"

    # Update to Hindi
    patch_hi = client.patch("/me/language", json={"language": "hi"}, headers=headers)
    assert patch_hi.status_code == 200
    assert patch_hi.json()["language"] == "hi"

    me_res3 = client.get("/me", headers=headers)
    assert me_res3.status_code == 200
    assert me_res3.json()["language"] == "hi"


# ============================================================================
# 3. GET /health Translation Encoding Verification Tests
# ============================================================================

def test_health_check_translation_encoding(client: TestClient):
    """Verify GET /health includes translation_encoding and detects clean vs corrupted strings."""
    # 1. Clean test DB should be valid
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "connected" in data["database"]
    assert "translation_encoding" in data
    assert data["translation_encoding"] == "valid"
    assert data["corrupted_translations"] == 0

    # 2. Simulate inserting a corrupted mojibake string (C393 prefix instead of E0A4/E0A5)
    corrupted_key = "test_corrupted_encoding_key"
    corrupted_val = "Óñ«Óñ¥"  # Typical mojibake bytes
    db.execute_update(
        "INSERT INTO translations (text_key, lang, text) VALUES (%s, %s, %s)",
        (corrupted_key, "mr", corrupted_val),
    )

    try:
        res_corrupted = client.get("/health")
        assert res_corrupted.status_code == 200
        data_corrupted = res_corrupted.json()
        assert data_corrupted["translation_encoding"] == "corrupted"
        assert data_corrupted["corrupted_translations"] >= 1
    finally:
        # Clean up
        db.execute_update("DELETE FROM translations WHERE text_key = %s", (corrupted_key,))

    # 3. Re-verify health status is clean again
    res_clean = client.get("/health")
    assert res_clean.status_code == 200
    assert res_clean.json()["translation_encoding"] == "valid"
    assert res_clean.json()["corrupted_translations"] == 0


# ============================================================================
# 4. POST /public/quick-recommend Validation & Rate Limiting Tests
# ============================================================================

def test_quick_recommend_success_and_rounding(client: TestClient):
    """Verify quick_recommend returns top 3 crops with scores rounded to 1 decimal place."""
    reset_rate_limit()

    payload = {
        "ph": 6.5,
        "n": 90.0,
        "p": 42.0,
        "k": 43.0,
        "temperature": 25.0,
        "humidity": 75.0,
        "rainfall": 150.0,
        "season": "Rabi",
        "lang": "en",
    }
    response = client.post("/public/quick-recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 3
    assert len(data) > 0

    first = data[0]
    assert first["rank_no"] == 1
    assert "crop_name" in first
    assert "localized_name" in first
    assert "suitability" in first
    # Verify score rounding to at most 1 decimal
    suitability_str = str(first["suitability"])
    if "." in suitability_str:
        assert len(suitability_str.split(".")[1]) <= 1


def test_quick_recommend_range_validations(client: TestClient):
    """Verify server-side validation rejects out-of-range soil and climate values with HTTP 400."""
    reset_rate_limit()

    base = {
        "ph": 6.5,
        "n": 90.0,
        "p": 42.0,
        "k": 43.0,
        "temperature": 25.0,
        "humidity": 75.0,
        "rainfall": 150.0,
    }

    # Invalid pH (< 0 or > 14)
    res_ph = client.post("/public/quick-recommend", json={**base, "ph": 15.0})
    assert res_ph.status_code == 400
    assert "pH must be between 0 and 14" in res_ph.json()["detail"]

    # Negative Nitrogen
    res_n = client.post("/public/quick-recommend", json={**base, "n": -10.0})
    assert res_n.status_code == 400
    assert "Nitrogen" in res_n.json()["detail"]

    # Negative Phosphorus
    res_p = client.post("/public/quick-recommend", json={**base, "p": -5.0})
    assert res_p.status_code == 400
    assert "Phosphorus" in res_p.json()["detail"]

    # Negative Potassium
    res_k = client.post("/public/quick-recommend", json={**base, "k": -1.0})
    assert res_k.status_code == 400
    assert "Potassium" in res_k.json()["detail"]

    # Out of bounds temperature
    res_t = client.post("/public/quick-recommend", json={**base, "temperature": 75.0})
    assert res_t.status_code == 400
    assert "Temperature" in res_t.json()["detail"]

    # Out of bounds humidity
    res_h = client.post("/public/quick-recommend", json={**base, "humidity": 105.0})
    assert res_h.status_code == 400
    assert "Humidity" in res_h.json()["detail"]

    # Negative rainfall
    res_r = client.post("/public/quick-recommend", json={**base, "rainfall": -20.0})
    assert res_r.status_code == 400
    assert "Rainfall" in res_r.json()["detail"]

    # Invalid season
    res_s = client.post("/public/quick-recommend", json={**base, "season": "InvalidSeason"})
    assert res_s.status_code == 400
    assert "Invalid season" in res_s.json()["detail"]


def test_quick_recommend_rate_limiting(client: TestClient):
    """Verify rate-limiting enforces maximum 20 requests per minute per IP."""
    reset_rate_limit()

    payload = {
        "ph": 6.5,
        "n": 80.0,
        "p": 40.0,
        "k": 40.0,
        "temperature": 24.0,
        "humidity": 65.0,
        "rainfall": 100.0,
    }

    # 20 requests should pass
    for i in range(20):
        res = client.post("/public/quick-recommend", json=payload)
        assert res.status_code == 200, f"Request {i+1} failed unexpectedly"

    # 21st request must trigger HTTP 429 Too Many Requests
    excess_res = client.post("/public/quick-recommend", json=payload)
    assert excess_res.status_code == 429
    assert "Rate limit exceeded" in excess_res.json()["detail"]

    # Reset afterwards for other tests
    reset_rate_limit()


# ============================================================================
# 5. Public Endpoints Expose No Personal Data Tests
# ============================================================================

def test_public_season_returns_crops_and_no_personal_data(client: TestClient):
    """Verify GET /public/season returns current season crops without leaking farmer info."""
    res = client.get("/public/season?lang=en")
    assert res.status_code == 200
    data = res.json()

    assert "season" in data
    assert "crops" in data
    assert isinstance(data["crops"], list)
    assert len(data["crops"]) > 0

    for crop in data["crops"]:
        assert "crop_id" in crop
        assert "crop_name" in crop
        assert "localized_name" in crop
        assert "season" in crop
        # Ensure no user or personal farm identifiers leaked
        assert "farmer_id" not in crop
        assert "user_id" not in crop
        assert "phone" not in crop
        assert "email" not in crop


def test_public_stats_returns_aggregates_and_no_personal_data(client: TestClient):
    """Verify GET /public/stats exposes only aggregated platform counts."""
    res = client.get("/public/stats")
    assert res.status_code == 200
    data = res.json()

    assert "crops_supported" in data
    assert "languages_supported" in data
    assert "recommendations_made" in data
    assert data["crops_supported"] >= 1
    assert data["languages_supported"] == 3

    # Ensure absolute privacy: no sensitive farmer or user fields
    forbidden_keys = ["farmers", "users", "names", "phones", "emails", "farms", "locations"]
    for key in forbidden_keys:
        assert key not in data


# ============================================================================
# 6. Public Home Page Serves index.html with Proper Structure
# ============================================================================

def test_root_serves_public_home_page(client: TestClient):
    """Verify GET / serves static/index.html with UTF-8 encoding and required sections."""
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")

    content = res.text
    # 1. UTF-8 meta charset
    assert '<meta charset="UTF-8">' in content or '<meta charset="utf-8">' in content

    # 2. Noto Sans Devanagari font loaded
    assert "Noto+Sans+Devanagari" in content

    # 3. Sticky header elements & language switch
    assert "landing-header" in content
    assert "lang-switch" in content

    # 4. Hero section & SVG animated field scene
    assert "hero-section" in content
    assert "field-svg" in content

    # 5. "Try it now" section with sliders & quick recommend form
    assert "try-it" in content
    assert "range-ph" in content
    assert "range-n" in content
    assert "quick-form" in content

    # 6. Sowing now card
    assert "sowing-now" in content

    # 7. Animated counters
    assert "stat-crops" in content
    assert "stat-langs" in content

    # 8. Features and How It Works
    assert "features" in content
    assert "how-it-works" in content

    # 9. Prefers-reduced-motion CSS support
    assert "prefers-reduced-motion" in content


def test_home_page_header_auth_switching(client: TestClient):
    """Verify that index.html contains dynamic header auth container switching between Login/Register and Dashboard."""
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    html = res.text

    # Verify presence of the header auth elements and JS switching logic
    assert 'id="header-auth-container"' in html
    assert 'id="nav-login-btn"' in html
    assert 'id="nav-register-btn"' in html
    assert "updateHeaderAuth" in html
    assert "API.getToken()" in html
    assert "user-avatar-btn" in html
    assert "user-avatar-circle" in html
    assert "Dashboard" in html


def test_home_page_header_logged_out_links(client: TestClient):
    """Bug 2 test: Verify GET / returns header with working links to /ui/login and /ui/register."""
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    html = res.text

    # Desktop header links
    assert 'href="/ui/login"' in html
    assert 'href="/ui/register"' in html
    assert 'id="nav-login-btn"' in html
    assert 'id="nav-register-btn"' in html

    # Mobile menu drawer links
    assert 'id="mobile-nav-drawer"' in html
    assert 'id="mobile-login-btn"' in html
    assert 'id="mobile-register-btn"' in html

    # Hero primary CTA links to /ui/register
    assert 'href="/ui/register" class="btn-hero-primary"' in html or 'class="btn-hero-primary"' in html


def test_login_and_register_pages_return_200_without_token(client: TestClient):
    """Bug 2 test: Verify /ui/login and /ui/register load with HTTP 200 without a token."""
    res_login = client.get("/ui/login", headers={"Accept": "text/html"})
    assert res_login.status_code == 200
    assert "text/html" in res_login.headers.get("content-type", "")
    assert "login-form" in res_login.text

    res_reg = client.get("/ui/register", headers={"Accept": "text/html"})
    assert res_reg.status_code == 200
    assert "text/html" in res_reg.headers.get("content-type", "")
    assert "register-form" in res_reg.text


def test_invalid_or_expired_token_handling(client: TestClient):
    """Bug 2 test: Verify /me rejects invalid tokens and index.html clears session to logged-out header."""
    # 1. Server rejects an expired/invalid token
    res = client.get("/me", headers={"Authorization": "Bearer invalid_expired_jwt_token_12345"})
    assert res.status_code in (401, 403)

    # 2. Client home page contains explicit session clearing on rejection
    res_home = client.get("/", headers={"Accept": "text/html"})
    assert res_home.status_code == 200
    html = res_home.text
    assert "API.clearSession()" in html
    assert "renderLoggedOutAuth()" in html


def test_home_page_sky_override_and_tokens(client: TestClient):
    """Bug 1 test: Verify index.html contains ?sky= testing override and design tokens."""
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    html = res.text

    assert "applyTimeOfDaySky" in html
    assert 'urlParams.get("sky")' in html
    assert "sky-dawn" in html
    assert "sky-day" in html
    assert "sky-dusk" in html
    assert "sky-night" in html
    assert "var(--hero-fg)" in html
    assert "var(--hero-scrim)" in html


