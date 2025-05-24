from mcp.server.fastmcp import FastMCP

mcp = FastMCP("CodeReview")

@mcp.prompt(name="Code Review")
def code_review() -> str:
    return "Please review the modified code files."

@mcp.prompt(name="Code Explain")
def code_explain(code: str) -> str:
    return f"""\
Please explain these code:
```
{code}
```\
"""

if __name__ == "__main__":
    mcp.run()