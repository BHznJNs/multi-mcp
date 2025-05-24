from mcp import ServerSession, types
from mcp.server import Server
from pydantic import AnyUrl
from ..lifespan import lifespan_factory

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

ServerSession._received_request = _received_request
####################################################################################


def proxy_server_factory(mcp_config_path: str, encoding: str):
    server = Server("one-mcp", lifespan=lifespan_factory(mcp_config_path, encoding))

    @server.list_prompts()
    async def _handle_list_prompts() -> list[types.Prompt]:
        # TODO
        # ctx = server.request_context
        return []

    @server.get_prompt()
    async def _handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        # TODO
        return types.GetPromptResult()

    @server.list_resources()
    async def _handle_list_resources() -> list[types.Resource]:
        # TODO
        return []

    @server.read_resource()
    async def _handle_read_resource(uri: AnyUrl) -> str:
        # TODO
        return ""

    @server.list_resource_templates()
    async def _handle_list_resource_templates() -> list[types.ResourceTemplate]:
        # TODO
        return []

    @server.list_tools()
    async def _handle_list_tools() -> list[types.Tool]:
        # TODO
        return []

    @server.call_tool()
    async def _handle_tool_call(
        name: str,
        arguments: dict[str, str] | None,
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        # TODO
        return []

    return server
