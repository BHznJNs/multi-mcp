import json

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from mcp.server import Server

from .client import ClientManager, config_parser


def lifespan_factory(mcp_config_path: str, encoding: str):
    with open(mcp_config_path, "r") as f:
        mcp_config = json.load(f)

    client_configs = config_parser(mcp_config)

    @asynccontextmanager
    async def lifespan(_server: Server) -> AsyncIterator[dict]:
        client_manager = ClientManager(encoding)
        await client_manager.create_clients(client_configs)
        try:
            yield {"client_manager": client_manager}
        finally:
            await client_manager.close()
    return lifespan
