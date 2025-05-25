from dataclasses import dataclass

from loguru import logger
from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, Field, model_validator

class MCPServer(BaseModel):
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

    name: str
    params: StdioParams | SseParams

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
        if validated.command:
            config = ClientConfig.StdioParams(
                validated.command,
                validated.args,
                validated.env)
        if validated.url:
            config = ClientConfig.SseParams(
                validated.url,
                validated.headers)
        assert config is not None
        clients[name] = ClientConfig(name=name, params=config)

    return list(clients.values())
