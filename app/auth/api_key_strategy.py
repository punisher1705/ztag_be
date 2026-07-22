"""
API-key-based implementation of `AuthStrategy`.
 
Same Dependency Inversion shape as `JWTAuthStrategy`: this class depends
on a small `ApiKeyRepository` interface, not on SQLAlchemy or a DB
session directly. That makes it testable with a plain in-memory stub
(see tests) and means swapping storage later (e.g. a cache layer in
front of MySQL) doesn't touch this class at all.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Protocol
from dataclasses import dataclass

from app.auth.base_strategy import AuthenticationError, AuthenticatedIdentity
from app.core.security.password_hasher import PasswordHasher
from app.core.security.api_key_generator import parse_api_key

@dataclass(frozen=True)
class ApiKeyRecord:
    key_id: str
    hashed_secret: str
    owner_user_id: uuid.UUID
    role: str
    is_usable: str

class ApiKeyRepository(Protocol):
    def find_by_key_id(self, key_id: str) -> ApiKeyRecord | None: ...
    def record_usage(self, key_id: str, *, used_at: datetime ) -> None: ...

class ApiKeyNotFoundError(AuthenticationError):
    """No record matches the presented key_id."""

class ApiKeyInactiveError(AuthenticationError):
    """Key exists but is revoked, deactivated, or expired."""

class ApiKeyInvalidError(AuthenticationError):
    """Malformed key, or secret doesn't match the stored hash."""

class ApiKeyAuthStrategy:
    def __init__(self, repository: ApiKeyRepository, hasher: PasswordHasher) -> None:
        self._repository = repository
        self._hasher = hasher
    
    def authenticate(self, crednetial: str) -> AuthenticatedIdentity:
        try:
            key_id, secret = parse_api_key(crednetial)
        except ValueError as exc:
            raise ApiKeyInvalidError(str(exc)) from exc
        
        record = self._repository.find_by_key_id(key_id)
        if record is None:
            raise ApiKeyNotFoundError("unknown or invalid API key")
        
        if not record.is_usable:
            raise ApiKeyInvalidError("this API key has been revoed, deactivated or expired")
        
        if not self._hasher.verify(secret, record.hashed_secret):
            raise ApiKeyNotFoundError("unknown or invalid API key")
        
        self._repository.record_usage(key_id, used_at=datetime.now(timezone.utc))

        return AuthenticatedIdentity(
            user_id=record.owner_user_id,
            role=record.role,
            token_type="api_key",
            jti=record.key_id
        )

        
