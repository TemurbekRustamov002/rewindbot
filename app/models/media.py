import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.message import Message


class MediaObject(Base, TimestampMixin):
    __tablename__ = "media_objects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message_id_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )

    telegram_file_id: Mapped[str] = mapped_column(String(500), nullable=False)
    file_unique_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    media_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PHOTO, VIDEO, VOICE, etc.
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sha256: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)

    download_status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False
    )  # PENDING, COMPLETED, FAILED, SKIPPED
    download_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    message: Mapped["Message"] = relationship("Message", back_populates="media_objects")
