"""
Gradio Web Interface for Company RAG System
A beautiful, user-friendly interface for querying company data.
"""
import gradio as gr
from pathlib import Path
import json
from typing import List, Tuple

from rag_engine import RAGEngine, create_rag_engine
from config import OPENAI_API_KEY


# Global RAG engine instance
rag_engine = None


def initialize_rag() -> str:
    """Initialize the RAG engine with default settings."""
    global rag_engine
    try:
        rag_engine = RAGEngine()
        return "✅ RAG engine initialized successfully!"
    except Exception as e:
        return f"❌ Error initializing RAG engine: {str(e)}"


def add_document(file) -> str:
    """Add a document to the RAG system."""
    global rag_engine
    
    if rag_engine is None:
        return "❌ Please initialize the RAG engine first."
    
    if file is None:
        return "❌ No file uploaded."
    
    try:
        result = rag_engine.add_document(file.name)
        return f"""✅ Document added successfully!
        
📄 **File:** {result['document'].source}
📊 **Chunks created:** {result['num_chunks']}
📝 **Word count:** {result['document'].metadata.get('word_count', 'N/A')}

Company Information:
- **Name:** {result['company_info'].get('company_name', 'N/A')}
- **Board Members:** {', '.join(result['company_info'].get('board_members', [])[:5]) or 'N/A'}
"""
    except Exception as e:
        return f"❌ Error adding document: {str(e)}"


def add_text_document(text: str, source_name: str) -> str:
    """Add text directly to the RAG system."""
    global rag_engine
    
    if rag_engine is None:
        return "❌ Please initialize the RAG engine first."
    
    if not text.strip():
        return "❌ Please enter some text."
    
    try:
        source = source_name.strip() or "direct_input"
        result = rag_engine.add_text(text, source)
        return f"""✅ Text added successfully!
        
📄 **Source:** {source}
📊 **Chunks created:** {result['num_chunks']}
"""
    except Exception as e:
        return f"❌ Error adding text: {str(e)}"


def build_index() -> str:
    """Build the vector index."""
    global rag_engine
    
    if rag_engine is None:
        return "❌ Please initialize the RAG engine first."
    
    if not rag_engine.chunks:
        return "❌ No documents loaded. Please add documents first."
    
    try:
        rag_engine.build_index()
        stats = rag_engine.get_stats()
        return f"""✅ Index built successfully!
        
📊 **Statistics:**
- Documents: {stats['num_documents']}
- Chunks: {stats['num_chunks']}
- Vectors: {stats['vector_store_size']}
"""
    except Exception as e:
        return f"❌ Error building index: {str(e)}"


def query_rag(question: str, use_hybrid: bool, use_reranking: bool, top_k: int) -> Tuple[str, str]:
    """Query the RAG system."""
    global rag_engine
    
    if rag_engine is None:
        return "❌ Please initialize the RAG engine first.", ""
    
    if not rag_engine.is_initialized:
        return "❌ Please build the index first.", ""
    
    if not question.strip():
        return "❌ Please enter a question.", ""
    
    try:
        result = rag_engine.query(
            question,
            top_k=int(top_k),
            use_hybrid=use_hybrid,
            use_reranking=use_reranking,
            verbose=False
        )
        
        # Format sources
        sources_text = "### 📚 Sources Used:\n\n"
        for i, source in enumerate(result['sources'], 1):
            score = source['score']
            if isinstance(score, float):
                score = f"{score:.3f}"
            sources_text += f"**{i}. {source['source']}** (score: {score})\n"
            sources_text += f"> {source['content_preview'][:150]}...\n\n"
        
        return result['answer'], sources_text
    except Exception as e:
        return f"❌ Error querying: {str(e)}", ""


def chat_with_rag(message: str, history: List[List[str]]) -> Tuple[str, List[List[str]]]:
    """Chat interface for the RAG system."""
    global rag_engine
    
    if rag_engine is None or not rag_engine.is_initialized:
        return "Please initialize the RAG engine and build the index first.", history
    
    if not message.strip():
        return "", history
    
    try:
        answer = rag_engine.chat(message)
        history.append([message, answer])
        return "", history
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        history.append([message, error_msg])
        return "", history


def clear_chat() -> List:
    """Clear the chat history."""
    global rag_engine
    if rag_engine:
        rag_engine.clear_history()
    return []


def get_stats() -> str:
    """Get RAG engine statistics."""
    global rag_engine
    
    if rag_engine is None:
        return "RAG engine not initialized."
    
    stats = rag_engine.get_stats()
    return f"""### 📊 RAG Engine Statistics

| Metric | Value |
|--------|-------|
| Documents | {stats['num_documents']} |
| Chunks | {stats['num_chunks']} |
| Vectors | {stats['vector_store_size']} |
| Cached Embeddings | {stats['embedding_cache_size']} |
| Conversation Length | {stats['conversation_length']} |
"""


# Create the Gradio interface
def create_interface():
    with gr.Blocks(title="🏢 Company RAG System", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🏢 Company Information RAG System
        
        An advanced Retrieval-Augmented Generation system for querying company data.
        Upload company documents and ask questions about them!
        
        ---
        """)
        
        with gr.Tab("📁 Setup"):
            gr.Markdown("### Step 1: Initialize the System")
            init_btn = gr.Button("🚀 Initialize RAG Engine", variant="primary")
            init_output = gr.Markdown()
            init_btn.click(initialize_rag, outputs=init_output)
            
            gr.Markdown("---")
            gr.Markdown("### Step 2: Add Documents")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Upload a File")
                    file_upload = gr.File(
                        label="Upload Document (DOCX, PDF, TXT)",
                        file_types=[".docx", ".pdf", ".txt", ".md"]
                    )
                    upload_btn = gr.Button("📤 Add Document")
                    upload_output = gr.Markdown()
                    upload_btn.click(add_document, inputs=file_upload, outputs=upload_output)
                
                with gr.Column():
                    gr.Markdown("#### Or Paste Text Directly")
                    text_input = gr.Textbox(
                        label="Company Information",
                        placeholder="Paste company data here...",
                        lines=10
                    )
                    source_name = gr.Textbox(
                        label="Source Name",
                        placeholder="e.g., Apple Inc."
                    )
                    text_btn = gr.Button("📝 Add Text")
                    text_output = gr.Markdown()
                    text_btn.click(add_text_document, inputs=[text_input, source_name], outputs=text_output)
            
            gr.Markdown("---")
            gr.Markdown("### Step 3: Build Index")
            build_btn = gr.Button("🔨 Build Vector Index", variant="primary")
            build_output = gr.Markdown()
            build_btn.click(build_index, outputs=build_output)
        
        with gr.Tab("❓ Query"):
            gr.Markdown("### Ask Questions About Your Companies")
            
            with gr.Row():
                with gr.Column(scale=3):
                    query_input = gr.Textbox(
                        label="Your Question",
                        placeholder="e.g., Who are the board members of Amazon?",
                        lines=2
                    )
                
                with gr.Column(scale=1):
                    use_hybrid = gr.Checkbox(label="Use Hybrid Search", value=True)
                    use_reranking = gr.Checkbox(label="Use Reranking", value=True)
                    top_k = gr.Slider(minimum=1, maximum=10, value=5, step=1, label="Number of Results")
            
            query_btn = gr.Button("🔍 Search & Answer", variant="primary")
            
            with gr.Row():
                with gr.Column():
                    answer_output = gr.Markdown(label="Answer")
                with gr.Column():
                    sources_output = gr.Markdown(label="Sources")
            
            query_btn.click(
                query_rag,
                inputs=[query_input, use_hybrid, use_reranking, top_k],
                outputs=[answer_output, sources_output]
            )
        
        with gr.Tab("💬 Chat"):
            gr.Markdown("### Chat with Your Company Data")
            
            chatbot = gr.Chatbot(height=400)
            msg = gr.Textbox(
                label="Message",
                placeholder="Ask me anything about the companies...",
                lines=2
            )
            
            with gr.Row():
                submit_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("Clear History")
            
            submit_btn.click(chat_with_rag, inputs=[msg, chatbot], outputs=[msg, chatbot])
            msg.submit(chat_with_rag, inputs=[msg, chatbot], outputs=[msg, chatbot])
            clear_btn.click(clear_chat, outputs=chatbot)
        
        with gr.Tab("📊 Stats"):
            gr.Markdown("### System Statistics")
            stats_btn = gr.Button("🔄 Refresh Stats")
            stats_output = gr.Markdown()
            stats_btn.click(get_stats, outputs=stats_output)
        
        gr.Markdown("""
        ---
        ### 🛠️ Advanced Features Used:
        - **Semantic Chunking**: Intelligently splits documents while preserving context
        - **Hybrid Search**: Combines semantic embeddings with BM25 keyword matching
        - **Query Expansion**: Generates multiple query variations for better retrieval
        - **Reranking**: Uses LLM to reorder results by relevance
        - **Contextual Compression**: Extracts only relevant parts of retrieved chunks
        - **Conversational Memory**: Maintains context across multiple questions
        """)
    
    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=False)
