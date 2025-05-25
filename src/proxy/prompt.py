import asyncio
from loguru import logger
from mcp import types

from .utils import use_client_manager, use_client_session, use_namespace, use_settings, with_namespace, without_namespace


async def handle_list_prompts() -> list[types.Prompt]:
    logger.info("List prompts requested")
    namespace = use_namespace()

    if namespace is not None:
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        list_tools_result = await client.list_prompts()
        return list_tools_result.prompts

    client_manager = use_client_manager()
    settings = use_settings()
    tasks = map(lambda session: session.list_prompts(), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    result_prompts = []
    for name, result in zip(client_manager.client_names, task_results):
        if isinstance(result, BaseException):
            logger.warning("Unexpected result type from list_prompts for client: {}", result)
            continue
        if settings.use_namespace:
            for prompt in result.prompts:
                prompt.name = with_namespace(name, prompt.name)
                result_prompts.append(prompt)
        else:
            result_prompts.extend(result.prompts)

    return result_prompts

async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    logger.info("Get prompt: '{}'", name)
    namespace = use_namespace()

    if namespace is not None:
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        get_prompt_result = await client.get_prompt(name, arguments)
        return get_prompt_result

    settings = use_settings()
    if settings.use_namespace:
        namespace, tool_name = without_namespace(name)
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        get_prompt_result = await client.get_prompt(tool_name, arguments)
        return get_prompt_result

    client_manager = use_client_manager()
    tasks = map(lambda session: session.get_prompt(name, arguments), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in task_results:
        if isinstance(result, BaseException):
            logger.warning("Unexpected exception from get_prompt for client: {}", result)
            continue
        return result

    logger.warning("Prompt not found: '{}'", name)
    return types.GetPromptResult(
        description=f"Prompt not found: '{name}'",
        messages=[],
    )
