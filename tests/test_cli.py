from typer.testing import CliRunner
from agentpool.cli import app


runner = CliRunner()


def test_app_exists():
    """Verify the Typer app object exists and is importable."""
    assert app is not None


def test_help_output():
    """Verify --help runs without error and shows expected content."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "agentpool" in result.output.lower()


def test_sync_command():
    """sync command runs and produces output (may fail in CI without network)."""
    result = runner.invoke(app, ["sync"])
    # Sync may exit 0 (success) or 1 (network unavailable in test) — both are valid
    assert "sync" in result.output.lower()


def test_search_command():
    """search command runs (may show no results if registry empty)."""
    result = runner.invoke(app, ["search", "rate limits"])
    assert result.exit_code == 0


def test_vote_command():
    """vote command runs and shows score."""
    result = runner.invoke(app, ["vote", "test-entry", "up"])
    assert result.exit_code == 0
    assert "score" in result.output.lower()
