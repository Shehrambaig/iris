# Company RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system for querying company information, board members, and business details.

## 🌟 Features

### Advanced RAG Techniques Implemented:

1. **Smart Document Loading**
   - Supports DOCX, PDF, TXT, and MD files
   - Automatic company information extraction
   - Metadata preservation

2. **Semantic Chunking**
   - Multiple chunking strategies (semantic, sentence, recursive)
   - Context-aware chunking that preserves meaning
   - Token-based overlap for continuity

3. **Hybrid Search**
   - Combines semantic embeddings (OpenAI text-embedding-3-small)
   - BM25 keyword matching for precise term matching
   - Reciprocal Rank Fusion for multi-query results

4. **Query Processing**
   - Query expansion (generates alternative phrasings)
   - HyDE (Hypothetical Document Embeddings)
   - Query decomposition for complex questions

5. **Reranking**
   - LLM-based relevance scoring
   - Batch reranking for efficiency
   - Configurable top-k results

6. **Contextual Compression**
   - Extracts only relevant parts of retrieved chunks
   - Reduces noise in the context
   - Improves answer quality

7. **Conversational Memory**
   - Maintains context across questions
   - Supports follow-up questions
   - Clear history option

## 📦 Installation

```bash
# Navigate to the project directory
cd "/Users/apple/Desktop/Agentic AI project"

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Run the Demo

```bash
python main.py
```

This will:
- Load your `amazon.docx` file
- Build the vector index
- Run example queries
- Save the index for future use

### 2. Command-Line Interface

```bash
python cli.py
```

Available commands:
- `add <file>` - Add a document
- `add-text` - Add text interactively
- `build` - Build the vector index
- `query <question>` - Ask a question
- `chat` - Start chat mode
- `stats` - Show statistics
- `save` / `load` - Persist state

### 3. Web Interface (Gradio)

```bash
python app.py
```

Opens a beautiful web interface at `http://localhost:7860`

## 📁 Project Structure

```
Agentic AI project/
├── config.py           # Configuration settings
├── document_loader.py  # Document loading and parsing
├── chunker.py          # Text chunking strategies
├── embeddings.py       # Embedding generation (OpenAI + BM25)
├── vector_store.py     # FAISS vector storage
├── query_processor.py  # Query expansion, reranking, compression
├── rag_engine.py       # Main RAG orchestration
├── main.py             # Demo script
├── cli.py              # Command-line interface
├── app.py              # Gradio web interface
├── requirements.txt    # Python dependencies
├── .env                # API keys (do not commit!)
└── README.md           # This file
```

## 💡 Usage Examples

### Python API

```python
from rag_engine import RAGEngine

# Initialize
engine = RAGEngine()

# Add documents
engine.add_document("company_data.docx")
engine.add_text("Google is a technology company...", "Google")

# Build index
engine.build_index()

# Query
result = engine.query("Who are the board members?")
print(result['answer'])

# Chat mode
answer = engine.chat("What does the company do?")
answer = engine.chat("And what about their products?")  # Maintains context

# Save for later
engine.save()
```

### Adding Multiple Companies

```python
# Add all documents from a directory
engine.add_directory("/path/to/company/documents/")
engine.build_index()

# Query across all companies
result = engine.query("Compare the board structures of Amazon and Google")
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Chunking
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 100

# Retrieval
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.7
HYBRID_SEARCH_ALPHA = 0.5  # Balance semantic vs keyword

# LLM
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.1

# Features
USE_QUERY_EXPANSION = True
USE_RERANKING = True
```

## 🔧 Advanced Configuration

### Custom Embedding Model

```python
from embeddings import EmbeddingGenerator

embedder = EmbeddingGenerator(
    model="text-embedding-3-large",  # Higher quality
    batch_size=50
)
```

### Custom Chunking Strategy

```python
from chunker import TextChunker

chunker = TextChunker(
    chunk_size=300,
    chunk_overlap=50
)

# Use different strategies
chunks = chunker.chunk_document(doc, strategy="sentence")
chunks = chunker.chunk_document(doc, strategy="recursive")
```

## 📊 Performance Tips

1. **For large document collections**: Use IVF or HNSW index
   ```python
   vector_store = VectorStore(index_type="ivf")
   ```

2. **For faster reranking**: Use batch reranking
   ```python
   results = reranker.batch_rerank(query, results)
   ```

3. **For better retrieval**: Enable hybrid search
   ```python
   result = engine.query(question, use_hybrid=True)
   ```

## 🔒 Security Note

Your API key is stored in `.env`. Never commit this file to version control!

Add to `.gitignore`:
```
.env
vector_store/
__pycache__/
```

## 📝 License

MIT License

## 🤝 Contributing

Feel free to extend this system with:
- Additional document formats
- Custom embedding models
- New retrieval strategies
- UI improvements
