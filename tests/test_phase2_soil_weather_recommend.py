"""Comprehensive tests for Phase 2: Soil Tests, Weather Caching, and Recommendations."""

from datetime import date, datetime, timedelta
from unittest.mock import patch
import pytest
from app import db
from app.services import weather_service


def get_farmer_token(client, phone, name="Test Farmer"):
    """Helper to register and login a farmer and return auth headers."""
    client.post("/auth/register", json={
        "name": name,
        "phone": phone,
        "password": "password123",
    })
    res = client.post("/auth/login", json={
        "identifier": phone,
        "password": "password123",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. Soil Tests Tests
# =============================================================================

def test_soil_test_crud_and_validation(client):
    """Test creating, listing, retrieving, and deleting soil tests with input validation."""
    headers = get_farmer_token(client, "9876544001", "Soil Farmer")

    # Create farm
    farm_res = client.post("/farms", json={"farm_name": "Soil Farm", "area_acres": 10.0}, headers=headers)
    farm_id = farm_res.json()["farm_id"]

    # Input validation: negative Nitrogen rejected
    bad_n = client.post(f"/farms/{farm_id}/soil-tests", json={
        "nitrogen": -5.0, "phosphorus": 40.0, "potassium": 40.0, "ph": 6.5,
    }, headers=headers)
    assert bad_n.status_code == 422

    # Input validation: pH > 14 rejected
    bad_ph = client.post(f"/farms/{farm_id}/soil-tests", json={
        "nitrogen": 80.0, "phosphorus": 40.0, "potassium": 40.0, "ph": 15.0,
    }, headers=headers)
    assert bad_ph.status_code == 422

    # Input validation: moisture > 100 rejected
    bad_m = client.post(f"/farms/{farm_id}/soil-tests", json={
        "nitrogen": 80.0, "phosphorus": 40.0, "potassium": 40.0, "ph": 6.5, "moisture": 105.0,
    }, headers=headers)
    assert bad_m.status_code == 422

    # 1. Successful creation
    valid_payload = {
        "nitrogen": 85.0,
        "phosphorus": 45.0,
        "potassium": 40.0,
        "ph": 6.5,
        "moisture": 60.0,
        "organic_carbon": 0.8,
        "test_date": str(date.today()),
    }
    create_res = client.post(f"/farms/{farm_id}/soil-tests", json=valid_payload, headers=headers)
    assert create_res.status_code == 201
    test_data = create_res.json()
    assert test_data["nitrogen"] == 85.0
    assert test_data["ph"] == 6.5
    test_id = test_data["test_id"]

    # 2. List soil tests (verify latest first)
    # Add an older test
    client.post(f"/farms/{farm_id}/soil-tests", json={
        "nitrogen": 60.0, "phosphorus": 30.0, "potassium": 30.0, "ph": 6.0,
        "test_date": str(date.today() - timedelta(days=60)),
    }, headers=headers)

    list_res = client.get(f"/farms/{farm_id}/soil-tests", headers=headers)
    assert list_res.status_code == 200
    tests = list_res.json()
    assert len(tests) == 2
    assert tests[0]["test_id"] == test_id  # Most recent first

    # 3. Retrieve single soil test
    get_res = client.get(f"/soil-tests/{test_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["test_id"] == test_id

    # 4. Delete soil test
    del_res = client.delete(f"/soil-tests/{test_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify deleted
    assert client.get(f"/soil-tests/{test_id}", headers=headers).status_code == 404


def test_soil_test_ownership_enforcement(client):
    """Test that a farmer cannot view, create, or delete soil tests on another farmer's farm."""
    headers_a = get_farmer_token(client, "9876544002", "Farmer A")
    headers_b = get_farmer_token(client, "9876544003", "Farmer B")

    # Farmer A creates farm and test
    farm_a = client.post("/farms", json={"farm_name": "Farm A", "area_acres": 5.0}, headers=headers_a).json()["farm_id"]
    test_a = client.post(f"/farms/{farm_a}/soil-tests", json={
        "nitrogen": 80.0, "phosphorus": 40.0, "potassium": 40.0, "ph": 6.5
    }, headers=headers_a).json()["test_id"]

    # Farmer B tries to add a soil test to Farm A -> 403 Forbidden
    res1 = client.post(f"/farms/{farm_a}/soil-tests", json={
        "nitrogen": 70.0, "phosphorus": 30.0, "potassium": 30.0, "ph": 6.0
    }, headers=headers_b)
    assert res1.status_code == 403

    # Farmer B tries to list soil tests of Farm A -> 403 Forbidden
    res2 = client.get(f"/farms/{farm_a}/soil-tests", headers=headers_b)
    assert res2.status_code == 403

    # Farmer B tries to view test_a -> 403 Forbidden
    res3 = client.get(f"/soil-tests/{test_a}", headers=headers_b)
    assert res3.status_code == 403

    # Farmer B tries to delete test_a -> 403 Forbidden
    res4 = client.delete(f"/soil-tests/{test_a}", headers=headers_b)
    assert res4.status_code == 403


# =============================================================================
# 2. Weather Caching & Upsert Tests
# =============================================================================

def test_weather_manual_and_upsert_no_duplicates(client):
    """Test manual weather recording and verify upsert does not create duplicate rows."""
    headers = get_farmer_token(client, "9876544004", "Weather Farmer")
    farm_id = client.post("/farms", json={"farm_name": "Weather Farm", "area_acres": 4.0}, headers=headers).json()["farm_id"]

    today_str = str(date.today())

    # 1. Insert manual weather record
    res1 = client.post(f"/farms/{farm_id}/weather/manual", json={
        "record_date": today_str,
        "temperature": 26.5,
        "humidity": 65.0,
        "rainfall_mm": 5.0,
    }, headers=headers)
    assert res1.status_code == 201
    assert res1.json()["temperature"] == 26.5
    assert res1.json()["source"] == "manual"

    # Verify count in database is 1
    cnt1 = db.fetch_one("SELECT COUNT(*) AS total FROM weather_records WHERE farm_id = %s", (farm_id,))["total"]
    assert cnt1 == 1

    # 2. Upsert same date with updated measurements
    res2 = client.post(f"/farms/{farm_id}/weather/manual", json={
        "record_date": today_str,
        "temperature": 29.0,
        "humidity": 70.0,
        "rainfall_mm": 12.0,
    }, headers=headers)
    assert res2.status_code == 201
    assert res2.json()["temperature"] == 29.0
    assert res2.json()["rainfall_mm"] == 12.0

    # Verify count in database is STILL 1 (no duplicate row created!)
    cnt2 = db.fetch_one("SELECT COUNT(*) AS total FROM weather_records WHERE farm_id = %s", (farm_id,))["total"]
    assert cnt2 == 1

    # Check updated record in DB
    updated_rec = db.fetch_one("SELECT * FROM weather_records WHERE farm_id = %s AND record_date = %s", (farm_id, today_str))
    assert updated_rec["temperature"] == 29.0
    assert updated_rec["rainfall_mm"] == 12.0


def test_weather_refresh_caching_and_mock(client, monkeypatch):
    """Test Open-Meteo refresh, 6-hour caching bypass, and force refresh."""
    headers = get_farmer_token(client, "9876544005", "Refresh Farmer")

    # Farm with coordinates
    farm_id = client.post("/farms", json={
        "farm_name": "GPS Farm",
        "area_acres": 8.0,
        "latitude": 18.5204,
        "longitude": 73.8567,
    }, headers=headers).json()["farm_id"]

    # Mock Open-Meteo fetch returning 30 dummy days
    mock_records = [
        {
            "record_date": str(date.today() - timedelta(days=i)),
            "temperature": 25.0 + (i % 5),
            "humidity": 70.0,
            "rainfall_mm": 2.5,
        }
        for i in range(30)
    ]

    api_call_count = 0

    def mock_fetch(lat, lon, past_days=30):
        nonlocal api_call_count
        api_call_count += 1
        return mock_records

    monkeypatch.setattr(weather_service, "fetch_open_meteo_weather", mock_fetch)

    # 1. First refresh -> calls API
    res1 = client.post(f"/farms/{farm_id}/weather/refresh", headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["records_synced"] == 30
    assert data1["cached"] is False
    assert api_call_count == 1

    # 2. Second refresh within 6 hours -> SKIPS API call (cached=True)
    res2 = client.post(f"/farms/{farm_id}/weather/refresh", headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["cached"] is True
    assert data2["records_synced"] == 0
    assert api_call_count == 1  # Not incremented!

    # 3. Third refresh with force=True -> Bypasses cache and calls API
    res3 = client.post(f"/farms/{farm_id}/weather/refresh?force=true", headers=headers)
    assert res3.status_code == 200
    assert res3.json()["cached"] is False
    assert api_call_count == 2

    # 4. Query weather history
    history_res = client.get(f"/farms/{farm_id}/weather?days=30", headers=headers)
    assert history_res.status_code == 200
    assert len(history_res.json()) == 30


def test_weather_no_coordinates_error(client):
    """Test that refreshing weather on a farm without latitude/longitude returns 400."""
    headers = get_farmer_token(client, "9876544006", "No GPS Farmer")
    farm_id = client.post("/farms", json={"farm_name": "No GPS Farm", "area_acres": 2.0}, headers=headers).json()["farm_id"]

    res = client.post(f"/farms/{farm_id}/weather/refresh", headers=headers)
    assert res.status_code == 400
    assert "coordinates" in res.json()["detail"].lower()


# =============================================================================
# 3. Recommendation & Stored Procedure Tests
# =============================================================================

def test_recommend_crops_success(client, monkeypatch):
    """Test successful recommendation run calling the recommend_crops procedure."""
    headers = get_farmer_token(client, "9876544007", "Recom Farmer")

    # Farm with GPS
    farm_id = client.post("/farms", json={
        "farm_name": "Recommendation Farm",
        "area_acres": 6.0,
        "latitude": 18.5204,
        "longitude": 73.8567,
    }, headers=headers).json()["farm_id"]

    # Soil test
    test_id = client.post(f"/farms/{farm_id}/soil-tests", json={
        "nitrogen": 80.0, "phosphorus": 48.0, "potassium": 40.0, "ph": 6.5, "moisture": 65.0
    }, headers=headers).json()["test_id"]

    # Populate 30 days of weather records
    today = date.today()
    for i in range(30):
        client.post(f"/farms/{farm_id}/weather/manual", json={
            "record_date": str(today - timedelta(days=i)),
            "temperature": 25.0,
            "humidity": 75.0,
            "rainfall_mm": 5.0,
        }, headers=headers)

    # Call recommend with season='Kharif'
    rec_res = client.post(f"/farms/{farm_id}/recommend", json={"season": "Kharif"}, headers=headers)
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["farm_id"] == farm_id
    assert rec_data["test_id"] == test_id
    assert rec_data["season"] == "Kharif"
    assert len(rec_data["recommendations"]) == 3

    # Check top crop score breakdown
    top_crop = rec_data["recommendations"][0]
    assert top_crop["rank_no"] == 1
    assert "crop_name" in top_crop
    assert "suitability" in top_crop
    assert top_crop["ph_score"] >= 0
    assert top_crop["temp_score"] >= 0

    # Verify that predictions were recorded in database
    predictions = db.fetch_all("SELECT * FROM predictions WHERE farm_id = %s", (farm_id,))
    assert len(predictions) == 3


def test_recommend_procedure_sqlstate_45000_mapped_to_400(client):
    """Test that stored procedure SQLSTATE 45000 errors map to HTTP 400."""
    headers = get_farmer_token(client, "9876544008", "Error Farmer")
    farm_id = client.post("/farms", json={"farm_name": "Incomplete Farm", "area_acres": 3.0}, headers=headers).json()["farm_id"]

    # 1. No soil test -> 400
    res_no_test = client.post(f"/farms/{farm_id}/recommend", json={}, headers=headers)
    assert res_no_test.status_code == 400
    assert "soil test" in res_no_test.json()["detail"].lower()

    # Create soil test
    test_id = client.post(f"/farms/{farm_id}/soil-tests", json={
        "nitrogen": 80.0, "phosphorus": 40.0, "potassium": 40.0, "ph": 6.5
    }, headers=headers).json()["test_id"]

    # 2. No weather data (procedure checks weather) -> 400
    res_no_weather = client.post(f"/farms/{farm_id}/recommend", json={"test_id": test_id}, headers=headers)
    assert res_no_weather.status_code == 400
    assert "weather" in res_no_weather.json()["detail"].lower()


def test_prediction_history_grouped_newest_first(client):
    """Test GET /farms/{farm_id}/predictions returns history grouped by predicted_on."""
    headers = get_farmer_token(client, "9876544009", "History Farmer")
    farm_id = client.post("/farms", json={"farm_name": "History Farm", "area_acres": 5.0}, headers=headers).json()["farm_id"]

    test_id = client.post(f"/farms/{farm_id}/soil-tests", json={
        "nitrogen": 80.0, "phosphorus": 48.0, "potassium": 40.0, "ph": 6.5
    }, headers=headers).json()["test_id"]

    today = date.today()
    for i in range(30):
        client.post(f"/farms/{farm_id}/weather/manual", json={
            "record_date": str(today - timedelta(days=i)),
            "temperature": 25.0,
            "humidity": 75.0,
            "rainfall_mm": 5.0,
        }, headers=headers)

    # Run recommendation
    rec_res = client.post(f"/farms/{farm_id}/recommend", json={"season": "Kharif"}, headers=headers)
    assert rec_res.status_code == 200, rec_res.text

    # Retrieve history
    hist_res = client.get(f"/farms/{farm_id}/predictions", headers=headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 1
    assert "predicted_on" in history[0]
    assert len(history[0]["crops"]) == 3
    assert history[0]["crops"][0]["rank_no"] == 1
    assert history[0]["crops"][0]["crop_name"] != ""
