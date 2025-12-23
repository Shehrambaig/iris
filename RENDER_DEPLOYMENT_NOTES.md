# Render.com Deployment Analysis

## ✅ What I Fixed:

### 1. **Added RAG Dependencies**
- Updated buildCommand to install both `/backend/requirements.txt` AND `/rag/requirements.txt`
- This ensures `readability-lxml` and other RAG libraries are installed

### 2. **Externalized Langfuse Secrets**
- Moved hardcoded Langfuse keys from code to environment variables
- Added `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_HOST` to render.yaml
- Updated `/backend/services/rag_service.py` to use env vars

### 3. **Added File Watcher Control**
- Added `ENABLE_FILE_WATCHER` environment variable (set to "false" in production)
- Updated `/backend/main.py` to conditionally start the file watcher
- This prevents errors when trying to watch non-existent scraper output directory

## 🔴 Critical Issues That Remain:

### 1. **Separate Filesystems (BLOCKING ISSUE)**

**Problem:**
- Scraper service writes to: `/scraper/src/change_tracking/new_urls/`
- Backend service tries to read from: The same path (doesn't exist on backend)
- **Result**: Scraped news won't be processed into RAG on Render

**Why This Happens:**
- Render free tier gives each service its own isolated filesystem
- Services cannot share files through local filesystem

**Solutions (Pick One):**

#### Option A: Use S3 or Cloud Storage (Recommended)
```python
# Scraper writes to S3
s3_client.put_object(
    Bucket='iris-scraped-news',
    Key=f'{company}-{timestamp}.json',
    Body=json.dumps(scraped_data)
)

# Backend polls S3 or gets S3 notifications
# Then processes files and adds to RAG
```

**Pros**: Reliable, scalable, persistent
**Cons**: Requires AWS account, ~$0.023/GB/month

#### Option B: Direct API Integration (Recommended for Free Tier)
```python
# Scraper POSTs directly to backend instead of saving files
async with aiohttp.ClientSession() as session:
    await session.post(
        f"{BACKEND_URL}/api/admin/ingest-scraped-news",
        json=scraped_data
    )

# Backend receives and processes immediately
@router.post("/api/admin/ingest-scraped-news")
async def ingest_scraped_news(data: dict):
    for url_data in data['urls']:
        await news_processor.process_url(url_data)
```

**Pros**: No external dependencies, works on free tier
**Cons**: Requires refactoring scraper code

#### Option C: Combine Services (Not Recommended)
- Run scraper and backend in the same service
- Use cron job or background thread for scraping

**Pros**: Shared filesystem
**Cons**: Less isolation, harder to scale, mixing concerns

### 2. **Ephemeral Storage (DATA LOSS ISSUE)**

**Problem:**
- FAISS vector store at `/rag/vector_store/` is stored on disk
- Render free tier uses **ephemeral storage** (wiped on restart/redeploy)
- **Result**: All scraped news in RAG lost on every restart

**Impact:**
- After restart, RAG only has original documents from git
- All scraped news articles are gone
- Must re-scrape and re-index everything

**Solutions:**

#### Option A: PostgreSQL + pgvector (Best for Production)
```yaml
# render.yaml
databases:
  - name: iris-db
    plan: free  # 90 days free trial
    region: oregon
```

Store vectors in PostgreSQL with pgvector extension instead of FAISS.

**Pros**: Persistent, supports filtering, SQL queries
**Cons**: More complex setup, 90-day free trial only

#### Option B: S3 for Vector Store
Save/load FAISS index to/from S3 on startup/shutdown.

**Pros**: Simple, cheap storage
**Cons**: Slower startup, requires S3

#### Option C: Accept Data Loss (Development Only)
Just rebuild RAG index from documents on each restart.

**Pros**: No changes needed
**Cons**: Loses all scraped news, slow startup

### 3. **Environment Variables Not Set**

You need to configure these secrets in Render dashboard:
- `OPENAI_API_KEY` - Your OpenAI API key
- `TAVILY_API_KEY` - Your Tavily API key
- `LANGFUSE_SECRET_KEY` - Langfuse secret key (or disable tracing)
- `LANGFUSE_PUBLIC_KEY` - Langfuse public key (or disable tracing)

**How to set:**
1. Go to Render Dashboard
2. Select your service (iris-backend)
3. Environment → Add Secret File or Environment Variable
4. Paste your keys

## 📋 Deployment Checklist

### Before Deploying:

- [ ] Choose scraper integration approach (Option A or B above)
- [ ] Implement chosen scraper integration
- [ ] Choose vector store persistence approach
- [ ] Set all environment variables in Render dashboard
- [ ] Test locally with `ENABLE_FILE_WATCHER=false` to simulate production
- [ ] Update frontend VITE_API_URL to point to Render backend URL
- [ ] Consider upgrading to paid plan for persistent disks ($7/month)

### After Deploying:

- [ ] Check backend logs for successful startup
- [ ] Verify RAG engine initialized (even if empty)
- [ ] Test health endpoint: `https://iris-backend.onrender.com/health`
- [ ] Test manual scraper trigger: `POST /api/admin/run-scraper`
- [ ] Verify WebSocket connection works (if enabled)
- [ ] Test RAG query with existing documents

## 🎯 Recommended Architecture for Production

```
┌─────────────┐
│   Scraper   │
│   (Worker)  │
└──────┬──────┘
       │ POST /api/admin/ingest-scraped-news
       ▼
┌─────────────────────────────────────┐
│           Backend API               │
│  ┌──────────────────────────────┐  │
│  │    NewsProcessorService      │  │
│  │  (processes URLs to RAG)     │  │
│  └──────────────┬───────────────┘  │
│                 ▼                   │
│  ┌──────────────────────────────┐  │
│  │   PostgreSQL + pgvector      │  │
│  │  (persistent vector store)   │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## 💰 Cost Considerations

### Free Tier (Current):
- **Cost**: $0/month
- **Limitations**:
  - Ephemeral storage (data loss on restart)
  - Separate filesystems (scraper integration broken)
  - 512 MB RAM per service
  - Services spin down after 15min inactivity

### Paid Tier Options:
- **Starter ($7/month per service)**:
  - Persistent disk (no data loss)
  - Always on (no spin down)
  - 512 MB RAM

- **PostgreSQL Free**:
  - 90-day free trial
  - 1 GB storage
  - After trial: $7/month

### Estimated Monthly Cost:
- Backend + Frontend + Scraper + PostgreSQL = ~$28/month
- OR stay free with API integration + accept data loss

## 🚀 Quick Start for Free Tier

**Minimal changes to make it work on free tier:**

1. **Modify scraper to POST data to backend**
2. **Accept that vector store resets on restart**
3. **Set environment variables in Render**
4. **Deploy!**

The scraped news integration will work during uptime, but you'll lose the vector store on restarts. For development/testing, this is acceptable.

## 📝 Next Steps

1. **Decide**: Are you deploying for production or just testing?
   - **Testing**: Accept limitations, use free tier
   - **Production**: Implement S3/PostgreSQL, upgrade to paid plan

2. **Implement** chosen scraper integration approach

3. **Test** locally with production settings:
   ```bash
   export ENABLE_FILE_WATCHER=false
   export LANGFUSE_HOST=https://cloud.langfuse.com
   cd backend && python main.py
   ```

4. **Deploy** and monitor logs carefully

Need help implementing any of these solutions? Let me know which approach you want to take!
