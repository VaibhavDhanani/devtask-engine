import pytest


@pytest.mark.asyncio
async def test_register_login_and_use_access_token(client):
    creds = {"email": "alice@example.com", "password": "supersecret123"}

    register = await client.post("/auth/register", json={**creds, "full_name": "Alice"})
    assert register.status_code == 201, register.text
    user_id = register.json()["id"]

    login = await client.post("/auth/login", json=creds)
    assert login.status_code == 200, login.text
    tokens = login.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    me = await client.get(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == creds["email"]


@pytest.mark.asyncio
async def test_login_with_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": "supersecret123"},
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_duplicate_email_rejected(client):
    payload = {"email": "carol@example.com", "password": "supersecret123"}
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["code"] == "conflict"
