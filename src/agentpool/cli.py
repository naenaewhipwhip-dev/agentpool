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
    from pathlib import Path
    from agentpool.contribute import create_entry_file
    from agentpool.sync import get_data_dir
    from rich import print as rprint
    from rich.prompt import Prompt, Confirm
    import subprocess
    import shutil

    rprint("[bold]Create a new AgentPool entry[/bold]\n")

    entry_type = Prompt.ask("Entry type", choices=["solution", "tip"], default="solution")
    title = Prompt.ask("Title")
    tags_str = Prompt.ask("Tags (comma-separated)", default="")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

    if entry_type == "solution":
        problem = Prompt.ask("Problem (what goes wrong?)")
        solution = Prompt.ask("Solution (what works?)")
        kwargs = {"problem": problem, "solution": solution}
    else:
        content = Prompt.ask("Tip content")
        kwargs = {"content": content}

    repo_dir = get_data_dir() / "repo"
    if not repo_dir.exists():
        rprint("[yellow]Registry not synced. Saving to current directory.[/yellow]")
        repo_dir = Path(".")

    path = create_entry_file(
        output_dir=repo_dir,
        entry_type=entry_type,
        title=title,
        tags=tags,
        **kwargs,
    )

    rprint(f"\n[green]✓[/green] Entry created: {path}")
    rprint(f"[dim]To submit, create a PR with this file at github.com/naenaewhipwhip-dev/agentpool[/dim]")

    # Offer gh CLI PR creation if available
    if shutil.which("gh"):
        if Confirm.ask("Create a GitHub PR automatically?", default=False):
            try:
                branch = f"contribute/{path.stem}"
                subprocess.run(["git", "-C", str(repo_dir), "checkout", "-b", branch], check=True, capture_output=True)
                subprocess.run(["git", "-C", str(repo_dir), "add", str(path)], check=True, capture_output=True)
                subprocess.run(["git", "-C", str(repo_dir), "commit", "-m", f"feat: add {title}"], check=True, capture_output=True)
                subprocess.run(["git", "-C", str(repo_dir), "push", "-u", "origin", branch], check=True, capture_output=True)
                result = subprocess.run(
                    ["gh", "pr", "create", "--repo", "naenaewhipwhip-dev/agentpool",
                     "--title", f"Add: {title}", "--body", f"New {entry_type} entry: {title}"],
                    check=True, capture_output=True, text=True
                )
                rprint(f"[green]✓[/green] PR created: {result.stdout.strip()}")
            except Exception as e:
                rprint(f"[red]PR creation failed: {e}[/red]")
                rprint("[dim]You can still submit manually.[/dim]")


@app.command()
def vote(
    entry_id: str = typer.Argument(..., help="ID of the entry to vote on"),
    down: bool = typer.Option(False, "--down", help="Downvote instead of upvote"),
):
    """Vote on a knowledge entry."""
    typer.echo("not implemented yet")


if __name__ == "__main__":
    app()
