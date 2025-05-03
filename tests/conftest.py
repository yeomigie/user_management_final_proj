"""
File: tests/conftest.py

Overview:
This file configures pytest fixtures for database setup/teardown, HTTP client,
user states, authentication tokens, and email stubbing.
"""

# Standard library imports
from datetime import timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

# Third-party imports
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, scoped_session
from faker import Faker

# Application-specific imports
from app.main import app
from app.database import Base, Database
from app.models.user_model import User, UserRole
from app.dependencies import get_db, get_settings
from app.utils.security import hash_password
from app.utils.template_manager import TemplateManager
from app.services.email_service import EmailService
from app.services.jwt_service import create_access_token

fake = Faker()
settings = get_settings()

# Configure test database URL for asyncpg
TEST_DATABASE_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(TEST_DATABASE_URL, echo=settings.debug)
AsyncTestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
AsyncSessionScoped = scoped_session(AsyncTestingSessionLocal)

# -------------------------------------------------------------------
# Prevent real SMTP connections in all tests
# -------------------------------------------------------------------
@pytest.fixture(autouse=True, scope="session")
def _stub_smtp(monkeypatch):
    """
    Stub out SMTPConnection.send_email so no real SMTP calls occur.
    """
    def _noop_send(self, *args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.utils.smtp_connection.SMTPConnection.send_email",
        _noop_send,
        raising=False
    )

# -------------------------------------------------------------------
# EmailService fixture with stubbed smtp_client.send_email
# -------------------------------------------------------------------
@pytest.fixture
def email_service(monkeypatch):
    """
    Provides an EmailService whose smtp_client.send_email is a no-op.
    """
    svc = EmailService(template_manager=TemplateManager())
    # Stub the low-level send_email
    monkeypatch.setattr(svc.smtp_client, "send_email", lambda *a, **k: None)
    return svc

# -------------------------------------------------------------------
# HTTP client fixture
# -------------------------------------------------------------------
@pytest.fixture(scope="function")
async def async_client(db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

# -------------------------------------------------------------------
# Database initialization & teardown
# -------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    try:
        Database.initialize(settings.database_url)
    except Exception as e:
        pytest.fail(f"Failed to initialize the database: {e}")

@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(setup_database):
    async with AsyncSessionScoped() as session:
        yield session
        await session.close()

# -------------------------------------------------------------------
# User fixtures
# -------------------------------------------------------------------
@pytest.fixture(scope="function")
async def locked_user(db_session):
    user = User(
        nickname=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        hashed_password=hash_password("MySuperPassword$1234"),
        role=UserRole.AUTHENTICATED,
        email_verified=False,
        is_locked=True,
        failed_login_attempts=settings.max_login_attempts,
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def user(db_session):
    user = User(
        nickname=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        hashed_password=hash_password("MySuperPassword$1234"),
        role=UserRole.AUTHENTICATED,
        email_verified=False,
        is_locked=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def verified_user(db_session):
    user = User(
        nickname=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        hashed_password=hash_password("MySuperPassword$1234"),
        role=UserRole.AUTHENTICATED,
        email_verified=True,
        is_locked=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def unverified_user(db_session):
    user = User(
        nickname=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        hashed_password=hash_password("MySuperPassword$1234"),
        role=UserRole.AUTHENTICATED,
        email_verified=False,
        is_locked=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def professional_user(db_session: AsyncSession):
    user = User(
        nickname="ProfessionalUser",
        email="professional@example.com",
        hashed_password=hash_password("StrongPassword123!"),
        is_professional=True,
        role=UserRole.AUTHENTICATED,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
async def users_with_same_role_50_users(db_session):
    users = []
    for _ in range(50):
        u = User(
            nickname=fake.user_name(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            hashed_password=hash_password("MySuperPassword$1234"),
            role=UserRole.AUTHENTICATED,
            email_verified=False,
            is_locked=False,
        )
        db_session.add(u)
        users.append(u)
    await db_session.commit()
    return users

@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession):
    user = User(
        nickname="admin_user",
        first_name="John",
        last_name="Doe",
        email="admin@example.com",
        hashed_password="securepassword",
        role=UserRole.ADMIN,
        is_locked=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture(scope="function")
async def manager_user(db_session: AsyncSession):
    user = User(
        nickname="manager_john",
        first_name="John",
        last_name="Doe",
        email="manager_user@example.com",
        hashed_password="securepassword",
        role=UserRole.MANAGER,
        is_locked=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user

# -------------------------------------------------------------------
# Token fixtures
# -------------------------------------------------------------------
@pytest.fixture(scope="function")
def admin_token(admin_user):
    token_data = {"sub": str(admin_user.id), "role": admin_user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))

@pytest.fixture(scope="function")
def manager_token(manager_user):
    token_data = {"sub": str(manager_user.id), "role": manager_user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))

@pytest.fixture(scope="function")
def user_token(user):
    token_data = {"sub": str(user.id), "role": user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))

@pytest.fixture(scope="function")
def auth_token(verified_user):
    token_data = {"sub": str(verified_user.id), "role": verified_user.role.name}
    return create_access_token(data=token_data, expires_delta=timedelta(minutes=30))