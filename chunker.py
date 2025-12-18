"""
Advanced Text Chunking Module
Implements multiple chunking strategies for optimal RAG performance.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import tiktoken

from document_loader import Document


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    source: str
    start_index: int
    end_index: int
    token_count: int
    
    def __repr__(self):
        return f"Chunk(id='{self.chunk_id}', tokens={self.token_count})"


class TextChunker:
    """
    Advanced text chunking with multiple strategies.
    
    Strategies:
    1. Fixed-size chunking with overlap
    2. Semantic chunking (by paragraphs/sections)
    3. Recursive character splitting
    4. Sentence-aware chunking
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        encoding_name: str = "cl100k_base"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding(encoding_name)
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text."""
        return len(self.tokenizer.encode(text))
    
    def chunk_document(
        self,
        document: Document,
        strategy: str = "semantic"
    ) -> List[Chunk]:
        """
        Chunk a document using the specified strategy.
        
        Args:
            document: The document to chunk
            strategy: One of 'fixed', 'semantic', 'recursive', 'sentence'
        """
        if strategy == "fixed":
            return self._fixed_size_chunking(document)
        elif strategy == "semantic":
            return self._semantic_chunking(document)
        elif strategy == "recursive":
            return self._recursive_chunking(document)
        elif strategy == "sentence":
            return self._sentence_chunking(document)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    def _fixed_size_chunking(self, document: Document) -> List[Chunk]:
        """
        Fixed-size chunking with token-based overlap.
        Good for uniform processing but may split semantic units.
        """
        chunks = []
        text = document.content
        tokens = self.tokenizer.encode(text)
        
        start = 0
        chunk_idx = 0
        
        while start < len(tokens):
            # Get chunk tokens
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Create chunk object
            chunk = Chunk(
                content=chunk_text,
                metadata={
                    **document.metadata,
                    'chunk_strategy': 'fixed',
                    'chunk_index': chunk_idx
                },
                chunk_id=f"{document.source}_{chunk_idx}",
                source=document.source,
                start_index=start,
                end_index=end,
                token_count=len(chunk_tokens)
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start = end - self.chunk_overlap
            chunk_idx += 1
        
        return chunks
    
    def _semantic_chunking(self, document: Document) -> List[Chunk]:
        """
        Semantic chunking that respects document structure.
        Splits by sections, paragraphs, and natural boundaries.
        Best for structured documents like company profiles.
        """
        chunks = []
        text = document.content
        
        # Split by major sections first
        section_patterns = [
            r'\n(?=[A-Z][A-Za-z\s]+:)',  # Section headers
            r'\n(?=What|About|Board|Products|Services|Overview)',
            r'\n\n+',  # Double line breaks
        ]
        
        # Combine patterns
        combined_pattern = '|'.join(f'({p})' for p in section_patterns)
        sections = re.split(combined_pattern, text)
        sections = [s for s in sections if s and s.strip()]
        
        current_chunk = ""
        chunk_idx = 0
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if adding this section exceeds chunk size
            combined = current_chunk + "\n\n" + section if current_chunk else section
            
            if self.count_tokens(combined) <= self.chunk_size:
                current_chunk = combined
            else:
                # Save current chunk if it has content
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, document, chunk_idx, 'semantic'
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                
                # Handle oversized sections
                if self.count_tokens(section) > self.chunk_size:
                    # Split oversized section into smaller chunks
                    sub_chunks = self._split_large_section(section, document, chunk_idx)
                    chunks.extend(sub_chunks)
                    chunk_idx += len(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = section
        
        # Don't forget the last chunk
        if current_chunk:
            chunk = self._create_chunk(current_chunk, document, chunk_idx, 'semantic')
            chunks.append(chunk)
        
        return chunks
    
    def _recursive_chunking(self, document: Document) -> List[Chunk]:
        """
        Recursive character text splitting.
        Tries different separators hierarchically.
        """
        separators = ["\n\n", "\n", ". ", ", ", " ", ""]
        return self._recursive_split(
            document.content, 
            separators, 
            document, 
            0
        )
    
    def _recursive_split(
        self,
        text: str,
        separators: List[str],
        document: Document,
        chunk_idx: int
    ) -> List[Chunk]:
        """Recursively split text using separators."""
        chunks = []
        
        if not separators:
            # Base case: force split by characters
            return self._force_split(text, document, chunk_idx)
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)
        
        current_chunk = ""
        
        for split in splits:
            combined = current_chunk + separator + split if current_chunk else split
            
            if self.count_tokens(combined) <= self.chunk_size:
                current_chunk = combined
            else:
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, document, chunk_idx, 'recursive'
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                
                # If split is too large, recurse with next separator
                if self.count_tokens(split) > self.chunk_size:
                    sub_chunks = self._recursive_split(
                        split, remaining_separators, document, chunk_idx
                    )
                    chunks.extend(sub_chunks)
                    chunk_idx += len(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = split
        
        if current_chunk:
            chunk = self._create_chunk(current_chunk, document, chunk_idx, 'recursive')
            chunks.append(chunk)
        
        return chunks
    
    def _sentence_chunking(self, document: Document) -> List[Chunk]:
        """
        Sentence-aware chunking.
        Groups complete sentences together without breaking mid-sentence.
        """
        chunks = []
        text = document.content
        
        # Split into sentences
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        current_chunk = ""
        chunk_idx = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            combined = current_chunk + " " + sentence if current_chunk else sentence
            
            if self.count_tokens(combined) <= self.chunk_size:
                current_chunk = combined
            else:
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, document, chunk_idx, 'sentence'
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                
                current_chunk = sentence
        
        if current_chunk:
            chunk = self._create_chunk(current_chunk, document, chunk_idx, 'sentence')
            chunks.append(chunk)
        
        return chunks
    
    def _split_large_section(
        self,
        section: str,
        document: Document,
        start_idx: int
    ) -> List[Chunk]:
        """Split an oversized section into smaller chunks."""
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', section)
        
        current_chunk = ""
        chunk_idx = start_idx
        
        for sentence in sentences:
            combined = current_chunk + " " + sentence if current_chunk else sentence
            
            if self.count_tokens(combined) <= self.chunk_size:
                current_chunk = combined
            else:
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, document, chunk_idx, 'semantic_split'
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                current_chunk = sentence
        
        if current_chunk:
            chunk = self._create_chunk(current_chunk, document, chunk_idx, 'semantic_split')
            chunks.append(chunk)
        
        return chunks
    
    def _force_split(
        self,
        text: str,
        document: Document,
        start_idx: int
    ) -> List[Chunk]:
        """Force split text into chunks when no separator works."""
        chunks = []
        tokens = self.tokenizer.encode(text)
        
        start = 0
        chunk_idx = start_idx
        
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            chunk = self._create_chunk(chunk_text, document, chunk_idx, 'force_split')
            chunks.append(chunk)
            
            start = end
            chunk_idx += 1
        
        return chunks
    
    def _create_chunk(
        self,
        content: str,
        document: Document,
        chunk_idx: int,
        strategy: str
    ) -> Chunk:
        """Create a Chunk object with metadata."""
        return Chunk(
            content=content.strip(),
            metadata={
                **document.metadata,
                'chunk_strategy': strategy,
                'chunk_index': chunk_idx
            },
            chunk_id=f"{document.source}_{chunk_idx}",
            source=document.source,
            start_index=0,  # Simplified for now
            end_index=len(content),
            token_count=self.count_tokens(content)
        )


class ContextualChunker(TextChunker):
    """
    Advanced chunker that adds context to each chunk.
    Implements the "Contextual Retrieval" technique.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_window = 2  # Number of surrounding chunks for context
    
    def add_context_to_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Add contextual information to each chunk.
        This includes information about surrounding chunks.
        """
        enhanced_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Get surrounding context
            prev_context = ""
            next_context = ""
            
            if i > 0:
                prev_context = chunks[i-1].content[:200]
            if i < len(chunks) - 1:
                next_context = chunks[i+1].content[:200]
            
            # Create enhanced content
            enhanced_content = f"""[Context: This chunk is from {chunk.source}]
            
{chunk.content}

[Previous context: {prev_context[:100]}...]
[Next context: {next_context[:100]}...]"""
            
            # Update metadata
            enhanced_metadata = {
                **chunk.metadata,
                'has_prev_context': bool(prev_context),
                'has_next_context': bool(next_context),
                'enhanced': True
            }
            
            enhanced_chunk = Chunk(
                content=enhanced_content,
                metadata=enhanced_metadata,
                chunk_id=chunk.chunk_id,
                source=chunk.source,
                start_index=chunk.start_index,
                end_index=chunk.end_index,
                token_count=self.count_tokens(enhanced_content)
            )
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks


if __name__ == "__main__":
    from document_loader import DocumentLoader
    
    # Test chunking
    loader = DocumentLoader()
    sample_text = """
    Amazon.com, Inc. is a multinational technology giant specializing in e-commerce, 
    cloud computing, online advertising, digital streaming, and artificial intelligence.
    
    What Amazon Does:
    Amazon operates a diversified business model, primarily focused on providing a vast 
    online marketplace and cloud computing services through AWS.
    
    Board of Directors:
    The Board of Directors provides oversight and strategic guidance:
    Jeffrey P. Bezos, Andrew R. Jassy, Jamie Gorelick, Keith Alexander
    """
    
    doc = loader.load_from_text(sample_text, "amazon_test")
    
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    
    print("=== Semantic Chunking ===")
    chunks = chunker.chunk_document(doc, strategy="semantic")
    for chunk in chunks:
        print(f"{chunk.chunk_id}: {chunk.content[:50]}... ({chunk.token_count} tokens)")
    
    print("\n=== Sentence Chunking ===")
    chunks = chunker.chunk_document(doc, strategy="sentence")
    for chunk in chunks:
        print(f"{chunk.chunk_id}: {chunk.content[:50]}... ({chunk.token_count} tokens)")
