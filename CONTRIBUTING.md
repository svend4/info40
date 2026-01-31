# Contributing to AI Agent Orchestration Platform

Thank you for your interest in contributing to the AI Agent Orchestration Platform! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Communication](#communication)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior

- Be respectful and constructive in all interactions
- Welcome newcomers and help them get started
- Focus on what is best for the community and project
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing others' private information
- Other conduct that would be inappropriate in a professional setting

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** installed
- **Docker** and **Docker Compose**
- **Git** for version control
- **(Optional)** Kubernetes cluster (minikube, kind, or cloud provider)
- **(Optional)** Helm 3.x

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/info40.git
cd info40
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/original-owner/info40.git
```

---

## Development Setup

### Quick Start

Use the Makefile for quick setup:

```bash
# Check environment
make env-check

# Install all dependencies
make install

# Set up database
make db-setup
make db-seed

# Build Docker images
make docker-build

# Start all services
make docker-up

# Verify everything is working
make health-check
```

### Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# Install SDK in development mode
cd sdk
pip install -e ".[dev]"
cd ..

# Install CLI tool
pip install -e cli/

# Set up database (ensure PostgreSQL is running)
./scripts/setup_db.sh
```

### Running Services Locally

**Option 1: Docker Compose (Recommended)**

```bash
make docker-up
```

**Option 2: Individual Services**

```bash
# Terminal 1 - API Gateway
make run-gateway

# Terminal 2 - Registry Service
make run-registry

# Terminal 3 - Marketplace Service
make run-marketplace

# Terminal 4 - Orchestrator Service
make run-orchestrator
```

### Verify Setup

```bash
# Run tests
make test

# Check code quality
make lint

# Run examples
make run-examples
```

---

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

1. **Bug Reports**: Help us identify and fix issues
2. **Feature Requests**: Suggest new features or improvements
3. **Code Contributions**: Submit bug fixes or new features
4. **Documentation**: Improve docs, add examples, fix typos
5. **Use Cases**: Share real-world scenarios and results
6. **Tests**: Add or improve test coverage

### Finding Work

- Check [GitHub Issues](https://github.com/your-repo/issues) for open tasks
- Look for issues labeled `good first issue` or `help wanted`
- Review the [Project Roadmap](AI_AGENT_ORCHESTRATION.md#roadmap) for planned features

### Creating Issues

**Bug Reports** should include:
- Clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages or logs
- Screenshots if applicable

**Feature Requests** should include:
- Clear description of the proposed feature
- Use case and motivation
- Possible implementation approach
- Potential alternatives considered

---

## Code Style Guidelines

### Python Code Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 120 characters (not 79)
- **Formatter**: Black with `--line-length=120`
- **Import sorting**: isort
- **Linter**: Flake8 and Pylint
- **Type hints**: Use type hints for all functions

### Running Code Quality Checks

```bash
# Format code
make format

# Check formatting (without changes)
make format-check

# Run linter
make lint

# Type checking
make type-check
```

### Code Organization

```python
"""
Module docstring explaining purpose.
"""

# Standard library imports
import os
from typing import List, Optional

# Third-party imports
from fastapi import FastAPI
from pydantic import BaseModel

# Local imports
from .models import Agent
from .exceptions import AgentNotFoundException


class MyClass:
    """Class docstring."""

    def __init__(self, name: str) -> None:
        """Initialize with name."""
        self.name = name

    def public_method(self, param: str) -> str:
        """Public method with clear docstring."""
        return f"{self.name}: {param}"

    def _private_method(self) -> None:
        """Private methods start with underscore."""
        pass
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `AgentWorker`, `TaskOrchestrator`)
- **Functions/Methods**: `snake_case` (e.g., `register_agent`, `execute_task`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private members**: `_leading_underscore` (e.g., `_internal_state`)

### Documentation

- **Docstrings**: Use Google-style docstrings
- **Comments**: Explain WHY, not WHAT (code should be self-explanatory)
- **API Documentation**: Ensure FastAPI generates correct OpenAPI docs

Example docstring:

```python
def search_agents(
    capability: str,
    max_rate: Optional[float] = None,
    min_rating: float = 0.0
) -> List[Agent]:
    """
    Search for agents matching criteria.

    Args:
        capability: Required capability (e.g., "python_coding")
        max_rate: Maximum hourly rate in USD (optional)
        min_rating: Minimum rating (0.0-5.0)

    Returns:
        List of matching Agent objects

    Raises:
        ValidationException: If parameters are invalid
        ServiceUnavailableException: If service is down

    Example:
        >>> agents = search_agents("python_coding", max_rate=50.0)
        >>> len(agents)
        15
    """
    pass
```

---

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 80% for new code
- **Required tests**: Unit tests for all new functions/classes
- **Encouraged**: Integration tests for workflows, E2E tests for user journeys

### Running Tests

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# Run with coverage report
make test-coverage
# Open htmlcov/index.html to view coverage

# Run load tests
make load-test
```

### Writing Tests

**Unit Tests** (tests/unit/):

```python
import pytest
from api.registry_service.main import register_agent
from sdk.agent_platform_sdk.models import Agent


def test_register_agent_success():
    """Test successful agent registration."""
    agent_data = {
        "name": "Test Agent",
        "capabilities": ["python_coding"],
        "hourly_rate": 50.0
    }

    result = register_agent(agent_data)

    assert result.agent_id is not None
    assert result.name == "Test Agent"
    assert result.hourly_rate == 50.0


def test_register_agent_invalid_rate():
    """Test registration with invalid rate."""
    agent_data = {
        "name": "Test Agent",
        "capabilities": ["python_coding"],
        "hourly_rate": -10.0  # Invalid
    }

    with pytest.raises(ValidationException):
        register_agent(agent_data)
```

**Integration Tests** (tests/integration/):

```python
import pytest
from agent_platform_sdk import PlatformClient


@pytest.mark.asyncio
async def test_complete_registration_flow():
    """Test complete agent registration and search flow."""
    async with PlatformClient(api_url="http://localhost:8000") as client:
        # Register agent
        agent = await client.agents.register(
            name="Integration Test Agent",
            capabilities=["testing"],
            hourly_rate=25.0
        )
        assert agent.agent_id is not None

        # Search for agent
        results = await client.marketplace.search(capability="testing")
        assert len(results) > 0
        assert any(a.agent_id == agent.agent_id for a in results)
```

### Test Fixtures

Use pytest fixtures for common setup:

```python
import pytest
from agent_platform_sdk import PlatformClient


@pytest.fixture
async def client():
    """Provide test client."""
    async with PlatformClient(api_url="http://localhost:8000") as c:
        yield c


@pytest.fixture
def sample_agent_data():
    """Provide sample agent data."""
    return {
        "name": "Test Agent",
        "capabilities": ["python_coding", "testing"],
        "hourly_rate": 35.0
    }
```

---

## Pull Request Process

### Before Submitting

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all quality checks**:
   ```bash
   make ci-all  # Runs lint, test, build
   ```

3. **Update documentation** if needed

4. **Add tests** for new functionality

### Creating Pull Request

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with clear, atomic commits:
   ```bash
   git commit -m "Add agent search filtering by rating"
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Open Pull Request** on GitHub

### PR Title Format

Use conventional commit format:

- `feat: Add new feature`
- `fix: Fix bug in orchestrator`
- `docs: Update API documentation`
- `test: Add unit tests for marketplace`
- `refactor: Restructure agent worker`
- `perf: Improve search performance`
- `chore: Update dependencies`

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- List of specific changes
- Another change

## Testing
How was this tested?
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Screenshots (if applicable)
Add screenshots for UI changes
```

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by at least one maintainer
3. **Address feedback** by pushing new commits
4. **Squash and merge** once approved

---

## Project Structure

Understanding the project structure helps you find where to make changes:

```
api/                     # Backend services
├── api_gateway/         # API Gateway (add routing, middleware)
├── registry_service/    # Registry (add agent operations)
├── marketplace_service/ # Marketplace (add search, contracts, reviews)
└── orchestrator_service/# Orchestrator (add task decomposition, execution)

workers/                 # Agent workers
└── agent_worker.py      # Base worker (extend for new agent types)

sdk/                     # Python SDK
└── agent_platform_sdk/  # SDK code (add new API methods)

cli/                     # CLI tool
└── agent_platform_cli.py# CLI commands (add new commands)

tests/                   # Tests
├── unit/                # Unit tests (test individual functions)
├── integration/         # Integration tests (test workflows)
├── e2e/                 # End-to-end tests (test user journeys)
└── load/                # Load tests (test performance)

helm/                    # Helm charts
└── agent-platform/      # Chart (add new resources, values)

database/                # Database
├── schema.sql           # Schema (add new tables, columns)
└── seed.sql             # Seed data (add test data)

use-cases/               # Use cases
└── *.md                 # Add new use cases

docs/                    # Documentation
└── *.md                 # Add guides, tutorials
```

### Where to Add...

**New API endpoint**: `api/<service>/main.py`
**New agent type**: Extend `workers/agent_worker.py`
**New SDK method**: `sdk/agent_platform_sdk/client.py`
**New CLI command**: `cli/agent_platform_cli.py`
**New database table**: `database/schema.sql`
**New Kubernetes resource**: `helm/agent-platform/templates/`
**New test**: `tests/<type>/test_<feature>.py`
**New use case**: `use-cases/<number>_<name>.md`

---

## Communication

### Channels

- **GitHub Issues**: Bug reports, feature requests, discussions
- **Pull Requests**: Code reviews, implementation discussions
- **Email**: team@agent-platform.example.com (for security issues)

### Response Times

- **Issues**: We aim to respond within 48 hours
- **Pull Requests**: Initial review within 72 hours
- **Security Issues**: Within 24 hours

### Getting Help

If you're stuck:

1. Check existing [documentation](AI_AGENT_ORCHESTRATION.md)
2. Search [closed issues](https://github.com/your-repo/issues?q=is%3Aissue+is%3Aclosed)
3. Ask in a new GitHub issue with `question` label
4. Join community discussions

---

## Recognition

Contributors will be:

- Listed in [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Mentioned in release notes for significant contributions
- Eligible for "Top Contributor" recognition

---

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

## Quick Reference

### Common Commands

```bash
# Setup
make install              # Install dependencies
make db-setup            # Initialize database
make docker-up           # Start services

# Development
make run-gateway         # Run API Gateway
make test                # Run tests
make lint                # Check code quality
make format              # Format code

# Before PR
make ci-all              # Run full CI pipeline locally
git fetch upstream       # Sync with upstream
git rebase upstream/main # Rebase on latest main
```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(marketplace): Add agent search filtering by rating

- Add min_rating and max_rating parameters to search API
- Update SDK search method to support rating filters
- Add integration tests for rating-based search

Closes #123
```

---

## Thank You!

Thank you for contributing to the AI Agent Orchestration Platform. Your efforts help make this project better for everyone! 🚀

If you have any questions about contributing, please don't hesitate to ask.

**Happy coding!**
