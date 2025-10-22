"""Real-Time Monitoring Dashboard Example for UAP"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel

from src.uap.client import AsyncUAPClient, StreamingClient
from src.uap.models.intent import IntentPacket, IntentType, IntentPriority

console = Console()


class MonitoringDashboard:
    """Real-time monitoring dashboard for UAP"""
    
    def __init__(self):
        self.events = []
        self.metrics = {
            "intents_created": 0,
            "graphs_executed": 0,
            "memories_stored": 0,
            "reflections_created": 0
        }
        self.health_status = {}
    
    def create_layout(self) -> Layout:
        """Create dashboard layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=5)
        )
        
        layout["main"].split_row(
            Layout(name="metrics"),
            Layout(name="events")
        )
        
        return layout
    
    def generate_header(self) -> Panel:
        """Generate header panel"""
        return Panel(
            "[bold cyan]UAP Real-Time Monitoring Dashboard[/bold cyan]\n"
            f"[dim]Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}[/dim]",
            style="bold blue"
        )
    
    def generate_metrics_table(self) -> Table:
        """Generate metrics table"""
        table = Table(title="System Metrics", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        for metric, value in self.metrics.items():
            table.add_row(metric.replace("_", " ").title(), str(value))
        
        return table
    
    def generate_events_table(self) -> Table:
        """Generate events table"""
        table = Table(title="Recent Events", show_header=True, header_style="bold magenta")
        table.add_column("Time", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Details", style="white")
        
        # Show last 10 events
        for event in self.events[-10:]:
            table.add_row(
                event.get("time", ""),
                event.get("type", ""),
                str(event.get("details", ""))[:50]
            )
        
        return table
    
    def generate_footer(self) -> Panel:
        """Generate footer panel"""
        health_text = " | ".join([
            f"{k}: {'✅' if v.get('status') == 'healthy' else '❌'}"
            for k, v in self.health_status.items()
        ])
        
        return Panel(
            f"[bold]Health Status:[/bold] {health_text if health_text else 'Checking...'}\n"
            "[dim]Press Ctrl+C to exit[/dim]",
            style="blue"
        )
    
    def update_display(self, layout: Layout) -> None:
        """Update dashboard display"""
        layout["header"].update(self.generate_header())
        layout["metrics"].update(Panel(self.generate_metrics_table()))
        layout["events"].update(Panel(self.generate_events_table()))
        layout["footer"].update(self.generate_footer())
    
    def add_event(self, event_type: str, details: Any) -> None:
        """Add an event to the dashboard"""
        self.events.append({
            "time": datetime.now(timezone.utc).strftime('%H:%M:%S'),
            "type": event_type,
            "details": details
        })
        
        # Update metrics
        if event_type == "intent.created":
            self.metrics["intents_created"] += 1
        elif event_type == "graph.executed":
            self.metrics["graphs_executed"] += 1
        elif event_type == "memory.stored":
            self.metrics["memories_stored"] += 1
        elif event_type == "reflection.created":
            self.metrics["reflections_created"] += 1


async def run_dashboard():
    """Run real-time monitoring dashboard"""
    
    dashboard = MonitoringDashboard()
    layout = dashboard.create_layout()
    
    # Create clients
    api_client = AsyncUAPClient("http://localhost:8000")
    stream_client = StreamingClient("ws://localhost:8000")
    
    try:
        await api_client.connect()
        await stream_client.connect()
        
        # Check health
        health = await api_client.detailed_health_check()
        dashboard.health_status = health.get("components", {})
        
        # Subscribe to events
        async def on_intent_created(message):
            dashboard.add_event("intent.created", message.get("data", {}))
        
        async def on_graph_executed(message):
            dashboard.add_event("graph.executed", message.get("data", {}))
        
        async def on_memory_stored(message):
            dashboard.add_event("memory.stored", message.get("data", {}))
        
        await stream_client.subscribe("intent.created", on_intent_created)
        await stream_client.subscribe("graph.executed", on_graph_executed)
        await stream_client.subscribe("memory.stored", on_memory_stored)
        
        # Create some sample activity
        async def generate_activity():
            """Generate sample activity"""
            for i in range(5):
                await asyncio.sleep(2)
                
                # Create random intents
                intent = IntentPacket(
                    type=IntentType.ACTION,
                    content=f"Sample activity {i+1}",
                    context={"iteration": i+1},
                    priority=IntentPriority.MEDIUM
                )
                
                await api_client.create_intent(intent)
        
        # Start activity generator
        activity_task = asyncio.create_task(generate_activity())
        
        # Run dashboard with live updates
        with Live(layout, refresh_per_second=2, console=console) as live:
            while not activity_task.done():
                dashboard.update_display(layout)
                live.update(layout)
                await asyncio.sleep(0.5)
            
            # Keep running to show final state
            await asyncio.sleep(5)
            dashboard.update_display(layout)
            live.update(layout)
        
        console.print("\n✅ Dashboard demonstration complete!")
        
    finally:
        await stream_client.disconnect()
        await api_client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(run_dashboard())
    except KeyboardInterrupt:
        console.print("\n\n👋 Dashboard stopped by user")
