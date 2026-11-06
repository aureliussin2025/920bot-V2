from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from fastapi.testclient import TestClient
# Importing main also runs its create_all() on the normal database engine;
# the override below affects endpoint requests, not that import-time setup.
from main import app
from db import Base, get_db

# Tests use their own SQLite file instead of the application's database.
TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    # TestClient may handle requests on another thread; SQLite normally
    # restricts a connection to the thread that created it.
    connect_args={"check_same_thread": False}
)

# Every request in a test receives a session bound to the test database.
TestingSessionLocal = sessionmaker(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    # Create test tables if missing. The teardown below drops them between
    # tests; create_all alone would not erase data left by an interrupted run.
    Base.metadata.create_all(bind=test_engine)

    # Replace the real get_db dependency whenever TestClient calls the app.
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        # The test function runs here with this configured client.
        yield test_client

    # Cleanup runs after the test, including when an assertion fails.
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
