"""
Data models for Agent Platform SDK
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Agent:
    """Agent model"""
    agent_id: str
    name: str
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    pricing_mode: str = "commercial"
    hourly_rate: float = 0.0
    rating: float = 0.0
    reviews_count: int = 0
    total_tasks_completed: int = 0
    status: str = "active"
    owner_id: str = ""
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Task model"""
    task_id: str
    customer_id: str
    title: str
    description: str
    required_capabilities: List[str]
    budget: float
    actual_cost: float = 0.0
    status: str = "pending"
    progress: float = 0.0
    subtask_count: int = 0
    assigned_agents: List[str] = field(default_factory=list)
    priority: str = "medium"
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deadline: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Contract:
    """Rental contract model"""
    contract_id: str
    agent_id: str
    customer_id: str
    rental_mode: str
    billing_model: str
    status: str
    hourly_rate: Optional[float] = None
    fixed_price: Optional[float] = None
    total_cost: float = 0.0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Review:
    """Review model"""
    review_id: str
    agent_id: str
    user_id: str
    username: str
    rating: float
    quality_score: float
    speed_score: float
    communication_score: float
    comment: str
    would_recommend: bool = True
    helpful_count: int = 0
    created_at: Optional[str] = None
    contract_id: Optional[str] = None
    task_id: Optional[str] = None
    value_for_money_score: Optional[float] = None


@dataclass
class AgentSearchParams:
    """Parameters for agent search"""
    capabilities: Optional[List[str]] = None
    pricing_mode: Optional[List[str]] = None
    min_rating: Optional[float] = None
    max_hourly_rate: Optional[float] = None
    min_tasks_completed: Optional[int] = None
    available_only: bool = True
    sort_by: str = "rating"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 20


@dataclass
class TaskCreateParams:
    """Parameters for task creation"""
    title: str
    description: str
    required_capabilities: List[str]
    budget: float
    customer_id: str = "sdk-user"
    priority: str = "medium"
    rental_mode: str = "commercial"
    deadline: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
