# Docker Setup для AI Agent Orchestration Platform

Эта директория содержит Docker конфигурации для локального развертывания и разработки платформы.

## 📋 Содержание

- [Структура](#структура)
- [Быстрый старт](#быстрый-старт)
- [Docker Images](#docker-images)
- [Docker Compose](#docker-compose)
- [Development](#development)
- [Production](#production)

## 📁 Структура

```
docker/
├── Dockerfile.api-gateway        # API Gateway
├── Dockerfile.registry-service   # Registry Service
├── Dockerfile.marketplace-service# Marketplace Service
├── Dockerfile.orchestrator-service# Orchestrator Service
├── Dockerfile.agent-worker       # Agent Worker
├── Dockerfile.python-agent       # Python Coding Agent
├── docker-compose.yaml           # Полный стек для локальной разработки
├── .dockerignore                 # Игнорируемые файлы
├── requirements/                 # Python зависимости
│   ├── base.txt
│   ├── api-gateway.txt
│   ├── registry-service.txt
│   ├── marketplace-service.txt
│   ├── orchestrator-service.txt
│   └── agent-worker.txt
└── README.md
```

## 🚀 Быстрый старт

### Предварительные требования

- Docker 24.0+
- Docker Compose 2.20+
- 8GB+ RAM
- 20GB+ свободного места на диске

### 1. Настройка окружения

Создайте файл `.env` в корне проекта:

```bash
# AI API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
GOOGLE_API_KEY=your-key-here

# Database
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_PASSWORD=your_secure_password

# RabbitMQ
RABBITMQ_PASSWORD=your_secure_password

# JWT
JWT_SECRET=your_long_random_secret_string

# Environment
ENVIRONMENT=development
```

### 2. Запуск всего стека

```bash
# Запустить все сервисы
cd docker
docker-compose up -d

# Проверить статус
docker-compose ps

# Посмотреть логи
docker-compose logs -f
```

### 3. Проверка работоспособности

```bash
# API Gateway
curl http://localhost:8000/health

# Registry Service
curl http://localhost:8080/health

# Marketplace Service
curl http://localhost:8081/health

# Orchestrator Service
curl http://localhost:8082/health

# RabbitMQ Management UI
open http://localhost:15672
# Логин: platform / Пароль: dev_password_CHANGE_ME

# Grafana
open http://localhost:3000
# Логин: admin / Пароль: admin_CHANGE_ME

# Jaeger UI
open http://localhost:16686
```

## 🐳 Docker Images

### Сборка отдельных образов

```bash
# API Gateway
docker build -f Dockerfile.api-gateway -t agent-platform/api-gateway:latest ..

# Registry Service
docker build -f Dockerfile.registry-service -t agent-platform/registry-service:latest ..

# Marketplace Service
docker build -f Dockerfile.marketplace-service -t agent-platform/marketplace-service:latest ..

# Orchestrator Service
docker build -f Dockerfile.orchestrator-service -t agent-platform/orchestrator-service:latest ..

# Agent Worker
docker build -f Dockerfile.agent-worker -t agent-platform/agent-worker:latest ..

# Python Agent
docker build -f Dockerfile.python-agent -t agent-platform/python-agent:latest ..
```

### Сборка всех образов

```bash
docker-compose build
```

### Тегирование для registry

```bash
# Для Docker Hub
docker tag agent-platform/api-gateway:latest your-username/agent-platform-api-gateway:latest
docker push your-username/agent-platform-api-gateway:latest

# Для Google Container Registry
docker tag agent-platform/api-gateway:latest gcr.io/your-project/agent-platform-api-gateway:latest
docker push gcr.io/your-project/agent-platform-api-gateway:latest

# Для AWS ECR
docker tag agent-platform/api-gateway:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/agent-platform-api-gateway:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/agent-platform-api-gateway:latest
```

## 🔧 Docker Compose

### Основные команды

```bash
# Запустить все сервисы
docker-compose up -d

# Запустить конкретные сервисы
docker-compose up -d postgres redis rabbitmq

# Остановить все сервисы
docker-compose down

# Остановить и удалить volumes
docker-compose down -v

# Перезапустить сервис
docker-compose restart orchestrator-service

# Просмотр логов
docker-compose logs -f api-gateway

# Масштабирование воркеров
docker-compose up -d --scale agent-worker=5
```

### Архитектура сервисов

```
┌─────────────────────────────────────────────────┐
│            http://localhost:8000                 │
│              API Gateway                         │
└──────┬──────────────┬────────────┬──────────────┘
       │              │            │
       ▼              ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Registry │  │Marketplace│ │Orchestr. │
│  :8080   │  │  :8081   │  │  :8082   │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   │
     ┌─────────────┴─────────────┐
     │                           │
     ▼                           ▼
┌──────────┐              ┌──────────┐
│PostgreSQL│              │ RabbitMQ │
│  :5432   │              │  :5672   │
└──────────┘              └────┬─────┘
     │                         │
     │                         ▼
     │                  ┌──────────────┐
     │                  │Agent Workers │
     │                  │(3 replicas)  │
     │                  └──────────────┘
     │
     ▼
┌──────────┐
│  Redis   │
│  :6379   │
└──────────┘
```

## 💻 Development

### Live Reload

Для разработки с live reload используйте volume mounts:

```yaml
# docker-compose.dev.yaml
services:
  registry-service:
    volumes:
      - ../src:/app/src
    environment:
      - RELOAD=true
```

Запуск:

```bash
docker-compose -f docker-compose.yaml -f docker-compose.dev.yaml up
```

### Debugging

Для debugging добавьте порты для debugger:

```yaml
services:
  registry-service:
    ports:
      - "8080:8080"
      - "5678:5678"  # debugpy
    environment:
      - DEBUG=true
```

### Тестирование

Запуск тестов в контейнере:

```bash
# Запустить pytest в контейнере
docker-compose exec registry-service pytest /app/tests

# С coverage
docker-compose exec registry-service pytest --cov=/app/src --cov-report=html
```

### Доступ к контейнерам

```bash
# Войти в контейнер
docker-compose exec registry-service /bin/bash

# Выполнить команду
docker-compose exec postgres psql -U platform_admin -d agent_platform

# Проверить логи
docker-compose logs -f --tail=100 orchestrator-service
```

## 🚀 Production

### Рекомендации для Production

**НЕ используйте docker-compose для production!** Используйте Kubernetes манифесты из `/k8s`.

Если всё же нужен Docker Compose:

1. **Используйте production образы**:
```yaml
services:
  registry-service:
    image: your-registry/agent-platform-registry:1.0.0
    # НЕ используйте build
```

2. **Настройте secrets**:
```bash
# Используйте Docker secrets
echo "your_secure_password" | docker secret create postgres_password -
```

3. **Используйте healthchecks**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

4. **Ограничьте ресурсы**:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

5. **Настройте логирование**:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

6. **Используйте restart policies**:
```yaml
restart: unless-stopped
```

### Production-ready docker-compose

```yaml
version: '3.8'

services:
  registry-service:
    image: your-registry/agent-platform-registry:${VERSION}
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - agent-platform
    secrets:
      - postgres_password
      - jwt_secret
```

## 📊 Мониторинг

### Prometheus Metrics

Все сервисы экспортируют метрики:

- **API Gateway**: http://localhost:9000/metrics
- **Registry Service**: http://localhost:9090/metrics
- **Marketplace Service**: http://localhost:9091/metrics
- **Orchestrator Service**: http://localhost:9092/metrics
- **Agent Workers**: http://localhost:9093/metrics

### Grafana Dashboards

Импортируйте готовые dashboards:

```bash
# Dashboard ID для Grafana
# FastAPI: 14280
# PostgreSQL: 9628
# Redis: 11835
# RabbitMQ: 10991
```

### Jaeger Tracing

Distributed tracing доступен по адресу: http://localhost:16686

## 🔒 Безопасность

### Best Practices

1. **Не используйте root**:
Все Dockerfiles создают непривилегированного пользователя

2. **Минимальные образы**:
Используем `-slim` и `-alpine` версии

3. **Multi-stage builds**:
Отделяем build dependencies от runtime

4. **Scan образов**:
```bash
docker scan agent-platform/api-gateway:latest
```

5. **Secrets management**:
Используйте Docker secrets или внешний vault

6. **Network isolation**:
Используйте custom networks

### Обновление зависимостей

```bash
# Обновить все requirements
pip-compile --upgrade requirements/*.txt

# Проверить уязвимости
safety check -r requirements/base.txt
```

## 🧪 Тестирование

### Integration Tests

```bash
# Запустить тесты
docker-compose -f docker-compose.test.yaml up --abort-on-container-exit

# Cleanup
docker-compose -f docker-compose.test.yaml down -v
```

### Load Testing

```bash
# Использовать locust для нагрузочного тестирования
docker run --network=docker_agent-platform -p 8089:8089 \
  locustio/locust -f /tests/locustfile.py \
  --host=http://api-gateway:8000
```

## 🗑️ Очистка

```bash
# Остановить и удалить все
docker-compose down -v

# Удалить образы
docker rmi $(docker images 'agent-platform/*' -q)

# Очистить все Docker ресурсы
docker system prune -a --volumes
```

## 📚 Дополнительные ресурсы

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)

## 🐛 Troubleshooting

### Контейнер не запускается

```bash
# Проверить логи
docker-compose logs registry-service

# Проверить healthcheck
docker inspect --format='{{json .State.Health}}' agent-platform-registry

# Войти в контейнер
docker-compose exec registry-service /bin/bash
```

### Проблемы с сетью

```bash
# Проверить сети
docker network ls

# Inspect сеть
docker network inspect docker_agent-platform

# Пересоздать сеть
docker-compose down
docker network prune
docker-compose up -d
```

### Проблемы с volumes

```bash
# Проверить volumes
docker volume ls

# Inspect volume
docker volume inspect docker_postgres_data

# Удалить и пересоздать
docker-compose down -v
docker-compose up -d
```

### Out of Memory

```bash
# Увеличить Docker memory limit
# macOS: Docker Desktop → Settings → Resources → Memory

# Linux: /etc/docker/daemon.json
{
  "default-ulimits": {
    "memlock": {
      "Hard": -1,
      "Name": "memlock",
      "Soft": -1
    }
  }
}
```

---

**Готово к разработке!** 🚀

Для production развертывания используйте [Kubernetes манифесты](/k8s/README.md).
