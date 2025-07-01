# tests/test_basic.py
"""
Basic tests to verify the core functionality works.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app

# Test client
client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns basic info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "Multi-Service API Testing Platform"

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code in [200, 503]  # May be 503 during startup
    data = response.json()
    assert "status" in data
    assert "components" in data

def test_system_info():
    """Test system info endpoint."""
    response = client.get("/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert "services" in data

def test_list_services():
    """Test service listing endpoint."""
    response = client.get("/api/v1/services/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_docs_endpoint():
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()