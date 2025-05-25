import os

from contextlib import AsyncExitStack
from typing import Iterable
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from loguru import logger

from .client_config import ClientConfig


class ClientManager:
    def __init__(self, encoding: str, client_configs: list[ClientConfig]):
        self._encoding = encoding
        self._client_configs = client_configs
        self._stack = AsyncExitStack()
        self._clients: dict[str, ClientSession] = {}

    async def init_clients(self, ):
        await self._stack.__aenter__() # manually enter the stack once

        for config in self._client_configs:
            name = config.name
            params = config.params

            if name in self._clients:
                logger.warning("Client '{}' already exists and will be overridden.", name)

            try:
                if type(params) is ClientConfig.StdioParams:
                    session = await self._init_stdio_client(name, params)
                elif type(params) is ClientConfig.SseParams:
                    session = await self._init_sse_client(name, params)
                else: raise Exception("Unreachable")
                await session.initialize()
                logger.info("MCP client for '{}' successfully created.", name)
            except Exception as e:
                logger.error("Failed to create client for {}: {}", name, e)
                continue
            self._clients[name] = session

    async def _init_stdio_client(self, name: str, params: ClientConfig.StdioParams) -> ClientSession:
        logger.info("Creating stdio client for '{}' with params: {}.", name, params)
        merged_env = os.environ.copy()
        merged_env.update(params.env)

        read, write = await self._stack.enter_async_context(
            stdio_client(StdioServerParameters(
                command=params.command,
                args=params.args,
                env=merged_env,
                encoding=self._encoding,
            )))
        session = await self._stack.enter_async_context(
            ClientSession(read, write))
        return session

    async def _init_sse_client(self, name: str, params: ClientConfig.SseParams) -> ClientSession:
        logger.info("Creating SSE client for '{}' with params: {}", name, params)
        read, write = await self._stack.enter_async_context(
            sse_client(
                url=params.url,
                headers=params.headers,
            ))
        session = await self._stack.enter_async_context(
            ClientSession(read, write))
        return session

    @property
    def client_names(self) -> Iterable[str]:
        return self._clients.keys()

    @property
    def client_sessions(self) -> Iterable[ClientSession]:
        return self._clients.values()

    def get_client(self, name: str) -> ClientSession | None:
        return self._clients.get(name)

    async def close(self) -> None:
        await self._stack.aclose()
