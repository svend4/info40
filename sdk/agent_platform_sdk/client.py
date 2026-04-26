"""
Platform Client for Agent Platform SDK
"""

import aiohttp
from typing import Optional, List, Dict, Any
from .models import Agent, Task, Contract, Review
from .exceptions import PlatformException, RateLimitException


class BaseClient:
    """Base client with common HTTP methods"""

    def __init__(self, base_url: str, api_key: Optional[str] = None, session: Optional[aiohttp.ClientSession] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self._session = session
        self._owned_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._owned_session and self._session:
            await self._session.close()

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        session = await self._get_session()
        url = f"{self.base_url}{path}"
        headers = self._get_headers()

        try:
            async with session.request(method, url, headers=headers, **kwargs) as response:
                if response.status == 429:
                    raise RateLimitException("Rate limit exceeded")
                elif response.status >= 400:
                    raise PlatformException(f"API error: {response.status}")

                return await response.json()
        except aiohttp.ClientError as e:
            raise PlatformException(f"Connection error: {e}")


class AgentsClient(BaseClient):
    """Client for agent operations"""

    async def list(self, page: int = 1, page_size: int = 20, **filters) -> List[Agent]:
        """List all agents"""
        params = {"page": page, "page_size": page_size, **filters}
        data = await self._request("GET", "/registry/agents", params=params)
        return [Agent(**agent) for agent in data.get("agents", [])]

    async def get(self, agent_id: str) -> Agent:
        """Get agent by ID"""
        data = await self._request("GET", f"/registry/agents/{agent_id}")
        return Agent(**data)

    async def register(self, name: str, capabilities: List[str], hourly_rate: float, **kwargs) -> Agent:
        """Register new agent"""
        payload = {
            "name": name,
            "capabilities": capabilities,
            "hourly_rate": hourly_rate,
            "pricing_mode": kwargs.get("pricing_mode", "commercial"),
            "description": kwargs.get("description", ""),
            "volunteer_percentage": kwargs.get("volunteer_percentage", 0),
            "max_concurrent_tasks": kwargs.get("max_concurrent_tasks", 5),
            "supported_languages": kwargs.get("supported_languages", ["en"]),
            "metadata": kwargs.get("metadata", {})
        }
        data = await self._request("POST", "/registry/agents", json=payload)
        return Agent(**data)


class TasksClient(BaseClient):
    """Client for task operations"""

    async def list(self, customer_id: Optional[str] = None, **filters) -> List[Task]:
        """List tasks"""
        params = {k: v for k, v in {"customer_id": customer_id, **filters}.items() if v is not None}
        data = await self._request("GET", "/orchestrator/tasks", params=params)
        return [Task(**task) for task in data]

    async def get(self, task_id: str) -> Task:
        """Get task by ID"""
        data = await self._request("GET", f"/orchestrator/tasks/{task_id}")
        return Task(**data)

    async def create(
        self,
        title: str,
        description: str,
        capabilities: List[str],
        budget: float,
        customer_id: str = "sdk-user",
        **kwargs
    ) -> Task:
        """Create new task"""
        payload = {
            "customer_id": customer_id,
            "title": title,
            "description": description,
            "required_capabilities": capabilities,
            "budget": budget,
            "priority": kwargs.get("priority", "medium"),
            "rental_mode": kwargs.get("rental_mode", "commercial"),
            "metadata": kwargs.get("metadata", {})
        }

        if "deadline" in kwargs:
            payload["deadline"] = kwargs["deadline"]

        data = await self._request("POST", "/orchestrator/tasks", json=payload)
        return Task(**data)


class MarketplaceClient(BaseClient):
    """Client for marketplace operations"""

    async def search(self, **filters) -> List[Agent]:
        """Search for agents"""
        payload = {
            "page": filters.get("page", 1),
            "page_size": filters.get("page_size", 20),
            "sort_by": filters.get("sort_by", "rating"),
            "sort_order": filters.get("sort_order", "desc"),
            "available_only": filters.get("available_only", True)
        }

        if "capability" in filters:
            payload["capabilities"] = [filters["capability"]]
        if "max_rate" in filters:
            payload["max_hourly_rate"] = filters["max_rate"]
        if "min_rating" in filters:
            payload["min_rating"] = filters["min_rating"]

        data = await self._request("POST", "/marketplace/agents/search", json=payload)
        return [Agent(**agent) for agent in data.get("agents", [])]

    async def create_contract(
        self,
        agent_id: str,
        customer_id: str,
        billing_model: str = "hourly",
        **kwargs
    ) -> Contract:
        """Create rental contract"""
        payload = {
            "agent_id": agent_id,
            "customer_id": customer_id,
            "rental_mode": kwargs.get("rental_mode", "commercial"),
            "billing_model": billing_model,
            "hourly_rate": kwargs.get("hourly_rate"),
            "fixed_price": kwargs.get("fixed_price"),
            "estimated_hours": kwargs.get("estimated_hours"),
            "terms": kwargs.get("terms")
        }
        data = await self._request("POST", "/marketplace/contracts", json=payload)
        return Contract(**data)

    async def submit_review(
        self,
        agent_id: str,
        user_id: str,
        rating: float,
        comment: str,
        **scores
    ) -> Review:
        """Submit agent review"""
        payload = {
            "agent_id": agent_id,
            "user_id": user_id,
            "rating": rating,
            "quality_score": scores.get("quality", rating),
            "speed_score": scores.get("speed", rating),
            "communication_score": scores.get("communication", rating),
            "comment": comment,
            "would_recommend": scores.get("would_recommend", True)
        }
        data = await self._request("POST", "/marketplace/reviews", json=payload)
        return Review(**data)


class PlatformClient:
    """Main client for AI Agent Orchestration Platform"""

    def __init__(self, api_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize Platform Client

        Args:
            api_url: Platform API base URL
            api_key: Optional API key for authentication
        """
        self.api_url = api_url
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

        # Initialize service clients
        self.agents = AgentsClient(api_url, api_key)
        self.tasks = TasksClient(api_url, api_key)
        self.marketplace = MarketplaceClient(api_url, api_key)

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        self.agents._session = self._session
        self.tasks._session = self._session
        self.marketplace._session = self._session
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def close(self):
        """Close HTTP session"""
        await self.agents.close()
        await self.tasks.close()
        await self.marketplace.close()

    async def health_check(self) -> Dict[str, Any]:
        """Check platform health"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/health") as response:
                return await response.json()
