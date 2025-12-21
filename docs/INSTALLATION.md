# MarketPulse - Installation Guide

## Quick Start

### Prerequisites
- **Python 3.10+** (tested on Python 3.14)
- **Node.js 18+** and npm
- **OpenAI API Key** (required for RAG & Sentiment Analysis)
- **Tavily API Key** (optional, for external news search)

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd Agentic-Front
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
# Install all dependencies (Backend + RAG + Scraper)
pip install -r requirements.txt
```

#### Configure Environment Variables
Create `backend/.env` file:
```env
# Required
OPENAI_API_KEY=sk-proj-your-key-here

# Optional
TAVILY_API_KEY=tvly-your-key-here
```

#### Start the Backend
```bash
# Windows
start-backend.bat

# Linux/Mac
python backend/main.py
```

The backend will start on **http://localhost:8000**

### 3. Frontend Setup

#### Install Dependencies
```bash
npm install
```

#### Start the Frontend
```bash
npm run dev
```

The frontend will start on **http://localhost:5173**

---

## What Gets Loaded Automatically?

When you start the backend, it automatically:
- ✅ **NASDAQ API** - Live stock prices (no key needed)
- ✅ **RAG System** - Loads 30 document chunks from `iris-apple-dev/documents/`
- ✅ **Sentiment Analysis** - OpenAI GPT-4o-mini based
- ✅ **News Scraper** - Auto-refresh every 3 hours
- ✅ **News Watcher** - Real-time WebSocket updates

---

## Features

### 📊 Real-Time Stock Data
- Live NASDAQ prices for 10 major tech stocks
- Price-based sentiment analysis
- Interactive TradingView-style charts

### 🤖 AI-Powered RAG Chat
- Ask questions about companies (Amazon, Google, Microsoft, NVIDIA, Tesla, Meta, etc.)
- Answers backed by actual company documents
- Source citations included

### 📰 Financial News
- Auto-scraping from multiple sources
- Real-time updates via WebSocket
- News sentiment analysis

### 📈 Price Sentiment
- Automatic sentiment calculation based on live price changes
- Visual indicators on homepage and charts
- Updates every 5 seconds

---

## Folder Structure

```
Agentic-Front/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main API server
│   ├── services/           # Backend services
│   └── .env                # API keys (create this!)
├── iris-apple-dev/         # RAG system
│   ├── rag_engine.py       # RAG implementation
│   ├── documents/          # Company documents (auto-loaded)
│   └── vector_store/       # FAISS vector store
├── iris-main/              # News scraper
│   └── src/                # Scraper source code
├── src/                    # React frontend
├── requirements.txt        # Python dependencies (ALL-IN-ONE)
└── package.json            # Node.js dependencies
```

---

## Troubleshooting

### Port 8000 Already in Use
```bash
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /F /PID <process-id>

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### RAG Not Loading
- Ensure `iris-apple-dev/vector_store/` contains FAISS index files
- Check `OPENAI_API_KEY` is set in `backend/.env`
- Restart backend after adding the API key

### Frontend Can't Connect to Backend
- Verify backend is running on `http://localhost:8000`
- Check browser console for errors
- Ensure `src/services/*.ts` files use port `8000` (not `8001`)

---

## API Keys

### OpenAI (Required)
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add to `backend/.env` as `OPENAI_API_KEY=sk-...`

### Tavily (Optional)
1. Go to https://tavily.com
2. Sign up for free tier
3. Add to `backend/.env` as `TAVILY_API_KEY=tvly-...`

---

## Development

### Run Tests
```bash
# Backend
cd backend
pytest

# Frontend
npm test
```

### Build for Production
```bash
# Frontend
npm run build
```

---

## License
[Your License Here]

## Support
For issues, please create a GitHub issue or contact [your-email@example.com]
