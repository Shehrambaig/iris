"""
Embedding Generator Module
Handles creating embeddings using OpenAI's API.
"""
from typing import List, Optional
import numpy as np
from openai import OpenAI
from tqdm import tqdm

from config import OPENAI_API_KEY, EMBEDDING_MODEL
from chunker import Chunk


class EmbeddingGenerator:
    """
    Generate embeddings using OpenAI's embedding models.
    Supports batch processing and caching.
    """
    
    def __init__(
        self,
        api_key: str = OPENAI_API_KEY,
        model: str = EMBEDDING_MODEL,
        batch_size: int = 100
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.batch_size = batch_size
        self._cache = {}  # Simple in-memory cache
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        # Check cache
        cache_key = hash(text)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        embedding = response.data[0].embedding
        
        # Cache the result
        self._cache[cache_key] = embedding
        
        return embedding
    
    def embed_texts(self, texts: List[str], show_progress: bool = True) -> List[List[float]]:
        """Generate embeddings for multiple texts with batching."""
        all_embeddings = []
        
        # Process in batches
        iterator = range(0, len(texts), self.batch_size)
        if show_progress:
            iterator = tqdm(iterator, desc="Generating embeddings")
        
        for i in iterator:
            batch = texts[i:i + self.batch_size]
            
            # Filter out already cached texts
            uncached_texts = []
            uncached_indices = []
            
            for j, text in enumerate(batch):
                cache_key = hash(text)
                if cache_key not in self._cache:
                    uncached_texts.append(text)
                    uncached_indices.append(j)
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=uncached_texts
                )
                
                # Cache the new embeddings
                for idx, embedding_data in enumerate(response.data):
                    text = uncached_texts[idx]
                    cache_key = hash(text)
                    self._cache[cache_key] = embedding_data.embedding
            
            # Collect embeddings in order
            batch_embeddings = []
            for text in batch:
                cache_key = hash(text)
                batch_embeddings.append(self._cache[cache_key])
            
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def embed_chunks(self, chunks: List[Chunk], show_progress: bool = True) -> np.ndarray:
        """Generate embeddings for a list of chunks."""
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embed_texts(texts, show_progress)
        return np.array(embeddings)
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a query."""
        embedding = self.embed_text(query)
        return np.array(embedding)
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._cache = {}
    
    @property
    def cache_size(self) -> int:
        """Get the number of cached embeddings."""
        return len(self._cache)


class HybridEmbeddingGenerator(EmbeddingGenerator):
    """
    Extended embedding generator that also creates sparse embeddings
    for hybrid search (combining semantic and keyword search).
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialize_bm25 = False
        self.bm25 = None
        self.corpus = None
    
    def create_sparse_embeddings(self, texts: List[str]):
        """
        Create BM25 sparse embeddings for keyword-based search.
        """
        from rank_bm25 import BM25Okapi
        import re
        
        # Tokenize texts
        tokenized_corpus = [self._tokenize(text) for text in texts]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.corpus = texts
        self._initialize_bm25 = True
    
    def get_bm25_scores(self, query: str) -> np.ndarray:
        """Get BM25 scores for a query."""
        if not self._initialize_bm25:
            raise ValueError("BM25 index not initialized. Call create_sparse_embeddings first.")
        
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        return np.array(scores)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        import re
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b\w+\b', text.lower())
        # Remove stopwords (basic list)
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                     'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                     'as', 'into', 'through', 'during', 'before', 'after',
                     'above', 'below', 'between', 'under', 'and', 'but', 'or',
                     'not', 'no', 'nor', 'so', 'than', 'too', 'very', 'just',
                     'that', 'this', 'these', 'those', 'it', 'its'}
        return [t for t in tokens if t not in stopwords and len(t) > 2]


if __name__ == "__main__":
    from document_loader import DocumentLoader
    from chunker import TextChunker
    
    # Test embedding generation
    loader = DocumentLoader()
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    
    sample_text = "Amazon is a multinational technology company focusing on e-commerce and cloud computing."
    doc = loader.load_from_text(sample_text, "test")
    chunks = chunker.chunk_document(doc, strategy="semantic")
    
    # Generate embeddings
    embedder = HybridEmbeddingGenerator()
    
    print("Generating embeddings...")
    embeddings = embedder.embed_chunks(chunks)
    print(f"Generated {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
    
    # Test BM25
    texts = [chunk.content for chunk in chunks]
    embedder.create_sparse_embeddings(texts)
    
    query = "What is Amazon?"
    bm25_scores = embedder.get_bm25_scores(query)
    print(f"BM25 scores: {bm25_scores}")
