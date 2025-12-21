# Project Contributions

## Team Members
- **Shehram Baig** - Backend Architecture, News Scraping System, Evaluation Framework (MAJOR CONTRIBUTOR)
- **Mr. Wahab** - RAG Engine Development
- **Umer** - Frontend Development & Live Market Data Integration

---

## A. Contribution Table

| Component | Shehram Baig | Mr. Wahab | Umer |
|-----------|--------------|-----------|------|
| **Data Work** | ✓✓✓ News scraper (Playwright), Data pipeline, Dataset preparation | Document loading, Chunking strategy | - |
| **Implementation** | ✓✓✓ FastAPI backend, Services integration, API endpoints, WebSocket implementation, Langfuse integration | RAG engine (FAISS, embeddings, hybrid search, reranking) | React frontend, Nasdaq live price integration, UI/UX |
| **Experiments** | ✓✓✓ Comprehensive evaluation framework, LLM-as-judge setup, Langfuse observability | RAG tuning (chunk size, retrieval methods) | Frontend optimization |
| **Evaluation & Testing** | ✓✓✓ Designed and executed 198 evaluation runs across 4 metrics, Langfuse dashboard setup | RAG pipeline validation | Frontend testing |
| **Writing** | ✓ Documentation, API documentation | RAG documentation | Frontend README |
| **Technical Leadership** | ✓✓✓ System architecture design, Integration orchestration, Deployment configuration | RAG system design | Frontend architecture |

**Legend**: ✓ = Contributed, ✓✓ = Major contribution, ✓✓✓ = Primary responsibility

---

## B. Individual Reflections

### Shehram Baig

**Biggest Contribution:**
My primary contribution was architecting and implementing the complete backend infrastructure and establishing a rigorous evaluation framework. I built the entire news scraping system using Playwright to collect real-time financial news, designed the FastAPI backend with multiple services (news, sentiment, RAG integration), and most importantly, created a comprehensive evaluation pipeline using Langfuse and LLM-as-judge methodology to validate our RAG system's performance.

**Key Achievements:**
- **Backend Development**: Built the complete FastAPI backend with 20+ endpoints, WebSocket support for real-time updates, and integration of multiple services (news scraping, sentiment analysis, RAG, external APIs)
- **News Scraping System**: Designed and implemented an automated news scraper using Playwright that monitors 10+ companies and broadcasts updates in real-time
- **Evaluation Framework**: Developed and executed a comprehensive evaluation system with 198 total evaluations across 4 key metrics:
- **Context Relevance** : 54 evals (avg score: 0.45)
  - Correctness: 54 evals (avg score: 0.39)
  - Hallucination Detection: 54 evals (avg score: 0.11)
  - Answer Relevance: 36 evals (avg score: 0.28)
- **Observability**: Integrated Langfuse for complete system tracing and LLM observability
- **System Integration**: Orchestrated the integration of RAG (by Wahab), frontend (by Umer), and all backend services into a cohesive system

**What I Learned:**
- **LLM Evaluation at Scale**: Learned how to design and implement evaluation systems using LLM-as-judge methodology with Langfuse. Understanding the importance of systematic evaluation beyond just "does it work" to quantifiable metrics
- **Real-time Data Architecture**: Gained deep experience in building WebSocket-based real-time systems for streaming news and market data
- **Production-Ready API Design**: Learned to design robust FastAPI services with proper error handling, CORS, background tasks, and monitoring
- **Observability Best Practices**: Mastered implementing comprehensive tracing with Langfuse to track RAG queries, LLM calls, and system performance

**What I'd Improve:**
- **Evaluation Coverage**: While we ran 198 evaluations, I'd expand the test dataset to cover more edge cases and company-specific scenarios
- **Automated Testing**: Implement CI/CD pipelines with automated evaluation runs on every deployment
- **Performance Optimization**: Add caching layers (Redis) for frequently accessed news and RAG queries to reduce latency
- **Evaluation Metrics**: Add more nuanced metrics like citation accuracy, source diversity, and answer completeness
- **Error Recovery**: Implement more robust retry mechanisms and fallback strategies for external API failures
- **Monitoring Dashboards**: Create custom Grafana dashboards to monitor system health, API latency, and evaluation scores in real-time

---

## Project Statistics

- **Total Backend Endpoints**: 20+ REST APIs + 2 WebSocket endpoints
- **Total Evaluations Run**: 198 (across 4 metrics)
- **News Sources Monitored**: 10+ companies
- **RAG Documents**: 10+ company profiles
- **Frontend Components**: 15+ React components
- **Lines of Code**: ~15,000+ (Backend: ~8,000, Frontend: ~5,000, RAG: ~2,000)

---

## Technology Stack

### Backend (Shehram)
- FastAPI, Python, WebSockets
- Playwright for web scraping
- Langfuse for observability
- OpenAI API for sentiment & LLM-as-judge
- Tavily API for web search

### RAG System (Wahab)
- FAISS vector store
- OpenAI embeddings (text-embedding-3-small)
- Hybrid search (semantic + BM25)
- GPT-4o-mini for generation
- Langchain for orchestration

### Frontend (Umer)
- React, TypeScript, Vite
- TailwindCSS
- Recharts for visualizations
- WebSocket client
- Nasdaq API integration

---

**Project Repository**: https://github.com/Shehrambaig/iris
