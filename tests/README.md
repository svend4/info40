# Tests for AI Agent Orchestration Platform

Comprehensive test suite for the AI Agent Orchestration Platform.

## Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_registry_service.py
│   ├── test_marketplace_service.py
│   └── test_orchestrator_service.py
├── integration/             # Integration tests (with external services)
│   ├── test_orchestration_workflow.py
│   ├── test_database_operations.py
│   └── test_messaging.py
├── e2e/                     # End-to-end tests (full system)
│   └── test_complete_platform.py
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Test dependencies
└── README.md               # This file
```

## Test Categories

### Unit Tests

Fast, isolated tests that don't require external dependencies.

- **Registry Service**: Agent registration, discovery, management
- **Marketplace Service**: Agent search, rental contracts, reviews
- **Orchestrator Service**: Task decomposition, scheduling, execution
- **Billing Service**: Payments, transactions, pricing calculations

**Characteristics**:
- No database required (uses mocks)
- No external API calls
- Fast execution (<1s per test)
- Can run in parallel

### Integration Tests

Tests that verify interactions between components with real dependencies.

- **Database Operations**: PostgreSQL interactions
- **Cache Operations**: Redis caching
- **Message Queue**: RabbitMQ messaging
- **Complete Workflows**: Multi-service interactions

**Characteristics**:
- Requires test database (PostgreSQL)
- Requires Redis and RabbitMQ
- Moderate execution time (1-5s per test)
- Uses test fixtures for setup/teardown

### End-to-End Tests

Full system tests that verify complete user workflows.

- **User Journey**: From registration to task completion
- **Agent Workflow**: Registration, task execution, payment
- **Marketplace**: Search, rent, review cycle
- **Volunteer Workflow**: Non-commercial task handling

**Characteristics**:
- Requires all services running
- Requires complete infrastructure
- Slow execution (5-30s per test)
- Tests real API endpoints

## Setup

### Install Dependencies

```bash
# Install test dependencies
pip install -r requirements.txt

# Or install with development dependencies
pip install -r ../docker/requirements/base.txt
pip install -r requirements.txt
```

### Setup Test Database

```bash
# Create test database
createdb agent_platform_test

# Apply schema
psql -d agent_platform_test -f ../database/schema.sql

# Load test seed data (optional)
psql -d agent_platform_test -f ../database/seed.sql
```

### Setup Test Services (Docker)

```bash
# Start test services with Docker Compose
docker-compose -f docker-compose.test.yml up -d

# Services started:
# - PostgreSQL (port 5432)
# - Redis (port 6379)
# - RabbitMQ (port 5672)
```

## Running Tests

### Run All Tests

```bash
# Run entire test suite
pytest

# Run with coverage report
pytest --cov=src --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# End-to-end tests only
pytest tests/e2e/ -v
```

### Run Tests by Marker

```bash
# Run only fast unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run end-to-end tests
pytest -m e2e

# Run async tests
pytest -m asyncio

# Exclude slow tests
pytest -m "not slow"
```

### Run Specific Test File

```bash
# Run specific test file
pytest tests/unit/test_registry_service.py -v

# Run specific test class
pytest tests/unit/test_registry_service.py::TestAgentRegistration -v

# Run specific test method
pytest tests/unit/test_registry_service.py::TestAgentRegistration::test_register_agent_success -v
```

### Parallel Execution

```bash
# Run tests in parallel (faster)
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

## Test Configuration

### Environment Variables

Create a `.env.test` file:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agent_platform_test
POSTGRES_USER=postgres
POSTGRES_PASSWORD=test_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# API
API_BASE_URL=http://localhost:8000
TEST_API_KEY=test_key_12345

# Test settings
TEST_TIMEOUT=30
LOG_LEVEL=DEBUG
```

### Pytest Configuration

See `pytest.ini` for detailed configuration including:
- Test discovery patterns
- Coverage settings
- Markers
- Output options

## Coverage Reports

### Generate Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Coverage Targets

- **Overall**: >80% coverage
- **Critical paths**: >90% coverage
- **Edge cases**: Document why not covered

### View Coverage in Terminal

```bash
pytest --cov=src --cov-report=term-missing
```

## Writing New Tests

### Unit Test Template

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """Test client for API"""
    from main import app
    return TestClient(app)

class TestFeature:
    """Test description"""

    def test_basic_functionality(self, client):
        """Test basic case"""
        response = client.get("/endpoint")
        assert response.status_code == 200

    def test_error_handling(self, client):
        """Test error case"""
        response = client.get("/invalid")
        assert response.status_code == 404
```

### Integration Test Template

```python
import pytest
import psycopg2

@pytest.fixture
def db_connection():
    """Database connection"""
    conn = psycopg2.connect(
        dbname="agent_platform_test",
        user="postgres",
        password="test_password"
    )
    yield conn
    conn.close()

@pytest.mark.integration
def test_database_operation(db_connection):
    """Test database operation"""
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM agents")
    count = cursor.fetchone()[0]
    assert count >= 0
```

### Async Test Template

```python
import pytest
import aiohttp

@pytest.mark.asyncio
async def test_async_operation():
    """Test async operation"""
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/health") as response:
            assert response.status == 200
            data = await response.json()
            assert data["status"] == "healthy"
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests
- Nightly builds

See `.github/workflows/ci.yml` for configuration.

### Running CI Locally

```bash
# Run the same checks as CI
./scripts/run_ci_checks.sh

# Individual checks
black --check .
isort --check-only .
flake8 .
mypy src/
pytest
```

## Troubleshooting

### Tests Failing Locally

```bash
# Clean test database
dropdb agent_platform_test
createdb agent_platform_test
psql -d agent_platform_test -f ../database/schema.sql

# Clear Redis cache
redis-cli FLUSHALL

# Restart services
docker-compose -f docker-compose.test.yml restart
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection
psql -h localhost -U postgres -d agent_platform_test

# View PostgreSQL logs
docker logs agent-platform-test-db
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Clear Redis
redis-cli FLUSHALL
```

### Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install package in development mode
pip install -e .
```

## Performance Testing

### Load Testing with Locust

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open browser at http://localhost:8089
```

### Benchmarking

```bash
# Run benchmarks
pytest tests/benchmarks/ --benchmark-only

# Compare benchmarks
pytest tests/benchmarks/ --benchmark-compare
```

## Test Data

### Fixtures

Common test fixtures are defined in `conftest.py`:
- Database connections
- Redis clients
- Sample data generators
- Mock objects

### Factories

Use `factory_boy` for generating test data:

```python
from factory import Factory, Faker

class AgentFactory(Factory):
    class Meta:
        model = Agent

    name = Faker('company')
    capabilities = ['python_coding']
    pricing_mode = 'commercial'
    hourly_rate = Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Always clean up test data in teardown
3. **Naming**: Use descriptive test names (test_what_when_then)
4. **Assertions**: One logical assertion per test
5. **Mocking**: Mock external dependencies in unit tests
6. **Documentation**: Document complex test scenarios
7. **Performance**: Keep unit tests fast (<1s)
8. **Coverage**: Aim for >80% coverage
9. **Fixtures**: Reuse fixtures for common setup
10. **Markers**: Use markers to categorize tests

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain >80% coverage
4. Add integration tests for workflows
5. Update this README if needed

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Happy Testing!** 🧪
