# AgentPool MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the AgentPool CLI — a community knowledge registry for AI agents where users sync, search locally, and contribute Problem+Solution pairs and Tips.

**Architecture:** Git repo as central registry of YAML knowledge entries. Python CLI tool syncs entries locally, embeds with sentence-transformers, stores in ChromaDB (in-process, no server), searches semantically. Contributions generate YAML files and optionally create GitHub PRs via `gh` CLI.

**Tech Stack:** Python 3.11+, Typer (CLI), ChromaDB (local vector DB), sentence-transformers (embeddings), PyYAML, Pydantic (validation), pytest

**Design doc:** `~/workspace-v5/docs/plans/2026-03-13-agentpool-design.md`

---

## Task 1: Repo Scaffold & Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `LICENSE`
- Create: `CONTRIBUTING.md`
- Create: `.gitignore`
- Create: `src/agentpool/__init__.py`
- Create: `src/agentpool/cli.py`
- Create: `tests/__init__.py`
- Create: `tests/test_cli.py`
- Create: `entries/solutions/.gitkeep`
- Create: `entries/tips/.gitkeep`
- Create: `schema/solution.json`
- Create: `schema/tip.json`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agentpool"
version = "0.1.0"
description = "Community-driven knowledge registry for AI agents. Search before you reason."
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "chromadb>=0.5",
    "sentence-transformers>=3.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-tmp-files>=0.0.2",
]

[project.scripts]
agentpool = "agentpool.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/agentpool"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 2: Create .gitignore**

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.venv/
.agentpool/
*.db
```

**Step 3: Create LICENSE (MIT)**

Standard MIT license, copyright 2026 AgentPool Contributors.

**Step 4: Create empty package files**

- `src/agentpool/__init__.py` — `__version__ = "0.1.0"`
- `src/agentpool/cli.py` — Typer app skeleton with placeholder commands
- `tests/__init__.py` — empty
- `entries/solutions/.gitkeep` — empty
- `entries/tips/.gitkeep` — empty

**Step 5: Create README.md**

Short README with:
- One-liner description
- Install instructions (`pip install agentpool`)
- Quick usage (sync, search, contribute)
- Link to CONTRIBUTING.md
- Architecture diagram (from design doc)

**Step 6: Create CONTRIBUTING.md**

How to submit knowledge:
- Entry format (YAML schema for solutions and tips)
- How to use `agentpool contribute`
- How to submit a PR manually
- Quality guidelines

**Step 7: Install in dev mode and verify**

Run: `cd ~/agentpool && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
Expected: `agentpool --help` prints usage

**Step 8: Commit**

```bash
git add -A
git commit -m "feat: initial repo scaffold with project structure and packaging"
```

---

## Task 2: Data Model & Validation

**Files:**
- Create: `src/agentpool/models.py`
- Create: `tests/test_models.py`
- Create: `schema/solution.json`
- Create: `schema/tip.json`

**Step 1: Write failing tests for data model**

```python
# tests/test_models.py
import pytest
from agentpool.models import Solution, Tip, generate_id, load_entry, validate_entry

def test_generate_solution_id():
    entry_id = generate_id("solution")
    assert entry_id.startswith("sol-")
    assert len(entry_id) == 12  # sol- + 8 hex chars

def test_generate_tip_id():
    entry_id = generate_id("tip")
    assert entry_id.startswith("tip-")
    assert len(entry_id) == 12

def test_solution_model_valid():
    sol = Solution(
        title="Test solution",
        problem="Something breaks",
        solution="Fix it this way",
        tags=["test"],
    )
    assert sol.type == "solution"
    assert sol.id.startswith("sol-")
    assert sol.votes == 0

def test_tip_model_valid():
    tip = Tip(
        title="Test tip",
        content="Do this thing",
        tags=["test"],
    )
    assert tip.type == "tip"
    assert tip.id.startswith("tip-")

def test_solution_to_yaml():
    sol = Solution(
        title="Test",
        problem="Problem",
        solution="Solution",
        tags=["a", "b"],
    )
    yaml_str = sol.to_yaml()
    assert "type: solution" in yaml_str
    assert "title: Test" in yaml_str
    assert "problem:" in yaml_str

def test_load_entry_solution(tmp_path):
    yaml_content = """id: sol-abcd1234
type: solution
title: Test
problem: Something breaks
solution: Fix it
tags: [test]
contributor: anon_0000
created: '2026-03-13'
votes: 0
"""
    f = tmp_path / "test.yaml"
    f.write_text(yaml_content)
    entry = load_entry(f)
    assert isinstance(entry, Solution)
    assert entry.title == "Test"

def test_validate_entry_rejects_missing_fields():
    with pytest.raises(ValueError):
        Solution(title="", problem="", solution="", tags=[])
```

**Step 2: Run tests to verify they fail**

Run: `cd ~/agentpool && source .venv/bin/activate && pytest tests/test_models.py -v`
Expected: ImportError — `agentpool.models` doesn't exist yet

**Step 3: Implement models.py**

```python
# src/agentpool/models.py
from __future__ import annotations
import uuid
from datetime import date
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, field_validator

def generate_id(entry_type: str) -> str:
    prefix = {"solution": "sol", "tip": "tip"}[entry_type]
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

class Solution(BaseModel):
    id: str = ""
    type: Literal["solution"] = "solution"
    title: str
    problem: str
    solution: str
    tags: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    contributor: str = "anonymous"
    created: str = Field(default_factory=lambda: str(date.today()))
    votes: int = 0

    def model_post_init(self, __context):
        if not self.id:
            self.id = generate_id("solution")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("title cannot be empty")
        return v

    @field_validator("problem")
    @classmethod
    def problem_not_empty(cls, v):
        if not v.strip():
            raise ValueError("problem cannot be empty")
        return v

    @field_validator("solution")
    @classmethod
    def solution_not_empty(cls, v):
        if not v.strip():
            raise ValueError("solution cannot be empty")
        return v

    def to_yaml(self) -> str:
        return yaml.dump(self.model_dump(), default_flow_style=False, sort_keys=False)

class Tip(BaseModel):
    id: str = ""
    type: Literal["tip"] = "tip"
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    contributor: str = "anonymous"
    created: str = Field(default_factory=lambda: str(date.today()))
    votes: int = 0

    def model_post_init(self, __context):
        if not self.id:
            self.id = generate_id("tip")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("title cannot be empty")
        return v

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("content cannot be empty")
        return v

    def to_yaml(self) -> str:
        return yaml.dump(self.model_dump(), default_flow_style=False, sort_keys=False)

def load_entry(path: Path) -> Solution | Tip:
    data = yaml.safe_load(path.read_text())
    if data["type"] == "solution":
        return Solution(**data)
    elif data["type"] == "tip":
        return Tip(**data)
    raise ValueError(f"Unknown entry type: {data.get('type')}")

def validate_entry(data: dict) -> Solution | Tip:
    entry_type = data.get("type", "solution")
    if entry_type == "solution":
        return Solution(**data)
    elif entry_type == "tip":
        return Tip(**data)
    raise ValueError(f"Unknown entry type: {entry_type}")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: All pass

**Step 5: Create JSON schemas for validation in CI**

Create `schema/solution.json` and `schema/tip.json` — JSON Schema definitions matching the Pydantic models. Used by GitHub Actions to validate PR submissions.

**Step 6: Commit**

```bash
git add src/agentpool/models.py tests/test_models.py schema/
git commit -m "feat: data model with Solution and Tip types, YAML serialization, validation"
```

---

## Task 3: Sync Command

**Files:**
- Create: `src/agentpool/sync.py`
- Create: `tests/test_sync.py`
- Modify: `src/agentpool/cli.py`

**Step 1: Write failing tests**

```python
# tests/test_sync.py
import pytest
from pathlib import Path
from agentpool.sync import get_data_dir, sync_repo, load_all_entries

def test_get_data_dir():
    d = get_data_dir()
    assert d == Path.home() / ".agentpool"

def test_sync_repo_clones_on_first_run(tmp_path, monkeypatch):
    monkeypatch.setattr("agentpool.sync.get_data_dir", lambda: tmp_path)
    # This test requires network — mark as integration test
    # For unit test, mock subprocess
    pass

def test_load_all_entries(tmp_path):
    solutions_dir = tmp_path / "entries" / "solutions"
    solutions_dir.mkdir(parents=True)
    (solutions_dir / "test.yaml").write_text("""id: sol-abcd1234
type: solution
title: Test Solution
problem: A problem
solution: The fix
tags: [test]
contributor: anon_0000
created: '2026-03-13'
votes: 0
""")
    entries = load_all_entries(tmp_path)
    assert len(entries) == 1
    assert entries[0].title == "Test Solution"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_sync.py -v`
Expected: ImportError

**Step 3: Implement sync.py**

```python
# src/agentpool/sync.py
from pathlib import Path
import subprocess
from agentpool.models import load_entry, Solution, Tip

REPO_URL = "https://github.com/naenaewhipwhip-dev/agentpool.git"

def get_data_dir() -> Path:
    return Path.home() / ".agentpool"

def sync_repo() -> Path:
    data_dir = get_data_dir()
    repo_dir = data_dir / "repo"
    if (repo_dir / ".git").exists():
        subprocess.run(["git", "-C", str(repo_dir), "pull", "--ff-only"],
                       check=True, capture_output=True)
    else:
        data_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", REPO_URL, str(repo_dir)],
                       check=True, capture_output=True)
    return repo_dir

def load_all_entries(repo_dir: Path) -> list[Solution | Tip]:
    entries = []
    entries_dir = repo_dir / "entries"
    if not entries_dir.exists():
        return entries
    for yaml_file in sorted(entries_dir.rglob("*.yaml")):
        try:
            entries.append(load_entry(yaml_file))
        except Exception:
            continue  # skip malformed entries
    return entries
```

**Step 4: Wire sync command into CLI**

```python
# In src/agentpool/cli.py
@app.command()
def sync():
    """Sync the knowledge registry to your local machine."""
    from agentpool.sync import sync_repo
    from rich import print as rprint
    rprint("[bold]Syncing AgentPool registry...[/bold]")
    repo_dir = sync_repo()
    rprint(f"[green]✓[/green] Registry synced to {repo_dir}")
```

**Step 5: Run tests**

Run: `pytest tests/test_sync.py -v`
Expected: Pass

**Step 6: Commit**

```bash
git add src/agentpool/sync.py src/agentpool/cli.py tests/test_sync.py
git commit -m "feat: sync command — clones/pulls registry locally"
```

---

## Task 4: Search Command (Local Embeddings + ChromaDB)

**Files:**
- Create: `src/agentpool/search.py`
- Create: `tests/test_search.py`
- Modify: `src/agentpool/cli.py`

**Step 1: Write failing tests**

```python
# tests/test_search.py
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_search.py -v`
Expected: ImportError

**Step 3: Implement search.py**

```python
# src/agentpool/search.py
from __future__ import annotations
from pathlib import Path
from agentpool.models import Solution, Tip

import chromadb

def _entry_to_text(entry: Solution | Tip) -> str:
    if isinstance(entry, Solution):
        return f"{entry.title}\n{entry.problem}\n{entry.solution}"
    return f"{entry.title}\n{entry.content}"

class SearchIndex:
    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = Path.home() / ".agentpool" / "chroma"
        db_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(db_path))
        self._collection = self._client.get_or_create_collection(
            name="agentpool",
            metadata={"hnsw:space": "cosine"},
        )

    def index_entries(self, entries: list[Solution | Tip]) -> None:
        # Clear and reindex
        self._client.delete_collection("agentpool")
        self._collection = self._client.create_collection(
            name="agentpool",
            metadata={"hnsw:space": "cosine"},
        )
        if not entries:
            return
        self._collection.add(
            ids=[e.id for e in entries],
            documents=[_entry_to_text(e) for e in entries],
            metadatas=[{"type": e.type, "title": e.title, "tags": ",".join(e.tags)} for e in entries],
        )

    def search(self, query: str, top_k: int = 5) -> list[Solution | Tip]:
        if self.count() == 0:
            return []
        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, self.count()),
        )
        # Reconstruct entries from metadata + documents
        # For MVP, return lightweight result objects
        entries = []
        for i, entry_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            doc = results["documents"][0][i]
            distance = results["distances"][0][i] if results.get("distances") else None
            if meta["type"] == "solution":
                parts = doc.split("\n", 2)
                entries.append(Solution(
                    id=entry_id,
                    title=meta["title"],
                    problem=parts[1] if len(parts) > 1 else "",
                    solution=parts[2] if len(parts) > 2 else "",
                    tags=meta["tags"].split(",") if meta["tags"] else [],
                ))
            else:
                parts = doc.split("\n", 1)
                entries.append(Tip(
                    id=entry_id,
                    title=meta["title"],
                    content=parts[1] if len(parts) > 1 else "",
                    tags=meta["tags"].split(",") if meta["tags"] else [],
                ))
        return entries

    def count(self) -> int:
        return self._collection.count()
```

Note: ChromaDB uses its own default embedding function (all-MiniLM-L6-v2 via sentence-transformers) when no embedding function is specified. This is perfect for MVP — zero config, decent quality.

**Step 4: Wire search command into CLI**

```python
@app.command()
def search(query: str, top_k: int = 5):
    """Search the local knowledge registry."""
    from agentpool.sync import get_data_dir, load_all_entries
    from agentpool.search import SearchIndex
    from rich import print as rprint
    from rich.table import Table

    repo_dir = get_data_dir() / "repo"
    if not repo_dir.exists():
        rprint("[red]Registry not synced yet. Run: agentpool sync[/red]")
        raise typer.Exit(1)

    entries = load_all_entries(repo_dir)
    index = SearchIndex()
    index.index_entries(entries)
    results = index.search(query, top_k=top_k)

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
```

**Step 5: Run tests**

Run: `pytest tests/test_search.py -v`
Expected: All pass (ChromaDB downloads all-MiniLM-L6-v2 on first run)

**Step 6: Commit**

```bash
git add src/agentpool/search.py tests/test_search.py src/agentpool/cli.py
git commit -m "feat: search command — local embeddings + ChromaDB vector search"
```

---

## Task 5: Contribute Command

**Files:**
- Create: `src/agentpool/contribute.py`
- Create: `tests/test_contribute.py`
- Modify: `src/agentpool/cli.py`

**Step 1: Write failing tests**

```python
# tests/test_contribute.py
import pytest
from pathlib import Path
from agentpool.contribute import create_entry_file, slugify

def test_slugify():
    assert slugify("Rate Limit Backoff!") == "rate-limit-backoff"
    assert slugify("Qdrant batch_size tip") == "qdrant-batch-size-tip"

def test_create_solution_file(tmp_path):
    path = create_entry_file(
        output_dir=tmp_path,
        entry_type="solution",
        title="Test Solution",
        problem="Something breaks",
        solution="Fix it this way",
        tags=["test", "demo"],
    )
    assert path.exists()
    assert path.suffix == ".yaml"
    assert "solutions" in str(path)
    content = path.read_text()
    assert "type: solution" in content
    assert "Test Solution" in content

def test_create_tip_file(tmp_path):
    path = create_entry_file(
        output_dir=tmp_path,
        entry_type="tip",
        title="Quick Tip",
        content="Do this thing",
        tags=["test"],
    )
    assert path.exists()
    assert "tips" in str(path)
    content = path.read_text()
    assert "type: tip" in content
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_contribute.py -v`
Expected: ImportError

**Step 3: Implement contribute.py**

```python
# src/agentpool/contribute.py
from __future__ import annotations
import re
from pathlib import Path
from agentpool.models import Solution, Tip

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")

def create_entry_file(
    output_dir: Path,
    entry_type: str,
    title: str,
    tags: list[str] | None = None,
    problem: str = "",
    solution: str = "",
    content: str = "",
) -> Path:
    tags = tags or []
    slug = slugify(title)

    if entry_type == "solution":
        entry = Solution(title=title, problem=problem, solution=solution, tags=tags)
        subdir = output_dir / "entries" / "solutions"
    else:
        entry = Tip(title=title, content=content, tags=tags)
        subdir = output_dir / "entries" / "tips"

    subdir.mkdir(parents=True, exist_ok=True)
    path = subdir / f"{slug}.yaml"
    path.write_text(entry.to_yaml())
    return path
```

**Step 4: Wire contribute command into CLI**

Interactive command using `typer.prompt()` and `rich`:
- Ask for entry type (solution or tip)
- Ask for title, problem/solution or content, tags
- Generate YAML file in the local repo clone
- Print the file path
- If `gh` CLI is available, offer to fork + create PR automatically

**Step 5: Run tests**

Run: `pytest tests/test_contribute.py -v`
Expected: All pass

**Step 6: Commit**

```bash
git add src/agentpool/contribute.py tests/test_contribute.py src/agentpool/cli.py
git commit -m "feat: contribute command — interactive entry creation with YAML output"
```

---

## Task 6: Vote Command

**Files:**
- Create: `src/agentpool/vote.py`
- Create: `tests/test_vote.py`
- Modify: `src/agentpool/cli.py`

**Step 1: Write failing tests**

```python
# tests/test_vote.py
import pytest
import yaml
from pathlib import Path
from agentpool.vote import cast_vote, load_votes, get_entry_votes

def test_cast_upvote(tmp_path):
    votes_file = tmp_path / "votes.yaml"
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0001")
    votes = load_votes(votes_file)
    assert "sol-abcd1234" in votes
    assert votes["sol-abcd1234"]["score"] == 1

def test_cast_downvote(tmp_path):
    votes_file = tmp_path / "votes.yaml"
    cast_vote(votes_file, "sol-abcd1234", "down", voter="anon_0001")
    votes = load_votes(votes_file)
    assert votes["sol-abcd1234"]["score"] == -1

def test_voter_can_only_vote_once(tmp_path):
    votes_file = tmp_path / "votes.yaml"
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0001")
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0001")
    votes = load_votes(votes_file)
    assert votes["sol-abcd1234"]["score"] == 1  # not 2

def test_get_entry_votes(tmp_path):
    votes_file = tmp_path / "votes.yaml"
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0001")
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0002")
    cast_vote(votes_file, "sol-abcd1234", "down", voter="anon_0003")
    score = get_entry_votes(votes_file, "sol-abcd1234")
    assert score == 1
```

**Step 2: Run tests to verify they fail**

**Step 3: Implement vote.py**

Votes stored in `metadata/votes.yaml` in the local repo. Structure:

```yaml
sol-abcd1234:
  score: 1
  voters:
    anon_0001: up
    anon_0002: up
    anon_0003: down
```

For MVP, votes are local only. Future: submit votes via PR or API.

**Step 4: Wire vote command into CLI**

**Step 5: Run tests, verify pass**

**Step 6: Commit**

```bash
git add src/agentpool/vote.py tests/test_vote.py src/agentpool/cli.py
git commit -m "feat: vote command — local upvote/downvote tracking"
```

---

## Task 7: GitHub Actions Curator Gate

**Files:**
- Create: `.github/workflows/validate.yaml`
- Create: `.github/workflows/curator.yaml`
- Create: `scripts/validate_entry.py`

**Step 1: Create YAML validation workflow**

`.github/workflows/validate.yaml` — runs on every PR:
- Checks that new/modified YAML files in `entries/` are valid
- Validates against Pydantic models (runs `scripts/validate_entry.py`)
- Fails the PR if validation errors

**Step 2: Create validate_entry.py script**

```python
#!/usr/bin/env python3
"""Validate YAML entries against the AgentPool schema."""
import sys
from pathlib import Path
import yaml
from agentpool.models import validate_entry

errors = []
for path in Path("entries").rglob("*.yaml"):
    try:
        data = yaml.safe_load(path.read_text())
        validate_entry(data)
    except Exception as e:
        errors.append(f"{path}: {e}")

if errors:
    for e in errors:
        print(f"❌ {e}", file=sys.stderr)
    sys.exit(1)
print(f"✓ All entries valid")
```

**Step 3: Create AI curator workflow (stretch goal)**

`.github/workflows/curator.yaml` — runs on PRs adding new entries:
- Sends entry content to a free LLM (Gemini Flash via API)
- Scores for quality, novelty, safety
- Posts review comment on the PR
- Does NOT auto-merge — just advisory

This is a stretch goal for MVP. The validation workflow is the priority.

**Step 4: Commit**

```bash
git add .github/ scripts/
git commit -m "ci: YAML validation on PRs, curator gate scaffold"
```

---

## Task 8: Seed Initial Entries

**Files:**
- Create: 10-20 YAML files in `entries/solutions/` and `entries/tips/`

**Step 1: Write seed entries from real agent knowledge**

Draw from Zach's experience running Madge, Claude Code, OpenClaw, k3s, etc. Focus on framework-agnostic, non-private knowledge. Examples:

Solutions:
- Rate limiting backoff for MCP tools
- Agent worktree isolation pattern
- LiteLLM fallback chain configuration
- Prompt strategy for multi-step tool chains
- Vector DB dedup with content hashing

Tips:
- ChromaDB default embedding model (all-MiniLM-L6-v2)
- Qdrant batch size limits
- Git commit email privacy
- YAML multiline strings (| vs >)
- MCP server health check pattern

**Step 2: Validate all entries**

Run: `python scripts/validate_entry.py`
Expected: All valid

**Step 3: Commit**

```bash
git add entries/
git commit -m "feat: seed initial knowledge entries (10-20 entries)"
```

---

## Task 9: End-to-End Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

```python
# tests/test_integration.py
"""End-to-end test: load entries from disk, index, search."""
import pytest
from pathlib import Path
from agentpool.sync import load_all_entries
from agentpool.search import SearchIndex

def test_full_pipeline(tmp_path):
    # Use the actual repo entries/ directory
    repo_root = Path(__file__).parent.parent
    entries = load_all_entries(repo_root)
    assert len(entries) > 0, "No seed entries found"

    index = SearchIndex(db_path=tmp_path / "chroma")
    index.index_entries(entries)
    assert index.count() == len(entries)

    results = index.search("rate limiting")
    assert len(results) > 0
    # First result should be relevant to rate limiting
    assert any("rate" in r.title.lower() or "rate" in getattr(r, 'problem', '').lower()
               for r in results)
```

**Step 2: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

**Step 3: Push to GitHub**

```bash
git push origin main
```

**Step 4: Verify GitHub Actions run on push**

Check: https://github.com/naenaewhipwhip-dev/agentpool/actions
Expected: Validation workflow passes

**Step 5: Final commit if any fixes needed**

---

## Summary

| Task | What | Est. Complexity |
|------|------|----------------|
| 1 | Repo scaffold & packaging | Low |
| 2 | Data model (Pydantic + YAML) | Low |
| 3 | Sync command (git clone/pull) | Low |
| 4 | Search command (ChromaDB + embeddings) | Medium |
| 5 | Contribute command (interactive YAML creation) | Medium |
| 6 | Vote command (local votes) | Low |
| 7 | GitHub Actions (validation + curator) | Medium |
| 8 | Seed initial entries | Low |
| 9 | Integration test + push | Low |

**After MVP is complete, next steps from the roadmap:**
- v0.2: MCP server wrapper (so agents can query AgentPool directly as an MCP tool)
- Gems export pipeline (staging branch curation)
- Community launch (HN, Reddit, Discord)
