import asyncio
from asyncio import tasks
from loguru import logger
from mcp import types
from pydantic import AnyUrl

from .utils import use_client_manager, use_client_session, use_namespace, use_settings, with_namespace


async def handle_list_resources() -> list[types.Resource]:
    logger.info("List resources requested")
    namespace = use_namespace()

    if namespace is not None:
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        list_resources_result = await client.list_resources()
        return list_resources_result.resources

    client_manager = use_client_manager()
    settings = use_settings()
    tasks = map(lambda session: session.list_resources(), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)

    result_resources = []
    for name, task_result in zip(client_manager.client_names, task_results):
        if isinstance(task_result, BaseException):
            logger.exception(f"Error while listing resources for server: {name}")
            continue

        if settings.use_namespace:
            for resource in task_result.resources:
                resource.name = with_namespace(name, resource.name)
                result_resources.append(resource)
        else:
            result_resources.extend(task_result.resources)
    
    logger.debug("Returned resources: {}", result_resources)
    return result_resources

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
    namespace = use_namespace()

    if namespace is not None:
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        read_resource_result = await client.read_resource(uri)
        return join_contents(read_resource_result.contents)

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
    namespace = use_namespace()

    if namespace is not None:
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        list_resource_templates_result = await client.list_resource_templates()
        return list_resource_templates_result.resourceTemplates

    client_manager = use_client_manager()
    settings = use_settings()
    tasks = map(lambda session: session.list_resource_templates(), client_manager.client_sessions)
    task_results = await asyncio.gather(*tasks, return_exceptions=True)

    templates = []
    for name, task_result in zip(client_manager.client_names, task_results):
        if isinstance(task_result, BaseException):
            logger.exception(f"Error while listing resource templates: {task_result}")
            continue
        if settings.use_namespace:
            for template in task_result.resourceTemplates:
                template.name = with_namespace(name, template.name)
                templates.append(template)
        else:
            templates.extend(task_result.resourceTemplates)
    return templates

async def handle_subscribe_resource(url: AnyUrl):
    logger.info("Subscribe resource '{}' requested", url)
    namespace = use_namespace()

    if namespace is not None:
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        await client.subscribe_resource(url)
        return

    client_manager = use_client_manager()
    tasks = map(lambda session: session.subscribe_resource(url), client_manager.client_sessions)
    await asyncio.gather(*tasks, return_exceptions=True)

async def handle_unsubscribe_resource(url: AnyUrl):
    logger.info("Unsubscribe resource '{}' requested", url)
    namespace = use_namespace()

    if namespace is not None:
        client = use_client_session(namespace)
        if client is None:
            raise ValueError(f"No client found for name: '{namespace}'")
        await client.unsubscribe_resource(url)
        return

    client_manager = use_client_manager()
    tasks = map(lambda session: session.unsubscribe_resource(url), client_manager.client_sessions)
    await asyncio.gather(*tasks, return_exceptions=True)
