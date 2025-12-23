import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator
from openai import OpenAI
from langfuse.openai import openai as langfuse_openai
from langfuse import Langfuse, observe

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

# Initialize Langfuse
try:
    langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

    if langfuse_secret and langfuse_public:
        langfuse = Langfuse(
            secret_key=langfuse_secret,
            public_key=langfuse_public,
            host=langfuse_host
        )
        print("[OK] Langfuse initialized for tracing")
        print(f"[INFO] Traces will be sent to: {langfuse_host}")
    else:
        print("[WARN] Langfuse keys not found in environment, tracing disabled")
        langfuse = None
except Exception as e:
    print(f"[WARN] Langfuse initialization failed: {e}")
    langfuse = None


class RAGService:
    def __init__(self):
        """Initialize RAG service with actual RAGEngine"""
        self.api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
        self.rag_engine = None
        self.documents_dir = IRIS_DIR / "documents"

        # Use environment variable for vector store path (supports both local and Render deployment)
        vector_store_env = os.getenv("VECTOR_STORE_PATH")
        if vector_store_env:
            self.vector_store_path = Path(vector_store_env)
        else:
            # Default to local development path
            self.vector_store_path = IRIS_DIR / "vector_store"

        if RAGEngine:
            try:
                # Initialize RAG engine
                self.rag_engine = RAGEngine(api_key=self.api_key)
                print("[OK] RAG Engine initialized in RAGService")

                # Try to load existing vector store
                try:
                    # Pass the full path to the vector store
                    self.rag_engine.load(str(self.vector_store_path))
                    # Force set is_initialized to True if load succeeded
                    if self.rag_engine.vector_store.size > 0:
                        self.rag_engine.is_initialized = True
                        print(f"[OK] RAG index loaded with {self.rag_engine.vector_store.size} vectors")
                        print(f"[OK] RAG is ready for queries")
                    else:
                        print("[WARN] No existing RAG index found or index is empty.")
                        # Try to load documents and build index if vector store is empty
                        self._load_and_build_index()
                except Exception as e:
                    print(f"[WARN] Could not load RAG index: {e}")
                    import traceback
                    traceback.print_exc()
                    # Try to load documents and build index
                    print("[NOTE] Attempting to load documents and build index...")
                    self._load_and_build_index()

            except Exception as e:
                print(f"[X] Failed to initialize RAG Engine: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[X] RAGEngine class not available (ImportError)")

    def _load_and_build_index(self):
        """Load documents from documents directory and build index"""
        try:
            if not self.documents_dir.exists():
                print(f"[WARN] Documents directory not found: {self.documents_dir}")
                return

            # Find all document files
            doc_files = list(self.documents_dir.glob("*.docx")) + \
                        list(self.documents_dir.glob("*.pdf")) + \
                        list(self.documents_dir.glob("*.txt"))

            if not doc_files:
                print("[WARN] No documents found in documents/ folder")
                return

            print(f"[INFO] Found {len(doc_files)} documents, loading...")

            # Load each document
            loaded = 0
            for doc_file in doc_files:
                try:
                    print(f"[INFO] Loading {doc_file.name}...")
                    result = self.rag_engine.add_document(str(doc_file))
                    print(f"[OK] Loaded {doc_file.name} - {result['num_chunks']} chunks")
                    loaded += 1
                except Exception as e:
                    print(f"[WARN] Failed to load {doc_file.name}: {e}")

            if loaded > 0:
                print(f"[INFO] Building vector index for {loaded} documents...")
                self.rag_engine.build_index()
                print("[OK] Index built successfully!")

                # Save the engine
                print("[INFO] Saving RAG engine...")
                self.rag_engine.save(str(self.vector_store_path))
                print("[OK] Engine saved!")
            else:
                print("[WARN] No documents were loaded successfully")

        except Exception as e:
            print(f"[ERROR] Failed to load and build index: {e}")
            import traceback
            traceback.print_exc()

    async def query_stream(
        self,
        question: str,
        symbol: Optional[str] = None,
        context: Optional[str] = None,
        session_id: str = "default",
        use_web_search: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Answer a question using RAG with streaming response and web search enrichment
        """
        # Create Langfuse trace for this query
        trace = None
        if langfuse:
            try:
                trace = langfuse.trace(
                    name="rag-query-stream",
                    input={"question": question, "symbol": symbol, "session_id": session_id},
                    metadata={"use_web_search": use_web_search}
                )
            except Exception as e:
                print(f"[WARN] Failed to create Langfuse trace: {e}")

        if not self.rag_engine or not self.rag_engine.is_initialized:
            yield json.dumps({
                "type": "error",
                "content": "RAG Engine is not initialized or index is empty."
            }) + "\n"
            if trace:
                trace.update(output={"error": "RAG_NOT_INITIALIZED"})
            return

        try:
            import asyncio

            # Step 1: Get relevant context from RAG
            yield json.dumps({"type": "status", "content": "Searching knowledge base..."}) + "\n"

            final_question = f"[{symbol}] {question}" if symbol else question
            print(f"\n[RAG QUERY] 📚 Vector Store Search: {final_question}")

            # Create span for RAG retrieval
            retrieval_span = None
            if trace:
                retrieval_span = trace.span(
                    name="rag-retrieval",
                    input={"question": final_question, "top_k": 5}
                )

            # Get RAG context in thread pool
            loop = asyncio.get_event_loop()
            rag_result = await loop.run_in_executor(
                None,
                lambda: self.rag_engine.query(
                    question=final_question,
                    top_k=5,
                    use_hybrid=True,
                    verbose=False
                )
            )

            print(f"[RAG QUERY] ✓ Found {len(rag_result.get('sources', []))} sources from vector store")

            # Update retrieval span
            if retrieval_span:
                retrieval_span.end(output={
                    "num_sources": len(rag_result.get('sources', [])),
                    "sources": [s.get('source') for s in rag_result.get('sources', [])[:3]]
                })

            # Step 2: Use web search to enrich context
            web_context = ""
            if use_web_search:
                yield json.dumps({"type": "status", "content": "Searching the web for latest information..."}) + "\n"
                web_context = await self._web_search(question, symbol)

            # Step 3: Combine contexts with proper source numbering
            combined_context = ""
            source_list = []

            if 'sources' in rag_result and rag_result['sources']:
                for idx, src in enumerate(rag_result['sources'], 1):
                    # Get chunk metadata for enhanced attribution
                    chunk_metadata = src.get('metadata', {})
                    source_type = chunk_metadata.get('source_type', 'document')

                    # Determine title based on source type
                    if source_type == "scraped_news":
                        source_title = chunk_metadata.get('article_title', src.get('source', 'Unknown Article'))
                    else:
                        source_title = src.get('source', 'Unknown Source')

                    source_content = src.get('content', '')
                    combined_context += f"\n[Source {idx}: {source_title}]\n{source_content}\n"

                    # Build base source object
                    source_obj = {
                        "number": idx,
                        "title": source_title,
                        "content": src.get('content_preview', ''),
                        "score": src.get('score', 0),
                        "type": source_type,
                    }

                    # Add type-specific metadata
                    if source_type == "scraped_news":
                        source_obj.update({
                            "company": chunk_metadata.get('company_name', 'Unknown'),
                            "url": chunk_metadata.get('original_url', ''),
                            "domain": chunk_metadata.get('domain', ''),
                            "timestamp": chunk_metadata.get('discovery_timestamp', ''),
                        })
                    elif source_type == "document":
                        source_obj.update({
                            "filename": chunk_metadata.get('filename', ''),
                        })

                    source_list.append(source_obj)

            # Add web search as additional source
            if web_context:
                web_source_num = len(source_list) + 1
                combined_context += f"\n[Source {web_source_num}: Web Search - Latest Information]\n{web_context}\n"
                source_list.append({
                    "number": web_source_num,
                    "title": "Web Search - Latest Information",
                    "content": web_context[:200] + "..." if len(web_context) > 200 else web_context,
                    "score": 1.0,
                    "type": "web_search"
                })
                print(f"[RAG QUERY] ✓ Combined: {len(source_list)-1} vector store + 1 web search = {len(source_list)} total sources")
            else:
                print(f"[RAG QUERY] ✓ Using {len(source_list)} sources from vector store only (no web search)")

            # Step 4: Stream the response
            yield json.dumps({"type": "status", "content": "Generating answer..."}) + "\n"

            # Create streaming chat completion with citation instructions
            # Use Langfuse-wrapped OpenAI client for automatic tracing
            if langfuse:
                client = langfuse_openai.OpenAI(api_key=self.api_key)
            else:
                client = OpenAI(api_key=self.api_key)

            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful financial analyst assistant.

IMPORTANT CITATION RULES:
1. Use the provided numbered sources [Source 1], [Source 2], etc.
2. Add inline citations using [1], [2], [3] etc. immediately after facts
3. Multiple sources can be cited together like [1, 2]
4. ALWAYS cite sources when providing specific information
5. Format: "Apple announced new products [1]. The stock rose 5% [2, 3]."
6. Be concise but comprehensive
7. If information isn't in the sources, clearly state that

Example format:
"Apple recently announced executive transitions [1] and expanded Apple Fitness+ to 28 new markets [2]. According to latest reports, the company is focusing on AI initiatives [5]."
"""
                },
                {
                    "role": "user",
                    "content": f"""Based on the following sources, answer the question with proper inline citations.

SOURCES:
{combined_context}

QUESTION: {question}

Remember to cite sources using [1], [2], etc. inline with your answer."""
                }
            ]

            # Create generation span for Langfuse
            generation_span = None
            if trace and langfuse:
                generation_span = trace.generation(
                    name="llm-answer-generation",
                    model="gpt-4o-mini",
                    input=messages,
                    metadata={"temperature": 0.7, "stream": True}
                )

            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
                temperature=0.7
            )

            # Collect response for tracing
            full_response = ""

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield json.dumps({
                        "type": "content",
                        "content": chunk.choices[0].delta.content
                    }) + "\n"

            # Step 5: Send numbered sources with citations
            yield json.dumps({
                "type": "sources",
                "sources": source_list
            }) + "\n"

            yield json.dumps({"type": "done"}) + "\n"

        except Exception as e:
            print(f"Error in RAG stream query: {e}")
            yield json.dumps({
                "type": "error",
                "content": f"Sorry, I encountered an error: {str(e)}"
            }) + "\n"

    async def _web_search(self, query: str, symbol: Optional[str] = None) -> str:
        """Use Tavily API for real-time web search"""
        try:
            import asyncio
            from datetime import datetime
            import aiohttp
            import ssl
            import certifi

            # Get Tavily API key
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if not tavily_api_key:
                print("[WARN] TAVILY_API_KEY not found, web search disabled")
                return ""

            # Create SSL context using certifi's certificate bundle
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            # Enhance query with symbol if provided
            search_query = f"{symbol} {query}" if symbol else query
            print(f"[TAVILY WEB SEARCH] 🌐 Searching for: '{search_query}'")

            # Tavily Search API
            async def _search():
                # Create connector with SSL context
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": tavily_api_key,
                            "query": search_query,
                            "search_depth": "basic",
                            "max_results": 5,
                            "include_answer": True,
                            "include_raw_content": False
                        },
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            # Extract answer and top results
                            results = []

                            # Add Tavily's AI-generated answer if available
                            if data.get('answer'):
                                results.append(f"Summary: {data['answer']}")
                                print(f"[TAVILY WEB SEARCH] ✓ AI Summary: {data['answer'][:100]}...")

                            # Add top search results
                            num_results = len(data.get('results', []))
                            for result in data.get('results', [])[:3]:
                                title = result.get('title', '')
                                content = result.get('content', '')
                                url = result.get('url', '')
                                results.append(f"{title}: {content} ({url})")

                            print(f"[TAVILY WEB SEARCH] ✓ Retrieved {num_results} results, using top 3")
                            return "\n\n".join(results)
                        else:
                            print(f"[TAVILY WEB SEARCH] ✗ Search failed with status {response.status}")
                            return ""

            web_results = await _search()
            if web_results:
                print(f"[TAVILY WEB SEARCH] ✓ Web search completed successfully ({len(web_results)} chars)")
            else:
                print(f"[TAVILY WEB SEARCH] ✗ No results returned")
            return web_results or ""

        except Exception as e:
            print(f"Web search error: {e}")
            import traceback
            traceback.print_exc()
            return ""

    async def query(
        self,
        question: str,
        symbol: Optional[str] = None,
        context: Optional[str] = None,
        session_id: str = "default",
        use_web_search: bool = True
    ) -> Dict:
        """
        Answer a question using RAG (non-streaming version for compatibility)
        Now includes Tavily web search!
        """
        if not self.rag_engine or not self.rag_engine.is_initialized:
            return {
                "answer": "RAG Engine is not initialized or index is empty.",
                "sources": [],
                "confidence": 0,
                "error": "RAG_NOT_INITIALIZED"
            }

        try:
            import asyncio

            final_question = f"[{symbol}] {question}" if symbol else question
            print(f"\n[RAG QUERY] 📚 Vector Store Search: {final_question}")

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

            print(f"[RAG QUERY] ✓ Found {len(result.get('sources', []))} sources from vector store")

            # Get web search results
            web_context = ""
            if use_web_search:
                web_context = await self._web_search(question, symbol)

            sources = []
            combined_context = ""
            source_num = 1

            if 'sources' in result:
                for src in result['sources']:
                    # Get chunk metadata for enhanced attribution
                    chunk_metadata = src.get('metadata', {})
                    source_type = chunk_metadata.get('source_type', 'document')

                    # Determine title based on source type
                    if source_type == "scraped_news":
                        source_title = chunk_metadata.get('article_title', src.get('source', 'Unknown Article'))
                    else:
                        source_title = src.get('source', 'Unknown Source')

                    # Add to combined context
                    combined_context += f"\n[Source {source_num}: {source_title}]\n{src.get('content', '')}\n"

                    # Build base source object
                    source_obj = {
                        "number": source_num,
                        "title": source_title,
                        "url": chunk_metadata.get('original_url', '') if source_type == "scraped_news" else "",
                        "content": src.get('content_preview', ''),
                        "score": src.get('score', 0),
                        "type": source_type,
                    }

                    # Add type-specific metadata
                    if source_type == "scraped_news":
                        source_obj.update({
                            "company": chunk_metadata.get('company_name', 'Unknown'),
                            "domain": chunk_metadata.get('domain', ''),
                            "timestamp": chunk_metadata.get('discovery_timestamp', ''),
                        })
                    elif source_type == "document":
                        source_obj.update({
                            "filename": chunk_metadata.get('filename', ''),
                        })

                    sources.append(source_obj)
                    source_num += 1

            # Add web search to combined context and sources
            if web_context:
                combined_context += f"\n[Source {source_num}: Web Search - Latest Information]\n{web_context}\n"
                sources.append({
                    "number": source_num,
                    "title": "Web Search - Latest Information",
                    "url": "",
                    "content": web_context[:200] + "..." if len(web_context) > 200 else web_context,
                    "score": 1.0,
                    "type": "web_search"
                })
                print(f"[RAG QUERY] ✓ Combined: {source_num-1} vector store + 1 web search = {source_num} total sources")
            else:
                print(f"[RAG QUERY] ✓ Using {len(sources)} sources from vector store only")

            # Generate answer with BOTH vector store and web search context
            client = OpenAI(api_key=self.api_key)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful financial analyst assistant.
Always cite sources using [1], [2], [3] etc. when providing specific information.
Be concise but comprehensive."""
                    },
                    {
                        "role": "user",
                        "content": f"""Based on the following sources, answer the question with inline citations.

SOURCES:
{combined_context}

QUESTION: {question}

Provide a helpful answer with citations [1], [2], etc."""
                    }
                ],
                temperature=0.1
            )

            answer = completion.choices[0].message.content

            return {
                "answer": answer,
                "sources": sources,
                "confidence": 0.9,
                "model": "gpt-4o-mini",
                "query": result.get('question', question)
            }

        except Exception as e:
            print(f"Error in RAG query: {e}")
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
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

