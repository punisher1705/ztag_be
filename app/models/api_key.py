"""
The `ApiKey` model.
 
Used for service-to-service (machine) auth — the `SERVICE` role on
`User` is the identity an API key acts *as*; the key itself is a
separate, revocable credential a service presents instead of a JWT.
 
Design: an API key the caller presents looks like `gwk_<key_id>.<secret>`.
Splitting it into two parts is deliberate, not cosmetic:
 
- `key_id` is stored in plaintext and indexed — it's how we find the
  *row* in O(1), the same way a username does for a login form.
- `secret` is never stored — only its Argon2 hash is, exactly like a
  password. A stolen database backup does not hand an attacker usable
  API keys, just like it shouldn't hand out usable passwords.
 
This mirrors how Stripe/GitHub-style API keys work, and is why a raw
API key can only ever be shown to the caller once, at creation time —
after that, only the hash exists, and there is no way to recover or
re-display the original secret.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.sessions import Base
from app.models.base import GUID, TimestampMixin, UUIDPrimaryKeyMixin

class ApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_keys"
    
    # Public lookup handle — safe to log, safe to show in a "your API keys" list.
    key_id: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)

    # Argon2 hash of the secret half. Never the raw secret.
    hashed_secret: Mapped[str] = mapped_column(String(255), nullable=False)

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[str] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.expires_at
    
    @property
    def is_usable(self) -> bool:
        """False if inactive, revoked, or expired — the strategy checks this, not just is_active."""
        return self.is_active and self.revoked_at is None and not self.is_expired
    
    def revoke(self) -> None:
        self.is_active = False
        self.revoked_at = datetime.now(timezone.utc)
    
    def mark_used(self) -> None:
        self.last_used_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<ApiKey key_id={self.key_id!r} name={self.name!r} active={self.is_usable}>"
