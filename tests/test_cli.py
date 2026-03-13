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


def test_sync_not_implemented():
    """sync command runs and prints not-implemented message."""
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0
    assert "not implemented yet" in result.output


def test_search_not_implemented():
    """search command runs and prints not-implemented message."""
    result = runner.invoke(app, ["search", "rate limits"])
    assert result.exit_code == 0
    assert "not implemented yet" in result.output


def test_contribute_not_implemented():
    """contribute command runs and prints not-implemented message."""
    result = runner.invoke(app, ["contribute"])
    assert result.exit_code == 0
    assert "not implemented yet" in result.output


def test_vote_not_implemented():
    """vote command runs and prints not-implemented message."""
    result = runner.invoke(app, ["vote", "some-entry-id"])
    assert result.exit_code == 0
    assert "not implemented yet" in result.output
