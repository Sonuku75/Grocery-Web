import os
import sys
import pytest
from typing import Generator
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Synchronous FastAPI TestClient fixture for reliable, fast ASGI testing.
    """
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
