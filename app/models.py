from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import ForeignKey, Numeric, Text, Enum
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
import uuid

class Base(AsyncAttrs, DeclarativeBase):
    pass

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STANDARD = "standard"

class ClientTag(str, enum.Enum):
    VIP = "VIP"
    PENDING = "pending"
    ACTIVE = "active"

class CashRunStatus(str, enum.Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STANDARD)
    pin_hash: Mapped[str | None] = mapped_column(Text)

class Client(Base):
    __tablename__ = "clients"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    contact_details: Mapped[str | None] = mapped_column(Text)
    wallets: Mapped[list[str]] = mapped_column(PG_ARRAY(Text))
    onboarding_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[ClientTag]] = mapped_column(PG_ARRAY(Enum(ClientTag)))

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    exchange: Mapped[str]
    api_key_enc: Mapped[str | None] = mapped_column(Text)
    balance: Mapped[Numeric] = mapped_column(Numeric(20, 8), default=0)
    pnl: Mapped[Numeric] = mapped_column(Numeric(20, 8), default=0)
    client: Mapped[Client] = relationship(back_populates="accounts")

Client.accounts = relationship(Account, back_populates="client")

class Wallet(Base):
    __tablename__ = "wallets"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    address: Mapped[str] = mapped_column(index=True)
    chain: Mapped[str]
    label: Mapped[str | None]
    client: Mapped[Client] = relationship()

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id"))
    type: Mapped[str]
    amount: Mapped[Numeric] = mapped_column(Numeric(20, 8))
    asset: Mapped[str]
    date: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    tx_hash: Mapped[str | None] = mapped_column(index=True)
    notes: Mapped[str | None] = mapped_column(Text)

class CashRun(Base):
    __tablename__ = "cash_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    pickup_staff: Mapped[list[str]] = mapped_column(PG_ARRAY(Text))
    dropoff_staff: Mapped[list[str]] = mapped_column(PG_ARRAY(Text))
    amount: Mapped[Numeric] = mapped_column(Numeric(15, 2))
    status: Mapped[CashRunStatus] = mapped_column(Enum(CashRunStatus), default=CashRunStatus.CREATED)
    fx_rate: Mapped[Numeric | None] = mapped_column(Numeric(10, 4))
    fee_percent: Mapped[Numeric] = mapped_column(Numeric(5, 2), default=4.0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    client: Mapped[Client] = relationship()