"""
The auth strategy interface.
 
Defined before any concrete implementation (JWT, and later API-key auth
for service-to-service calls) — decide the contract first, then write
code that satisfies it. This is the Strategy pattern: the middleware
that protects routes depends on `AuthStrategy`, never on `JWTAuthStrategy`
directly, so adding API-key auth later means writing a new class, not
touching the middleware or any route.
"""

from __future__ import annotations
 
import uuid
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class AuthenticatedIdentity:
    user_id: uuid.UUID
    role: str
    token_type: str
    jti: str

class AuthenticationError(Exception):
    """Base class for auth failures the strategy surfaces to its caller."""

class AuthStrategy(Protocol):
    """Interface every authentication method must satisfy."""
 
    def authenticate(self, credential: str) -> AuthenticatedIdentity:
        """
        Validate `credential` (e.g. a raw 'Authorization: Bearer <token>'
        value, already stripped of the 'Bearer ' prefix by the caller)
        and return the identity it represents.
 
        Raises AuthenticationError (or a subclass) on any failure —
        expired, invalid, revoked, wrong type — rather than returning
        None, so the caller can distinguish failure reasons and respond
        appropriately (401 vs. a specific "token expired, please refresh"
        signal).
        """
        ...