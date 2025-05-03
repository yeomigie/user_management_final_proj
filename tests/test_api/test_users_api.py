from builtins import str
 import pytest
 from httpx import AsyncClient
 from app.main import app
 from app.models.user_model import User, UserRole
 from app.utils.nickname_gen import generate_nickname
 from app.utils.security import hash_password
 from app.services.jwt_service import decode_token  # Import your FastAPI app
 
 # Example of a test function using the async_client fixture
 @pytest.mark.asyncio
 async def test_create_user_access_denied(async_client, user_token, email_service):
     headers = {"Authorization": f"Bearer {user_token}"}
     # Define user data for the test
     user_data = {
         "nickname": generate_nickname(),
         "email": "test@example.com",
         "password": "sS#fdasrongPassword123!",
     }
     # Send a POST request to create a user
     response = await async_client.post("/users/", json=user_data, headers=headers)
     # Asserts
     assert response.status_code == 403
 
 # You can similarly refactor other test functions to use the async_client fixture
 @pytest.mark.asyncio
 async def test_retrieve_user_access_denied(async_client, verified_user, user_token):
     headers = {"Authorization": f"Bearer {user_token}"}
     response = await async_client.get(f"/users/{verified_user.id}", headers=headers)
     assert response.status_code == 403
 
 @pytest.mark.asyncio
 async def test_retrieve_user_access_allowed(async_client, admin_user, admin_token):
     headers = {"Authorization": f"Bearer {admin_token}"}
     response = await async_client.get(f"/users/{admin_user.id}", headers=headers)
     assert response.status_code == 200
     assert response.json()["id"] == str(admin_user.id)
 
 @pytest.mark.asyncio
 async def test_update_user_email_access_denied(async_client, verified_user, user_token):
     updated_data = {"email": f"updated_{verified_user.id}@example.com"}
     headers = {"Authorization": f"Bearer {user_token}"}
     response = await async_client.put(f"/users/{verified_user.id}", json=updated_data, headers=headers)
     assert response.status_code == 403
 
 @pytest.mark.asyncio
 async def test_update_user_email_access_allowed(async_client, admin_user, admin_token):
     updated_data = {"email": f"updated_{admin_user.id}@example.com"}
     headers = {"Authorization": f"Bearer {admin_token}"}
     response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
     assert response.status_code == 200
     assert response.json()["email"] == updated_data["email"]
 
 @pytest.mark.asyncio
 async def test_update_nonexistent_user(async_client, admin_token):
     non_existent_user_id = "00000000-0000-0000-0000-000000000000"
     updated_data = {"first_name": "NonExistent"}
     headers = {"Authorization": f"Bearer {admin_token}"}
     response = await async_client.put(f"/users/{non_existent_user_id}", json=updated_data, headers=headers)
     assert response.status_code == 404
     assert "User not found" in response.json().get("detail", "")
 
 @pytest.mark.asyncio
 async def test_create_user_invalid_role(async_client, admin_token):
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
 
     found = any(
         "Input should be 'ANONYMOUS', 'AUTHENTICATED', 'MANAGER' or 'ADMIN'" in error.get("msg", "")
         for error in error_details
     )
     assert found, "Expected role validation error message not found in response"
 
 @pytest.mark.asyncio
 async def test_promote_user(async_client, admin_user, admin_token):
     headers = {"Authorization": f"Bearer {admin_token}"}
     response = await async_client.patch(f"/users/{admin_user.id}/promote", headers=headers)
     
     print(response.status_code)  # Log status code
     print(response.json())  # Log the response content
     
     assert response.status_code == 200  # Ensure the correct status
     assert response.json()["is_professional"] is True
 
 
 @pytest.mark.asyncio
 async def test_promote_user_denied(async_client, admin_user, user_token):
     headers = {"Authorization": f"Bearer {user_token}"}
     response = await async_client.patch(f"/users/{admin_user.id}/promote", headers=headers)
     assert response.status_code == 403
 
 @pytest.mark.asyncio
 async def test_update_self_profile_not_allowed(async_client, admin_user, admin_token):
     updated_data = {"first_name": "Test", "last_name": "User"}
     response = await async_client.put("/users/update-profile", json=updated_data)
     assert response.status_code == 401
 
 @pytest.mark.asyncio
 async def test_update_user_success(async_client, verified_user, auth_token):
     updated_data = {"first_name": "Test", "last_name": "User"}
     headers = {"Authorization": f"Bearer {auth_token}"}
     response = await async_client.put("/users/update-profile", json=updated_data, headers=headers)
     assert response.status_code == 403
 
 @pytest.mark.asyncio
 async def test_delete_user(async_client, admin_user, admin_token):
     headers = {"Authorization": f"Bearer {admin_token}"}
     delete_response = await async_client.delete(f"/users/{admin_user.id}", headers=headers)
     assert delete_response.status_code == 204
     # Verify the user is deleted
     fetch_response = await async_client.get(f"/users/{admin_user.id}", headers=headers)
     assert fetch_response.status_code == 404
 
 @pytest.mark.asyncio
 async def test_create_user_duplicate_email(async_client, verified_user):
     user_data = {
         "email": verified_user.email,
         "password": "AnotherPassword123!",
         "role": UserRole.ADMIN.name
     }
     response = await async_client.post("/register/", json=user_data)
     assert response.status_code == 400
     assert "Email already exists" in response.json().get("detail", "")
 
 @pytest.mark.asyncio
 async def test_create_user_invalid_email(async_client):
     user_data = {
         "email": "notanemail",
         "password": "ValidPassword123!",
     }
     response = await async_client.post("/register/", json=user_data)
     assert response.status_code == 422
 
 import pytest
 from app.services.jwt_service import decode_token
 from urllib.parse import urlencode
 
 @pytest.mark.asyncio
 async def test_login_success(async_client, verified_user):
     # Attempt to login with the test user
     form_data = {
         "username": verified_user.email,
         "password": "MySuperPassword$1234"
     }
     response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
 
     # Check for successful login response
     assert response.status_code == 200
     data = response.json()
     assert "access_token" in data
     assert data["token_type"] == "bearer"
 
     # Use the decode_token method from jwt_service to decode the JWT
     decoded_token = decode_token(data["access_token"])
     assert decoded_token is not None, "Failed to decode token"
     assert decoded_token["role"] == "AUTHENTICATED", "The user role should be AUTHENTICATED"
 
 @pytest.mark.asyncio
 async def test_login_user_not_found(async_client):
     form_data = {
         "username": "nonexistentuser@here.edu",
         "password": "DoesNotMatter123!"
     }
     response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
     assert response.status_code == 401
     assert "Incorrect email or password." in response.json().get("detail", "")
 
 @pytest.mark.asyncio
 async def test_login_incorrect_password(async_client, verified_user):
     form_data = {
         "username": verified_user.email,
         "password": "IncorrectPassword123!"
     }
     response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
     assert response.status_code == 401
     assert "Incorrect email or password." in response.json().get("detail", "")
 
 @pytest.mark.asyncio
 async def test_login_weak_password(async_client, verified_user):
     user_data = {
         "email": verified_user.email,
         "password": "abc234",
         "role": verified_user.role.name  
     }
     response = await async_client.post("/register/", json=user_data)
     assert response.status_code == 422
 
     details = response.json().get("detail", [])
 
     found = any("String should have at least 8 characters" in error.get("msg", "") for error in details)
     assert found, "Expected password length error message not found in response details"
 
 
 @pytest.mark.asyncio
 async def test_login_unverified_user(async_client, unverified_user):
     form_data = {
         "username": unverified_user.email,
         "password": "MySuperPassword$1234"
     }
     response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
     assert response.status_code == 401
 
 @pytest.mark.asyncio
 async def test_login_locked_user(async_client, locked_user):
     form_data = {
         "username": locked_user.email,
         "password": "MySuperPassword$1234"
     }
     response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
     assert response.status_code == 400
     assert "Account locked due to too many failed login attempts." in response.json().get("detail", "")
 @pytest.mark.asyncio
 async def test_delete_user_does_not_exist(async_client, admin_token):
     non_existent_user_id = "00000000-0000-0000-0000-000000000000"  # Valid UUID format
     headers = {"Authorization": f"Bearer {admin_token}"}
     delete_response = await async_client.delete(f"/users/{non_existent_user_id}", headers=headers)
     assert delete_response.status_code == 404
 
 @pytest.mark.asyncio
 async def test_update_user_github(async_client, admin_user, admin_token):
     updated_data = {"github_profile_url": "http://www.github.com/kaw393939"}
     headers = {"Authorization": f"Bearer {admin_token}"}
     response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
     assert response.status_code == 200
     assert response.json()["github_profile_url"] == updated_data["github_profile_url"]
 
 @pytest.mark.asyncio
 async def test_update_user_linkedin(async_client, admin_user, admin_token):
     updated_data = {"linkedin_profile_url": "http://www.linkedin.com/kaw393939"}
     headers = {"Authorization": f"Bearer {admin_token}"}
     response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
     assert response.status_code == 200
     assert response.json()["linkedin_profile_url"] == updated_data["linkedin_profile_url"]
 
 @pytest.mark.asyncio
 async def test_list_users_as_admin(async_client, admin_token):
     response = await async_client.get(
         "/users/",
         headers={"Authorization": f"Bearer {admin_token}"}
     )
     assert response.status_code == 200
     assert 'items' in response.json()
 
 @pytest.mark.asyncio
 async def test_list_users_as_manager(async_client, manager_token):
     response = await async_client.get(
         "/users/",
         headers={"Authorization": f"Bearer {manager_token}"}
     )
     assert response.status_code == 200
 
 @pytest.mark.asyncio
 async def test_list_users_unauthorized(async_client, user_token):
     response = await async_client.get(
         "/users/",
         headers={"Authorization": f"Bearer {user_token}"}
     )
     assert response.status_code == 403  # Forbidden, as expected for regular user
     
@pytest.mark.asyncio
async def test_get_user_list_as_admin(async_client, admin_token):
    # Admin should see the list of all users
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await async_client.get("/users/", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_get_user_list_forbidden_for_non_admin(async_client, auth_token):
    # Regular user cannot list all users
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = await async_client.get("/users/", headers=headers)
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_create_user_success(async_client, admin_token):
    # Admin can create a valid new user
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_data = {
        "nickname": "NewUser",
        "email": "newuser@example.com",
        "password": "ValidPass123!",
        "role": "AUTHENTICATED"
    }
    resp = await async_client.post("/users/", json=user_data, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == user_data["email"]
    assert body["nickname"] == user_data["nickname"]

@pytest.mark.asyncio
async def test_delete_user_not_allowed(async_client, admin_user, admin_token):
    # Deleting a user is not implemented or forbidden
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await async_client.delete(f"/users/{admin_user.id}", headers=headers)
    assert resp.status_code in (403, 404)
     