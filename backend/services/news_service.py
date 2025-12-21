"""
News Service - Iris Scraper Integration
Provides financial news from company investor relations pages
"""

import json
import glob
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import re


class NewsService:
    def __init__(self):
        # Path to scraper data
        self.scraper_path = Path(__file__).parent.parent.parent / "scraper" / "src"
        self.new_urls_path = self.scraper_path / "change_tracking" / "new_urls"

        # Company symbol mapping (same as in stock service)
        self.symbol_to_company = {
            "NVDA": "NVIDIA",
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Alphabet",
            "GOOG": "Alphabet",
            "AMZN": "Amazon",
            "AVGO": "Broadcom",
            "META": "Meta",
            "TSLA": "Tesla",
            "BRK.B": "Berkshire_Hathaway",
            "JPM": "JPMorgan_Chase",
            "PORSCHE": "Porsche",
        }

        # Domain patterns for each company to filter out contaminated URLs
        self.company_domains = {
            "NVIDIA": ["nvidia.com", "nvidianews"],
            "Apple": ["apple.com", "investor.apple"],
            "Microsoft": ["microsoft.com", "investor.microsoft"],
            "Alphabet": ["abc.xyz", "google.com", "blog.google"],
            "Amazon": ["aboutamazon.com", "press.aboutamazon", "ir.aboutamazon"],
            "Broadcom": ["broadcom.com", "investors.broadcom"],
            "Meta": ["meta.com", "investor.atmeta", "investor.fb"],
            "Tesla": ["tesla.com", "ir.tesla"],
            "Berkshire_Hathaway": ["berkshirehathaway.com"],
            "JPMorgan_Chase": ["jpmorganchase.com"],
            "Porsche": ["porsche.com", "newsroom.porsche"],
        }

    def _url_matches_company_domain(self, url: str, company_name: str) -> bool:
        """Check if URL domain matches the company (to filter out contaminated URLs)"""
        url_lower = url.lower()
        domains = self.company_domains.get(company_name, [])

        for domain in domains:
            if domain.lower() in url_lower:
                return True

        return False

    def _is_news_article(self, url_data: Dict, company_name: Optional[str] = None) -> bool:
        """Filter out navigation links and keep only news articles"""
        url = url_data.get('url', '').lower()
        text = url_data.get('text', '').lower()

        # CRITICAL: Filter out URLs that don't match the company domain (page contamination fix)
        if company_name and not self._url_matches_company_domain(url, company_name):
            return False

        # Skip if text is "read more" or similar short non-descriptive text
        skip_texts = [
            'read more', 'load more', 'subscribe', 'skip news',
            'skip to main navigation', 'skip to content', 'skip to main',
            'skip navigation', 'menu', 'search'
        ]
        if text.lower() in skip_texts:
            return False

        # Exclude social media and generic navigation links
        exclude_patterns = [
            'twitter.com', 'linkedin.com', 'facebook.com', 'instagram.com', 'youtube.com',
            'about-us', 'contact-us', 'careers', 'login', 'signup',
            'terms-of', 'privacy-policy', 'conditions-of-use', 'cookie',
            'images-and-videos', '/images/', '/videos/',
            '/page/', '/tag/', '/category/', '/search/',
        ]

        for pattern in exclude_patterns:
            if pattern in url:
                return False

        # Include links that look like news articles (contain dates or news-related keywords)
        include_patterns = [
            r'/\d{4}/', # Year in URL (e.g., /2025/)
            r'/\d{2}/',  # Month in URL
            'press-release', 'press-center', '/news', 'announcement',
            'financial', 'earnings', 'investor', 'quarterly', 'results',
            'ir.', 'investors.', '/aws/'
        ]

        for pattern in include_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                # Title should be descriptive (longer than just a few words)
                if len(text) > 20:
                    return True

        return False

    def _get_latest_news_files(self, company_name: Optional[str] = None, limit: int = 5) -> List[Path]:
        """Get the most recent news files"""
        pattern = f"{company_name}-*.json" if company_name else "*.json"
        files = list(self.new_urls_path.glob(pattern))

        # Sort by modification time (most recent first)
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        return files[:limit]

    async def get_financial_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Get latest financial news for a stock symbol"""
        try:
            # Map symbol to company name
            company_name = self.symbol_to_company.get(symbol.upper())
            if not company_name:
                return []

            # Due to page contamination bug, search ALL scraper files for URLs matching this company's domain
            # (e.g., NVIDIA news might be in Amazon's file and vice versa)
            all_news_files = list(self.new_urls_path.glob("*.json"))

            if not all_news_files:
                return []

            # Sort by modification time (most recent first)
            all_news_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            all_news = []

            # Search through all files (limit to recent 20 files for performance)
            for file_path in all_news_files[:20]:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    discovery_timestamp = data.get('discovery_timestamp', '')
                    new_urls = data.get('new_urls', [])

                    # Filter for URLs matching this company's domain
                    for url_data in new_urls:
                        if self._is_news_article(url_data, company_name):
                            # Extract title - use URL path if text is CSS/short
                            title = url_data.get('text', 'No title')
                            if len(title) > 200 or '{' in title or 'background:' in title:
                                # Title is CSS/malformed, extract from URL
                                url = url_data.get('url', '')
                                # Get last path segment and clean it
                                title = url.rstrip('/').split('/')[-1].replace('-', ' ').title()

                            all_news.append({
                                'id': url_data.get('url', ''),
                                'title': title,
                                'content': '',
                                'source': company_name,
                                'publishedAt': url_data.get('discovered_at', discovery_timestamp),
                                'url': url_data.get('url', ''),
                                'symbol': symbol,
                                'thumbnail': ''
                            })

                except Exception as e:
                    print(f"Error reading news file {file_path}: {e}")
                    continue

            # Sort by published date (most recent first)
            all_news.sort(key=lambda x: x['publishedAt'], reverse=True)

            # Return limited number of results
            return all_news[:limit]

        except Exception as e:
            print(f"Error fetching news for {symbol}: {e}")
            return []

    async def get_all_companies_news(self, limit_per_company: int = 10, max_files_per_company: int = 5) -> List[Dict]:
        """Get news from all tracked companies (including historical news)"""
        try:
            # Get all files
            all_files = list(self.new_urls_path.glob("*.json"))

            if not all_files:
                return []

            # Group files by company
            companies_files = {}
            for file_path in all_files:
                # Extract company name from filename (e.g., "NVIDIA-20251130_121919.json" -> "NVIDIA")
                company_name = file_path.stem.rsplit('-', 1)[0]

                if company_name not in companies_files:
                    companies_files[company_name] = []
                companies_files[company_name].append(file_path)

            all_news = []

            for company_name, files in companies_files.items():
                # Sort files by modification time (newest first) and take recent ones
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                recent_files = files[:max_files_per_company]

                news_count = 0

                # Process recent files for this company
                for file_path in recent_files:
                    if news_count >= limit_per_company:
                        break

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        company = data.get('company_name', company_name)
                        discovery_timestamp = data.get('discovery_timestamp', '')
                        new_urls = data.get('new_urls', [])

                        # Get news from this file with domain filtering
                        for url_data in new_urls:
                            if news_count >= limit_per_company:
                                break

                            if self._is_news_article(url_data, company_name):
                                # Extract title - use URL path if text is CSS/short
                                title = url_data.get('text', 'No title')
                                if len(title) > 200 or '{' in title or 'background:' in title:
                                    # Title is CSS/malformed, extract from URL
                                    url = url_data.get('url', '')
                                    # Get last path segment and clean it
                                    title = url.rstrip('/').split('/')[-1].replace('-', ' ').title()

                                all_news.append({
                                    'id': url_data.get('url', ''),
                                    'title': title,
                                    'content': '',
                                    'source': company,
                                    'publishedAt': url_data.get('discovered_at', discovery_timestamp),
                                    'url': url_data.get('url', ''),
                                    'symbol': '',
                                    'thumbnail': ''
                                })
                                news_count += 1

                    except Exception as e:
                        print(f"Error reading news file {file_path}: {e}")
                        continue

            # Sort all news by published date (newest first)
            all_news.sort(key=lambda x: x['publishedAt'], reverse=True)

            return all_news

        except Exception as e:
            print(f"Error fetching all companies news: {e}")
            return []
