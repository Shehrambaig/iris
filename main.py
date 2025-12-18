"""
Company RAG System - Main Entry Point
Demonstrates the full RAG pipeline with your Amazon document.
"""
import os
import sys
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from rag_engine import RAGEngine
from document_loader import CompanyDataLoader

console = Console()


def main():
    """
    Main function demonstrating the RAG system with your Amazon document.
    """
    console.print("\n[bold blue]🏢 Company Information RAG System[/bold blue]\n")
    
    # Initialize RAG engine
    console.print("[yellow]Initializing RAG Engine...[/yellow]")
    engine = RAGEngine()
    
    # Path to your document
    doc_path = "/Users/apple/Desktop/Agentic AI project/amazon.docx"
    
    # Check if document exists
    if not Path(doc_path).exists():
        console.print(f"[red]Document not found: {doc_path}[/red]")
        console.print("[yellow]Please make sure the file exists or add documents manually.[/yellow]")
        return
    
    # Add the document
    console.print(f"\n[yellow]Loading document: {doc_path}[/yellow]")
    try:
        result = engine.add_document(doc_path)
        console.print(f"[green]✓ Document loaded successfully![/green]")
        console.print(f"  - Chunks created: {result['num_chunks']}")
        console.print(f"  - Company: {result['company_info'].get('company_name', 'N/A')}")
    except Exception as e:
        console.print(f"[red]Error loading document: {e}[/red]")
        # Try reading as text directly
        try:
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            result = engine.add_text(content, "amazon.docx")
            console.print(f"[green]✓ Loaded as text: {result['num_chunks']} chunks[/green]")
        except Exception as e2:
            console.print(f"[red]Error: {e2}[/red]")
            return
    
    # Build the index
    console.print("\n[yellow]Building vector index...[/yellow]")
    engine.build_index()
    console.print("[green]✓ Index built successfully![/green]")
    
    # Example queries
    console.print("\n[bold]📋 Demo Queries:[/bold]\n")
    
    demo_queries = [
        "What does Amazon do?",
        "Who are the board members of Amazon?",
        "What is AWS and what services does it provide?",
        "Who is the CEO of Amazon?",
        "What subscription services does Amazon offer?",
        "What products does Amazon sell under its own brands?"
    ]
    
    for i, query in enumerate(demo_queries, 1):
        console.print(f"\n[bold cyan]Question {i}:[/bold cyan] {query}")
        console.print("-" * 60)
        
        result = engine.query(query, verbose=False)
        
        # Print answer
        console.print(Panel(
            Markdown(result['answer']),
            title="[green]Answer[/green]",
            border_style="green"
        ))
        
        # Print sources
        console.print("[dim]Sources used:[/dim]")
        for source in result['sources'][:2]:
            score = f"{source['score']:.3f}" if isinstance(source['score'], float) else source['score']
            console.print(f"  [dim]• {source['source'].split('/')[-1]} (score: {score})[/dim]")
    
    # Save the engine
    console.print("\n[yellow]Saving RAG engine...[/yellow]")
    engine.save()
    
    # Print stats
    console.print("\n[bold]📊 Final Statistics:[/bold]")
    stats = engine.get_stats()
    for key, value in stats.items():
        console.print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    console.print("\n[green]✓ Demo complete![/green]")
    console.print("\n[bold]To start interactive mode, run:[/bold]")
    console.print("  python cli.py    # Command-line interface")
    console.print("  python app.py    # Web interface (requires gradio)")


if __name__ == "__main__":
    main()
