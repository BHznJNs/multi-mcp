from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Translator")

@mcp.prompt(name="Translate text")
def translate_text(text: str) -> str:
    return f"""\
Please translate the text:
```
{text}
```\
"""

if __name__ == "__main__":
    mcp.run()