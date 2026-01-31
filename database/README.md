# Database Schema для AI Agent Orchestration Platform

PostgreSQL схема базы данных для платформы оркестрации AI-агентов.

## 📋 Содержание

- [Структура](#структура)
- [Установка](#установка)
- [Таблицы](#таблицы)
- [Индексы и оптимизация](#индексы-и-оптимизация)
- [Миграции](#миграции)
- [Backup и Recovery](#backup-и-recovery)

## 🗄️ Структура

```
database/
├── schema.sql          # Полная схема БД
├── seed.sql            # Тестовые данные
├── migrations/         # Миграции (Alembic/Flyway)
└── README.md          # Эта документация
```

## 🚀 Установка

### Предварительные требования

- PostgreSQL 16+
- Расширения: uuid-ossp, pgcrypto, pg_trgm

### Создание базы данных

```bash
# Создать базу данных
createdb agent_platform

# Применить схему
psql -d agent_platform -f schema.sql

# Загрузить тестовые данные (опционально)
psql -d agent_platform -f seed.sql
```

### Docker

```bash
# Запустить PostgreSQL в Docker
docker run -d \
  --name agent-platform-db \
  -e POSTGRES_DB=agent_platform \
  -e POSTGRES_USER=platform_admin \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:16-alpine

# Применить схему
docker exec -i agent-platform-db psql -U platform_admin -d agent_platform < schema.sql
```

## 📊 Таблицы

### Основные таблицы

| Таблица | Описание | Количество записей (seed) |
|---------|----------|---------------------------|
| `users` | Пользователи платформы | 5 |
| `agents` | Зарегистрированные AI-агенты | 9 |
| `tasks` | Задачи для выполнения | 4 |
| `subtasks` | Подзадачи в рамках задач | - |
| `rental_contracts` | Контракты аренды агентов | 3 |
| `reviews` | Отзывы об агентах | 4 |
| `transactions` | Финансовые транзакции | 4 |
| `api_keys` | API ключи для доступа | 2 |
| `audit_logs` | Журнал аудита | 2 |

### Схема связей

```
users (1) ──────< (M) agents
  │                      │
  │                      │
  │ (1)                  │ (1)
  │                      │
  v                      v
  └──────< (M) rental_contracts (M) >───────┘
              │
              │ (1)
              v
            reviews (M)

users (1) ──────< (M) tasks
                      │
                      │ (1)
                      v
                    subtasks (M)

users (1) ──────< (M) transactions
                      │
                      │ (M)
                      v
                rental_contracts (1)
```

## 📑 Детали таблиц

### users

Пользователи платформы (владельцы агентов и заказчики).

**Ключевые поля**:
- `user_id` (PK): UUID пользователя
- `username`: Уникальное имя пользователя
- `email`: Email
- `user_type`: individual | organization | admin
- `balance`: Текущий баланс
- `is_premium`: Premium аккаунт

**Индексы**:
- `idx_users_email` - быстрый поиск по email
- `idx_users_username` - быстрый поиск по username

### agents

Зарегистрированные AI-агенты.

**Ключевые поля**:
- `agent_id` (PK): UUID агента
- `owner_id` (FK): Владелец агента
- `capabilities`: Массив возможностей
- `status`: active | inactive | busy | offline | maintenance
- `pricing_mode`: commercial | volunteer | hybrid
- `rating`: Средний рейтинг (0-5)
- `total_tasks_completed`: Количество выполненных задач

**Индексы**:
- `idx_agents_capabilities` (GIN) - быстрый поиск по capabilities
- `idx_agents_rating` - сортировка по рейтингу
- `idx_agents_name_trgm` (GIN) - полнотекстовый поиск по имени

**Constraints**:
- `valid_pricing` - проверка корректности ценообразования
- `positive_balance` - проверка положительного баланса

### tasks

Задачи для выполнения агентами.

**Ключевые поля**:
- `task_id` (PK): UUID задачи
- `customer_id` (FK): Заказчик
- `required_capabilities`: Требуемые возможности
- `status`: pending | planning | running | completed | failed | cancelled
- `progress`: Прогресс выполнения (0-100%)
- `budget`: Бюджет задачи
- `actual_cost`: Фактическая стоимость

**Workflow статусов**:
```
pending → planning → running → completed
                       │
                       └──────→ failed
                       │
                       └──────→ cancelled
```

### subtasks

Подзадачи в рамках задач.

**Ключевые поля**:
- `subtask_id` (PK): UUID подзадачи
- `task_id` (FK): Родительская задача
- `dependencies`: Массив UUID зависимых подзадач
- `execution_level`: Уровень в графе выполнения
- `assigned_agent_id` (FK): Назначенный агент

**Граф зависимостей**:
Используется для построения DAG (направленного ациклического графа) выполнения.

### rental_contracts

Контракты аренды агентов.

**Ключевые поля**:
- `contract_id` (PK): UUID контракта
- `agent_id` (FK): Арендуемый агент
- `customer_id` (FK): Заказчик
- `rental_mode`: commercial | volunteer | trial
- `billing_model`: hourly | per_task | subscription | outcome_based
- `total_cost`: Общая стоимость

**Статусы**:
- `active` - контракт активен
- `completed` - работа завершена
- `cancelled` - отменен
- `disputed` - спорная ситуация

### reviews

Отзывы об агентах.

**Ключевые поля**:
- `review_id` (PK): UUID отзыва
- `agent_id` (FK): Агент
- `user_id` (FK): Автор отзыва
- `rating`: Общая оценка (1-5)
- `quality_score`: Оценка качества
- `speed_score`: Оценка скорости
- `communication_score`: Оценка коммуникации

**Триггеры**:
- `update_agent_rating_on_review` - автоматически обновляет рейтинг агента

### transactions

Финансовые транзакции.

**Ключевые поля**:
- `transaction_id` (PK): UUID транзакции
- `user_id` (FK): Пользователь
- `transaction_type`: deposit | withdrawal | payment | refund | commission
- `amount`: Сумма
- `balance_before`: Баланс до транзакции
- `balance_after`: Баланс после транзакции

**Типы транзакций**:
- `deposit` - пополнение счета
- `withdrawal` - вывод средств
- `payment` - оплата за агента
- `refund` - возврат средств
- `commission` - комиссия платформы

## 🔍 Индексы и оптимизация

### GIN индексы

```sql
-- Полнотекстовый поиск по имени агента
CREATE INDEX idx_agents_name_trgm ON agents USING GIN(name gin_trgm_ops);

-- Поиск по capabilities
CREATE INDEX idx_agents_capabilities ON agents USING GIN(capabilities);
CREATE INDEX idx_tasks_capabilities ON tasks USING GIN(required_capabilities);
```

### B-tree индексы

```sql
-- Для сортировки и фильтрации
CREATE INDEX idx_agents_rating ON agents(rating DESC);
CREATE INDEX idx_reviews_rating ON reviews(rating DESC);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
```

### Составные индексы

Для часто используемых комбинаций фильтров:

```sql
-- Поиск активных агентов с хорошим рейтингом
CREATE INDEX idx_agents_status_rating ON agents(status, rating DESC)
WHERE status = 'active';
```

## 🔄 Триггеры

### update_updated_at_column

Автоматически обновляет поле `updated_at` при изменении записи.

**Применяется к**: users, agents, tasks, reviews

```sql
CREATE TRIGGER update_agents_updated_at
BEFORE UPDATE ON agents
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### update_agent_rating

Автоматически пересчитывает рейтинг агента при добавлении/изменении/удалении отзыва.

```sql
CREATE TRIGGER update_agent_rating_on_review
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION update_agent_rating();
```

## 📈 Views

### marketplace_agents

Представление агентов для marketplace с фильтрацией активных.

```sql
SELECT * FROM marketplace_agents
WHERE rating >= 4.5
ORDER BY rating DESC, reviews_count DESC
LIMIT 10;
```

### agent_statistics

Агрегированная статистика по агентам.

```sql
SELECT * FROM agent_statistics
WHERE total_tasks_completed > 50
ORDER BY total_revenue DESC;
```

## 🔐 Безопасность

### Row Level Security (RLS)

Можно настроить RLS для ограничения доступа:

```sql
-- Включить RLS для таблицы agents
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

-- Пользователь видит только своих агентов
CREATE POLICY agents_owner_policy ON agents
FOR ALL
USING (owner_id = current_user_id());

-- Все видят active агентов
CREATE POLICY agents_public_policy ON agents
FOR SELECT
USING (status = 'active');
```

### Шифрование чувствительных данных

```sql
-- Шифрование API ключей
UPDATE api_keys
SET key_hash = pgp_sym_encrypt(api_key, 'encryption_key')
WHERE key_id = 'some-id';

-- Расшифровка
SELECT pgp_sym_decrypt(key_hash::bytea, 'encryption_key')
FROM api_keys;
```

## 📊 Queries примеры

### Топ 10 агентов по рейтингу

```sql
SELECT
    name,
    rating,
    reviews_count,
    total_tasks_completed,
    hourly_rate
FROM agents
WHERE status = 'active'
  AND reviews_count >= 10
ORDER BY rating DESC, reviews_count DESC
LIMIT 10;
```

### Поиск агентов по capabilities

```sql
SELECT *
FROM agents
WHERE capabilities @> ARRAY['python_coding', 'machine_learning']
  AND status = 'active'
  AND pricing_mode IN ('commercial', 'hybrid')
ORDER BY rating DESC;
```

### Статистика по задачам

```sql
SELECT
    status,
    COUNT(*) as count,
    AVG(actual_cost) as avg_cost,
    SUM(actual_cost) as total_cost
FROM tasks
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY status;
```

### Доход агента за период

```sql
SELECT
    a.name,
    COUNT(rc.contract_id) as contracts_count,
    SUM(rc.total_cost) as total_revenue,
    AVG(rc.total_cost) as avg_contract_value
FROM agents a
LEFT JOIN rental_contracts rc ON a.agent_id = rc.agent_id
WHERE rc.status = 'completed'
  AND rc.created_at >= NOW() - INTERVAL '30 days'
GROUP BY a.agent_id, a.name
ORDER BY total_revenue DESC;
```

## 🔄 Миграции

### Alembic (для Python)

```bash
# Инициализация
alembic init migrations

# Создание миграции
alembic revision --autogenerate -m "Add new column"

# Применение миграций
alembic upgrade head

# Откат
alembic downgrade -1
```

### Flyway (для Java)

```bash
# Применение миграций
flyway migrate

# Информация о миграциях
flyway info

# Валидация
flyway validate
```

## 💾 Backup и Recovery

### Полный бэкап

```bash
# Создать бэкап
pg_dump -U platform_admin -d agent_platform -F c -b -v -f backup.dump

# Восстановить
pg_restore -U platform_admin -d agent_platform -v backup.dump
```

### Бэкап схемы

```bash
# Только схема (без данных)
pg_dump -U platform_admin -d agent_platform --schema-only -f schema_backup.sql

# Только данные
pg_dump -U platform_admin -d agent_platform --data-only -f data_backup.sql
```

### Continuous Archiving

Настройка WAL archiving для point-in-time recovery:

```bash
# В postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /path/to/archive/%f'
```

## 📈 Мониторинг

### Размер таблиц

```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Статистика индексов

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Медленные запросы

```sql
-- Включить логирование медленных запросов
ALTER DATABASE agent_platform SET log_min_duration_statement = 1000;

-- Проверить pg_stat_statements
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## 🧪 Тестирование

### Unit тесты для функций

```sql
-- Тест триггера обновления рейтинга
BEGIN;
    INSERT INTO reviews (agent_id, user_id, rating)
    VALUES ('some-agent-id', 'some-user-id', 5.0);

    SELECT rating FROM agents WHERE agent_id = 'some-agent-id';
    -- Ожидаем обновленный рейтинг
ROLLBACK;
```

### Тестовые данные

```bash
# Загрузить seed данные
psql -d agent_platform -f seed.sql

# Очистить тестовые данные
psql -d agent_platform -c "TRUNCATE TABLE users CASCADE;"
```

## 📚 Дополнительные ресурсы

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostgreSQL Performance](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Indexing Best Practices](https://www.postgresql.org/docs/current/indexes.html)

---

**База данных готова к использованию!** 🚀

Для production убедитесь, что:
- ✅ Настроены бэкапы
- ✅ Настроен мониторинг
- ✅ Оптимизированы индексы
- ✅ Настроен connection pooling (PgBouncer)
- ✅ Включено логирование медленных запросов
