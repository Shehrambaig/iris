#!/usr/bin/env python3
"""
Auto-load all documents from the documents folder
"""
from pathlib import Path
from rag_engine import RAGEngine
from rich.console import Console

console = Console()

def main():
    console.print("\n[bold blue]🏢 Auto-Loading Documents[/bold blue]\n")
    
    # Initialize RAG engine
    engine = RAGEngine()
    
    # Get all documents
    docs_dir = Path("documents")
    
    if not docs_dir.exists():
        console.print("[red]✗ documents/ folder not found[/red]")
        return
    
    # Find all document files
    doc_files = list(docs_dir.glob("*.docx")) + list(docs_dir.glob("*.pdf")) + list(docs_dir.glob("*.txt"))
    
    if not doc_files:
        console.print("[yellow]⚠ No documents found in documents/ folder[/yellow]")
        return
    
    console.print(f"[cyan]Found {len(doc_files)} documents[/cyan]\n")
    
    # Load each document
    loaded = 0
    failed = 0
    
    for doc_file in doc_files:
        try:
            console.print(f"[yellow]Loading {doc_file.name}...[/yellow]")
            result = engine.add_document(str(doc_file))
            console.print(f"[green]✓ Loaded {doc_file.name} - {result['num_chunks']} chunks[/green]")
            loaded += 1
        except Exception as e:
            console.print(f"[red]✗ Failed to load {doc_file.name}: {str(e)}[/red]")
            # Try loading as plain text
            try:
                console.print(f"[yellow]  Trying as plain text...[/yellow]")
                with open(doc_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                result = engine.add_text(content, doc_file.name)
                console.print(f"[green]✓ Loaded as text - {result['num_chunks']} chunks[/green]")
                loaded += 1
            except Exception as e2:
                console.print(f"[red]✗ Complete failure: {str(e2)}[/red]")
                failed += 1
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  ✓ Loaded: {loaded}")
    console.print(f"  ✗ Failed: {failed}")
    
    if loaded > 0:
        console.print("\n[yellow]Building vector index...[/yellow]")
        engine.build_index()
        console.print("[green]✓ Index built successfully![/green]")
        
        # Save the engine
        console.print("\n[yellow]Saving RAG engine...[/yellow]")
        engine.save()
        console.print("[green]✓ Engine saved![/green]")
        
        # Show stats
        stats = engine.get_stats()
        console.print(f"\n[bold cyan]Statistics:[/bold cyan]")
        console.print(f"  Documents: {stats['num_documents']}")
        console.print(f"  Chunks: {stats['num_chunks']}")
        console.print(f"  Vectors: {stats['vector_store_size']}")
        
        console.print("\n[green]✓ All done! You can now run:[/green]")
        console.print("  [bold]python cli.py[/bold] - then use 'load' command")
        console.print("  or use 'query <your question>' to ask questions")
    
if __name__ == "__main__":
    main()
