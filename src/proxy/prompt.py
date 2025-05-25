import asyncio
from loguru import logger
from mcp import types

from .utils import use_client_manager


async def handle_list_prompts() -> list[types.Prompt]:
    logger.info("List prompts requested")
    client_manager = use_client_manager()

    tasks = map(lambda session: session.list_prompts(), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    result_prompts = []
    for result in task_results:
        if isinstance(result, BaseException):
            logger.warning("Unexpected result type from list_prompts for client: {}", result)
            continue
        result_prompts.extend(result.prompts)
    logger.debug("Returned prompts: {}", result_prompts)
    return result_prompts

async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    logger.info("Get prompt: '{}'", name)
    client_manager = use_client_manager()

    tasks = map(lambda session: session.get_prompt(name, arguments), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in task_results:
        if isinstance(result, BaseException):
            logger.warning("Unexpected result type from get_prompt for client: {}", result)
            continue
        return result
    logger.error("No prompt found for name: {}", name)
    return types.GetPromptResult(
        description=f"Prompt '{name}' not found!",
        messages=[],
    )
