from tests.conftest import create_test_user, get_auth_headers


def test_register_success(client):
    response = client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "new@test.com",
        "password": "secret123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "viewer"


def test_register_duplicate_username(client, editor_user):
    response = client.post("/api/auth/register", json={
        "username": "editor",
        "email": "other@test.com",
        "password": "secret123",
    })
    assert response.status_code == 409


def test_login_success(client, editor_user):
    response = client.post("/api/auth/login", json={
        "username": "editor",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, editor_user):
    response = client.post("/api/auth/login", json={
        "username": "editor",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_me_authenticated(client, editor_user, editor_headers):
    response = client.get("/api/auth/me", headers=editor_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "editor"


def test_me_no_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
