"""
Simple Langfuse Tracer - Use REST API directly
Add this to your RAG code to send traces
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from base64 import b64encode


class SimpleLangfuseTracer:
    """Simple tracer that sends data directly to Langfuse REST API"""

    def __init__(self):
        self.host = "http://localhost:3000"
        self.secret_key = "sk-lf-4087f44f-b41b-45fe-980c-66522b90445e"
        self.public_key = "pk-lf-9f6ed26f-9ae0-427e-96f1-0f1e2983776e"

        # Create auth header
        auth_string = f"{self.public_key}:{self.secret_key}"
        auth_bytes = auth_string.encode('ascii')
        base64_bytes = b64encode(auth_bytes)
        self.auth_header = f"Basic {base64_bytes.decode('ascii')}"

    def create_trace(self, name: str, input_data: Any, output_data: Any = None,
                     metadata: Dict = None) -> bool:
        """Create a trace in Langfuse"""

        trace_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        payload = {
            "id": trace_id,
            "name": name,
            "input": input_data,
            "output": output_data,
            "metadata": metadata or {},
            "timestamp": timestamp
        }

        try:
            response = requests.post(
                f"{self.host}/api/public/traces",
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code in [200, 201]:
                print(f"✅ Trace sent: {trace_id}")
                return True
            else:
                print(f"❌ Failed to send trace: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error sending trace: {e}")
            return False

    def create_generation(self, trace_id: str, name: str, input_data: Any,
                          output_data: Any, metadata: Dict = None) -> bool:
        """Create a generation (LLM call) within a trace"""

        generation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        payload = {
            "id": generation_id,
            "traceId": trace_id,
            "name": name,
            "input": input_data,
            "output": output_data,
            "metadata": metadata or {},
            "startTime": timestamp,
            "endTime": timestamp
        }

        try:
            response = requests.post(
                f"{self.host}/api/public/generations",
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code in [200, 201]:
                return True
            else:
                print(f"❌ Failed to send generation: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error sending generation: {e}")
            return False


# Global tracer instance
tracer = SimpleLangfuseTracer()


# ============================================
# SIMPLE WRAPPER FUNCTIONS
# ============================================

def trace_query(question: str, answer: str, sources: list = None,
                metadata: dict = None):
    """Simple function to trace a RAG query"""

    input_data = {
        "question": question,
        "timestamp": datetime.now().isoformat()
    }

    output_data = {
        "answer": answer,
        "num_sources": len(sources) if sources else 0
    }

    if sources:
        output_data["sources"] = [
            {"source": s.get("source", "unknown"), "score": s.get("score", 0)}
            for s in sources[:5]  # First 5 sources only
        ]

    full_metadata = metadata or {}
    full_metadata["interface"] = "gradio"

    tracer.create_trace(
        name="rag-query",
        input_data=input_data,
        output_data=output_data,
        metadata=full_metadata
    )


def trace_chat(message: str, response: str, conversation_length: int = 0):
    """Simple function to trace a chat interaction"""

    tracer.create_trace(
        name="rag-chat",
        input_data={
            "message": message,
            "conversation_length": conversation_length
        },
        output_data={
            "response": response
        },
        metadata={
            "interface": "gradio-chat"
        }
    )


# ============================================
# INTEGRATION EXAMPLE
# ============================================

def example_integration():
    """
    Example: How to add tracing to your existing query function

    BEFORE:
    def query_rag(question, use_hybrid, use_reranking, top_k):
        result = rag_engine.query(question, top_k=top_k, ...)
        return result['answer'], format_sources(result['sources'])

    AFTER:
    def query_rag(question, use_hybrid, use_reranking, top_k):
        result = rag_engine.query(question, top_k=top_k, ...)

        # Add this line to send trace
        trace_query(question, result['answer'], result['sources'],
                   {"use_hybrid": use_hybrid, "use_reranking": use_reranking})

        return result['answer'], format_sources(result['sources'])
    """

    # Example usage
    question = "Who are the board members?"
    answer = "The board members are John, Jane, and Bob."
    sources = [
        {"source": "doc1.pdf", "score": 0.95},
        {"source": "doc2.pdf", "score": 0.87}
    ]

    trace_query(question, answer, sources, {"model": "gpt-4"})
    print("✅ Example trace sent!")


if __name__ == "__main__":
    # Test the tracer
    print("Testing Langfuse tracer...")
    example_integration()