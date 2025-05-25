# Multi MCP

An MCP server that proxies multiple MCP servers.

## Getting Started

Clone and cd:
```bash
git clone https://github.com/One-MCP/multi-mcp.git
cd multi-mcp
```

Install dependencies:
```bash
uv venv
uv pip install -r requirements.txt
```

Start server:
```bash
hypercorn src.main:app
# hypercorn src.main:app --bind 0.0.0.0:7860
```

Then you can access the server via `http://localhost:8080/sse` (for SSE mode) or `http://localhost:8080/mcp` (for streamable HTTP mode).

## Configuration

You can follows the [VSCode Documentation#Configuration format](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#_configuration-format) to create the configuration JSON files, and there are also example files in the [examples/config](examples/config).

## Environment Variables

|  Variable Name  | Default Value | Description |
|      ---        |      ---      |     ---     |
| `AUTH_TOKEN`    | `None`        | The authentication token, the server will not perform authentication if not set |
| `CONFIG`        | `./examples/config/mcp_tools.json` | Path to the MCP configuration file |
| `ENCODING`      | `utf-8`       | The character encoding used for communication |
| `TRANSPORT`     | `sse`         | The transport protocol for the server (one of `stdio`, `sse`, `http`) |
| `USE_NAMESPACE` | `True`        | Whether to use namespaces for tools/resources |
| `DEBUG`         | `False`       | Enable or disable debug mode |

## Inspiration

This project is inspired by: [multi-mcp](https://github.com/kfirtoledo/multi-mcp)
