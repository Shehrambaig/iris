"""
Configuration settings for the RAG system
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"
DOCUMENTS_DIR = BASE_DIR / "documents"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
VECTOR_STORE_DIR.mkdir(exist_ok=True)
DOCUMENTS_DIR.mkdir(exist_ok=True)

# Embedding Settings
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI's latest embedding model
EMBEDDING_DIMENSIONS = 1536

# Chunking Settings
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 100  # tokens
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

# Retrieval Settings
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.7
HYBRID_SEARCH_ALPHA = 0.5  # Balance between semantic and keyword search

# LLM Settings
LLM_MODEL = "gpt-4o-mini"  # Cost-effective and capable
LLM_TEMPERATURE = 0.1
MAX_TOKENS = 1000

# Reranking Settings
RERANK_TOP_K = 3
USE_RERANKING = True

# Query Expansion Settings
USE_QUERY_EXPANSION = True
NUM_EXPANDED_QUERIES = 3
