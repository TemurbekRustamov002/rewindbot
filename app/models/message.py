import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import BigInteger, String, Boolean, DateTime, Text, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.chat import Chat
    from app.models.media import MediaObject
    from app.models.event import DeletedEvent


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chat_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="SET NULL"), nullable=True, index=True
    )

    business_connection_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    sender_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    direction: Mapped[str] = mapped_column(String(20), default="INCOMING", nullable=False)  # INCOMING, OUTGOING
    type: Mapped[str] = mapped_column(String(50), default="TEXT", nullable=False)  # TEXT, PHOTO, VIDEO, etc.

    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entities_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reply_to_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    media_group_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Deletion tracking
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("business_connection_id", "telegram_chat_id", "telegram_message_id", name="uq_business_chat_message"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="messages")
    chat: Mapped[Optional["Chat"]] = relationship("Chat", back_populates="messages")
    versions: Mapped[List["MessageVersion"]] = relationship("MessageVersion", back_populates="message", cascade="all, delete-orphan")
    media_objects: Mapped[List["MediaObject"]] = relationship("MediaObject", back_populates="message", cascade="all, delete-orphan")
    deleted_events: Mapped[List["DeletedEvent"]] = relationship("DeletedEvent", back_populates="message", cascade="all, delete-orphan")


class MessageVersion(Base, TimestampMixin):
    __tablename__ = "message_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message_id_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entities_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    telegram_edit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("message_id_fk", "version_number", name="uq_msg_version"),
    )

    # Relationship
    message: Mapped["Message"] = relationship("Message", back_populates="versions")
