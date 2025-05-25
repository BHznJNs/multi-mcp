from mcp import ClientSession
from starlette_context import context

from ..client.client_manager import ClientManager
from ..settings import Settings


### Hooks

def use_client_session(name: str) -> ClientSession | None:
    client_manager = use_client_manager()
    return client_manager.get_client(name)

def use_client_manager():
    client_manager = context.get("client_manager")
    assert type(client_manager) is ClientManager
    return client_manager

def use_namespace() -> str | None:
    namespace = context.get("namespace")
    return namespace

def use_settings() -> Settings:
    settings = context.get("settings")
    assert type(settings) is Settings
    return settings

### Tool functions

def with_namespace(namespace: str, name: str) -> str:
    return f"{namespace}::{name}"

def without_namespace(namespaced: str) -> tuple[str, str]:
    namespace, name = namespaced.split("::")
    return namespace, name
