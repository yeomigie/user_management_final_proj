import pytest
from httpx import AsyncClient
from faker import Faker
from app.main import app
from app.models.user_model import UserRole
from app.utils.nickname_gen import generate_nickname
from app.utils.security import hash_password
from app.services.jwt_service import decode_token
from urllib.parse import urlencode

fake = Faker()

# -------------------------
# User-API tests
# -------------------------

@pytest.mark.asyncio
async def test_create_user_access_denied(async_client: AsyncClient, user_token, email_service):
    headers = {"Authorization": f"Bearer {user_token}"}
    user_data = {
        "nickname": generate_nickname(),
        "email": "test@example.com",
        "password": "sS#fdasrongPassword123!",
    }
    response = await async_client.post("/users/", json=user_data, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_retrieve_user_access_denied(async_client: AsyncClient, verified_user, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.get(f"/users/{verified_user.id}", headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_retrieve_user_access_allowed(async_client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get(f"/users/{admin_user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(admin_user.id)

@pytest.mark.asyncio
async def test_update_user_email_access_denied(async_client: AsyncClient, verified_user, user_token):
    updated_data = {"email": f"updated_{verified_user.id}@example.com"}
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.put(f"/users/{verified_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_user_email_access_allowed(async_client: AsyncClient, admin_user, admin_token):
    updated_data = {"email": f"updated_{admin_user.id}@example.com"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == updated_data["email"]

@pytest.mark.asyncio
async def test_update_nonexistent_user(async_client: AsyncClient, admin_token):
    non_existent_user_id = "00000000-0000-0000-0000-000000000000"
    updated_data = {"first_name": "NonExistent"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(f"/users/{non_existent_user_id}", json=updated_data, headers=headers)
    assert response.status_code == 404
    assert "User not found" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_create_user_invalid_role(async_client: AsyncClient, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_data = {
        "nickname": "InvalidRoleUser",
        "email": "invalidrole@example.com",
        "password": "StrongPassword123!",
        "role": "INVALID_ROLE"
    }
    response = await async_client.post("/users/", json=user_data, headers=headers)
    assert response.status_code == 422
    error_details = response.json().get("detail", [])
    assert any(
        "Input should be 'ANONYMOUS', 'AUTHENTICATED', 'MANAGER' or 'ADMIN'" in err.get("msg", "")
        for err in error_details
    )

@pytest.mark.asyncio
async def test_promote_user_denied(async_client: AsyncClient, admin_user, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.patch(f"/users/{admin_user.id}/promote", headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_promote_user_success(async_client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.patch(f"/users/{admin_user.id}/promote", headers=headers)
    assert response.status_code == 200
    assert response.json().get("is_professional") is True

@pytest.mark.asyncio
async def test_update_self_profile_not_allowed(async_client: AsyncClient):
    updated_data = {"first_name": "Test", "last_name": "User"}
    response = await async_client.put("/users/update-profile", json=updated_data)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_update_user_success(async_client: AsyncClient, verified_user, auth_token):
    updated_data = {"first_name": "Test", "last_name": "User"}
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await async_client.put("/users/update-profile", json=updated_data, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_user(async_client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    delete_resp = await async_client.delete(f"/users/{admin_user.id}", headers=headers)
    assert delete_resp.status_code == 204
    # Verify deletion
    fetch_resp = await async_client.get(f"/users/{admin_user.id}", headers=headers)
    assert fetch_resp.status_code == 404

@pytest.mark.asyncio
async def test_create_user_duplicate_email(async_client: AsyncClient, verified_user):
    user_data = {
        "email": verified_user.email,
        "password": "AnotherPassword123!",
        "role": UserRole.ADMIN.name
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 400
    assert "Email already exists" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_list_users_as_admin(async_client: AsyncClient, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "items" in body and isinstance(body["items"], list)

@pytest.mark.asyncio
async def test_list_users_as_manager(async_client: AsyncClient, manager_token):
    headers = {"Authorization": f"Bearer {manager_token}"}
    response = await async_client.get("/users/", headers=headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_list_users_unauthorized(async_client: AsyncClient, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.get("/users/", headers=headers)
    assert response.status_code == 403

# -------------------------
# Login & Registration tests
# -------------------------

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, verified_user):
    form_data = {
        "username": verified_user.email,
        "password": "MySuperPassword$1234"
    }
    response = await async_client.post(
        "/login/",
        data=urlencode(form_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    decoded = decode_token(data["access_token"])
    assert decoded["role"] == UserRole.AUTHENTICATED.name

@pytest.mark.asyncio
async def test_login_user_not_found(async_client: AsyncClient):
    form_data = {
        "username": "nonexistent@here.edu",
        "password": "DoesNotMatter123!"
    }
    response = await async_client.post(
        "/login/",
        data=urlencode(form_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_login_incorrect_password(async_client: AsyncClient, verified_user):
    form_data = {
        "username": verified_user.email,
        "password": "WrongPassword!"
    }
    response = await async_client.post(
        "/login/",
        data=urlencode(form_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_login_weak_password(async_client: AsyncClient):
    user_data = {
        "email": fake.email(),
        "password": "abc234",
        "role": "AUTHENTICATED"
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 422
    msgs = [err.get("msg", "") for err in response.json().get("detail", [])]
    assert any("at least 8 characters" in m for m in msgs), msgs

@pytest.mark.asyncio
async def test_login_unverified_user(async_client: AsyncClient, unverified_user):
    form_data = {
        "username": unverified_user.email,
        "password": "MySuperPassword$1234"
    }
    response = await async_client.post(
        "/login/",
        data=urlencode(form_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_locked_user(async_client: AsyncClient, locked_user):
    form_data = {
        "username": locked_user.email,
        "password": "MySuperPassword$1234"
    }
    response = await async_client.post(
        "/login/",
        data=urlencode(form_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 400
    assert "Account locked due to too many failed login attempts." in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_delete_user_does_not_exist(async_client: AsyncClient, admin_token):
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.delete(f"/users/{non_existent_id}", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_user_github(async_client: AsyncClient, admin_user, admin_token):
    updated_data = {"github_profile_url": "http://github.com/kaw393939"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["github_profile_url"] == updated_data["github_profile_url"]

@pytest.mark.asyncio
async def test_update_user_linkedin(async_client: AsyncClient, admin_user, admin_token):
    updated_data = {"linkedin_profile_url": "http://linkedin.com/kaw393939"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["linkedin_profile_url"] == updated_data["linkedin_profile_url"]