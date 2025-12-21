"""
Simple Command-Line Interface for the Company RAG System
Use this if Gradio is not installed or you prefer CLI.
"""
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
import sys

from rag_engine import RAGEngine
from config import OPENAI_API_KEY

console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║         🏢 Company Information RAG System 🏢              ║
    ║                                                           ║
    ║   Advanced Retrieval-Augmented Generation for Company     ║
    ║   Information, Board Members, and Business Insights       ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def print_help():
    """Print available commands."""
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("add <file>", "Add a document file (docx, pdf, txt)")
    table.add_row("add-text", "Add text directly (interactive)")
    table.add_row("build", "Build the vector index")
    table.add_row("query <question>", "Ask a question")
    table.add_row("chat", "Start interactive chat mode")
    table.add_row("stats", "Show system statistics")
    table.add_row("save", "Save the RAG engine state")
    table.add_row("load", "Load a saved RAG engine state")
    table.add_row("clear", "Clear conversation history")
    table.add_row("help", "Show this help message")
    table.add_row("quit", "Exit the application")
    
    console.print(table)


def interactive_add_text(engine: RAGEngine):
    """Interactively add text to the RAG system."""
    console.print("\n[bold]Add Text to RAG System[/bold]")
    console.print("Enter your text (press Enter twice to finish):\n")
    
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    
    text = "\n".join(lines[:-1])  # Remove last empty line
    
    if not text.strip():
        console.print("[yellow]No text entered.[/yellow]")
        return
    
    source = Prompt.ask("Source name", default="direct_input")
    
    result = engine.add_text(text, source)
    console.print(f"[green]✓ Added {result['num_chunks']} chunks from '{source}'[/green]")


def interactive_chat(engine: RAGEngine):
    """Start interactive chat mode."""
    console.print("\n[bold blue]Chat Mode[/bold blue]")
    console.print("Type your questions (type 'exit' to leave chat mode)\n")
    
    while True:
        try:
            question = Prompt.ask("[bold cyan]You[/bold cyan]")
            
            if question.lower() in ['exit', 'quit', 'q']:
                console.print("[dim]Exiting chat mode...[/dim]")
                break
            
            if not question.strip():
                continue
            
            result = engine.query(question, verbose=False)
            console.print(Panel(
                Markdown(result['answer']),
                title="[bold green]Assistant[/bold green]",
                border_style="green"
            ))
            
            # Show sources briefly
            sources = [s['source'].split('/')[-1] for s in result['sources'][:3]]
            console.print(f"[dim]Sources: {', '.join(sources)}[/dim]\n")
            
        except KeyboardInterrupt:
            console.print("\n[dim]Exiting chat mode...[/dim]")
            break


def main():
    """Main CLI entry point."""
    print_banner()
    
    # Initialize RAG engine
    console.print("[blue]Initializing RAG Engine...[/blue]")
    try:
        engine = RAGEngine()
        console.print("[green]✓ RAG Engine initialized[/green]\n")
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize: {e}[/red]")
        sys.exit(1)
    
    print_help()
    console.print()
    
    while True:
        try:
            command = Prompt.ask("\n[bold]RAG[/bold]").strip()
            
            if not command:
                continue
            
            parts = command.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd in ['quit', 'exit', 'q']:
                console.print("[dim]Goodbye![/dim]")
                break
            
            elif cmd == 'help':
                print_help()
            
            elif cmd == 'add':
                if not args:
                    console.print("[yellow]Usage: add <file_path>[/yellow]")
                else:
                    try:
                        result = engine.add_document(args)
                        console.print(f"[green]✓ Added document: {result['num_chunks']} chunks[/green]")
                    except Exception as e:
                        console.print(f"[red]✗ Error: {e}[/red]")
            
            elif cmd == 'add-text':
                interactive_add_text(engine)
            
            elif cmd == 'build':
                try:
                    engine.build_index()
                except Exception as e:
                    console.print(f"[red]✗ Error building index: {e}[/red]")
            
            elif cmd == 'query':
                if not args:
                    console.print("[yellow]Usage: query <your question>[/yellow]")
                elif not engine.is_initialized:
                    console.print("[yellow]Please build the index first (use 'build' command)[/yellow]")
                else:
                    result = engine.query(args, verbose=True)
            
            elif cmd == 'chat':
                if not engine.is_initialized:
                    console.print("[yellow]Please build the index first (use 'build' command)[/yellow]")
                else:
                    interactive_chat(engine)
            
            elif cmd == 'stats':
                stats = engine.get_stats()
                table = Table(title="RAG Engine Statistics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")
                
                for key, value in stats.items():
                    table.add_row(key.replace('_', ' ').title(), str(value))
                
                console.print(table)
            
            elif cmd == 'save':
                try:
                    engine.save()
                except Exception as e:
                    console.print(f"[red]✗ Error saving: {e}[/red]")
            
            elif cmd == 'load':
                try:
                    engine.load()
                except Exception as e:
                    console.print(f"[red]✗ Error loading: {e}[/red]")
            
            elif cmd == 'clear':
                engine.clear_history()
                console.print("[green]✓ Conversation history cleared[/green]")
            
            else:
                console.print(f"[yellow]Unknown command: {cmd}. Type 'help' for available commands.[/yellow]")
        
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'quit' to exit[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
