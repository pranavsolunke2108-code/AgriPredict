"""Tests for Phase 4: Agronomic Advisory, Crop Calendar, Weather Triggers, Alerts, and Admin Tasks."""

from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient


def register_farmer(client: TestClient, name="Suresh Patil", phone="9876500001", email="suresh@example.com", role="farmer"):
    """Helper to register a farmer and obtain JWT auth headers."""
    resp = client.post(
        "/auth/register",
        json={
            "name": name,
            "phone": phone,
            "email": email,
            "password": "SecurePassword123!",
            "district": "Pune",
            "village": "Baramati",
            "language": "en",
        },
    )
    assert resp.status_code == 201, resp.text
    farmer_id = resp.json()["farmer_id"]

    # Login to get JWT access token
    login_resp = client.post(
        "/auth/login",
        json={
            "identifier": phone,
            "password": "SecurePassword123!",
        },
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]

    # Update role directly if admin requested
    if role == "admin":
        from app import db
        db.execute_update("UPDATE farmers SET role = 'admin' WHERE farmer_id = %s", (farmer_id,))

    return {"Authorization": f"Bearer {token}"}, farmer_id


def create_farm(client: TestClient, headers: dict, name="Green Acres", area=2.5, lat=18.5204, lon=73.8567):
    """Helper to create a test farm."""
    resp = client.post(
        "/farms",
        json={
            "farm_name": name,
            "area_acres": area,
            "latitude": lat,
            "longitude": lon,
            "soil_type": "Black",
            "irrigation": "Drip",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["farm_id"]


def test_fertilizer_advice_default_test_selection(client: TestClient):
    """Verify POST /farms/{farm_id}/fertilizer-advice defaults to the latest soil test if test_id is omitted."""
    headers, _ = register_farmer(client, phone="9876540001", email="fert1@example.com")
    farm_id = create_farm(client, headers, area=2.0)

    # 1. First older test (test_date = 2026-08-01): high nitrogen
    client.post(
        f"/farms/{farm_id}/soil-tests",
        json={
            "test_date": "2026-08-01",
            "nitrogen": 120.0,
            "phosphorus": 60.0,
            "potassium": 50.0,
            "ph": 6.8,
            "moisture": 30.0,
        },
        headers=headers,
    )

    # 2. Second newer test (test_date = 2026-09-15): lower nitrogen (N=40, P=20, K=15) -> Wheat needs N=100, P=50, K=40
    test2_resp = client.post(
        f"/farms/{farm_id}/soil-tests",
        json={
            "test_date": "2026-09-15",
            "nitrogen": 40.0,
            "phosphorus": 20.0,
            "potassium": 15.0,
            "ph": 6.5,
            "moisture": 35.0,
        },
        headers=headers,
    )
    assert test2_resp.status_code == 201
    latest_test_id = test2_resp.json()["test_id"]

    # 3. Call fertilizer advice without specifying test_id
    resp = client.post(
        f"/farms/{farm_id}/fertilizer-advice",
        json={"crop_id": 3},  # Wheat
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["test_id"] == latest_test_id
    assert data["crop_id"] == 3
    assert len(data["fertilizers"]) > 0

    fert_names = [f["fertilizer"] for f in data["fertilizers"]]
    assert "DAP" in fert_names
    assert "Urea" in fert_names
    assert "MOP (Potash)" in fert_names

    for item in data["fertilizers"]:
        assert item["kg_per_acre"] > 0
        assert item["kg_for_farm"] == round(item["kg_per_acre"] * 2.0, 2)
        assert item["estimated_cost"] > 0


def test_fertilizer_advice_empty_result_sufficient_nutrients(client: TestClient):
    """When soil test nutrients meet or exceed crop requirements, return a clear sufficiency message."""
    headers, _ = register_farmer(client, phone="9876540002", email="fert2@example.com")
    farm_id = create_farm(client, headers, area=3.0)

    # Add a soil test with abundant nutrients (exceeding wheat requirements)
    client.post(
        f"/farms/{farm_id}/soil-tests",
        json={
            "test_date": "2026-09-20",
            "nitrogen": 200.0,
            "phosphorus": 100.0,
            "potassium": 100.0,
            "ph": 6.8,
            "moisture": 40.0,
        },
        headers=headers,
    )

    resp = client.post(
        f"/farms/{farm_id}/fertilizer-advice",
        json={"crop_id": 3},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["fertilizers"] == []
    assert "sufficient" in data["message"].lower()


def test_fertilizer_advice_ownership_check(client: TestClient):
    """Farmer B cannot access fertilizer advice for Farmer A's farm."""
    headers_a, _ = register_farmer(client, phone="9876540003", email="ferta@example.com")
    headers_b, _ = register_farmer(client, phone="9876540004", email="fertb@example.com")
    farm_a_id = create_farm(client, headers_a)

    resp = client.post(
        f"/farms/{farm_a_id}/fertilizer-advice",
        json={"crop_id": 1},
        headers=headers_b,
    )
    assert resp.status_code == 403


def test_rotation_advice_empty_when_no_closed_cycle(client: TestClient):
    """GET /farms/{farm_id}/rotation-advice returns a friendly message when farm has no closed cycle."""
    headers, _ = register_farmer(client, phone="9876540005", email="rot1@example.com")
    farm_id = create_farm(client, headers)

    resp = client.get(f"/farms/{farm_id}/rotation-advice", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["advice"] == []
    assert "No completed crop cycle found" in data["message"]


def test_rotation_advice_with_harvested_cycle(client: TestClient):
    """GET /farms/{farm_id}/rotation-advice recommends succession crops after a harvested cycle."""
    headers, _ = register_farmer(client, phone="9876540006", email="rot2@example.com")
    farm_id = create_farm(client, headers)

    # Start a cycle with Rice (crop_id=1)
    cycle_resp = client.post(
        f"/farms/{farm_id}/cycles",
        json={"crop_id": 1, "sowing_date": "2026-05-01"},
        headers=headers,
    )
    assert cycle_resp.status_code == 201
    cycle_id = cycle_resp.json()["cycle_id"]

    # Close cycle as Harvested
    close_resp = client.post(
        f"/cycles/{cycle_id}/close",
        json={"status": "Harvested", "yield_kg": 2500, "price_per_quintal": 2200},
        headers=headers,
    )
    assert close_resp.status_code == 200

    # Request rotation advice
    resp = client.get(f"/farms/{farm_id}/rotation-advice", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["advice"]) > 0

    crops_recommended = [c["crop_name"] for c in data["advice"]]
    assert "Chickpea" in crops_recommended or "Lentil" in crops_recommended


def test_rotation_advice_ownership_check(client: TestClient):
    """Farmer B cannot access rotation advice for Farmer A's farm."""
    headers_a, _ = register_farmer(client, phone="9876540007", email="rota@example.com")
    headers_b, _ = register_farmer(client, phone="9876540008", email="rotb@example.com")
    farm_a = create_farm(client, headers_a)

    resp = client.get(f"/farms/{farm_a}/rotation-advice", headers=headers_b)
    assert resp.status_code == 403


def test_crop_calendar_timeline_and_ownership(client: TestClient):
    """GET /cycles/{cycle_id}/calendar returns stages with Done/Current/Upcoming status and tasks."""
    headers_a, _ = register_farmer(client, phone="9876540009", email="cal_a@example.com")
    headers_b, _ = register_farmer(client, phone="9876540010", email="cal_b@example.com")
    farm_id = create_farm(client, headers_a)

    # Sowing date 30 days ago: CRI (0-25 days) should be 'Done', Tillering (26-60 days) should be 'Current'
    sow_date = (date.today() - timedelta(days=30)).isoformat()
    cycle_resp = client.post(
        f"/farms/{farm_id}/cycles",
        json={"crop_id": 3, "sowing_date": sow_date},  # Wheat has stages seeded
        headers=headers_a,
    )
    assert cycle_resp.status_code == 201
    cycle_id = cycle_resp.json()["cycle_id"]

    # Verify calendar output
    cal_resp = client.get(f"/cycles/{cycle_id}/calendar", headers=headers_a)
    assert cal_resp.status_code == 200, cal_resp.text
    stages = cal_resp.json()
    assert len(stages) >= 4

    cri_stage = next((s for s in stages if s["stage_name"] == "Crown Root Initiation (CRI)"), None)
    assert cri_stage is not None
    assert cri_stage["stage_status"] == "Done"
    assert "irrigation" in cri_stage["task"].lower()

    tillering = next((s for s in stages if s["stage_name"] == "Tillering & Jointing"), None)
    assert tillering is not None
    assert tillering["stage_status"] == "Current"

    grain_fill = next((s for s in stages if s["stage_name"] == "Grain Filling & Maturity"), None)
    assert grain_fill is not None
    assert grain_fill["stage_status"] == "Upcoming"

    # Verify Farmer B cannot view Farmer A's cycle calendar
    forbidden_resp = client.get(f"/cycles/{cycle_id}/calendar", headers=headers_b)
    assert forbidden_resp.status_code == 403


def test_weather_triggers_create_alerts(client: TestClient):
    """Inserting weather_records triggers automatic creation of weather alerts without backend intervention."""
    headers, _ = register_farmer(client, phone="9876540011", email="weather_alert@example.com")
    farm_id = create_farm(client, headers)

    # Insert heavy rainfall (> 50mm) and high temperature (> 38C)
    weather_resp = client.post(
        f"/farms/{farm_id}/weather/manual",
        json={
            "record_date": "2026-10-01",
            "temperature": 41.5,
            "humidity": 45.0,
            "rainfall_mm": 65.0,
        },
        headers=headers,
    )
    assert weather_resp.status_code == 201

    # Fetch alerts for this farmer
    alerts_resp = client.get("/alerts", headers=headers)
    assert alerts_resp.status_code == 200, alerts_resp.text
    alerts = alerts_resp.json()
    assert len(alerts) >= 2

    alert_types = [a["alert_type"] for a in alerts]
    assert "Rain" in alert_types
    assert "Heat" in alert_types


def test_alert_read_and_unread_handling(client: TestClient):
    """Test GET /alerts?unread=true, GET /alerts/unread-count, PATCH /alerts/{id}/read, POST /alerts/read-all."""
    headers, _ = register_farmer(client, phone="9876540012", email="read_alerts@example.com")
    farm_id = create_farm(client, headers)

    # Insert extreme weather to trigger 2 alerts
    client.post(
        f"/farms/{farm_id}/weather/manual",
        json={
            "record_date": "2026-10-02",
            "temperature": 42.0,
            "humidity": 50.0,
            "rainfall_mm": 70.0,
        },
        headers=headers,
    )

    # Check unread count
    count_resp = client.get("/alerts/unread-count", headers=headers)
    assert count_resp.status_code == 200
    assert count_resp.json()["unread_count"] >= 2

    # Fetch unread alerts
    unread_resp = client.get("/alerts?unread=true", headers=headers)
    assert unread_resp.status_code == 200
    alerts = unread_resp.json()
    first_alert_id = alerts[0]["alert_id"]

    # Mark first alert as read
    patch_resp = client.patch(f"/alerts/{first_alert_id}/read", headers=headers)
    assert patch_resp.status_code == 200

    # Unread count should decrease by 1
    count_after_one = client.get("/alerts/unread-count", headers=headers).json()["unread_count"]
    assert count_after_one == len(alerts) - 1

    # Mark all alerts as read
    read_all_resp = client.post("/alerts/read-all", headers=headers)
    assert read_all_resp.status_code == 200

    final_count = client.get("/alerts/unread-count", headers=headers).json()["unread_count"]
    assert final_count == 0


def test_alert_ownership_check(client: TestClient):
    """Farmer B cannot read Farmer A's alerts, nor see them in /alerts."""
    headers_a, _ = register_farmer(client, phone="9876540013", email="alerta@example.com")
    headers_b, _ = register_farmer(client, phone="9876540014", email="alertb@example.com")
    farm_a = create_farm(client, headers_a)

    client.post(
        f"/farms/{farm_a}/weather/manual",
        json={
            "record_date": "2026-10-03",
            "temperature": 2.0,  # triggers Frost alert
            "humidity": 50.0,
            "rainfall_mm": 0.0,
        },
        headers=headers_a,
    )

    alerts_a = client.get("/alerts", headers=headers_a).json()
    assert len(alerts_a) > 0
    target_alert_id = alerts_a[0]["alert_id"]

    # Farmer B sees 0 alerts
    alerts_b = client.get("/alerts", headers=headers_b).json()
    assert len(alerts_b) == 0

    # Farmer B tries to mark Farmer A's alert as read
    resp = client.patch(f"/alerts/{target_alert_id}/read", headers=headers_b)
    assert resp.status_code == 403


def test_admin_run_task_alerts(client: TestClient):
    """Regular farmer cannot trigger admin task alert runner; admin can trigger it."""
    headers_farmer, _ = register_farmer(client, phone="9876540015", email="farmer_reg@example.com", role="farmer")
    headers_admin, _ = register_farmer(client, phone="9876540016", email="admin_user@example.com", role="admin")

    # Regular farmer -> 403
    forbidden_resp = client.post("/admin/run-task-alerts", headers=headers_farmer)
    assert forbidden_resp.status_code == 403

    # Admin farmer -> 200
    ok_resp = client.post("/admin/run-task-alerts?days_ahead=3", headers=headers_admin)
    assert ok_resp.status_code == 200, ok_resp.text
    assert "executed successfully" in ok_resp.json()["detail"]
