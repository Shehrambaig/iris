# MarketPulse - Complete Setup Guide

## Overview

MarketPulse is a real-time financial trading dashboard with:
- ✅ **Yahoo Finance** integration (FREE - no API key needed!)
- 🧠 **AI Sentiment Analysis** on news
- 🔍 **Tavily** external news search agent
- 📊 **Real-time candlestick charts** with event markers
- ⚡ **WebSocket** live updates

---

## Quick Start (5 Minutes)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Start the backend server
python main.py
```

The backend will start at `http://localhost:8000`

✅ **Yahoo Finance works immediately** - no API key needed!

### 2. Frontend Setup

```bash
# Navigate back to project root
cd ..

# Install Node dependencies (if not already done)
npm install

# Start frontend development server
npm run dev
```

The frontend will start at `http://localhost:5173` (or another port if 5173 is busy)

---

## Features & Configuration

### 🆓 Free Features (Works Out of the Box)

These work immediately without any configuration:

1. **Real-time Stock Data** - Yahoo Finance
2. **Live Candlestick Charts** - Historical & real-time
3. **Index Data** - SPX, NASDAQ, DJI, VIX, DXY
4. **Financial News** - From Yahoo Finance
5. **Basic Sentiment Analysis** - Keyword-based

### 🔑 Premium Features (Requires API Keys)

To enable these advanced features, add API keys to `backend/.env`:

#### Tavily External News Search

Get your free API key: https://tavily.com

```env
TAVILY_API_KEY=your_tavily_api_key_here
```

**What it does:**
- Searches web for related financial news
- Auto-triggers when financial news is detected
- Aggregates from CNBC, Reuters, Bloomberg, WSJ, etc.

#### Advanced AI Sentiment Analysis

Requires transformers + PyTorch (optional):

```bash
pip install transformers torch
```

**What it does:**
- Uses RoBERTa AI model for sentiment analysis
- More accurate than keyword-based analysis
- Provides confidence scores

---

## Architecture

### Backend (Python FastAPI)

```
backend/
├── main.py                     # Main API server
├── requirements.txt            # Python dependencies
├── .env                        # Configuration (create from .env.example)
├── services/
│   ├── stock_service.py       # Yahoo Finance integration ✅
│   ├── news_service.py        # Financial news ✅
│   ├── sentiment_service.py   # AI sentiment analysis
│   └── tavily_service.py      # External news agent 🔑
```

### Frontend (React + TypeScript)

```
src/
├── components/
│   ├── CandlestickChart.tsx   # Chart with event markers
│   ├── TopBar.tsx             # Futuristic animated logo
│   ├── RightSidebar.tsx       # Live prices
│   └── SymbolIcon.tsx         # Company icons
├── services/
│   ├── api.ts                 # Backend API client
│   └── stockDataService.ts    # Real-time data service
├── hooks/
│   └── useLiveStockData.ts    # Live data hooks
```

---

## API Endpoints

### Stock Data (Free - Yahoo Finance)

```bash
# Single stock
curl http://localhost:8000/api/stock/NVDA

# Multiple stocks
curl -X POST http://localhost:8000/api/stocks \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "NVDA"]}'

# Index data
curl http://localhost:8000/api/index/SPX

# Candlestick data
curl "http://localhost:8000/api/candles/NVDA?period=6mo&interval=1d"
```

### News & Sentiment

```bash
# Financial news with sentiment
curl http://localhost:8000/api/news/NVDA

# External news search (requires Tavily API key)
curl -X POST http://localhost:8000/api/news/search \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NVDA",
    "query": "NVIDIA AI chips",
    "limit": 5
  }'

# Combined news (financial + external)
curl http://localhost:8000/api/news/combined/NVDA
```

---

## Event Markers on Chart

The candlestick chart shows **event markers** directly on candles:

- 📊 **Blue** - Earnings & Revenue
- 💰 **Green** - Dividends
- 🔔 **Purple** - News Events

**Features:**
- Positioned exactly on the candle where event occurred
- Shows price at that time
- Click to see event details
- Hover to see price tooltip

---

## Sentiment Analysis

All news articles include sentiment analysis:

```json
{
  "title": "NVIDIA Announces Record Earnings",
  "content": "...",
  "sentiment": {
    "score": 0.87,        // -1 to 1 scale
    "label": "positive",   // positive/neutral/negative
    "confidence": 0.95,    // 0 to 1
    "summary": "Sentiment: POSITIVE (confidence: 95%)"
  }
}
```

---

## News Agent Workflow

When financial news is detected, the system automatically:

1. **Detects** financial news from Yahoo Finance
2. **Triggers** Tavily agent to search external sources
3. **Analyzes** sentiment on both sources
4. **Aggregates** all news with sentiment scores
5. **Displays** on chart timeline with markers

---

## Development

### Running Both Servers

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

### Testing

```bash
# Test backend health
curl http://localhost:8000/health

# Test stock data
curl http://localhost:8000/api/stock/NVDA

# Frontend will automatically connect to backend
# Check browser console for connection status:
# ✅ Using backend API for NVDA
# ⚠️  Backend unavailable, using mock data
```

---

## Troubleshooting

### Backend Won't Start

**Issue:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Frontend Shows Mock Data

**Issue:** Frontend not connecting to backend

**Solution:**
1. Make sure backend is running: `http://localhost:8000/health`
2. Check CORS settings in `backend/main.py` allow your frontend port
3. Check browser console for connection errors

### Tavily Not Working

**Issue:** External news search returns empty results

**Solution:**
1. Get API key from https://tavily.com
2. Add to `backend/.env`: `TAVILY_API_KEY=your_key_here`
3. Restart backend server

### Chart Events Not Showing

**Issue:** No markers on candlestick chart

**Solution:**
- Markers appear for news events in the data
- Check browser console for positioning errors
- Try zooming out on the chart

---

## Production Deployment

### Backend

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

**Backend (.env):**
```env
TAVILY_API_KEY=your_production_key
PORT=8000
HOST=0.0.0.0
```

**Frontend (.env.production):**
```env
VITE_API_BASE=https://your-backend-domain.com
```

---

## API Keys Needed

| Service | Required | Cost | URL |
|---------|----------|------|-----|
| Yahoo Finance | ✅ No | FREE | Built-in |
| Tavily | Optional | Free tier available | https://tavily.com |
| Transformers | Optional | FREE (open-source) | Auto-downloaded |

---

## Support

- **Backend Issues:** Check `backend/README.md`
- **API Docs:** Visit `http://localhost:8000/docs` when backend is running
- **Frontend:** Check browser console for errors

---

## What's Working Now

✅ Real-time stock data (Yahoo Finance)
✅ Live candlestick charts
✅ Index tracking (SPX, NASDAQ, etc.)
✅ Financial news
✅ Basic sentiment analysis
✅ Event markers on chart
✅ Futuristic animated logo
✅ Modern UI with gradients

## What Needs API Keys

🔑 Tavily external news search
🔑 Advanced AI sentiment (optional - uses free models)

---

**You're ready to go! Start both servers and test with real data. 🚀**
