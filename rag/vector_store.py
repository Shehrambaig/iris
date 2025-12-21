"""
Vector Store Module
Implements FAISS-based vector storage with advanced retrieval features.
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pickle
from pathlib import Path
import json

from config import VECTOR_STORE_DIR, TOP_K_RESULTS, SIMILARITY_THRESHOLD, HYBRID_SEARCH_ALPHA
from chunker import Chunk
from embeddings import EmbeddingGenerator, HybridEmbeddingGenerator


class VectorStore:
    """
    FAISS-based vector store for efficient similarity search.
    
    Features:
    - Fast approximate nearest neighbor search
    - Persistence (save/load)
    - Metadata storage
    - Filtering support
    """
    
    def __init__(self, dimension: int = 1536, index_type: str = "flat"):
        """
        Initialize the vector store.
        
        Args:
            dimension: Embedding dimension (1536 for text-embedding-3-small)
            index_type: Type of FAISS index ('flat', 'ivf', 'hnsw')
        """
        import faiss
        
        self.dimension = dimension
        self.index_type = index_type
        
        # Create FAISS index
        if index_type == "flat":
            # Exact search - best for small datasets
            self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine with normalized vectors)
        elif index_type == "ivf":
            # Approximate search with inverted file index
            quantizer = faiss.IndexFlatIP(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)
        elif index_type == "hnsw":
            # HNSW for very fast approximate search
            self.index = faiss.IndexHNSWFlat(dimension, 32)
        else:
            raise ValueError(f"Unknown index type: {index_type}")
        
        # Store chunks and metadata
        self.chunks: List[Chunk] = []
        self.metadata: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
    
    def add_chunks(
        self,
        chunks: List[Chunk],
        embeddings: np.ndarray
    ):
        """Add chunks and their embeddings to the store."""
        # Normalize embeddings for cosine similarity
        faiss = self._import_faiss()
        normalized_embeddings = self._normalize_embeddings(embeddings)
        
        # Train index if needed (for IVF)
        if self.index_type == "ivf" and not self.index.is_trained:
            self.index.train(normalized_embeddings)
        
        # Add to index
        self.index.add(normalized_embeddings)
        
        # Store chunks and metadata
        self.chunks.extend(chunks)
        self.metadata.extend([chunk.metadata for chunk in chunks])
        
        # Store embeddings for hybrid search
        if self.embeddings is None:
            self.embeddings = normalized_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, normalized_embeddings])
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = TOP_K_RESULTS,
        threshold: float = SIMILARITY_THRESHOLD,
        filter_func: Optional[callable] = None
    ) -> List[Tuple[Chunk, float]]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            threshold: Minimum similarity score
            filter_func: Optional function to filter results
        
        Returns:
            List of (chunk, score) tuples
        """
        # Normalize query
        query_normalized = self._normalize_embeddings(query_embedding.reshape(1, -1))
        
        # Search with extra results for filtering
        search_k = top_k * 3 if filter_func else top_k
        scores, indices = self.index.search(query_normalized, min(search_k, len(self.chunks)))
        
        # Collect results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            if score < threshold:
                continue
            
            chunk = self.chunks[idx]
            
            # Apply filter if provided
            if filter_func and not filter_func(chunk):
                continue
            
            results.append((chunk, float(score)))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def hybrid_search(
        self,
        query: str,
        query_embedding: np.ndarray,
        bm25_scores: np.ndarray,
        top_k: int = TOP_K_RESULTS,
        alpha: float = HYBRID_SEARCH_ALPHA
    ) -> List[Tuple[Chunk, float]]:
        """
        Hybrid search combining semantic and keyword search.
        
        Args:
            query: Original query text
            query_embedding: Query embedding vector
            bm25_scores: BM25 scores from keyword search
            top_k: Number of results
            alpha: Weight for semantic search (1-alpha for keyword)
        """
        # Get semantic scores
        query_normalized = self._normalize_embeddings(query_embedding.reshape(1, -1))
        semantic_scores, indices = self.index.search(query_normalized, len(self.chunks))
        
        # Normalize scores to [0, 1]
        semantic_scores = semantic_scores[0]
        semantic_scores = (semantic_scores - semantic_scores.min()) / (semantic_scores.max() - semantic_scores.min() + 1e-8)
        
        bm25_normalized = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min() + 1e-8)
        
        # Combine scores
        # Create a mapping from index to semantic score
        index_to_semantic = {idx: score for score, idx in zip(semantic_scores, indices[0])}
        
        combined_scores = []
        for i in range(len(self.chunks)):
            semantic_score = index_to_semantic.get(i, 0)
            bm25_score = bm25_normalized[i] if i < len(bm25_normalized) else 0
            
            combined = alpha * semantic_score + (1 - alpha) * bm25_score
            combined_scores.append((i, combined))
        
        # Sort by combined score
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        results = []
        for idx, score in combined_scores[:top_k]:
            results.append((self.chunks[idx], float(score)))
        
        return results
    
    def save(self, path: Optional[str] = None):
        """Save the vector store to disk."""
        import faiss
        
        save_path = Path(path) if path else VECTOR_STORE_DIR
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path / "index.faiss"))
        
        # Save chunks and metadata
        with open(save_path / "chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)
        
        with open(save_path / "metadata.json", "w") as f:
            json.dump(self.metadata, f)
        
        if self.embeddings is not None:
            np.save(save_path / "embeddings.npy", self.embeddings)
        
        print(f"[OK] Vector store saved to {save_path}")
    
    def load(self, path: Optional[str] = None):
        """Load the vector store from disk."""
        import faiss
        
        load_path = Path(path) if path else VECTOR_STORE_DIR
        
        if not load_path.exists():
            raise FileNotFoundError(f"Vector store not found at {load_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path / "index.faiss"))
        
        # Load chunks
        with open(load_path / "chunks.pkl", "rb") as f:
            self.chunks = pickle.load(f)
        
        # Load metadata
        with open(load_path / "metadata.json", "r") as f:
            self.metadata = json.load(f)
        
        # Load embeddings if available
        embeddings_path = load_path / "embeddings.npy"
        if embeddings_path.exists():
            self.embeddings = np.load(embeddings_path)
        
        print(f"[OK] Vector store loaded from {load_path}")
        print(f"  - {len(self.chunks)} chunks")
        print(f"  - Index size: {self.index.ntotal}")
    
    def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit vectors for cosine similarity."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / (norms + 1e-8)
    
    def _import_faiss(self):
        """Import FAISS lazily."""
        import faiss
        return faiss
    
    @property
    def size(self) -> int:
        """Get the number of vectors in the store."""
        return self.index.ntotal
    
    def get_all_chunks(self) -> List[Chunk]:
        """Get all stored chunks."""
        return self.chunks
    
    def clear(self):
        """Clear the vector store."""
        import faiss
        
        # Reset index
        if self.index_type == "flat":
            self.index = faiss.IndexFlatIP(self.dimension)
        elif self.index_type == "ivf":
            quantizer = faiss.IndexFlatIP(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        elif self.index_type == "hnsw":
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        
        self.chunks = []
        self.metadata = []
        self.embeddings = None


if __name__ == "__main__":
    # Test vector store
    import faiss
    
    # Create a simple test
    dimension = 1536
    store = VectorStore(dimension=dimension)
    
    # Create dummy data
    from document_loader import DocumentLoader
    from chunker import TextChunker, Chunk
    
    # Create fake chunks
    chunks = [
        Chunk(
            content="Amazon is an e-commerce company",
            metadata={"source": "test"},
            chunk_id="1",
            source="test",
            start_index=0,
            end_index=100,
            token_count=10
        ),
        Chunk(
            content="Google is a search engine company",
            metadata={"source": "test"},
            chunk_id="2",
            source="test",
            start_index=0,
            end_index=100,
            token_count=10
        )
    ]
    
    # Create random embeddings for testing
    embeddings = np.random.randn(2, dimension).astype('float32')
    
    # Add to store
    store.add_chunks(chunks, embeddings)
    print(f"Store size: {store.size}")
    
    # Test search
    query_embedding = np.random.randn(dimension).astype('float32')
    results = store.search(query_embedding, top_k=2, threshold=0.0)
    
    for chunk, score in results:
        print(f"Score {score:.4f}: {chunk.content}")
