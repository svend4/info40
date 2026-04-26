# Kubernetes Deployment для AI Agent Orchestration Platform

Эта директория содержит все Kubernetes манифесты для развертывания платформы оркестрации AI-агентов в production.

## 📋 Оглавление

- [Архитектура](#архитектура)
- [Компоненты](#компоненты)
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Развертывание](#развертывание)
- [Масштабирование](#масштабирование)
- [Мониторинг](#мониторинг)
- [Безопасность](#безопасность)

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Ingress (NGINX)                           │
│              api.agent-platform.example.com                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  API Gateway (3 pods)                        │
│                  Rate Limiting, Auth                         │
└─────────┬───────────┬───────────┬───────────────────────────┘
          │           │           │
          ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │Registry │ │Marketplace│ │Orchestr.│
    │Service  │ │ Service  │ │ Service │
    │(3 pods) │ │(3 pods)  │ │(5 pods) │
    └────┬────┘ └────┬─────┘ └────┬────┘
         │           │            │
         └───────────┼────────────┘
                     ▼
         ┌───────────────────────┐
         │   PostgreSQL (1 pod)  │
         │   Redis (1 pod)       │
         │   RabbitMQ (1 pod)    │
         └───────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Agent Workers        │
         │  (10-100 pods)        │
         │  Auto-scaling         │
         └───────────────────────┘
```

## 📦 Компоненты

### Основные сервисы

| Файл | Компонент | Назначение | Реплики |
|------|-----------|------------|---------|
| `01-namespace.yaml` | Namespace | Изоляция ресурсов | - |
| `02-configmap.yaml` | ConfigMap | Конфигурация платформы | - |
| `03-secrets.yaml` | Secrets | Чувствительные данные | - |
| `04-storage.yaml` | PVC | Постоянное хранилище | - |
| `05-postgres.yaml` | PostgreSQL | База данных | 1 |
| `06-redis.yaml` | Redis | Кэш и сессии | 1 |
| `07-rabbitmq.yaml` | RabbitMQ | Message broker | 1 |
| `08-registry-service.yaml` | Registry | Реестр агентов | 3-10 |
| `09-marketplace-service.yaml` | Marketplace | Marketplace агентов | 3-10 |
| `10-orchestrator-service.yaml` | Orchestrator | Оркестрация задач | 5-20 |
| `11-agent-sandbox.yaml` | Agent Workers | Выполнение задач | 10-100 |
| `12-api-gateway-ingress.yaml` | API Gateway | Точка входа | 3-15 |
| `13-monitoring.yaml` | Monitoring | Метрики и алерты | 1 |

### Инфраструктурные компоненты

- **PostgreSQL**: Хранение данных агентов, задач, пользователей
- **Redis**: Кэширование, rate limiting, сессии
- **RabbitMQ**: Очередь задач для агентов
- **Jaeger**: Distributed tracing

## 📋 Требования

### Kubernetes Cluster

- **Версия**: Kubernetes 1.25+
- **Узлы**: Минимум 3 worker nodes
- **CPU**: 16+ cores всего
- **RAM**: 32GB+ всего
- **Storage**: 200GB+ для PersistentVolumes

### Дополнительные компоненты

```bash
# NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Cert-Manager (для TLS сертификатов)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Prometheus Operator (для мониторинга)
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.68.0/bundle.yaml

# Kagent (для AI Agents)
kubectl apply -f https://github.com/kagent-dev/kagent/releases/latest/download/kagent.yaml
```

### StorageClass

Убедитесь, что в кластере есть подходящий StorageClass:

```bash
kubectl get storageclass

# Если нет, создайте (пример для локального развертывания):
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
EOF
```

## 🚀 Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone <repository-url>
cd info40/k8s
```

### 2. Настроить секреты

**ВАЖНО**: Измените пароли и API ключи в `03-secrets.yaml`:

```bash
# Создайте копию для редактирования
cp 03-secrets.yaml 03-secrets.local.yaml

# Отредактируйте файл (замените все CHANGE_ME)
nano 03-secrets.local.yaml
```

### 3. Настроить Ingress

Отредактируйте `12-api-gateway-ingress.yaml` и замените `agent-platform.example.com` на ваш домен:

```yaml
spec:
  tls:
  - hosts:
    - api.YOUR-DOMAIN.com
    - marketplace.YOUR-DOMAIN.com
```

### 4. Развернуть все компоненты

```bash
# Применить все манифесты в правильном порядке
kubectl apply -f 01-namespace.yaml
kubectl apply -f 02-configmap.yaml
kubectl apply -f 03-secrets.local.yaml  # Используйте локальную версию с секретами
kubectl apply -f 04-storage.yaml
kubectl apply -f 05-postgres.yaml
kubectl apply -f 06-redis.yaml
kubectl apply -f 07-rabbitmq.yaml

# Подождите пока БД будут готовы
kubectl wait --for=condition=ready pod -l app=postgres -n agent-platform --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n agent-platform --timeout=300s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n agent-platform --timeout=300s

# Разверните сервисы
kubectl apply -f 08-registry-service.yaml
kubectl apply -f 09-marketplace-service.yaml
kubectl apply -f 10-orchestrator-service.yaml
kubectl apply -f 11-agent-sandbox.yaml
kubectl apply -f 12-api-gateway-ingress.yaml
kubectl apply -f 13-monitoring.yaml
```

### 5. Проверить статус

```bash
# Проверить все поды
kubectl get pods -n agent-platform

# Проверить сервисы
kubectl get svc -n agent-platform

# Проверить Ingress
kubectl get ingress -n agent-platform

# Проверить логи
kubectl logs -f -n agent-platform -l app=api-gateway
```

## 📊 Развертывание

### Применить все манифесты одной командой

```bash
kubectl apply -f .
```

### Применить с помощью Kustomize

Создайте `kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: agent-platform

resources:
  - 01-namespace.yaml
  - 02-configmap.yaml
  - 03-secrets.yaml
  - 04-storage.yaml
  - 05-postgres.yaml
  - 06-redis.yaml
  - 07-rabbitmq.yaml
  - 08-registry-service.yaml
  - 09-marketplace-service.yaml
  - 10-orchestrator-service.yaml
  - 11-agent-sandbox.yaml
  - 12-api-gateway-ingress.yaml
  - 13-monitoring.yaml
```

Развернуть:

```bash
kubectl apply -k .
```

### Использование Helm (опционально)

Можно упаковать манифесты в Helm chart для более удобного управления.

## 🔧 Масштабирование

### Автоматическое масштабирование

Платформа использует HorizontalPodAutoscaler (HPA) для автоматического масштабирования:

- **Registry Service**: 3-10 pods
- **Marketplace Service**: 3-10 pods
- **Orchestrator Service**: 5-20 pods
- **Agent Workers**: 10-100 pods
- **API Gateway**: 3-15 pods

### Ручное масштабирование

```bash
# Увеличить количество воркеров
kubectl scale deployment agent-worker -n agent-platform --replicas=50

# Увеличить количество orchestrator-ов
kubectl scale deployment orchestrator-service -n agent-platform --replicas=10
```

### Масштабирование по метрикам

Agent Workers масштабируются по количеству сообщений в RabbitMQ:

```yaml
- type: External
  external:
    metric:
      name: rabbitmq_queue_messages
    target:
      type: AverageValue
      averageValue: "10"  # 1 pod на 10 задач
```

## 📈 Мониторинг

### Prometheus Metrics

Все сервисы экспортируют метрики на порт `9090-9092`:

```bash
# Port-forward для просмотра метрик
kubectl port-forward -n agent-platform svc/registry-service 9090:9090
curl http://localhost:9090/metrics
```

### Grafana Dashboard

Dashboard автоматически создается из ConfigMap `grafana-dashboard-agent-platform`.

Доступ к Grafana:

```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
# Откройте http://localhost:3000
```

### Jaeger Tracing

Distributed tracing для отладки:

```bash
kubectl port-forward -n agent-platform svc/jaeger-service 16686:16686
# Откройте http://localhost:16686
```

### Логи

```bash
# Логи всех сервисов
kubectl logs -f -n agent-platform -l component=core

# Логи конкретного сервиса
kubectl logs -f -n agent-platform -l app=orchestrator-service

# Логи воркеров
kubectl logs -f -n agent-platform -l app=agent-worker
```

### Алерты

Алерты настроены в `13-monitoring.yaml`:

- HighCPUUsage
- HighMemoryUsage
- ServiceDown
- DatabaseConnectionIssues
- TaskQueueBackup
- HighAgentFailureRate

## 🔒 Безопасность

### NetworkPolicy

Настроены политики для ограничения сетевого трафика:

- API Gateway может общаться только с core сервисами
- Core сервисы могут общаться с БД
- Agent workers изолированы в sandboxes

### RBAC

ServiceAccount и Role настроены для agent-worker:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: agent-worker-sa
```

### Secrets Management

**Для production**:

1. Используйте [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets):
```bash
kubeseal --format=yaml < 03-secrets.yaml > 03-secrets-sealed.yaml
```

2. Или используйте внешний Secret Manager:
   - AWS Secrets Manager
   - Google Secret Manager
   - HashiCorp Vault

### TLS/SSL

Ingress настроен на использование TLS с cert-manager:

```yaml
tls:
- hosts:
  - api.agent-platform.example.com
  secretName: tls-secret
```

## 🧪 Тестирование

### Проверка здоровья сервисов

```bash
# Health check всех сервисов
kubectl exec -it -n agent-platform deploy/api-gateway -- curl http://registry-service:8080/health
kubectl exec -it -n agent-platform deploy/api-gateway -- curl http://marketplace-service:8081/health
kubectl exec -it -n agent-platform deploy/api-gateway -- curl http://orchestrator-service:8082/health
```

### Тестовый запрос через API Gateway

```bash
# Port-forward
kubectl port-forward -n agent-platform svc/api-gateway 8000:8000

# Тест
curl http://localhost:8000/health
```

## 🔄 Обновление

### Rolling Update

```bash
# Обновить образ сервиса
kubectl set image deployment/registry-service -n agent-platform \
  registry-service=agent-platform/registry-service:v1.1.0

# Следить за обновлением
kubectl rollout status deployment/registry-service -n agent-platform
```

### Rollback

```bash
# Откатить обновление
kubectl rollout undo deployment/registry-service -n agent-platform

# Откатить на конкретную ревизию
kubectl rollout undo deployment/registry-service -n agent-platform --to-revision=2
```

## 🗑️ Удаление

```bash
# Удалить все ресурсы платформы
kubectl delete namespace agent-platform

# Или удалить по одному файлу
kubectl delete -f .
```

## 📚 Дополнительные ресурсы

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kagent Documentation](https://kagent.dev/docs)
- [Prometheus Operator](https://prometheus-operator.dev/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)

## 🐛 Troubleshooting

### Поды не запускаются

```bash
# Проверить события
kubectl get events -n agent-platform --sort-by='.lastTimestamp'

# Описать под
kubectl describe pod <pod-name> -n agent-platform

# Логи
kubectl logs <pod-name> -n agent-platform
```

### PVC не создаются

```bash
# Проверить StorageClass
kubectl get storageclass

# Проверить PVC
kubectl get pvc -n agent-platform

# Описать PVC
kubectl describe pvc <pvc-name> -n agent-platform
```

### База данных недоступна

```bash
# Проверить статус PostgreSQL
kubectl get pods -n agent-platform -l app=postgres

# Подключиться к PostgreSQL
kubectl exec -it -n agent-platform deploy/postgres -- psql -U platform_admin -d agent_platform

# Проверить логи
kubectl logs -n agent-platform -l app=postgres
```

---

**Готово к развертыванию!** 🚀

Для production убедитесь, что:
- ✅ Изменены все пароли и секреты
- ✅ Настроен мониторинг и алерты
- ✅ Настроены бэкапы БД
- ✅ Настроен SSL/TLS
- ✅ Проведено нагрузочное тестирование
