import re
from http.client import HTTPConnection
from starlette.requests import Request, HTTPConnection
from starlette_context.plugins import Plugin

from ..client.client_manager import ClientManager
from ..settings import Settings


class ClientManagerPlugin(Plugin):
    key = "client_manager"

    def __init__(self, client_manager: ClientManager) -> None:
        super().__init__()
        self._client_manager = client_manager

    async def process_request(self, request: Request | HTTPConnection) -> ClientManager:
        return self._client_manager

class SettingsPlugin(Plugin):
    key = "settings"

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings

    async def process_request(self, request: Request | HTTPConnection) -> Settings:
        return self._settings

class NamespacePlugin(Plugin):
    key = "namespace"

    async def process_request(self, request: Request | HTTPConnection):
        path = request.scope.get("path")
        if path is None:
            return None
        if path in ["/sse", "/mcp", "/sse/", "/mcp/"]:
            return None
        match = re.match(r"^/([^/]+)/(sse|mcp)/?$", path)
        if match:
            return match.group(1)
        return None
