import pytest
from fastapi.testclient import TestClient
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app
from services import store


@pytest.fixture(autouse=True)
def reset_store():
    """Reset shared in-memory state before every test."""
    store.reset_all()
    yield
    store.reset_all()


@pytest.fixture
def client():
    return TestClient(app)
