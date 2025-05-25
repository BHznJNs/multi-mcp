from starlette_context.plugins import Plugin

from ..client.client_manager import ClientManager


class ClientManagerPlugin(Plugin):
    key = "client_manager"

    def __init__(self, client_manager: ClientManager) -> None:
        super().__init__()
        self._client_manager = client_manager

    async def process_request(self, request) -> ClientManager:
        return self._client_manager
