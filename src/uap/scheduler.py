"""Task Scheduling for UAP"""

from __future__ import annotations

import asyncio
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from croniter import croniter

from .logging_config import get_logger
from .exceptions import UAPException

logger = get_logger(__name__)


class ScheduledTask:
    """A scheduled task"""
    
    def __init__(
        self,
        task_id: str,
        func: Callable,
        schedule: str,
        args: tuple = (),
        kwargs: Dict[str, Any] = None
    ):
        self.task_id = task_id
        self.func = func
        self.schedule = schedule
        self.args = args
        self.kwargs = kwargs or {}
        self.next_run: Optional[datetime] = None
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self._calculate_next_run()
    
    def _calculate_next_run(self) -> None:
        """Calculate next run time"""
        cron = croniter(self.schedule, datetime.now(timezone.utc))
        self.next_run = cron.get_next(datetime)
    
    def should_run(self) -> bool:
        """Check if task should run now"""
        if self.next_run is None:
            return False
        return datetime.now(timezone.utc) >= self.next_run
    
    async def run(self) -> Any:
        """Run the task"""
        logger.info("Running scheduled task", task_id=self.task_id)
        
        self.last_run = datetime.now(timezone.utc)
        self.run_count += 1
        
        try:
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(*self.args, **self.kwargs)
            else:
                result = self.func(*self.args, **self.kwargs)
            
            self._calculate_next_run()
            
            logger.info("Scheduled task completed", 
                       task_id=self.task_id,
                       run_count=self.run_count)
            
            return result
            
        except Exception as e:
            logger.error("Scheduled task failed", 
                        task_id=self.task_id,
                        error=str(e),
                        exc_info=True)
            self._calculate_next_run()
            raise


class Scheduler:
    """Task scheduler for UAP"""
    
    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
    
    def schedule(
        self,
        task_id: str,
        func: Callable,
        cron_expression: str,
        *args,
        **kwargs
    ) -> None:
        """Schedule a task with cron expression"""
        task = ScheduledTask(task_id, func, cron_expression, args, kwargs)
        self._tasks[task_id] = task
        logger.info("Task scheduled", task_id=task_id, schedule=cron_expression)
    
    def unschedule(self, task_id: str) -> None:
        """Unschedule a task"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.info("Task unscheduled", task_id=task_id)
    
    async def start(self) -> None:
        """Start the scheduler"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run())
        logger.info("Scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler"""
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None
        
        logger.info("Scheduler stopped")
    
    async def _run(self) -> None:
        """Main scheduler loop"""
        while self._running:
            try:
                # Check all tasks
                for task_id, task in list(self._tasks.items()):
                    if task.should_run():
                        # Run task in background
                        asyncio.create_task(task.run())
                
                # Sleep for 1 second before checking again
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduler error", error=str(e), exc_info=True)
                await asyncio.sleep(5)


# Global scheduler instance
_scheduler = Scheduler()


def get_scheduler() -> Scheduler:
    """Get global scheduler instance"""
    return _scheduler


def schedule(task_id: str, cron_expression: str):
    """Decorator for scheduling tasks"""
    def decorator(func):
        _scheduler.schedule(task_id, func, cron_expression)
        return func
    return decorator

