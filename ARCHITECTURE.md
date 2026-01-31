# Architecture Overview

This document provides a comprehensive overview of the AI Agent Orchestration Platform architecture.

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Component Diagram](#component-diagram)
- [Data Flow](#data-flow)
- [Deployment Architecture](#deployment-architecture)
- [Security Architecture](#security-architecture)
- [Scalability Architecture](#scalability-architecture)

---

## High-Level Architecture

The platform follows a microservices architecture with clear separation of concerns:

```mermaid
graph TB
    subgraph "External Users"
        Client[Client Application]
        CLI[CLI Tool]
        SDK[Python SDK]
    end

    subgraph "API Layer"
        Gateway[API Gateway<br/>:8000]
    end

    subgraph "Core Services"
        Registry[Registry Service<br/>:8001]
        Marketplace[Marketplace Service<br/>:8002]
        Orchestrator[Orchestrator Service<br/>:8003]
    end

    subgraph "Execution Layer"
        Workers[Agent Workers<br/>Kagent Pods]
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL<br/>Database)]
        Redis[(Redis<br/>Cache)]
        RabbitMQ[RabbitMQ<br/>Queue]
    end

    subgraph "Monitoring"
        Prometheus[Prometheus]
        Grafana[Grafana]
    end

    Client --> Gateway
    CLI --> Gateway
    SDK --> Gateway

    Gateway --> Registry
    Gateway --> Marketplace
    Gateway --> Orchestrator

    Registry --> PostgreSQL
    Marketplace --> PostgreSQL
    Orchestrator --> PostgreSQL
    Orchestrator --> RabbitMQ

    RabbitMQ --> Workers
    Workers --> PostgreSQL

    Gateway --> Redis
    Marketplace --> Redis

    Registry -.metrics.-> Prometheus
    Marketplace -.metrics.-> Prometheus
    Orchestrator -.metrics.-> Prometheus
    Workers -.metrics.-> Prometheus

    Prometheus --> Grafana
```

---

## Component Diagram

### Detailed Service Breakdown

```mermaid
graph LR
    subgraph "API Gateway"
        GW_Router[Router]
        GW_Auth[Auth Middleware]
        GW_RateLimit[Rate Limiter]
        GW_Logger[Request Logger]
    end

    subgraph "Registry Service"
        REG_API[Agent API]
        REG_CRUD[CRUD Operations]
        REG_Search[Capability Search]
        REG_Validation[Input Validation]
    end

    subgraph "Marketplace Service"
        MKT_Search[Agent Search]
        MKT_Contract[Contract Management]
        MKT_Review[Review System]
        MKT_Billing[Billing Tracker]
    end

    subgraph "Orchestrator Service"
        ORCH_Decompose[Task Decomposer]
        ORCH_DAG[DAG Builder]
        ORCH_Assign[Agent Assigner]
        ORCH_Monitor[Progress Monitor]
    end

    Client[Client] --> GW_Router
    GW_Router --> GW_Auth
    GW_Auth --> GW_RateLimit
    GW_RateLimit --> GW_Logger

    GW_Logger --> REG_API
    GW_Logger --> MKT_Search
    GW_Logger --> ORCH_Decompose

    REG_API --> REG_CRUD
    REG_API --> REG_Search
    REG_API --> REG_Validation

    MKT_Search --> MKT_Contract
    MKT_Contract --> MKT_Billing
    MKT_Search --> MKT_Review

    ORCH_Decompose --> ORCH_DAG
    ORCH_DAG --> ORCH_Assign
    ORCH_Assign --> ORCH_Monitor
```

---

## Data Flow

### Task Execution Flow

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Orchestrator
    participant Marketplace
    participant DB as PostgreSQL
    participant Queue as RabbitMQ
    participant Worker as Agent Worker

    Client->>Gateway: POST /tasks (create task)
    Gateway->>Orchestrator: Forward request
    Orchestrator->>DB: Save task
    Orchestrator->>Orchestrator: Decompose into subtasks
    Orchestrator->>DB: Save subtasks
    Orchestrator->>Marketplace: Find agents by capabilities
    Marketplace->>DB: Query agents
    DB-->>Marketplace: Return matching agents
    Marketplace-->>Orchestrator: Agent list
    Orchestrator->>Orchestrator: Assign agents to subtasks
    Orchestrator->>Queue: Publish subtasks
    Queue-->>Worker: Deliver subtask
    Worker->>Worker: Execute task
    Worker->>DB: Update progress
    Worker->>DB: Save result
    Worker->>Orchestrator: Report completion
    Orchestrator->>Orchestrator: Check if all subtasks done
    Orchestrator->>DB: Update task status
    Orchestrator-->>Gateway: Task completed
    Gateway-->>Client: Return result
```

### Agent Registration Flow

```mermaid
sequenceDiagram
    participant Owner as Agent Owner
    participant Gateway
    participant Registry
    participant DB as PostgreSQL

    Owner->>Gateway: POST /agents (register)
    Gateway->>Gateway: Validate API key
    Gateway->>Gateway: Rate limit check
    Gateway->>Registry: Forward request
    Registry->>Registry: Validate input (Pydantic)
    Registry->>DB: Check for duplicates
    DB-->>Registry: No duplicates
    Registry->>DB: INSERT agent
    DB-->>Registry: agent_id
    Registry->>DB: Log audit entry
    Registry-->>Gateway: Agent registered
    Gateway-->>Owner: Return agent details
```

---

## Deployment Architecture

### Kubernetes Deployment

```mermaid
graph TB
    subgraph "Ingress Layer"
        Ingress[NGINX Ingress<br/>TLS Termination]
    end

    subgraph "Application Layer"
        subgraph "API Gateway Pods"
            GW1[Gateway Pod 1]
            GW2[Gateway Pod 2]
            GW3[Gateway Pod 3]
        end

        subgraph "Registry Service Pods"
            REG1[Registry Pod 1]
            REG2[Registry Pod 2]
        end

        subgraph "Marketplace Service Pods"
            MKT1[Marketplace Pod 1]
            MKT2[Marketplace Pod 2]
        end

        subgraph "Orchestrator Service Pods"
            ORCH1[Orchestrator Pod 1]
            ORCH2[Orchestrator Pod 2]
            ORCH3[Orchestrator Pod 3]
        end

        subgraph "Agent Worker Pods (Auto-scaling)"
            WORK1[Worker Pod 1]
            WORK2[Worker Pod 2]
            WORK_N[Worker Pod N<br/>10-100 pods]
        end
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL<br/>StatefulSet)]
        Redis[(Redis<br/>Deployment)]
        RabbitMQ[RabbitMQ<br/>StatefulSet]
    end

    subgraph "Monitoring"
        Prometheus[Prometheus<br/>StatefulSet]
        Grafana[Grafana<br/>Deployment]
    end

    Ingress --> GW1 & GW2 & GW3
    GW1 & GW2 & GW3 --> REG1 & REG2
    GW1 & GW2 & GW3 --> MKT1 & MKT2
    GW1 & GW2 & GW3 --> ORCH1 & ORCH2 & ORCH3

    REG1 & REG2 --> PostgreSQL
    MKT1 & MKT2 --> PostgreSQL
    ORCH1 & ORCH2 & ORCH3 --> PostgreSQL

    ORCH1 & ORCH2 & ORCH3 --> RabbitMQ
    RabbitMQ --> WORK1 & WORK2 & WORK_N
    WORK1 & WORK2 & WORK_N --> PostgreSQL

    GW1 & GW2 & GW3 --> Redis
    MKT1 & MKT2 --> Redis

    GW1 & GW2 & GW3 -.metrics.-> Prometheus
    REG1 & REG2 -.metrics.-> Prometheus
    MKT1 & MKT2 -.metrics.-> Prometheus
    ORCH1 & ORCH2 & ORCH3 -.metrics.-> Prometheus
    WORK1 & WORK2 & WORK_N -.metrics.-> Prometheus

    Prometheus --> Grafana
```

### Horizontal Pod Autoscaling (HPA)

```mermaid
graph LR
    subgraph "HPA Configuration"
        direction TB
        HPA_GW[API Gateway HPA<br/>Min: 3, Max: 15<br/>Target CPU: 70%]
        HPA_REG[Registry HPA<br/>Min: 3, Max: 10<br/>Target CPU: 70%]
        HPA_MKT[Marketplace HPA<br/>Min: 3, Max: 10<br/>Target CPU: 70%]
        HPA_ORCH[Orchestrator HPA<br/>Min: 5, Max: 20<br/>Target CPU: 70%]
        HPA_WORK[Worker HPA<br/>Min: 10, Max: 100<br/>Target CPU: 80%]
    end

    HPA_GW -->|scales| GW_Pods[Gateway Pods]
    HPA_REG -->|scales| REG_Pods[Registry Pods]
    HPA_MKT -->|scales| MKT_Pods[Marketplace Pods]
    HPA_ORCH -->|scales| ORCH_Pods[Orchestrator Pods]
    HPA_WORK -->|scales| WORK_Pods[Worker Pods]
```

---

## Security Architecture

### Multi-Layer Security

```mermaid
graph TB
    subgraph "External Layer"
        Internet[Internet]
    end

    subgraph "Perimeter Security"
        TLS[TLS 1.3<br/>Encryption]
        DDoS[DDoS Protection]
    end

    subgraph "Application Security"
        Auth[JWT Auth]
        RateLimit[Rate Limiting]
        InputVal[Input Validation]
    end

    subgraph "Network Security"
        NetworkPolicy[K8s Network Policy]
        RBAC[RBAC Controls]
    end

    subgraph "Data Security"
        Encryption[Encryption at Rest]
        Secrets[K8s Secrets]
    end

    subgraph "Execution Security"
        Sandbox[Agent Sandboxing<br/>Kagent]
        ResourceLimit[Resource Limits]
        NonRoot[Non-root Containers]
    end

    Internet --> TLS
    TLS --> DDoS
    DDoS --> Auth
    Auth --> RateLimit
    RateLimit --> InputVal
    InputVal --> NetworkPolicy
    NetworkPolicy --> RBAC
    RBAC --> Encryption
    Encryption --> Secrets
    Secrets --> Sandbox
    Sandbox --> ResourceLimit
    ResourceLimit --> NonRoot
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Auth as Auth Service
    participant Redis
    participant Service as Backend Service

    Client->>Gateway: Request + API Key
    Gateway->>Redis: Check rate limit
    Redis-->>Gateway: OK
    Gateway->>Auth: Validate API Key
    Auth->>Auth: Generate JWT
    Auth-->>Gateway: JWT token
    Gateway->>Gateway: Add JWT to headers
    Gateway->>Service: Forward request + JWT
    Service->>Service: Validate JWT
    Service->>Service: Process request
    Service-->>Gateway: Response
    Gateway-->>Client: Response
```

---

## Scalability Architecture

### Load Distribution

```mermaid
graph TB
    subgraph "Load Balancing"
        LB[Load Balancer]
    end

    subgraph "API Gateway Layer"
        GW1[Gateway 1]
        GW2[Gateway 2]
        GW3[Gateway 3]
    end

    subgraph "Service Layer"
        REG[Registry Service<br/>3-10 pods]
        MKT[Marketplace Service<br/>3-10 pods]
        ORCH[Orchestrator Service<br/>5-20 pods]
    end

    subgraph "Worker Layer"
        WORK[Agent Workers<br/>10-100 pods]
    end

    subgraph "Data Layer Scaling"
        PostgreSQL_Master[(PostgreSQL Master)]
        PostgreSQL_Replica1[(PostgreSQL Replica 1)]
        PostgreSQL_Replica2[(PostgreSQL Replica 2)]
        Redis_Cluster[(Redis Cluster<br/>3 nodes)]
    end

    LB --> GW1 & GW2 & GW3
    GW1 & GW2 & GW3 --> REG & MKT & ORCH
    ORCH --> WORK

    REG & MKT & ORCH -->|writes| PostgreSQL_Master
    REG & MKT & ORCH -->|reads| PostgreSQL_Replica1 & PostgreSQL_Replica2

    GW1 & GW2 & GW3 --> Redis_Cluster
    MKT --> Redis_Cluster
```

---

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ AGENTS : owns
    USERS ||--o{ TASKS : creates
    USERS ||--o{ RENTAL_CONTRACTS : participates
    USERS ||--o{ REVIEWS : writes
    USERS ||--o{ API_KEYS : has

    AGENTS ||--o{ RENTAL_CONTRACTS : rented_in
    AGENTS ||--o{ REVIEWS : reviewed_in
    AGENTS ||--o{ SUBTASKS : assigned_to

    TASKS ||--o{ SUBTASKS : contains
    TASKS ||--o{ TRANSACTIONS : generates

    RENTAL_CONTRACTS ||--o{ TRANSACTIONS : generates
    RENTAL_CONTRACTS ||--o{ REVIEWS : results_in

    USERS {
        uuid user_id PK
        string username UK
        string email UK
        decimal balance
        timestamp created_at
    }

    AGENTS {
        uuid agent_id PK
        uuid owner_id FK
        string name
        text[] capabilities
        string pricing_mode
        decimal hourly_rate
        decimal rating
        int reviews_count
        string status
    }

    TASKS {
        uuid task_id PK
        uuid customer_id FK
        string title
        text[] required_capabilities
        decimal budget
        decimal actual_cost
        string status
        int progress
    }

    SUBTASKS {
        uuid subtask_id PK
        uuid task_id FK
        uuid assigned_agent_id FK
        jsonb dependencies
        string status
        decimal cost
    }

    RENTAL_CONTRACTS {
        uuid contract_id PK
        uuid agent_id FK
        uuid customer_id FK
        string rental_mode
        string billing_model
        decimal total_cost
        string status
    }

    REVIEWS {
        uuid review_id PK
        uuid agent_id FK
        uuid user_id FK
        decimal rating
        decimal quality_score
        decimal speed_score
        text comment
    }

    TRANSACTIONS {
        uuid transaction_id PK
        uuid from_user_id FK
        uuid to_user_id FK
        uuid contract_id FK
        decimal amount
        string type
    }

    API_KEYS {
        uuid key_id PK
        uuid user_id FK
        string key_hash
        timestamp expires_at
    }
```

---

## Technology Stack

### Backend Stack

```mermaid
graph LR
    subgraph "Application Framework"
        FastAPI[FastAPI<br/>Python 3.8+]
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL 14+)]
        Redis[(Redis 7+)]
        RabbitMQ[RabbitMQ 3.11+]
    end

    subgraph "Container Orchestration"
        Docker[Docker 24+]
        Kubernetes[Kubernetes 1.28+]
        Helm[Helm 3+]
        Kagent[Kagent<br/>Agent Framework]
    end

    subgraph "Monitoring"
        Prometheus[Prometheus]
        Grafana[Grafana]
        Jaeger[Jaeger]
    end

    FastAPI --> PostgreSQL
    FastAPI --> Redis
    FastAPI --> RabbitMQ

    Docker --> Kubernetes
    Kubernetes --> Helm
    Kubernetes --> Kagent

    FastAPI -.metrics.-> Prometheus
    Prometheus --> Grafana
    FastAPI -.traces.-> Jaeger
```

---

## Deployment Models

### Development

```
Docker Compose
├── All services in single host
├── Single instance per service
└── Local volumes for data
```

### Staging

```
Kubernetes (single cluster)
├── Multi-pod deployment
├── HPA with lower limits
└── Shared database instance
```

### Production

```
Kubernetes (multi-cluster)
├── Multi-region deployment
├── HPA with production limits
├── Database replication
├── CDN for static assets
└── Multi-AZ availability
```

---

## Performance Characteristics

### Latency Targets

- **API Gateway**: < 10ms (p99)
- **Registry Service**: < 50ms (p99)
- **Marketplace Search**: < 100ms (p99)
- **Task Creation**: < 200ms (p99)
- **Agent Worker Task Execution**: Variable (task-dependent)

### Throughput Targets

- **API Gateway**: 10,000 req/sec
- **Agent Registration**: 100 req/sec
- **Task Creation**: 500 req/sec
- **Concurrent Workers**: 100+ agents

### Scalability Limits

- **Max Concurrent Tasks**: 10,000+
- **Max Registered Agents**: 100,000+
- **Max Concurrent Workers**: 1,000+ (with auto-scaling)
- **Database Connections**: 1,000 (pooled)

---

## References

- [Kubernetes Architecture](https://kubernetes.io/docs/concepts/architecture/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL High Availability](https://www.postgresql.org/docs/current/high-availability.html)
- [Prometheus Operator](https://prometheus-operator.dev/)
- [Kagent Framework](https://kagent.dev/)
