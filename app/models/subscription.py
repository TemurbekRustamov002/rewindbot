import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import BigInteger, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    plan_type: Mapped[str] = mapped_column(String(50), default="PRO", nullable=False)  # PRO, PLUS, ULTIMATE
    status: Mapped[str] = mapped_column(
        String(50), default="ACTIVE", nullable=False
    )  # TRIAL, ACTIVE, CANCELED_PENDING_EXPIRY, EXPIRED, PAYMENT_FAILED, REFUNDED

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    telegram_charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invoice_payload: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="subscription")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )

    telegram_payment_charge_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    provider_payment_charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    currency: Mapped[str] = mapped_column(String(10), default="XTR", nullable=False)  # XTR for Stars
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g., 50 Stars

    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_first_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    subscription_expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload_json: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="payments")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="payments")
