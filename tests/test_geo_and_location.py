"""Automated tests for Geolocation Proxies, Soft Validation, Location Persistence, and Profile Address Updates."""

from unittest.mock import MagicMock, patch
import pytest

from app import db
from app.routers.geo import clear_geo_cache


@pytest.fixture(autouse=True)
def reset_cache():
    """Ensure in-memory geocoding caches are reset before every test."""
    clear_geo_cache()
    yield
    clear_geo_cache()


def mock_nominatim_client(mock_resp):
    """Context manager to mock Nominatim httpx.Client in app.routers.geo without affecting TestClient."""
    mock_instance = MagicMock()
    mock_instance.get.return_value = mock_resp
    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_instance
    mock_ctx.__exit__.return_value = None
    p = patch("app.routers.geo.httpx.Client", return_value=mock_ctx)
    return p, mock_instance


# -----------------------------------------------------------------------------
# 1. Nominatim Search Proxy Tests
# -----------------------------------------------------------------------------

def test_geo_search_success_with_mocked_http(client):
    """Test GET /geo/search proxies to Nominatim, formats labels, and filters India."""
    mock_nominatim_results = [
        {
            "place_id": 1001,
            "lat": "18.5204",
            "lon": "73.8567",
            "display_name": "Pune, Pune District, Maharashtra, 411001, India",
            "name": "Pune",
            "address": {
                "city": "Pune",
                "state_district": "Pune",
                "state": "Maharashtra",
                "country": "India",
                "country_code": "in",
            },
        },
        {
            "place_id": 1002,
            "lat": "18.1511",
            "lon": "74.5772",
            "display_name": "Baramati, Pune District, Maharashtra, 413102, India",
            "name": "Baramati",
            "address": {
                "town": "Baramati",
                "district": "Pune",
                "state": "Maharashtra",
                "country": "India",
                "country_code": "in",
            },
        },
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_nominatim_results

    patcher, mock_http = mock_nominatim_client(mock_resp)
    with patcher:
        resp = client.get("/geo/search?q=pune")
        assert resp.status_code == 200
        data = resp.json()

        assert len(data) == 2
        assert data[0]["label"] == "Pune, Maharashtra"
        assert data[0]["lat"] == 18.5204
        assert data[0]["lon"] == 73.8567
        assert data[0]["address"]["city"] == "Pune"

        assert data[1]["label"] == "Baramati, Pune, Maharashtra"
        assert data[1]["lat"] == 18.1511
        assert data[1]["lon"] == 74.5772

        # Verify Nominatim call parameters: User-Agent, countrycodes=in, limit=5
        mock_http.get.assert_called_once()
        args, kwargs = mock_http.get.call_args
        assert kwargs["params"]["q"] == "pune"
        assert kwargs["params"]["countrycodes"] == "in"
        assert kwargs["params"]["limit"] == 5
        assert "AgriPredict" in kwargs["headers"]["User-Agent"]


def test_geo_search_caching(client):
    """Test that repeated search queries return cached results without additional HTTP requests."""
    mock_results = [
        {
            "lat": "19.0760",
            "lon": "72.8777",
            "display_name": "Mumbai, Maharashtra, India",
            "address": {"city": "Mumbai", "state": "Maharashtra"},
        }
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_results

    patcher, mock_http = mock_nominatim_client(mock_resp)
    with patcher:
        # First call hits mock
        resp1 = client.get("/geo/search?q=mumbai")
        assert resp1.status_code == 200
        assert mock_http.get.call_count == 1

        # Second call should be served directly from in-memory cache
        resp2 = client.get("/geo/search?q=mumbai")
        assert resp2.status_code == 200
        assert resp2.json() == resp1.json()
        assert mock_http.get.call_count == 1  # No additional HTTP call


def test_geo_search_upstream_error_handled_gracefully(client):
    """Test that upstream Nominatim timeouts or errors return an empty list gracefully."""
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.json.return_value = {"error": "Service unavailable"}

    patcher, mock_http = mock_nominatim_client(mock_resp)
    with patcher:
        resp = client.get("/geo/search?q=aurangabad")
        assert resp.status_code == 200
        assert resp.json() == []


# -----------------------------------------------------------------------------
# 2. Nominatim Reverse Geocoding Proxy Tests
# -----------------------------------------------------------------------------

def test_geo_reverse_success_and_label_formatting(client):
    """Test GET /geo/reverse reverse-geocodes lat/lon to a formatted label."""
    mock_reverse_result = {
        "place_id": 2001,
        "lat": "18.5204",
        "lon": "73.8567",
        "display_name": "Shivajinagar, Pune, Maharashtra, 411005, India",
        "address": {
            "suburb": "Shivajinagar",
            "city": "Pune",
            "state_district": "Pune",
            "state": "Maharashtra",
            "country": "India",
        },
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_reverse_result

    patcher, mock_http = mock_nominatim_client(mock_resp)
    with patcher:
        resp = client.get("/geo/reverse?lat=18.5204&lon=73.8567")
        assert resp.status_code == 200
        data = resp.json()

        assert "Shivajinagar" in data["label"]
        assert "Maharashtra" in data["label"]
        assert data["lat"] == 18.5204
        assert data["lon"] == 73.8567
        assert data["warning"] is None  # Inside India bounds


def test_geo_reverse_caching(client):
    """Test that repeated reverse geocode queries are served from cache."""
    mock_reverse_result = {
        "lat": "18.5204",
        "lon": "73.8567",
        "display_name": "Pune, Maharashtra, India",
        "address": {"city": "Pune", "state": "Maharashtra"},
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_reverse_result

    patcher, mock_http = mock_nominatim_client(mock_resp)
    with patcher:
        resp1 = client.get("/geo/reverse?lat=18.5204&lon=73.8567")
        assert resp1.status_code == 200
        assert mock_http.get.call_count == 1

        resp2 = client.get("/geo/reverse?lat=18.5204&lon=73.8567")
        assert resp2.status_code == 200
        assert resp2.json()["label"] == resp1.json()["label"]
        assert mock_http.get.call_count == 1


# -----------------------------------------------------------------------------
# 3. Validation & Soft Warning for Coordinates Outside India
# -----------------------------------------------------------------------------

def test_geo_reverse_soft_warning_outside_india(client):
    """Test coordinates outside India (expected lat 6-38, lon 68-98) receive a soft warning."""
    # Coordinates in London (lat 51.5074, lon -0.1278)
    mock_result = {
        "lat": "51.5074",
        "lon": "-0.1278",
        "display_name": "London, Greater London, England, United Kingdom",
        "address": {"city": "London", "country": "United Kingdom"},
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_result

    patcher, mock_http = mock_nominatim_client(mock_resp)
    with patcher:
        resp = client.get("/geo/reverse?lat=51.5074&lon=-0.1278")
        assert resp.status_code == 200
        data = resp.json()
        assert data["warning"] is not None
        assert "outside India" in data["warning"]
        assert "expected lat 6-38, lon 68-98" in data["warning"]


def test_geo_reverse_invalid_bounds_rejected(client):
    """Test coordinates outside global range (-90..90, -180..180) are rejected with 422."""
    res_lat = client.get("/geo/reverse?lat=100.0&lon=73.8567")
    assert res_lat.status_code == 422

    res_lon = client.get("/geo/reverse?lat=18.5204&lon=200.0")
    assert res_lon.status_code == 422


# -----------------------------------------------------------------------------
# 4. Farm Location Label Persistence Tests
# -----------------------------------------------------------------------------

def test_farm_create_and_update_with_location_label(client):
    """Test that location_label is persisted and retrieved across farm CRUD operations."""
    # Register and login farmer
    client.post("/auth/register", json={
        "name": "Geoloc Farmer",
        "phone": "9876500001",
        "password": "password123",
    })
    login_res = client.post("/auth/login", json={
        "identifier": "9876500001",
        "password": "password123",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create farm with location_label
    create_payload = {
        "farm_name": "Sahyadri Agro Plot",
        "area_acres": 5.0,
        "location_label": "Khadakwasla, Pune, Maharashtra",
        "latitude": 18.4418,
        "longitude": 73.7619,
        "soil_type": "Black",
        "irrigation": "Canal",
    }
    create_res = client.post("/farms", json=create_payload, headers=headers)
    assert create_res.status_code == 201, create_res.text
    farm_data = create_res.json()
    farm_id = farm_data["farm_id"]
    assert farm_data["location_label"] == "Khadakwasla, Pune, Maharashtra"
    assert farm_data["latitude"] == 18.4418
    assert farm_data["longitude"] == 73.7619

    # 2. Get farm by ID
    get_res = client.get(f"/farms/{farm_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["location_label"] == "Khadakwasla, Pune, Maharashtra"

    # 3. List farms includes location_label
    list_res = client.get("/farms", headers=headers)
    assert list_res.status_code == 200
    farms_list = list_res.json()
    matching = [f for f in farms_list if f["farm_id"] == farm_id]
    assert len(matching) == 1
    assert matching[0]["location_label"] == "Khadakwasla, Pune, Maharashtra"

    # 4. Update farm location_label
    update_payload = {
        "farm_name": "Sahyadri Agro Plot",
        "area_acres": 5.0,
        "location_label": "Donje, Haveli, Maharashtra",
        "latitude": 18.3980,
        "longitude": 73.7550,
        "soil_type": "Black",
        "irrigation": "Well",
    }
    update_res = client.put(f"/farms/{farm_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["location_label"] == "Donje, Haveli, Maharashtra"
    assert update_res.json()["latitude"] == 18.3980


def test_farm_without_location_label_defaults_to_none(client):
    """Test creating a farm without location_label keeps it None for backward compatibility."""
    client.post("/auth/register", json={
        "name": "Old School Farmer",
        "phone": "9876500002",
        "password": "password123",
    })
    login_res = client.post("/auth/login", json={
        "identifier": "9876500002",
        "password": "password123",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_payload = {
        "farm_name": "Legacy Plot",
        "area_acres": 3.2,
        "latitude": 19.1234,
        "longitude": 74.5678,
        "soil_type": "Red",
        "irrigation": "Rainfed",
    }
    res = client.post("/farms", json=create_payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["location_label"] is None


# -----------------------------------------------------------------------------
# 5. Farmer Profile Address Update Tests (PATCH /me/address)
# -----------------------------------------------------------------------------

def test_update_farmer_address_from_location(client):
    """Test PATCH /me/address updates the farmer's district and village."""
    client.post("/auth/register", json={
        "name": "Nitin Gadve",
        "phone": "9876500003",
        "password": "password123",
        # district and village omitted/empty
    })
    login_res = client.post("/auth/login", json={
        "identifier": "9876500003",
        "password": "password123",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Initial profile check
    me_initial = client.get("/me", headers=headers).json()
    assert me_initial["district"] is None
    assert me_initial["village"] is None

    # Update address
    update_res = client.patch(
        "/me/address",
        json={"district": "Solapur", "village": "Pandharpur"},
        headers=headers,
    )
    assert update_res.status_code == 200
    updated_profile = update_res.json()
    assert updated_profile["district"] == "Solapur"
    assert updated_profile["village"] == "Pandharpur"

    # Verify persisted in database
    me_after = client.get("/me", headers=headers).json()
    assert me_after["district"] == "Solapur"
    assert me_after["village"] == "Pandharpur"
