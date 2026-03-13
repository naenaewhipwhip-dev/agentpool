"""End-to-end test: load entries from disk, index, search."""
from pathlib import Path
from agentpool.sync import load_all_entries
from agentpool.search import SearchIndex


def test_full_pipeline(tmp_path):
    repo_root = Path(__file__).parent.parent
    entries = load_all_entries(repo_root)
    assert len(entries) > 0, "No seed entries found"

    index = SearchIndex(db_path=tmp_path / "chroma")
    index.index_entries(entries)
    assert index.count() == len(entries)

    results = index.search("rate limiting")
    assert len(results) > 0
    assert any(
        "rate" in r.title.lower() or "rate" in getattr(r, "problem", "").lower()
        for r in results
    )


def test_search_different_queries(tmp_path):
    repo_root = Path(__file__).parent.parent
    entries = load_all_entries(repo_root)
    index = SearchIndex(db_path=tmp_path / "chroma")
    index.index_entries(entries)

    # Search for git-related entries
    git_results = index.search("git worktree isolation")
    assert len(git_results) > 0

    # Search for MCP entries
    mcp_results = index.search("MCP server health")
    assert len(mcp_results) > 0

    # Search for vector DB entries
    vec_results = index.search("vector database deduplication")
    assert len(vec_results) > 0
