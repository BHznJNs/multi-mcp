from starlette_context import context
from ..client.client_manager import ClientManager


def use_client_manager():
    client_manager = context.get("client_manager")
    assert type(client_manager) is ClientManager
    return client_manager
