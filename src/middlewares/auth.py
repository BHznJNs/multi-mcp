import os
from loguru import logger
from starlette.authentication import (
    AuthCredentials, AuthenticationBackend, AuthenticationError, SimpleUser, UnauthenticatedUser
)
from starlette.middleware.authentication import AuthenticationMiddleware


class ConditionalAuthMiddleware(AuthenticationMiddleware):
    async def __call__(self, scope, receive, send):
        if os.environ.get("AUTH_TOKEN") is None:
            logger.info("Authorization is disabled.")
            scope["auth"] = AuthCredentials(["authenticated"])
            scope["user"] = SimpleUser("default_user")
            await self.app(scope, receive, send)
        else:
            await super().__call__(scope, receive, send)

class AuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        # use both `Authorization` and `X-MCP-Token` to authenticate the user
        if "Authorization" not in conn.headers and\
            "X-MCP-Token" not in conn.headers:
            logger.warning("Authorization header not found in request.")
            return

        auth = conn.headers.get("Authorization") or\
               conn.headers.get("X-MCP-Token")
        assert auth is not None
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != "bearer":
                raise AuthenticationError("Bearer prefixed token is required.")

            token = credentials
            if not token:
                raise AuthenticationError("Bearer token is missing.")

            expected_token = os.environ.get("AUTH_TOKEN")
            if expected_token and token != expected_token:
                raise AuthenticationError("Invalid auth token.")

            username = "authenticated_user"
            logger.log("Authenticated user: {}", username)
            return AuthCredentials(["authenticated"]), SimpleUser(username)

        except ValueError:
            raise AuthenticationError("Invalid Authorization header format")
        except AuthenticationError as e:
            logger.info("Authorization failed: {}", e)
            raise e
        except Exception as e:
            raise AuthenticationError(f"Unexpected error during authorization: {e}")
