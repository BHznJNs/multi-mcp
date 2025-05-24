import os

from contextlib import AsyncExitStack
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from loguru import logger

from .client_config import ClientConfig


class ClientManager:
    def __init__(self, encoding: str):
        self._encoding = encoding
        self._stack = AsyncExitStack()
        self._clients: dict[str, ClientSession] = {}

    async def create_clients(self, client_configs: list[ClientConfig]):
        await self._stack.__aenter__() # manually enter the stack once

        for config in client_configs:
            name = config.name
            params = config.params
            try:
                if type(params) is ClientConfig.StdioParams:
                    logger.info(f"Creating stdio client for {name}")
                    merged_env = os.environ.copy()
                    merged_env.update(params.env)

                    read, write = await self._stack.enter_async_context(
                        stdio_client(StdioServerParameters(
                            command=params.command,
                            args=params.args,
                            env=merged_env,
                            encoding=self._encoding,
                        )))
                    session = await self._stack.enter_async_context(ClientSession(read, write))
                elif type(params) is ClientConfig.SseParams:
                    logger.info(f"Creating SSE client for {name}")
                    read, write = await self._stack.enter_async_context(
                        sse_client(
                            url=params.url,
                            headers=params.headers,
                        ))
                    session = await self._stack.enter_async_context(ClientSession(read, write))
                else: raise Exception("Unreachable")
                self._clients[name] = session
            except Exception as e:
                logger.error(f"Failed to create client for {name}: {e}")

    def get_client(self, name: str) -> ClientSession | None:
        return self._clients.get(name)

    async def close(self) -> None:
        await self._stack.aclose()
