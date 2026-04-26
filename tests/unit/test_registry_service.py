"""
Unit tests for Registry Service

Tests agent registration, discovery, and management functionality.
"""

import pytest
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

# Assuming the registry service is in api/registry_service/main.py
import sys
sys.path.insert(0, "../../api/registry_service")

from main import app, AgentRegistration, AgentStatus, PricingMode


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_agent():
    """Sample agent data for testing"""
    return {
        "name": "TestAgent",
        "description": "A test agent for unit testing",
        "capabilities": ["python_coding", "data_analysis"],
        "pricing_mode": "commercial",
        "hourly_rate": 25.0,
        "volunteer_percentage": 0,
        "max_concurrent_tasks": 3,
        "supported_languages": ["en", "ru"],
        "metadata": {
            "framework": "langchain",
            "model": "claude-3-sonnet"
        }
    }


class TestAgentRegistration:
    """Test agent registration endpoints"""

    def test_register_agent_success(self, client, sample_agent):
        """Test successful agent registration"""
        response = client.post("/agents", json=sample_agent)

        assert response.status_code == 200
        data = response.json()

        assert "agent_id" in data
        assert data["name"] == sample_agent["name"]
        assert data["status"] == "active"
        assert data["capabilities"] == sample_agent["capabilities"]
        assert data["pricing_mode"] == sample_agent["pricing_mode"]
        assert data["hourly_rate"] == sample_agent["hourly_rate"]

    def test_register_agent_missing_required_fields(self, client):
        """Test registration with missing required fields"""
        invalid_agent = {
            "name": "TestAgent"
            # Missing required fields
        }

        response = client.post("/agents", json=invalid_agent)
        assert response.status_code == 422  # Validation error

    def test_register_agent_invalid_pricing(self, client, sample_agent):
        """Test registration with invalid pricing configuration"""
        sample_agent["pricing_mode"] = "commercial"
        sample_agent["hourly_rate"] = 0.0  # Invalid for commercial

        response = client.post("/agents", json=sample_agent)
        assert response.status_code == 400

    def test_register_volunteer_agent(self, client, sample_agent):
        """Test registration of volunteer agent"""
        sample_agent["pricing_mode"] = "volunteer"
        sample_agent["hourly_rate"] = 0.0
        sample_agent["volunteer_percentage"] = 100

        response = client.post("/agents", json=sample_agent)
        assert response.status_code == 200

        data = response.json()
        assert data["pricing_mode"] == "volunteer"
        assert data["hourly_rate"] == 0.0

    def test_register_hybrid_agent(self, client, sample_agent):
        """Test registration of hybrid agent"""
        sample_agent["pricing_mode"] = "hybrid"
        sample_agent["hourly_rate"] = 20.0
        sample_agent["volunteer_percentage"] = 30

        response = client.post("/agents", json=sample_agent)
        assert response.status_code == 200

        data = response.json()
        assert data["pricing_mode"] == "hybrid"
        assert data["volunteer_percentage"] == 30


class TestAgentDiscovery:
    """Test agent discovery and search endpoints"""

    def setup_method(self):
        """Register test agents before each test"""
        # This would be replaced with proper test database setup
        pass

    def test_list_all_agents(self, client):
        """Test listing all agents"""
        response = client.get("/agents")

        assert response.status_code == 200
        data = response.json()

        assert "agents" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["agents"], list)

    def test_search_by_capabilities(self, client, sample_agent):
        """Test searching agents by capabilities"""
        # Register agent
        client.post("/agents", json=sample_agent)

        # Search by capability
        response = client.get("/agents?capabilities=python_coding")

        assert response.status_code == 200
        data = response.json()

        # All returned agents should have python_coding capability
        for agent in data["agents"]:
            assert "python_coding" in agent["capabilities"]

    def test_search_by_pricing_mode(self, client):
        """Test searching agents by pricing mode"""
        response = client.get("/agents?pricing_mode=commercial")

        assert response.status_code == 200
        data = response.json()

        for agent in data["agents"]:
            assert agent["pricing_mode"] == "commercial"

    def test_search_with_rating_filter(self, client):
        """Test searching agents with minimum rating"""
        response = client.get("/agents?min_rating=4.5")

        assert response.status_code == 200
        data = response.json()

        for agent in data["agents"]:
            assert agent["rating"] >= 4.5

    def test_search_with_max_hourly_rate(self, client):
        """Test searching agents with max hourly rate"""
        response = client.get("/agents?max_hourly_rate=30.0")

        assert response.status_code == 200
        data = response.json()

        for agent in data["agents"]:
            assert agent["hourly_rate"] <= 30.0

    def test_pagination(self, client):
        """Test pagination of agent listing"""
        # Get first page
        response1 = client.get("/agents?page=1&page_size=10")
        assert response1.status_code == 200
        data1 = response1.json()

        # Get second page
        response2 = client.get("/agents?page=2&page_size=10")
        assert response2.status_code == 200
        data2 = response2.json()

        # Pages should have different agents
        if len(data1["agents"]) > 0 and len(data2["agents"]) > 0:
            assert data1["agents"][0]["agent_id"] != data2["agents"][0]["agent_id"]


class TestAgentManagement:
    """Test agent management endpoints"""

    def test_get_agent_by_id(self, client, sample_agent):
        """Test retrieving agent by ID"""
        # Register agent
        register_response = client.post("/agents", json=sample_agent)
        agent_id = register_response.json()["agent_id"]

        # Get agent
        response = client.get(f"/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
        assert data["name"] == sample_agent["name"]

    def test_get_nonexistent_agent(self, client):
        """Test retrieving non-existent agent"""
        fake_id = str(uuid4())
        response = client.get(f"/agents/{fake_id}")

        assert response.status_code == 404

    def test_update_agent_status(self, client, sample_agent):
        """Test updating agent status"""
        # Register agent
        register_response = client.post("/agents", json=sample_agent)
        agent_id = register_response.json()["agent_id"]

        # Update status to inactive
        response = client.patch(
            f"/agents/{agent_id}",
            json={"status": "inactive"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "inactive"

    def test_update_agent_pricing(self, client, sample_agent):
        """Test updating agent pricing"""
        # Register agent
        register_response = client.post("/agents", json=sample_agent)
        agent_id = register_response.json()["agent_id"]

        # Update pricing
        response = client.patch(
            f"/agents/{agent_id}",
            json={"hourly_rate": 30.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["hourly_rate"] == 30.0

    def test_delete_agent(self, client, sample_agent):
        """Test deleting agent"""
        # Register agent
        register_response = client.post("/agents", json=sample_agent)
        agent_id = register_response.json()["agent_id"]

        # Delete agent
        response = client.delete(f"/agents/{agent_id}")
        assert response.status_code == 200

        # Verify agent is deleted
        get_response = client.get(f"/agents/{agent_id}")
        assert get_response.status_code == 404


class TestAgentStatistics:
    """Test agent statistics and metrics"""

    def test_get_agent_statistics(self, client, sample_agent):
        """Test retrieving agent statistics"""
        # Register agent
        register_response = client.post("/agents", json=sample_agent)
        agent_id = register_response.json()["agent_id"]

        # Get statistics
        response = client.get(f"/agents/{agent_id}/statistics")

        assert response.status_code == 200
        data = response.json()

        assert "total_tasks_completed" in data
        assert "total_revenue" in data
        assert "average_rating" in data
        assert "success_rate" in data

    def test_get_platform_statistics(self, client):
        """Test retrieving platform-wide statistics"""
        response = client.get("/statistics")

        assert response.status_code == 200
        data = response.json()

        assert "total_agents" in data
        assert "active_agents" in data
        assert "total_tasks" in data
        assert "average_agent_rating" in data


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limiting(self, client):
        """Test that rate limiting is enforced"""
        # Make many requests quickly
        responses = []
        for _ in range(150):  # Assuming limit is 100/s
            response = client.get("/agents")
            responses.append(response)

        # Some requests should be rate limited
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
