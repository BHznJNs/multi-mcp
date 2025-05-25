from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from loguru import logger
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from .client import ClientManager

def sse_lifespan_factory(client_manager: ClientManager):
    @asynccontextmanager
    async def sse_lifespan(_) -> AsyncIterator[dict]:
        logger.info("SSE server lifespan started")
        await client_manager.init_clients()
        try:
            yield {"client_manager": client_manager}
        finally:
            await client_manager.close()
            logger.info("SSE server lifespan ended")
    return sse_lifespan

def streamable_lifespan_factory(
    client_manager: ClientManager,
    session_manager: StreamableHTTPSessionManager,
):
    @asynccontextmanager
    async def lifespan(_) -> AsyncIterator[dict]:
        logger.info("Streamable HTTP server lifespan starting")
        async with session_manager.run():
            logger.info("Streamable HTTP server lifespan started")
            await client_manager.init_clients()
            try:
                yield {"client_manager": client_manager}
            finally:
                await client_manager.close()
                logger.info("Streamable HTTP server lifespan ended")
    return lifespan
