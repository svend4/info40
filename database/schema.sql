-- ============================================================================
-- AI Agent Orchestration Platform - Database Schema
-- PostgreSQL 16+
-- ============================================================================

-- Включаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Для полнотекстового поиска

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

-- Таблица пользователей
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),

    -- Типы пользователей
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('individual', 'organization', 'admin')),

    -- Статус аккаунта
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,

    -- Биллинг
    balance DECIMAL(10, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT positive_balance CHECK (balance >= 0)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Таблица API ключей
CREATE TABLE api_keys (
    key_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_name VARCHAR(100) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL, -- Первые символы для идентификации

    -- Права доступа
    scopes TEXT[] DEFAULT ARRAY['read'],

    -- Лимиты
    rate_limit_per_minute INTEGER DEFAULT 60,
    daily_quota INTEGER,

    -- Статус
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);

-- ============================================================================
-- AGENTS
-- ============================================================================

-- Таблица агентов
CREATE TABLE agents (
    agent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Основная информация
    name VARCHAR(100) NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',

    -- AI модель
    model VARCHAR(100) NOT NULL DEFAULT 'claude-sonnet-4.5',
    model_provider VARCHAR(50) NOT NULL DEFAULT 'anthropic',

    -- Capabilities
    capabilities TEXT[] NOT NULL,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Статус
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'busy', 'offline', 'maintenance')),

    -- Доступность
    availability_schedule VARCHAR(50) DEFAULT '24/7',
    max_concurrent_tasks INTEGER DEFAULT 1 CHECK (max_concurrent_tasks > 0),
    current_load INTEGER DEFAULT 0 CHECK (current_load >= 0),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),

    -- Pricing
    pricing_mode VARCHAR(20) NOT NULL CHECK (pricing_mode IN ('commercial', 'volunteer', 'hybrid')),
    billing_model VARCHAR(20) CHECK (billing_model IN ('hourly', 'per_task', 'subscription', 'outcome_based')),
    hourly_rate DECIMAL(10, 2),
    task_rate DECIMAL(10, 2),
    subscription_monthly DECIMAL(10, 2),
    volunteer_quota INTEGER DEFAULT 0 CHECK (volunteer_quota BETWEEN 0 AND 100),

    -- Метрики
    total_tasks_completed INTEGER DEFAULT 0,
    total_tasks_failed INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 4) DEFAULT 0.0 CHECK (success_rate BETWEEN 0 AND 1),
    avg_response_time INTEGER DEFAULT 0, -- в секундах
    avg_quality_score DECIMAL(3, 2) DEFAULT 0.0 CHECK (avg_quality_score BETWEEN 0 AND 5),

    -- Рейтинг
    rating DECIMAL(3, 2) DEFAULT 0.0 CHECK (rating BETWEEN 0 AND 5),
    reviews_count INTEGER DEFAULT 0,
    total_rating_sum DECIMAL(10, 2) DEFAULT 0.0,

    -- Технические детали
    api_endpoint VARCHAR(255),
    webhook_url VARCHAR(255),
    authentication JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_pricing CHECK (
        (pricing_mode = 'commercial' AND hourly_rate > 0) OR
        (pricing_mode = 'volunteer') OR
        (pricing_mode = 'hybrid' AND hourly_rate > 0 AND volunteer_quota > 0)
    )
);

CREATE INDEX idx_agents_owner_id ON agents(owner_id);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_capabilities ON agents USING GIN(capabilities);
CREATE INDEX idx_agents_pricing_mode ON agents(pricing_mode);
CREATE INDEX idx_agents_rating ON agents(rating DESC);
CREATE INDEX idx_agents_created_at ON agents(created_at);
CREATE INDEX idx_agents_name_trgm ON agents USING GIN(name gin_trgm_ops);

-- ============================================================================
-- TASKS & WORKFLOWS
-- ============================================================================

-- Таблица задач
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Основная информация
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    task_type VARCHAR(50) NOT NULL,

    -- Требования
    required_capabilities TEXT[] NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),

    -- Бюджет и время
    budget DECIMAL(10, 2),
    estimated_cost DECIMAL(10, 2),
    actual_cost DECIMAL(10, 2) DEFAULT 0.0,

    deadline TIMESTAMP WITH TIME ZONE,
    estimated_duration INTEGER, -- в секундах
    actual_duration INTEGER,

    -- Статус
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'planning', 'running', 'completed', 'failed', 'cancelled')),

    -- Прогресс
    progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    subtasks_total INTEGER DEFAULT 0,
    subtasks_completed INTEGER DEFAULT 0,

    -- Результат
    result JSONB,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_tasks_customer_id ON tasks(customer_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_capabilities ON tasks USING GIN(required_capabilities);

-- Таблица подзадач
CREATE TABLE subtasks (
    subtask_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    parent_subtask_id UUID REFERENCES subtasks(subtask_id) ON DELETE CASCADE,

    -- Информация
    description TEXT NOT NULL,
    required_capability VARCHAR(100) NOT NULL,

    -- Граф зависимостей
    dependencies UUID[] DEFAULT ARRAY[]::UUID[],
    execution_level INTEGER DEFAULT 0, -- уровень в графе выполнения

    -- Назначенный агент
    assigned_agent_id UUID REFERENCES agents(agent_id) ON DELETE SET NULL,

    -- Статус
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'assigned', 'running', 'completed', 'failed')),

    -- Результат
    result JSONB,
    error_message TEXT,

    -- Метрики
    estimated_time INTEGER,
    actual_time INTEGER,
    estimated_cost DECIMAL(10, 2),
    actual_cost DECIMAL(10, 2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_subtasks_task_id ON subtasks(task_id);
CREATE INDEX idx_subtasks_assigned_agent_id ON subtasks(assigned_agent_id);
CREATE INDEX idx_subtasks_status ON subtasks(status);

-- ============================================================================
-- MARKETPLACE & CONTRACTS
-- ============================================================================

-- Таблица контрактов аренды
CREATE TABLE rental_contracts (
    contract_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(task_id) ON DELETE SET NULL,

    -- Условия
    rental_mode VARCHAR(20) NOT NULL CHECK (rental_mode IN ('commercial', 'volunteer', 'trial')),
    billing_model VARCHAR(20) NOT NULL CHECK (billing_model IN ('hourly', 'per_task', 'subscription', 'outcome_based')),

    -- Цены
    rate DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
    total_cost DECIMAL(10, 2) DEFAULT 0.0,

    -- Время
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    total_time_seconds INTEGER DEFAULT 0,

    -- Статус
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled', 'disputed')),

    -- Оплата
    paid BOOLEAN DEFAULT FALSE,
    payment_id VARCHAR(255),

    -- Описание проекта (для волонтерских)
    task_description TEXT,
    project_name VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_contracts_agent_id ON rental_contracts(agent_id);
CREATE INDEX idx_contracts_customer_id ON rental_contracts(customer_id);
CREATE INDEX idx_contracts_status ON rental_contracts(status);
CREATE INDEX idx_contracts_created_at ON rental_contracts(created_at);

-- Таблица отзывов
CREATE TABLE reviews (
    review_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    contract_id UUID REFERENCES rental_contracts(contract_id) ON DELETE SET NULL,

    -- Оценка
    rating DECIMAL(3, 2) NOT NULL CHECK (rating BETWEEN 1 AND 5),

    -- Отзыв
    title VARCHAR(255),
    comment TEXT,

    -- Категории оценки
    quality_score DECIMAL(3, 2) CHECK (quality_score BETWEEN 0 AND 5),
    speed_score DECIMAL(3, 2) CHECK (speed_score BETWEEN 0 AND 5),
    communication_score DECIMAL(3, 2) CHECK (speed_score BETWEEN 0 AND 5),

    -- Тип задачи
    task_type VARCHAR(50),

    -- Статус
    is_verified BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT one_review_per_contract UNIQUE (user_id, contract_id)
);

CREATE INDEX idx_reviews_agent_id ON reviews(agent_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_rating ON reviews(rating DESC);
CREATE INDEX idx_reviews_created_at ON reviews(created_at DESC);

-- ============================================================================
-- BILLING & TRANSACTIONS
-- ============================================================================

-- Таблица транзакций
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    contract_id UUID REFERENCES rental_contracts(contract_id) ON DELETE SET NULL,

    -- Тип транзакции
    transaction_type VARCHAR(20) NOT NULL
        CHECK (transaction_type IN ('deposit', 'withdrawal', 'payment', 'refund', 'commission')),

    -- Сумма
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',

    -- Баланс
    balance_before DECIMAL(10, 2) NOT NULL,
    balance_after DECIMAL(10, 2) NOT NULL,

    -- Статус
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),

    -- Платежные данные
    payment_method VARCHAR(50),
    payment_provider VARCHAR(50),
    payment_id VARCHAR(255),

    -- Описание
    description TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,

    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_contract_id ON transactions(contract_id);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);

-- ============================================================================
-- AUDIT & LOGS
-- ============================================================================

-- Таблица аудита
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Кто
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    agent_id UUID REFERENCES agents(agent_id) ON DELETE SET NULL,

    -- Что
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,

    -- Детали
    old_values JSONB,
    new_values JSONB,

    -- Контекст
    ip_address INET,
    user_agent TEXT,

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_agent_id ON audit_logs(agent_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Функция обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Применяем триггер к таблицам
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функция обновления рейтинга агента
CREATE OR REPLACE FUNCTION update_agent_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE agents
    SET
        total_rating_sum = (
            SELECT COALESCE(SUM(rating), 0)
            FROM reviews
            WHERE agent_id = NEW.agent_id
        ),
        reviews_count = (
            SELECT COUNT(*)
            FROM reviews
            WHERE agent_id = NEW.agent_id
        ),
        rating = (
            SELECT COALESCE(AVG(rating), 0)
            FROM reviews
            WHERE agent_id = NEW.agent_id
        )
    WHERE agent_id = NEW.agent_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического обновления рейтинга
CREATE TRIGGER update_agent_rating_on_review
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION update_agent_rating();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Представление для marketplace
CREATE VIEW marketplace_agents AS
SELECT
    a.agent_id,
    a.name,
    a.description,
    a.capabilities,
    a.model,
    a.status,
    a.pricing_mode,
    a.hourly_rate,
    a.task_rate,
    a.rating,
    a.reviews_count,
    a.total_tasks_completed,
    a.success_rate,
    a.avg_response_time,
    u.username as owner_username,
    u.user_type as owner_type,
    a.created_at
FROM agents a
JOIN users u ON a.owner_id = u.user_id
WHERE a.status = 'active' AND a.deleted_at IS NULL
ORDER BY a.rating DESC, a.reviews_count DESC;

-- Представление для статистики агентов
CREATE VIEW agent_statistics AS
SELECT
    a.agent_id,
    a.name,
    a.total_tasks_completed,
    a.total_tasks_failed,
    a.success_rate,
    COUNT(DISTINCT rc.contract_id) as total_contracts,
    SUM(rc.total_cost) as total_revenue,
    AVG(r.rating) as avg_rating,
    COUNT(DISTINCT r.review_id) as total_reviews
FROM agents a
LEFT JOIN rental_contracts rc ON a.agent_id = rc.agent_id
LEFT JOIN reviews r ON a.agent_id = r.agent_id
GROUP BY a.agent_id, a.name, a.total_tasks_completed, a.total_tasks_failed, a.success_rate;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Создание системного пользователя
INSERT INTO users (user_id, username, email, password_hash, full_name, user_type, is_verified)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'system',
    'system@agent-platform.local',
    'SYSTEM_ACCOUNT',
    'System Account',
    'admin',
    true
);

-- ============================================================================
-- GRANTS (настройте под ваши нужды)
-- ============================================================================

-- Создание ролей
-- CREATE ROLE agent_platform_app;
-- CREATE ROLE agent_platform_readonly;

-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO agent_platform_app;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_platform_readonly;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO agent_platform_app;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'Пользователи платформы';
COMMENT ON TABLE agents IS 'Зарегистрированные AI-агенты';
COMMENT ON TABLE tasks IS 'Задачи для выполнения';
COMMENT ON TABLE subtasks IS 'Подзадачи в рамках задач';
COMMENT ON TABLE rental_contracts IS 'Контракты аренды агентов';
COMMENT ON TABLE reviews IS 'Отзывы об агентах';
COMMENT ON TABLE transactions IS 'Финансовые транзакции';
COMMENT ON TABLE audit_logs IS 'Журнал аудита действий';
