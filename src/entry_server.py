import mcp.server.sse
import mcp.server.stdio
from starlette.applications import Starlette

from .settings import Settings


class EntryServer:
    def __init__(self, settings: Settings) -> None:
        from .proxy import proxy_server_factory
        self._startlette_app = None
        self._server = proxy_server_factory(settings.config, settings.encoding)

    @property
    def app(self) -> Starlette | None:
        return self._startlette_app

    async def start_stdio_server(self):
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self._server.run(
                read_stream,
                write_stream,
                self._server.create_initialization_options())

    def start_sse_server(self):
        from starlette.authentication import requires
        from starlette.middleware import Middleware
        from starlette_context.middleware import ContextMiddleware
        from starlette.routing import Route, Mount
        from starlette.responses import JSONResponse
        from .middlewares.auth import AuthBackend, ConditionalAuthMiddleware

        @requires("authenticated")
        async def handle_sse(request):
            nonlocal app, sse
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(
                    streams[0],
                    streams[1],
                    app.create_initialization_options())

            response = JSONResponse({"message": "SSE connection closed"})
            await response(request.scope, request.receive, request._send)
            return response

        async def handle_messages(scope, receive, send):
            nonlocal sse
            await sse.handle_post_message(scope, receive, send)

        app = self._server
        sse = mcp.server.sse.SseServerTransport("/messages/")
        self._startlette_app = Starlette(
            middleware=[
                Middleware(ContextMiddleware),
                Middleware(ConditionalAuthMiddleware, backend=AuthBackend())
            ],
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=handle_messages),
            ]
        )
