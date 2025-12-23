"""
RAG Engine Module
The main RAG system that orchestrates all components.
"""
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from config import (
    OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, MAX_TOKENS,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS,
    USE_QUERY_EXPANSION, USE_RERANKING, HYBRID_SEARCH_ALPHA
)
from document_loader import DocumentLoader, CompanyDataLoader, Document
from chunker import TextChunker, ContextualChunker, Chunk
from embeddings import EmbeddingGenerator, HybridEmbeddingGenerator
from vector_store import VectorStore
from query_processor import QueryProcessor, QueryResult


console = Console()


class RAGEngine:
    """
    Advanced RAG Engine with all modern techniques:
    
    1. Smart document loading and preprocessing
    2. Semantic and contextual chunking
    3. Hybrid search (semantic + keyword)
    4. Query expansion and HyDE
    5. Reranking
    6. Contextual compression
    7. Conversational memory
    """
    
    def __init__(
        self,
        api_key: str = OPENAI_API_KEY,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ):
        self.api_key = api_key or OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        
        # Initialize components
        self.document_loader = CompanyDataLoader()
        self.chunker = ContextualChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedder = HybridEmbeddingGenerator(api_key=api_key)
        self.vector_store = VectorStore()
        self.query_processor = QueryProcessor(api_key=api_key)
        
        # State
        self.documents: List[Document] = []
        self.chunks: List[Chunk] = []
        self.conversation_history: List[Dict[str, str]] = []
        self.is_initialized = False
    
    def add_document(self, file_path: str) -> Dict[str, Any]:
        """Add a single document to the RAG system."""
        console.print(f"[blue]Loading document: {file_path}[/blue]")
        
        # Load document
        doc = self.document_loader.load_file(file_path)
        self.documents.append(doc)
        
        # Extract company info
        company_info = self.document_loader.extract_company_info(doc)
        
        # Chunk document
        doc_chunks = self.chunker.chunk_document(doc, strategy="semantic")
        
        # Add context to chunks
        doc_chunks = self.chunker.add_context_to_chunks(doc_chunks)
        
        self.chunks.extend(doc_chunks)
        
        console.print(f"[green][OK] Created {len(doc_chunks)} chunks[/green]")
        
        return {
            'document': doc,
            'company_info': company_info,
            'num_chunks': len(doc_chunks)
        }
    
    def add_text(self, text: str, source_name: str = "direct_input",
                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add raw text to the RAG system with optional custom metadata.

        Args:
            text: The text content to add
            source_name: Identifier for the source (e.g., URL or filename)
            metadata: Optional custom metadata to attach to the document

        Returns:
            Dict with document and num_chunks
        """
        doc = self.document_loader.load_from_text(text, source_name, metadata)
        self.documents.append(doc)

        # Chunk document
        doc_chunks = self.chunker.chunk_document(doc, strategy="semantic")
        doc_chunks = self.chunker.add_context_to_chunks(doc_chunks)
        self.chunks.extend(doc_chunks)

        # Auto-update index if already initialized (enables real-time processing)
        if self.is_initialized and self.vector_store and self.embedder:
            try:
                # Generate embeddings for new chunks only
                new_embeddings = self.embedder.embed_chunks(doc_chunks, show_progress=False)

                # Add to existing vector store
                self.vector_store.add_chunks(doc_chunks, new_embeddings)

                # Update BM25 index for hybrid search
                if hasattr(self.embedder, 'create_sparse_embeddings'):
                    all_texts = [chunk.content for chunk in self.chunks]
                    self.embedder.create_sparse_embeddings(all_texts)
            except Exception as e:
                print(f"[WARN] Failed to auto-update index: {e}")

        return {
            'document': doc,
            'num_chunks': len(doc_chunks)
        }
    
    def add_directory(self, directory_path: str) -> Dict[str, Any]:
        """Add all documents from a directory."""
        console.print(f"[blue]Loading documents from: {directory_path}[/blue]")
        
        docs = self.document_loader.load_directory(directory_path)
        results = []
        
        for doc in docs:
            self.documents.append(doc)
            doc_chunks = self.chunker.chunk_document(doc, strategy="semantic")
            doc_chunks = self.chunker.add_context_to_chunks(doc_chunks)
            self.chunks.extend(doc_chunks)
            results.append({
                'source': doc.source,
                'num_chunks': len(doc_chunks)
            })
        
        console.print(f"[green][OK] Loaded {len(docs)} documents, {len(self.chunks)} total chunks[/green]")
        
        return {
            'num_documents': len(docs),
            'total_chunks': len(self.chunks),
            'details': results
        }
    
    def build_index(self):
        """Build the vector index from all loaded chunks."""
        if not self.chunks:
            raise ValueError("No documents loaded. Add documents first.")
        
        console.print("[blue]Building vector index...[/blue]")
        
        # Generate embeddings
        embeddings = self.embedder.embed_chunks(self.chunks, show_progress=True)
        
        # Add to vector store
        self.vector_store.add_chunks(self.chunks, embeddings)
        
        # Build BM25 index for hybrid search
        texts = [chunk.content for chunk in self.chunks]
        self.embedder.create_sparse_embeddings(texts)
        
        self.is_initialized = True
        
        console.print(f"[green][OK] Index built with {self.vector_store.size} vectors[/green]")
    
    def retrieve(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        use_hybrid: bool = True,
        expand_query: bool = USE_QUERY_EXPANSION
    ) -> List[Tuple[Chunk, float]]:
        """
        Retrieve relevant chunks for a query.
        
        Uses:
        - Query expansion (optional)
        - Hybrid search (semantic + keyword)
        - Reciprocal rank fusion for multi-query results
        """
        if not self.is_initialized:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Process query
        processed = self.query_processor.process_query(
            query,
            expand=expand_query,
            use_hyde=False
        )
        
        all_results = []
        
        # Search with each query variation
        for q in processed['expanded_queries']:
            query_embedding = self.embedder.embed_query(q)
            
            if use_hybrid:
                # Hybrid search
                bm25_scores = self.embedder.get_bm25_scores(q)
                results = self.vector_store.hybrid_search(
                    q, query_embedding, bm25_scores,
                    top_k=top_k * 2,
                    alpha=HYBRID_SEARCH_ALPHA
                )
            else:
                # Pure semantic search
                results = self.vector_store.search(
                    query_embedding,
                    top_k=top_k * 2
                )
            
            all_results.extend(results)
        
        # Deduplicate and aggregate scores using Reciprocal Rank Fusion
        chunk_scores = {}
        for chunk, score in all_results:
            chunk_id = chunk.chunk_id
            if chunk_id not in chunk_scores:
                chunk_scores[chunk_id] = {'chunk': chunk, 'scores': []}
            chunk_scores[chunk_id]['scores'].append(score)
        
        # Calculate RRF score
        fused_results = []
        k = 60  # RRF constant
        for chunk_id, data in chunk_scores.items():
            # Average of reciprocal ranks
            rrf_score = sum(1 / (k + i) for i, _ in enumerate(sorted(data['scores'], reverse=True)))
            fused_results.append((data['chunk'], rrf_score))
        
        # Sort by fused score
        fused_results.sort(key=lambda x: x[1], reverse=True)
        
        return fused_results[:top_k]
    
    def generate_response(
        self,
        query: str,
        context_chunks: List[QueryResult],
        use_history: bool = True
    ) -> str:
        """
        Generate a response using the retrieved context.
        """
        # Build context string
        context_parts = []
        for i, result in enumerate(context_chunks):
            content = result.compressed_content or result.chunk.content
            source = result.chunk.source
            context_parts.append(f"[Source {i+1}: {source}]\n{content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Build system prompt
        system_prompt = """You are a helpful assistant answering questions about companies.
Use the provided context to answer questions accurately.
If the context doesn't contain enough information, say so clearly.
Always cite the source when providing specific information.
Be concise but comprehensive."""

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context
        if use_history and self.conversation_history:
            # Add last 3 exchanges
            for exchange in self.conversation_history[-6:]:
                messages.append(exchange)
        
        # Add current query with context
        user_message = f"""Context information:
{context}

Question: {query}

Please provide a helpful answer based on the context above."""

        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        
        answer = response.choices[0].message.content
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": query})
        self.conversation_history.append({"role": "assistant", "content": answer})
        
        return answer
    
    def query(
        self,
        question: str,
        top_k: int = TOP_K_RESULTS,
        use_hybrid: bool = True,
        use_reranking: bool = USE_RERANKING,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline: retrieve, rerank, and generate.
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        if verbose:
            console.print(f"\n[bold blue]Query:[/bold blue] {question}")
        
        # Step 1: Retrieve
        retrieved = self.retrieve(question, top_k=top_k * 2, use_hybrid=use_hybrid)
        
        if verbose:
            console.print(f"[dim]Retrieved {len(retrieved)} chunks[/dim]")
        
        # Step 2: Process results (rerank and compress)
        processed_results = self.query_processor.process_results(
            question,
            retrieved,
            rerank=use_reranking,
            compress=True,
            top_k=top_k
        )
        
        if verbose:
            console.print(f"[dim]After reranking: {len(processed_results)} chunks[/dim]")
        
        # Step 3: Generate response
        answer = self.generate_response(question, processed_results)
        
        # Prepare sources
        sources = []
        for result in processed_results:
            sources.append({
                'source': result.chunk.source,
                'score': result.rerank_score or result.score,
                'content_preview': result.chunk.content[:200] + "..."
            })
        
        if verbose:
            console.print(Panel(Markdown(answer), title="Answer", border_style="green"))
        
        return {
            'question': question,
            'answer': answer,
            'sources': sources,
            'num_chunks_retrieved': len(retrieved),
            'num_chunks_used': len(processed_results)
        }
    
    def chat(self, message: str) -> str:
        """
        Simple chat interface that returns just the answer.
        """
        result = self.query(message, verbose=False)
        return result['answer']
    
    def save(self, path: str = None):
        """Save the RAG engine state."""
        self.vector_store.save(path)
        console.print("[green][OK] RAG engine saved[/green]")
    
    def load(self, path: str = None):
        """Load a saved RAG engine state."""
        self.vector_store.load(path)
        self.chunks = self.vector_store.get_all_chunks()
        
        # Rebuild BM25 index
        texts = [chunk.content for chunk in self.chunks]
        self.embedder.create_sparse_embeddings(texts)
        
        self.is_initialized = True
        console.print("[green][OK] RAG engine loaded[/green]")
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG engine."""
        return {
            'num_documents': len(self.documents),
            'num_chunks': len(self.chunks),
            'vector_store_size': self.vector_store.size if self.is_initialized else 0,
            'embedding_cache_size': self.embedder.cache_size,
            'conversation_length': len(self.conversation_history)
        }


def create_rag_engine(
    documents_path: Optional[str] = None,
    api_key: str = OPENAI_API_KEY
) -> RAGEngine:
    """
    Factory function to create and initialize a RAG engine.
    """
    engine = RAGEngine(api_key=api_key)
    
    if documents_path:
        path = Path(documents_path)
        if path.is_file():
            engine.add_document(str(path))
        elif path.is_dir():
            engine.add_directory(str(path))
        else:
            raise ValueError(f"Invalid path: {documents_path}")
        
        engine.build_index()
    
    return engine


if __name__ == "__main__":
    # Demo usage
    console.print("[bold]RAG Engine Demo[/bold]\n")
    
    # Create engine
    engine = RAGEngine()
    
    # Add sample data
    sample_text = """
    Amazon.com, Inc. is a multinational technology giant specializing in e-commerce, 
    cloud computing, online advertising, digital streaming, and artificial intelligence.
    
    What Amazon Does:
    Amazon operates the world's largest online marketplace and AWS cloud services.
    
    Board of Directors:
    Jeffrey P. Bezos, Andrew R. Jassy, Jamie Gorelick, Keith Alexander, Indra Nooyi
    """
    
    engine.add_text(sample_text, "Amazon Company Profile")
    engine.build_index()
    
    # Test queries
    queries = [
        "What does Amazon do?",
        "Who are the board members of Amazon?",
        "What is AWS?"
    ]
    
    for query in queries:
        result = engine.query(query, verbose=True)
        console.print()
