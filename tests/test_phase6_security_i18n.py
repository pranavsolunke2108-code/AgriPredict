"""Tests for Phase 6: Least-Privilege Security, i18n Fallback, Language Persistence, and Health Check."""

import pytest
from fastapi.testclient import TestClient

from app import db


def test_health_endpoint(client: TestClient):
    """Verify GET /health returns 200 and healthy DB connection status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "connected" in data["database"]


def test_i18n_english_dictionary(client: TestClient):
    """Verify GET /i18n/en returns all English translation keys."""
    response = client.get("/i18n/en")
    assert response.status_code == 200
    dict_en = response.json()
    assert isinstance(dict_en, dict)
    assert "current_status" in dict_en
    assert dict_en["current_status"] == "Current Status"
    assert "login" in dict_en
    assert dict_en["login"] == "Login"


def test_i18n_fallback_to_english(client: TestClient):
    """Verify GET /i18n/{lang} returns localized values and falls back to English for missing keys."""
    # Insert an English-only test key
    db.execute_query(
        "INSERT INTO translations (text_key, lang, text) VALUES ('test_unique_fallback', 'en', 'English Fallback Text')",
        commit=True,
    )

    # 1. Fetch Marathi translations
    response_mr = client.get("/i18n/mr")
    assert response_mr.status_code == 200
    dict_mr = response_mr.json()

    # Known Marathi translation should be localized
    assert dict_mr.get("crop_rice") == "भात"
    assert dict_mr.get("current_status") == "सद्यस्थिती"

    # Missing in Marathi should fall back to English
    assert dict_mr.get("test_unique_fallback") == "English Fallback Text"

    # 2. Fetch Hindi translations
    response_hi = client.get("/i18n/hi")
    assert response_hi.status_code == 200
    dict_hi = response_hi.json()
    assert dict_hi.get("crop_rice") == "धान"
    assert dict_hi.get("test_unique_fallback") == "English Fallback Text"


def test_language_persistence_workflow(client: TestClient):
    """Verify PATCH /me/language updates farmers.language and loads on subsequent login."""
    # 1. Register a test farmer (defaults to 'en')
    reg_payload = {
        "name": "Suresh Dev",
        "phone": "9811122233",
        "password": "Password@123",
        "district": "Nagpur",
        "village": "Umred",
    }
    reg_res = client.post("/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    farmer_data = reg_res.json()
    assert farmer_data["language"] == "en"

    # 2. Login to obtain access token
    login_res = client.post(
        "/auth/login",
        json={"identifier": "9811122233", "password": "Password@123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Update farmer language to Marathi via PATCH /me/language
    patch_res = client.patch(
        "/me/language",
        json={"language": "mr"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["language"] == "mr"
    assert patch_data["name"] == "Suresh Dev"

    # 4. Verify GET /auth/me reflects the updated language
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["language"] == "mr"

    # 5. Subsequent login must return updated language
    relogin_res = client.post(
        "/auth/login",
        json={"identifier": "9811122233", "password": "Password@123"},
    )
    assert relogin_res.status_code == 200
    assert relogin_res.json()["farmer"]["language"] == "mr"

    # 6. Change to Hindi and verify
    patch_hi_res = client.patch(
        "/me/language",
        json={"language": "hi"},
        headers=headers,
    )
    assert patch_hi_res.status_code == 200
    assert patch_hi_res.json()["language"] == "hi"

    me_hi_res = client.get("/auth/me", headers=headers)
    assert me_hi_res.json()["language"] == "hi"


def test_language_validation_rejects_unsupported(client: TestClient):
    """Verify PATCH /me/language rejects invalid language codes with 422."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "name": "Validation Test Farmer",
            "phone": "9822233344",
            "password": "Password@123",
            "district": "Pune",
        },
    )
    login_res = client.post(
        "/auth/login",
        json={"identifier": "9822233344", "password": "Password@123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid language 'fr'
    res = client.patch("/me/language", json={"language": "fr"}, headers=headers)
    assert res.status_code == 422


def test_localized_crops_endpoint(client: TestClient):
    """Verify GET /crops/localized uses crop_localized_view with language fallback."""
    res_mr = client.get("/crops/localized?lang=mr")
    assert res_mr.status_code == 200
    crops_mr = res_mr.json()
    assert isinstance(crops_mr, list)
    assert len(crops_mr) > 0

    # Find Rice in Marathi
    rice_mr = next((c for c in crops_mr if c["crop_name"] == "Rice"), None)
    assert rice_mr is not None
    assert rice_mr["localized_name"] == "भात"
