def test_security_headers_present_on_every_response(client):
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_signup_request_with_unknown_field_is_rejected(client):
    response = client.post(
        "/auth/signup",
        json={"email": "strict@example.com", "password": "verifypassword123", "full_name": "Strict", "is_admin": True},
    )
    assert response.status_code == 422


def test_error_responses_use_the_consistent_shape(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]


def test_login_is_rate_limited():
    # The shared `client` fixture disables rate limiting for the rest of the
    # suite (it logs in many test users rapidly), and that's global state on
    # the same `app` object, not scoped to a fixture instance. Force it on
    # for this test regardless of what ran before, and restore it after,
    # so this test's result never depends on test execution order.
    from fastapi.testclient import TestClient

    from app.main import app

    app.state.limiter.enabled = True
    try:
        with TestClient(app) as isolated_client:
            responses = [
                isolated_client.post("/auth/login", data={"username": "nobody@example.com", "password": "wrong"})
                for _ in range(7)
            ]
    finally:
        app.state.limiter.enabled = False

    statuses = [r.status_code for r in responses]
    assert statuses.count(429) > 0
    assert statuses[:5] == [401, 401, 401, 401, 401]
