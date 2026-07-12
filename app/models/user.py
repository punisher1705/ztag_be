"""
The `User` model.
 
This is the identity record the auth middleware (JWT + API-key strategies,
still to come) will authenticate against. Deliberately includes brute-force
lockout state (`failed_login_attempts`, `locked_until`) at the model level —
in a zero-trust gateway, "never trust, always verify" extends to not trusting
that the auth layer above will always rate-limit login attempts correctly.
The data needed to make that decision lives with the account it protects.
"""

from __future__ import annotations

import enum
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.sessions import Base
from app.core.security.password_hasher import PasswordHasher
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

class UserRole(str, enum.Enum):
    """
    Coarse-grained role for authorization checks.
 
    ADMIN manages users/config; SERVICE is for machine-to-machine API-key
    callers (the "API key auth strategy" item still on the status table);
    VIEWER is read-only. Fine-grained per-resource permissions are a
    separate concern for later — this only decides "is this identity
    allowed to exist at all, and roughly what for."
    """
 
    ADMIN = "admin"
    SERVICE = "service"
    VIEWER = "viewer"

class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20), default=UserRole.VIEWER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Password management (Dependency Inversion: caller supplies the hasher) ---

    def set_password(self, plain_password: str, hasher: PasswordHasher) -> None:
        self.password_hash = hasher.hash(plain_password)

    def verify_password(self, plain_password: str, hasher: PasswordHasher) -> None:
        return hasher.verify(plain_password, self.password_hash)
    
    # --- Account lockout state machine ---

    @property
    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until
    
    def register_failed_login(self) -> None:
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            self.locked_until = datetime.now(timezone.utx) + timedelta(
                minutes=LOCKOUT_DURATION_MINUTES
            )

    def register_successful_login(self) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role.value}>"
