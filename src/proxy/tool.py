import asyncio
from loguru import logger
from mcp import types

from .utils import use_client_manager


async def handle_list_tools() -> list[types.Tool]:
    logger.info("Handling list tools request")
    client_manager = use_client_manager()

    tasks = map(lambda client: client.list_tools(), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks)
    result_tools = []
    for result in task_results:
        if isinstance(result, BaseException):
            logger.warning("Unexpected result type from list_prompts for client: {}", result)
            continue
        result_tools.extend(result.tools)
    logger.debug("Returned tools: {}", result_tools)
    return result_tools

async def handle_call_tool(
    name: str,
    arguments: dict[str, str] | None,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    logger.info("Handling call tool request for tool '{}'", name)
    client_manager = use_client_manager()

    tasks = map(lambda client: client.call_tool(name, arguments), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks)
    for result in task_results:
        if isinstance(result, BaseException):
            logger.warning("Unexpected result type from call_tool for client: {}", result)
            continue
        return result.content
    raise ValueError(f"No tool named '{name}' found")
