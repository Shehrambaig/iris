#!/usr/bin/env python3
"""
Python-based scheduler for the change detection scraper.
Runs the scraper every 3 hours automatically.

This is an alternative to using system cron - keeps the process running continuously.
"""
import asyncio
import time
import signal
import sys
from datetime import datetime
from pathlib import Path
import logging

# Add the src directory to the path if needed
sys.path.insert(0, str(Path(__file__).parent))

# Import from run_scraper.py (using importlib)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "run_scraper",
    Path(__file__).parent / "run_scraper.py"
)
run_scraper_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_scraper_module)
run_scraper = run_scraper_module.run_scraper

# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScraperScheduler:
    """Scheduler that runs the scraper every 3 hours"""

    def __init__(self, interval_hours: int = 3):
        self.interval_hours = interval_hours
        self.interval_seconds = interval_hours * 60 * 60
        self.running = False
        self.run_count = 0

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("\nReceived shutdown signal. Stopping scheduler...")
        self.running = False

    async def run_scheduled_task(self):
        """Run the scraper and handle errors"""
        self.run_count += 1
        logger.info(f"\n{'#' * 80}")
        logger.info(f"SCHEDULED RUN #{self.run_count}")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'#' * 80}\n")

        try:
            await run_scraper()
            logger.info(f"✓ Scheduled run #{self.run_count} completed successfully")
        except Exception as e:
            logger.error(f"✗ Error in scheduled run #{self.run_count}: {str(e)}", exc_info=True)

    async def start(self):
        """Start the scheduler loop"""
        self.running = True

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        logger.info("=" * 80)
        logger.info("SCRAPER SCHEDULER STARTED")
        logger.info("=" * 80)
        logger.info(f"Interval: Every {self.interval_hours} hours")
        logger.info(f"Next run: Immediately")
        logger.info(f"Press Ctrl+C to stop")
        logger.info("=" * 80)

        # Run immediately on start
        await self.run_scheduled_task()

        # Then run on schedule
        while self.running:
            next_run = datetime.now().timestamp() + self.interval_seconds
            next_run_time = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')

            logger.info(f"\n{'=' * 80}")
            logger.info(f"Waiting {self.interval_hours} hours until next run...")
            logger.info(f"Next run scheduled for: {next_run_time}")
            logger.info(f"{'=' * 80}\n")

            # Sleep in small intervals to allow for responsive shutdown
            sleep_remaining = self.interval_seconds
            while sleep_remaining > 0 and self.running:
                sleep_time = min(60, sleep_remaining)  # Check every minute
                await asyncio.sleep(sleep_time)
                sleep_remaining -= sleep_time

            if self.running:
                await self.run_scheduled_task()

        logger.info("\n" + "=" * 80)
        logger.info("SCHEDULER STOPPED")
        logger.info(f"Total runs completed: {self.run_count}")
        logger.info("=" * 80)


def main():
    """Entry point for the scheduler"""
    # Allow custom interval via command line argument
    interval_hours = 3

    if len(sys.argv) > 1:
        try:
            interval_hours = int(sys.argv[1])
            logger.info(f"Using custom interval: {interval_hours} hours")
        except ValueError:
            logger.error(f"Invalid interval: {sys.argv[1]}. Using default: 3 hours")

    scheduler = ScraperScheduler(interval_hours=interval_hours)

    try:
        asyncio.run(scheduler.start())
    except KeyboardInterrupt:
        logger.info("\nScheduler interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
