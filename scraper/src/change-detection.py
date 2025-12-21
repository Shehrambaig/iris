import asyncio
import json
import time
import random
from asyncio import wait_for
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import hashlib
import os
from enum import Enum
import glob
from pathlib import Path


from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
from readability import Document
import aiohttp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ExtractionStatus(Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    PARSING_ERROR = "parsing_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ExtractedContent:
    url: str
    title: str
    cleaned_content: str
    plain_text: str
    clickable_elements: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: str
    content_hash: str
    status: ExtractionStatus
    company_name: Optional[str] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    retry_count: int = 0


@dataclass
class UrlChangeDetection:
    url: str
    company_name: str
    new_urls: List[Dict[str, Any]]
    changed_urls: List[Dict[str, Any]]
    total_previous_urls: int
    total_current_urls: int
    has_url_changes: bool


@dataclass
class ChangeDetection:
    url: str
    has_changes: bool
    new_content_hash: str
    previous_content_hash: Optional[str]
    changes_detected: List[str]
    url_changes: Optional[UrlChangeDetection] = None
    previous_file_path: Optional[str] = None


@dataclass
class ChangeReport:
    main_url: str
    company_name: str
    changed_urls: List[Dict[str, Any]]
    timestamp: str
    total_changes: int


@dataclass
class SiteConfig:
    domain: str
    timeout: int = 120000  # Increased from 50s to 120s
    wait_strategy: str = "domcontentloaded"  # networkidle, domcontentloaded, load
    wait_selector: Optional[str] = None
    custom_selectors: Dict[str, str] = None
    max_retries: int = 2  # Reduced from 3 to 2 retries
    retry_delay: int = 5


class UrlTracker:
    """Handles tracking and comparison of clickable URLs"""

    def __init__(self, storage_dir: str = "change_tracking"):
        self.storage_dir = Path(storage_dir)
        self.url_tracking_dir = self.storage_dir / "url_tracking-june_26-direct-IR-pages"
        self.url_tracking_dir.mkdir(parents=True, exist_ok=True)

    def _get_domain_file(self, company_name: str) -> Path:
        """Get the tracking file path for a company (master file with all historical URLs)"""
        safe_name = company_name.replace(' ', '_').replace('.', '_').replace(':', '_')
        return self.url_tracking_dir / f"{safe_name}_master_urls.json"

    def _load_previous_urls(self, company_name: str) -> List[Dict[str, Any]]:
        """Load previously stored URLs for a company from master file"""
        file_path = self._get_domain_file(company_name)
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('clickable_urls', [])
            except Exception as e:
                logger.warning(f"Could not load previous URLs for {company_name}: {e}")
        return []

    def _save_current_urls(self, company_name: str, url: str, clickable_urls: List[Dict[str, Any]]):
        """Save current URLs to master file (all historical URLs) for future comparison"""
        file_path = self._get_domain_file(company_name)
        data = {
            'company_name': company_name,
            'url': url,
            'domain': urlparse(url).netloc,
            'last_updated': datetime.now().isoformat(),
            'clickable_urls': clickable_urls,
            'total_urls': len(clickable_urls)
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save URLs for {company_name}: {e}")

    def _normalize_url_data(self, clickable_urls: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Normalize URL data for comparison"""
        normalized = []
        for item in clickable_urls:
            if item.get('url') and item.get('text'):
                normalized.append({
                    'url': item['url'].strip(),
                    'text': item['text'].strip(),
                    'element_type': item.get('element_type', 'unknown')
                })
        return normalized

    def detect_url_changes(self, company_name: str, url: str, current_clickable_urls: List[Dict[str, Any]]) -> UrlChangeDetection:
        """Detect only NEW clickable URLs that weren't seen before"""
        # Load previous URLs from master file
        previous_urls = self._load_previous_urls(company_name)

        # Normalize both sets for comparison
        current_normalized = self._normalize_url_data(current_clickable_urls)
        previous_normalized = self._normalize_url_data(previous_urls)

        # Create sets for comparison (using URL as unique identifier)
        # Only track URLs, not text changes
        previous_url_set = {item['url'] for item in previous_normalized}
        current_url_set = {item['url'] for item in current_normalized}

        # Find NEW URLs (URLs that weren't in the master file before)
        new_url_strings = current_url_set - previous_url_set
        new_urls = [item for item in current_normalized if item['url'] in new_url_strings]

        # We're no longer tracking "changed URLs" - only truly new URLs
        changed_urls = []

        # Update master file with ALL current URLs (merge old + new)
        # This ensures the master file contains complete historical record
        all_urls = current_clickable_urls.copy()

        # Add any old URLs that are still not in current (to preserve history)
        current_url_lookup = {item['url']: item for item in current_normalized}
        for prev_item in previous_urls:
            if prev_item.get('url') not in current_url_lookup:
                all_urls.append(prev_item)

        # Save updated master file
        self._save_current_urls(company_name, url, all_urls)

        has_changes = len(new_urls) > 0

        return UrlChangeDetection(
            url=url,
            company_name=company_name,
            new_urls=new_urls,
            changed_urls=changed_urls,
            total_previous_urls=len(previous_normalized),
            total_current_urls=len(current_normalized),
            has_url_changes=has_changes
        )


class PersistentChangeTracker:
    """Handles persistent storage and comparison of content changes"""

    def __init__(self, storage_dir: str = "change_tracking"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.hash_file = self.storage_dir / "content_hashes.json"
        self.changes_dir = self.storage_dir / "changes"
        self.new_urls_dir = self.storage_dir / "new_urls"  # NEW: separate directory for new URLs
        self.changes_dir.mkdir(exist_ok=True)
        self.new_urls_dir.mkdir(exist_ok=True)  # NEW

        # Initialize URL tracker
        self.url_tracker = UrlTracker(storage_dir)

        # Load existing hashes
        self.content_hashes = self._load_hashes()

    def _load_hashes(self) -> Dict[str, Dict[str, str]]:
        """Load previously stored content hashes"""
        if self.hash_file.exists():
            try:
                with open(self.hash_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load hash file: {e}")
        return {}

    def _save_hashes(self):
        """Save content hashes to disk"""
        try:
            with open(self.hash_file, 'w', encoding='utf-8') as f:
                json.dump(self.content_hashes, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save hash file: {e}")

    def _get_url_key(self, url: str) -> str:
        """Generate a safe key for URL storage"""
        parsed = urlparse(url)
        return f"{parsed.netloc}_{hashlib.md5(url.encode()).hexdigest()[:8]}"

    def _save_new_urls_report(self, company_name: str, url: str, new_urls: List[Dict[str, Any]]):
        """Save ONLY new URLs to a separate file with company_name-timestamp format"""
        if not new_urls:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company_name = company_name.replace(' ', '_').replace('.', '_').replace(':', '_')
        filename = f"{safe_company_name}-{timestamp}.json"
        filepath = self.new_urls_dir / filename

        # Add discovery timestamp and state to each URL
        enriched_urls = []
        for url_item in new_urls:
            enriched_url = url_item.copy()
            enriched_url['discovered_at'] = datetime.now().isoformat()
            enriched_url['state'] = 'pending'
            enriched_urls.append(enriched_url)

        report_data = {
            'company_name': company_name,
            'source_url': url,
            'domain': urlparse(url).netloc,
            'discovery_timestamp': datetime.now().isoformat(),
            'total_new_urls': len(enriched_urls),
            'new_urls': enriched_urls
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            logger.info(f"New URLs report saved: {filepath}")
        except Exception as e:
            logger.error(f"Could not save new URLs report: {e}")

    def track_content(self, company_name: str, url: str, content_hash: str, file_path: str,
                      clickable_urls: List[Dict[str, Any]]) -> ChangeDetection:
        """Track content changes for a URL including URL changes"""
        url_key = self._get_url_key(url)

        # Get previous data
        previous_data = self.content_hashes.get(url_key, {})
        previous_hash = previous_data.get('hash')
        previous_file = previous_data.get('file_path')

        # Determine if there are content changes
        has_content_changes = previous_hash != content_hash
        changes_detected = []

        # Detect URL changes (only new URLs)
        url_changes = self.url_tracker.detect_url_changes(company_name, url, clickable_urls)

        if not previous_hash:
            changes_detected.append("First time scraping this URL")
        elif has_content_changes:
            changes_detected.append("Content hash changed")
            changes_detected.append(f"Previous hash: {previous_hash}")
            changes_detected.append(f"New hash: {content_hash}")
        else:
            changes_detected.append("No content changes detected")

        # Add URL change information
        if url_changes.has_url_changes:
            changes_detected.append(
                f"URL changes detected: {len(url_changes.new_urls)} new URLs discovered")
        else:
            changes_detected.append("No new URLs detected")

        # Update tracking data
        self.content_hashes[url_key] = {
            'url': url,
            'company_name': company_name,
            'hash': content_hash,
            'file_path': file_path,
            'last_updated': datetime.now().isoformat(),
            'previous_hash': previous_hash
        }

        # Save updated hashes
        self._save_hashes()

        # Determine overall change status
        has_overall_changes = has_content_changes or url_changes.has_url_changes

        return ChangeDetection(
            url=url,
            has_changes=has_overall_changes,
            new_content_hash=content_hash,
            previous_content_hash=previous_hash,
            changes_detected=changes_detected,
            url_changes=url_changes,
            previous_file_path=previous_file
        )

    def create_change_report(self, company_name: str, main_url: str, results: List[ExtractedContent]) -> Optional[ChangeReport]:
        """Create a focused change report with only new URLs"""
        changed_urls = []

        for result in results:
            if result.status == ExtractionStatus.SUCCESS:
                change_detection = self.track_content(
                    company_name,
                    result.url,
                    result.content_hash,
                    "",
                    result.clickable_elements
                )

                # Only include if there are new URLs
                if change_detection.url_changes and len(change_detection.url_changes.new_urls) > 0:
                    # Save new URLs to separate file (company_name-timestamp.json)
                    self._save_new_urls_report(company_name, result.url, change_detection.url_changes.new_urls)

                    url_change_data = {
                        'url': result.url,
                        'title': result.title,
                        'timestamp': result.timestamp,
                        'new_urls': change_detection.url_changes.new_urls,
                        'summary': {
                            'total_new_urls': len(change_detection.url_changes.new_urls),
                            'previous_url_count': change_detection.url_changes.total_previous_urls,
                            'current_url_count': change_detection.url_changes.total_current_urls
                        }
                    }
                    changed_urls.append(url_change_data)

        if changed_urls:
            report = ChangeReport(
                main_url=main_url,
                company_name=company_name,
                changed_urls=changed_urls,
                timestamp=datetime.now().isoformat(),
                total_changes=len(changed_urls)
            )

            # Save change report
            self._save_change_report(report)
            return report

        return None

    def _save_change_report(self, report: ChangeReport):
        """Save change report to file with company_name-timestamp format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company_name = report.company_name.replace(' ', '_').replace('.', '_').replace(':', '_')
        filename = f"{safe_company_name}-{timestamp}.json"
        filepath = self.changes_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(report), f, indent=2, ensure_ascii=False)
            logger.info(f"Change report saved: {filepath}")
        except Exception as e:
            logger.error(f"Could not save change report: {e}")


class UniversalScraper:
    def __init__(self, headless: bool = True, max_concurrent: int = 5):
        self.headless = headless
        self.max_concurrent = max_concurrent
        self.browser: Optional[Browser] = None
        self.failed_urls: Dict[str, int] = {}  # URL -> failure_count
        self.site_configs: Dict[str, SiteConfig] = {}
        self.change_tracker = PersistentChangeTracker()
        self._setup_default_configs()

        # NEW: Store persistent context and page pool
        self.context = None
        self.page_pool = []  # Pool of reusable pages
        self.max_pages = max_concurrent  # Maximum number of pages to keep open

        self._setup_default_configs()

        # Proxy configuration - DISABLED by default (set 'enabled': True to use)
        # Note: Update credentials with valid proxy credentials before enabling
        self.proxy_config = {
            'enabled': False,  # Changed to False - proxies causing timeouts
            'protocol': 'http',
            'regions': {
                'US': {
                    'host': 'geo.iproyal.com',
                    'port': 12321,
                    'username': 'YOUR_USERNAME_HERE',  # Update with real credentials
                    'password': 'YOUR_PASSWORD_HERE'
                },
                'EU': {
                    'host': 'geo.iproyal.com',
                    'port': 12321,
                    'username': 'YOUR_USERNAME_HERE',
                    'password': 'YOUR_PASSWORD_HERE'
                },
                'ASIA': {
                    'host': 'geo.iproyal.com',
                    'port': 12321,
                    'username': 'YOUR_USERNAME_HERE',
                    'password': 'YOUR_PASSWORD_HERE'
                }
            }
        }

        os.makedirs("../screenshots", exist_ok=True)
        os.makedirs("../extracted_data", exist_ok=True)

    def _get_random_proxy(self) -> Dict[str, Any]:
        """Get a random proxy configuration"""
        if not self.proxy_config['enabled']:
            return None

        region = random.choice(list(self.proxy_config['regions'].keys()))
        proxy_info = self.proxy_config['regions'][region]

        proxy = {
            'server': f"http://{proxy_info['host']}:{proxy_info['port']}",
            'username': proxy_info['username'],
            'password': proxy_info['password']
        }

        logger.info(f"Using proxy from region: {region}")
        return proxy

    def _setup_default_configs(self):
        """Setup default configurations for known problematic sites"""
        configs = [
            SiteConfig("investors.3m.com", timeout=60000, wait_strategy="domcontentloaded", max_retries=2),
            SiteConfig("investor.apple.com", wait_selector=".news-listing", timeout=45000),
            SiteConfig("https://www.angloamerican.com/investors/regulatory-news",wait_selector="div.GridViewStyle",wait_strategy="domcontentloaded", custom_selectors="div.GridViewStyle" , timeout=20000),
            SiteConfig("investors.netflix.com", timeout=45000, wait_strategy="domcontentloaded"),
            SiteConfig("abbott.com", timeout=60000, max_retries=2),
            SiteConfig("abbvie.com", timeout=45000),
        ]

        for config in configs:
            self.site_configs[config.domain] = config

    def get_site_config(self, url: str) -> SiteConfig:
        """Get site-specific configuration"""
        domain = urlparse(url).netloc

        # Check for exact domain match
        if domain in self.site_configs:
            return self.site_configs[domain]

        # Check for partial domain matches
        for config_domain, config in self.site_configs.items():
            if config_domain in domain or domain in config_domain:
                return config

        # Return default config
        return SiteConfig(domain)

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions'
            ]
        )

        # NEW: Create a persistent context
        self.context = await self.browser.new_context()

        # NEW: Pre-create page pool
        for _ in range(self.max_pages):
            page = await self.context.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            self.page_pool.append(page)

        logger.info(f"Browser started with {len(self.page_pool)} pages in pool")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # NEW: Close all pages in pool
        for page in self.page_pool:
            try:
                await page.close()
            except:
                pass

        # NEW: Close context
        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()
        await self.playwright.stop()
        logger.info("Browser closed")

    async def _get_page_from_pool(self) -> Page:
        """Get an available page from the pool and clear it"""
        # Simply return pages in rotation - asyncio.Semaphore handles concurrency
        # Use a simple round-robin approach
        if not hasattr(self, '_page_index'):
            self._page_index = 0

        page = self.page_pool[self._page_index % len(self.page_pool)]
        self._page_index += 1

        # CRITICAL: Clear the page to prevent contamination from previous scrapes
        try:
            await page.goto('about:blank', wait_until='domcontentloaded', timeout=5000)
        except Exception as e:
            logger.warning(f"Could not clear page: {e}")

        return page

    async def extract_content_with_retry(self, url: str, company_name: str = None, config: SiteConfig = None) -> ExtractedContent:
        """Extract content with retry mechanism and proxy rotation"""
        if not config:
            config = self.get_site_config(url)

        last_error = None
        retry_count = 0

        for attempt in range(config.max_retries + 1):
            try:
                retry_count = attempt
                if attempt > 0:
                    logger.info(f"Retry {attempt}/{config.max_retries} for {url}")
                    await asyncio.sleep(config.retry_delay * attempt)  # Exponential backoff

                # Use proxy starting from 2nd retry (attempt 1)
                proxy = None
                if attempt >= 1:  # 2nd attempt and beyond
                    proxy = self._get_random_proxy()

                result = await self._extract_content_single_attempt(url, company_name, config, proxy)
                result.retry_count = retry_count
                return result

            except asyncio.TimeoutError as e:
                last_error = f"Timeout after {config.timeout}ms"
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")

            except Exception as e:
                last_error = f"Error: {str(e)}"
                logger.warning(f"Error on attempt {attempt + 1} for {url}: {str(e)}")

        # All retries failed
        logger.error(f"All {config.max_retries + 1} attempts failed for {url}: {last_error}")
        return self._create_failed_result(url, company_name, last_error, retry_count)

    async def _extract_content_single_attempt(self, url: str, company_name: str, config: SiteConfig,
                                              proxy: Dict[str, Any] = None) -> ExtractedContent:
        """Single attempt to extract content using page from pool"""

        # If proxy is needed, create new context with proxy (can't change proxy on existing context)
        if proxy:
            logger.info(f"Using proxy for {url}: {proxy['server']}")
            context = await self.browser.new_context(proxy=proxy)
            page = await context.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            should_close_context = True
        else:
            # Use page from pool
            page = await self._get_page_from_pool()
            context = None
            should_close_context = False

        try:
            # Note: Resource blocking disabled to prevent navigation issues
            # Uncomment below to block images/ads for faster loading (may cause some sites to fail)
            # await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
            # await page.route("**/ads/**", lambda route: route.abort())
            # await page.route("**/analytics/**", lambda route: route.abort())

            # Navigate to page with proper error handling
            logger.info(f"Navigating to {url}")

            try:
                await page.goto(url, wait_until=config.wait_strategy, timeout=config.timeout)
            except Exception as e:
                if "timeout" in str(e).lower():
                    # Try with a more lenient wait strategy
                    logger.info(f"Retrying {url} with domcontentloaded strategy")
                    await page.goto(url, wait_until='domcontentloaded', timeout=config.timeout)
                else:
                    raise

            # Wait for specific selector if provided
            if config.wait_selector:
                try:
                    await page.wait_for_selector(config.wait_selector, timeout=20000)
                except Exception as e:
                    logger.warning(f"Wait selector '{config.wait_selector}' not found for {url}: {str(e)}")

            # Wait for content to stabilize (reduced from 60s to 3s)
            await page.wait_for_timeout(3000)

            # Get page content
            html_content = await page.content()
            title = await page.title()

            # Extract clickable elements
            clickable_elements = await self._extract_clickable_elements(page, url)

            # Clean and prettify content with multiple strategies
            cleaned_content, plain_text = await self._clean_content_with_fallback(html_content, url)

            # Generate content hash for change detection
            content_hash = hashlib.md5(plain_text.encode()).hexdigest()

            # Take screenshot with error handling
            screenshot_path = None
            try:
                screenshot_path = f"screenshots/{urlparse(url).netloc}_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path, full_page=True, timeout=10000)
            except Exception as e:
                logger.warning(f"Screenshot failed for {url}: {str(e)}")

            # Create metadata
            metadata = {
                'url': url,
                'domain': urlparse(url).netloc,
                'page_title': title,
                'content_length': len(plain_text),
                'clickable_count': len(clickable_elements),
                'extraction_time': datetime.now().isoformat(),
                'wait_strategy': config.wait_strategy,
                'timeout_used': config.timeout,
                'proxy_used': proxy is not None,
                'proxy_server': proxy['server'] if proxy else None
            }

            return ExtractedContent(
                url=url,
                title=title,
                cleaned_content=cleaned_content,
                plain_text=plain_text,
                clickable_elements=clickable_elements,
                metadata=metadata,
                timestamp=datetime.now().isoformat(),
                content_hash=content_hash,
                status=ExtractionStatus.SUCCESS,
                company_name=company_name,
                screenshot_path=screenshot_path
            )


        finally:

            # Only close page and context if using proxy (temporary context)

            if should_close_context:
                await page.close()

                await context.close()

            # If using pooled page, don't navigate away - just leave it on the last URL

            # The semaphore will prevent conflicts

    def _create_failed_result(self, url: str, company_name: str, error_message: str, retry_count: int) -> ExtractedContent:
        """Create a failed result object"""
        domain = urlparse(url).netloc

        # Determine status based on error message
        if "timeout" in error_message.lower():
            status = ExtractionStatus.TIMEOUT
        elif "network" in error_message.lower():
            status = ExtractionStatus.NETWORK_ERROR
        else:
            status = ExtractionStatus.UNKNOWN_ERROR

        return ExtractedContent(
            url=url,
            title="",
            cleaned_content="",
            plain_text="",
            clickable_elements=[],
            metadata={
                'url': url,
                'domain': domain,
                'extraction_time': datetime.now().isoformat(),
                'failed': True
            },
            timestamp=datetime.now().isoformat(),
            content_hash="",
            status=status,
            company_name=company_name,
            error_message=error_message,
            retry_count=retry_count
        )

    async def _extract_clickable_elements(self, page: Page, base_url: str) -> List[Dict[str, Any]]:
        """Extract all clickable elements from the page with enhanced error handling"""
        clickable_elements = []

        # Enhanced JavaScript to extract clickable elements
        js_code = """
        () => {
            const clickableElements = [];

            try {
                // Find all elements with click handlers or links
                const selectors = [
                    'a[href]:not([href="#"]):not([href=""])',
                    '[onclick]',
                    '.clickable',
                    'button:not([disabled])',
                    '[role="button"]',
                    '[data-href]',
                    '.bold-font-weight.clickable',
                    '.news-item a',
                    '.press-release a',
                    '.financial-news a',
                    '[class*="link"]',
                    '[class*="btn"]',
                    'div.GridViewStyle a',
                ];

                const processedElements = new Set();

                selectors.forEach(selector => {
                    try {
                        document.querySelectorAll(selector).forEach(element => {
                            const rect = element.getBoundingClientRect();
                            const text = element.textContent?.trim() || '';

                            // Skip if element is not visible or has no text
                            if (rect.width <= 0 || rect.height <= 0 || !text || text.length < 2) {
                                return;
                            }

                            // Create unique identifier to avoid duplicates
                            const elementId = text + (element.href || element.getAttribute('data-href') || '');
                            if (processedElements.has(elementId)) {
                                return;
                            }
                            processedElements.add(elementId);

                            const elementData = {
                                tag: element.tagName.toLowerCase(),
                                text: text.substring(0, 200),
                                href: element.href || element.getAttribute('data-href') || '',
                                onclick: element.getAttribute('onclick') || '',
                                className: element.className || '',
                                id: element.id || '',
                                title: element.title || element.getAttribute('aria-label') || '',
                                position: {
                                    x: Math.round(rect.left),
                                    y: Math.round(rect.top),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                }
                            };
                            clickableElements.push(elementData);
                        });
                    } catch (selectorError) {
                        console.warn('Error with selector:', selector, selectorError);
                    }
                });

                return clickableElements;
            } catch (error) {
                console.error('Error extracting clickable elements:', error);
                return [];
            }
        }
        """

        try:
            raw_elements = await page.evaluate(js_code)

            for element in raw_elements:
                if element['text'] and len(element['text'].strip()) > 2:
                    processed_element = {
                        'text': element['text'].strip(),
                        'url': self._resolve_url(element['href'], base_url),
                        'element_type': element['tag'],
                        'classes': element['className'],
                        'element_id': element['id'],
                        'title': element['title'],
                        'has_onclick': bool(element['onclick']),
                        'extraction_method': self._determine_extraction_method(element),
                        'position': element['position']
                    }

                    # Only add if we found a valid URL or onclick handler
                    if processed_element['url'] or processed_element['has_onclick']:
                        clickable_elements.append(processed_element)

        except Exception as e:
            logger.warning(f"Error extracting clickable elements: {str(e)}")

        return clickable_elements

    def _resolve_url(self, href: str, base_url: str) -> str:
        """Resolve relative URLs to absolute URLs with better error handling"""
        if not href or href in ['#', 'javascript:void(0)', 'javascript:;']:
            return ""

        try:
            if href.startswith(('http://', 'https://')):
                return href
            elif href.startswith('//'):
                return f"https:{href}"
            elif href.startswith('/'):
                return urljoin(base_url, href)
            else:
                return urljoin(base_url, href)
        except Exception as e:
            logger.warning(f"Error resolving URL {href}: {str(e)}")
            return ""

    def _determine_extraction_method(self, element: Dict) -> str:
        """Determine how the clickable element was extracted"""
        if element['href']:
            return 'href'
        elif element['onclick']:
            return 'onclick'
        elif 'clickable' in element['className'].lower():
            return 'css_class'
        elif element['tag'] == 'button':
            return 'button'
        else:
            return 'unknown'

    async def _clean_content_with_fallback(self, html_content: str, url: str) -> tuple[str, str]:
        """Clean content with multiple fallback strategies"""
        try:
            # Strategy 1: Use Readability (primary)
            doc = Document(html_content)
            cleaned_html = doc.summary()

            # Use BeautifulSoup for additional cleaning
            soup = BeautifulSoup(cleaned_html, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
                element.decompose()

            # Extract plain text
            plain_text = soup.get_text(separator=' ', strip=True)

            # Clean up whitespace
            plain_text = ' '.join(plain_text.split())

            # Validate content quality
            if len(plain_text) < 100:  # Too little content, try fallback
                logger.info(f"Content too short for {url}, trying fallback extraction")
                return await self._fallback_content_extraction(html_content)

            return str(soup), plain_text

        except Exception as e:
            logger.warning(f"Readability extraction failed for {url}: {str(e)}")
            return await self._fallback_content_extraction(html_content)

    async def _fallback_content_extraction(self, html_content: str) -> tuple[str, str]:
        """Fallback content extraction method"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript', 'meta']):
                element.decompose()

            # Try to find main content areas
            main_content = None
            for selector in ['main', 'article', '.content', '.main-content', '[role="main"]', '.news-content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if main_content:
                cleaned_html = str(main_content)
                plain_text = main_content.get_text(separator=' ', strip=True)
            else:
                # Use full body as fallback
                body = soup.find('body') or soup
                cleaned_html = str(body)
                plain_text = body.get_text(separator=' ', strip=True)

            # Clean up whitespace
            plain_text = ' '.join(plain_text.split())

            return cleaned_html, plain_text

        except Exception as e:
            logger.error(f"Fallback content extraction failed: {str(e)}")
            return "", ""

    async def scrape_multiple_urls(self, urls: List[str], company_name: str = None) -> List[ExtractedContent]:
        """Scrape multiple URLs concurrently with enhanced error handling"""
        # Validate and clean URLs
        valid_urls = []
        for url in urls:
            url = url.strip()
            if url and url.startswith(('http://', 'https://')):
                valid_urls.append(url)
            else:
                logger.warning(f"Invalid URL skipped: {url}")

        if not valid_urls:
            logger.error("No valid URLs provided")
            return []

        logger.info(f"Starting to scrape {len(valid_urls)} URLs for {company_name}")
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def scrape_single(url: str) -> ExtractedContent:
            async with semaphore:
                return await self.extract_content_with_retry(url, company_name)

        # Process all URLs
        tasks = [scrape_single(url) for url in valid_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Unexpected error for {valid_urls[i]}: {str(result)}")
                # Create a failed result
                failed_result = self._create_failed_result(
                    valid_urls[i],
                    company_name,
                    f"Unexpected error: {str(result)}",
                    0
                )
                valid_results.append(failed_result)
            else:
                valid_results.append(result)

        return valid_results

    def get_success_stats(self, results: List[ExtractedContent]) -> Dict[str, Any]:
        """Get statistics about scraping success"""
        total = len(results)
        successful = sum(1 for r in results if r.status == ExtractionStatus.SUCCESS)
        failed = total - successful

        failure_types = {}
        for result in results:
            if result.status != ExtractionStatus.SUCCESS:
                failure_types[result.status.value] = failure_types.get(result.status.value, 0) + 1

        proxy_usage = sum(1 for r in results if r.metadata.get('proxy_used', False))

        return {
            'total_urls': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'failure_breakdown': failure_types,
            'proxy_usage': {
                'total_requests_with_proxy': proxy_usage,
                'proxy_usage_rate': (proxy_usage / total * 100) if total > 0 else 0
            },
            'retry_stats': {
                'avg_retries': sum(r.retry_count for r in results) / total if total > 0 else 0,
                'max_retries': max((r.retry_count for r in results), default=0)
            }
        }

    async def scrape_with_change_detection(self, urls: List[str], company_name: str = None, main_url: str = None) -> Dict[str, Any]:
        """Scrape URLs and create change reports focusing only on new/changed URLs"""
        if not main_url and urls:
            main_url = urls[0]  # Use first URL as main URL if not specified

        # Scrape all URLs
        results = await self.scrape_multiple_urls(urls, company_name)

        # Create change report (now only includes new/changed URLs)
        change_report = self.change_tracker.create_change_report(company_name, main_url, results)

        # Get statistics
        stats = self.get_success_stats(results)

        # Save successful results (optional, for full data)
        saved_files = []
        for result in results:
            if result.status == ExtractionStatus.SUCCESS:
                filename = f"scrape_report/{int(time.time())}.json"
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(asdict(result), f, indent=2, ensure_ascii=False, default=str)
                    saved_files.append(filename)
                except Exception as e:
                    logger.error(f"Could not save result file: {e}")

        return {
            'results': results,
            'change_report': change_report,
            'stats': stats,
            'saved_files': saved_files
        }


# Enhanced testing function
async def test_enhanced_scraper():
    """Test the enhanced scraper with URL change detection using company_urls.json"""

    # Load company URLs from configuration file
    config_path = Path(__file__).parent / "company_urls.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            company_configs = json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        logger.error("Please create company_urls.json with company names and URLs")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing company_urls.json: {e}")
        return

    logger.info(f"Loaded {len(company_configs)} companies from configuration")

    async with UniversalScraper(headless=False, max_concurrent=10) as scraper:
        logger.info("Starting enhanced scraper test with PARALLEL URL change detection...")
        logger.info(f"Using 10 parallel workers for {len(company_configs)} companies")

        # Create async function to process single company
        async def process_company(company_config):
            company_name = company_config.get('company_name')
            url = company_config.get('url')

            if not company_name or not url:
                logger.warning(f"Skipping invalid config: {company_config}")
                return None

            print(f"\n[STARTED] {company_name}")

            # Scrape with change detection for this company
            scrape_result = await scraper.scrape_with_change_detection(
                urls=[url],
                company_name=company_name,
                main_url=url
            )

            results = scrape_result['results']
            change_report = scrape_result['change_report']
            stats = scrape_result['stats']

            return {
                'company_name': company_name,
                'results': results,
                'change_report': change_report,
                'stats': stats
            }

        # Process all companies in parallel
        tasks = [process_company(config) for config in company_configs]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Display results for each company
        for company_result in all_results:
            if company_result is None or isinstance(company_result, Exception):
                continue

            company_name = company_result['company_name']
            stats = company_result['stats']
            change_report = company_result['change_report']

            print(f"\n{'=' * 80}")
            print(f"RESULTS: {company_name}")
            print(f"{'=' * 80}")

            # Display statistics
            print(f"\n--- SCRAPING STATISTICS for {company_name} ---")
            print(f"Total URLs: {stats['total_urls']}")
            print(f"Successful: {stats['successful']}")
            print(f"Failed: {stats['failed']}")
            print(f"Success Rate: {stats['success_rate']:.1f}%")
            print(f"Proxy Usage: {stats['proxy_usage']['total_requests_with_proxy']} requests ({stats['proxy_usage']['proxy_usage_rate']:.1f}%)")

            # Display change detection results
            print(f"\n--- NEW URLs DETECTION for {company_name} ---")

            if change_report:
                print(f"Company: {change_report.company_name}")
                print(f"Pages with new URLs: {change_report.total_changes}")
                print(f"Main URL: {change_report.main_url}")

                for i, page_change in enumerate(change_report.changed_urls, 1):
                    print(f"\n  Page {i}: {page_change['title']}")
                    print(f"  URL: {page_change['url']}")
                    print(f"  Summary: {page_change['summary']['total_new_urls']} new URLs discovered")

                    # Show new URLs
                    if page_change['new_urls']:
                        print(f"\n  New URLs ({len(page_change['new_urls'])}):")
                        for j, new_url in enumerate(page_change['new_urls'][:5], 1):  # Show first 5
                            print(f"    {j}. [{new_url.get('state', 'pending')}] {new_url['text'][:60]}...")
                            print(f"       -> {new_url['url'][:80]}...")
                            print(f"       Discovered: {new_url.get('discovered_at', 'N/A')}")

                        if len(page_change['new_urls']) > 5:
                            print(f"    ... and {len(page_change['new_urls']) - 5} more")
            else:
                print(f"No new URLs detected for {company_name}")

        print(f"\n{'=' * 80}")
        print("STORAGE INFORMATION")
        print(f"{'=' * 80}")
        print("Master URL tracking files: change_tracking/url_tracking-june_26-direct-IR-pages/")
        print("  - Format: CompanyName_master_urls.json (contains ALL historical URLs)")
        print("Change reports: change_tracking/changes/")
        print("  - Format: CompanyName-YYYYMMDD_HHMMSS.json")
        print("New URLs only: change_tracking/new_urls/")
        print("  - Format: CompanyName-YYYYMMDD_HHMMSS.json (contains ONLY newly discovered URLs)")
        print("Content hashes: change_tracking/content_hashes.json")


if __name__ == "__main__":
    # Run the enhanced test
    asyncio.run(test_enhanced_scraper())