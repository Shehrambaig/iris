"""
Tavily Service - External News Search Agent
Searches web for external news using Tavily API
"""

import os
import aiohttp
from typing import List, Dict
from datetime import datetime


class TavilyService:
    def __init__(self):
        """Initialize Tavily service"""
        # Get API key from environment variable
        self.api_key = os.getenv("TAVILY_API_KEY", "YOUR_TAVILY_API_KEY_HERE")
        self.api_url = "https://api.tavily.com/search"

        if self.api_key == "YOUR_TAVILY_API_KEY_HERE":
            print("WARNING: Tavily API key not set. Add TAVILY_API_KEY to environment variables.")
            print("   Get your key at: https://tavily.com")

    async def search_news(self, symbol: str, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for external news using Tavily API

        Args:
            symbol: Stock symbol
            query: Search query
            limit: Maximum number of results

        Returns:
            List of news articles with sentiment
        """
        if self.api_key == "YOUR_TAVILY_API_KEY_HERE":
            print(f"Tavily API key not configured, returning empty results for {symbol}")
            return []

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "basic",
                    "include_answer": False,
                    "include_images": False,
                    "include_raw_content": False,
                    "max_results": limit,
                    "include_domains": [
                        "cnbc.com",
                        "reuters.com",
                        "bloomberg.com",
                        "wsj.com",
                        "marketwatch.com",
                        "seekingalpha.com",
                        "benzinga.com"
                    ]
                }

                async with session.post(self.api_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Tavily API error: {response.status} - {error_text}")
                        return []

                    data = await response.json()
                    results = data.get("results", [])

                    # Format results
                    articles = []
                    for idx, item in enumerate(results):
                        articles.append({
                            "id": f"tavily_{symbol}_{idx}",
                            "title": item.get("title", ""),
                            "content": item.get("content", ""),
                            "source": item.get("url", "").split("/")[2] if item.get("url") else "Unknown",
                            "publishedAt": item.get("published_date", datetime.now().isoformat()),
                            "url": item.get("url", ""),
                            "symbol": symbol,
                            "score": item.get("score", 0),  # Relevance score from Tavily
                        })

                    return articles

        except Exception as e:
            print(f"Error searching Tavily for {symbol}: {e}")
            return []

    async def search_related_news(self, symbol: str, financial_news_title: str, limit: int = 5) -> List[Dict]:
        """
        Search for external news related to a financial news event

        This is triggered when financial news is detected
        """
        # Create a search query based on the financial news
        query = f"{symbol} {financial_news_title} stock market analysis"

        return await self.search_news(symbol, query, limit)
