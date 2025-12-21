# Agentic IRIS - System Architecture Diagram

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer - React + TypeScript (Umer)"
        UI[User Interface]
        HomePage[Home Page<br/>News Feed + Market Overview]
        GraphPage[Graph Page<br/>Interactive Charts]
        ChatPage[Chat Page<br/>RAG Q&A Interface]
        UI --> HomePage
        UI --> GraphPage
        UI --> ChatPage
    end

    subgraph "Backend Layer - FastAPI (Shehram)"
        API[FastAPI Server<br/>Port 8000]

        subgraph "Services"
            NewsService[News Service<br/>Aggregation & Filtering]
            RAGService[RAG Service<br/>Query Interface]
            SentimentService[Sentiment Service<br/>OpenAI Analysis]
            TavilyService[Tavily Service<br/>Web Search]
            StockService[Stock Service<br/>Market Data]
        end

        API --> NewsService
        API --> RAGService
        API --> SentimentService
        API --> TavilyService
        API --> StockService
    end

    subgraph "Data Collection Layer (Shehram)"
        Scraper[News Scraper<br/>Playwright]
        ScraperDB[(Change Tracking<br/>JSON Files)]
        Scraper --> ScraperDB
    end

    subgraph "RAG Engine Layer (Wahab)"
        RAGEngine[RAG Engine Core]

        subgraph "RAG Components"
            DocLoader[Document Loader<br/>DOCX, PDF, TXT]
            Chunker[Semantic Chunker<br/>512 tokens + overlap]
            Embedder[Embedding Generator<br/>OpenAI text-embedding-3-small]
            VectorStore[Vector Store<br/>FAISS Index]
            QueryProc[Query Processor<br/>Expansion + Reranking]
        end

        DocLoader --> Chunker
        Chunker --> Embedder
        Embedder --> VectorStore
        RAGEngine --> QueryProc
        QueryProc --> VectorStore
    end

    subgraph "External APIs"
        OpenAI[OpenAI API<br/>GPT-4o-mini<br/>Embeddings]
        Nasdaq[Nasdaq API<br/>Live Stock Prices]
        Tavily[Tavily API<br/>Web Search]
        Langfuse[Langfuse<br/>Observability Platform]
    end

    subgraph "Data Storage"
        Documents[(Company Documents<br/>10 DOCX files)]
        VectorDB[(FAISS Vector Store<br/>150+ chunks)]
        NewsDB[(News JSON Files<br/>50+ articles/day)]
    end

    %% Frontend to Backend
    HomePage -->|REST API| API
    GraphPage -->|REST API| API
    ChatPage -->|REST API + WebSocket| API

    %% Backend to Services
    NewsService --> ScraperDB
    RAGService --> RAGEngine

    %% Services to External APIs
    SentimentService --> OpenAI
    TavilyService --> Tavily
    StockService --> Nasdaq
    RAGService --> Langfuse

    %% RAG Engine to External
    RAGEngine --> OpenAI
    RAGEngine --> Langfuse

    %% Data Flows
    Documents --> DocLoader
    VectorStore --> VectorDB
    Scraper -.->|Every 3 hours| NewsDB
    NewsService --> NewsDB

    %% WebSocket Real-time Updates
    Scraper -.->|WebSocket Broadcast| API
    API -.->|WebSocket| ChatPage
    API -.->|WebSocket| HomePage

    %% Dark Grey Styling for All Nodes
    classDef darkBox fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff
    class UI,HomePage,GraphPage,ChatPage,API,NewsService,RAGService,SentimentService,TavilyService,StockService,Scraper,ScraperDB,RAGEngine,DocLoader,Chunker,Embedder,VectorStore,QueryProc,OpenAI,Nasdaq,Tavily,Langfuse,Documents,VectorDB,NewsDB darkBox
```

## Detailed RAG Pipeline

```mermaid
flowchart LR
    A[User Question] --> B[Query Processing]
    B --> C{Query Expansion}
    C --> D[Generate 3 Variations]
    D --> E[Hybrid Search]

    subgraph "Hybrid Retrieval"
        E --> F[Vector Search<br/>FAISS]
        E --> G[Keyword Search<br/>BM25]
        F --> H[Combine Results<br/>α=0.5]
        G --> H
    end

    H --> I[Top-10 Chunks]
    I --> J[Reranking<br/>Cross-Encoder]
    J --> K[Top-5 Chunks]
    K --> L{Web Search?}
    L -->|Yes| M[Tavily/OpenAI<br/>Latest Info]
    L -->|No| N[Context Assembly]
    M --> N

    N --> O[LLM Generation<br/>GPT-4o-mini]
    O --> P[Streaming Response]
    P --> Q[Answer with Citations]

    subgraph "Observability"
        B -.-> R[Langfuse Trace]
        E -.-> R
        J -.-> R
        O -.-> R
    end

    Q --> S[Return to User]

    %% Dark Grey Styling
    classDef darkBox fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff
    class A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S darkBox
```

## Data Flow Architecture

```mermaid
flowchart TB
    subgraph "Data Ingestion"
        A1[Company Websites] -->|Playwright| A2[News Scraper]
        A3[Company Docs] -->|Manual Upload| A4[Document Loader]
        A2 --> A5[(News JSON)]
        A4 --> A6[(Vector Store)]
    end

    subgraph "Real-time Pipeline"
        B1[Nasdaq API] -->|Every 30s| B2[Stock Service]
        A5 -->|WebSocket| B3[News Service]
        B2 --> B4[Frontend Display]
        B3 --> B4
    end

    subgraph "RAG Query Pipeline"
        C1[User Query] --> C2[RAG Service]
        C2 --> C3[RAG Engine]
        A6 -->|Retrieve| C3
        C3 --> C4[OpenAI LLM]
        C4 --> C5[Streaming Answer]
    end

    subgraph "Observability Layer"
        D1[Langfuse SDK] -.->|Trace| C2
        D1 -.->|Trace| C3
        D1 -.->|Trace| C4
        D1 --> D2[(Langfuse DB)]
    end

    %% Dark Grey Styling
    classDef darkBox fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff
    class A1,A2,A3,A4,A5,A6,B1,B2,B3,B4,C1,C2,C3,C4,C5,D1,D2 darkBox
```

## Evaluation Framework

```mermaid
flowchart LR
    A[Test Questions<br/>54 unique] --> B[RAG System]
    B --> C[Generated Answers]

    C --> D[LLM Judge<br/>GPT-4o-mini]

    subgraph "Evaluation Metrics"
        D --> E1[Context Relevance<br/>54 evals]
        D --> E2[Correctness<br/>54 evals]
        D --> E3[Hallucination<br/>54 evals]
        D --> E4[Answer Relevance<br/>36 evals]
    end

    E1 --> F[Langfuse Dashboard]
    E2 --> F
    E3 --> F
    E4 --> F

    F --> G[Results Analysis<br/>198 total scores]

    G --> H{Performance<br/>Good?}
    H -->|No| I[Adjust RAG Config]
    H -->|Yes| J[Deploy to Production]

    I --> B

    %% Dark Grey Styling
    classDef darkBox fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff
    class A,B,C,D,E1,E2,E3,E4,F,G,H,I,J darkBox
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        A1[Local Machine]
        A2[VS Code]
        A3[Git Repository]
    end

    subgraph "Backend Services"
        B1[FastAPI Server<br/>localhost:8000]
        B2[Uvicorn<br/>ASGI Server]
        B1 --> B2
    end

    subgraph "Frontend Services"
        C1[React App<br/>localhost:5173]
        C2[Vite Dev Server]
        C1 --> C2
    end

    subgraph "Background Jobs"
        D1[News Scraper<br/>Every 3 hours]
        D2[Playwright Browser]
        D1 --> D2
    end

    subgraph "External Services"
        E1[OpenAI API]
        E2[Nasdaq API]
        E3[Langfuse<br/>localhost:3000]
    end

    A1 --> B1
    A1 --> C1
    A1 --> D1

    B1 --> E1
    B1 --> E2
    B1 --> E3

    C2 -->|HTTP| B2

    %% Dark Grey Styling
    classDef darkBox fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff
    class A1,A2,A3,B1,B2,C1,C2,D1,D2,E1,E2,E3 darkBox
```

## Technology Stack Overview

```mermaid
mindmap
    root((Agentic IRIS))
        Frontend
            React 18
            TypeScript
            TailwindCSS
            Vite
            Recharts
            WebSocket Client
        Backend
            FastAPI
            Python 3.12
            Uvicorn
            WebSockets
            CORS Middleware
            Background Tasks
        RAG System
            FAISS
            OpenAI Embeddings
            GPT-4o-mini
            Langchain
            Sentence Transformers
        Data Collection
            Playwright
            Selenium
            BeautifulSoup
            Pandas
        Observability
            Langfuse
            Custom Logging
            Trace Management
        External APIs
            OpenAI API
            Nasdaq API
            Tavily API
            Yahoo Finance
```

---

## How to Use This Diagram

### In GitHub (Auto-renders)
Just view this file on GitHub - Mermaid diagrams render automatically!

### In VS Code
1. Install "Markdown Preview Mermaid Support" extension
2. Open this file and click "Preview" (Ctrl/Cmd + Shift + V)

### Export as Image
1. Use https://mermaid.live/
2. Copy the Mermaid code
3. Paste and export as PNG/SVG

### In Documentation
1. Copy the Mermaid code blocks
2. Paste into any Markdown file
3. Most modern viewers support Mermaid

---

## Legend

- **Blue boxes**: Frontend components
- **Yellow boxes**: Backend services
- **Green boxes**: RAG/AI components
- **Pink boxes**: Data collection
- **Purple boxes**: External APIs
- **Solid arrows**: Direct API calls
- **Dotted arrows**: Async/WebSocket/Background processes

---

**Created by:** Shehram Baig
**Date:** December 2024
**Project:** Agentic IRIS - Financial Intelligence Platform
