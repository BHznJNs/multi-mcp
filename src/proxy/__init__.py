import asyncio
from loguru import logger
from mcp import ServerSession, types
from mcp.server import Server
from pydantic import AnyUrl

from .resource import handle_list_resource_templates, handle_list_resources, handle_read_resource, handle_subscribe_resource, handle_unsubscribe_resource
from .tool import handle_list_tools, handle_call_tool
from .prompt import handle_get_prompt, handle_list_prompts
from .utils import use_client_manager, use_client_session, use_namespace


####################################################################################
# Temporary monkeypatch which avoids crashing when a POST message is received
# before a connection has been initialized, e.g: after a deployment.
# This patch is from: https://github.com/modelcontextprotocol/python-sdk/issues/423#issuecomment-2799890581
# And it makes the python-sdk version 1.9.1 works

old__received_request = ServerSession._received_request

async def _received_request(self, *args, **kwargs):
    try:
        return await old__received_request(self, *args, **kwargs)
    except RuntimeError:
        # triggered: Received request before initialization was complete
        pass

ServerSession._received_request = _received_request # type: ignore
####################################################################################


def proxy_server_factory():
    server = Server("one-mcp")

    @server.list_prompts()
    async def _handle_list_prompts() -> list[types.Prompt]:
        return await handle_list_prompts()

    @server.get_prompt()
    async def _handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        return await handle_get_prompt(name, arguments)

    @server.list_resources()
    async def _handle_list_resources() -> list[types.Resource]:
        return await handle_list_resources()

    @server.read_resource()
    async def _handle_read_resource(uri: AnyUrl) -> str | bytes:
        return await handle_read_resource(uri)

    @server.list_resource_templates()
    async def _handle_list_resource_templates() -> list[types.ResourceTemplate]:
        return await handle_list_resource_templates()

    @server.subscribe_resource()
    async def _handle_subscribe_resource(url: AnyUrl):
        return await handle_subscribe_resource(url)

    @server.unsubscribe_resource()
    async def _handle_unsubscribe_resource(url: AnyUrl):
        return await handle_unsubscribe_resource(url)

    @server.list_tools()
    async def _handle_list_tools() -> list[types.Tool]:
        return await handle_list_tools()

    @server.call_tool()
    async def _handle_call_tool(
        name: str,
        arguments: dict[str, str] | None,
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        return await handle_call_tool(name, arguments)

    @server.completion()
    async def _handle_completion(
        ref: types.PromptReference | types.ResourceReference,
        argument: types.CompletionArgument,
    ) -> types.Completion | None:
        client_manager = use_client_manager()
        tasks = map(lambda session: session.complete(ref, {argument.name: argument.value}),
                    client_manager.client_sessions)
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in task_results:
            if isinstance(result, types.Completion):
                return result
        return None

    @server.progress_notification()
    async def _handle_progress_notification(
        progressToken: str | int,
        progress: float,
        total: float | None,
        message: str | None = None
    ):
        namespace = use_namespace()
        if namespace is not None:
            client = use_client_session(namespace)
            if client is None:
                logger.warning("No client found for name: {}", namespace)
                return
            await client.send_progress_notification(progressToken, progress, total, message)
            return

        client_manager = use_client_manager()
        tasks = map(lambda session: session.send_progress_notification(progressToken, progress, total, message),
                    client_manager.client_sessions)
        await asyncio.gather(*tasks, return_exceptions=True)

    @server.set_logging_level()
    async def _handle_set_logging_level(logging_level: types.LoggingLevel):
        namespace = use_namespace()
        if namespace is not None:
            client = use_client_session(namespace)
            if client is None:
                logger.warning("No client found for name: {}", namespace)
                return
            await client.set_logging_level(logging_level)
            return

        client_manager = use_client_manager()
        tasks = map(lambda client: client.set_logging_level(logging_level), client_manager.client_sessions)
        await asyncio.gather(*tasks)

    return server
