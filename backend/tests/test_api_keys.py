import pytest
from datetime import datetime, timezone, timedelta


def test_list_api_keys_unauthorized(client):
    response = client.get("/api-keys")
    assert response.status_code == 401


def test_list_api_keys_authorized(client, test_api_key):
    response = client.get("/api-keys", headers={"X-API-Key": test_api_key["plain"]})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_api_key_unauthorized(client):
    response = client.post("/api-keys", json={"name": "test"})
    assert response.status_code == 401


def test_create_api_key_authorized(client, test_api_key):
    response = client.post(
        "/api-keys",
        json={"name": "new-key"},
        headers={"X-API-Key": test_api_key["plain"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert "key" in data
    assert data["name"] == "new-key"
    assert data["is_active"] is True
    assert len(data["key"]) > 0


def test_create_api_key_with_expiration(client, test_api_key):
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    response = client.post(
        "/api-keys",
        json={"name": "expiring-key", "expires_at": expires_at},
        headers={"X-API-Key": test_api_key["plain"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["expires_at"] is not None


def test_update_api_key(client, test_api_key, db):
    from app.models import ApiKey

    key_id = test_api_key["id"]
    response = client.patch(
        f"/api-keys/{key_id}",
        json={"name": "updated-key", "is_active": False},
        headers={"X-API-Key": test_api_key["plain"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated-key"
    assert data["is_active"] is False


def test_delete_api_key(client, test_api_key):
    key_id = test_api_key["id"]
    response = client.delete(
        f"/api-keys/{key_id}",
        headers={"X-API-Key": test_api_key["plain"]}
    )
    assert response.status_code == 204


def test_delete_nonexistent_key(client, test_api_key):
    response = client.delete(
        "/api-keys/99999",
        headers={"X-API-Key": test_api_key["plain"]}
    )
    assert response.status_code == 404


def test_update_nonexistent_key(client, test_api_key):
    response = client.patch(
        "/api-keys/99999",
        json={"name": "updated"},
        headers={"X-API-Key": test_api_key["plain"]}
    )
    assert response.status_code == 404
