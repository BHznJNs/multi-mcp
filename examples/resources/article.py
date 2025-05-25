from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Article")

@mcp.resource("articles://{article_id}")
def get_article(article_id: str) -> str:
    """Get article content"""
    return f"Article content for article: {article_id}"

@mcp.resource("articles://{article_id}/comments")
def get_article_comments(article_id: str) -> str:
    """Dynamic user data"""
    return f"Comments for article: {article_id}"

if __name__ == "__main__":
    mcp.run()