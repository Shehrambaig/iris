"""
Document Loader Module
Handles loading various document formats (DOCX, PDF, TXT, etc.)
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import re

@dataclass
class Document:
    """Represents a loaded document with content and metadata."""
    content: str
    metadata: Dict[str, Any]
    source: str
    
    def __repr__(self):
        return f"Document(source='{self.source}', length={len(self.content)})"


class DocumentLoader:
    """
    Universal document loader supporting multiple file formats.
    Supports: .docx, .pdf, .txt, .md
    """
    
    def __init__(self):
        self.supported_extensions = {'.docx', '.pdf', '.txt', '.md'}
    
    def load_docx(self, file_path: str) -> str:
        """Load content from a DOCX file."""
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(file_path)
            full_text = []
            for paragraph in doc.paragraphs:
                full_text.append(paragraph.text)
            return '\n'.join(full_text)
        except ImportError:
            # Fallback: try to read as text (some docx files are readable)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    
    def load_pdf(self, file_path: str) -> str:
        """Load content from a PDF file."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = []
            for page in reader.pages:
                text.append(page.extract_text())
            return '\n'.join(text)
        except ImportError:
            raise ImportError("pypdf is required for PDF support. Install with: pip install pypdf")
    
    def load_text(self, file_path: str) -> str:
        """Load content from a text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_file(self, file_path: str) -> Document:
        """Load a single file and return a Document object."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = path.suffix.lower()
        
        # Load content based on file type
        if extension == '.docx':
            content = self.load_docx(file_path)
        elif extension == '.pdf':
            content = self.load_pdf(file_path)
        elif extension in {'.txt', '.md'}:
            content = self.load_text(file_path)
        else:
            # Try to read as text
            content = self.load_text(file_path)
        
        # Clean the content
        content = self._clean_content(content)
        
        # Extract metadata
        metadata = {
            'filename': path.name,
            'extension': extension,
            'file_size': path.stat().st_size,
            'word_count': len(content.split()),
            'char_count': len(content)
        }
        
        return Document(content=content, metadata=metadata, source=str(path))
    
    def load_directory(self, directory_path: str) -> List[Document]:
        """Load all supported documents from a directory."""
        documents = []
        path = Path(directory_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        for file_path in path.rglob('*'):
            if file_path.suffix.lower() in self.supported_extensions:
                try:
                    doc = self.load_file(str(file_path))
                    documents.append(doc)
                    print(f"✓ Loaded: {file_path.name}")
                except Exception as e:
                    print(f"✗ Failed to load {file_path.name}: {e}")
        
        return documents
    
    def load_from_text(self, text: str, source_name: str = "direct_input") -> Document:
        """Create a Document from raw text input."""
        content = self._clean_content(text)
        metadata = {
            'filename': source_name,
            'extension': '.txt',
            'word_count': len(content.split()),
            'char_count': len(content)
        }
        return Document(content=content, metadata=metadata, source=source_name)
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize document content."""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        # Remove special characters that might cause issues
        content = content.replace('\x00', '')
        # Normalize line breaks
        content = re.sub(r'[\r\n]+', '\n', content)
        # Strip leading/trailing whitespace
        content = content.strip()
        return content


class CompanyDataLoader(DocumentLoader):
    """
    Specialized loader for company data documents.
    Extracts structured information about companies.
    """
    
    def extract_company_info(self, document: Document) -> Dict[str, Any]:
        """
        Extract structured company information from a document.
        Returns a dictionary with company details.
        """
        content = document.content
        
        # Try to extract company name (usually at the beginning)
        company_name = self._extract_company_name(content)
        
        # Try to extract board members
        board_members = self._extract_board_members(content)
        
        # Try to extract what the company does
        business_description = self._extract_business_description(content)
        
        return {
            'company_name': company_name,
            'board_members': board_members,
            'business_description': business_description,
            'source': document.source
        }
    
    def _extract_company_name(self, content: str) -> str:
        """Extract company name from content."""
        # Look for patterns like "Company Name, Inc." or "Company Name Corporation"
        patterns = [
            r'^([A-Z][A-Za-z\s]+(?:Inc\.|Corporation|Corp\.|LLC|Ltd\.|Company))',
            r'^([A-Z][A-Za-z\s]+) is a',
            r'^About ([A-Z][A-Za-z\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        # Return first line as fallback
        first_line = content.split('\n')[0][:100]
        return first_line
    
    def _extract_board_members(self, content: str) -> List[str]:
        """Extract board members from content."""
        members = []
        
        # Look for sections about board members
        board_section_patterns = [
            r'Board of Directors[:\s]*(.*?)(?=\n\n|Executive|$)',
            r'Board Members[:\s]*(.*?)(?=\n\n|$)',
            r'Directors[:\s]*(.*?)(?=\n\n|$)'
        ]
        
        for pattern in board_section_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                section = match.group(1)
                # Extract names (capitalized words)
                names = re.findall(r'([A-Z][a-z]+ [A-Z]\.? [A-Z][a-z]+|[A-Z][a-z]+ [A-Z][a-z]+)', section)
                members.extend(names)
        
        return list(set(members))  # Remove duplicates
    
    def _extract_business_description(self, content: str) -> str:
        """Extract business description from content."""
        # Look for sections about what the company does
        patterns = [
            r'What .+ Does[:\s]*(.*?)(?=Board|Directors|$)',
            r'About[:\s]*(.*?)(?=Board|Directors|Products|$)',
            r'Overview[:\s]*(.*?)(?=Board|Directors|Products|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:1000]  # Limit length
        
        return content[:500]  # Return first 500 chars as fallback


if __name__ == "__main__":
    # Test the document loader
    loader = CompanyDataLoader()
    
    # Test with a sample document
    sample_text = """
    Amazon.com, Inc. is a multinational technology company.
    
    What Amazon Does:
    Amazon operates e-commerce and cloud computing services.
    
    Board of Directors:
    Jeff Bezos
    Andy Jassy
    Keith Alexander
    """
    
    doc = loader.load_from_text(sample_text, "amazon_test")
    print(f"Loaded document: {doc}")
    
    info = loader.extract_company_info(doc)
    print(f"Extracted info: {info}")
