"""
Marketplace Service API

Handles agent discovery, rental contracts, and reviews.
"""

from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
from prometheus_client import Counter, Histogram, make_asgi_app
import time


# ============================================================================
# Configuration
# ============================================================================

app = FastAPI(
    title="Marketplace Service",
    description="Agent marketplace for discovery, rental, and reviews",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Metrics
search_requests = Counter(
    'marketplace_search_requests_total',
    'Total agent search requests',
    ['filters_used']
)
contract_creations = Counter(
    'marketplace_contracts_created_total',
    'Total rental contracts created',
    ['rental_mode']
)
review_submissions = Counter(
    'marketplace_reviews_submitted_total',
    'Total reviews submitted',
    ['rating_category']
)
search_duration = Histogram(
    'marketplace_search_duration_seconds',
    'Agent search duration'
)


# ============================================================================
# Models
# ============================================================================

class RentalMode(str, Enum):
    COMMERCIAL = "commercial"
    VOLUNTEER = "volunteer"
    HYBRID = "hybrid"
    TRIAL = "trial"


class BillingModel(str, Enum):
    HOURLY = "hourly"
    PER_TASK = "per_task"
    SUBSCRIPTION = "subscription"
    OUTCOME_BASED = "outcome_based"


class ContractStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class AgentSearchRequest(BaseModel):
    """Agent search parameters"""
    capabilities: Optional[List[str]] = None
    pricing_mode: Optional[List[str]] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    max_hourly_rate: Optional[float] = Field(None, gt=0)
    min_tasks_completed: Optional[int] = Field(None, ge=0)
    available_only: bool = True
    sort_by: str = Field("rating", regex="^(rating|price|tasks|reviews)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class AgentSearchResult(BaseModel):
    """Single agent in search results"""
    agent_id: str
    name: str
    description: str
    capabilities: List[str]
    pricing_mode: str
    hourly_rate: float
    rating: float
    reviews_count: int
    total_tasks_completed: int
    success_rate: float
    availability: str
    owner_id: str
    created_at: datetime


class AgentSearchResponse(BaseModel):
    """Search results with pagination"""
    agents: List[AgentSearchResult]
    total: int
    page: int
    page_size: int
    total_pages: int


class RentalContractCreate(BaseModel):
    """Create rental contract"""
    agent_id: str
    customer_id: str
    task_id: Optional[str] = None
    rental_mode: RentalMode
    billing_model: BillingModel
    hourly_rate: Optional[float] = Field(None, gt=0)
    fixed_price: Optional[float] = Field(None, gt=0)
    estimated_hours: Optional[float] = Field(None, gt=0)
    expected_outcome: Optional[str] = None
    terms: Optional[str] = None

    @validator('hourly_rate')
    def validate_hourly_rate(cls, v, values):
        if values.get('billing_model') == BillingModel.HOURLY and not v:
            raise ValueError("hourly_rate required for hourly billing")
        return v

    @validator('fixed_price')
    def validate_fixed_price(cls, v, values):
        if values.get('billing_model') == BillingModel.PER_TASK and not v:
            raise ValueError("fixed_price required for per-task billing")
        return v


class RentalContractResponse(BaseModel):
    """Rental contract response"""
    contract_id: str
    agent_id: str
    customer_id: str
    task_id: Optional[str]
    rental_mode: str
    billing_model: str
    hourly_rate: Optional[float]
    fixed_price: Optional[float]
    estimated_hours: Optional[float]
    status: str
    total_cost: float
    start_time: datetime
    end_time: Optional[datetime]
    created_at: datetime


class ReviewCreate(BaseModel):
    """Create review for agent"""
    agent_id: str
    user_id: str
    contract_id: Optional[str] = None
    task_id: Optional[str] = None
    rating: float = Field(..., ge=1, le=5)
    quality_score: float = Field(..., ge=1, le=5)
    speed_score: float = Field(..., ge=1, le=5)
    communication_score: float = Field(..., ge=1, le=5)
    value_for_money_score: Optional[float] = Field(None, ge=1, le=5)
    comment: str = Field(..., min_length=10, max_length=2000)
    would_recommend: bool = True


class ReviewResponse(BaseModel):
    """Review response"""
    review_id: str
    agent_id: str
    user_id: str
    username: str
    contract_id: Optional[str]
    task_id: Optional[str]
    rating: float
    quality_score: float
    speed_score: float
    communication_score: float
    value_for_money_score: Optional[float]
    comment: str
    would_recommend: bool
    helpful_count: int
    created_at: datetime


class MarketplaceStats(BaseModel):
    """Marketplace statistics"""
    total_agents: int
    active_agents: int
    total_contracts: int
    active_contracts: int
    total_reviews: int
    average_rating: float
    total_revenue: float
    top_categories: List[Dict[str, Any]]


# ============================================================================
# In-Memory Storage (Replace with Database)
# ============================================================================

# Mock data stores
agents_db: Dict[str, Dict] = {}
contracts_db: Dict[str, Dict] = {}
reviews_db: Dict[str, Dict] = {}


# ============================================================================
# Helper Functions
# ============================================================================

def filter_agents(search_params: AgentSearchRequest) -> List[Dict]:
    """Filter agents based on search criteria"""
    filtered = list(agents_db.values())

    if search_params.capabilities:
        filtered = [
            a for a in filtered
            if any(cap in a['capabilities'] for cap in search_params.capabilities)
        ]

    if search_params.pricing_mode:
        filtered = [
            a for a in filtered
            if a['pricing_mode'] in search_params.pricing_mode
        ]

    if search_params.min_rating is not None:
        filtered = [a for a in filtered if a['rating'] >= search_params.min_rating]

    if search_params.max_hourly_rate is not None:
        filtered = [
            a for a in filtered
            if a['hourly_rate'] <= search_params.max_hourly_rate
        ]

    if search_params.min_tasks_completed is not None:
        filtered = [
            a for a in filtered
            if a['total_tasks_completed'] >= search_params.min_tasks_completed
        ]

    if search_params.available_only:
        filtered = [a for a in filtered if a['status'] == 'active']

    return filtered


def sort_agents(agents: List[Dict], sort_by: str, sort_order: str) -> List[Dict]:
    """Sort agents by criteria"""
    sort_key_map = {
        'rating': 'rating',
        'price': 'hourly_rate',
        'tasks': 'total_tasks_completed',
        'reviews': 'reviews_count'
    }

    key = sort_key_map.get(sort_by, 'rating')
    reverse = (sort_order == 'desc')

    return sorted(agents, key=lambda x: x.get(key, 0), reverse=reverse)


def paginate(items: List[Any], page: int, page_size: int) -> List[Any]:
    """Paginate results"""
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "marketplace-service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/agents/search", response_model=AgentSearchResponse)
async def search_agents(search: AgentSearchRequest):
    """
    Search for agents with filtering and pagination

    Supports filtering by:
    - Capabilities
    - Pricing mode
    - Minimum rating
    - Maximum hourly rate
    - Minimum tasks completed
    - Availability
    """
    start_time = time.time()

    # Track which filters are used
    filters_used = []
    if search.capabilities:
        filters_used.append('capabilities')
    if search.pricing_mode:
        filters_used.append('pricing_mode')
    if search.min_rating is not None:
        filters_used.append('rating')
    if search.max_hourly_rate is not None:
        filters_used.append('price')

    search_requests.labels(filters_used=','.join(filters_used) or 'none').inc()

    # Filter agents
    filtered_agents = filter_agents(search)

    # Sort agents
    sorted_agents = sort_agents(filtered_agents, search.sort_by, search.sort_order)

    # Calculate pagination
    total = len(sorted_agents)
    total_pages = (total + search.page_size - 1) // search.page_size

    # Paginate
    paginated_agents = paginate(sorted_agents, search.page, search.page_size)

    # Convert to response models
    results = [
        AgentSearchResult(
            agent_id=agent['agent_id'],
            name=agent['name'],
            description=agent['description'],
            capabilities=agent['capabilities'],
            pricing_mode=agent['pricing_mode'],
            hourly_rate=agent['hourly_rate'],
            rating=agent['rating'],
            reviews_count=agent['reviews_count'],
            total_tasks_completed=agent['total_tasks_completed'],
            success_rate=agent.get('success_rate', 0.95),
            availability=agent['status'],
            owner_id=agent['owner_id'],
            created_at=agent['created_at']
        )
        for agent in paginated_agents
    ]

    duration = time.time() - start_time
    search_duration.observe(duration)

    return AgentSearchResponse(
        agents=results,
        total=total,
        page=search.page,
        page_size=search.page_size,
        total_pages=total_pages
    )


@app.post("/contracts", response_model=RentalContractResponse, status_code=status.HTTP_201_CREATED)
async def create_rental_contract(contract: RentalContractCreate):
    """
    Create a rental contract for an agent

    Supports multiple billing models:
    - Hourly: Pay by the hour
    - Per Task: Fixed price per task
    - Subscription: Monthly subscription
    - Outcome Based: Pay based on results
    """
    # Validate agent exists
    if contract.agent_id not in agents_db:
        raise HTTPException(
            status_code=404,
            detail=f"Agent {contract.agent_id} not found"
        )

    agent = agents_db[contract.agent_id]

    # Validate agent is available
    if agent['status'] != 'active':
        raise HTTPException(
            status_code=400,
            detail=f"Agent {contract.agent_id} is not available"
        )

    # Validate rental mode compatibility
    if contract.rental_mode == RentalMode.VOLUNTEER and agent['pricing_mode'] == 'commercial':
        raise HTTPException(
            status_code=400,
            detail="Agent does not support volunteer mode"
        )

    # Create contract
    contract_id = f"contract-{uuid.uuid4()}"
    now = datetime.now()

    contract_data = {
        "contract_id": contract_id,
        "agent_id": contract.agent_id,
        "customer_id": contract.customer_id,
        "task_id": contract.task_id,
        "rental_mode": contract.rental_mode.value,
        "billing_model": contract.billing_model.value,
        "hourly_rate": contract.hourly_rate or agent['hourly_rate'],
        "fixed_price": contract.fixed_price,
        "estimated_hours": contract.estimated_hours,
        "expected_outcome": contract.expected_outcome,
        "terms": contract.terms,
        "status": ContractStatus.ACTIVE.value,
        "total_cost": 0.0,
        "start_time": now,
        "end_time": None,
        "created_at": now
    }

    contracts_db[contract_id] = contract_data

    # Track metric
    contract_creations.labels(rental_mode=contract.rental_mode.value).inc()

    return RentalContractResponse(**contract_data)


@app.get("/contracts/{contract_id}", response_model=RentalContractResponse)
async def get_contract(contract_id: str):
    """Get rental contract details"""
    if contract_id not in contracts_db:
        raise HTTPException(status_code=404, detail="Contract not found")

    return RentalContractResponse(**contracts_db[contract_id])


@app.patch("/contracts/{contract_id}/complete")
async def complete_contract(
    contract_id: str,
    total_cost: float = Query(..., gt=0)
):
    """Mark contract as completed"""
    if contract_id not in contracts_db:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = contracts_db[contract_id]

    if contract['status'] != ContractStatus.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail="Only active contracts can be completed"
        )

    contract['status'] = ContractStatus.COMPLETED.value
    contract['end_time'] = datetime.now()
    contract['total_cost'] = total_cost

    return {"message": "Contract completed successfully", "contract": contract}


@app.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(review: ReviewCreate):
    """
    Submit a review for an agent

    Reviews help build trust in the marketplace and improve agent quality.
    """
    # Validate agent exists
    if review.agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Validate contract if provided
    if review.contract_id and review.contract_id not in contracts_db:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Check for duplicate review
    existing_reviews = [
        r for r in reviews_db.values()
        if r['user_id'] == review.user_id
        and r['agent_id'] == review.agent_id
        and r.get('contract_id') == review.contract_id
    ]

    if existing_reviews:
        raise HTTPException(
            status_code=400,
            detail="You have already reviewed this agent for this contract"
        )

    # Create review
    review_id = f"review-{uuid.uuid4()}"

    review_data = {
        "review_id": review_id,
        "agent_id": review.agent_id,
        "user_id": review.user_id,
        "username": f"user-{review.user_id[:8]}",  # Mock username
        "contract_id": review.contract_id,
        "task_id": review.task_id,
        "rating": review.rating,
        "quality_score": review.quality_score,
        "speed_score": review.speed_score,
        "communication_score": review.communication_score,
        "value_for_money_score": review.value_for_money_score,
        "comment": review.comment,
        "would_recommend": review.would_recommend,
        "helpful_count": 0,
        "created_at": datetime.now()
    }

    reviews_db[review_id] = review_data

    # Update agent rating (simplified - should be more sophisticated)
    agent = agents_db[review.agent_id]
    agent['reviews_count'] += 1
    total_rating = agent['rating'] * (agent['reviews_count'] - 1) + review.rating
    agent['rating'] = round(total_rating / agent['reviews_count'], 2)

    # Track metric
    rating_category = 'high' if review.rating >= 4 else 'medium' if review.rating >= 3 else 'low'
    review_submissions.labels(rating_category=rating_category).inc()

    return ReviewResponse(**review_data)


@app.get("/reviews", response_model=List[ReviewResponse])
async def get_reviews(
    agent_id: Optional[str] = None,
    user_id: Optional[str] = None,
    min_rating: Optional[float] = Query(None, ge=1, le=5),
    limit: int = Query(20, ge=1, le=100)
):
    """Get reviews with optional filtering"""
    filtered_reviews = list(reviews_db.values())

    if agent_id:
        filtered_reviews = [r for r in filtered_reviews if r['agent_id'] == agent_id]

    if user_id:
        filtered_reviews = [r for r in filtered_reviews if r['user_id'] == user_id]

    if min_rating is not None:
        filtered_reviews = [r for r in filtered_reviews if r['rating'] >= min_rating]

    # Sort by created_at descending
    filtered_reviews.sort(key=lambda x: x['created_at'], reverse=True)

    # Limit results
    filtered_reviews = filtered_reviews[:limit]

    return [ReviewResponse(**review) for review in filtered_reviews]


@app.get("/statistics", response_model=MarketplaceStats)
async def get_marketplace_statistics():
    """Get marketplace-wide statistics"""
    total_agents = len(agents_db)
    active_agents = sum(1 for a in agents_db.values() if a['status'] == 'active')

    total_contracts = len(contracts_db)
    active_contracts = sum(
        1 for c in contracts_db.values()
        if c['status'] == ContractStatus.ACTIVE.value
    )

    total_reviews = len(reviews_db)
    average_rating = (
        sum(r['rating'] for r in reviews_db.values()) / total_reviews
        if total_reviews > 0 else 0.0
    )

    total_revenue = sum(
        c['total_cost'] for c in contracts_db.values()
        if c['status'] == ContractStatus.COMPLETED.value
    )

    # Top categories (mock data)
    top_categories = [
        {"category": "Python Development", "agent_count": 15},
        {"category": "Data Analysis", "agent_count": 12},
        {"category": "Content Writing", "agent_count": 10},
        {"category": "Research", "agent_count": 8},
        {"category": "Design", "agent_count": 6}
    ]

    return MarketplaceStats(
        total_agents=total_agents,
        active_agents=active_agents,
        total_contracts=total_contracts,
        active_contracts=active_contracts,
        total_reviews=total_reviews,
        average_rating=round(average_rating, 2),
        total_revenue=round(total_revenue, 2),
        top_categories=top_categories
    )


@app.get("/agents/{agent_id}/marketplace-profile")
async def get_agent_marketplace_profile(agent_id: str):
    """Get detailed marketplace profile for an agent"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = agents_db[agent_id]

    # Get agent reviews
    agent_reviews = [r for r in reviews_db.values() if r['agent_id'] == agent_id]

    # Calculate detailed statistics
    total_reviews = len(agent_reviews)
    avg_quality = (
        sum(r['quality_score'] for r in agent_reviews) / total_reviews
        if total_reviews > 0 else 0
    )
    avg_speed = (
        sum(r['speed_score'] for r in agent_reviews) / total_reviews
        if total_reviews > 0 else 0
    )
    avg_communication = (
        sum(r['communication_score'] for r in agent_reviews) / total_reviews
        if total_reviews > 0 else 0
    )

    # Get recent contracts
    agent_contracts = [
        c for c in contracts_db.values()
        if c['agent_id'] == agent_id
    ]
    completed_contracts = [
        c for c in agent_contracts
        if c['status'] == ContractStatus.COMPLETED.value
    ]

    return {
        "agent_id": agent_id,
        "name": agent['name'],
        "description": agent['description'],
        "capabilities": agent['capabilities'],
        "pricing_mode": agent['pricing_mode'],
        "hourly_rate": agent['hourly_rate'],
        "rating": agent['rating'],
        "statistics": {
            "total_reviews": total_reviews,
            "total_contracts": len(agent_contracts),
            "completed_contracts": len(completed_contracts),
            "total_tasks_completed": agent['total_tasks_completed'],
            "success_rate": agent.get('success_rate', 0.95),
            "avg_quality_score": round(avg_quality, 2),
            "avg_speed_score": round(avg_speed, 2),
            "avg_communication_score": round(avg_communication, 2),
        },
        "recent_reviews": sorted(
            agent_reviews,
            key=lambda x: x['created_at'],
            reverse=True
        )[:5]
    }


# ============================================================================
# Initialization
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    print("Marketplace Service starting up...")

    # Load mock data (in production, this would connect to database)
    # For now, we'll rely on Registry Service to populate agents

    print("Marketplace Service ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Marketplace Service shutting down...")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
