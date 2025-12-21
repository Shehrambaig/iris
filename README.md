# Agentic IRIS - Financial Intelligence Platform

Real-time market intelligence platform combining automated news scraping, sentiment analysis, AI chat, and stock monitoring.

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Scraper   │───▶│   Backend    │◀───│  Frontend   │
│ (Playwright)│    │   (FastAPI)  │    │   (React)   │
└─────────────┘    └──────┬───────┘    └─────────────┘
                          │
                    ┌─────▼──────┐
                    │    RAG     │
                    │ (OpenAI +  │
                    │  Vectors)  │
                    └────────────┘
```

**Scraper** → Monitors IR pages → Detects new URLs → Stores in JSON
**Backend** → Serves news API → Runs sentiment analysis → Integrates RAG
**Frontend** → Displays dashboard → Shows live stock prices → AI chat interface
**RAG** → Vector search → Document QA → GPT-4o-mini responses

## Quick Start

### 1. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo 'OPENAI_API_KEY=sk-xxx\nTAVILY_API_KEY=tvly-xxx' > .env
python main.py  # Runs on :8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev  # Runs on :5173
```

### 3. RAG (Optional)
```bash
cd rag
pip install -r requirements.txt
echo 'OPENAI_API_KEY=sk-xxx' > .env
# Add PDFs to documents/ folder
python load_all_docs.py
```

### 4. Scraper (Optional)
```bash
cd scraper
pip install -r requirements.txt
playwright install chromium
python src/run_scraper.py
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/nasdaq/watchlist` | Live stock prices |
| `GET /api/news/all` | All company news |
| `GET /api/news/{symbol}` | Company-specific news |
| `GET /api/sentiment/stocks` | Price-based sentiment |
| `POST /api/rag/query` | AI chat query |
| `WS /ws/news` | Real-time news stream |

## Environment Variables

```env
# Backend & RAG
OPENAI_API_KEY=sk-xxx

# Backend (optional)
TAVILY_API_KEY=tvly-xxx
```

## Deployment (Render)

```bash
# Push to GitHub
git init && git add . && git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/agentic-iris.git
git push -u origin main

# Use render.yaml for one-click deploy
```

See `render.yaml` for configuration.

## How It Works

1. **Scraper** runs every 3 hours, scraping IR pages of major companies (NVDA, AAPL, MSFT, etc.)
2. New URLs are saved to `scraper/src/change_tracking/new_urls/`
3. **Backend** reads these files and exposes them via `/api/news/*` endpoints
4. **Sentiment analysis** uses OpenAI GPT-4o-mini (or keyword fallback)
5. **RAG system** allows users to ask questions about uploaded documents
6. **Frontend** displays everything in a real-time dashboard with WebSocket updates

## Tech Stack

- **Backend**: FastAPI, Python 3.12
- **Frontend**: React, Vite, TailwindCSS, Redux
- **RAG**: LangChain, OpenAI Embeddings, FAISS
- **Scraper**: Playwright, BeautifulSoup
- **APIs**: OpenAI, Tavily, NASDAQ

## Project Structure

```
├── scraper/       # IR page scraper
├── backend/       # FastAPI server
├── frontend/      # React app
├── rag/           # RAG system
└── render.yaml    # Deployment config
```

## Development

```bash
# Terminal 1 - Backend
cd backend && python main.py

# Terminal 2 - Frontend
cd frontend && npm run dev

# Terminal 3 - Scraper (optional)
cd scraper && python src/run_scraper.py
```

Access at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## License

Proprietary
