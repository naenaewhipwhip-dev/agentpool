"""Allow running as: python -m agentpool.server"""
from agentpool.server import create_mcp_server, build_app
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentpool-main")

server = create_mcp_server(auto_sync=True)
app = build_app(server)
logger.info("App type: %s", type(app).__name__)
uvicorn.run(app, host="0.0.0.0", port=9886, log_level="info", lifespan="on")
