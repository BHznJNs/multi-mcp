from dataclasses import dataclass
from typing import Literal

from loguru import logger
from pydantic import BaseModel
from pydantic import BaseModel, Field, model_validator

class MCPServer(BaseModel):
    type: Literal["stdio", "sse", "http"] | None = None
    disabled: bool = False
    command: str | None = None
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_command_or_url(self) -> "MCPServer":
        if (self.command is None and self.url is None) or (self.command is not None and self.url is not None):
            raise ValueError("Must only provide one of 'command' or 'url'.")
        return self
    
    @model_validator(mode="after")
    def check_type(self) -> "MCPServer":
        match self.type:
            case "stdio" if self.command is None:
                raise ValueError("Must provide 'command' for 'type':'stdio'.")
            case "sse" if self.url is None:
                raise ValueError("Must provide 'url' for 'type':'sse'.")
            case "http" if self.url is None:
                raise ValueError("Must provide 'url' for 'type': 'http'.")
            case None if self.command:
                self.type = "stdio"
            case None if self.url:
                # use http as default type for url
                self.type = "http"
        return self

@dataclass
class ClientConfig:
    @dataclass
    class StdioParams:
        command: str
        args: list[str]
        env: dict[str, str]
    @dataclass
    class SseParams:
        url: str
        headers: dict[str, str]
    @dataclass
    class StreamableParams:
        url: str
        headers: dict[str, str]

    name: str
    params: StdioParams | SseParams | StreamableParams
    disabled: bool

def config_parser(raw: dict) -> list[ClientConfig]:
    servers = raw.get("mcpServers")
    if servers is None or type(servers) is not dict: return []

    clients: dict[str, ClientConfig] = {}
    for name, server in servers.items():
        if name in clients:
            logger.warning("Client '{}' already exists and will be overridden.", name)

        try:
            validated = MCPServer(**server)
        except ValueError as e:
            msg: str = e.args[0]
            logger.error("Failed to parse server config for {}: {}", name, msg)
            continue

        config = None
        match validated.type:
            case "stdio":
                assert validated.command is not None
                config = ClientConfig.StdioParams(
                    validated.command,
                    validated.args,
                    validated.env)
            case "sse":
                assert validated.url is not None
                config = ClientConfig.SseParams(
                    validated.url,
                    validated.headers)
            case "http":
                assert validated.url is not None
                config = ClientConfig.StreamableParams(
                    validated.url,
                    validated.headers)
            case _: raise ValueError("Unreachable")

        clients[name] = ClientConfig(
            name=name,
            params=config,
            disabled=validated.disabled)

    return list(clients.values())
