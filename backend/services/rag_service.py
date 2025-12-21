import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add rag to path to import rag_engine
# Assuming backend is at root/backend and rag is at root/rag
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
IRIS_DIR = PROJECT_ROOT / "rag"
sys.path.append(str(IRIS_DIR))

try:
    from rag_engine import RAGEngine, create_rag_engine
except ImportError as e:
    print(f"Error importing RAG engine: {e}")
    RAGEngine = None


class RAGService:
    def __init__(self):
        """Initialize RAG service with actual RAGEngine"""
        self.api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
        self.rag_engine = None
        self.documents_dir = IRIS_DIR / "documents"

        if RAGEngine:
            try:
                # Initialize RAG engine
                self.rag_engine = RAGEngine(api_key=self.api_key)
                print("[OK] RAG Engine initialized in RAGService")

                # Try to load existing vector store
                try:
                    self.rag_engine.load()
                    # Force set is_initialized to True if load succeeded
                    if self.rag_engine.vector_store.size > 0:
                        self.rag_engine.is_initialized = True
                        print(f"[OK] RAG index loaded with {self.rag_engine.vector_store.size} vectors")
                        print(f"[OK] RAG is ready for queries")
                    else:
                        print("[WARN] No existing RAG index found. RAG will be empty until documents are added.")
                except Exception as e:
                    print(f"[WARN] Could not load RAG index: {e}")
                    print("[NOTE] RAG will be empty until documents are added.")

            except Exception as e:
                print(f"[X] Failed to initialize RAG Engine: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[X] RAGEngine class not available (ImportError)")

    async def query(
        self,
        question: str,
        symbol: Optional[str] = None,
        context: Optional[str] = None,
        session_id: str = "default"
    ) -> Dict:
        """
        Answer a question using RAG
        """
        if not self.rag_engine or not self.rag_engine.is_initialized:
            # Fallback if RAG is not ready
            return {
                "answer": "RAG Engine is not initialized or index is empty. Please add documents via the setup interface or ensure the backend has built the index.",
                "sources": [],
                "confidence": 0,
                "error": "RAG_NOT_INITIALIZED"
            }

        try:
            import asyncio

            # Prepare query parameters
            # The RAG engine's query method is synchronous (it calls OpenAI sync client),
            # Run in thread pool to avoid blocking async event loop and prevent Windows file I/O errors

            # Incorporate symbol context if provided
            final_question = question
            if symbol:
                final_question = f"[{symbol}] {question}"

            # Use the RAG engine to get answer and sources in a thread pool
            # We use use_hybrid=True by default for best results
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.rag_engine.query(
                    question=final_question,
                    top_k=5,
                    use_hybrid=True,
                    verbose=False
                )
            )
            
            # Format sources for frontend
            sources = []
            if 'sources' in result:
                for src in result['sources']:
                    sources.append({
                        "title": src.get('source', 'Unknown Source'),
                        "url": "",  # Link not available in current RAG implementation
                        "content": src.get('content_preview', ''),
                        "score": src.get('score', 0)
                    })

            return {
                "answer": result.get('answer', "No answer generated."),
                "sources": sources,
                "confidence": 0.9, # Placeholder
                "model": "gpt-4o-mini", # From config
                "query": result.get('question', question)
            }

        except Exception as e:
            print(f"Error in RAG query: {e}")
            return {
                "answer": f"Sorry, I encountered an error during RAG query: {str(e)}",
                "sources": [],
                "confidence": 0,
                "error": str(e)
            }

    async def get_company_info(self, symbol: str) -> str:
        """
        Get company information for RAG context
        """
        # This can be expanded to use the RAG engine to retrieve specific doc summaries
        return f"Company context for {symbol}"

    def clear_history(self, session_id: str = "default"):
        """Clear conversation history"""
        if self.rag_engine:
            self.rag_engine.clear_history()

    def get_history(self, session_id: str = "default") -> List[Dict]:
        """Get conversation history"""
        if self.rag_engine:
            return self.rag_engine.conversation_history
        return []

