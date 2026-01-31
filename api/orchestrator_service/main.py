"""
Orchestrator Service API

Handles task decomposition, agent assignment, and execution orchestration.
"""

from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import time


# ============================================================================
# Configuration
# ============================================================================

app = FastAPI(
    title="Orchestrator Service",
    description="Task orchestration and execution management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
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
tasks_created = Counter('orchestrator_tasks_created_total', 'Total tasks created', ['priority'])
tasks_completed = Counter('orchestrator_tasks_completed_total', 'Total tasks completed')
tasks_failed = Counter('orchestrator_tasks_failed_total', 'Total tasks failed')
decomposition_duration = Histogram('task_decomposition_duration_seconds', 'Task decomposition time')
agent_matching_duration = Histogram('agent_matching_duration_seconds', 'Agent matching time')
task_queue_depth = Gauge('task_queue_depth', 'Current task queue depth', ['status'])
subtask_count = Histogram('task_subtask_count', 'Number of subtasks per task')


# ============================================================================
# Models
# ============================================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SubtaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskCreate(BaseModel):
    """Create a new task"""
    customer_id: str
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    required_capabilities: List[str] = Field(..., min_items=1)
    budget: float = Field(..., gt=0)
    deadline: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    rental_mode: str = "commercial"
    max_subtasks: int = Field(100, ge=1, le=100)
    metadata: Optional[Dict[str, Any]] = {}


class TaskResponse(BaseModel):
    """Task response"""
    task_id: str
    customer_id: str
    title: str
    description: str
    required_capabilities: List[str]
    budget: float
    actual_cost: float
    deadline: Optional[datetime]
    priority: str
    status: str
    progress: float
    subtask_count: int
    assigned_agents: List[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class SubtaskCreate(BaseModel):
    """Create subtask (internal use)"""
    task_id: str
    title: str
    description: str
    required_capabilities: List[str]
    dependencies: List[str] = []
    execution_level: int = 0
    estimated_cost: float
    estimated_hours: Optional[float] = None


class SubtaskResponse(BaseModel):
    """Subtask response"""
    subtask_id: str
    task_id: str
    title: str
    description: str
    required_capabilities: List[str]
    dependencies: List[str]
    execution_level: int
    status: str
    assigned_agent_id: Optional[str]
    estimated_cost: float
    actual_cost: float
    progress: float
    created_at: datetime
    completed_at: Optional[datetime]


class TaskDecompositionResult(BaseModel):
    """Result of task decomposition"""
    task_id: str
    subtasks: List[SubtaskResponse]
    execution_graph: Dict[str, Any]
    total_estimated_cost: float
    estimated_duration_hours: float


class AgentAssignment(BaseModel):
    """Agent assignment to subtask"""
    subtask_id: str
    agent_id: str
    estimated_start: datetime
    estimated_completion: datetime


class ExecutionPlan(BaseModel):
    """Complete execution plan"""
    task_id: str
    execution_levels: List[List[str]]  # Subtask IDs grouped by execution level
    agent_assignments: List[AgentAssignment]
    estimated_total_cost: float
    estimated_completion: datetime


# ============================================================================
# In-Memory Storage
# ============================================================================

tasks_db: Dict[str, Dict] = {}
subtasks_db: Dict[str, Dict] = {}
execution_plans_db: Dict[str, Dict] = {}

# Mock agents pool
available_agents: List[Dict] = []


# ============================================================================
# Task Decomposition Logic
# ============================================================================

def decompose_task(task: Dict) -> List[Dict]:
    """
    Decompose task into subtasks using heuristics

    In production, this would use:
    - LLM (Claude, GPT-4) for intelligent decomposition
    - Pre-trained models for task analysis
    - Historical data for patterns

    For now, we use simple heuristics based on capabilities.
    """
    subtasks = []
    capabilities = task['required_capabilities']

    # Heuristic 1: One subtask per capability (simple approach)
    for i, capability in enumerate(capabilities):
        subtask = {
            "subtask_id": f"subtask-{uuid.uuid4()}",
            "task_id": task['task_id'],
            "title": f"Execute {capability} for {task['title']}",
            "description": f"Subtask requiring {capability} capability",
            "required_capabilities": [capability],
            "dependencies": [],
            "execution_level": 0,
            "status": SubtaskStatus.PENDING.value,
            "assigned_agent_id": None,
            "estimated_cost": task['budget'] / len(capabilities),
            "actual_cost": 0.0,
            "estimated_hours": 5.0,  # Default estimate
            "progress": 0.0,
            "created_at": datetime.now(),
            "completed_at": None
        }
        subtasks.append(subtask)

    # Heuristic 2: For complex tasks, add coordination subtask
    if len(capabilities) > 3:
        coordination_subtask = {
            "subtask_id": f"subtask-{uuid.uuid4()}",
            "task_id": task['task_id'],
            "title": f"Coordinate and integrate results",
            "description": "Final coordination and quality check",
            "required_capabilities": ["coordination", "quality_assurance"],
            "dependencies": [st['subtask_id'] for st in subtasks],
            "execution_level": 1,
            "status": SubtaskStatus.PENDING.value,
            "assigned_agent_id": None,
            "estimated_cost": task['budget'] * 0.1,
            "actual_cost": 0.0,
            "estimated_hours": 2.0,
            "progress": 0.0,
            "created_at": datetime.now(),
            "completed_at": None
        }
        subtasks.append(coordination_subtask)

    # Heuristic 3: For data-heavy tasks, add preparation subtask
    if any(cap in ['data_analysis', 'machine_learning'] for cap in capabilities):
        prep_subtask = {
            "subtask_id": f"subtask-{uuid.uuid4()}",
            "task_id": task['task_id'],
            "title": "Data preparation and validation",
            "description": "Prepare and validate data before analysis",
            "required_capabilities": ["data_engineering"],
            "dependencies": [],
            "execution_level": 0,
            "status": SubtaskStatus.PENDING.value,
            "assigned_agent_id": None,
            "estimated_cost": task['budget'] * 0.15,
            "actual_cost": 0.0,
            "estimated_hours": 3.0,
            "progress": 0.0,
            "created_at": datetime.now(),
            "completed_at": None
        }
        # Make other subtasks depend on data prep
        for st in subtasks:
            if any(cap in st['required_capabilities'] for cap in ['data_analysis', 'machine_learning']):
                st['dependencies'].append(prep_subtask['subtask_id'])
                st['execution_level'] = 1

        subtasks.insert(0, prep_subtask)

    return subtasks


def build_execution_graph(subtasks: List[Dict]) -> Dict[str, Any]:
    """Build execution dependency graph"""
    graph = {
        "nodes": [],
        "edges": [],
        "levels": {}
    }

    for subtask in subtasks:
        # Add node
        graph["nodes"].append({
            "id": subtask['subtask_id'],
            "title": subtask['title'],
            "level": subtask['execution_level']
        })

        # Add edges for dependencies
        for dep_id in subtask['dependencies']:
            graph["edges"].append({
                "from": dep_id,
                "to": subtask['subtask_id']
            })

        # Group by execution level
        level = subtask['execution_level']
        if level not in graph["levels"]:
            graph["levels"][level] = []
        graph["levels"][level].append(subtask['subtask_id'])

    return graph


def assign_agents_to_subtasks(subtasks: List[Dict]) -> List[Dict]:
    """
    Assign best-fit agents to subtasks

    In production, this would use:
    - Agent capability matching
    - Load balancing
    - Cost optimization
    - Availability checking
    """
    assignments = []

    for subtask in subtasks:
        # Find agents with matching capabilities (mock)
        matching_agents = [
            agent for agent in available_agents
            if any(cap in agent['capabilities'] for cap in subtask['required_capabilities'])
        ]

        if matching_agents:
            # Pick best agent (by rating, for now)
            best_agent = max(matching_agents, key=lambda a: a.get('rating', 0))

            subtask['assigned_agent_id'] = best_agent['agent_id']
            subtask['status'] = SubtaskStatus.ASSIGNED.value

            # Create assignment
            now = datetime.now()
            estimated_hours = subtask.get('estimated_hours', 5.0)

            assignment = {
                "subtask_id": subtask['subtask_id'],
                "agent_id": best_agent['agent_id'],
                "estimated_start": now + timedelta(hours=subtask['execution_level'] * estimated_hours),
                "estimated_completion": now + timedelta(hours=(subtask['execution_level'] + 1) * estimated_hours)
            }
            assignments.append(assignment)

    return assignments


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator-service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "queue_depth": {
            "pending": len([t for t in tasks_db.values() if t['status'] == TaskStatus.PENDING.value]),
            "running": len([t for t in tasks_db.values() if t['status'] == TaskStatus.RUNNING.value])
        }
    }


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, background_tasks: BackgroundTasks):
    """
    Create a new task

    The task will be:
    1. Validated
    2. Decomposed into subtasks
    3. Assigned to agents
    4. Queued for execution
    """
    task_id = f"task-{uuid.uuid4()}"
    now = datetime.now()

    task_data = {
        "task_id": task_id,
        "customer_id": task.customer_id,
        "title": task.title,
        "description": task.description,
        "required_capabilities": task.required_capabilities,
        "budget": task.budget,
        "actual_cost": 0.0,
        "deadline": task.deadline,
        "priority": task.priority.value,
        "rental_mode": task.rental_mode,
        "status": TaskStatus.PENDING.value,
        "progress": 0.0,
        "subtask_count": 0,
        "assigned_agents": [],
        "created_at": now,
        "started_at": None,
        "completed_at": None,
        "metadata": task.metadata
    }

    tasks_db[task_id] = task_data

    # Track metrics
    tasks_created.labels(priority=task.priority.value).inc()
    task_queue_depth.labels(status='pending').inc()

    # Schedule background decomposition and planning
    background_tasks.add_task(decompose_and_plan_task, task_id)

    return TaskResponse(**task_data)


async def decompose_and_plan_task(task_id: str):
    """
    Background task to decompose and plan execution
    """
    if task_id not in tasks_db:
        return

    task = tasks_db[task_id]
    start_time = time.time()

    try:
        # Update status to planning
        task['status'] = TaskStatus.PLANNING.value
        task_queue_depth.labels(status='pending').dec()
        task_queue_depth.labels(status='planning').inc()

        # Decompose task into subtasks
        subtasks = decompose_task(task)

        # Store subtasks
        for subtask in subtasks:
            subtasks_db[subtask['subtask_id']] = subtask

        # Track decomposition metrics
        duration = time.time() - start_time
        decomposition_duration.observe(duration)
        subtask_count.observe(len(subtasks))

        # Build execution graph
        execution_graph = build_execution_graph(subtasks)

        # Assign agents
        match_start = time.time()
        assignments = assign_agents_to_subtasks(subtasks)
        agent_matching_duration.observe(time.time() - match_start)

        # Create execution plan
        execution_plan = {
            "task_id": task_id,
            "execution_levels": list(execution_graph["levels"].values()),
            "agent_assignments": assignments,
            "estimated_total_cost": sum(st['estimated_cost'] for st in subtasks),
            "estimated_completion": datetime.now() + timedelta(hours=24)
        }
        execution_plans_db[task_id] = execution_plan

        # Update task
        task['subtask_count'] = len(subtasks)
        task['assigned_agents'] = [a['agent_id'] for a in assignments]
        task['status'] = TaskStatus.RUNNING.value
        task['started_at'] = datetime.now()

        task_queue_depth.labels(status='planning').dec()
        task_queue_depth.labels(status='running').inc()

        # In production, this would trigger actual execution
        # For now, we'll simulate completion after a delay
        await asyncio.sleep(5)
        await simulate_task_completion(task_id)

    except Exception as e:
        task['status'] = TaskStatus.FAILED.value
        task_queue_depth.labels(status='planning').dec()
        tasks_failed.inc()
        print(f"Failed to decompose task {task_id}: {e}")


async def simulate_task_completion(task_id: str):
    """Simulate task completion (for demo purposes)"""
    if task_id not in tasks_db:
        return

    task = tasks_db[task_id]

    # Mark all subtasks as completed
    for subtask_id, subtask in subtasks_db.items():
        if subtask['task_id'] == task_id:
            subtask['status'] = SubtaskStatus.COMPLETED.value
            subtask['progress'] = 100.0
            subtask['actual_cost'] = subtask['estimated_cost']
            subtask['completed_at'] = datetime.now()

    # Mark task as completed
    task['status'] = TaskStatus.COMPLETED.value
    task['progress'] = 100.0
    task['actual_cost'] = sum(
        st['actual_cost'] for st in subtasks_db.values()
        if st['task_id'] == task_id
    )
    task['completed_at'] = datetime.now()

    task_queue_depth.labels(status='running').dec()
    tasks_completed.inc()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task details"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(**tasks_db[task_id])


@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    customer_id: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    limit: int = 50
):
    """List tasks with optional filtering"""
    filtered_tasks = list(tasks_db.values())

    if customer_id:
        filtered_tasks = [t for t in filtered_tasks if t['customer_id'] == customer_id]

    if status:
        filtered_tasks = [t for t in filtered_tasks if t['status'] == status.value]

    if priority:
        filtered_tasks = [t for t in filtered_tasks if t['priority'] == priority.value]

    # Sort by created_at descending
    filtered_tasks.sort(key=lambda x: x['created_at'], reverse=True)

    return [TaskResponse(**task) for task in filtered_tasks[:limit]]


@app.get("/tasks/{task_id}/decomposition", response_model=TaskDecompositionResult)
async def get_task_decomposition(task_id: str):
    """Get task decomposition details"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get subtasks for this task
    task_subtasks = [
        st for st in subtasks_db.values()
        if st['task_id'] == task_id
    ]

    if not task_subtasks:
        raise HTTPException(status_code=404, detail="Task not yet decomposed")

    # Build execution graph
    execution_graph = build_execution_graph(task_subtasks)

    # Calculate totals
    total_estimated_cost = sum(st['estimated_cost'] for st in task_subtasks)
    total_estimated_hours = sum(st.get('estimated_hours', 0) for st in task_subtasks)

    return TaskDecompositionResult(
        task_id=task_id,
        subtasks=[SubtaskResponse(**st) for st in task_subtasks],
        execution_graph=execution_graph,
        total_estimated_cost=total_estimated_cost,
        estimated_duration_hours=total_estimated_hours
    )


@app.get("/tasks/{task_id}/execution-plan", response_model=ExecutionPlan)
async def get_execution_plan(task_id: str):
    """Get task execution plan"""
    if task_id not in execution_plans_db:
        raise HTTPException(status_code=404, detail="Execution plan not found")

    plan = execution_plans_db[task_id]

    return ExecutionPlan(
        task_id=plan['task_id'],
        execution_levels=plan['execution_levels'],
        agent_assignments=[AgentAssignment(**a) for a in plan['agent_assignments']],
        estimated_total_cost=plan['estimated_total_cost'],
        estimated_completion=plan['estimated_completion']
    )


@app.get("/subtasks/{subtask_id}", response_model=SubtaskResponse)
async def get_subtask(subtask_id: str):
    """Get subtask details"""
    if subtask_id not in subtasks_db:
        raise HTTPException(status_code=404, detail="Subtask not found")

    return SubtaskResponse(**subtasks_db[subtask_id])


@app.patch("/subtasks/{subtask_id}/status")
async def update_subtask_status(
    subtask_id: str,
    status: SubtaskStatus,
    progress: Optional[float] = None
):
    """Update subtask status and progress"""
    if subtask_id not in subtasks_db:
        raise HTTPException(status_code=404, detail="Subtask not found")

    subtask = subtasks_db[subtask_id]
    subtask['status'] = status.value

    if progress is not None:
        subtask['progress'] = min(100.0, max(0.0, progress))

    if status == SubtaskStatus.COMPLETED:
        subtask['progress'] = 100.0
        subtask['completed_at'] = datetime.now()

        # Check if all subtasks for task are completed
        task_id = subtask['task_id']
        await check_task_completion(task_id)

    return {"message": "Subtask updated successfully", "subtask": subtask}


async def check_task_completion(task_id: str):
    """Check if all subtasks are completed and update task status"""
    if task_id not in tasks_db:
        return

    task_subtasks = [
        st for st in subtasks_db.values()
        if st['task_id'] == task_id
    ]

    if not task_subtasks:
        return

    # Check if all subtasks completed
    all_completed = all(
        st['status'] == SubtaskStatus.COMPLETED.value
        for st in task_subtasks
    )

    if all_completed:
        task = tasks_db[task_id]
        task['status'] = TaskStatus.COMPLETED.value
        task['progress'] = 100.0
        task['completed_at'] = datetime.now()
        task['actual_cost'] = sum(st['actual_cost'] for st in task_subtasks)

        task_queue_depth.labels(status='running').dec()
        tasks_completed.inc()


@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a task"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks_db[task_id]

    if task['status'] in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel completed or failed task"
        )

    task['status'] = TaskStatus.CANCELLED.value

    # Cancel all subtasks
    for subtask in subtasks_db.values():
        if subtask['task_id'] == task_id and subtask['status'] not in [
            SubtaskStatus.COMPLETED.value,
            SubtaskStatus.FAILED.value
        ]:
            subtask['status'] = SubtaskStatus.FAILED.value

    task_queue_depth.labels(status=task['status']).dec()

    return {"message": "Task cancelled successfully"}


@app.get("/statistics")
async def get_orchestrator_statistics():
    """Get orchestrator statistics"""
    total_tasks = len(tasks_db)

    status_counts = {}
    for task_status in TaskStatus:
        status_counts[task_status.value] = sum(
            1 for t in tasks_db.values()
            if t['status'] == task_status.value
        )

    total_subtasks = len(subtasks_db)
    avg_subtasks = total_subtasks / total_tasks if total_tasks > 0 else 0

    total_cost = sum(
        t['actual_cost'] for t in tasks_db.values()
        if t['status'] == TaskStatus.COMPLETED.value
    )

    return {
        "total_tasks": total_tasks,
        "status_breakdown": status_counts,
        "total_subtasks": total_subtasks,
        "avg_subtasks_per_task": round(avg_subtasks, 2),
        "total_cost": round(total_cost, 2),
        "queue_depth": {
            status.value: status_counts.get(status.value, 0)
            for status in [TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.RUNNING]
        }
    }


# ============================================================================
# Initialization
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    print("Orchestrator Service starting up...")

    # Initialize mock agents pool
    global available_agents
    available_agents = [
        {
            "agent_id": f"agent-{i}",
            "name": f"Agent {i}",
            "capabilities": ["python_coding", "data_analysis"],
            "rating": 4.5 + (i % 5) * 0.1,
            "status": "active"
        }
        for i in range(10)
    ]

    print("Orchestrator Service ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Orchestrator Service shutting down...")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
