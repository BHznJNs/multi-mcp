from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_CONFIG_FILE = "./examples/config/mcp.json"
DEFAULT_ENCODING = "utf-8"
TRANSPORT_MODES = Literal["stdio", "sse", "streamable"]

class Settings(BaseSettings):
    config: str = DEFAULT_CONFIG_FILE
    encoding: str = DEFAULT_ENCODING
    transport: TRANSPORT_MODES = "sse"
    use_namespace: bool = True
    debug: bool = False

    model_config = SettingsConfigDict()
