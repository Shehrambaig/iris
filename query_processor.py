"""
Query Processing Module
Implements query expansion, reranking, and contextual compression.
"""
from typing import List, Tuple, Optional
from dataclasses import dataclass
import re

from openai import OpenAI
from config import (
    OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE,
    NUM_EXPANDED_QUERIES, RERANK_TOP_K
)
from chunker import Chunk


@dataclass
class QueryResult:
    """Represents a processed query result."""
    chunk: Chunk
    score: float
    rerank_score: Optional[float] = None
    compressed_content: Optional[str] = None


class QueryExpander:
    """
    Expands queries to improve retrieval coverage.
    
    Techniques:
    1. Synonym expansion
    2. Query decomposition (breaking complex queries)
    3. Hypothetical document generation
    """
    
    def __init__(self, api_key: str = OPENAI_API_KEY):
        self.client = OpenAI(api_key=api_key)
    
    def expand_query(self, query: str, num_expansions: int = NUM_EXPANDED_QUERIES) -> List[str]:
        """
        Generate multiple query variations for better retrieval.
        """
        prompt = f"""Generate {num_expansions} alternative phrasings of the following query.
Each variation should:
1. Capture the same intent but use different words
2. Include synonyms and related terms
3. Consider different ways a user might ask the same question

Original query: {query}

Return ONLY the alternative queries, one per line, without numbering or explanations."""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        
        expansions = response.choices[0].message.content.strip().split('\n')
        expansions = [q.strip() for q in expansions if q.strip()]
        
        # Always include the original query
        return [query] + expansions[:num_expansions]
    
    def decompose_query(self, query: str) -> List[str]:
        """
        Break down complex queries into simpler sub-queries.
        Useful for multi-hop questions.
        """
        prompt = f"""Analyze this query and break it down into simpler sub-queries if needed.
If the query is already simple, return it as is.

Query: {query}

Return the sub-queries, one per line, without numbering."""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        sub_queries = response.choices[0].message.content.strip().split('\n')
        return [q.strip() for q in sub_queries if q.strip()]
    
    def generate_hypothetical_answer(self, query: str) -> str:
        """
        Generate a hypothetical answer to the query.
        This is used for HyDE (Hypothetical Document Embeddings).
        """
        prompt = f"""Generate a brief, factual answer to this query as if you had perfect knowledge.
This will be used to find relevant documents, so include key terms and concepts.

Query: {query}

Provide a concise, informative answer (2-3 sentences):"""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()


class Reranker:
    """
    Reranks retrieved results using LLM-based relevance scoring.
    
    This provides more accurate ranking than pure embedding similarity.
    """
    
    def __init__(self, api_key: str = OPENAI_API_KEY):
        self.client = OpenAI(api_key=api_key)
    
    def rerank(
        self,
        query: str,
        results: List[Tuple[Chunk, float]],
        top_k: int = RERANK_TOP_K
    ) -> List[QueryResult]:
        """
        Rerank results using LLM-based relevance scoring.
        """
        if not results:
            return []
        
        reranked = []
        
        for chunk, original_score in results:
            # Score relevance using LLM
            relevance_score = self._score_relevance(query, chunk.content)
            
            reranked.append(QueryResult(
                chunk=chunk,
                score=original_score,
                rerank_score=relevance_score
            ))
        
        # Sort by rerank score
        reranked.sort(key=lambda x: x.rerank_score or 0, reverse=True)
        
        return reranked[:top_k]
    
    def _score_relevance(self, query: str, content: str) -> float:
        """Score the relevance of content to a query."""
        prompt = f"""Rate the relevance of the following passage to the query on a scale of 0-10.
Consider:
- Does it directly answer the question?
- Does it contain relevant information?
- Is the information accurate and complete?

Query: {query}

Passage: {content[:1000]}

Return ONLY a number from 0-10:"""

        try:
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=10
            )
            
            score_text = response.choices[0].message.content.strip()
            # Extract number from response
            numbers = re.findall(r'\d+\.?\d*', score_text)
            if numbers:
                score = float(numbers[0])
                return min(score / 10.0, 1.0)  # Normalize to [0, 1]
        except Exception as e:
            print(f"Error scoring relevance: {e}")
        
        return 0.5  # Default score if parsing fails
    
    def batch_rerank(
        self,
        query: str,
        results: List[Tuple[Chunk, float]],
        top_k: int = RERANK_TOP_K
    ) -> List[QueryResult]:
        """
        More efficient batch reranking using a single LLM call.
        """
        if not results:
            return []
        
        # Create numbered list of passages
        passages_text = "\n\n".join([
            f"[{i+1}] {chunk.content[:500]}"
            for i, (chunk, _) in enumerate(results[:10])  # Limit to top 10
        ])
        
        prompt = f"""Given the query and passages below, rank the passages by relevance.
Return the passage numbers in order of relevance (most relevant first).

Query: {query}

Passages:
{passages_text}

Return ONLY the passage numbers separated by commas (e.g., "3, 1, 5, 2, 4"):"""

        try:
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=50
            )
            
            # Parse ranking
            ranking_text = response.choices[0].message.content.strip()
            rankings = [int(x.strip()) - 1 for x in re.findall(r'\d+', ranking_text)]
            
            # Build reranked results
            reranked = []
            for rank, idx in enumerate(rankings):
                if idx < len(results):
                    chunk, original_score = results[idx]
                    reranked.append(QueryResult(
                        chunk=chunk,
                        score=original_score,
                        rerank_score=1.0 - (rank / len(rankings))  # Higher rank = higher score
                    ))
            
            return reranked[:top_k]
            
        except Exception as e:
            print(f"Error in batch reranking: {e}")
            # Fallback to original order
            return [
                QueryResult(chunk=chunk, score=score, rerank_score=score)
                for chunk, score in results[:top_k]
            ]


class ContextualCompressor:
    """
    Compresses retrieved context to focus on relevant information.
    Removes irrelevant parts of chunks to improve answer quality.
    """
    
    def __init__(self, api_key: str = OPENAI_API_KEY):
        self.client = OpenAI(api_key=api_key)
    
    def compress(self, query: str, results: List[QueryResult]) -> List[QueryResult]:
        """
        Compress each result to only include relevant information.
        """
        compressed_results = []
        
        for result in results:
            compressed_content = self._compress_content(query, result.chunk.content)
            
            compressed_result = QueryResult(
                chunk=result.chunk,
                score=result.score,
                rerank_score=result.rerank_score,
                compressed_content=compressed_content
            )
            compressed_results.append(compressed_result)
        
        return compressed_results
    
    def _compress_content(self, query: str, content: str) -> str:
        """Extract only the relevant parts of content for the query."""
        prompt = f"""Extract only the parts of the following text that are relevant to answering the query.
Remove any irrelevant information while preserving the meaning and context of relevant parts.

Query: {query}

Text: {content}

Relevant extract (preserve exact wording where possible):"""

        try:
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error compressing content: {e}")
            return content  # Return original if compression fails


class QueryProcessor:
    """
    Main query processing pipeline combining all techniques.
    """
    
    def __init__(self, api_key: str = OPENAI_API_KEY):
        self.expander = QueryExpander(api_key)
        self.reranker = Reranker(api_key)
        self.compressor = ContextualCompressor(api_key)
    
    def process_query(
        self,
        query: str,
        expand: bool = True,
        use_hyde: bool = False
    ) -> dict:
        """
        Process a query with optional expansion and HyDE.
        
        Returns a dictionary with:
        - original_query: The original query
        - expanded_queries: List of expanded queries (if enabled)
        - hypothetical_answer: HyDE answer (if enabled)
        """
        result = {
            'original_query': query,
            'expanded_queries': [query],
            'hypothetical_answer': None
        }
        
        if expand:
            result['expanded_queries'] = self.expander.expand_query(query)
        
        if use_hyde:
            result['hypothetical_answer'] = self.expander.generate_hypothetical_answer(query)
        
        return result
    
    def process_results(
        self,
        query: str,
        results: List[Tuple[Chunk, float]],
        rerank: bool = True,
        compress: bool = True,
        top_k: int = RERANK_TOP_K
    ) -> List[QueryResult]:
        """
        Process retrieved results with reranking and compression.
        """
        # Convert to QueryResult
        query_results = [
            QueryResult(chunk=chunk, score=score)
            for chunk, score in results
        ]
        
        if rerank:
            query_results = self.reranker.batch_rerank(query, results, top_k=top_k)
        
        if compress:
            query_results = self.compressor.compress(query, query_results[:top_k])
        
        return query_results


if __name__ == "__main__":
    # Test query processing
    processor = QueryProcessor()
    
    # Test query expansion
    query = "Who are the board members of Amazon?"
    processed = processor.process_query(query, expand=True, use_hyde=True)
    
    print("Original query:", processed['original_query'])
    print("\nExpanded queries:")
    for q in processed['expanded_queries']:
        print(f"  - {q}")
    print("\nHypothetical answer:", processed['hypothetical_answer'])
