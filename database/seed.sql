-- ============================================================================
-- Seed Data для AI Agent Orchestration Platform
-- Тестовые данные для development и демонстрации
-- ============================================================================

-- ============================================================================
-- USERS
-- ============================================================================

-- Тестовые пользователи
INSERT INTO users (username, email, password_hash, full_name, user_type, is_verified, is_premium, balance) VALUES
('alice_dev', 'alice@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5agyWdHJmLV/2', 'Alice Developer', 'individual', true, false, 1000.00),
('bob_researcher', 'bob@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5agyWdHJmLV/2', 'Bob Researcher', 'individual', true, true, 5000.00),
('techcorp', 'tech@corp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5agyWdHJmLV/2', 'TechCorp Inc', 'organization', true, true, 50000.00),
('opensource_foundation', 'oss@foundation.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5agyWdHJmLV/2', 'OpenSource Foundation', 'organization', true, false, 10000.00),
('student_maria', 'maria@university.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5agyWdHJmLV/2', 'Maria Student', 'individual', true, false, 100.00);

-- ============================================================================
-- AGENTS
-- ============================================================================

-- Python Coding Agents
INSERT INTO agents (
    owner_id,
    name,
    description,
    capabilities,
    model,
    status,
    pricing_mode,
    billing_model,
    hourly_rate,
    volunteer_quota,
    total_tasks_completed,
    success_rate,
    avg_response_time,
    rating,
    reviews_count
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'alice_dev'),
    'PythonMaster',
    'Expert in Python development, specializing in Django, FastAPI, and data processing',
    ARRAY['python_coding', 'code_review', 'debugging', 'unit_testing'],
    'claude-sonnet-4.5',
    'active',
    'hybrid',
    'hourly',
    30.00,
    20,
    156,
    0.95,
    420,
    4.8,
    42
),
(
    (SELECT user_id FROM users WHERE username = 'techcorp'),
    'EnterpriseCodeBot',
    'Enterprise-grade Python development with security focus',
    ARRAY['python_coding', 'security_audit', 'performance_optimization'],
    'claude-opus-4.5',
    'active',
    'commercial',
    'hourly',
    75.00,
    0,
    324,
    0.97,
    300,
    4.9,
    87
);

-- Data Science Agents
INSERT INTO agents (
    owner_id,
    name,
    description,
    capabilities,
    model,
    status,
    pricing_mode,
    billing_model,
    hourly_rate,
    volunteer_quota,
    total_tasks_completed,
    success_rate,
    avg_response_time,
    rating
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'bob_researcher'),
    'DataSciencePro',
    'Advanced data analysis, machine learning, and statistical modeling',
    ARRAY['data_analysis', 'machine_learning', 'visualization', 'statistical_modeling'],
    'claude-opus-4.5',
    'active',
    'hybrid',
    'hourly',
    45.00,
    30,
    89,
    0.92,
    600,
    4.6
),
(
    (SELECT user_id FROM users WHERE username = 'opensource_foundation'),
    'MLResearcher',
    'ML research for academic and open-source projects',
    ARRAY['machine_learning', 'research', 'paper_writing'],
    'claude-sonnet-4.5',
    'active',
    'volunteer',
    'hourly',
    0.00,
    100,
    67,
    0.89,
    900,
    4.7
);

-- Research & Writing Agents
INSERT INTO agents (
    owner_id,
    name,
    description,
    capabilities,
    model,
    status,
    pricing_mode,
    billing_model,
    task_rate,
    total_tasks_completed,
    success_rate,
    rating
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'alice_dev'),
    'ResearchBot',
    'Scientific research, literature review, and academic writing',
    ARRAY['research', 'fact_verification', 'scientific_writing', 'citation_management'],
    'claude-opus-4.5',
    'active',
    'hybrid',
    'per_task',
    50.00,
    112,
    0.97,
    4.9
),
(
    (SELECT user_id FROM users WHERE username = 'student_maria'),
    'ContentWriter',
    'Creative content writing and copywriting',
    ARRAY['writing', 'editing', 'copywriting', 'content_strategy'],
    'claude-sonnet-4.5',
    'active',
    'commercial',
    'per_task',
    25.00,
    234,
    0.88,
    4.5
);

-- Web Development Agents
INSERT INTO agents (
    owner_id,
    name,
    description,
    capabilities,
    model,
    status,
    pricing_mode,
    billing_model,
    hourly_rate,
    total_tasks_completed,
    success_rate,
    rating
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'techcorp'),
    'FullStackDev',
    'Full-stack web development (React, Node.js, PostgreSQL)',
    ARRAY['frontend_development', 'backend_development', 'database_design', 'devops'],
    'claude-opus-4.5',
    'active',
    'commercial',
    'hourly',
    85.00,
    178,
    0.91,
    4.7
),
(
    (SELECT user_id FROM users WHERE username = 'opensource_foundation'),
    'OpenSourceContributor',
    'Open-source web development and documentation',
    ARRAY['frontend_development', 'documentation', 'code_review'],
    'claude-sonnet-4.5',
    'active',
    'volunteer',
    'hourly',
    0.00,
    95,
    0.93,
    4.8
);

-- Specialized Agents
INSERT INTO agents (
    owner_id,
    name,
    description,
    capabilities,
    model,
    status,
    pricing_mode,
    billing_model,
    hourly_rate,
    total_tasks_completed,
    success_rate,
    rating
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'bob_researcher'),
    'BioinformaticsExpert',
    'Bioinformatics analysis and genomics',
    ARRAY['bioinformatics', 'genomics', 'data_analysis', 'scientific_computing'],
    'claude-opus-4.5',
    'active',
    'commercial',
    'hourly',
    90.00,
    34,
    0.94,
    5.0
),
(
    (SELECT user_id FROM users WHERE username = 'techcorp'),
    'SecurityAuditor',
    'Security auditing and penetration testing',
    ARRAY['security_audit', 'penetration_testing', 'vulnerability_assessment'],
    'claude-opus-4.5',
    'active',
    'commercial',
    'hourly',
    120.00,
    56,
    0.98,
    4.9
);

-- ============================================================================
-- TASKS
-- ============================================================================

-- Completed Tasks
INSERT INTO tasks (
    customer_id,
    title,
    description,
    task_type,
    required_capabilities,
    priority,
    budget,
    estimated_cost,
    actual_cost,
    status,
    progress,
    subtasks_total,
    subtasks_completed,
    created_at,
    started_at,
    completed_at
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'bob_researcher'),
    'Climate Change Data Analysis',
    'Analyze 10 years of climate data and produce visualizations',
    'data_analysis',
    ARRAY['data_analysis', 'visualization', 'scientific_writing'],
    'high',
    500.00,
    450.00,
    425.00,
    'completed',
    100,
    3,
    3,
    CURRENT_TIMESTAMP - INTERVAL '14 days',
    CURRENT_TIMESTAMP - INTERVAL '14 days',
    CURRENT_TIMESTAMP - INTERVAL '10 days'
),
(
    (SELECT user_id FROM users WHERE username = 'techcorp'),
    'E-commerce Backend Development',
    'Build REST API for e-commerce platform',
    'backend_development',
    ARRAY['backend_development', 'database_design', 'api_development'],
    'critical',
    3000.00,
    2800.00,
    2650.00,
    'completed',
    100,
    5,
    5,
    CURRENT_TIMESTAMP - INTERVAL '30 days',
    CURRENT_TIMESTAMP - INTERVAL '28 days',
    CURRENT_TIMESTAMP - INTERVAL '7 days'
);

-- Running Tasks
INSERT INTO tasks (
    customer_id,
    title,
    description,
    task_type,
    required_capabilities,
    priority,
    budget,
    estimated_cost,
    status,
    progress,
    subtasks_total,
    subtasks_completed,
    created_at,
    started_at
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'alice_dev'),
    'Machine Learning Model Development',
    'Develop and train ML model for image classification',
    'machine_learning',
    ARRAY['machine_learning', 'python_coding', 'data_analysis'],
    'high',
    1500.00,
    1200.00,
    'running',
    65,
    4,
    2,
    CURRENT_TIMESTAMP - INTERVAL '5 days',
    CURRENT_TIMESTAMP - INTERVAL '4 days'
);

-- Pending Tasks
INSERT INTO tasks (
    customer_id,
    title,
    description,
    task_type,
    required_capabilities,
    priority,
    budget,
    status,
    created_at
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'student_maria'),
    'Research Paper on AI Ethics',
    'Write comprehensive research paper on AI ethics and bias',
    'research',
    ARRAY['research', 'scientific_writing', 'fact_verification'],
    'normal',
    300.00,
    'pending',
    CURRENT_TIMESTAMP - INTERVAL '2 days'
);

-- ============================================================================
-- RENTAL CONTRACTS
-- ============================================================================

-- Completed Contracts
INSERT INTO rental_contracts (
    agent_id,
    customer_id,
    task_id,
    rental_mode,
    billing_model,
    rate,
    total_cost,
    start_time,
    end_time,
    total_time_seconds,
    status,
    paid
) VALUES
(
    (SELECT agent_id FROM agents WHERE name = 'DataSciencePro'),
    (SELECT user_id FROM users WHERE username = 'bob_researcher'),
    (SELECT task_id FROM tasks WHERE title = 'Climate Change Data Analysis'),
    'commercial',
    'hourly',
    45.00,
    425.00,
    CURRENT_TIMESTAMP - INTERVAL '14 days',
    CURRENT_TIMESTAMP - INTERVAL '10 days',
    34200, -- 9.5 hours
    'completed',
    true
),
(
    (SELECT agent_id FROM agents WHERE name = 'FullStackDev'),
    (SELECT user_id FROM users WHERE username = 'techcorp'),
    (SELECT task_id FROM tasks WHERE title = 'E-commerce Backend Development'),
    'commercial',
    'hourly',
    85.00,
    2650.00,
    CURRENT_TIMESTAMP - INTERVAL '28 days',
    CURRENT_TIMESTAMP - INTERVAL '7 days',
    112320, -- 31.2 hours
    'completed',
    true
);

-- Active Contracts
INSERT INTO rental_contracts (
    agent_id,
    customer_id,
    task_id,
    rental_mode,
    billing_model,
    rate,
    total_cost,
    start_time,
    total_time_seconds,
    status,
    paid
) VALUES
(
    (SELECT agent_id FROM agents WHERE name = 'MLResearcher'),
    (SELECT user_id FROM users WHERE username = 'alice_dev'),
    (SELECT task_id FROM tasks WHERE title = 'Machine Learning Model Development'),
    'volunteer',
    'hourly',
    0.00,
    0.00,
    CURRENT_TIMESTAMP - INTERVAL '4 days',
    57600, -- 16 hours
    'active',
    false
);

-- ============================================================================
-- REVIEWS
-- ============================================================================

INSERT INTO reviews (
    agent_id,
    user_id,
    contract_id,
    rating,
    title,
    comment,
    quality_score,
    speed_score,
    communication_score,
    task_type,
    is_verified
) VALUES
(
    (SELECT agent_id FROM agents WHERE name = 'DataSciencePro'),
    (SELECT user_id FROM users WHERE username = 'bob_researcher'),
    (SELECT contract_id FROM rental_contracts WHERE agent_id = (SELECT agent_id FROM agents WHERE name = 'DataSciencePro') LIMIT 1),
    5.0,
    'Excellent data analysis work!',
    'The agent provided comprehensive analysis with beautiful visualizations. Very professional and thorough.',
    5.0,
    4.5,
    5.0,
    'data_analysis',
    true
),
(
    (SELECT agent_id FROM agents WHERE name = 'FullStackDev'),
    (SELECT user_id FROM users WHERE username = 'techcorp'),
    (SELECT contract_id FROM rental_contracts WHERE agent_id = (SELECT agent_id FROM agents WHERE name = 'FullStackDev') LIMIT 1),
    4.7,
    'Great backend development',
    'Solid work on the API. Clean code and good documentation. Minor delays but overall excellent.',
    5.0,
    4.0,
    5.0,
    'backend_development',
    true
),
(
    (SELECT agent_id FROM agents WHERE name = 'PythonMaster'),
    (SELECT user_id FROM users WHERE username = 'alice_dev'),
    NULL,
    4.8,
    'Reliable Python expert',
    'Used this agent multiple times for Python projects. Always delivers quality code.',
    4.8,
    4.8,
    4.7,
    'python_coding',
    true
),
(
    (SELECT agent_id FROM agents WHERE name = 'ResearchBot'),
    (SELECT user_id FROM users WHERE username = 'bob_researcher'),
    NULL,
    4.9,
    'Outstanding research capabilities',
    'Best research agent I have used. Comprehensive literature review and accurate citations.',
    5.0,
    4.8,
    4.9,
    'research',
    true
);

-- ============================================================================
-- TRANSACTIONS
-- ============================================================================

-- Deposits
INSERT INTO transactions (
    user_id,
    transaction_type,
    amount,
    balance_before,
    balance_after,
    status,
    payment_method,
    description
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'alice_dev'),
    'deposit',
    1000.00,
    0.00,
    1000.00,
    'completed',
    'credit_card',
    'Initial deposit'
),
(
    (SELECT user_id FROM users WHERE username = 'techcorp'),
    'deposit',
    50000.00,
    0.00,
    50000.00,
    'completed',
    'bank_transfer',
    'Company account funding'
);

-- Payments
INSERT INTO transactions (
    user_id,
    contract_id,
    transaction_type,
    amount,
    balance_before,
    balance_after,
    status,
    description
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'bob_researcher'),
    (SELECT contract_id FROM rental_contracts WHERE agent_id = (SELECT agent_id FROM agents WHERE name = 'DataSciencePro') LIMIT 1),
    'payment',
    -425.00,
    5000.00,
    4575.00,
    'completed',
    'Payment for Climate Change Data Analysis'
),
(
    (SELECT user_id FROM users WHERE username = 'techcorp'),
    (SELECT contract_id FROM rental_contracts WHERE agent_id = (SELECT agent_id FROM agents WHERE name = 'FullStackDev') LIMIT 1),
    'payment',
    -2650.00,
    50000.00,
    47350.00,
    'completed',
    'Payment for E-commerce Backend Development'
);

-- ============================================================================
-- API KEYS
-- ============================================================================

INSERT INTO api_keys (
    user_id,
    key_hash,
    key_name,
    key_prefix,
    scopes,
    rate_limit_per_minute,
    daily_quota
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'alice_dev'),
    'hashed_key_alice_123',
    'Development Key',
    'apk_dev_',
    ARRAY['read', 'write'],
    100,
    10000
),
(
    (SELECT user_id FROM users WHERE username = 'techcorp'),
    'hashed_key_techcorp_456',
    'Production API Key',
    'apk_prod_',
    ARRAY['read', 'write', 'admin'],
    1000,
    100000
);

-- ============================================================================
-- AUDIT LOGS (samples)
-- ============================================================================

INSERT INTO audit_logs (
    user_id,
    action,
    resource_type,
    resource_id,
    ip_address,
    metadata
) VALUES
(
    (SELECT user_id FROM users WHERE username = 'alice_dev'),
    'agent.register',
    'agent',
    (SELECT agent_id FROM agents WHERE name = 'PythonMaster'),
    '192.168.1.100',
    '{"agent_name": "PythonMaster"}'::jsonb
),
(
    (SELECT user_id FROM users WHERE username = 'bob_researcher'),
    'task.create',
    'task',
    (SELECT task_id FROM tasks WHERE title = 'Climate Change Data Analysis'),
    '192.168.1.101',
    '{"task_title": "Climate Change Data Analysis"}'::jsonb
);

-- ============================================================================
-- STATISTICS
-- ============================================================================

-- Обновляем статистику агентов
UPDATE agents SET last_seen = CURRENT_TIMESTAMP WHERE status = 'active';

-- ============================================================================
-- Вывод статистики
-- ============================================================================

SELECT 'Database seeded successfully!' as status;
SELECT COUNT(*) as users FROM users;
SELECT COUNT(*) as agents FROM agents;
SELECT COUNT(*) as tasks FROM tasks;
SELECT COUNT(*) as contracts FROM rental_contracts;
SELECT COUNT(*) as reviews FROM reviews;
SELECT COUNT(*) as transactions FROM transactions;
