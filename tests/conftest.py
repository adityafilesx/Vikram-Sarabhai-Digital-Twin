import os
import pytest
from dotenv import load_dotenv

# Load environment variables for all tests
load_dotenv()

@pytest.fixture
def test_memory_db():
    """Provide an in-memory SQLite database for testing."""
    from memory.memory_db import MemoryDatabase
    db = MemoryDatabase("sqlite:///:memory:")
    return db
