"""
Integration tests for Orchestration Workflow

Tests the complete workflow from task creation to completion
with real database and service interactions.
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
import psycopg2
import redis
import pika

# Test configuration
TEST_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "agent_platform_test",
    "user": "postgres",
    "password": "test_password"
}

TEST_REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0
}

TEST_RABBITMQ_CONFIG = {
    "host": "localhost",
    "port": 5672,
    "username": "guest",
    "password": "guest"
}


@pytest.fixture(scope="session")
def db_connection():
    """Database connection for integration tests"""
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def redis_client():
    """Redis client for integration tests"""
    client = redis.Redis(**TEST_REDIS_CONFIG)
    yield client
    client.close()


@pytest.fixture(scope="session")
def rabbitmq_connection():
    """RabbitMQ connection for integration tests"""
    credentials = pika.PlainCredentials(
        TEST_RABBITMQ_CONFIG["username"],
        TEST_RABBITMQ_CONFIG["password"]
    )
    parameters = pika.ConnectionParameters(
        host=TEST_RABBITMQ_CONFIG["host"],
        port=TEST_RABBITMQ_CONFIG["port"],
        credentials=credentials
    )
    connection = pika.BlockingConnection(parameters)
    yield connection
    connection.close()


@pytest.fixture(autouse=True)
def setup_teardown_db(db_connection):
    """Setup and teardown database for each test"""
    cursor = db_connection.cursor()

    # Setup: Create test data
    yield

    # Teardown: Clean up test data
    cursor.execute("TRUNCATE TABLE tasks, subtasks, rental_contracts CASCADE")
    db_connection.commit()
    cursor.close()


class TestCompleteWorkflow:
    """Test complete task orchestration workflow"""

    @pytest.mark.asyncio
    async def test_simple_task_workflow(self, db_connection):
        """Test simple task from creation to completion"""

        # Step 1: Create a task
        task_data = {
            "customer_id": str(uuid4()),
            "title": "Simple Python Script",
            "description": "Write a Python script to parse CSV",
            "required_capabilities": ["python_coding"],
            "budget": 100.0,
            "deadline": (datetime.now() + timedelta(days=7)).isoformat()
        }

        cursor = db_connection.cursor()
        task_id = str(uuid4())

        cursor.execute("""
            INSERT INTO tasks (
                task_id, customer_id, title, description,
                required_capabilities, budget, deadline, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING task_id
        """, (
            task_id,
            task_data["customer_id"],
            task_data["title"],
            task_data["description"],
            task_data["required_capabilities"],
            task_data["budget"],
            task_data["deadline"],
            "pending"
        ))

        db_connection.commit()

        # Step 2: Verify task was created
        cursor.execute("SELECT * FROM tasks WHERE task_id = %s", (task_id,))
        task = cursor.fetchone()
        assert task is not None

        # Step 3: Simulate task decomposition into subtasks
        subtask_id = str(uuid4())
        cursor.execute("""
            INSERT INTO subtasks (
                subtask_id, task_id, title, description,
                required_capabilities, estimated_cost, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            subtask_id,
            task_id,
            "Parse CSV file",
            "Write Python code to parse CSV",
            ["python_coding"],
            50.0,
            "pending"
        ))

        db_connection.commit()

        # Step 4: Assign agent to subtask
        agent_id = str(uuid4())
        cursor.execute("""
            UPDATE subtasks
            SET assigned_agent_id = %s, status = %s
            WHERE subtask_id = %s
        """, (agent_id, "assigned", subtask_id))

        db_connection.commit()

        # Step 5: Complete subtask
        cursor.execute("""
            UPDATE subtasks
            SET status = %s, completed_at = %s
            WHERE subtask_id = %s
        """, ("completed", datetime.now(), subtask_id))

        db_connection.commit()

        # Step 6: Mark main task as completed
        cursor.execute("""
            UPDATE tasks
            SET status = %s, completed_at = %s, actual_cost = %s
            WHERE task_id = %s
        """, ("completed", datetime.now(), 50.0, task_id))

        db_connection.commit()

        # Step 7: Verify final state
        cursor.execute("SELECT status, actual_cost FROM tasks WHERE task_id = %s", (task_id,))
        result = cursor.fetchone()
        assert result[0] == "completed"  # status
        assert result[1] == 50.0  # actual_cost

        cursor.close()


    @pytest.mark.asyncio
    async def test_complex_task_with_dependencies(self, db_connection):
        """Test complex task with multiple subtasks and dependencies"""

        cursor = db_connection.cursor()

        # Create main task
        task_id = str(uuid4())
        cursor.execute("""
            INSERT INTO tasks (
                task_id, customer_id, title, description,
                required_capabilities, budget, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            task_id,
            str(uuid4()),
            "Build Web Application",
            "Complete web app with frontend and backend",
            ["python_coding", "javascript", "database"],
            1000.0,
            "pending"
        ))

        # Create subtasks with dependencies
        subtask_1_id = str(uuid4())  # Database schema
        subtask_2_id = str(uuid4())  # Backend API (depends on 1)
        subtask_3_id = str(uuid4())  # Frontend (depends on 2)

        # Subtask 1: Database schema (no dependencies)
        cursor.execute("""
            INSERT INTO subtasks (
                subtask_id, task_id, title, execution_level,
                dependencies, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (subtask_1_id, task_id, "Design database schema", 0, [], "pending"))

        # Subtask 2: Backend API (depends on subtask 1)
        cursor.execute("""
            INSERT INTO subtasks (
                subtask_id, task_id, title, execution_level,
                dependencies, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (subtask_2_id, task_id, "Build backend API", 1, [subtask_1_id], "pending"))

        # Subtask 3: Frontend (depends on subtask 2)
        cursor.execute("""
            INSERT INTO subtasks (
                subtask_id, task_id, title, execution_level,
                dependencies, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (subtask_3_id, task_id, "Build frontend", 2, [subtask_2_id], "pending"))

        db_connection.commit()

        # Execute subtasks in order
        # Level 0: Database schema
        cursor.execute("""
            UPDATE subtasks
            SET status = %s, completed_at = %s
            WHERE subtask_id = %s
        """, ("completed", datetime.now(), subtask_1_id))

        # Level 1: Backend API (after database is done)
        cursor.execute("""
            UPDATE subtasks
            SET status = %s, completed_at = %s
            WHERE subtask_id = %s
        """, ("completed", datetime.now(), subtask_2_id))

        # Level 2: Frontend (after backend is done)
        cursor.execute("""
            UPDATE subtasks
            SET status = %s, completed_at = %s
            WHERE subtask_id = %s
        """, ("completed", datetime.now(), subtask_3_id))

        db_connection.commit()

        # Verify all subtasks completed
        cursor.execute("""
            SELECT COUNT(*) FROM subtasks
            WHERE task_id = %s AND status = %s
        """, (task_id, "completed"))

        count = cursor.fetchone()[0]
        assert count == 3

        cursor.close()


class TestAgentMarketplace:
    """Test marketplace operations"""

    def test_agent_rental_contract(self, db_connection):
        """Test creating and managing rental contracts"""

        cursor = db_connection.cursor()

        # Create rental contract
        contract_id = str(uuid4())
        agent_id = str(uuid4())
        customer_id = str(uuid4())

        cursor.execute("""
            INSERT INTO rental_contracts (
                contract_id, agent_id, customer_id, rental_mode,
                billing_model, hourly_rate, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            contract_id,
            agent_id,
            customer_id,
            "commercial",
            "hourly",
            25.0,
            "active"
        ))

        db_connection.commit()

        # Verify contract
        cursor.execute("SELECT * FROM rental_contracts WHERE contract_id = %s", (contract_id,))
        contract = cursor.fetchone()
        assert contract is not None

        # Complete contract
        cursor.execute("""
            UPDATE rental_contracts
            SET status = %s, end_time = %s, total_cost = %s
            WHERE contract_id = %s
        """, ("completed", datetime.now(), 200.0, contract_id))

        db_connection.commit()

        # Create review for the agent
        review_id = str(uuid4())
        cursor.execute("""
            INSERT INTO reviews (
                review_id, agent_id, user_id, contract_id,
                rating, quality_score, speed_score, communication_score,
                comment
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            review_id,
            agent_id,
            customer_id,
            contract_id,
            5.0,
            5.0,
            5.0,
            5.0,
            "Excellent work!"
        ))

        db_connection.commit()

        cursor.close()


class TestPaymentFlow:
    """Test payment and transaction flow"""

    def test_complete_payment_flow(self, db_connection):
        """Test complete payment flow from deposit to payment"""

        cursor = db_connection.cursor()

        user_id = str(uuid4())

        # Create user with initial balance
        cursor.execute("""
            INSERT INTO users (user_id, username, email, balance)
            VALUES (%s, %s, %s, %s)
        """, (user_id, "testuser", "test@example.com", 0.0))

        # Step 1: User deposits money
        transaction_id = str(uuid4())
        cursor.execute("""
            INSERT INTO transactions (
                transaction_id, user_id, transaction_type,
                amount, balance_before, balance_after, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            transaction_id,
            user_id,
            "deposit",
            500.0,
            0.0,
            500.0,
            "completed"
        ))

        # Update user balance
        cursor.execute("""
            UPDATE users SET balance = %s WHERE user_id = %s
        """, (500.0, user_id))

        db_connection.commit()

        # Step 2: User pays for agent service
        payment_id = str(uuid4())
        cursor.execute("""
            INSERT INTO transactions (
                transaction_id, user_id, transaction_type,
                amount, balance_before, balance_after, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            payment_id,
            user_id,
            "payment",
            200.0,
            500.0,
            300.0,
            "completed"
        ))

        # Update user balance
        cursor.execute("""
            UPDATE users SET balance = %s WHERE user_id = %s
        """, (300.0, user_id))

        db_connection.commit()

        # Verify final balance
        cursor.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
        balance = cursor.fetchone()[0]
        assert balance == 300.0

        cursor.close()


class TestCachingBehavior:
    """Test Redis caching behavior"""

    def test_agent_cache(self, redis_client):
        """Test caching of agent data"""

        agent_id = str(uuid4())
        agent_data = {
            "name": "TestAgent",
            "capabilities": ["python_coding"],
            "rating": 4.8
        }

        # Store in cache
        redis_client.setex(
            f"agent:{agent_id}",
            3600,  # 1 hour TTL
            str(agent_data)
        )

        # Retrieve from cache
        cached_data = redis_client.get(f"agent:{agent_id}")
        assert cached_data is not None

        # Test expiration
        ttl = redis_client.ttl(f"agent:{agent_id}")
        assert ttl > 0 and ttl <= 3600


class TestMessageQueue:
    """Test RabbitMQ message queue operations"""

    def test_task_queue(self, rabbitmq_connection):
        """Test publishing and consuming task messages"""

        channel = rabbitmq_connection.channel()
        queue_name = "test_tasks"

        # Declare queue
        channel.queue_declare(queue=queue_name, durable=True)

        # Publish message
        task_message = {
            "task_id": str(uuid4()),
            "action": "process_task",
            "data": {"priority": "high"}
        }

        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=str(task_message)
        )

        # Consume message
        method_frame, header_frame, body = channel.basic_get(queue=queue_name)
        assert body is not None
        assert "task_id" in str(body)

        # Acknowledge message
        if method_frame:
            channel.basic_ack(method_frame.delivery_tag)

        channel.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
