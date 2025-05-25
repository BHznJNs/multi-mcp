import json
import mcp.server.sse
import mcp.server.stdio
from loguru import logger
from starlette.authentication import requires
from starlette.middleware import Middleware
from starlette_context.middleware import ContextMiddleware
from starlette.routing import Route, Mount
from starlette.responses import Response
from starlette.applications import Starlette
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from .lifespan import sse_lifespan_factory, streamable_lifespan_factory
from .client import config_parser, ClientManager
from .proxy import proxy_server_factory
from .middlewares.context import ClientManagerPlugin, NamespacePlugin, SettingsPlugin
from .middlewares.auth import AuthBackend, ConditionalAuthMiddleware
from .settings import Settings


class EntryServer:
    def __init__(self, settings: Settings) -> None:
        self._starlette_app = None
        self._settings = settings
        self._server = proxy_server_factory()
        self._init_client_manager()

    def _init_client_manager(self):
        with open(self._settings.config, "r") as f:
            mcp_config = json.load(f)

        client_configs = config_parser(mcp_config)
        self._client_manager = ClientManager(self._settings.encoding, client_configs)

    @property
    def app(self) -> Starlette | None:
        return self._starlette_app

    async def start_stdio_server(self):
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self._server.run(
                read_stream,
                write_stream,
                self._server.create_initialization_options())

    def start_sse_server(self):
        @requires("authenticated")
        async def handle_sse(request):
            nonlocal sse
            logger.info("SSE connection received")
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await self._server.run(
                    streams[0],
                    streams[1],
                    self._server.create_initialization_options())
            return Response()
        
        @requires("authenticated")
        async def handle_named_sse(request):
            nonlocal sse
            name = request.path_params["name"]
            logger.info("SSE connection received for server: {}", name)
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await self._server.run(
                    streams[0],
                    streams[1],
                    self._server.create_initialization_options())
            return Response()

        logger.info("Starting SSE server")
        sse = mcp.server.sse.SseServerTransport("/messages/")
        self._starlette_app = Starlette(
            middleware=[
                Middleware(ContextMiddleware, plugins=[
                    SettingsPlugin(self._settings),
                    ClientManagerPlugin(self._client_manager),
                    NamespacePlugin(),
                ]),
                Middleware(ConditionalAuthMiddleware, backend=AuthBackend())
            ],
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Route("/{name}/sse", endpoint=handle_named_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
            lifespan=sse_lifespan_factory(self._client_manager),
            debug=self._settings.debug,
        )

    def start_streamable_server(self):
        async def handle_streamable_http(scope, receive, send) -> None:
            logger.info("Streamable HTTP connection received")
            await self._session_manager.handle_request(scope, receive, send)

        async def handle_named_streamable_http(scope, receive, send) -> None:
            name = scope["path_params"]["name"]
            logger.info("Streamable HTTP connection received for server: {}", name)
            await self._session_manager.handle_request(scope, receive, send)

        logger.info("Starting Streamable server")
        self._session_manager = StreamableHTTPSessionManager(
            app=self._server,
            event_store=None,
            stateless=True,
        )
        self._starlette_app = Starlette(
            middleware=[
                Middleware(ContextMiddleware, plugins=[
                    SettingsPlugin(self._settings),
                    ClientManagerPlugin(self._client_manager),
                    NamespacePlugin(),
                ]),
                Middleware(ConditionalAuthMiddleware, backend=AuthBackend()),
            ],
            routes=[
                Mount("/mcp", app=handle_streamable_http),
                Mount("/{name}/mcp", app=handle_named_streamable_http),
            ],
            lifespan=streamable_lifespan_factory(self._client_manager, self._session_manager),
            debug=self._settings.debug,
        )
