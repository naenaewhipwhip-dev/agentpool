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
    limit: int = typer.Option(5, "--limit", "-n", help="Number of results to return"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Filter by tag (comma-separated)"),
):
    """Search the knowledge registry for solutions and tips."""
    typer.echo("not implemented yet")


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
