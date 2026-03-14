"""Allow running as: python -m agentpool"""
from agentpool.server import create_mcp_server, build_app
import uvicorn

server = create_mcp_server(auto_sync=True)
app = build_app(server)
uvicorn.run(app, host="0.0.0.0", port=9886, log_level="info", lifespan="on")
