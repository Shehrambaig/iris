# MarketPulse Backend API

Real-time stock market data with sentiment analysis and intelligent news aggregation.

## Features

- 📈 **Yahoo Finance Integration** - Real-time stock data (FREE)
- 🧠 **AI Sentiment Analysis** - Analyzes news sentiment using RoBERTa model
- 🔍 **Tavily News Search** - External news aggregation agent
- ⚡ **WebSocket Support** - Real-time price updates
- 🎯 **Dual News Sources** - Financial + External news with sentiment

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```
TAVILY_API_KEY=your_tavily_api_key_here
```

**Get API Keys:**
- Tavily: https://tavily.com (for external news search)
- Yahoo Finance: No API key needed! (it's free)

### 3. Run the Server

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --port 8000
```

The API will be available at: `http://localhost:8000`

## API Endpoints

### Stock Data

```bash
# Get single stock
GET /api/stock/NVDA

# Get multiple stocks
POST /api/stocks
Body: {"symbols": ["AAPL", "NVDA", "TSLA"]}

# Get index data
GET /api/index/SPX

# Get candlestick data
GET /api/candles/NVDA?period=6mo&interval=1d
```

### News & Sentiment

```bash
# Get financial news with sentiment
GET /api/news/NVDA?limit=10

# Search external news (Tavily)
POST /api/news/search
Body: {
  "symbol": "NVDA",
  "query": "NVIDIA AI chips",
  "limit": 5
}

# Get combined news (financial + external)
GET /api/news/combined/NVDA?limit=5

# Analyze sentiment
POST /api/sentiment/analyze
Body: {"text": "Stock prices surge on positive earnings"}
```

### Real-time Updates

```javascript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/stock/NVDA');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Stock update:', data);
};
```

## Architecture

### Services

1. **StockService** - Yahoo Finance integration
   - Real-time price data
   - Historical candles
   - Index data

2. **NewsService** - Financial news from Yahoo Finance
   - Company-specific news
   - Financial events
   - Earnings reports

3. **SentimentService** - AI sentiment analysis
   - RoBERTa model (advanced)
   - Keyword fallback (simple)
   - -1 to 1 sentiment score

4. **TavilyService** - External news search agent
   - Web search for related news
   - Auto-triggers on financial news
   - Filters by financial sources

### News Agent Workflow

```
Financial News Detected
    ↓
Tavily Agent Searches External News
    ↓
Sentiment Analysis on Both Sources
    ↓
Combined Results Sent to Frontend
```

## Configuration

### Sentiment Analysis

The backend uses transformers for advanced sentiment analysis. If transformers is not available (requires PyTorch), it falls back to keyword-based analysis.

**For full AI features:**
```bash
pip install transformers torch
```

**For lightweight setup (keyword-based only):**
```bash
# Just install core dependencies
pip install fastapi uvicorn yfinance aiohttp pydantic
```

### API Keys

- **Yahoo Finance**: No key needed (free)
- **Tavily**: Required for external news search
- **Transformers**: Optional (uses open-source models)

## Development

### Project Structure

```
backend/
├── main.py                 # FastAPI application
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── services/
│   ├── __init__.py
│   ├── stock_service.py   # Yahoo Finance
│   ├── news_service.py    # Financial news
│   ├── sentiment_service.py # AI sentiment
│   └── tavily_service.py  # External news agent
```

### Testing

```bash
# Health check
curl http://localhost:8000/health

# Test stock endpoint
curl http://localhost:8000/api/stock/NVDA

# Test news with sentiment
curl http://localhost:8000/api/news/NVDA
```

## Frontend Integration

Update `src/services/api.ts` to use this backend:

```typescript
const API_BASE = 'http://localhost:8000';

export const stockApi = {
  getStock: (symbol: string) =>
    fetch(`${API_BASE}/api/stock/${symbol}`).then(r => r.json()),

  getCandles: (symbol: string) =>
    fetch(`${API_BASE}/api/candles/${symbol}`).then(r => r.json()),

  getNews: (symbol: string) =>
    fetch(`${API_BASE}/api/news/combined/${symbol}`).then(r => r.json()),
};
```

## Production Deployment

1. Set production environment variables
2. Use a production ASGI server
3. Enable HTTPS
4. Configure CORS for your domain
5. Add rate limiting
6. Monitor API usage

```bash
# Production with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## License

MIT
