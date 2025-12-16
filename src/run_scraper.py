#!/usr/bin/env python3
"""
Cron-friendly runner script for the change detection scraper.
This script can be executed by cron or run manually.
"""
import asyncio
import json
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the src directory to the path if needed
sys.path.insert(0, str(Path(__file__).parent))

# Import from change-detection.py (using importlib for hyphenated module name)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "change_detection",
    Path(__file__).parent / "change-detection.py"
)
change_detection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(change_detection)
UniversalScraper = change_detection.UniversalScraper

# Configure logging to file for cron jobs
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"scraper_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger(__name__)


async def process_single_company(scraper, company_config, idx, total_companies):
    """Process a single company - designed for parallel execution"""
    company_name = company_config.get('company_name')
    url = company_config.get('url')

    if not company_name or not url:
        logger.warning(f"Skipping invalid config: {company_config}")
        return {
            'success': False,
            'company_name': company_name or 'Unknown',
            'new_urls': 0,
            'error': 'Invalid configuration'
        }

    logger.info(f"[{idx}/{total_companies}] Starting: {company_name}")

    try:
        # Scrape with change detection for this company
        scrape_result = await scraper.scrape_with_change_detection(
            urls=[url],
            company_name=company_name,
            main_url=url
        )

        results = scrape_result['results']
        change_report = scrape_result['change_report']
        stats = scrape_result['stats']

        # Calculate new URLs found
        new_url_count = 0
        if change_report:
            new_url_count = sum(
                page['summary']['total_new_urls']
                for page in change_report.changed_urls
            )

        # Log results
        logger.info(f"[{idx}/{total_companies}] ✓ {company_name}: "
                   f"Success={stats['successful']>0}, New URLs={new_url_count}")

        if new_url_count > 0:
            logger.info(f"  └─ Saved to: change_tracking/new_urls/{company_name.replace(' ', '_')}-*.json")

        return {
            'success': stats['successful'] > 0,
            'company_name': company_name,
            'new_urls': new_url_count,
            'stats': stats
        }

    except Exception as e:
        logger.error(f"[{idx}/{total_companies}] ✗ {company_name}: {str(e)}")
        return {
            'success': False,
            'company_name': company_name,
            'new_urls': 0,
            'error': str(e)
        }


async def run_scraper():
    """Main function to run the scraper for all companies IN PARALLEL"""
    logger.info("=" * 80)
    logger.info("Starting scheduled scraper run with PARALLEL processing")
    logger.info("=" * 80)

    # Load company URLs from configuration file
    config_path = Path(__file__).parent / "company_urls.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            company_configs = json.load(f)
        logger.info(f"Loaded {len(company_configs)} companies from configuration")
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        logger.error("Please create company_urls.json with company names and URLs")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing company_urls.json: {e}")
        return False

    total_companies = len(company_configs)

    # Use 5 concurrent workers for parallel processing (reduced from 10 to avoid timeouts)
    async with UniversalScraper(headless=True, max_concurrent=5) as scraper:
        logger.info(f"Using 5 parallel workers to process {total_companies} companies")
        logger.info("=" * 80)

        # Create tasks for all companies to run in parallel
        tasks = [
            process_single_company(scraper, config, idx, total_companies)
            for idx, config in enumerate(company_configs, 1)
        ]

        # Execute all tasks in parallel and gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_companies = 0
        failed_companies = 0
        total_new_urls = 0

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Unexpected error: {str(result)}")
                failed_companies += 1
            elif isinstance(result, dict):
                if result['success']:
                    successful_companies += 1
                else:
                    failed_companies += 1
                total_new_urls += result.get('new_urls', 0)
            else:
                failed_companies += 1

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("SCRAPER RUN COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Total companies processed: {total_companies}")
    logger.info(f"Successful: {successful_companies}")
    logger.info(f"Failed: {failed_companies}")
    logger.info(f"Total new URLs discovered: {total_new_urls}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 80)

    return failed_companies == 0


def main():
    """Entry point for the script"""
    try:
        success = asyncio.run(run_scraper())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nScraper interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
