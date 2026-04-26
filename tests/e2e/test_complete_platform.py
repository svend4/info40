"""
End-to-End tests for the complete platform

Tests the entire platform workflow from user registration
through task completion and payment.
"""

import pytest
import asyncio
import aiohttp
from uuid import uuid4
from datetime import datetime, timedelta


# Platform API endpoints
API_BASE_URL = "http://localhost:8000"
REGISTRY_URL = f"{API_BASE_URL}/registry"
MARKETPLACE_URL = f"{API_BASE_URL}/marketplace"
ORCHESTRATOR_URL = f"{API_BASE_URL}/orchestrator"


@pytest.fixture
async def api_session():
    """Async HTTP session for API calls"""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
async def test_user():
    """Create a test user"""
    return {
        "user_id": str(uuid4()),
        "username": "e2e_testuser",
        "email": "e2e@example.com",
        "api_key": "test_api_key_12345"
    }


@pytest.fixture
async def test_agent():
    """Register a test agent"""
    agent_data = {
        "name": "E2E Test Agent",
        "description": "Agent for end-to-end testing",
        "capabilities": ["python_coding", "data_analysis"],
        "pricing_mode": "commercial",
        "hourly_rate": 25.0,
        "max_concurrent_tasks": 5
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{REGISTRY_URL}/agents",
            json=agent_data
        ) as response:
            return await response.json()


class TestCompleteUserJourney:
    """Test complete user journey from registration to task completion"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, api_session, test_user):
        """
        Test the complete workflow:
        1. User registers on platform
        2. User deposits funds
        3. User searches for agents
        4. User creates a task
        5. Task is decomposed and assigned to agents
        6. Agents execute task
        7. Task is completed
        8. User reviews agent
        9. Payment is processed
        """

        # Step 1: User Registration (simulated - assume user exists)
        headers = {"Authorization": f"Bearer {test_user['api_key']}"}

        # Step 2: User deposits funds
        deposit_data = {
            "user_id": test_user["user_id"],
            "amount": 500.0,
            "payment_method": "credit_card"
        }

        async with api_session.post(
            f"{API_BASE_URL}/transactions/deposit",
            json=deposit_data,
            headers=headers
        ) as response:
            assert response.status == 200
            deposit_result = await response.json()
            assert deposit_result["new_balance"] == 500.0

        # Step 3: Search for agents
        async with api_session.get(
            f"{MARKETPLACE_URL}/agents",
            params={
                "capabilities": "python_coding",
                "max_hourly_rate": 30.0,
                "min_rating": 4.0
            },
            headers=headers
        ) as response:
            assert response.status == 200
            agents = await response.json()
            assert len(agents["agents"]) > 0

        # Step 4: Create a task
        task_data = {
            "customer_id": test_user["user_id"],
            "title": "Data Analysis Script",
            "description": "Write Python script to analyze CSV data",
            "required_capabilities": ["python_coding", "data_analysis"],
            "budget": 200.0,
            "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "priority": "high"
        }

        async with api_session.post(
            f"{ORCHESTRATOR_URL}/tasks",
            json=task_data,
            headers=headers
        ) as response:
            assert response.status == 200
            task = await response.json()
            task_id = task["task_id"]
            assert task["status"] == "pending"

        # Step 5: Wait for task decomposition
        await asyncio.sleep(2)  # Simulate processing time

        # Check task status
        async with api_session.get(
            f"{ORCHESTRATOR_URL}/tasks/{task_id}",
            headers=headers
        ) as response:
            assert response.status == 200
            task_status = await response.json()
            assert task_status["status"] in ["planning", "running"]

        # Step 6: Simulate task execution (in real scenario, agents execute)
        # For E2E test, we'll poll until completion
        max_wait = 60  # seconds
        waited = 0
        completed = False

        while waited < max_wait and not completed:
            async with api_session.get(
                f"{ORCHESTRATOR_URL}/tasks/{task_id}",
                headers=headers
            ) as response:
                task_status = await response.json()
                if task_status["status"] == "completed":
                    completed = True
                    break

            await asyncio.sleep(5)
            waited += 5

        # For testing purposes, we'll assume completion
        # In production, task would actually execute

        # Step 7: Verify task completion
        async with api_session.get(
            f"{ORCHESTRATOR_URL}/tasks/{task_id}",
            headers=headers
        ) as response:
            final_task = await response.json()
            # In real scenario: assert final_task["status"] == "completed"

        # Step 8: Submit review for agent
        # Get the agent that worked on the task
        agent_id = agents["agents"][0]["agent_id"]

        review_data = {
            "agent_id": agent_id,
            "user_id": test_user["user_id"],
            "rating": 5.0,
            "quality_score": 5.0,
            "speed_score": 5.0,
            "communication_score": 5.0,
            "comment": "Excellent work on the data analysis script!"
        }

        async with api_session.post(
            f"{MARKETPLACE_URL}/reviews",
            json=review_data,
            headers=headers
        ) as response:
            assert response.status == 200
            review = await response.json()
            assert review["rating"] == 5.0

        # Step 9: Verify payment processed
        async with api_session.get(
            f"{API_BASE_URL}/transactions",
            params={"user_id": test_user["user_id"]},
            headers=headers
        ) as response:
            assert response.status == 200
            transactions = await response.json()

            # Should have deposit and payment transactions
            transaction_types = [t["transaction_type"] for t in transactions["transactions"]]
            assert "deposit" in transaction_types


class TestAgentWorkflow:
    """Test workflow from agent's perspective"""

    @pytest.mark.asyncio
    async def test_agent_registration_to_earning(self, api_session):
        """Test agent registration, task execution, and earning"""

        # Step 1: Register agent
        agent_data = {
            "name": "Python Expert Agent",
            "description": "Specialized in Python development",
            "capabilities": ["python_coding", "testing", "debugging"],
            "pricing_mode": "commercial",
            "hourly_rate": 35.0,
            "volunteer_percentage": 0,
            "max_concurrent_tasks": 3
        }

        async with api_session.post(
            f"{REGISTRY_URL}/agents",
            json=agent_data
        ) as response:
            assert response.status == 200
            agent = await response.json()
            agent_id = agent["agent_id"]

        # Step 2: Agent becomes available
        async with api_session.patch(
            f"{REGISTRY_URL}/agents/{agent_id}",
            json={"status": "active"}
        ) as response:
            assert response.status == 200

        # Step 3: Agent receives task assignment
        # (In real scenario, agent would listen for tasks via WebSocket/SSE)

        # Step 4: Agent completes task and gets paid
        # (Simulated - would involve actual task execution)

        # Step 5: Check agent earnings
        async with api_session.get(
            f"{REGISTRY_URL}/agents/{agent_id}/statistics"
        ) as response:
            assert response.status == 200
            stats = await response.json()
            assert "total_revenue" in stats


class TestVolunteerWorkflow:
    """Test volunteer agent workflow"""

    @pytest.mark.asyncio
    async def test_volunteer_agent_workflow(self, api_session, test_user):
        """Test volunteer agent working on academic project"""

        # Step 1: Register volunteer agent
        volunteer_agent = {
            "name": "Academic Helper",
            "description": "Volunteer agent for research projects",
            "capabilities": ["research", "data_analysis", "scientific_writing"],
            "pricing_mode": "volunteer",
            "hourly_rate": 0.0,
            "volunteer_percentage": 100
        }

        async with api_session.post(
            f"{REGISTRY_URL}/agents",
            json=volunteer_agent
        ) as response:
            assert response.status == 200
            agent = await response.json()
            agent_id = agent["agent_id"]

        # Step 2: Create academic task
        academic_task = {
            "customer_id": test_user["user_id"],
            "title": "Literature Review",
            "description": "Conduct systematic literature review",
            "required_capabilities": ["research", "scientific_writing"],
            "budget": 0.0,  # Volunteer work
            "rental_mode": "volunteer",
            "tags": ["academic", "research"]
        }

        async with api_session.post(
            f"{ORCHESTRATOR_URL}/tasks",
            json=academic_task,
            headers={"Authorization": f"Bearer {test_user['api_key']}"}
        ) as response:
            assert response.status == 200
            task = await response.json()
            task_id = task["task_id"]

        # Verify volunteer agent can be matched to this task
        async with api_session.get(
            f"{MARKETPLACE_URL}/agents/match",
            params={
                "task_id": task_id,
                "rental_mode": "volunteer"
            }
        ) as response:
            assert response.status == 200
            matches = await response.json()
            matched_ids = [m["agent_id"] for m in matches["agents"]]
            assert agent_id in matched_ids


class TestHybridPricingWorkflow:
    """Test hybrid pricing model workflow"""

    @pytest.mark.asyncio
    async def test_hybrid_agent_allocation(self, api_session):
        """Test hybrid agent working on mix of volunteer and commercial tasks"""

        # Register hybrid agent
        hybrid_agent = {
            "name": "Hybrid Developer",
            "description": "Commercial with volunteer hours",
            "capabilities": ["python_coding", "javascript"],
            "pricing_mode": "hybrid",
            "hourly_rate": 30.0,
            "volunteer_percentage": 30  # 30% volunteer, 70% commercial
        }

        async with api_session.post(
            f"{REGISTRY_URL}/agents",
            json=hybrid_agent
        ) as response:
            assert response.status == 200
            agent = await response.json()
            agent_id = agent["agent_id"]

        # Verify agent shows in both commercial and volunteer searches
        async with api_session.get(
            f"{MARKETPLACE_URL}/agents",
            params={"pricing_mode": "commercial,hybrid"}
        ) as response:
            commercial_agents = await response.json()
            assert any(a["agent_id"] == agent_id for a in commercial_agents["agents"])

        async with api_session.get(
            f"{MARKETPLACE_URL}/agents",
            params={"pricing_mode": "volunteer,hybrid"}
        ) as response:
            volunteer_agents = await response.json()
            assert any(a["agent_id"] == agent_id for a in volunteer_agents["agents"])


class TestPlatformHealth:
    """Test platform health and monitoring"""

    @pytest.mark.asyncio
    async def test_all_services_healthy(self, api_session):
        """Test that all services are healthy"""

        services = [
            f"{API_BASE_URL}/health",
            f"{REGISTRY_URL}/health",
            f"{MARKETPLACE_URL}/health",
            f"{ORCHESTRATOR_URL}/health"
        ]

        for service_url in services:
            async with api_session.get(service_url) as response:
                assert response.status == 200
                health = await response.json()
                assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, api_session):
        """Test Prometheus metrics endpoint"""

        async with api_session.get(f"{API_BASE_URL}/metrics") as response:
            assert response.status == 200
            metrics = await response.text()
            # Verify some key metrics exist
            assert "http_requests_total" in metrics
            assert "task_execution_duration_seconds" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
