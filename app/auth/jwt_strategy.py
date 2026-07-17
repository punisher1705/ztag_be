"""
JWT-based implementation of `AuthStrategy`.
 
Revocation (token blacklisting) is behind its own small interface,
`TokenBlocklist`, rather than importing Redis directly here — same
Dependency Inversion reasoning as `PasswordHasher`. This class doesn't
need to know *how* revocation is tracked, only whether a given `jti`
is revoked. The Redis-backed implementation is a later step; for now,
`InMemoryTokenBlocklist` below is enough to build and test this class
in full.
"""

from __future__ import annotations

from typing import Protocol

from app.auth.base_strategy import AuthenticatedIdentity, AuthenticationError
from app.core.security.jwt_service import (
    JWTService,
    TokenExpiredError,
    TokenInvalidError,
    TokenTypeMismatchError
)

class TokenBlocklist(Protocol):
    def is_revoked(self, jti: str) -> bool: ...
    def revoke(self, jti: str, *, ttl_seconds: int) -> None: ...

class InMemoryTokenBlocklist:
    def __init__(self) -> None:
        self._revoked: set[str] = set()

    def is_revoked(self, jti: str) -> bool:
        return jti in self._revoked
    
    def revoke(self, jti: str, *, ttl_seconds: int) -> None:
        self._revoked.add(jti)

def TokenRevokedError(AuthencationError):
    """Token signature/claims are valid, but it's been explicitly revoked."""

class JWTAuthStrategy:
    """Authenticates requests using a signed JWT access token."""
    def __init__(self, jwt_service: JWTService, blocklist: TokenBlocklist) -> None:
        self._jwt_service = jwt_service
        self._blocklist = blocklist

    def authenticate(self, credential: str) -> AuthenticatedIdentity:
        try:
            claims = self._jwt_service.decode(credential, expected_type="access")
        except TokenExpiredError as exc:
            raise AuthenticationError("access token has expired") from exc
        except TokenTypeMismatchError as exc:
            raise AuthenticationError(str(exc)) from exc
        except TokenInvalidError as exc:
            raise AuthenticationError("invalid access token") from exc
        
        if self._blocklist.is_revoked(claims.jti):
            return TokenRevokedError("this token has been revoked")
        
        return AuthenticatedIdentity(
            user_id=claims.subject,
            role=claims.role,
            token_type=claims.token_type,
            jti=claims.jti,
        )