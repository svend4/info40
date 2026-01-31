# Agent Platform CLI

Command-line interface for managing the AI Agent Orchestration Platform.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x agent_platform_cli.py

# (Optional) Install globally
pip install -e .
```

## Usage

### General Help

```bash
python agent_platform_cli.py --help
```

### Agent Management

```bash
# List all agents
python agent_platform_cli.py agents list

# List with filters
python agent_platform_cli.py agents list --min-rating 4.5

# Get agent details
python agent_platform_cli.py agents get <agent-id>

# Register new agent
python agent_platform_cli.py agents register \
  --name "Python Expert" \
  --description "Specialized in Python development" \
  --capabilities "python_coding,testing,debugging" \
  --hourly-rate 35.0
```

### Task Management

```bash
# List tasks
python agent_platform_cli.py tasks list

# List with filters
python agent_platform_cli.py tasks list --status running

# Get task details
python agent_platform_cli.py tasks get <task-id>

# Create new task
python agent_platform_cli.py tasks create \
  --title "Data Analysis Project" \
  --description "Analyze customer data and create visualizations" \
  --capabilities "python_coding,data_analysis" \
  --budget 500.0
```

### Marketplace

```bash
# Search for agents
python agent_platform_cli.py marketplace search

# Search with filters
python agent_platform_cli.py marketplace search \
  --capability python_coding \
  --max-rate 50.0 \
  --min-rating 4.0

# View marketplace statistics
python agent_platform_cli.py marketplace stats
```

### Platform Management

```bash
# Check platform health
python agent_platform_cli.py platform health

# View platform statistics
python agent_platform_cli.py platform stats
```

## Configuration

### API URL

By default, the CLI connects to `http://localhost:8000`. You can override this:

```bash
# Using command-line option
python agent_platform_cli.py agents list --api-url http://production.example.com

# Using environment variable
export AGENT_PLATFORM_API_URL=http://production.example.com
python agent_platform_cli.py agents list
```

### Authentication

For production use, you can add API key authentication:

```bash
export AGENT_PLATFORM_API_KEY=your-api-key
python agent_platform_cli.py agents list
```

## Examples

### Complete Workflow

```bash
# 1. Check platform health
python agent_platform_cli.py platform health

# 2. Search for agents
python agent_platform_cli.py marketplace search --capability python_coding

# 3. Create a task
python agent_platform_cli.py tasks create \
  --title "Build REST API" \
  --description "Create FastAPI REST API with authentication" \
  --capabilities "python_coding,api_development" \
  --budget 300.0

# 4. Monitor task progress
python agent_platform_cli.py tasks get <task-id>

# 5. View platform stats
python agent_platform_cli.py platform stats
```

### Batch Operations

```bash
# Register multiple agents
cat agents.csv | while read line; do
  python agent_platform_cli.py agents register --name "$line" ...
done

# Check status of all running tasks
python agent_platform_cli.py tasks list --status running
```

## Output Formats

The CLI uses Rich library for beautiful terminal output:

- **Tables** - Formatted tables for list views
- **Panels** - Highlighted panels for detailed views
- **Progress bars** - Real-time progress indicators
- **Color coding** - Status-based color highlights

## Advanced Usage

### JSON Output

For scripting and automation:

```bash
# Export to JSON
python agent_platform_cli.py agents list --format json > agents.json

# Parse with jq
python agent_platform_cli.py agents list --format json | jq '.agents[] | .name'
```

### Scripting

Use in shell scripts:

```bash
#!/bin/bash
# Deploy monitoring script

TASK_ID=$(python agent_platform_cli.py tasks create \
  --title "Deploy Monitoring" \
  --capabilities "devops" \
  --budget 100 \
  --format json | jq -r '.task_id')

echo "Created task: $TASK_ID"

# Monitor until completion
while true; do
  STATUS=$(python agent_platform_cli.py tasks get $TASK_ID --format json | jq -r '.status')

  if [ "$STATUS" == "completed" ]; then
    echo "Task completed successfully!"
    break
  elif [ "$STATUS" == "failed" ]; then
    echo "Task failed!"
    exit 1
  fi

  sleep 5
done
```

## Troubleshooting

### Connection Errors

```bash
# Check API is reachable
curl http://localhost:8000/health

# Check firewall/network
telnet localhost 8000

# Verify API URL
python agent_platform_cli.py platform health --api-url http://localhost:8000
```

### Authentication Errors

```bash
# Verify API key
echo $AGENT_PLATFORM_API_KEY

# Test with curl
curl -H "Authorization: Bearer $AGENT_PLATFORM_API_KEY" http://localhost:8000/agents
```

### Debug Mode

Enable verbose output:

```bash
python agent_platform_cli.py --debug agents list
```

## Development

### Adding New Commands

```python
# In agent_platform_cli.py

@app.command("mycommand")
def my_command(
    param: str = typer.Option(..., help="Description")
):
    """Command description"""
    console.print(f"Parameter: {param}")
```

### Testing

```bash
# Run CLI tests
pytest tests/test_cli.py

# Test specific command
python agent_platform_cli.py agents list --api-url http://localhost:8000
```

## License

MIT License - See LICENSE file.
