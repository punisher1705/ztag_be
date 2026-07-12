"""
Password hashing, behind an interface.

The `User` model (and anything else that needs to check a password)
depends on `PasswordHasher`, not on argon2-cffi directly. That's the
Dependency Inversion half of SOLID applied concretely: swapping the
hashing algorithm later (e.g. moving to a FIPS-approved KDF for a
compliance requirement) means writing a new class, not touching the
model or every call site.

Argon2id is the default choice here (not bcrypt/PBKDF2) because it's
the current OWASP-recommended algorithm for password storage — it's
memory-hard, which meaningfully raises the cost of GPU/ASIC cracking
compared to bcrypt.
"""

from __future__ import annotations

from typing import Protocol

from argon2 import PasswordHasher as _Argon2PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError


class PasswordHasher(Protocol):
    """Interface every password hashing strategy must satisfy."""

    def hash(self, plain_password: str) -> str: ...

    def verify(self, plain_password: str, hashed_password: str) -> bool: ...

    def needs_rehash(self, hashed_password: str) -> bool: ...


class Argon2PasswordHasher:
    """Argon2id-based implementation of `PasswordHasher`."""

    def __init__(self) -> None:
        # Defaults from argon2-cffi already track OWASP guidance
        # (time_cost=3, memory_cost=64MB, parallelism=4). Kept explicit
        # here so a future tuning change is a one-line, reviewable diff.
        self._hasher = _Argon2PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16,
        )

    def hash(self, plain_password: str) -> str:
        return self._hasher.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self._hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, InvalidHashError):
            return False

    def needs_rehash(self, hashed_password: str) -> bool:
        """True if stored hash was made with older/weaker parameters."""
        return self._hasher.check_needs_rehash(hashed_password)