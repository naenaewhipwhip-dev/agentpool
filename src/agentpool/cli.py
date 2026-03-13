import typer
from typing import Optional

app = typer.Typer(
    name="agentpool",
    help="Community-driven knowledge registry for AI agents. Search before you reason.",
    no_args_is_help=True,
)


@app.command()
def sync():
    """Pull the latest community knowledge from the registry."""
    from agentpool.sync import sync_repo, load_all_entries
    from rich import print as rprint
    rprint("[bold]Syncing AgentPool registry...[/bold]")
    try:
        repo_dir = sync_repo()
        entries = load_all_entries(repo_dir)
        rprint(f"[green]✓[/green] Registry synced to {repo_dir}")
        rprint(f"[dim]{len(entries)} entries available[/dim]")
    except Exception as e:
        rprint(f"[red]✗ Sync failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="What to search for"),
    limit: int = typer.Option(5, "--limit", "-n", help="Max results"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Filter by tag (comma-separated)"),
):
    """Search the knowledge registry for solutions and tips."""
    from agentpool.sync import get_data_dir, load_all_entries
    from agentpool.search import SearchIndex
    from agentpool.models import Solution
    from rich import print as rprint

    repo_dir = get_data_dir() / "repo"
    if not repo_dir.exists():
        rprint("[red]Registry not synced yet. Run: agentpool sync[/red]")
        raise typer.Exit(1)

    entries = load_all_entries(repo_dir)
    if not entries:
        rprint("[yellow]No entries in registry. Run: agentpool sync[/yellow]")
        return

    index = SearchIndex()
    index.index_entries(entries)
    results = index.search(query, top_k=limit)

    if not results:
        rprint("[yellow]No results found.[/yellow]")
        return

    for r in results:
        rprint(f"\n[bold cyan]{r.title}[/bold cyan] ({r.id})")
        if isinstance(r, Solution):
            rprint(f"[dim]Problem:[/dim] {r.problem[:200]}")
            rprint(f"[green]Solution:[/green] {r.solution[:200]}")
        else:
            rprint(f"[green]{r.content[:200]}[/green]")
        if r.tags:
            rprint(f"[dim]Tags: {', '.join(r.tags)}[/dim]")


@app.command()
def contribute():
    """Interactively create a new knowledge entry to contribute."""
    typer.echo("not implemented yet")


@app.command()
def vote(
    entry_id: str = typer.Argument(..., help="ID of the entry to vote on"),
    down: bool = typer.Option(False, "--down", help="Downvote instead of upvote"),
):
    """Vote on a knowledge entry."""
    typer.echo("not implemented yet")


if __name__ == "__main__":
    app()
