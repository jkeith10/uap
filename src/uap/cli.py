"""UAP Command Line Interface"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from .config import get_config, UAPConfig, Environment
from .logging_config import configure_logging
from .main import UAPApplication
from .storage.postgres_client import PostgreSQLClient
from .storage.redis_client import RedisClient

app = typer.Typer(
    name="uap",
    help="Unified Autonomy Protocol - Command Line Interface",
    add_completion=False,
)
console = Console()


@app.command()
def init(
    name: str = typer.Option("my-uap-project", help="Project name"),
    directory: Optional[Path] = typer.Option(None, help="Project directory"),
):
    """Initialize a new UAP project"""
    console.print(Panel.fit("🚀 Initializing UAP Project", style="bold blue"))
    
    project_dir = directory or Path.cwd() / name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating project structure...", total=5)
        
        # Create directories
        (project_dir / "config").mkdir(exist_ok=True)
        progress.update(task, advance=1)
        
        (project_dir / "examples").mkdir(exist_ok=True)
        progress.update(task, advance=1)
        
        (project_dir / "logs").mkdir(exist_ok=True)
        progress.update(task, advance=1)
        
        # Create .env file
        env_content = """# UAP Configuration
UAP_ENVIRONMENT=development
UAP_DEBUG=true
UAP_HOST=0.0.0.0
UAP_PORT=8000

# Database
UAP_DATABASE__HOST=localhost
UAP_DATABASE__PORT=5432
UAP_DATABASE__NAME=uap
UAP_DATABASE__USER=uap
UAP_DATABASE__PASSWORD=uap_password

# Redis
UAP_REDIS__HOST=localhost
UAP_REDIS__PORT=6379
UAP_REDIS__DB=0

# Logging
UAP_LOGGING__LEVEL=INFO
UAP_LOGGING__FORMAT=json
"""
        (project_dir / ".env").write_text(env_content)
        progress.update(task, advance=1)
        
        # Create README
        readme_content = f"""# {name}

UAP Project initialized with CLI.

## Getting Started

```bash
# Start the UAP server
uap serve

# Run database migrations
uap migrate

# Check system status
uap status
```

## Configuration

Edit `.env` to configure your UAP instance.
"""
        (project_dir / "README.md").write_text(readme_content)
        progress.update(task, advance=1)
    
    console.print(f"\n✅ Project initialized at: [bold green]{project_dir}[/bold green]")
    console.print("\n📝 Next steps:")
    console.print("   1. cd " + str(project_dir))
    console.print("   2. Edit .env with your configuration")
    console.print("   3. Run: uap migrate")
    console.print("   4. Run: uap serve")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
):
    """Start the UAP server"""
    import uvicorn
    
    console.print(Panel.fit("🚀 Starting UAP Server", style="bold blue"))
    console.print(f"📍 Server will be available at: [bold]http://{host}:{port}[/bold]")
    console.print(f"📖 API Docs: [bold]http://{host}:{port}/docs[/bold]")
    console.print(f"💚 Health Check: [bold]http://{host}:{port}/health[/bold]\n")
    
    uvicorn.run(
        "src.uap.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


@app.command()
def migrate(
    revision: str = typer.Option("head", help="Target revision"),
    sql: bool = typer.Option(False, help="Show SQL only"),
):
    """Run database migrations"""
    import subprocess
    
    console.print(Panel.fit("📦 Running Database Migrations", style="bold blue"))
    
    try:
        if sql:
            cmd = ["alembic", "upgrade", revision, "--sql"]
        else:
            cmd = ["alembic", "upgrade", revision]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("✅ Migrations completed successfully")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print(f"❌ Migration failed: {result.stderr}", style="bold red")
            sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error running migrations: {e}", style="bold red")
        sys.exit(1)


@app.command()
def status():
    """Check UAP system status"""
    console.print(Panel.fit("🔍 Checking UAP System Status", style="bold blue"))
    
    async def check_status():
        config = get_config()
        
        table = Table(title="System Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="green")
        
        # Check Redis
        try:
            redis_client = RedisClient(
                host=config.redis.host,
                port=config.redis.port,
                db=config.redis.db
            )
            await redis_client.connect()
            health = await redis_client.health_check()
            await redis_client.disconnect()
            table.add_row("Redis", "✅ Connected", f"{config.redis.host}:{config.redis.port}")
        except Exception as e:
            table.add_row("Redis", "❌ Error", str(e)[:50])
        
        # Check PostgreSQL
        try:
            pg_client = PostgreSQLClient(
                host=config.database.host,
                port=config.database.port,
                database=config.database.name,
                user=config.database.user,
                password=config.database.password
            )
            await pg_client.connect()
            health = await pg_client.health_check()
            await pg_client.disconnect()
            table.add_row("PostgreSQL", "✅ Connected", f"{config.database.host}:{config.database.port}")
        except Exception as e:
            table.add_row("PostgreSQL", "❌ Error", str(e)[:50])
        
        # Configuration
        table.add_row("Environment", f"📋 {config.environment.value}", f"Debug: {config.debug}")
        table.add_row("Service", "⚙️ Configured", f"{config.host}:{config.port}")
        
        console.print(table)
    
    asyncio.run(check_status())


@app.command()
def demo():
    """Run a demonstration workflow"""
    console.print(Panel.fit("🎬 Running UAP Demo", style="bold blue"))
    
    async def run_demo():
        from .models.intent import IntentPacket, IntentType, IntentPriority
        from .models.action_graph import ActionGraph, ActionNode
        
        console.print("\n1️⃣ Creating sample intent...")
        intent = IntentPacket(
            type=IntentType.ACTION,
            content="Optimize HVAC system for conference room",
            context={"room": "conference_room_a", "target_temp": 72},
            priority=IntentPriority.HIGH
        )
        console.print(f"   Intent ID: {intent.id}")
        
        console.print("\n2️⃣ Creating action graph...")
        node1 = ActionNode(type="sensor_read", data={"sensor": "temperature"})
        node2 = ActionNode(type="hvac_adjust", data={"target": 72})
        graph = ActionGraph(
            nodes=[node1, node2],
            edges=[{"from": str(node1.id), "to": str(node2.id)}]
        )
        console.print(f"   Graph ID: {graph.id}")
        console.print(f"   Nodes: {len(graph.nodes)}")
        
        console.print("\n✅ Demo completed successfully!")
        console.print("\n💡 To run a real workflow:")
        console.print("   1. Start the server: uap serve")
        console.print("   2. Check API docs: http://localhost:8000/docs")
        console.print("   3. Create intents via API or SDK")
    
    asyncio.run(run_demo())


@app.command()
def config(
    show: bool = typer.Option(False, help="Show current configuration"),
    validate: bool = typer.Option(False, help="Validate configuration"),
):
    """Manage UAP configuration"""
    if show:
        console.print(Panel.fit("⚙️ Current Configuration", style="bold blue"))
        config = get_config()
        
        table = Table()
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Environment", config.environment.value)
        table.add_row("Debug Mode", str(config.debug))
        table.add_row("Service", f"{config.host}:{config.port}")
        table.add_row("Database", f"{config.database.host}:{config.database.port}/{config.database.name}")
        table.add_row("Redis", f"{config.redis.host}:{config.redis.port}/{config.redis.db}")
        table.add_row("Log Level", config.logging.level.value)
        
        console.print(table)
    
    if validate:
        console.print(Panel.fit("✓ Validating Configuration", style="bold blue"))
        try:
            config = get_config()
            console.print("✅ Configuration is valid")
        except Exception as e:
            console.print(f"❌ Configuration error: {e}", style="bold red")
            sys.exit(1)


@app.command()
def version():
    """Show UAP version"""
    console.print(Panel.fit("📦 UAP Version", style="bold blue"))
    console.print("\n[bold]Unified Autonomy Protocol[/bold]")
    console.print("Version: [bold cyan]1.0.0[/bold cyan]")
    console.print("Python: [bold cyan]3.11+[/bold cyan]")
    console.print("\n🌐 Repository: https://github.com/jkeith10/uap")
    console.print("📖 Documentation: https://github.com/jkeith10/uap/docs")


def main():
    """Main CLI entry point"""
    app()


if __name__ == "__main__":
    main()

