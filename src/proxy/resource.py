import asyncio
from asyncio import tasks
from loguru import logger
from mcp import types
from pydantic import AnyUrl

from .utils import use_client_manager


async def handle_list_resources() -> list[types.Resource]:
    logger.info("List resources requested")
    client_manager = use_client_manager()

    tasks = map(lambda session: session.list_resources(), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    resources = []
    for task_result in task_results:
        if isinstance(task_result, BaseException):
            logger.exception(f"Error while listing resources: {task_result}")
            continue
        resources.extend(task_result.resources)
    return resources

async def handle_read_resource(uri: AnyUrl) -> str | bytes:
    def join_contents(contents: list[types.TextResourceContents | types.BlobResourceContents]) -> str | bytes:
        if type(contents[0]) is types.TextResourceContents:
            # assert all type(content in contents) is types.TextResourceContents
            return "".join(content.text for content in contents) # type: ignore
        elif type(contents[0]) is types.BlobResourceContents:
            # assert all type(content in contents) is types.BlobResourceContents
            return b"".join(content.blob for content in contents) # type: ignore
        else:
            raise ValueError("Unreachable")

    logger.info(f"Read resource requested: {uri}")
    client_manager = use_client_manager()

    tasks = map(lambda session: session.read_resource(uri), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    for task_result in task_results:
        if isinstance(task_result, BaseException):
            logger.exception(f"Error while reading resource: {task_result}")
            continue
        return join_contents(task_result.contents)

    raise ValueError("Resource '{}' not found", uri)

async def handle_list_resource_templates() -> list[types.ResourceTemplate]:
    logger.info("List resource templates requested")
    client_manager = use_client_manager()

    tasks = map(lambda session: session.list_resource_templates(), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    templates = []
    for task_result in task_results:
        if isinstance(task_result, BaseException):
            logger.exception(f"Error while listing resource templates: {task_result}")
            continue
        templates.extend(task_result.resourceTemplates)
    return templates

async def handle_subscribe_resource(url: AnyUrl):
    logger.info("Subscribe resource '{}' requested", url)
    client_manager = use_client_manager()
    tasks = map(lambda session: session.subscribe_resource(url), client_manager.client_sessions)
    await asyncio.gather(*tasks, return_exceptions=True)

async def handle_unsubscribe_resource(url: AnyUrl):
    logger.info("Unsubscribe resource '{}' requested", url)
    client_manager = use_client_manager()
    tasks = map(lambda session: session.unsubscribe_resource(url), client_manager.client_sessions)
    await asyncio.gather(*tasks, return_exceptions=True)
