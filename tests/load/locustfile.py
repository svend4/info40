"""
Locust Load Testing for AI Agent Orchestration Platform

Run with:
    locust -f locustfile.py --host=http://localhost:8000

Or with specific user count:
    locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10
"""

from locust import HttpUser, task, between, SequentialTaskSet, events
from locust.contrib.fasthttp import FastHttpUser
import random
import json
import uuid
from datetime import datetime, timedelta


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_agent_data():
    """Generate mock agent registration data"""
    capabilities = ['python_coding', 'data_analysis', 'javascript', 'research', 'writing']

    return {
        "name": f"Agent-{uuid.uuid4().hex[:8]}",
        "description": "Test agent for load testing",
        "capabilities": random.sample(capabilities, k=random.randint(1, 3)),
        "pricing_mode": random.choice(["commercial", "volunteer", "hybrid"]),
        "hourly_rate": round(random.uniform(10, 100), 2),
        "volunteer_percentage": random.randint(0, 50),
        "max_concurrent_tasks": random.randint(1, 5),
        "supported_languages": ["en", "ru"],
        "metadata": {
            "test": True,
            "load_test_timestamp": datetime.now().isoformat()
        }
    }


def generate_task_data(customer_id):
    """Generate mock task creation data"""
    capabilities = ['python_coding', 'data_analysis', 'javascript', 'research', 'writing']

    return {
        "customer_id": customer_id,
        "title": f"Test Task {uuid.uuid4().hex[:8]}",
        "description": "Load testing task " * 10,  # Make it at least 100 chars
        "required_capabilities": random.sample(capabilities, k=random.randint(1, 2)),
        "budget": round(random.uniform(100, 1000), 2),
        "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
        "priority": random.choice(["low", "medium", "high"]),
        "rental_mode": "commercial",
        "metadata": {
            "test": True
        }
    }


def generate_search_params():
    """Generate agent search parameters"""
    capabilities = ['python_coding', 'data_analysis', 'javascript', 'research', 'writing']

    params = {
        "page": random.randint(1, 5),
        "page_size": 20,
        "available_only": True,
        "sort_by": random.choice(["rating", "price", "tasks"]),
        "sort_order": "desc"
    }

    # Randomly add filters
    if random.random() > 0.5:
        params["capabilities"] = random.choice(capabilities)

    if random.random() > 0.7:
        params["min_rating"] = round(random.uniform(3.0, 4.5), 1)

    if random.random() > 0.7:
        params["max_hourly_rate"] = round(random.uniform(20, 80), 2)

    return params


def generate_review_data(agent_id, user_id):
    """Generate review data"""
    return {
        "agent_id": agent_id,
        "user_id": user_id,
        "rating": round(random.uniform(3.0, 5.0), 1),
        "quality_score": round(random.uniform(3.0, 5.0), 1),
        "speed_score": round(random.uniform(3.0, 5.0), 1),
        "communication_score": round(random.uniform(3.0, 5.0), 1),
        "value_for_money_score": round(random.uniform(3.0, 5.0), 1),
        "comment": "Great work! " * 5,  # At least 50 chars
        "would_recommend": random.choice([True, False])
    }


# ============================================================================
# Task Sets
# ============================================================================

class MarketplaceUserBehavior(SequentialTaskSet):
    """Simulates typical marketplace user behavior"""

    def on_start(self):
        """Initialize user session"""
        self.user_id = f"user-{uuid.uuid4()}"
        self.searched_agents = []

    @task
    def search_agents(self):
        """Search for agents"""
        params = generate_search_params()

        with self.client.get(
            "/marketplace/agents/search",
            json=params,
            catch_response=True,
            name="/marketplace/agents/search"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.searched_agents = [agent['agent_id'] for agent in data.get('agents', [])]
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")

    @task
    def view_agent_profile(self):
        """View detailed agent profile"""
        if not self.searched_agents:
            return

        agent_id = random.choice(self.searched_agents)

        with self.client.get(
            f"/marketplace/agents/{agent_id}/marketplace-profile",
            catch_response=True,
            name="/marketplace/agents/[id]/marketplace-profile"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Profile view failed: {response.status_code}")

    @task
    def create_contract(self):
        """Create rental contract"""
        if not self.searched_agents:
            return

        agent_id = random.choice(self.searched_agents)

        contract_data = {
            "agent_id": agent_id,
            "customer_id": self.user_id,
            "rental_mode": "commercial",
            "billing_model": "hourly",
            "hourly_rate": 25.0,
            "estimated_hours": 10.0
        }

        with self.client.post(
            "/marketplace/contracts",
            json=contract_data,
            catch_response=True,
            name="/marketplace/contracts"
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Contract creation failed: {response.status_code}")

    @task
    def submit_review(self):
        """Submit agent review"""
        if not self.searched_agents:
            return

        agent_id = random.choice(self.searched_agents)
        review_data = generate_review_data(agent_id, self.user_id)

        with self.client.post(
            "/marketplace/reviews",
            json=review_data,
            catch_response=True,
            name="/marketplace/reviews"
        ) as response:
            if response.status_code in [200, 201, 400]:  # 400 for duplicate reviews
                response.success()
            else:
                response.failure(f"Review submission failed: {response.status_code}")


class OrchestratorUserBehavior(SequentialTaskSet):
    """Simulates task creation and management"""

    def on_start(self):
        """Initialize user session"""
        self.customer_id = f"customer-{uuid.uuid4()}"
        self.created_tasks = []

    @task
    def create_task(self):
        """Create a new task"""
        task_data = generate_task_data(self.customer_id)

        with self.client.post(
            "/orchestrator/tasks",
            json=task_data,
            catch_response=True,
            name="/orchestrator/tasks [POST]"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.created_tasks.append(data['task_id'])
                response.success()
            else:
                response.failure(f"Task creation failed: {response.status_code}")

    @task
    def check_task_status(self):
        """Check status of created task"""
        if not self.created_tasks:
            return

        task_id = random.choice(self.created_tasks)

        with self.client.get(
            f"/orchestrator/tasks/{task_id}",
            catch_response=True,
            name="/orchestrator/tasks/[id] [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Task status check failed: {response.status_code}")

    @task
    def get_task_decomposition(self):
        """Get task decomposition"""
        if not self.created_tasks:
            return

        task_id = random.choice(self.created_tasks)

        with self.client.get(
            f"/orchestrator/tasks/{task_id}/decomposition",
            catch_response=True,
            name="/orchestrator/tasks/[id]/decomposition"
        ) as response:
            if response.status_code in [200, 404]:  # 404 if not yet decomposed
                response.success()
            else:
                response.failure(f"Decomposition fetch failed: {response.status_code}")

    @task
    def list_my_tasks(self):
        """List customer's tasks"""
        with self.client.get(
            f"/orchestrator/tasks?customer_id={self.customer_id}",
            catch_response=True,
            name="/orchestrator/tasks [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Task list failed: {response.status_code}")


class RegistryUserBehavior(SequentialTaskSet):
    """Simulates agent registration and management"""

    def on_start(self):
        """Initialize user session"""
        self.owner_id = f"owner-{uuid.uuid4()}"
        self.registered_agents = []

    @task
    def register_agent(self):
        """Register a new agent"""
        agent_data = generate_agent_data()

        with self.client.post(
            "/registry/agents",
            json=agent_data,
            catch_response=True,
            name="/registry/agents [POST]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.registered_agents.append(data['agent_id'])
                response.success()
            else:
                response.failure(f"Agent registration failed: {response.status_code}")

    @task
    def list_agents(self):
        """List all agents"""
        params = {"page": random.randint(1, 3), "page_size": 20}

        with self.client.get(
            "/registry/agents",
            params=params,
            catch_response=True,
            name="/registry/agents [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Agent list failed: {response.status_code}")

    @task
    def get_agent_details(self):
        """Get agent details"""
        if not self.registered_agents:
            return

        agent_id = random.choice(self.registered_agents)

        with self.client.get(
            f"/registry/agents/{agent_id}",
            catch_response=True,
            name="/registry/agents/[id]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Agent details failed: {response.status_code}")


# ============================================================================
# User Classes
# ============================================================================

class MarketplaceUser(FastHttpUser):
    """User focused on marketplace operations"""
    wait_time = between(1, 3)
    tasks = [MarketplaceUserBehavior]
    weight = 3  # 30% of users


class OrchestratorUser(FastHttpUser):
    """User focused on task creation and management"""
    wait_time = between(2, 5)
    tasks = [OrchestratorUserBehavior]
    weight = 5  # 50% of users


class RegistryUser(FastHttpUser):
    """User focused on agent registration"""
    wait_time = between(3, 7)
    tasks = [RegistryUserBehavior]
    weight = 2  # 20% of users


class MixedBehaviorUser(FastHttpUser):
    """User with mixed behavior patterns"""
    wait_time = between(1, 5)

    @task(3)
    def marketplace_task(self):
        """Marketplace operations"""
        behavior = MarketplaceUserBehavior(self)
        behavior.run()

    @task(2)
    def orchestrator_task(self):
        """Orchestration operations"""
        behavior = OrchestratorUserBehavior(self)
        behavior.run()

    @task(1)
    def registry_task(self):
        """Registry operations"""
        behavior = RegistryUserBehavior(self)
        behavior.run()

    weight = 1  # 10% of users


# ============================================================================
# Event Handlers for Custom Metrics
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    print("🚀 Load test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    print("\n✅ Load test completed!")

    # Print summary statistics
    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests per second: {stats.total.total_rps:.2f}")

    if stats.total.num_requests > 0:
        failure_rate = (stats.total.num_failures / stats.total.num_requests) * 100
        print(f"Failure rate: {failure_rate:.2f}%")


# ============================================================================
# Custom Shape (Advanced Load Testing)
# ============================================================================

from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    A step load shape that increases users in steps

    Step 1: 10 users for 60s
    Step 2: 50 users for 60s
    Step 3: 100 users for 60s
    Step 4: 200 users for 60s
    Step 5: 300 users for 60s
    """

    step_time = 60
    step_load = 10
    spawn_rate = 10
    time_limit = 300

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = int(run_time // self.step_time)
        users = self.step_load * (current_step + 1) * (2 ** min(current_step, 4))

        return (min(users, 300), self.spawn_rate)


if __name__ == "__main__":
    import os
    os.system("locust -f locustfile.py --host=http://localhost:8000")
