"""Scheduler module for managing Gonzo's continuous operation."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, Awaitable

logger = logging.getLogger(__name__)

class WorkflowScheduler:
    """Manages scheduled execution of workflow cycles."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.min_interval = config.get('response', {}).get('frequency', {}).get('min_interval', 300)
        self.max_per_hour = config.get('response', {}).get('frequency', {}).get('max_per_hour', 12)
        self.last_run = None
        self.running = False
        self._shutdown = False
        self.run_count = 0
        self.hour_start = datetime.now()

    async def should_run(self) -> bool:
        """Check if conditions are met to run a new cycle."""
        current_time = datetime.now()

        # First run or minimum interval check
        if self.last_run is None:
            return True

        time_since_last = (current_time - self.last_run).total_seconds()
        if time_since_last < self.min_interval:
            return False

        # Reset hourly counter if hour has passed
        if (current_time - self.hour_start).total_seconds() >= 3600:
            self.run_count = 0
            self.hour_start = current_time

        # Check hourly limit
        if self.run_count >= self.max_per_hour:
            return False

        return True

    async def schedule_workflow(self, workflow_func: Callable[[], Awaitable[Any]]) -> None:
        """Schedule and manage workflow execution."""
        self.running = True
        self._shutdown = False

        try:
            while not self._shutdown:
                if await self.should_run():
                    try:
                        await workflow_func()
                        self.last_run = datetime.now()
                        self.run_count += 1
                        logger.info(
                            f"Workflow cycle completed. "
                            f"Run count this hour: {self.run_count}/{self.max_per_hour}"
                        )
                    except Exception as e:
                        logger.error(f"Error in workflow execution: {str(e)}")
                        # Wait before retry on error
                        await asyncio.sleep(60)

                # Adaptive sleep based on conditions
                if self.run_count >= self.max_per_hour:
                    # Sleep until next hour if limit reached
                    seconds_to_next_hour = 3600 - (datetime.now() - self.hour_start).total_seconds()
                    await asyncio.sleep(max(0, seconds_to_next_hour))
                else:
                    # Regular interval sleep
                    await asyncio.sleep(min(60, self.min_interval))

        except asyncio.CancelledError:
            logger.info("Scheduler received cancellation signal")
        finally:
            self.running = False
            logger.info("Scheduler stopped")

    def request_shutdown(self) -> None:
        """Request graceful shutdown of scheduler."""
        self._shutdown = True
        logger.info("Shutdown requested for scheduler")

    @property
    def is_running(self) -> bool:
        """Check if scheduler is currently running."""
        return self.running
