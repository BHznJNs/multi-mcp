from dotenv import load_dotenv

from .settings import Settings
from .entry_server import EntryServer


load_dotenv(override=True)

settings = Settings()
print(settings.transport)
server = EntryServer(settings)
match settings.transport:
    case "stdio":
        import asyncio
        asyncio.run(server.start_stdio_server())
    case "sse":
        server.start_sse_server()
        app = server.app
