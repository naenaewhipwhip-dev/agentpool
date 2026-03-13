"""
AgentPool MCP Server — exposes community knowledge search as MCP tools.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

logger = logging.getLogger("agentpool-mcp")

_index = None
_entry_count = 0
_last_sync: Optional[str] = None


def _init_index(data_dir: Path | None = None):
    """Sync repo and build search index."""
    global _index, _entry_count, _last_sync
    from agentpool.sync import sync_repo, load_all_entries, get_data_dir
    from agentpool.search import SearchIndex

    try:
        repo_dir = sync_repo()
    except Exception:
        repo_dir = (data_dir or get_data_dir()) / "repo"
        if not repo_dir.exists():
            logger.warning("No local repo and sync failed — index will be empty")
            return

    entries = load_all_entries(repo_dir)
    db_path = (data_dir or get_data_dir()) / "chroma"
    _index = SearchIndex(db_path=db_path)
    _index.index_entries(entries)
    _entry_count = len(entries)
    _last_sync = datetime.now(timezone.utc).isoformat()
    logger.info(f"Indexed {_entry_count} entries")


def create_mcp_server(auto_sync: bool = True) -> FastMCP:
    """Create and return the FastMCP server instance."""
    mcp = FastMCP("agentpool")

    if auto_sync:
        _init_index()

    @mcp.tool()
    def agentpool_search(query: str, top_k: int = 5) -> str:
        """Search the AgentPool community knowledge registry for solutions, tips, and patterns.
        Use this BEFORE solving a problem to check if a known solution exists.
        Returns matching entries with titles, problems, solutions, and tags."""
        if _index is None or _index.count() == 0:
            return "Index is empty. Run agentpool_sync first."

        from agentpool.models import Solution
        results = _index.search(query, top_k=top_k)
        if not results:
            return "No matching entries found."

        lines = []
        for r in results:
            lines.append(f"### {r.title} ({r.id})")
            if isinstance(r, Solution):
                lines.append(f"**Problem:** {r.problem}")
                lines.append(f"**Solution:** {r.solution}")
            else:
                lines.append(r.content)
            if r.tags:
                lines.append(f"Tags: {', '.join(r.tags)}")
            lines.append("")
        return "\n".join(lines)

    @mcp.tool()
    def agentpool_sync() -> str:
        """Pull latest entries from the AgentPool registry and re-index."""
        try:
            _init_index()
            return f"Synced and indexed {_entry_count} entries."
        except Exception as e:
            return f"Sync failed: {e}"

    @mcp.tool()
    def agentpool_stats() -> str:
        """Show AgentPool registry statistics."""
        count = _index.count() if _index else 0
        return (
            f"Entries indexed: {count}\n"
            f"Last sync: {_last_sync or 'never'}\n"
            f"Status: {'ready' if count > 0 else 'empty — run agentpool_sync'}"
        )

    return mcp


def build_app(mcp: FastMCP):
    """Build ASGI app with /health route + MCP endpoint at /mcp.

    Uses a raw ASGI middleware class to intercept /health before Starlette
    routing, which is necessary because FastMCP's internal middleware
    stack can intercept requests before the outer router in some deployment
    environments (e.g., launchd on macOS with uvloop).
    """
    import json

    base_app = mcp.http_app(path="/mcp")

    class HealthMiddleware:
        """ASGI middleware that intercepts GET /health and forwards the rest."""

        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            logger.info("HealthMiddleware called: scope type=%s path=%s", scope.get("type"), scope.get("path"))
            if scope["type"] == "http" and scope.get("path") == "/health":
                count = _index.count() if _index else 0
                body = json.dumps({
                    "status": "ok" if count > 0 else "degraded",
                    "entries": count,
                    "last_sync": _last_sync,
                }).encode()
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"content-length", str(len(body)).encode()],
                    ],
                })
                await send({
                    "type": "http.response.body",
                    "body": body,
                })
            else:
                await self.app(scope, receive, send)

    return HealthMiddleware(base_app)
