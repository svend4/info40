"""
Registry Service API
Сервис регистрации и управления AI-агентами

Endpoints:
- POST /agents - Регистрация нового агента
- GET /agents - Получение списка агентов
- GET /agents/{agent_id} - Получение информации об агенте
- PUT /agents/{agent_id} - Обновление информации об агенте
- DELETE /agents/{agent_id} - Удаление агента
- GET /agents/{agent_id}/health - Проверка здоровья агента
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Agent Registry Service",
    description="Сервис регистрации и управления AI-агентами",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Models
# ============================================================================

class AgentStatus(str, Enum):
    """Статус агента"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class PricingMode(str, Enum):
    """Модель ценообразования"""
    COMMERCIAL = "commercial"
    VOLUNTEER = "volunteer"
    HYBRID = "hybrid"


class BillingModel(str, Enum):
    """Модель биллинга"""
    HOURLY = "hourly"
    PER_TASK = "per_task"
    SUBSCRIPTION = "subscription"
    OUTCOME_BASED = "outcome_based"


class AgentAvailability(BaseModel):
    """Доступность агента"""
    schedule: str = Field(default="24/7", description="Расписание работы")
    max_concurrent_tasks: int = Field(default=1, ge=1, le=100)
    priority: str = Field(default="normal", pattern="^(low|normal|high|critical)$")


class AgentPricing(BaseModel):
    """Ценообразование агента"""
    mode: PricingMode
    hourly_rate: Optional[float] = Field(None, ge=0)
    task_rate: Optional[float] = Field(None, ge=0)
    subscription_monthly: Optional[float] = Field(None, ge=0)
    volunteer_quota: int = Field(default=0, ge=0, le=100, description="% времени на волонтерство")

    @validator('hourly_rate', 'task_rate', 'subscription_monthly')
    def validate_pricing(cls, v, values, field):
        mode = values.get('mode')
        if mode in [PricingMode.COMMERCIAL, PricingMode.HYBRID]:
            if field.name == 'hourly_rate' and v is None:
                raise ValueError("hourly_rate обязателен для коммерческих агентов")
        return v


class AgentMetrics(BaseModel):
    """Метрики производительности агента"""
    total_tasks_completed: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_response_time: int = Field(default=0, ge=0, description="Среднее время ответа в секундах")
    avg_quality_score: float = Field(default=0.0, ge=0.0, le=5.0)


class AgentRegistration(BaseModel):
    """Запрос на регистрацию агента"""
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., max_length=500)
    capabilities: List[str] = Field(..., min_items=1, max_items=20)
    model: str = Field(default="claude-sonnet-4.5")
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")

    availability: AgentAvailability = Field(default_factory=AgentAvailability)
    pricing: AgentPricing

    # Опциональные поля
    api_endpoint: Optional[str] = None
    webhook_url: Optional[str] = None
    authentication: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Ответ с информацией об агенте"""
    agent_id: str
    owner_id: str
    name: str
    description: str
    capabilities: List[str]
    model: str
    version: str

    status: AgentStatus
    availability: AgentAvailability
    pricing: AgentPricing
    metrics: AgentMetrics

    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    reviews_count: int = Field(default=0, ge=0)

    created_at: datetime
    updated_at: datetime
    last_seen: Optional[datetime] = None


class AgentListResponse(BaseModel):
    """Ответ со списком агентов"""
    total: int
    page: int
    page_size: int
    agents: List[AgentResponse]


class HealthResponse(BaseModel):
    """Ответ health check"""
    status: str
    agent_id: str
    current_load: int
    available_capacity: int
    last_task_completed: Optional[datetime]


# ============================================================================
# In-memory storage (для примера, в production используйте БД)
# ============================================================================

agents_db: Dict[str, AgentResponse] = {}


# ============================================================================
# Dependencies
# ============================================================================

def get_current_user() -> str:
    """Получить текущего пользователя (mock)"""
    # В production здесь будет проверка JWT токена
    return "user-123"


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "registry-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready", tags=["System"])
async def readiness_check():
    """Readiness check endpoint"""
    # Проверить подключение к БД, Redis и т.д.
    return {
        "status": "ready",
        "database": "connected",
        "cache": "connected"
    }


@app.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Agents"]
)
async def register_agent(
    agent: AgentRegistration,
    owner_id: str = Depends(get_current_user)
):
    """
    Регистрация нового агента в системе

    **Пример запроса:**
    ```json
    {
      "name": "PythonMaster",
      "description": "Эксперт в Python разработке",
      "capabilities": ["python_coding", "code_review"],
      "model": "claude-sonnet-4.5",
      "pricing": {
        "mode": "commercial",
        "hourly_rate": 30.0
      }
    }
    ```
    """
    logger.info(f"Регистрация агента: {agent.name} для пользователя {owner_id}")

    # Генерация ID
    agent_id = f"agent-{uuid.uuid4()}"

    # Создание объекта агента
    now = datetime.utcnow()
    agent_response = AgentResponse(
        agent_id=agent_id,
        owner_id=owner_id,
        name=agent.name,
        description=agent.description,
        capabilities=agent.capabilities,
        model=agent.model,
        version=agent.version,
        status=AgentStatus.ACTIVE,
        availability=agent.availability,
        pricing=agent.pricing,
        metrics=AgentMetrics(),
        created_at=now,
        updated_at=now
    )

    # Сохранение в "БД"
    agents_db[agent_id] = agent_response

    logger.info(f"Агент зарегистрирован: {agent_id}")

    return agent_response


@app.get(
    "/agents",
    response_model=AgentListResponse,
    tags=["Agents"]
)
async def list_agents(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    capabilities: Optional[List[str]] = Query(None, description="Фильтр по capabilities"),
    status: Optional[AgentStatus] = Query(None, description="Фильтр по статусу"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Минимальный рейтинг")
):
    """
    Получить список всех агентов с фильтрацией и пагинацией

    **Фильтры:**
    - `capabilities`: Список требуемых возможностей
    - `status`: Статус агента (active, inactive, busy, offline)
    - `min_rating`: Минимальный рейтинг агента

    **Пагинация:**
    - `page`: Номер страницы (начиная с 1)
    - `page_size`: Количество элементов на странице (1-100)
    """
    logger.info(f"Запрос списка агентов: page={page}, page_size={page_size}")

    # Фильтрация
    filtered_agents = list(agents_db.values())

    if capabilities:
        filtered_agents = [
            agent for agent in filtered_agents
            if any(cap in agent.capabilities for cap in capabilities)
        ]

    if status:
        filtered_agents = [
            agent for agent in filtered_agents
            if agent.status == status
        ]

    if min_rating is not None:
        filtered_agents = [
            agent for agent in filtered_agents
            if agent.rating >= min_rating
        ]

    # Пагинация
    total = len(filtered_agents)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_agents = filtered_agents[start_idx:end_idx]

    return AgentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        agents=paginated_agents
    )


@app.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    tags=["Agents"]
)
async def get_agent(agent_id: str):
    """
    Получить информацию об агенте по ID

    **Возвращает:**
    - Полную информацию об агенте включая метрики, рейтинг и доступность
    """
    logger.info(f"Запрос информации об агенте: {agent_id}")

    if agent_id not in agents_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Агент {agent_id} не найден"
        )

    return agents_db[agent_id]


@app.put(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    tags=["Agents"]
)
async def update_agent(
    agent_id: str,
    agent_update: AgentRegistration,
    owner_id: str = Depends(get_current_user)
):
    """
    Обновить информацию об агенте

    **Требования:**
    - Только владелец агента может его обновить
    - Нельзя изменить agent_id
    """
    logger.info(f"Обновление агента: {agent_id}")

    if agent_id not in agents_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Агент {agent_id} не найден"
        )

    existing_agent = agents_db[agent_id]

    # Проверка прав доступа
    if existing_agent.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления агента"
        )

    # Обновление полей
    existing_agent.name = agent_update.name
    existing_agent.description = agent_update.description
    existing_agent.capabilities = agent_update.capabilities
    existing_agent.model = agent_update.model
    existing_agent.version = agent_update.version
    existing_agent.availability = agent_update.availability
    existing_agent.pricing = agent_update.pricing
    existing_agent.updated_at = datetime.utcnow()

    agents_db[agent_id] = existing_agent

    logger.info(f"Агент обновлен: {agent_id}")

    return existing_agent


@app.delete(
    "/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Agents"]
)
async def delete_agent(
    agent_id: str,
    owner_id: str = Depends(get_current_user)
):
    """
    Удалить агента из системы

    **Требования:**
    - Только владелец агента может его удалить
    - Агент не должен иметь активных задач
    """
    logger.info(f"Удаление агента: {agent_id}")

    if agent_id not in agents_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Агент {agent_id} не найден"
        )

    existing_agent = agents_db[agent_id]

    # Проверка прав доступа
    if existing_agent.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления агента"
        )

    # Проверка что агент не занят
    if existing_agent.status == AgentStatus.BUSY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Нельзя удалить агента, который выполняет задачи"
        )

    del agents_db[agent_id]

    logger.info(f"Агент удален: {agent_id}")

    return None


@app.get(
    "/agents/{agent_id}/health",
    response_model=HealthResponse,
    tags=["Agents"]
)
async def check_agent_health(agent_id: str):
    """
    Проверить здоровье и доступность агента

    **Возвращает:**
    - Текущий статус агента
    - Загрузку (количество активных задач)
    - Доступную мощность
    """
    logger.info(f"Проверка здоровья агента: {agent_id}")

    if agent_id not in agents_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Агент {agent_id} не найден"
        )

    agent = agents_db[agent_id]

    # Mock данные о нагрузке
    current_load = 2 if agent.status == AgentStatus.BUSY else 0

    return HealthResponse(
        status=agent.status.value,
        agent_id=agent_id,
        current_load=current_load,
        available_capacity=agent.availability.max_concurrent_tasks - current_load,
        last_task_completed=agent.last_seen
    )


@app.get("/metrics", tags=["System"])
async def get_metrics():
    """Prometheus metrics endpoint"""
    # В production это будет настоящий Prometheus экспорт
    return {
        "total_agents": len(agents_db),
        "active_agents": sum(1 for a in agents_db.values() if a.status == AgentStatus.ACTIVE),
        "busy_agents": sum(1 for a in agents_db.values() if a.status == AgentStatus.BUSY),
        "total_tasks_completed": sum(a.metrics.total_tasks_completed for a in agents_db.values())
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,  # Для development
        log_level="info"
    )
