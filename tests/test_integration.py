import pytest
import os

# Skip integration tests if API key is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set — skipping integration tests"
)

def test_login_endpoint():
    """Test user login endpoint."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    response = client.post("/users/login", json={"username": "integration_user", "display_name": "Integration User"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "integration_user"
    assert "id" in data

def test_start_conversation():
    """Test starting a conversation."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    # First login
    login_resp = client.post("/users/login", json={"username": "integration_user_2", "display_name": "Integration User 2"})
    user_id = login_resp.json()["id"]
    
    # Start conv
    conv_resp = client.post("/conversations", json={"user_id": user_id})
    assert conv_resp.status_code == 200
    assert "id" in conv_resp.json()

def test_health_endpoint():
    """Test health check endpoint."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_memory_dashboard():
    """Test memory dashboard endpoint returns valid structure."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/memory/nonexistent_user/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "interests" in data
    assert "projects" in data
