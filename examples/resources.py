from mcp.server.fastmcp import FastMCP

mcp = FastMCP("CodeReview")

@mcp.resource("config://app")
def get_config() -> str:
    """Static configuration data"""
    return "App configuration here"

@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """Dynamic user data"""
    return f"Profile data for user {user_id}"

if __name__ == "__main__":
    mcp.run()