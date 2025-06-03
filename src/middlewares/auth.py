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
        # use both `Authorization` or `X-MCP-Token` to authenticate the user
        if "Authorization" not in conn.headers and\
            "X-MCP-Token" not in conn.headers:
            logger.warning("Authorization header not found in request.")
            raise AuthenticationError("Authorization header not found in request.")

        default_auth   = conn.headers.get("Authorization")
        extra_auth     = conn.headers.get("X-MCP-Token")
        expected_token = os.environ.get("AUTH_TOKEN")
        try:
            if default_auth is not None:
                # use bearer token
                logger.info("Use default Authorization header.")
                scheme, token = default_auth.split()
                if scheme.lower() != "bearer":
                    logger.debug("Auth failed: Bearer prefixed token is required.")
                    raise AuthenticationError("Bearer prefixed token is required.")

                if not token:
                    logger.debug("Auth failed: Bearer token is missing.")
                    raise AuthenticationError("Bearer token is missing.")

                expected_token = os.environ.get("AUTH_TOKEN")
                if token != expected_token:
                    logger.debug("Auth failed: Invalid auth token.")
                    raise AuthenticationError("Invalid auth token.")

            if extra_auth is not None:
                # directly compare token
                logger.info("Use extra X-MCP-Token header.")
                if extra_auth != expected_token:
                    logger.debug("Auth failed: Invalid auth token.")
                    raise AuthenticationError("Invalid auth token.")

            username = "authenticated_user"
            logger.info("Authenticated user: {}", username)
            return AuthCredentials(["authenticated"]), SimpleUser(username)

        except ValueError:
            raise AuthenticationError("Invalid Authorization header format")
        except AuthenticationError as e:
            logger.info("Authorization failed: {}", e)
            raise e
        except Exception as e:
            raise AuthenticationError(f"Unexpected error during authorization: {e}")
