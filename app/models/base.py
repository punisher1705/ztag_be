from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.dialects.mssql import CHAR
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

class GUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(str(value))
    
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """Adds `created_at` / `updated_at`, both maintained by the app, not the DB."""
 
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )