"""
News Processor Service
Fetches, extracts, and processes scraped news articles into the RAG system
"""
import asyncio
import aiohttp
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from readability import Document as ReadabilityDocument
import logging

logger = logging.getLogger(__name__)


class NewsProcessorService:
    """Service to process scraped news URLs and add them to RAG"""

    def __init__(self, rag_engine, news_service):
        """
        Initialize the news processor

        Args:
            rag_engine: RAGEngine instance from rag_service
            news_service: NewsService instance for filtering
        """
        self.rag_engine = rag_engine
        self.news_service = news_service
        self.processed_urls = set()  # In-memory cache for deduplication

    async def process_news_file(self, file_path: str) -> Dict:
        """
        Process all news URLs in a scraper JSON file

        Args:
            file_path: Path to the JSON file containing scraped URLs

        Returns:
            Dict with processing statistics
        """
        stats = {
            "file": file_path,
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }

        try:
            # Load JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            company_name = data.get('company_name', 'Unknown')
            new_urls = data.get('new_urls', [])

            # Filter to news URLs only using existing filter
            news_urls = [
                url_data for url_data in new_urls
                if self.news_service._is_news_article(url_data, company_name)
            ]

            logger.info(f"Processing {len(news_urls)}/{len(new_urls)} news URLs from {company_name}")

            # Process each URL
            for url_data in news_urls:
                url = url_data.get('url', '')
                state = url_data.get('state', 'pending')

                # Skip if already processed
                if state == 'processed' or url in self.processed_urls:
                    stats['skipped'] += 1
                    continue

                # Fetch and process
                try:
                    # Fetch HTML
                    fetch_result = await self.fetch_article_content(url)
                    if not fetch_result['success']:
                        stats['failed'] += 1
                        stats['errors'].append(f"{url}: {fetch_result['error']}")
                        await self.update_url_state(file_path, url, 'failed')
                        continue

                    # Extract text
                    extract_result = await self.extract_clean_text(
                        fetch_result['html'], url
                    )

                    if not extract_result['text'] or len(extract_result['text']) < 100:
                        stats['failed'] += 1
                        stats['errors'].append(f"{url}: Insufficient content extracted")
                        await self.update_url_state(file_path, url, 'failed')
                        continue

                    # Add to RAG
                    success = await self.add_to_rag(
                        extract_result['text'],
                        url_data,
                        company_name,
                        extract_result['title']
                    )

                    if success:
                        stats['processed'] += 1
                        self.processed_urls.add(url)
                        await self.update_url_state(file_path, url, 'processed')
                    else:
                        stats['failed'] += 1
                        stats['errors'].append(f"{url}: Failed to add to RAG")
                        await self.update_url_state(file_path, url, 'failed')

                    # Rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    stats['failed'] += 1
                    stats['errors'].append(f"{url}: {str(e)}")
                    logger.error(f"Error processing {url}: {e}")

            return stats

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            stats['errors'].append(f"File error: {str(e)}")
            return stats

    async def fetch_article_content(self, url: str, timeout: int = 30) -> Dict:
        """
        Fetch HTML content from URL with retry logic

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            Dict with success status, HTML content, and error info
        """
        max_retries = 3

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                        headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'}
                    ) as response:
                        if response.status == 200:
                            html = await response.text()
                            return {"success": True, "html": html, "status_code": 200, "error": None}
                        elif response.status in [429, 503]:
                            # Rate limited - retry with backoff
                            logger.warning(f"Rate limited on {url}, attempt {attempt + 1}")
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            return {
                                "success": False,
                                "html": "",
                                "status_code": response.status,
                                "error": f"HTTP {response.status}"
                            }

            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url}, attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return {"success": False, "html": "", "status_code": 0, "error": "Timeout"}

            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return {"success": False, "html": "", "status_code": 0, "error": str(e)}

        return {"success": False, "html": "", "status_code": 0, "error": "Max retries exceeded"}

    async def extract_clean_text(self, html: str, url: str) -> Dict:
        """
        Extract clean text from HTML using multiple strategies

        Tries in order: readability-lxml → article tag → main tag → paragraphs

        Args:
            html: HTML content
            url: Source URL (for error logging)

        Returns:
            Dict with title, text, and extraction method used
        """
        # Strategy 1: readability-lxml (best for article extraction)
        try:
            doc = ReadabilityDocument(html)
            title = doc.title()
            content_html = doc.summary()
            # Convert to plain text
            soup = BeautifulSoup(content_html, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            if len(text) > 100:
                return {"title": title, "text": text, "extracted_by": "readability"}
        except Exception as e:
            logger.debug(f"Readability failed for {url}: {e}")

        # Strategy 2: BeautifulSoup <article> tag
        try:
            soup = BeautifulSoup(html, 'html.parser')
            article = soup.find('article')
            if article:
                title_tag = soup.find('h1')
                title_text = title_tag.get_text(strip=True) if title_tag else ""
                text = article.get_text(separator='\n', strip=True)
                if len(text) > 100:
                    return {"title": title_text, "text": text, "extracted_by": "article_tag"}
        except Exception as e:
            logger.debug(f"Article tag extraction failed for {url}: {e}")

        # Strategy 3: BeautifulSoup <main> tag
        try:
            soup = BeautifulSoup(html, 'html.parser')
            main = soup.find('main')
            if main:
                title_tag = soup.find('h1')
                title_text = title_tag.get_text(strip=True) if title_tag else ""
                text = main.get_text(separator='\n', strip=True)
                if len(text) > 100:
                    return {"title": title_text, "text": text, "extracted_by": "main_tag"}
        except Exception as e:
            logger.debug(f"Main tag extraction failed for {url}: {e}")

        # Strategy 4: All paragraphs (fallback)
        try:
            soup = BeautifulSoup(html, 'html.parser')
            title_tag = soup.find('h1')
            title_text = title_tag.get_text(strip=True) if title_tag else urlparse(url).path.split('/')[-1]
            paragraphs = soup.find_all('p')
            text = '\n'.join(p.get_text(strip=True) for p in paragraphs)
            if len(text) > 100:
                return {"title": title_text, "text": text, "extracted_by": "paragraphs"}
        except Exception as e:
            logger.debug(f"Paragraph extraction failed for {url}: {e}")

        # All strategies failed
        return {
            "title": urlparse(url).path.split('/')[-1],
            "text": "",
            "extracted_by": "none",
            "error": "All extraction strategies failed"
        }

    async def add_to_rag(self, text: str, url_data: Dict,
                         company_name: str, title: str) -> bool:
        """
        Add article to RAG with enhanced metadata

        Args:
            text: Extracted article text
            url_data: Original URL data from scraper JSON
            company_name: Company that published the news
            title: Extracted article title

        Returns:
            True if successfully added, False otherwise
        """
        try:
            url = url_data.get('url', '')
            discovered_at = url_data.get('discovered_at', '')

            # Build enhanced metadata
            metadata = {
                "source_type": "scraped_news",
                "company_name": company_name,
                "original_url": url,
                "domain": urlparse(url).netloc,
                "article_title": title or url_data.get('text', 'Untitled'),
                "discovery_timestamp": discovered_at,
                "processing_timestamp": datetime.now().isoformat(),
                "content_hash": hashlib.md5(text.encode()).hexdigest(),
            }

            # Add to RAG in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.rag_engine.add_text(text, url, metadata)
            )

            logger.info(f"Added to RAG: {title} ({result['num_chunks']} chunks)")
            return True

        except Exception as e:
            logger.error(f"Failed to add to RAG: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def update_url_state(self, file_path: str, url: str, new_state: str) -> bool:
        """
        Update URL state in JSON file

        Args:
            file_path: Path to JSON file
            url: URL to update
            new_state: New state value ("processed" or "failed")

        Returns:
            True if update succeeded, False otherwise
        """
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Find and update URL
            updated = False
            for url_obj in data.get('new_urls', []):
                if url_obj['url'] == url:
                    url_obj['state'] = new_state
                    url_obj['processed_at'] = datetime.now().isoformat()
                    updated = True
                    break

            if not updated:
                logger.warning(f"URL not found in file for state update: {url}")
                return False

            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Failed to update state for {url}: {e}")
            return False
