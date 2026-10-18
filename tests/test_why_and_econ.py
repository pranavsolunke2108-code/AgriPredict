"""Tests for 'Why this crop?' explanation and economic data-source labels."""

from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from app import db
from app.routers.public import reset_rate_limit
from app.security import create_access_token
from app.services.why_service import build_why_crop_response


def create_test_user(client: TestClient, phone="9988771122", name="Farmer Test", role="farmer"):
    res = client.post("/auth/register", json={
        "name": name,
        "phone": phone,
        "password": "Password123",
        "district": "Pune",
    })
    farmer_id = res.json()["farmer_id"]
    if role != "farmer":
        db.execute_update("UPDATE farmers SET role = %s WHERE farmer_id = %s", (role, farmer_id))
    token = create_access_token({"sub": str(farmer_id), "role": role})
    return farmer_id, {"Authorization": f"Bearer {token}"}


def setup_farm_with_soil_and_weather(client: TestClient, headers: dict, phone_suffix="01"):
    # 1. Create farm
    f_res = client.post("/farms", json={"farm_name": f"Farm {phone_suffix}", "area_acres": 5.0}, headers=headers)
    assert f_res.status_code == 201
    farm_id = f_res.json()["farm_id"]

    # 2. Add soil test
    st_res = client.post(f"/farms/{farm_id}/soil-tests", json={
        "ph": 6.5,
        "nitrogen": 80.0,
        "phosphorus": 45.0,
        "potassium": 40.0,
    }, headers=headers)
    assert st_res.status_code == 201
    test_id = st_res.json()["test_id"]

    # 3. Add 30-day weather record
    db.execute_update(
        "INSERT INTO weather_records (farm_id, record_date, temperature, humidity, rainfall_mm) VALUES (%s, %s, %s, %s, %s)",
        (farm_id, date.today().isoformat(), 26.0, 75.0, 180.0),
    )

    return farm_id, test_id


def test_status_mapping_and_thresholds():
    """Verify stored procedure evaluation status mappings and summary_level thresholds."""
    # Test case 1: 7 good items -> strong match
    raw_rows_all_good = [
        {"param_key": "ph", "farm_value": 6.5, "ideal_min": 5.5, "ideal_max": 7.0, "status": "ideal", "score": 100.0, "weight": 15},
        {"param_key": "temperature", "farm_value": 25.0, "ideal_min": 20.0, "ideal_max": 30.0, "status": "ideal", "score": 100.0, "weight": 20},
        {"param_key": "humidity", "farm_value": 75.0, "ideal_min": 70.0, "ideal_max": 90.0, "status": "ideal", "score": 100.0, "weight": 10},
        {"param_key": "rainfall", "farm_value": 200.0, "ideal_min": 150.0, "ideal_max": 300.0, "status": "ideal", "score": 100.0, "weight": 20},
        {"param_key": "nitrogen", "farm_value": 80.0, "ideal_min": 80.0, "ideal_max": 80.0, "status": "ok", "score": 100.0, "weight": 12},
        {"param_key": "phosphorus", "farm_value": 45.0, "ideal_min": 48.0, "ideal_max": 48.0, "status": "ok", "score": 93.8, "weight": 12},
        {"param_key": "potassium", "farm_value": 40.0, "ideal_min": 40.0, "ideal_max": 40.0, "status": "ok", "score": 100.0, "weight": 11},
    ]
    resp1 = build_why_crop_response(1, "Rice", raw_rows_all_good, lang="en")
    assert resp1.good_count == 7
    assert resp1.summary_level == "strong"
    assert resp1.tips == []  # No tips when all ideal/ok

    # Test case 2: 4 good items -> moderate match, tips selection
    raw_rows_moderate = [
        {"param_key": "ph", "farm_value": 4.5, "ideal_min": 5.5, "ideal_max": 7.0, "status": "low", "score": 40.0, "weight": 15},
        {"param_key": "temperature", "farm_value": 38.0, "ideal_min": 20.0, "ideal_max": 30.0, "status": "high", "score": 35.0, "weight": 20},
        {"param_key": "humidity", "farm_value": 75.0, "ideal_min": 70.0, "ideal_max": 90.0, "status": "ideal", "score": 100.0, "weight": 10},
        {"param_key": "rainfall", "farm_value": 200.0, "ideal_min": 150.0, "ideal_max": 300.0, "status": "ideal", "score": 100.0, "weight": 20},
        {"param_key": "nitrogen", "farm_value": 30.0, "ideal_min": 80.0, "ideal_max": 80.0, "status": "very_low", "score": 37.5, "weight": 12},
        {"param_key": "phosphorus", "farm_value": 48.0, "ideal_min": 48.0, "ideal_max": 48.0, "status": "ok", "score": 100.0, "weight": 12},
        {"param_key": "potassium", "farm_value": 40.0, "ideal_min": 40.0, "ideal_max": 40.0, "status": "ok", "score": 100.0, "weight": 11},
    ]
    resp2 = build_why_crop_response(1, "Rice", raw_rows_moderate, lang="en")
    assert resp2.good_count == 4
    assert resp2.summary_level == "moderate"
    # Tips: nitrogen is very_low -> fertilizer tip; temp is high -> climate tip; ph is low -> ph tip
    assert "why_tip_fertilizer" in resp2.tips
    assert "why_tip_climate" in resp2.tips
    assert "why_tip_ph" in resp2.tips

    # Test case 3: 2 good items -> weak match
    raw_rows_weak = [
        {"param_key": "ph", "farm_value": 8.5, "ideal_min": 5.5, "ideal_max": 7.0, "status": "very_high", "score": 0.0, "weight": 15},
        {"param_key": "temperature", "farm_value": 40.0, "ideal_min": 20.0, "ideal_max": 30.0, "status": "very_high", "score": 0.0, "weight": 20},
        {"param_key": "humidity", "farm_value": 40.0, "ideal_min": 70.0, "ideal_max": 90.0, "status": "very_low", "score": 0.0, "weight": 10},
        {"param_key": "rainfall", "farm_value": 50.0, "ideal_min": 150.0, "ideal_max": 300.0, "status": "very_low", "score": 0.0, "weight": 20},
        {"param_key": "nitrogen", "farm_value": 20.0, "ideal_min": 80.0, "ideal_max": 80.0, "status": "very_low", "score": 25.0, "weight": 12},
        {"param_key": "phosphorus", "farm_value": 48.0, "ideal_min": 48.0, "ideal_max": 48.0, "status": "ok", "score": 100.0, "weight": 12},
        {"param_key": "potassium", "farm_value": 40.0, "ideal_min": 40.0, "ideal_max": 40.0, "status": "ok", "score": 100.0, "weight": 11},
    ]
    resp3 = build_why_crop_response(1, "Rice", raw_rows_weak, lang="mr")
    assert resp3.good_count == 2
    assert resp3.summary_level == "weak"


def test_why_crop_farm_endpoint_and_ownership(client: TestClient):
    """Test GET /farms/{farm_id}/recommendations/{crop_id}/why ownership check and default soil test."""
    _, farmer1_headers = create_test_user(client, "9988112233", "Farmer One")
    _, farmer2_headers = create_test_user(client, "9988112244", "Farmer Two")

    farm_id, test_id = setup_farm_with_soil_and_weather(client, farmer1_headers, "1")

    # 1. Ownership check: Farmer Two cannot access Farmer One's farm recommendations explanation
    unauth_res = client.get(f"/farms/{farm_id}/recommendations/1/why", headers=farmer2_headers)
    assert unauth_res.status_code == 403

    # 2. Owner can access with explicit test_id
    res_explicit = client.get(f"/farms/{farm_id}/recommendations/1/why?test_id={test_id}", headers=farmer1_headers)
    assert res_explicit.status_code == 200
    data_exp = res_explicit.json()
    assert data_exp["crop_id"] == 1
    assert "summary_level" in data_exp
    assert "good_count" in data_exp
    assert len(data_exp["items"]) == 7

    # 3. Default latest soil test when test_id omitted
    res_default = client.get(f"/farms/{farm_id}/recommendations/1/why", headers=farmer1_headers)
    assert res_default.status_code == 200
    data_def = res_default.json()
    assert data_def["crop_id"] == 1
    assert len(data_def["items"]) == 7


def test_why_crop_no_weather_returns_400(client: TestClient):
    """Test 400 Bad Request when farm lacks 30-day weather records."""
    _, headers = create_test_user(client, "9988112255", "Weatherless Farmer")

    # Create farm with soil test but NO weather records
    f_res = client.post("/farms", json={"farm_name": "No Weather Farm", "area_acres": 3.0}, headers=headers)
    farm_id = f_res.json()["farm_id"]

    client.post(f"/farms/{farm_id}/soil-tests", json={
        "ph": 6.8, "nitrogen": 70.0, "phosphorus": 40.0, "potassium": 40.0,
    }, headers=headers)

    res = client.get(f"/farms/{farm_id}/recommendations/1/why", headers=headers)
    assert res.status_code == 400
    assert "weather" in res.json()["detail"].lower()


def test_public_why_validation_and_rate_limit(client: TestClient):
    """Test server-side range validation and rate limiting for POST /public/why."""
    reset_rate_limit()

    valid_payload = {
        "crop_id": 1,
        "ph": 6.5,
        "n": 80.0,
        "p": 45.0,
        "k": 40.0,
        "temperature": 25.0,
        "humidity": 70.0,
        "rainfall": 150.0,
        "lang": "en",
    }

    # 1. Validation: negative N
    bad_n = dict(valid_payload, n=-10.0)
    assert client.post("/public/why", json=bad_n).status_code == 400

    # 2. Validation: invalid pH > 14
    bad_ph = dict(valid_payload, ph=15.5)
    assert client.post("/public/why", json=bad_ph).status_code == 400

    # 3. Validation: temperature out of range (< -10 or > 60)
    bad_temp = dict(valid_payload, temperature=75.0)
    assert client.post("/public/why", json=bad_temp).status_code == 400

    # 4. Validation: humidity out of range (> 100)
    bad_hum = dict(valid_payload, humidity=120.0)
    assert client.post("/public/why", json=bad_hum).status_code == 400

    # 5. Validation: negative rainfall
    bad_rain = dict(valid_payload, rainfall=-5.0)
    assert client.post("/public/why", json=bad_rain).status_code == 400

    # 6. Success
    success_res = client.post("/public/why", json=valid_payload)
    assert success_res.status_code == 200
    res_data = success_res.json()
    assert res_data["crop_id"] == 1
    assert len(res_data["items"]) == 7

    # 7. Rate Limit (20 requests per minute)
    for _ in range(19):
        client.post("/public/why", json=valid_payload)

    rate_limit_res = client.post("/public/why", json=valid_payload)
    assert rate_limit_res.status_code == 429
    assert "rate limit" in rate_limit_res.json()["detail"].lower() or "too many" in rate_limit_res.json()["detail"].lower()

    reset_rate_limit()


def test_admin_crop_econ_source_and_data_quality(client: TestClient):
    """Test admin CRUD with econ_source & econ_year, and GET /admin/data-quality."""
    _, admin_headers = create_test_user(client, "9988998800", "Admin User", role="admin")

    # 1. Create crop with econ_source and econ_year
    create_payload = {
        "crop_name": "Test Sorghum",
        "season": "Kharif",
        "duration_days": 100,
        "min_ph": 6.0,
        "max_ph": 7.5,
        "min_temp": 20.0,
        "max_temp": 35.0,
        "min_humidity": 50.0,
        "max_humidity": 80.0,
        "min_rainfall": 400.0,
        "max_rainfall": 800.0,
        "n_required": 80,
        "p_required": 40,
        "k_required": 40,
        "avg_yield_q_per_acre": 12.0,
        "est_cost_per_acre": 15000.0,
        "econ_source": "MPKV Rahuri Cost Study",
        "econ_year": 2024,
    }
    c_res = client.post("/admin/crops", json=create_payload, headers=admin_headers)
    assert c_res.status_code == 201
    created_crop = c_res.json()
    crop_id = created_crop["crop_id"]
    assert created_crop["econ_source"] == "MPKV Rahuri Cost Study"
    assert created_crop["econ_year"] == 2024

    # 2. Update crop econ_source
    update_payload = dict(create_payload, econ_source="ICAR Revised 2025", econ_year=2025)
    u_res = client.put(f"/admin/crops/{crop_id}", json=update_payload, headers=admin_headers)
    assert u_res.status_code == 200
    updated_crop = u_res.json()
    assert updated_crop["econ_source"] == "ICAR Revised 2025"
    assert updated_crop["econ_year"] == 2025

    # 3. Test GET /admin/data-quality
    dq_res = client.get("/admin/data-quality", headers=admin_headers)
    assert dq_res.status_code == 200
    dq_data = dq_res.json()
    assert "missing_econ_source" in dq_data
    assert "missing_price_data" in dq_data
    assert isinstance(dq_data["missing_econ_source"], list)
    assert isinstance(dq_data["missing_price_data"], list)
