import asyncio
from loguru import logger
from mcp import types

from .utils import use_client_manager, use_client_session, use_namespace, use_settings, with_namespace, without_namespace


async def handle_list_tools() -> list[types.Tool]:
    logger.info("Handling list tools request")
    namespace = use_namespace()

    if namespace is not None:
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        list_tools_result = await client.list_tools()
        return list_tools_result.tools

    client_manager = use_client_manager()
    settings = use_settings()
    tasks = map(lambda client: client.list_tools(), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    result_tools = []
    for name, result in zip(client_manager.client_names, task_results):
        if isinstance(result, BaseException):
            logger.warning("Unexpected result from list_prompts for server: {}", name)
            continue
        if settings.use_namespace:
            for tool in result.tools:
                tool.name = with_namespace(name, tool.name)
                result_tools.append(tool)
        else:
            result_tools.extend(result.tools)

    return result_tools

async def handle_call_tool(
    name: str,
    arguments: dict[str, str] | None,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    logger.info("Handling call tool request for tool '{}'", name)
    namespace = use_namespace()

    if namespace is not None:
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        call_tool_result = await client.call_tool(name, arguments)
        return call_tool_result.content

    settings = use_settings()
    if settings.use_namespace:
        namespace, tool_name = without_namespace(name)
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        call_tool_result = await client.call_tool(tool_name, arguments)
        return call_tool_result.content

    client_manager = use_client_manager()
    tasks = map(lambda client: client.list_tools(), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    for client_name, result in zip(client_manager.client_names, task_results):
        if isinstance(result, BaseException): continue
        # try to find the tool in the result
        filtered = filter(lambda tool: tool.name == name, result.tools)
        optional_tool = next(filtered, None)
        if optional_tool is None: continue

        # if found, call it on the corresponding client
        target_client = client_manager.get_client(client_name)
        assert target_client is not None # since the name is from the list of client_names, it should not be None
        call_tool_result = await target_client.call_tool(name, arguments)
        return call_tool_result.content

    logger.warning("No tool named '{}' found", name)
    raise ValueError(f"No tool named '{name}' found")
