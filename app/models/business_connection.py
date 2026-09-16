import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class BusinessConnection(Base, TimestampMixin):
    __tablename__ = "business_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_connection_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    connection_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_reply: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rights_json: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="business_connections")
