
"""Comprehensive automated tests for authentication, authorization, and farm CRUD."""

import pytest
from app import db
from app.security import hash_password


def test_register_farmer_success(client):
    """Test successful registration of a new farmer."""
    payload = {
        "name": "Ramesh Kumar",
        "phone": "9876543210",
        "email": "ramesh@example.com",
        "password": "securepassword123",
        "district": "Pune",
        "village": "Baramati",
        "language": "mr",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "Ramesh Kumar"
    assert data["phone"] == "9876543210"
    assert data["email"] == "ramesh@example.com"
    assert data["district"] == "Pune"
    assert data["village"] == "Baramati"
    assert data["language"] == "mr"
    assert data["role"] == "farmer"
    assert data["is_active"] is True
    assert "password_hash" not in data


def test_register_validation_failures(client):
    """Test that invalid inputs are rejected with 422."""
    # Password too short (< 6 chars)
    res1 = client.post("/auth/register", json={
        "name": "Invalid Farmer",
        "phone": "9876543210",
        "password": "123",
    })
    assert res1.status_code == 422

    # Phone too short
    res2 = client.post("/auth/register", json={
        "name": "Invalid Farmer",
        "phone": "12345",
        "password": "validpassword",
    })
    assert res2.status_code == 422


def test_register_duplicate_phone_rejected(client):
    """Test that duplicate phone numbers are rejected with 409 Conflict."""
    payload1 = {
        "name": "Farmer One",
        "phone": "9876543211",
        "email": "farmer1@example.com",
        "password": "password123",
    }
    res1 = client.post("/auth/register", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "name": "Farmer Two",
        "phone": "9876543211",  # Same phone
        "email": "farmer2@example.com",
        "password": "password123",
    }
    res2 = client.post("/auth/register", json=payload2)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"]


def test_register_duplicate_email_rejected(client):
    """Test that duplicate email addresses are rejected with 409 Conflict."""
    client.post("/auth/register", json={
        "name": "Farmer A",
        "phone": "9876543212",
        "email": "shared@example.com",
        "password": "password123",
    })

    res = client.post("/auth/register", json={
        "name": "Farmer B",
        "phone": "9876543213",
        "email": "shared@example.com",
        "password": "password123",
    })
    assert res.status_code == 409
    assert "already registered" in res.json()["detail"]


def test_login_success_with_phone_and_email(client):
    """Test login using both phone number and email."""
    # Register farmer
    client.post("/auth/register", json={
        "name": "Sunil Patil",
        "phone": "9876543214",
        "email": "sunil@example.com",
        "password": "password123",
    })

    # Login via phone
    res_phone = client.post("/auth/login", json={
        "identifier": "9876543214",
        "password": "password123",
    })
    assert res_phone.status_code == 200
    data_phone = res_phone.json()
    assert "access_token" in data_phone
    assert data_phone["token_type"] == "bearer"
    assert data_phone["farmer"]["name"] == "Sunil Patil"

    # Login via email
    res_email = client.post("/auth/login", json={
        "identifier": "sunil@example.com",
        "password": "password123",
    })
    assert res_email.status_code == 200
    data_email = res_email.json()
    assert "access_token" in data_email


def test_login_invalid_credentials(client):
    """Test that wrong password or non-existent user returns 401."""
    client.post("/auth/register", json={
        "name": "Test Farmer",
        "phone": "9876543215",
        "password": "correctpassword",
    })

    # Wrong password
    res1 = client.post("/auth/login", json={
        "identifier": "9876543215",
        "password": "wrongpassword",
    })
    assert res1.status_code == 401

    # Non-existent user
    res2 = client.post("/auth/login", json={
        "identifier": "9999999999",
        "password": "any_password",
    })
    assert res2.status_code == 401


def test_login_inactive_user_rejected(client):
    """Test that inactive farmer account login is rejected with 403."""
    reg = client.post("/auth/register", json={
        "name": "Inactive Farmer",
        "phone": "9876543216",
        "password": "password123",
    })
    farmer_id = reg.json()["farmer_id"]

    # Deactivate in database
    db.execute_update("UPDATE farmers SET is_active = 0 WHERE farmer_id = %s", (farmer_id,))

    res = client.post("/auth/login", json={
        "identifier": "9876543216",
        "password": "password123",
    })
    assert res.status_code == 403
    assert "inactive" in res.json()["detail"].lower()


def test_get_me_profile(client):
    """Test GET /me endpoint with and without valid JWT."""
    # Without token
    res_no_auth = client.get("/me")
    assert res_no_auth.status_code == 401

    # Register and login
    client.post("/auth/register", json={
        "name": "Anita Deshmukh",
        "phone": "9876543217",
        "password": "password123",
        "district": "Nashik",
    })
    login_res = client.post("/auth/login", json={
        "identifier": "9876543217",
        "password": "password123",
    })
    token = login_res.json()["access_token"]

    # With valid Bearer token
    res_auth = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert res_auth.status_code == 200
    profile = res_auth.json()
    assert profile["name"] == "Anita Deshmukh"
    assert profile["phone"] == "9876543217"
    assert profile["district"] == "Nashik"


def test_admin_role_check(client):
    """Test require_admin() dependency on /admin/overview."""
    # 1. Normal farmer access -> 403 Forbidden
    client.post("/auth/register", json={
        "name": "Regular Farmer",
        "phone": "9876543218",
        "password": "password123",
    })
    login_farmer = client.post("/auth/login", json={
        "identifier": "9876543218",
        "password": "password123",
    })
    farmer_token = login_farmer.json()["access_token"]

    res_forbidden = client.get(
        "/admin/overview",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert res_forbidden.status_code == 403
    assert "Administrator privileges required" in res_forbidden.json()["detail"]

    # 2. Insert admin into database and access -> 200 OK
    admin_pw_hash = hash_password("adminpass123")
    db.execute_insert(
        """
        INSERT INTO farmers (name, phone, email, password_hash, district, village, language, role, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'admin', 1)
        """,
        ("Admin User", "9998887770", "admin@agripredict.in", admin_pw_hash, "Admin HQ", "Central", "en"),
    )

    login_admin = client.post("/auth/login", json={
        "identifier": "9998887770",
        "password": "adminpass123",
    })
    admin_token = login_admin.json()["access_token"]

    res_admin = client.get(
        "/admin/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    overview = res_admin.json()
    assert overview["admin"]["role"] == "admin"
    assert "statistics" in overview


def test_farm_crud_and_ownership_isolation(client):
    """Test Farm CRUD operations and strict farmer ownership isolation."""
    # Create Farmer 1
    client.post("/auth/register", json={
        "name": "Farmer One",
        "phone": "9876543221",
        "password": "password123",
    })
    login1 = client.post("/auth/login", json={
        "identifier": "9876543221",
        "password": "password123",
    })
    token1 = login1.json()["access_token"]
    farmer1_id = login1.json()["farmer"]["farmer_id"]

    # Create Farmer 2
    client.post("/auth/register", json={
        "name": "Farmer Two",
        "phone": "9876543222",
        "password": "password123",
    })
    login2 = client.post("/auth/login", json={
        "identifier": "9876543222",
        "password": "password123",
    })
    token2 = login2.json()["access_token"]

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 1. Farmer 1 creates a farm
    farm_payload = {
        "farm_name": "Krishna Valley Farm",
        "area_acres": 4.5,
        "latitude": 18.52043,
        "longitude": 73.85674,
        "soil_type": "Black",
        "irrigation": "Drip",
    }
    create_res = client.post("/farms", json=farm_payload, headers=headers1)
    assert create_res.status_code == 201
    farm1 = create_res.json()
    assert farm1["farm_name"] == "Krishna Valley Farm"
    assert farm1["farmer_id"] == farmer1_id
    assert farm1["area_acres"] == 4.5
    assert farm1["soil_type"] == "Black"
    assert farm1["irrigation"] == "Drip"
    farm1_id = farm1["farm_id"]

    # 2. Farmer 1 lists farms -> sees farm1
    list1 = client.get("/farms", headers=headers1)
    assert list1.status_code == 200
    assert len(list1.json()) == 1
    assert list1.json()[0]["farm_id"] == farm1_id

    # 3. Farmer 2 lists farms -> does NOT see Farmer 1's farm
    list2 = client.get("/farms", headers=headers2)
    assert list2.status_code == 200
    assert len(list2.json()) == 0

    # 4. Farmer 2 tries to GET Farmer 1's farm -> 403 Forbidden
    get_forbidden = client.get(f"/farms/{farm1_id}", headers=headers2)
    assert get_forbidden.status_code == 403

    # 5. Farmer 2 tries to UPDATE Farmer 1's farm -> 403 Forbidden
    put_forbidden = client.put(
        f"/farms/{farm1_id}",
        json={"farm_name": "Hijacked Farm"},
        headers=headers2,
    )
    assert put_forbidden.status_code == 403

    # 6. Farmer 2 tries to DELETE Farmer 1's farm -> 403 Forbidden
    del_forbidden = client.delete(f"/farms/{farm1_id}", headers=headers2)
    assert del_forbidden.status_code == 403

    # 7. Farmer 1 updates their own farm -> 200 OK
    update_res = client.put(
        f"/farms/{farm1_id}",
        json={"farm_name": "Krishna Valley Organic Plot", "area_acres": 5.0},
        headers=headers1,
    )
    assert update_res.status_code == 200
    assert update_res.json()["farm_name"] == "Krishna Valley Organic Plot"
    assert update_res.json()["area_acres"] == 5.0

    # 8. Farmer 1 deletes their own farm -> 200 OK
    delete_res = client.delete(f"/farms/{farm1_id}", headers=headers1)
    assert delete_res.status_code == 200

    # 9. Verifying farm no longer exists -> 404 Not Found
    get_after_delete = client.get(f"/farms/{farm1_id}", headers=headers1)
    assert get_after_delete.status_code == 404


def test_farm_not_found_errors(client):
    """Test 404 responses for non-existent farm IDs."""
    client.post("/auth/register", json={
        "name": "Edge Farmer",
        "phone": "9876543230",
        "password": "password123",
    })
    login = client.post("/auth/login", json={
        "identifier": "9876543230",
        "password": "password123",
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert client.get("/farms/9999", headers=headers).status_code == 404
    assert client.put("/farms/9999", json={"farm_name": "Test"}, headers=headers).status_code == 404
    assert client.delete("/farms/9999", headers=headers).status_code == 404


def test_farm_input_validation(client):
    """Test farm field validation constraints."""
    client.post("/auth/register", json={
        "name": "Validating Farmer",
        "phone": "9876543231",
        "password": "password123",
    })
    login = client.post("/auth/login", json={
        "identifier": "9876543231",
        "password": "password123",
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Zero or negative area_acres rejected
    res_area = client.post("/farms", json={"farm_name": "Zero Farm", "area_acres": 0}, headers=headers)
    assert res_area.status_code == 422

    res_neg_area = client.post("/farms", json={"farm_name": "Neg Farm", "area_acres": -2.5}, headers=headers)
    assert res_neg_area.status_code == 422

    # Invalid soil type rejected
    res_soil = client.post(
        "/farms",
        json={"farm_name": "Bad Soil", "area_acres": 2.0, "soil_type": "MartianSoil"},
        headers=headers,
    )
    assert res_soil.status_code == 422

    # Invalid irrigation type rejected
    res_irr = client.post(
        "/farms",
        json={"farm_name": "Bad Irr", "area_acres": 2.0, "irrigation": "MagicWand"},
        headers=headers,
    )
    assert res_irr.status_code == 422


def test_corrupt_jwt_token(client):
    """Test authentication rejection with malformed or tampered JWT token."""
    res = client.get("/me", headers={"Authorization": "Bearer this.is.invalid"})
    assert res.status_code == 401
    assert "Invalid or expired session token" in res.json()["detail"]

