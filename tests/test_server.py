import asyncio
import pytest
from agentpool.server import create_mcp_server


def test_create_mcp_server_returns_fastmcp():
    from fastmcp import FastMCP
    server = create_mcp_server(auto_sync=False)
    assert isinstance(server, FastMCP)


def test_search_tool_exists():
    server = create_mcp_server(auto_sync=False)
    tool_names = [t.name for t in asyncio.run(server.list_tools())]
    assert "agentpool_search" in tool_names


def test_sync_tool_exists():
    server = create_mcp_server(auto_sync=False)
    tool_names = [t.name for t in asyncio.run(server.list_tools())]
    assert "agentpool_sync" in tool_names


def test_stats_tool_exists():
    server = create_mcp_server(auto_sync=False)
    tool_names = [t.name for t in asyncio.run(server.list_tools())]
    assert "agentpool_stats" in tool_names
