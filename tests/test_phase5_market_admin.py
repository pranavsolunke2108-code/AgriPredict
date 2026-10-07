"""Unit and integration tests for Phase 5: Market prices, profit analytics, admin panel, and audit trail."""

from datetime import date, timedelta
import io
import pytest
from fastapi.testclient import TestClient

from app.security import create_access_token


def create_test_farmer(client: TestClient, name="Farmer Ramesh", phone="9876543210", email="ramesh@example.com", district="Pune", role="farmer", is_active=True):
    """Helper to register and optionally elevate a farmer/admin."""
    resp = client.post(
        "/auth/register",
        json={
            "name": name,
            "phone": phone,
            "email": email,
            "password": "SecretPassword123",
            "district": district,
            "village": "Haveli",
            "language": "en",
        },
    )
    assert resp.status_code == 201, resp.text
    farmer_data = resp.json()
    farmer_id = farmer_data["farmer_id"]

    # If admin role or custom active status requested, update directly in test DB
    from app import db
    if role != "farmer" or not is_active:
        db.execute_update(
            "UPDATE farmers SET role = %s, is_active = %s WHERE farmer_id = %s",
            (role, 1 if is_active else 0, farmer_id),
        )

    # Generate token
    token = create_access_token({"sub": str(farmer_id), "role": role})
    headers = {"Authorization": f"Bearer {token}"}
    return farmer_id, headers


def test_admin_access_control_and_farmer_rejection(client: TestClient):
    """Verify that regular farmers receive HTTP 403 Forbidden on all admin endpoints."""
    farmer_id, farmer_headers = create_test_farmer(client, phone="9111111111", email="regular@test.com")

    # Farmer tries to access admin crops
    res1 = client.get("/admin/crops", headers=farmer_headers)
    assert res1.status_code == 403
    assert "Administrator privileges required" in res1.json()["detail"]

    # Farmer tries to access admin audit log
    res2 = client.get("/admin/audit-log", headers=farmer_headers)
    assert res2.status_code == 403

    # Farmer tries to access user list
    res3 = client.get("/admin/users", headers=farmer_headers)
    assert res3.status_code == 403

    # Farmer tries to upload CSV
    csv_file = io.BytesIO(b"crop_name,district,price_per_quintal,price_date\nRice,Pune,2500,2026-10-01\n")
    res4 = client.post("/admin/market-prices/upload-csv", files={"file": ("prices.csv", csv_file, "text/csv")}, headers=farmer_headers)
    assert res4.status_code == 403


def test_farm_ownership_on_profit_estimates(client: TestClient):
    """Verify that farmers cannot query profit estimates for farms they do not own."""
    f1_id, f1_headers = create_test_farmer(client, name="Farmer 1", phone="9222222221", email="f1@test.com")
    f2_id, f2_headers = create_test_farmer(client, name="Farmer 2", phone="9222222222", email="f2@test.com")

    # Farmer 1 creates a farm
    farm_resp = client.post(
        "/farms",
        json={"farm_name": "Farmer 1 Plot", "area_acres": 5.0, "latitude": 18.52, "longitude": 73.85, "soil_type": "Black", "irrigation": "Well"},
        headers=f1_headers,
    )
    assert farm_resp.status_code == 201
    farm_id = farm_resp.json()["farm_id"]

    # Farmer 2 tries to access Farmer 1's profit estimates -> 403
    resp1 = client.get(f"/farms/{farm_id}/profit-estimates", headers=f2_headers)
    assert resp1.status_code == 403
    assert "permission" in resp1.json()["detail"].lower()

    # Farmer 2 tries to access Farmer 1's crop profit -> 403
    resp2 = client.get(f"/farms/{farm_id}/crops/1/profit", headers=f2_headers)
    assert resp2.status_code == 403
    assert "permission" in resp2.json()["detail"].lower()


def test_profit_estimates_no_recommendations_and_with_recommendations(client: TestClient):
    """Verify profit estimates return a friendly message when empty, and calculated values when predictions exist."""
    farmer_id, headers = create_test_farmer(client, name="Profit Farmer", phone="9333333331", email="profit@test.com", district="Pune")

    farm_resp = client.post(
        "/farms",
        json={"farm_name": "Krishna Farm", "area_acres": 4.0, "latitude": 18.52, "longitude": 73.85, "soil_type": "Black"},
        headers=headers,
    )
    farm_id = farm_resp.json()["farm_id"]

    # 1. No recommendations run yet -> friendly message
    resp_empty = client.get(f"/farms/{farm_id}/profit-estimates", headers=headers)
    assert resp_empty.status_code == 200
    data_empty = resp_empty.json()
    assert "No crop recommendations found" in data_empty["message"]
    assert data_empty["estimates"] == []

    # 2. Single crop profit without market price -> 'no price data available'
    resp_crop_no_price = client.get(f"/farms/{farm_id}/crops/1/profit", headers=headers)
    assert resp_crop_no_price.status_code == 200
    assert resp_crop_no_price.json()["message"] == "no price data available"

    # 3. Add mandi market price as Admin
    admin_id, admin_headers = create_test_farmer(client, name="Admin User", phone="9333333339", email="admin@test.com", role="admin")
    price_resp = client.post(
        "/admin/market-prices",
        json={"crop_id": 1, "district": "Pune", "price_per_quintal": 2200.0, "price_date": "2026-10-01"},
        headers=admin_headers,
    )
    assert price_resp.status_code == 200

    # 4. Now query single crop profit -> has revenue, profit
    resp_crop_profit = client.get(f"/farms/{farm_id}/crops/1/profit", headers=headers)
    assert resp_crop_profit.status_code == 200
    crop_data = resp_crop_profit.json()
    assert crop_data["message"] == "Profit estimated successfully"
    assert crop_data["price_per_quintal"] == 2200.0
    assert crop_data["revenue_per_acre"] is not None
    assert crop_data["profit_per_acre"] is not None
    assert crop_data["profit_for_farm"] is not None


def test_market_prices_upsert_no_duplicates(client: TestClient):
    """Verify that posting market prices with same crop/district/date updates existing row rather than duplicating."""
    admin_id, admin_headers = create_test_farmer(client, name="Admin Rates", phone="9444444441", email="rates@test.com", role="admin")

    # Insert price 1
    r1 = client.post(
        "/admin/market-prices",
        json={"crop_id": 1, "district": "Nashik", "price_per_quintal": 2400.0, "price_date": "2026-10-02"},
        headers=admin_headers,
    )
    assert r1.status_code == 200

    # Insert price 2 (upsert: same crop, district, date, updated price)
    r2 = client.post(
        "/admin/market-prices",
        json={"crop_id": 1, "district": "Nashik", "price_per_quintal": 2650.0, "price_date": "2026-10-02"},
        headers=admin_headers,
    )
    assert r2.status_code == 200

    # Query latest prices for Nashik
    farmer_id, f_headers = create_test_farmer(client, phone="9444444442", email="nashik@test.com", district="Nashik")
    prices_list = client.get("/prices?crop_id=1&district=Nashik", headers=f_headers).json()
    assert len(prices_list) == 1
    assert prices_list[0]["price_per_quintal"] == 2650.0


def test_delete_used_crop_returns_409_conflict(client: TestClient):
    """Verify that deleting a crop referenced by active crop cycles or recommendations returns HTTP 409 Conflict."""
    admin_id, admin_headers = create_test_farmer(client, name="Admin Crops", phone="9555555551", email="cropadmin@test.com", role="admin")
    farmer_id, f_headers = create_test_farmer(client, name="Farmer Cycle", phone="9555555552", email="cyclefarmer@test.com")

    # Create farm and active crop cycle for Crop #1 (Rice)
    farm_resp = client.post("/farms", json={"farm_name": "Rice Farm", "area_acres": 2.0}, headers=f_headers)
    farm_id = farm_resp.json()["farm_id"]

    cycle_resp = client.post(
        f"/farms/{farm_id}/cycles",
        json={"crop_id": 1, "sowing_date": "2026-06-15"},
        headers=f_headers,
    )
    assert cycle_resp.status_code == 201

    # Admin attempts to delete Crop #1 -> must return 409 Conflict
    del_resp = client.delete("/admin/crops/1", headers=admin_headers)
    assert del_resp.status_code == 409
    assert "Cannot delete crop" in del_resp.json()["detail"]
    assert "referenced by" in del_resp.json()["detail"]


def test_admin_audit_log_records_changes(client: TestClient):
    """Verify that admin edits to crops write audit entries containing the admin ID and delta."""
    admin_id, admin_headers = create_test_farmer(client, name="Audit Admin", phone="9666666661", email="auditadmin@test.com", role="admin")

    # Update Crop #2 (Maize)
    update_resp = client.put(
        "/admin/crops/2",
        json={
            "crop_name": "Maize",
            "season": "Kharif",
            "duration_days": 105,
            "min_ph": 5.5,
            "max_ph": 7.0,
            "min_temp": 18.0,
            "max_temp": 28.0,
            "min_humidity": 50.0,
            "max_humidity": 80.0,
            "min_rainfall": 50.0,
            "max_rainfall": 120.0,
            "n_required": 80,
            "p_required": 50,
            "k_required": 25,
            "avg_yield_q_per_acre": 30.0,
            "est_cost_per_acre": 16000.0,
        },
        headers=admin_headers,
    )
    assert update_resp.status_code == 200

    # Query audit log
    audit_resp = client.get("/admin/audit-log?table=crops", headers=admin_headers)
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    assert len(logs) >= 1
    latest_log = logs[0]
    assert latest_log["table_name"] == "crops"
    assert latest_log["action"] == "UPDATE"
    assert f"admin:{admin_id}" in latest_log["changed_by"]


def test_user_active_toggle_by_admin(client: TestClient):
    """Verify admin can deactivate a farmer account and deactivated accounts cannot log in."""
    admin_id, admin_headers = create_test_farmer(client, name="Master Admin", phone="9777777771", email="master@test.com", role="admin")
    farmer_id, f_headers = create_test_farmer(client, name="Subject Farmer", phone="9777777772", email="subject@test.com")

    # Farmer can access /me
    me_resp = client.get("/me", headers=f_headers)
    assert me_resp.status_code == 200

    # Admin deactivates farmer
    patch_resp = client.patch(f"/admin/users/{farmer_id}/active", json={"is_active": False}, headers=admin_headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_active"] is False

    # Farmer tries to access /me -> 403 Forbidden
    me_blocked = client.get("/me", headers=f_headers)
    assert me_blocked.status_code == 403
    assert "inactive" in me_blocked.json()["detail"].lower()

    # Admin reactivates farmer
    patch_resp2 = client.patch(f"/admin/users/{farmer_id}/active", json={"is_active": True}, headers=admin_headers)
    assert patch_resp2.status_code == 200

    # Farmer can access /me again
    me_ok = client.get("/me", headers=f_headers)
    assert me_ok.status_code == 200


def test_csv_bulk_upload_market_prices(client: TestClient):
    """Verify bulk CSV upload imports valid rows and reports row-by-row validation errors."""
    admin_id, admin_headers = create_test_farmer(client, name="CSV Admin", phone="9888888881", email="csvadmin@test.com", role="admin")

    csv_data = (
        "crop_name,district,price_per_quintal,price_date\n"
        "Rice,Pune,2350.50,2026-10-03\n"
        "Wheat,Pune,2450.00,2026-10-03\n"
        "NonExistentCrop,Pune,1500,2026-10-03\n"  # error: crop not found
        "Rice,Pune,-500,2026-10-03\n"             # error: negative price
        "Wheat,Pune,1800,invalid-date\n"          # error: bad date
    )
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))

    upload_resp = client.post(
        "/admin/market-prices/upload-csv",
        files={"file": ("test_prices.csv", file_bytes, "text/csv")},
        headers=admin_headers,
    )
    assert upload_resp.status_code == 200
    res_json = upload_resp.json()
    assert res_json["total_rows"] == 5
    assert res_json["imported"] == 2
    assert len(res_json["errors"]) == 3
    assert any("not found" in err["error"] for err in res_json["errors"])
    assert any("must be positive" in err["error"] for err in res_json["errors"])
    assert any("Invalid date format" in err["error"] for err in res_json["errors"]), f"Actual errors: {res_json['errors']}"


def test_expense_summary_endpoints(client: TestClient):
    """Verify cycle expense summary and farmer category expense breakdown."""
    farmer_id, f_headers = create_test_farmer(client, name="Expense Farmer", phone="9999999991", email="exp@test.com")

    farm_resp = client.post("/farms", json={"farm_name": "Expense Plot", "area_acres": 3.0}, headers=f_headers)
    farm_id = farm_resp.json()["farm_id"]

    cycle_resp = client.post(f"/farms/{farm_id}/cycles", json={"crop_id": 1, "sowing_date": "2026-06-01"}, headers=f_headers)
    cycle_id = cycle_resp.json()["cycle_id"]

    # Add expenses
    client.post(f"/cycles/{cycle_id}/expenses", json={"category": "Seeds", "amount": 3500.0, "expense_date": "2026-06-02"}, headers=f_headers)
    client.post(f"/cycles/{cycle_id}/expenses", json={"category": "Fertilizer", "amount": 6500.0, "expense_date": "2026-06-10"}, headers=f_headers)

    # 1. Cycle expense summary
    summary_resp = client.get(f"/cycles/{cycle_id}/expense-summary", headers=f_headers)
    assert summary_resp.status_code == 200
    categories = summary_resp.json()
    assert len(categories) == 2
    cat_names = [c["category"] for c in categories]
    assert "Seeds" in cat_names
    assert "Fertilizer" in cat_names

    # 2. Dashboard expenses by category
    dash_exp_resp = client.get("/dashboard/expenses-by-category", headers=f_headers)
    assert dash_exp_resp.status_code == 200
    dash_cats = dash_exp_resp.json()
    assert len(dash_cats) >= 2
    fert_item = next(c for c in dash_cats if c["category"] == "Fertilizer")
    assert fert_item["total_amount"] == 6500.0
