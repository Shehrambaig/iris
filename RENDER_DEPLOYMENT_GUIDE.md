# Render.com Deployment Guide (Paid Tier)

## ✅ Configuration Complete!

Your `render.yaml` is now configured for **Render Starter Plan** with:
- ✅ Persistent shared disk across backend and scraper
- ✅ Langfuse disabled (local development only)
- ✅ Full scraped news integration working
- ✅ Vector store persists across restarts

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────┐
│          Persistent Disk: iris-data            │
│              /data (1 GB)                       │
│                                                  │
│  /data/scraper_output/  ← Scraper writes here  │
│  /data/vector_store/    ← RAG index stored here│
└─────────────────────────────────────────────────┘
         ↑                          ↑
         │                          │
    ┌────────┐                 ┌────────┐
    │Scraper │                 │Backend │
    │Worker  │                 │  API   │
    └────────┘                 └────────┘
         │                          │
         └──────────────┬───────────┘
                        │
                   File Watcher
            (Real-time RAG updates)
```

## 🎯 What's Been Updated

### 1. **render.yaml Changes**
- **All services** set to `plan: starter` (paid tier)
- **Persistent disk** configured: `iris-data` (1 GB, shared across backend & scraper)
- **Environment variables** added:
  - `SCRAPER_OUTPUT_PATH=/data/scraper_output` (both backend & scraper)
  - `VECTOR_STORE_PATH=/data/vector_store` (backend)
  - `ENABLE_FILE_WATCHER=true` (backend can access shared disk)
- **Langfuse removed** (not deployed to production)

### 2. **Backend Code Changes**
- `/backend/services/rag_service.py`:
  - Langfuse now optional (uses env vars, gracefully disabled if not set)
  - Vector store path uses `VECTOR_STORE_PATH` env var

- `/backend/main.py`:
  - File watcher uses `SCRAPER_OUTPUT_PATH` env var
  - Creates directory if missing on startup

### 3. **Scraper Code Changes**
- `/scraper/src/change-detection.py`:
  - Checks `SCRAPER_OUTPUT_PATH` environment variable
  - Writes to shared disk when deployed to Render
  - Falls back to local path for development

## 🚀 Deployment Steps

### 1. Set Environment Variables in Render Dashboard

Before deploying, set these secrets in Render:

**For Backend Service (iris-backend):**
```
OPENAI_API_KEY=sk-proj-...your-key...
TAVILY_API_KEY=tvly-...your-key...
```

**Note:** Langfuse variables are NOT needed (local only)

### 2. Deploy to Render

```bash
# Commit your changes
git add .
git commit -m "Configure for Render paid tier with persistent disk"
git push origin main

# Render will auto-deploy when connected to your repo
```

### 3. Verify Deployment

**Check backend logs:**
```
[OK] RAG Engine initialized in RAGService
[OK] RAG index loaded with X vectors
[INFO] News Watcher: Disabled (ENABLE_FILE_WATCHER=false)
[WARN] Langfuse keys not found in environment, tracing disabled
```

**Check scraper logs:**
```
INFO - Loaded X companies from configuration
INFO - Scraping company: Apple...
INFO - New URLs only: /data/scraper_output/
```

## 📁 File Paths Comparison

### Local Development:
```
/scraper/src/change_tracking/new_urls/  ← Scraper writes here
/rag/vector_store/                       ← RAG index stored here
```

### Render Production:
```
/data/scraper_output/  ← Scraper writes here (shared disk)
/data/vector_store/    ← RAG index stored here (shared disk)
```

## ✨ How It Works

### 1. **Scraper Runs Every 3 Hours**
- Discovers new URLs from company pages
- Writes to `/data/scraper_output/{Company}-{timestamp}.json`
- Sets state: "pending"

### 2. **Backend File Watcher Detects New Files**
- Monitors `/data/scraper_output/` every 5 seconds
- Detects new JSON files

### 3. **NewsProcessorService Processes URLs**
- Fetches article HTML
- Extracts clean text (multi-strategy)
- Adds to RAG with metadata:
  ```json
  {
    "source_type": "scraped_news",
    "company_name": "Apple",
    "original_url": "https://...",
    "article_title": "Executive Transitions",
    "discovery_timestamp": "2025-12-23T14:49:35"
  }
  ```
- Updates state: "processed"

### 4. **RAG Engine Indexes Content**
- Generates embeddings (OpenAI text-embedding-3-small)
- Adds to FAISS vector store at `/data/vector_store/`
- Updates BM25 index for hybrid search

### 5. **Frontend Queries Show Results**
- User asks: "What's new with Apple?"
- RAG returns sources with URLs, companies, timestamps
- Frontend displays with clickable links

## 💰 Cost Breakdown

### Render Starter Plan Costs:
- **Backend**: $7/month (always on, persistent disk)
- **Frontend**: $7/month (always on)
- **Scraper**: $7/month (always on, persistent disk)
- **Total**: **$21/month**

### Additional Costs:
- **OpenAI API**: Pay-as-you-go
  - Embeddings: ~$0.00002/1K tokens
  - GPT-4o-mini: ~$0.00015/1K input tokens
  - Estimated: $5-15/month depending on usage

**Total Estimated: $26-36/month**

## 🔧 Maintenance

### View Logs
```bash
# Via Render Dashboard
# Services → Select Service → Logs

# Or use Render CLI
render logs iris-backend --tail
render logs iris-scraper --tail
```

### Check Disk Usage
```bash
# Render Dashboard
# Services → iris-backend → Disk
# Shows usage of /data disk
```

### Manual Scraper Trigger
```bash
# POST to your deployed backend
curl -X POST https://iris-backend.onrender.com/api/admin/run-scraper
```

## 🐛 Troubleshooting

### Scraper Not Writing to Shared Disk
**Check logs for**:
```
Permission denied: /data/scraper_output
```

**Fix**: Ensure disk is properly mounted in render.yaml

### Backend Not Finding Scraped Files
**Check logs for**:
```
Scraper output directory not found: /data/scraper_output
```

**Fix**: Verify `SCRAPER_OUTPUT_PATH` environment variable is set

### Vector Store Not Persisting
**Check logs for**:
```
Could not load RAG index
```

**Fix**: Verify `VECTOR_STORE_PATH=/data/vector_store` is set

### Langfuse Errors (Expected)
```
[WARN] Langfuse keys not found in environment, tracing disabled
```

**This is normal** - Langfuse is local-only and not deployed

## 📝 Testing Locally with Production Settings

Simulate Render environment locally:

```bash
# Set environment variables
export SCRAPER_OUTPUT_PATH=/tmp/iris_data/scraper_output
export VECTOR_STORE_PATH=/tmp/iris_data/vector_store
export ENABLE_FILE_WATCHER=true

# Start backend
cd backend
python main.py

# In another terminal, start scraper
cd scraper
python src/run_scraper.py

# Check that files are written to /tmp/iris_data/scraper_output/
ls -la /tmp/iris_data/scraper_output/

# Check that RAG index is at /tmp/iris_data/vector_store/
ls -la /tmp/iris_data/vector_store/
```

## ✅ Production Checklist

Before going live:

- [ ] Environment variables set in Render Dashboard (OPENAI_API_KEY, TAVILY_API_KEY)
- [ ] Persistent disk configured (iris-data, 1 GB)
- [ ] All services set to `plan: starter`
- [ ] Git repository connected to Render
- [ ] Test scraper manually after deployment
- [ ] Verify RAG query returns results
- [ ] Check file watcher is detecting new files
- [ ] Confirm vector store persists after restart

## 🎉 You're All Set!

Your Agentic IRIS application is now ready for production deployment with:
- ✅ Real-time scraped news integration
- ✅ Persistent vector store
- ✅ Shared filesystem for scraper/backend communication
- ✅ Langfuse tracing (local development only)
- ✅ Rich source attribution with URLs

Deploy and enjoy! 🚀
