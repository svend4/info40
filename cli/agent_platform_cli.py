#!/usr/bin/env python3
"""
Agent Platform CLI

Command-line interface for managing the AI Agent Orchestration Platform

Installation:
    pip install typer requests rich

Usage:
    python agent_platform_cli.py --help
    python agent_platform_cli.py agents list
    python agent_platform_cli.py tasks create --title "My Task" --budget 100

Or install as script:
    chmod +x agent_platform_cli.py
    ./agent_platform_cli.py agents list
"""

import typer
import requests
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich.panel import Panel
from rich.progress import Progress
import json
from datetime import datetime, timedelta


# ============================================================================
# Configuration
# ============================================================================

app = typer.Typer(
    name="agent-platform",
    help="CLI for AI Agent Orchestration Platform",
    add_completion=False
)

console = Console()

# API endpoints
DEFAULT_API_URL = "http://localhost:8000"
API_URL = typer.get_app_dir("agent-platform")


# ============================================================================
# Agent Commands
# ============================================================================

agents_app = typer.Typer(help="Manage agents")
app.add_typer(agents_app, name="agents")


@agents_app.command("list")
def list_agents(
    page: int = typer.Option(1, help="Page number"),
    page_size: int = typer.Option(20, help="Items per page"),
    min_rating: Optional[float] = typer.Option(None, help="Minimum rating filter"),
    api_url: str = typer.Option(DEFAULT_API_URL, help="API base URL")
):
    """List all registered agents"""
    try:
        params = {"page": page, "page_size": page_size}
        if min_rating:
            params["min_rating"] = min_rating

        response = requests.get(f"{api_url}/registry/agents", params=params)
        response.raise_for_status()

        data = response.json()
        agents = data.get("agents", [])

        if not agents:
            console.print("[yellow]No agents found[/yellow]")
            return

        # Create table
        table = Table(title=f"Agents (Page {page})", show_header=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Capabilities", style="blue")
        table.add_column("Pricing", style="yellow")
        table.add_column("Rate", justify="right")
        table.add_column("Rating", justify="center")
        table.add_column("Tasks", justify="right")

        for agent in agents:
            capabilities = ", ".join(agent.get("capabilities", [])[:3])
            if len(agent.get("capabilities", [])) > 3:
                capabilities += "..."

            table.add_row(
                agent["agent_id"][:16] + "...",
                agent["name"],
                capabilities,
                agent["pricing_mode"],
                f"${agent['hourly_rate']}/hr",
                f"{agent['rating']:.1f}⭐",
                str(agent.get("total_tasks_completed", 0))
            )

        console.print(table)
        console.print(f"\n[dim]Total: {data.get('total', 0)} agents[/dim]")

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@agents_app.command("get")
def get_agent(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    api_url: str = typer.Option(DEFAULT_API_URL, help="API base URL")
):
    """Get detailed agent information"""
    try:
        response = requests.get(f"{api_url}/registry/agents/{agent_id}")
        response.raise_for_status()

        agent = response.json()

        # Display agent info in a panel
        info = f"""
[bold]Name:[/bold] {agent['name']}
[bold]Description:[/bold] {agent['description']}
[bold]Capabilities:[/bold] {', '.join(agent['capabilities'])}
[bold]Pricing Mode:[/bold] {agent['pricing_mode']}
[bold]Hourly Rate:[/bold] ${agent['hourly_rate']}
[bold]Rating:[/bold] {agent['rating']}⭐ ({agent.get('reviews_count', 0)} reviews)
[bold]Status:[/bold] {agent['status']}
[bold]Tasks Completed:[/bold] {agent.get('total_tasks_completed', 0)}
[bold]Success Rate:[/bold] {agent.get('success_rate', 0) * 100:.1f}%
[bold]Created:[/bold] {agent['created_at']}
        """

        console.print(Panel(info, title=f"Agent {agent_id[:16]}", border_style="green"))

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@agents_app.command("register")
def register_agent(
    name: str = typer.Option(..., prompt=True, help="Agent name"),
    description: str = typer.Option(..., prompt=True, help="Agent description"),
    capabilities: str = typer.Option(..., prompt=True, help="Capabilities (comma-separated)"),
    pricing_mode: str = typer.Option("commercial", help="Pricing mode"),
    hourly_rate: float = typer.Option(25.0, help="Hourly rate"),
    api_url: str = typer.Option(DEFAULT_API_URL, help="API base URL")
):
    """Register a new agent"""
    try:
        agent_data = {
            "name": name,
            "description": description,
            "capabilities": [c.strip() for c in capabilities.split(",")],
            "pricing_mode": pricing_mode,
            "hourly_rate": hourly_rate,
            "volunteer_percentage": 0 if pricing_mode == "commercial" else 100,
            "max_concurrent_tasks": 5,
            "supported_languages": ["en"],
            "metadata": {}
        }

        response = requests.post(f"{api_url}/registry/agents", json=agent_data)
        response.raise_for_status()

        agent = response.json()

        console.print(f"[green]✓[/green] Agent registered successfully!")
        console.print(f"[bold]Agent ID:[/bold] {agent['agent_id']}")

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# Task Commands
# ============================================================================

tasks_app = typer.Typer(help="Manage tasks")
app.add_typer(tasks_app, name="tasks")


@tasks_app.command("list")
def list_tasks(
    customer_id: Optional[str] = typer.Option(None, help="Filter by customer ID"),
    status: Optional[str] = typer.Option(None, help="Filter by status"),
    limit: int = typer.Option(20, help="Number of tasks to show"),
    api_url: str = typer.Option(DEFAULT_API_URL, help="API base URL")
):
    """List tasks"""
    try:
        params = {"limit": limit}
        if customer_id:
            params["customer_id"] = customer_id
        if status:
            params["status"] = status

        response = requests.get(f"{api_url}/orchestrator/tasks", params=params)
        response.raise_for_status()

        tasks = response.json()

        if not tasks:
            console.print("[yellow]No tasks found[/yellow]")
            return

        # Create table
        table = Table(title="Tasks", show_header=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Progress", justify="right")
        table.add_column("Budget", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Created", style="dim")

        for task in tasks:
            # Color-code status
            status_color = {
                "pending": "yellow",
                "planning": "blue",
                "running": "cyan",
                "completed": "green",
                "failed": "red"
            }.get(task["status"], "white")

            table.add_row(
                task["task_id"][:16] + "...",
                task["title"][:30],
                f"[{status_color}]{task['status']}[/{status_color}]",
                f"{task['progress']:.0f}%",
                f"${task['budget']:.2f}",
                f"${task['actual_cost']:.2f}",
                task["created_at"][:10]
            )

        console.print(table)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@tasks_app.command("get")
def get_task(
    task_id: str = typer.Argument(..., help="Task ID"),
    api_url: str = typer.Option(DEFAULT_API_URL, help="API base URL")
):
    """Get detailed task information"""
    try:
        response = requests.get(f"{api_url}/orchestrator/tasks/{task_id}")
        response.raise_for_status()

        task = response.json()

        # Status color
        status_color = {
            "pending": "yellow",
            "planning": "blue",
            "running": "cyan",
            "completed": "green",
            "failed": "red"
        }.get(task["status"], "white")

        info = f"""
[bold]Title:[/bold] {task['title']}
[bold]Description:[/bold] {task['description']}
[bold]Status:[/bold] [{status_color}]{task['status']}[/{status_color}]
[bold]Progress:[/bold] {task['progress']:.0f}%
[bold]Budget:[/bold] ${task['budget']:.2f}
[bold]Actual Cost:[/bold] ${task['actual_cost']:.2f}
[bold]Priority:[/bold] {task['priority']}
[bold]Capabilities Required:[/bold] {', '.join(task['required_capabilities'])}
[bold]Subtasks:[/bold] {task['subtask_count']}
[bold]Assigned Agents:[/bold] {len(task['assigned_agents'])}
[bold]Created:[/bold] {task['created_at']}
[bold]Started:[/bold] {task.get('started_at', 'N/A')}
[bold]Completed:[/bold] {task.get('completed_at', 'N/A')}
        """

        console.print(Panel(info, title=f"Task {task_id[:16]}", border_style="blue"))

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@tasks_app.command("create")
def create_task(
    title: str = typer.Option(..., prompt=True, help="Task title"),
    description: str = typer.Option(..., prompt=True, help="Task description"),
    capabilities: str = typer.Option(..., prompt=True, help="Required capabilities (comma-separated)"),
    budget: float = typer.Option(..., prompt=True, help="Task budget"),
    customer_id: str = typer.Option("cli-user", help="Customer ID"),
    priority: str = typer.Option("medium", help="Task priority"),
    api_url: str = typer.Option(DEFAULT_API_URL, help="API base URL")
):
    """Create a new task"""
    try:
        task_data = {
            "customer_id": customer_id,
            "title": title,
            "description": description,
            "required_capabilities": [c.strip() for c in capabilities.split(",")],
            "budget": budget,
            "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "priority": priority,
            "rental_mode": "commercial",
            "metadata": {"source": "cli"}
        }

        with Progress() as progress:
            task_progress = progress.add_task("[cyan]Creating task...", total=100)

            response = requests.post(f"{api_url}/orchestrator/tasks", json=task_data)
            response.raise_for_status()

            progress.update(task_progress, completed=100)

        task = response.json()

        console.print(f"\n[green]✓[/green] Task created successfully!")
        console.print(f"[bold]Task ID:[/bold] {task['task_id']}")
        console.print(f"[bold]Status:[/bold] {task['status']}")

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# Marketplace Commands
# ============================================================================

marketplace_app = typer.Typer(help="Marketplace operations")
app.add_typer(marketplace_app, name="marketplace")


@marketplace_app.command("search")
def search_agents(
    capability: Optional[str] = typer.Option(None, help="Required capability"),
    max_rate: Optional[float] = typer.Option(None, help="Maximum hourly rate"),
    min_rating: Optional[float] = typer.Option(None, help="Minimum rating"),
    api_url: str = typer.Option(DEFAULT_API_URL, help="API base URL")
):
    """Search for agents in marketplace"""
    try:
        search_params = {
            "page": 1,
            "page_size": 20,
            "sort_by": "rating",
            "sort_order": "desc"
        }

        if capability:
            search_params["capabilities"] = [capability]
        if max_rate:
            search_params["max_hourly_rate"] = max_rate
        if min_rating:
            search_params["min_rating"] = min_rating

        response = requests.post(
            f"{api_url}/marketplace/agents/search",
            json=search_params
        )
        response.raise_for_status()

        data = response.json()
        agents = data.get("agents", [])

        if not agents:
            console.print("[yellow]No agents found matching criteria[/yellow]")
            return

        table = Table(title="Marketplace Search Results", show_header=True)
        table.add_column("Name", style="green")
        table.add_column("Capabilities", style="blue")
        table.add_column("Mode", style="yellow")
        table.add_column("Rate/hr", justify="right")
        table.add_column("Rating", justify="center")
        table.add_column("Reviews", justify="right")
        table.add_column("Tasks", justify="right")

        for agent in agents:
            caps = ", ".join(agent["capabilities"][:2])
            if len(agent["capabilities"]) > 2:
                caps += "..."

            table.add_row(
                agent["name"],
                caps,
                agent["pricing_mode"],
                f"${agent['hourly_rate']:.2f}",
                f"{agent['rating']:.1f}⭐",
                str(agent["reviews_count"]),
                str(agent["total_tasks_completed"])
            )

        console.print(table)
        console.print(f"\n[dim]Found {data.get('total', 0)} agents[/dim]")

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@marketplace_app.command("stats")
def marketplace_stats(
    api_url: str = typer.Option(DEFAULT_API_URL, help="API base URL")
):
    """Show marketplace statistics"""
    try:
        response = requests.get(f"{api_url}/marketplace/statistics")
        response.raise_for_status()

        stats = response.json()

        info = f"""
[bold cyan]Platform Statistics[/bold cyan]

[bold]Agents:[/bold]
  • Total: {stats['total_agents']}
  • Active: {stats['active_agents']}

[bold]Contracts:[/bold]
  • Total: {stats['total_contracts']}
  • Active: {stats['active_contracts']}

[bold]Reviews:[/bold]
  • Total: {stats['total_reviews']}
  • Average Rating: {stats['average_rating']:.2f}⭐

[bold]Revenue:[/bold]
  • Total: ${stats['total_revenue']:.2f}

[bold]Top Categories:[/bold]
        """

        for cat in stats.get('top_categories', [])[:5]:
            info += f"\n  • {cat['category']}: {cat['agent_count']} agents"

        console.print(Panel(info, border_style="green"))

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# Platform Commands
# ============================================================================

platform_app = typer.Typer(help="Platform management")
app.add_typer(platform_app, name="platform")


@platform_app.command("health")
def check_health(
    api_url: str = typer.Option(DEFAULT_API_URL, help="API base URL")
):
    """Check platform health"""
    services = [
        ("API Gateway", f"{api_url}/health"),
        ("Registry", f"{api_url}/registry/health"),
        ("Marketplace", f"{api_url}/marketplace/health"),
        ("Orchestrator", f"{api_url}/orchestrator/health")
    ]

    table = Table(title="Platform Health Check", show_header=True)
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Response Time", justify="right")

    for service_name, url in services:
        try:
            import time
            start = time.time()
            response = requests.get(url, timeout=5)
            duration = (time.time() - start) * 1000

            if response.status_code == 200:
                status = "[green]✓ Healthy[/green]"
            else:
                status = f"[yellow]⚠ {response.status_code}[/yellow]"

            table.add_row(service_name, status, f"{duration:.0f}ms")

        except requests.exceptions.RequestException:
            table.add_row(service_name, "[red]✗ Down[/red]", "—")

    console.print(table)


@platform_app.command("stats")
def platform_stats(
    api_url: str = typer.Option(DEFAULT_API_URL, help="API base URL")
):
    """Show platform-wide statistics"""
    try:
        # Get orchestrator stats
        orch_response = requests.get(f"{api_url}/orchestrator/statistics")
        orch_response.raise_for_status()
        orch_stats = orch_response.json()

        info = f"""
[bold cyan]Orchestrator Statistics[/bold cyan]

[bold]Tasks:[/bold]
  • Total: {orch_stats['total_tasks']}
  • Pending: {orch_stats['status_breakdown'].get('pending', 0)}
  • Running: {orch_stats['status_breakdown'].get('running', 0)}
  • Completed: {orch_stats['status_breakdown'].get('completed', 0)}
  • Failed: {orch_stats['status_breakdown'].get('failed', 0)}

[bold]Subtasks:[/bold]
  • Total: {orch_stats['total_subtasks']}
  • Avg per Task: {orch_stats['avg_subtasks_per_task']}

[bold]Cost:[/bold]
  • Total: ${orch_stats['total_cost']:.2f}
        """

        console.print(Panel(info, border_style="blue"))

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# Main
# ============================================================================

@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show version")
):
    """
    AI Agent Orchestration Platform CLI

    Manage agents, tasks, and marketplace operations from the command line.
    """
    if version:
        console.print("[bold]Agent Platform CLI[/bold] version 1.0.0")
        raise typer.Exit()


if __name__ == "__main__":
    app()
