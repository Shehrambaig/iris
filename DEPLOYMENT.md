# Deployment Guide - Agentic IRIS

This guide covers deploying the complete Agentic IRIS platform with all components.

## Deployment Options

### Option 1: Local Development (Recommended for Testing)

#### Step 1: Clone and Setup

```bash
cd /Users/shehrambaig/PycharmProjects/Agentic_IRIS
```

#### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
EOF

# Start backend
python main.py
```

Backend runs at `http://localhost:8000`

#### Step 3: RAG Setup

```bash
cd ../rag

# Use same venv or create new one
source ../backend/venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
EOF

# Add documents to documents/ folder
# Build index
python load_all_docs.py
```

#### Step 4: Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at `http://localhost:5173`

#### Step 5: Scraper Setup (Optional)

```bash
cd ../scraper

# Use same venv
source ../backend/venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install playwright
playwright install chromium

# Run scraper
python src/run_scraper.py
```

---

### Option 2: Docker Deployment (Coming Soon)

#### Prerequisites
- Docker Desktop installed
- Docker Compose installed

#### Steps

```bash
# Create .env file in project root
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
EOF

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

---

### Option 3: Production Deployment

#### Backend (FastAPI)

**Option A: Railway / Render / Fly.io**

1. Create account on chosen platform
2. Connect GitHub repository
3. Configure build:
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables:
   - `OPENAI_API_KEY`
   - `TAVILY_API_KEY`

**Option B: AWS EC2**

```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Python
sudo apt update
sudo apt install python3-pip python3-venv -y

# Clone repository
git clone your-repo-url
cd Agentic_IRIS/backend

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/iris-backend.service
```

Add to service file:
```ini
[Unit]
Description=IRIS Backend API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Agentic_IRIS/backend
Environment="PATH=/home/ubuntu/Agentic_IRIS/backend/venv/bin"
Environment="OPENAI_API_KEY=your_key"
Environment="TAVILY_API_KEY=your_key"
ExecStart=/home/ubuntu/Agentic_IRIS/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl enable iris-backend
sudo systemctl start iris-backend

# Setup nginx reverse proxy (optional)
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/iris
```

#### Frontend (React + Vite)

**Option A: Vercel (Recommended)**

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Set environment variable
# In Vercel dashboard: VITE_API_URL=https://your-backend-url
```

**Option B: Netlify**

```bash
cd frontend

# Build
npm run build

# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod --dir=dist
```

**Option C: Static hosting (S3, GitHub Pages, etc.)**

```bash
cd frontend

# Build for production
npm run build

# Upload dist/ folder to your hosting service
```

#### RAG System

The RAG system is typically integrated with the backend. Ensure:

1. Documents are in `rag/documents/`
2. Run `python load_all_docs.py` to build index
3. `rag/vector_store/` contains the built index
4. Deploy these folders with the backend

#### Scraper

**Option A: Cron job on same server**

```bash
# Edit crontab
crontab -e

# Add line to run every 3 hours
0 */3 * * * cd /path/to/Agentic_IRIS/scraper && /path/to/venv/bin/python src/run_scraper.py >> /path/to/logs/scraper.log 2>&1
```

**Option B: Separate service**

Deploy as separate container or service that runs periodically.

---

## Environment Variables

### Backend
```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

### Frontend
```env
VITE_API_URL=http://localhost:8000
# Or in production:
VITE_API_URL=https://api.yourdomain.com
```

### RAG
```env
OPENAI_API_KEY=sk-...
```

---

## Post-Deployment Checklist

- [ ] Backend health check responds at `/health`
- [ ] Frontend loads and connects to backend
- [ ] News API returns data at `/api/news/all`
- [ ] RAG chat works at `/api/rag/query`
- [ ] WebSocket connects at `/ws/news`
- [ ] Scraper runs and creates files in `scraper/src/change_tracking/new_urls/`
- [ ] CORS is configured for your frontend domain
- [ ] API keys are set correctly
- [ ] SSL/HTTPS configured (production only)

---

## Monitoring & Maintenance

### Health Checks
```bash
# Backend
curl http://localhost:8000/health

# Check scraper status
curl http://localhost:8000/api/admin/scraper-status
```

### Logs
```bash
# Backend logs (if using systemd)
sudo journalctl -u iris-backend -f

# Scraper logs
tail -f /path/to/Agentic_IRIS/scraper/logs/scraper_*.log

# Frontend logs (in browser console)
```

### Updating

```bash
# Pull latest changes
git pull

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart iris-backend

# Frontend
cd frontend
npm install
npm run build
# Re-deploy to hosting service

# RAG (if documents changed)
cd rag
python load_all_docs.py
```

---

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (needs 3.9+)
- Check dependencies: `pip install -r requirements.txt`
- Check API keys in `.env`
- Check port 8000 is available: `lsof -i :8000`

### Frontend can't connect to backend
- Check `VITE_API_URL` environment variable
- Check CORS settings in `backend/main.py`
- Verify backend is running and accessible

### RAG returns errors
- Check `OPENAI_API_KEY` is valid
- Verify index exists: `ls rag/vector_store/`
- Rebuild index: `python rag/load_all_docs.py`

### Scraper not running
- Check Playwright is installed: `playwright install chromium`
- Check cron job is configured
- Run manually to test: `python scraper/src/run_scraper.py`

---

## Security Notes

- Never commit `.env` files to git
- Use environment variables for all secrets
- Enable HTTPS in production
- Set up firewall rules
- Regularly update dependencies
- Monitor API usage to avoid excessive costs
- Rate limit API endpoints in production

---

For more help, check the individual component documentation in `docs/`.