"""
Multi-Company RAG Demo
Demonstrates querying across multiple company profiles.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from rag_engine import RAGEngine
from sample_companies import SAMPLE_COMPANIES, add_sample_companies_to_rag

console = Console()


def main():
    """Demo with multiple companies."""
    console.print("\n[bold blue]🏢 Multi-Company RAG Demo[/bold blue]\n")
    
    # Initialize
    engine = RAGEngine()
    
    # Add Amazon from your docx file
    doc_path = "/Users/apple/Desktop/Agentic AI project/amazon.docx"
    if Path(doc_path).exists():
        try:
            engine.add_document(doc_path)
        except:
            # Read as text if docx parsing fails
            with open(doc_path, 'r', errors='ignore') as f:
                engine.add_text(f.read(), "Amazon Company Profile")
    
    # Add more sample companies
    console.print("[yellow]Adding sample companies...[/yellow]")
    add_sample_companies_to_rag(engine, ['Google', 'Apple', 'Microsoft', 'Meta', 'Tesla'])
    
    # Build index
    console.print("\n[yellow]Building vector index...[/yellow]")
    engine.build_index()
    
    # Cross-company queries
    console.print("\n[bold]📋 Cross-Company Queries:[/bold]\n")
    
    queries = [
        "Who are the CEOs of Amazon, Google, and Apple?",
        "Which companies focus on cloud computing?",
        "Compare the board sizes of Tesla and Meta",
        "What AI products do these tech companies offer?",
        "Which company makes electric vehicles?",
        "What streaming services do Amazon and Apple offer?",
    ]
    
    for query in queries:
        console.print(f"\n[bold cyan]Q:[/bold cyan] {query}")
        result = engine.query(query, verbose=False)
        console.print(Panel(
            Markdown(result['answer']),
            title="[green]Answer[/green]",
            border_style="green"
        ))
        # Show which sources were used
        sources_used = set(s['source'].split('/')[-1] for s in result['sources'])
        console.print(f"[dim]Sources: {', '.join(sources_used)}[/dim]")
    
    # Save
    engine.save()
    console.print("\n[green]✓ Multi-company demo complete![/green]")
    
    # Stats
    stats = engine.get_stats()
    console.print(f"\n[dim]Total documents: {stats['num_documents']}, Chunks: {stats['num_chunks']}[/dim]")


if __name__ == "__main__":
    main()
