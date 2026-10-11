"""Comprehensive test suite for Phase 3: Dashboard Views, Crop Cycles, Expenses, and Ownership Isolation."""

from datetime import date, timedelta
import pytest
from app import db


def get_farmer_auth(client, phone: str, name: str = "Test Farmer"):
    """Helper to register and login a farmer, returning auth headers and farmer info."""
    client.post("/auth/register", json={
        "name": name,
        "phone": phone,
        "password": "password123",
        "district": "Pune",
        "village": "Baramati",
    })
    res = client.post("/auth/login", json={
        "identifier": phone,
        "password": "password123",
    })
    data = res.json()
    token = data["access_token"]
    farmer_id = data["farmer"]["farmer_id"]
    return {"Authorization": f"Bearer {token}"}, farmer_id


# =============================================================================
# 1. Starting Crop Cycles & One-Active-Cycle Rule
# =============================================================================

def test_start_crop_cycle_success_and_trigger_rule(client):
    """Test starting a cycle, calculating harvest date, and enforcing one-active-cycle rule."""
    headers, farmer_id = get_farmer_auth(client, "9876500001", "Cycle Farmer")

    # Create farm
    farm_res = client.post("/farms", json={"farm_name": "Plot Alpha", "area_acres": 5.0}, headers=headers)
    assert farm_res.status_code == 201
    farm_id = farm_res.json()["farm_id"]

    # 1. Start a cycle (Rice = crop_id 1, duration 120 days)
    today = date.today()
    start_res = client.post(
        f"/farms/{farm_id}/cycles",
        json={"crop_id": 1, "sowing_date": str(today)},
        headers=headers,
    )
    assert start_res.status_code == 201, start_res.text
    cycle_data = start_res.json()
    assert cycle_data["cycle_id"] > 0
    assert cycle_data["farm_id"] == farm_id
    assert cycle_data["crop_id"] == 1
    assert cycle_data["status"] == "Growing"
    assert cycle_data["crop_name"] == "Rice"
    assert cycle_data["expected_harvest"] == str(today + timedelta(days=120))

    # 2. Attempt to start a SECOND active cycle on the same farm -> must return 400
    second_res = client.post(
        f"/farms/{farm_id}/cycles",
        json={"crop_id": 2, "sowing_date": str(today)},
        headers=headers,
    )
    assert second_res.status_code == 400
    assert "already has an active" in second_res.json()["detail"].lower()


def test_start_cycle_with_prediction_link(client):
    """Test linking a cycle to an existing prediction_id."""
    headers, farmer_id = get_farmer_auth(client, "9876500002", "Predict Farmer")
    farm_id = client.post("/farms", json={"farm_name": "Plot Beta", "area_acres": 4.0}, headers=headers).json()["farm_id"]

    # Insert a fake prediction row to link against
    pred_id = db.execute_insert(
        """
        INSERT INTO predictions (farm_id, test_id, crop_id, suitability_score, rank_no)
        VALUES (%s, 1, 1, 88.5, 1)
        """,
        (farm_id,),
    )

    start_res = client.post(
        f"/farms/{farm_id}/cycles",
        json={"crop_id": 1, "prediction_id": pred_id},
        headers=headers,
    )
    assert start_res.status_code == 201
    cycle = start_res.json()
    assert cycle["prediction_id"] == pred_id


# =============================================================================
# 2. Ownership Checks
# =============================================================================

def test_crop_cycle_ownership_isolation(client):
    """Farmer B must not be able to start, close, or view Farmer A's cycles."""
    headers_a, farmer_a_id = get_farmer_auth(client, "9876500010", "Farmer A")
    headers_b, farmer_b_id = get_farmer_auth(client, "9876500011", "Farmer B")

    # Farmer A creates farm and cycle
    farm_a_id = client.post("/farms", json={"farm_name": "Farm A", "area_acres": 3.0}, headers=headers_a).json()["farm_id"]
    cycle_a_id = client.post(f"/farms/{farm_a_id}/cycles", json={"crop_id": 1}, headers=headers_a).json()["cycle_id"]

    # 1. Farmer B attempts to start cycle on Farmer A's farm -> 403 Forbidden
    res_b_start = client.post(f"/farms/{farm_a_id}/cycles", json={"crop_id": 2}, headers=headers_b)
    assert res_b_start.status_code == 403

    # 2. Farmer B attempts to view Farmer A's cycle details -> 403 Forbidden
    res_b_view = client.get(f"/cycles/{cycle_a_id}", headers=headers_b)
    assert res_b_view.status_code == 403

    # 3. Farmer B attempts to view Farmer A's cycle audit log -> 403 Forbidden
    res_b_log = client.get(f"/cycles/{cycle_a_id}/log", headers=headers_b)
    assert res_b_log.status_code == 403

    # 4. Farmer B attempts to close Farmer A's cycle -> 403 Forbidden
    res_b_close = client.post(f"/cycles/{cycle_a_id}/close", json={"status": "Failed"}, headers=headers_b)
    assert res_b_close.status_code == 403


# =============================================================================
# 3. Expenses CRUD and Ownership
# =============================================================================

def test_cycle_expenses_crud_and_ownership(client):
    """Test adding, listing, and deleting expenses with cycle-to-farm ownership validation."""
    headers_a, farmer_a_id = get_farmer_auth(client, "9876500020", "Expense Farmer A")
    headers_b, farmer_b_id = get_farmer_auth(client, "9876500021", "Expense Farmer B")

    farm_id = client.post("/farms", json={"farm_name": "Cash Farm", "area_acres": 8.0}, headers=headers_a).json()["farm_id"]
    cycle_id = client.post(f"/farms/{farm_id}/cycles", json={"crop_id": 1}, headers=headers_a).json()["cycle_id"]

    # 1. Negative amount rejected by schema
    bad_exp = client.post(
        f"/cycles/{cycle_id}/expenses",
        json={"category": "Seeds", "amount": -100.0},
        headers=headers_a,
    )
    assert bad_exp.status_code == 422

    # 2. Create valid expenses
    exp1 = client.post(
        f"/cycles/{cycle_id}/expenses",
        json={"category": "Seeds", "amount": 1500.0, "notes": "Certified paddy seeds"},
        headers=headers_a,
    ).json()
    assert exp1["expense_id"] > 0
    assert exp1["category"] == "Seeds"
    assert exp1["amount"] == 1500.0

    exp2 = client.post(
        f"/cycles/{cycle_id}/expenses",
        json={"category": "Fertilizer", "amount": 2500.0, "notes": "Urea & DAP"},
        headers=headers_a,
    ).json()

    # 3. List expenses
    list_res = client.get(f"/cycles/{cycle_id}/expenses", headers=headers_a)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 2

    # 4. Farmer B attempts to add expense to Farmer A's cycle -> 403 Forbidden
    res_b_add = client.post(
        f"/cycles/{cycle_id}/expenses",
        json={"category": "Labour", "amount": 500.0},
        headers=headers_b,
    )
    assert res_b_add.status_code == 403

    # 5. Farmer B attempts to delete Farmer A's expense -> 403 Forbidden
    res_b_del = client.delete(f"/expenses/{exp1['expense_id']}", headers=headers_b)
    assert res_b_del.status_code == 403

    # 6. Farmer A deletes expense successfully
    del_res = client.delete(f"/expenses/{exp1['expense_id']}", headers=headers_a)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify only 1 expense remains
    remaining = client.get(f"/cycles/{cycle_id}/expenses", headers=headers_a).json()
    assert len(remaining) == 1
    assert remaining[0]["expense_id"] == exp2["expense_id"]


# =============================================================================
# 4. Closing Crop Cycle & Audit Log
# =============================================================================

def test_close_crop_cycle_harvested_and_failed(client):
    """Test closing cycle as Harvested and Failed, and verifying audit log."""
    headers, farmer_id = get_farmer_auth(client, "9876500030", "Close Farmer")
    farm_id = client.post("/farms", json={"farm_name": "Harvest Farm", "area_acres": 5.0}, headers=headers).json()["farm_id"]
    cycle_id = client.post(f"/farms/{farm_id}/cycles", json={"crop_id": 1}, headers=headers).json()["cycle_id"]

    # 1. Closing with status 'Harvested' without yield should fail validation
    bad_close = client.post(
        f"/cycles/{cycle_id}/close",
        json={"status": "Harvested", "yield_kg": None},
        headers=headers,
    )
    assert bad_close.status_code == 422 or bad_close.status_code == 400

    # 2. Close cycle successfully as Harvested
    close_res = client.post(
        f"/cycles/{cycle_id}/close",
        json={
            "status": "Harvested",
            "yield_kg": 4500.0,
            "price_per_quintal": 2200.0,
        },
        headers=headers,
    )
    assert close_res.status_code == 200, close_res.text
    closed = close_res.json()
    assert closed["status"] == "Harvested"
    assert closed["yield_kg"] == 4500.0
    assert closed["selling_price_per_quintal"] == 2200.0

    # 3. Attempting to close or reopen an already closed cycle -> 400 Bad Request
    reclose = client.post(
        f"/cycles/{cycle_id}/close",
        json={"status": "Failed"},
        headers=headers,
    )
    assert reclose.status_code == 400
    assert "cannot be reopened" in reclose.json()["detail"].lower()

    # 4. Check audit log has both creation and harvest transitions
    log_res = client.get(f"/cycles/{cycle_id}/log", headers=headers)
    assert log_res.status_code == 200
    logs = log_res.json()
    assert len(logs) >= 2
    assert logs[0]["old_status"] is None
    assert logs[0]["new_status"] == "Growing"
    assert logs[1]["old_status"] == "Growing"
    assert logs[1]["new_status"] == "Harvested"


# =============================================================================
# 5. Dashboard Views: Summary, Current Status, History
# =============================================================================

def test_dashboard_summary_current_and_history(client):
    """Test GET /dashboard/summary, /dashboard/current, and /dashboard/history."""
    headers, farmer_id = get_farmer_auth(client, "9876500040", "Dashboard Farmer")

    # Create farm 1 and start an active cycle
    farm1_id = client.post("/farms", json={"farm_name": "Active Plot", "area_acres": 6.0}, headers=headers).json()["farm_id"]
    cycle1_id = client.post(f"/farms/{farm1_id}/cycles", json={"crop_id": 1}, headers=headers).json()["cycle_id"]
    # Add expense to active cycle
    client.post(f"/cycles/{cycle1_id}/expenses", json={"category": "Fertilizer", "amount": 3000.0}, headers=headers)

    # Create farm 2, start cycle, add expense, and harvest it
    farm2_id = client.post("/farms", json={"farm_name": "History Plot", "area_acres": 4.0}, headers=headers).json()["farm_id"]
    cycle2_id = client.post(f"/farms/{farm2_id}/cycles", json={"crop_id": 2}, headers=headers).json()["cycle_id"]
    client.post(f"/cycles/{cycle2_id}/expenses", json={"category": "Seeds", "amount": 1000.0}, headers=headers)
    client.post(
        f"/cycles/{cycle2_id}/close",
        json={"status": "Harvested", "yield_kg": 3000.0, "price_per_quintal": 2000.0},
        headers=headers,
    )
    # Expected revenue for cycle2: (3000 kg / 100) * 2000 = 60,000
    # Expected profit for cycle2: 60,000 - 1000 = 59,000

    # 1. GET /dashboard/summary
    sum_res = client.get("/dashboard/summary", headers=headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["farmer_id"] == farmer_id
    assert summary["total_farms"] == 2
    assert summary["active_cycles"] == 1
    assert summary["completed_cycles"] == 1
    assert summary["total_revenue"] == 60000.0
    assert summary["total_expenses"] == 1000.0
    assert summary["net_profit"] == 59000.0

    # 2. GET /dashboard/current
    curr_res = client.get("/dashboard/current", headers=headers)
    assert curr_res.status_code == 200
    active_list = curr_res.json()
    assert len(active_list) == 1
    active_item = active_list[0]
    assert active_item["cycle_id"] == cycle1_id
    assert active_item["crop_name"] == "Rice"
    assert active_item["status"] == "Growing"
    assert active_item["expenses_so_far"] == 3000.0

    # 3. GET /dashboard/history with filters
    hist_res = client.get("/dashboard/history", headers=headers)
    assert hist_res.status_code == 200
    hist_list = hist_res.json()
    assert len(hist_list) == 1
    item = hist_list[0]
    assert item["cycle_id"] == cycle2_id
    assert item["status"] == "Harvested"
    assert item["revenue"] == 60000.0
    assert item["profit"] == 59000.0

    # History filtering by farm_id
    f_match = client.get(f"/dashboard/history?farm_id={farm2_id}", headers=headers).json()
    assert len(f_match) == 1
    f_none = client.get(f"/dashboard/history?farm_id={farm1_id}", headers=headers).json()
    assert len(f_none) == 0

    # History filtering by crop name
    c_match = client.get("/dashboard/history?crop=Maize", headers=headers).json()
    assert len(c_match) == 1
    c_none = client.get("/dashboard/history?crop=Wheat", headers=headers).json()
    assert len(c_none) == 0


def test_translations_endpoint(client):
    """Test GET /translations returns multilingual UI keys."""
    res_en = client.get("/translations?lang=en")
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert "login" in data_en
    assert data_en["login"] == "Login"

    res_mr = client.get("/translations?lang=mr")
    assert res_mr.status_code == 200
    data_mr = res_mr.json()
    assert "login" in data_mr
    assert data_mr["login"] != ""


def test_frontend_ui_pages(client):
    """Test that frontend static HTML pages and redirect endpoints are served properly."""
    res_login = client.get("/ui/login")
    assert res_login.status_code == 200
    assert "AgriPredict" in res_login.text

    res_reg = client.get("/ui/register")
    assert res_reg.status_code == 200
    assert "Create Account" in res_reg.text

    headers, _ = get_farmer_auth(client, "9876500050", "UI Farmer")

    res_dash = client.get("/ui/dashboard", headers=headers)
    assert res_dash.status_code == 200
    assert "Farming Overview" in res_dash.text

    res_farms = client.get("/ui/farms", headers=headers)
    assert res_farms.status_code == 200
    assert "My Farms" in res_farms.text

    res_cycle = client.get("/ui/cycle-detail", headers=headers)
    assert res_cycle.status_code == 200
    assert "Crop Cycle Details" in res_cycle.text

    res_alerts = client.get("/ui/alerts", headers=headers)
    assert res_alerts.status_code == 200
    assert "Field Alerts" in res_alerts.text

    # Root endpoint browser redirect
    res_root = client.get("/", headers={"Accept": "text/html"})
    assert res_root.status_code in (200, 307)


