import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Notification preferences
    notify_deleted_text: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_edited_messages: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_deleted_photos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_deleted_videos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_deleted_voice: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_deleted_documents: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_view_once: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="settings")


class SupportTicket(Base, TimestampMixin):
    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", nullable=False)  # OPEN, RESOLVED, CLOSED
    admin_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
