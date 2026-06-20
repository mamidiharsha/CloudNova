"""
CloudNova Support Agent - Command-Line Interface
Interactive chatbot with rich terminal output.

Usage:
    python cli.py
"""

import json
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from src.agents.workflow import SupportAgent
from src.models.schemas import PersonaType

console = Console()

# Persona colors
PERSONA_COLORS = {
    PersonaType.TECHNICAL_EXPERT: "blue",
    PersonaType.FRUSTRATED_USER: "red",
    PersonaType.BUSINESS_EXECUTIVE: "magenta",
}

PERSONA_ICONS = {
    PersonaType.TECHNICAL_EXPERT: "🔧",
    PersonaType.FRUSTRATED_USER: "😤",
    PersonaType.BUSINESS_EXECUTIVE: "💼",
}


def print_welcome():
    """Print the welcome banner."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]CloudNova Support Agent[/bold cyan]\n"
            "[dim]Persona-Adaptive AI Customer Support[/dim]\n\n"
            "Type your question or issue below.\n"
            "Commands: [bold]/quit[/bold] · [bold]/reset[/bold] · [bold]/export[/bold]",
            title="☁️  Welcome",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()


def print_response(response):
    """Print the agent's response with all metadata."""
    persona = response.persona
    retrieval = response.retrieval
    escalation = response.escalation

    color = PERSONA_COLORS.get(persona.persona, "white")
    icon = PERSONA_ICONS.get(persona.persona, "🤖")

    # Persona badge
    console.print()
    persona_text = Text()
    persona_text.append(f" {icon} Persona: ", style="bold")
    persona_text.append(f"{persona.persona.value}", style=f"bold {color}")
    persona_text.append(f"  (confidence: {persona.confidence:.0%})", style="dim")
    persona_text.append(f"  │  Sentiment: ", style="bold")
    persona_text.append(f"{persona.sentiment.value}", style="italic")
    console.print(persona_text)

    # Retrieved sources
    if retrieval.documents:
        sources_table = Table(
            title="📚 Retrieved Sources",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold cyan",
            title_style="bold",
            padding=(0, 1),
        )
        sources_table.add_column("#", style="dim", width=3)
        sources_table.add_column("Source", style="cyan")
        sources_table.add_column("Section", style="dim")
        sources_table.add_column("Score", justify="right", style="green")

        seen_sources = set()
        for i, doc in enumerate(retrieval.documents[:5], 1):
            source_key = f"{doc.source}:{doc.section}"
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                score_color = "green" if doc.similarity_score > 0.5 else "yellow" if doc.similarity_score > 0.3 else "red"
                sources_table.add_row(
                    str(i),
                    doc.source,
                    (doc.section or "")[:40],
                    f"[{score_color}]{doc.similarity_score:.3f}[/{score_color}]",
                )
        console.print(sources_table)

    # Response
    console.print(
        Panel(
            Markdown(response.response_text),
            title="💬 Response",
            border_style=color,
            padding=(1, 2),
        )
    )

    # Escalation
    if escalation.should_escalate:
        console.print(
            Panel(
                f"[bold red]🚨 ESCALATED TO HUMAN AGENT[/bold red]\n\n"
                f"Reasons: {escalation.details}",
                title="⚠️  Escalation",
                border_style="red",
                padding=(1, 2),
            )
        )

        if response.handoff_summary:
            hs = response.handoff_summary
            handoff_text = (
                f"[bold]Escalation ID:[/bold] {hs.escalation_id}\n"
                f"[bold]Priority:[/bold] {hs.priority}\n"
                f"[bold]Issue:[/bold] {hs.issue_summary}\n"
                f"[bold]Documents Used:[/bold] {', '.join(hs.documents_used)}\n"
                f"[bold]Attempted Steps:[/bold] {', '.join(hs.attempted_steps)}\n"
                f"[bold]Next Steps:[/bold] {', '.join(hs.recommended_next_steps)}"
            )
            console.print(
                Panel(
                    handoff_text,
                    title="📋 Handoff Summary",
                    border_style="yellow",
                    padding=(1, 2),
                )
            )

    console.print(f"[dim]Turn #{response.turn_number} • Session: {response.session_id}[/dim]")
    console.print()


def main():
    """Run the CLI chatbot."""
    print_welcome()

    try:
        agent = SupportAgent()
    except Exception as e:
        console.print(f"[red]Error initializing agent: {e}[/red]")
        console.print("[yellow]Make sure you've run 'python ingest.py' first and set GOOGLE_API_KEY in .env[/yellow]")
        sys.exit(1)

    session_id = agent.create_session()
    console.print(f"[dim]Session started: {session_id}[/dim]\n")

    last_response = None

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye! 👋[/dim]")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.lower() == "/quit":
            console.print("[dim]Goodbye! 👋[/dim]")
            break

        if user_input.lower() == "/reset":
            session_id = agent.create_session()
            console.print(f"[cyan]New session started: {session_id}[/cyan]\n")
            continue

        if user_input.lower() == "/export":
            if last_response and last_response.handoff_summary:
                export_data = last_response.handoff_summary.model_dump()
                filename = f"handoff_{last_response.handoff_summary.escalation_id}.json"
                with open(filename, "w") as f:
                    json.dump(export_data, f, indent=2)
                console.print(f"[green]Exported handoff summary to {filename}[/green]\n")
            else:
                console.print("[yellow]No handoff summary to export.[/yellow]\n")
            continue

        # Process the message
        with console.status("[bold cyan]Thinking...", spinner="dots"):
            try:
                response = agent.process_message(user_input, session_id)
                last_response = response
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]\n")
                continue

        print_response(response)


if __name__ == "__main__":
    main()
