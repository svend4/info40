"""
Agent Worker Implementation

Base class for AI agents that execute tasks on the platform.

Usage:
    class MyAgent(AgentWorker):
        async def execute_task(self, task):
            # Implement your task execution logic
            return result

    agent = MyAgent(
        agent_id="agent-123",
        api_url="http://localhost:8000"
    )
    await agent.run()
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json
from abc import ABC, abstractmethod
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time


# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Metrics
# ============================================================================

tasks_received = Counter(
    'agent_tasks_received_total',
    'Total tasks received by agent',
    ['agent_id']
)

tasks_completed = Counter(
    'agent_tasks_completed_total',
    'Total tasks completed by agent',
    ['agent_id', 'status']
)

task_duration = Histogram(
    'agent_task_duration_seconds',
    'Task execution duration',
    ['agent_id', 'task_type']
)

active_tasks = Gauge(
    'agent_active_tasks',
    'Number of currently executing tasks',
    ['agent_id']
)

agent_errors = Counter(
    'agent_errors_total',
    'Total errors encountered',
    ['agent_id', 'error_type']
)


# ============================================================================
# Agent Worker Base Class
# ============================================================================

class AgentWorker(ABC):
    """
    Base class for AI agent workers

    Handles:
    - Connection to platform
    - Task polling
    - Task execution
    - Progress reporting
    - Error handling
    """

    def __init__(
        self,
        agent_id: str,
        api_url: str,
        api_key: Optional[str] = None,
        poll_interval: int = 5,
        max_concurrent_tasks: int = 3,
        metrics_port: int = 9090
    ):
        """
        Initialize agent worker

        Args:
            agent_id: Unique agent identifier
            api_url: Platform API base URL
            api_key: Optional API key for authentication
            poll_interval: Seconds between task polls
            max_concurrent_tasks: Maximum concurrent tasks
            metrics_port: Port for Prometheus metrics
        """
        self.agent_id = agent_id
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.poll_interval = poll_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        self.metrics_port = metrics_port

        self.running = False
        self.session: Optional[aiohttp.ClientSession] = None
        self.current_tasks: Dict[str, asyncio.Task] = {}

        logger.info(f"Agent {agent_id} initialized")

    async def start(self):
        """Start the agent worker"""
        logger.info(f"Starting agent {self.agent_id}...")

        # Start metrics server
        try:
            start_http_server(self.metrics_port)
            logger.info(f"Metrics server started on port {self.metrics_port}")
        except Exception as e:
            logger.warning(f"Could not start metrics server: {e}")

        # Create HTTP session
        self.session = aiohttp.ClientSession(
            headers=self._get_headers(),
            timeout=aiohttp.ClientTimeout(total=30)
        )

        # Register agent with platform
        await self._register_agent()

        # Start task polling loop
        self.running = True
        await self._task_loop()

    async def stop(self):
        """Stop the agent worker"""
        logger.info(f"Stopping agent {self.agent_id}...")
        self.running = False

        # Wait for current tasks to complete
        if self.current_tasks:
            logger.info(f"Waiting for {len(self.current_tasks)} tasks to complete...")
            await asyncio.gather(*self.current_tasks.values(), return_exceptions=True)

        # Close HTTP session
        if self.session:
            await self.session.close()

        logger.info(f"Agent {self.agent_id} stopped")

    async def run(self):
        """Run the agent (blocking)"""
        try:
            await self.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Agent crashed: {e}", exc_info=True)
        finally:
            await self.stop()

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"AgentWorker/{self.agent_id}"
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    async def _register_agent(self):
        """Register agent with platform"""
        try:
            # Get agent info from platform
            url = f"{self.api_url}/registry/agents/{self.agent_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    logger.info(f"Agent {self.agent_id} already registered")
                    return

            # Agent not found, would need to register
            logger.warning(f"Agent {self.agent_id} not found in registry")

        except Exception as e:
            logger.error(f"Failed to register agent: {e}")

    async def _task_loop(self):
        """Main task polling loop"""
        logger.info("Starting task polling loop...")

        while self.running:
            try:
                # Check if we can accept more tasks
                if len(self.current_tasks) >= self.max_concurrent_tasks:
                    logger.debug(f"At capacity ({len(self.current_tasks)} tasks), waiting...")
                    await asyncio.sleep(self.poll_interval)
                    continue

                # Poll for new tasks
                task = await self._poll_for_task()

                if task:
                    # Start task execution in background
                    task_id = task['subtask_id']
                    task_coro = self._execute_task_wrapper(task)
                    self.current_tasks[task_id] = asyncio.create_task(task_coro)

                    # Track metrics
                    tasks_received.labels(agent_id=self.agent_id).inc()
                    active_tasks.labels(agent_id=self.agent_id).set(len(self.current_tasks))

                else:
                    # No tasks available, wait
                    await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"Error in task loop: {e}", exc_info=True)
                agent_errors.labels(
                    agent_id=self.agent_id,
                    error_type="task_loop"
                ).inc()
                await asyncio.sleep(self.poll_interval)

    async def _poll_for_task(self) -> Optional[Dict[str, Any]]:
        """
        Poll platform for available tasks

        In production, this would:
        - Query orchestrator for tasks assigned to this agent
        - Use WebSocket/SSE for real-time task notifications
        - Pull from message queue (RabbitMQ)

        For now, returns None (no tasks)
        """
        try:
            # This is a placeholder - in production would query orchestrator
            # url = f"{self.api_url}/orchestrator/agents/{self.agent_id}/tasks/next"
            # async with self.session.get(url) as response:
            #     if response.status == 200:
            #         return await response.json()

            return None  # No tasks available

        except Exception as e:
            logger.error(f"Error polling for tasks: {e}")
            return None

    async def _execute_task_wrapper(self, task: Dict[str, Any]):
        """
        Wrapper for task execution with error handling and reporting
        """
        task_id = task['subtask_id']
        task_type = task.get('task_type', 'unknown')

        logger.info(f"Starting task {task_id}")

        start_time = time.time()

        try:
            # Update task status to running
            await self._update_task_status(task_id, "running", 0)

            # Execute the task (implemented by subclass)
            result = await self.execute_task(task)

            # Calculate duration
            duration = time.time() - start_time

            # Update task status to completed
            await self._update_task_status(task_id, "completed", 100, result)

            # Track metrics
            tasks_completed.labels(
                agent_id=self.agent_id,
                status="success"
            ).inc()
            task_duration.labels(
                agent_id=self.agent_id,
                task_type=task_type
            ).observe(duration)

            logger.info(f"Task {task_id} completed in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)

            # Update task status to failed
            await self._update_task_status(
                task_id,
                "failed",
                0,
                error=str(e)
            )

            # Track metrics
            tasks_completed.labels(
                agent_id=self.agent_id,
                status="failure"
            ).inc()
            agent_errors.labels(
                agent_id=self.agent_id,
                error_type="task_execution"
            ).inc()

        finally:
            # Remove from current tasks
            if task_id in self.current_tasks:
                del self.current_tasks[task_id]

            active_tasks.labels(agent_id=self.agent_id).set(len(self.current_tasks))

    async def _update_task_status(
        self,
        task_id: str,
        status: str,
        progress: float,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ):
        """Update task status on platform"""
        try:
            url = f"{self.api_url}/orchestrator/subtasks/{task_id}/status"

            payload = {
                "status": status,
                "progress": progress
            }

            if result is not None:
                payload["result"] = result

            if error is not None:
                payload["error"] = error

            async with self.session.patch(url, json=payload) as response:
                if response.status not in [200, 201]:
                    logger.warning(
                        f"Failed to update task status: {response.status}"
                    )

        except Exception as e:
            logger.error(f"Error updating task status: {e}")

    async def report_progress(self, task_id: str, progress: float, message: Optional[str] = None):
        """
        Report task progress

        Args:
            task_id: Task identifier
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        logger.info(f"Task {task_id} progress: {progress}%")

        await self._update_task_status(task_id, "running", progress)

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Any:
        """
        Execute a task (must be implemented by subclass)

        Args:
            task: Task data including:
                - subtask_id: Unique task ID
                - title: Task title
                - description: Task description
                - required_capabilities: List of required capabilities
                - input_data: Input data for task

        Returns:
            Task result (any JSON-serializable data)

        Raises:
            Exception: If task execution fails
        """
        raise NotImplementedError("Subclasses must implement execute_task()")


# ============================================================================
# Example Agent Implementations
# ============================================================================

class PythonCodingAgent(AgentWorker):
    """Example: Python coding agent"""

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python coding task"""
        logger.info(f"Executing Python coding task: {task['title']}")

        # Simulate work
        await asyncio.sleep(5)

        # Report progress
        await self.report_progress(task['subtask_id'], 50, "Code written")

        await asyncio.sleep(5)

        await self.report_progress(task['subtask_id'], 90, "Tests passing")

        await asyncio.sleep(2)

        # Return result
        return {
            "code": "def hello(): return 'Hello, World!'",
            "tests_passed": True,
            "coverage": 100,
            "complexity": "low"
        }


class DataAnalysisAgent(AgentWorker):
    """Example: Data analysis agent"""

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data analysis task"""
        logger.info(f"Executing data analysis task: {task['title']}")

        # Simulate data loading
        await self.report_progress(task['subtask_id'], 20, "Loading data")
        await asyncio.sleep(3)

        # Simulate analysis
        await self.report_progress(task['subtask_id'], 50, "Analyzing")
        await asyncio.sleep(7)

        # Simulate visualization
        await self.report_progress(task['subtask_id'], 80, "Creating visualizations")
        await asyncio.sleep(3)

        # Return results
        return {
            "rows_analyzed": 10000,
            "insights": [
                "Strong correlation between X and Y",
                "Outliers detected in column Z"
            ],
            "visualizations": ["chart1.png", "chart2.png"],
            "recommendations": "Further investigation needed"
        }


# ============================================================================
# Main
# ============================================================================

async def main():
    """Example usage"""
    import sys

    agent_type = sys.argv[1] if len(sys.argv) > 1 else "python"

    if agent_type == "python":
        agent = PythonCodingAgent(
            agent_id="python-agent-001",
            api_url="http://localhost:8000"
        )
    elif agent_type == "data":
        agent = DataAnalysisAgent(
            agent_id="data-agent-001",
            api_url="http://localhost:8000"
        )
    else:
        print(f"Unknown agent type: {agent_type}")
        return

    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
