import pytest
from agentpool.search import SearchIndex
from agentpool.models import Solution, Tip


@pytest.fixture
def index(tmp_path):
    return SearchIndex(db_path=tmp_path / "chroma")


@pytest.fixture
def sample_entries():
    return [
        Solution(
            id="sol-test0001",
            title="Rate limit backoff",
            problem="MCP tool calls hit rate limits",
            solution="Use exponential backoff with jitter",
            tags=["mcp", "rate-limiting"],
        ),
        Tip(
            id="tip-test0001",
            title="Qdrant batch size",
            content="Keep batch size under 50 for nomic-embed-text on 16GB RAM",
            tags=["qdrant", "performance"],
        ),
        Solution(
            id="sol-test0002",
            title="Git conflict resolution for agents",
            problem="Agents create merge conflicts when editing the same file",
            solution="Use git worktrees for isolation, one worktree per agent task",
            tags=["git", "multi-agent"],
        ),
    ]


def test_index_entries(index, sample_entries):
    index.index_entries(sample_entries)
    assert index.count() == 3


def test_search_returns_relevant_results(index, sample_entries):
    index.index_entries(sample_entries)
    results = index.search("rate limiting for MCP tools", top_k=2)
    assert len(results) <= 2
    assert results[0].id == "sol-test0001"


def test_search_empty_index(index):
    results = index.search("anything")
    assert results == []


def test_reindex_replaces_entries(index, sample_entries):
    index.index_entries(sample_entries)
    assert index.count() == 3
    index.index_entries(sample_entries[:1])
    assert index.count() == 1
