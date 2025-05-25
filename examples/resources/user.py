from mcp.server.fastmcp import FastMCP

mcp = FastMCP("User")

@mcp.resource("users://{user_id}")
def get_user(user_id: str) -> str:
    """Get user data"""
    return f"User data for user {user_id}"

@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """Dynamic user data"""
    return f"Profile data for user {user_id}"

if __name__ == "__main__":
    mcp.run()