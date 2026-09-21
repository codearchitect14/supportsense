def test_signup_creates_viewer_by_default(client):
    response = client.post(
        "/auth/signup", json={"email": "new@example.com", "password": "verifypassword123", "full_name": "New User"}
    )
    assert response.status_code == 201
    assert response.json()["role"] == "viewer"


def test_signup_rejects_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "verifypassword123", "full_name": "Dup User"}
    client.post("/auth/signup", json=payload)
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 409


def test_signup_rejects_weak_password(client):
    response = client.post("/auth/signup", json={"email": "weak@example.com", "password": "123", "full_name": "Weak"})
    assert response.status_code == 422


def test_signup_rejects_unexpected_fields(client):
    response = client.post(
        "/auth/signup",
        json={
            "email": "extra@example.com",
            "password": "verifypassword123",
            "full_name": "Extra",
            "role": "admin",
        },
    )
    assert response.status_code == 422


def test_login_rejects_wrong_password(client, make_user):
    make_user("loginuser@example.com", password="correctpassword123")
    response = client.post("/auth/login", data={"username": "loginuser@example.com", "password": "wrongpassword"})
    assert response.status_code == 401


def test_login_sets_httponly_refresh_cookie(client, make_user):
    make_user("cookieuser@example.com", password="correctpassword123")
    response = client.post("/auth/login", data={"username": "cookieuser@example.com", "password": "correctpassword123"})
    assert response.status_code == 200
    assert "refresh_token" in response.cookies


def test_refresh_rotates_and_revokes_old_token(client, make_user):
    make_user("refreshuser@example.com", password="correctpassword123")
    login = client.post("/auth/login", data={"username": "refreshuser@example.com", "password": "correctpassword123"})
    old_refresh_token = login.cookies["refresh_token"]

    refreshed = client.post("/auth/refresh", cookies={"refresh_token": old_refresh_token})
    assert refreshed.status_code == 200

    reused = client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
    assert reused.status_code == 401


def test_me_requires_a_valid_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_change_password_then_login_with_new_password(client, auth_headers):
    headers = auth_headers("pwuser@example.com")
    response = client.post(
        "/auth/change-password",
        json={"current_password": "verifypassword123", "new_password": "newpassword456"},
        headers=headers,
    )
    assert response.status_code == 200

    old_login = client.post("/auth/login", data={"username": "pwuser@example.com", "password": "verifypassword123"})
    assert old_login.status_code == 401

    new_login = client.post("/auth/login", data={"username": "pwuser@example.com", "password": "newpassword456"})
    assert new_login.status_code == 200


def test_change_password_rejects_wrong_current_password(client, auth_headers):
    headers = auth_headers("pwuser2@example.com")
    response = client.post(
        "/auth/change-password",
        json={"current_password": "wrongpassword", "new_password": "irrelevant123"},
        headers=headers,
    )
    assert response.status_code == 401


def test_admin_can_list_users_non_admin_cannot(client, auth_headers):
    admin_headers = auth_headers("admin1@example.com", role="admin")
    auth_headers("viewer1@example.com", role="viewer")

    admin_resp = client.get("/users", headers=admin_headers)
    assert admin_resp.status_code == 200
    assert len(admin_resp.json()) >= 2

    viewer_headers = auth_headers("viewer2@example.com", role="viewer")
    assert client.get("/users", headers=viewer_headers).status_code == 403


def test_admin_cannot_change_own_role(client, auth_headers, db_session):
    from app.models.user import User

    admin_headers = auth_headers("selfadmin@example.com", role="admin")
    admin_id = db_session.query(User).filter(User.email == "selfadmin@example.com").first().id

    response = client.patch(f"/users/{admin_id}/role", json={"role": "viewer"}, headers=admin_headers)
    assert response.status_code == 400


def test_admin_can_change_another_users_role(client, auth_headers, db_session):
    from app.models.user import User

    admin_headers = auth_headers("admin2@example.com", role="admin")
    auth_headers("targetuser@example.com", role="viewer")
    target_id = db_session.query(User).filter(User.email == "targetuser@example.com").first().id

    response = client.patch(f"/users/{target_id}/role", json={"role": "agent"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "agent"
