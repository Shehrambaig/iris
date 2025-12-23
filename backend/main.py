"""
MarketPulse Backend API
Real-time stock data with Yahoo Finance, sentiment analysis, and external news search
"""

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import json
from datetime import datetime
import logging
import sys
import httpx

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

from services.stock_service import StockService
from services.news_service import NewsService
from services.sentiment_service import SentimentService
from services.tavily_service import TavilyService
from services.rag_service import RAGService

app = FastAPI(title="MarketPulse API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
# stock_service = StockService()  # DISABLED - Yahoo Finance blocking
news_service = NewsService()
sentiment_service = SentimentService()
tavily_service = TavilyService()
rag_service = RAGService()

# Connected WebSocket clients
connected_clients: List[WebSocket] = []
news_websocket_clients: List[WebSocket] = []


# Models
class StockRequest(BaseModel):
    symbols: List[str]


class SentimentRequest(BaseModel):
    text: str
    source: Optional[str] = "unknown"


class NewsSearchRequest(BaseModel):
    symbol: str
    query: str
    limit: int = 5


class RAGQueryRequest(BaseModel):
    question: str
    symbol: Optional[str] = None
    session_id: str = "default"


# Test endpoint for debugging - calls real news service
@app.get("/api/test/news")
async def test_news_endpoint(limit: int = 3):
    """Test endpoint that returns real news data"""
    logger.info(f"TEST ENDPOINT CALLED with limit={limit}")
    try:
        all_news = await news_service.get_all_companies_news(limit)
        logger.info(f"Got {len(all_news)} news items from service")

        # Add 'company' field for frontend compatibility (frontend expects both 'source' and 'company')
        for item in all_news:
            if 'company' not in item:
                item['company'] = item.get('source', 'Unknown')

        return {
            "count": len(all_news),
            "news": all_news,
            "debug": f"Successfully fetched {len(all_news)} items"
        }
    except Exception as e:
        logger.error(f"ERROR in test endpoint: {e}", exc_info=True)
        return {
            "count": 0,
            "news": [],
            "error": str(e)
        }


# Health check
@app.get("/health")
async def health_check():
    import os
    openai_key = os.getenv("OPENAI_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "yfinance": "active",
            "openai": "configured" if openai_key and openai_key != "YOUR_OPENAI_API_KEY_HERE" else "not configured",
            "tavily": "configured" if tavily_key and tavily_key != "YOUR_TAVILY_API_KEY_HERE" else "not configured"
        }
    }


# NASDAQ API Proxy endpoint
@app.get("/api/nasdaq/watchlist")
async def nasdaq_watchlist():
    """
    Proxy endpoint for NASDAQ API to avoid CORS issues
    Fetches live stock prices for all tracked companies
    """
    try:
        # All companies we're tracking
        symbols = [
            'nvda|stocks',
            'aapl|stocks',
            'goog|stocks',
            'msft|stocks',
            'amzn|stocks',
            'meta|stocks',
            'tsla|stocks',
            'amd|stocks',
            'nflx|stocks',
            'dis|stocks',
        ]

        # Build the URL
        base_url = "https://api.nasdaq.com/api/quote/watchlist"
        symbol_params = '&'.join([f'symbol={symbol}' for symbol in symbols])
        url = f"{base_url}?{symbol_params}&type=Rv"

        # Make the request to NASDAQ API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                },
                timeout=10.0
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="NASDAQ API error")

            return response.json()

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="NASDAQ API timeout")
    except Exception as e:
        logger.error(f"Error fetching NASDAQ data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Stock data endpoints
@app.get("/api/stock/{symbol}")
async def get_stock(symbol: str):
    """Get real-time stock data for a single symbol"""
    try:
        return await stock_service.get_stock_data(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stocks")
async def get_multiple_stocks(request: StockRequest):
    """Get real-time data for multiple stocks"""
    try:
        return await stock_service.get_multiple_stocks(request.symbols)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/index/{symbol}")
async def get_index(symbol: str):
    """Get real-time index data"""
    try:
        return await stock_service.get_index_data(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/candles/{symbol}")
async def get_candles(symbol: str, period: str = "6mo", interval: str = "1d"):
    """Get historical candlestick data"""
    try:
        return await stock_service.get_candle_data(symbol, period, interval)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# News endpoints
@app.get("/api/news/all")
async def get_all_news(limit: int = 50):
    """Get latest news from all companies (for homepage feed) - includes historical news"""
    try:
        # Get news from all companies (10 items per company, looking at last 5 scraper runs)
        all_news_items = await news_service.get_all_companies_news(
            limit_per_company=10,
            max_files_per_company=5
        )

        # Filter out navigation/skip links from old scraped data
        skip_titles = [
            'read more', 'load more', 'subscribe', 'skip news',
            'skip to main navigation', 'skip to content', 'skip to main',
            'skip navigation', 'menu', 'search'
        ]

        filtered_news = [
            item for item in all_news_items
            if item.get('title', '').lower() not in skip_titles
        ]

        return {
            "count": len(filtered_news),
            "news": filtered_news[:limit]
        }
    except Exception as e:
        print(f"Error fetching all news: {e}")
        return {"count": 0, "news": []}


@app.get("/api/news/{symbol}")
async def get_news(symbol: str, limit: int = 10, include_context: bool = True, skip_sentiment: bool = False):
    """
    Get combined financial news (scraper) + contextual news (Tavily) with sentiment analysis

    Args:
        symbol: Stock symbol
        limit: Number of financial news items to fetch
        include_context: Whether to fetch contextual news via Tavily for each financial news
        skip_sentiment: Skip sentiment analysis for faster response
    """
    try:
        # Get financial news from scraper
        financial_news = await news_service.get_financial_news(symbol, limit)

        enhanced_news = []

        for item in financial_news:
            # Analyze sentiment on financial news (skip if requested)
            if not skip_sentiment:
                financial_sentiment = await sentiment_service.analyze_text(item.get("title", ""))
                item["sentiment"] = financial_sentiment
            else:
                item["sentiment"] = {"label": "neutral", "score": 0.0}
            item["type"] = "financial"

            # If include_context is true, fetch related contextual news via Tavily
            contextual_news = []
            if include_context and item.get("title"):
                try:
                    # Search Tavily for context about this specific financial news
                    search_query = f"{symbol} {item.get('title', '')[:100]}"
                    tavily_results = await tavily_service.search_news(symbol, search_query, 2)

                    for tavily_item in tavily_results:
                        # Analyze sentiment on contextual news
                        context_sentiment = await sentiment_service.analyze_text(
                            tavily_item.get("title", "") + " " + tavily_item.get("content", "")
                        )
                        tavily_item["sentiment"] = context_sentiment
                        tavily_item["type"] = "contextual"
                        contextual_news.append(tavily_item)

                except Exception as e:
                    print(f"Error fetching contextual news for {symbol}: {e}")

            # Combine financial news with its contextual news
            enhanced_news.append({
                **item,
                "contextual_news": contextual_news,
                "has_context": len(contextual_news) > 0
            })

        return enhanced_news
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/news/search")
async def search_external_news(request: NewsSearchRequest):
    """Search external news using Tavily API"""
    try:
        # Search for external news
        external_news = await tavily_service.search_news(request.symbol, request.query, request.limit)

        # Analyze sentiment for each news item
        for item in external_news:
            sentiment = await sentiment_service.analyze_text(item.get("title", "") + " " + item.get("content", ""))
            item["sentiment"] = sentiment

        return {
            "symbol": request.symbol,
            "query": request.query,
            "results": external_news,
            "count": len(external_news)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/combined/{symbol}")
async def get_combined_news(symbol: str, limit: int = 5):
    """Get both financial and external news with sentiment analysis"""
    try:
        # Get financial news
        financial_news = await news_service.get_financial_news(symbol, limit)

        # Get external news using Tavily
        external_news = await tavily_service.search_news(
            symbol,
            f"{symbol} stock market news",
            limit
        )

        # Analyze sentiment for all news
        all_news = []

        for item in financial_news:
            sentiment = await sentiment_service.analyze_text(item.get("title", "") + " " + item.get("content", ""))
            item["sentiment"] = sentiment
            item["source_type"] = "financial"
            all_news.append(item)

        for item in external_news:
            sentiment = await sentiment_service.analyze_text(item.get("title", "") + " " + item.get("content", ""))
            item["sentiment"] = sentiment
            item["source_type"] = "external"
            all_news.append(item)

        # Sort by timestamp
        all_news.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)

        return {
            "symbol": symbol,
            "financial_news_count": len(financial_news),
            "external_news_count": len(external_news),
            "news": all_news[:limit * 2]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Sentiment analysis endpoint
@app.post("/api/sentiment/analyze")
async def analyze_sentiment(request: SentimentRequest):
    """Analyze sentiment of text"""
    try:
        return await sentiment_service.analyze_text(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sentiment/stocks")
async def get_stock_sentiments():
    """
    Get price-based sentiment for all watchlist stocks
    Uses live NASDAQ data (price changes, volume) to determine market sentiment
    """
    try:
        # Fetch live NASDAQ data
        nasdaq_data = await nasdaq_watchlist()

        if not nasdaq_data or 'data' not in nasdaq_data:
            raise HTTPException(status_code=500, detail="Failed to fetch NASDAQ data")

        rows = nasdaq_data['data'].get('rows', [])

        sentiments = []
        for stock in rows:
            # Analyze price-based sentiment
            price_sentiment = sentiment_service.analyze_price_sentiment(stock)

            sentiments.append({
                "symbol": stock['symbol'],
                "name": stock['name'],
                "price": stock['lastSale'],
                "change": stock['change'],
                "pctChange": stock['pctChange'],
                "volume": stock['volume'],
                "sentiment": price_sentiment
            })

        return {
            "count": len(sentiments),
            "stocks": sentiments,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching stock sentiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sentiment/stock/{symbol}")
async def get_stock_sentiment_with_news(symbol: str, include_news: bool = True):
    """
    Get combined sentiment for a specific stock
    Combines price data (70%) + news (30%) for comprehensive sentiment
    """
    try:
        # Fetch NASDAQ data for this stock
        nasdaq_data = await nasdaq_watchlist()

        if not nasdaq_data or 'data' not in nasdaq_data:
            raise HTTPException(status_code=500, detail="Failed to fetch NASDAQ data")

        rows = nasdaq_data['data'].get('rows', [])
        stock_data = next((s for s in rows if s['symbol'].upper() == symbol.upper()), None)

        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found in watchlist")

        # Get news text if requested
        news_text = None
        if include_news:
            financial_news = await news_service.get_financial_news(symbol, limit=3)
            if financial_news:
                # Combine top 3 news titles
                news_text = " ".join([news.get('title', '') for news in financial_news[:3]])

        # Get combined sentiment
        combined_sentiment = await sentiment_service.analyze_combined_sentiment(
            symbol=symbol,
            price_data=stock_data,
            news_text=news_text,
            price_weight=0.7,
            news_weight=0.3
        )

        return {
            "symbol": symbol,
            "name": stock_data['name'],
            "price": stock_data['lastSale'],
            "change": stock_data['change'],
            "pctChange": stock_data['pctChange'],
            "volume": stock_data['volume'],
            "sentiment": combined_sentiment,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sentiment for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time updates
@app.websocket("/ws/stock/{symbol}")
async def websocket_stock_updates(websocket: WebSocket, symbol: str):
    """WebSocket endpoint for real-time stock updates"""
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        while True:
            # Get latest stock data
            stock_data = await stock_service.get_stock_data(symbol)

            # Send to client
            await websocket.send_json({
                "type": "stock_update",
                "symbol": symbol,
                "data": stock_data,
                "timestamp": datetime.now().isoformat()
            })

            # Wait 1 second before next update
            await asyncio.sleep(30)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)


@app.websocket("/ws/news")
async def websocket_news_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time news updates"""
    await websocket.accept()
    news_websocket_clients.append(websocket)
    logger.info(f"News WebSocket client connected. Total clients: {len(news_websocket_clients)}")

    try:
        # Keep connection alive and listen for messages
        while True:
            # Wait for ping/pong to keep connection alive
            await asyncio.sleep(30)
            try:
                await websocket.send_json({"type": "ping", "timestamp": datetime.now().isoformat()})
            except:
                break
    except Exception as e:
        logger.error(f"News WebSocket error: {e}")
    finally:
        if websocket in news_websocket_clients:
            news_websocket_clients.remove(websocket)
        logger.info(f"News WebSocket client disconnected. Total clients: {len(news_websocket_clients)}")


# Background task to check for news and trigger external search
async def monitor_news_and_search(symbol: str):
    """Monitor for new financial news and trigger external search"""
    last_news_check = datetime.now()

    while True:
        try:
            # Check for new financial news
            news_items = await news_service.get_financial_news(symbol, limit=1)

            if news_items and len(news_items) > 0:
                latest_news = news_items[0]
                news_time = datetime.fromisoformat(latest_news.get("publishedAt", ""))

                # If there's new news, trigger external search
                if news_time > last_news_check:
                    print(f"New financial news detected for {symbol}, searching external sources...")

                    # Search external news
                    external_news = await tavily_service.search_news(
                        symbol,
                        latest_news.get("title", f"{symbol} news"),
                        limit=5
                    )

                    # Analyze sentiment for all news
                    combined_results = {
                        "symbol": symbol,
                        "financial_news": latest_news,
                        "external_news": external_news,
                        "timestamp": datetime.now().isoformat()
                    }

                    # Broadcast to all connected clients
                    for client in connected_clients:
                        try:
                            await client.send_json({
                                "type": "news_update",
                                "data": combined_results
                            })
                        except:
                            pass

                    last_news_check = news_time

            # Check every 30 seconds
            await asyncio.sleep(30)

        except Exception as e:
            print(f"Error in news monitoring: {e}")
            await asyncio.sleep(30)


# RAG Chat endpoints
@app.post("/api/rag/query")
async def rag_query(request: RAGQueryRequest):
    """Ask a question using RAG"""
    try:
        # Get additional context if symbol provided
        context = None
        if request.symbol:
            context = await rag_service.get_company_info(request.symbol)

        result = await rag_service.query(
            question=request.question,
            symbol=request.symbol,
            context=context,
            session_id=request.session_id
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/query-stream")
async def rag_query_stream(request: RAGQueryRequest):
    """Ask a question using RAG with streaming response and web search"""
    from fastapi.responses import StreamingResponse

    try:
        # Get additional context if symbol provided
        context = None
        if request.symbol:
            context = await rag_service.get_company_info(request.symbol)

        # Return streaming response
        return StreamingResponse(
            rag_service.query_stream(
                question=request.question,
                symbol=request.symbol,
                context=context,
                session_id=request.session_id,
                use_web_search=True  # Enable web search by default
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/clear-history")
async def clear_rag_history(session_id: str = "default"):
    """Clear RAG conversation history"""
    try:
        rag_service.clear_history(session_id)
        return {"success": True, "message": "Conversation history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rag/history/{session_id}")
async def get_rag_history(session_id: str):
    """Get RAG conversation history"""
    try:
        history = rag_service.get_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints
@app.post("/api/admin/run-scraper")
async def trigger_scraper(background_tasks: BackgroundTasks):
    """Manually trigger the news scraper"""
    try:
        global scraper_running

        if scraper_running:
            return {
                "status": "already_running",
                "message": "Scraper is already running. Please wait for it to complete."
            }

        # Run scraper in the background
        background_tasks.add_task(run_scraper_once)

        return {
            "status": "started",
            "message": "Scraper started in background. Check logs for progress."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/scraper-status")
async def get_scraper_status():
    """Get scraper status"""
    global scraper_running
    return {
        "running": scraper_running,
        "auto_scraper_enabled": scraper_task is not None
    }


# Background task for scraper
scraper_task = None
scraper_running = False
news_watcher_task = None

async def broadcast_news_to_clients(news_items: List[Dict]):
    """Broadcast new news to all connected WebSocket clients"""
    if not news_websocket_clients:
        return

    message = {
        "type": "news_update",
        "news": news_items,
        "timestamp": datetime.now().isoformat()
    }

    # Broadcast to all connected clients
    disconnected = []
    for client in news_websocket_clients:
        try:
            await client.send_json(message)
            logger.info(f"Broadcasted {len(news_items)} news items to client")
        except Exception as e:
            logger.error(f"Failed to send to client: {e}")
            disconnected.append(client)

    # Remove disconnected clients
    for client in disconnected:
        if client in news_websocket_clients:
            news_websocket_clients.remove(client)

async def watch_scraper_output():
    """Watch for new scraper output files, process them into RAG, and broadcast news in real-time"""
    from pathlib import Path
    import json
    from services.news_processor_service import NewsProcessorService

    # Use environment variable for scraper output path (supports both local and Render deployment)
    scraper_output_path = os.getenv("SCRAPER_OUTPUT_PATH")
    if scraper_output_path:
        scraper_output_dir = Path(scraper_output_path)
    else:
        # Default to local development path
        scraper_output_dir = Path(__file__).parent.parent / "scraper" / "src" / "change_tracking" / "new_urls"

    if not scraper_output_dir.exists():
        logger.warning(f"Scraper output directory not found: {scraper_output_dir}")
        logger.info("Creating directory for scraper output...")
        scraper_output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize news processor service
    news_processor = NewsProcessorService(
        rag_engine=rag_service.rag_engine,
        news_service=news_service
    )

    # Track files we've already processed
    processed_files = set()

    # Initial scan - mark all existing files as processed
    for file_path in scraper_output_dir.glob("*.json"):
        processed_files.add(str(file_path))

    logger.info(f"News watcher started. Monitoring: {scraper_output_dir}")
    print(f"[NEWS WATCHER] Started monitoring: {scraper_output_dir}")
    print(f"[NEWS WATCHER] Already processed {len(processed_files)} existing files")

    while True:
        try:
            # Check for new files
            current_files = set(str(f) for f in scraper_output_dir.glob("*.json"))
            new_files = current_files - processed_files

            if new_files:
                logger.info(f"Detected {len(new_files)} new scraper output file(s)")
                print(f"[NEWS WATCHER] 🔔 Detected {len(new_files)} new file(s)!")

                # Process each new file
                for file_path_str in new_files:
                    try:
                        # Process news articles and add to RAG
                        news_result = await news_processor.process_news_file(file_path_str)
                        logger.info(
                            f"RAG Processing: {news_result['processed']} articles added, "
                            f"{news_result['failed']} failed, {news_result['skipped']} skipped"
                        )

                        # Also broadcast to WebSocket clients
                        with open(file_path_str, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        company_name = data.get('company_name', 'Unknown')
                        new_urls = data.get('new_urls', [])
                        discovery_timestamp = data.get('discovery_timestamp', '')

                        # Convert to news format
                        news_items = []
                        for url_data in new_urls:
                            # Filter out non-news URLs
                            if news_service._is_news_article(url_data, company_name):
                                title = url_data.get('text', 'No title')

                                # Clean up malformed titles
                                if len(title) > 200 or '{' in title or 'background:' in title:
                                    url = url_data.get('url', '')
                                    title = url.rstrip('/').split('/')[-1].replace('-', ' ').title()

                                news_items.append({
                                    'id': url_data.get('url', ''),
                                    'title': title,
                                    'content': '',
                                    'source': company_name,
                                    'company': company_name,
                                    'publishedAt': url_data.get('discovered_at', discovery_timestamp),
                                    'url': url_data.get('url', ''),
                                    'thumbnail': ''
                                })

                        if news_items:
                            logger.info(f"Broadcasting {len(news_items)} new articles from {company_name}")
                            await broadcast_news_to_clients(news_items)

                        processed_files.add(file_path_str)

                    except Exception as e:
                        logger.error(f"Error processing new file {file_path_str}: {e}")
                        processed_files.add(file_path_str)  # Mark as processed to avoid retry loops

            # Check every 2 seconds for new files
            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Error in news watcher: {e}")
            await asyncio.sleep(5)

def _run_scraper_subprocess():
    """Helper function to run scraper in a thread (blocking operation)"""
    import subprocess
    import sys
    from pathlib import Path

    # Path to the scraper script
    scraper_script = Path(__file__).parent.parent / "scraper" / "src" / "run_scraper.py"

    if not scraper_script.exists():
        logger.error(f"Scraper script not found: {scraper_script}")
        return {"status": "error", "error": "Scraper script not found"}

    logger.info("Running scraper scan as subprocess...")

    # Run the scraper as a separate Python subprocess
    # This avoids the asyncio.create_subprocess_exec issue in Python 3.14
    process = subprocess.Popen(
        [sys.executable, str(scraper_script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(scraper_script.parent)
    )

    # Wait for completion (blocking)
    stdout, stderr = process.communicate()
    success = process.returncode == 0

    if success:
        logger.info(f"Scraper scan completed successfully")
        logger.debug(f"Scraper output: {stdout[:500]}...")  # Log first 500 chars
    else:
        logger.error(f"Scraper scan failed with code {process.returncode}")
        logger.error(f"Scraper error: {stderr[:500]}...")

    return {"status": "completed", "success": success, "returncode": process.returncode}

async def run_scraper_once():
    """Run the scraper one time as a separate subprocess (Windows Python 3.14 workaround)"""
    global scraper_running

    if scraper_running:
        logger.warning("Scraper is already running, skipping this request")
        return {"status": "already_running"}

    scraper_running = True

    try:
        # Run the blocking subprocess in a thread pool to avoid blocking FastAPI
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _run_scraper_subprocess)
        return result
    except Exception as e:
        logger.error(f"Error running scraper subprocess: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        scraper_running = False

async def run_scraper_periodically():
    """Run the scraper every 3 hours in the background"""
    logger.info("[OK] Scraper scheduled (runs every 3 hours)")

    # Skip initial run - only run on schedule
    # This prevents errors if Playwright isn't installed yet
    # To run scraper manually: POST /api/admin/run-scraper
    logger.info("Scraper will run automatically every 3 hours")
    logger.info("To run now: POST /api/admin/run-scraper")

    # Run every 3 hours
    while True:
        await asyncio.sleep(3 * 60 * 60)  # 3 hours
        logger.info("Running scheduled scraper scan...")
        await run_scraper_once()

@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup"""
    global scraper_task
    import os
    import sys
    import asyncio

    # Fix for Windows + Python 3.14 subprocess issue with Playwright
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        logger.info("Set Windows ProactorEventLoop for subprocess support")

    print("\n" + "="*50)
    print("MarketPulse API Starting...")
    print("="*50)
    print("Yahoo Finance integration: Active")

    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")

    if openai_key and openai_key != "YOUR_OPENAI_API_KEY_HERE":
        print(f"OpenAI API: CONNECTED (key: {openai_key[:20]}...)")
        print("Sentiment Analysis: GPT-4o-mini Active")
        print("RAG Chat: GPT-4o-mini Active")
    else:
        print("OpenAI API: NOT CONFIGURED (using keyword fallback)")
        print("Sentiment Analysis: Keyword-based fallback")
        print("RAG Chat: Disabled")

    if tavily_key and tavily_key != "YOUR_TAVILY_API_KEY_HERE":
        print(f"Tavily API: CONNECTED (key: {tavily_key[:20]}...)")
        print("External News Search: Active")
    else:
        print("Tavily API: NOT CONFIGURED")
        print("External News Search: Disabled")

    # Start scraper background task
    print("\n" + "="*50)
    print("Background Services Status...")
    print("="*50)
    try:
        scraper_task = asyncio.create_task(run_scraper_periodically())
        print("[OK] Scraper: Auto-refresh enabled (runs every 3 hours)")
        print("    Manual trigger: POST /api/admin/run-scraper")
    except Exception as e:
        logger.error(f"Failed to start automatic scraper: {e}")
        print("[NOTE] Scraper: Manual mode only (use /api/admin/run-scraper endpoint)")
    print("       Existing scraped news is available and being served")

    # Start news watcher for real-time WebSocket updates (disabled in production)
    enable_file_watcher = os.getenv("ENABLE_FILE_WATCHER", "true").lower() == "true"
    if enable_file_watcher:
        try:
            global news_watcher_task
            news_watcher_task = asyncio.create_task(watch_scraper_output())
            print("[OK] News Watcher: Real-time WebSocket updates enabled")
            print("    WebSocket endpoint: ws://localhost:8000/ws/news")
        except Exception as e:
            logger.error(f"Failed to start news watcher: {e}")
            print("[NOTE] News Watcher: Disabled (manual refresh only)")
    else:
        print("[INFO] News Watcher: Disabled (ENABLE_FILE_WATCHER=false)")
        print("[NOTE] On Render: Scraper runs on separate service with separate filesystem")

    # RAG is already initialized by rag_service = RAGService() at the top
    if rag_service.rag_engine:
        print("[OK] RAG Engine: Loaded with {} documents".format(
            rag_service.rag_engine.vector_store.size if hasattr(rag_service.rag_engine, 'vector_store') else 0
        ))
    else:
        print("[X] RAG Engine: Not initialized (add documents to enable)")

    print("="*50 + "\n")


if __name__ == "__main__":
    import uvicorn
    import sys
    import asyncio

    # Fix for Windows + Python 3.14 subprocess issue with Playwright
    if sys.platform == 'win32':
        # Use ProactorEventLoop on Windows for subprocess support
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
