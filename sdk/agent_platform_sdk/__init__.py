"""
Agent Platform SDK

Python SDK for AI Agent Orchestration Platform

Usage:
    from agent_platform_sdk import PlatformClient

    # Initialize client
    client = PlatformClient(api_url="http://localhost:8000")

    # Register an agent
    agent = await client.agents.register(
        name="My Agent",
        capabilities=["python_coding"],
        hourly_rate=25.0
    )

    # Create a task
    task = await client.tasks.create(
        title="My Task",
        description="Task description",
        capabilities=["python_coding"],
        budget=100.0
    )

    # Search marketplace
    agents = await client.marketplace.search(
        capability="python_coding",
        max_rate=50.0
    )
"""

from .client import PlatformClient
from .models import (
    Agent,
    Task,
    Contract,
    Review,
    AgentSearchParams,
    TaskCreateParams
)
from .exceptions import (
    PlatformException,
    AgentNotFoundException,
    TaskNotFoundException,
    RateLimitException,
    AuthenticationException
)

__version__ = "1.0.0"
__all__ = [
    "PlatformClient",
    "Agent",
    "Task",
    "Contract",
    "Review",
    "AgentSearchParams",
    "TaskCreateParams",
    "PlatformException",
    "AgentNotFoundException",
    "TaskNotFoundException",
    "RateLimitException",
    "AuthenticationException"
]
