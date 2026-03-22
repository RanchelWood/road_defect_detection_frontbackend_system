from uuid import uuid4


def _register(client, email: str, password: str = "Password1"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )


def _login(client, email: str, password: str = "Password1"):
    return client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )


def test_register_and_login_success(client):
    email = f"user-{uuid4()}@example.com"

    register_response = _register(client, email)
    assert register_response.status_code == 201
    register_payload = register_response.json()
    assert register_payload["success"] is True
    assert "access_token" in register_payload["data"]
    assert "refresh_token" in register_payload["data"]

    login_response = _login(client, email)
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["success"] is True
    assert login_payload["data"]["user"]["email"] == email


def test_register_duplicate_email_returns_conflict(client):
    email = f"dup-{uuid4()}@example.com"

    first_response = _register(client, email)
    assert first_response.status_code == 201

    second_response = _register(client, email)
    assert second_response.status_code == 409
    payload = second_response.json()
    assert payload["error"]["code"] == "AUTH_EMAIL_EXISTS"


def test_login_invalid_credentials(client):
    email = f"invalid-{uuid4()}@example.com"
    _register(client, email)

    response = _login(client, email, password="WrongPass1")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


def test_refresh_and_logout_flow(client):
    email = f"refresh-{uuid4()}@example.com"
    register_response = _register(client, email)

    refresh_token = register_response.json()["data"]["refresh_token"]

    refresh_response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 200
    assert refresh_response.json()["success"] is True

    logout_response = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 200
    assert logout_response.json()["data"]["message"] == "Logged out."

    post_logout_refresh = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert post_logout_refresh.status_code == 401
    assert post_logout_refresh.json()["error"]["code"] == "AUTH_TOKEN_INVALID"