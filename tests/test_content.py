import pytest


async def _register_and_login(client, email: str = "owner@example.com") -> str:
    creds = {"email": email, "password": "supersecret123"}
    await client.post("/auth/register", json=creds)
    login = await client.post("/auth/login", json=creds)
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_content_crud(client):
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/content",
        json={"title": "Hello", "body": "World"},
        headers=headers,
    )
    assert create.status_code == 201
    content_id = create.json()["id"]

    fetched = await client.get(f"/content/{content_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Hello"

    updated = await client.patch(
        f"/content/{content_id}",
        json={"title": "Hello there"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Hello there"

    listing = await client.get("/content", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    deleted = await client.delete(f"/content/{content_id}", headers=headers)
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_content_isolated_between_users(client):
    alice_token = await _register_and_login(client, email="alice@example.com")
    bob_token = await _register_and_login(client, email="bob@example.com")

    create = await client.post(
        "/content",
        json={"title": "Alice's note", "body": ""},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    content_id = create.json()["id"]

    # Bob must not see Alice's content — 404, not 403, to avoid leaking existence.
    resp = await client.get(
        f"/content/{content_id}",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert resp.status_code == 404
