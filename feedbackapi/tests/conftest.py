import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from feedbackapi.main import app
from feedbackapi.models import Base
from feedbackapi.db import get_db
from feedbackapi.settings import TEST_DB_URL


# ---------------------------
# Event loop fixture
# ---------------------------
@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------
# Test DB engine
# ---------------------------
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    if not TEST_DB_URL:
        raise RuntimeError(
            "TEST_DB_URL not set! Ensure DATABASE_URL is present in test.env"
        )
    
    engine = create_async_engine(TEST_DB_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


# ---------------------------
# Async DB session fixture
# ---------------------------
@pytest_asyncio.fixture
async def db_session(test_engine):
    AsyncSessionLocal = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        async with session.begin_nested():
            yield session
            await session.rollback()


# ---------------------------
# Test client fixture
# ---------------------------
@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
