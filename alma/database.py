from datetime import datetime
from typing import Optional, List
import uuid
from enum import Enum
from sqlalchemy import String, Numeric, DateTime, Text, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, ARRAY, ENUM
import os
from dotenv import load_dotenv

load_dotenv()

# Convert async DATABASE_URL to sync
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Create sync engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

# Enums (same as before)
class UserRole(str, Enum):
    ADMIN = "admin"
    FX_PROVIDER = "fx_provider"
    COLLECTOR = "collector"

class ClientType(str, Enum):
    REGULAR = "regular"
    FREQUENT = "frequent"

class OperationStatus(str, Enum):
    PENDING = "Pending"
    ASSIGNED = "Assigned"
    COLLECTING = "Collecting"
    COLLECTED = "Collected"
    VALIDATED = "Validated"
    DELIVERED_TO_FX = "Delivered to FX"
    FX_PROCESSING = "FX Processing"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    ERROR = "Error"

# Models (same as before)
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(ENUM(UserRole, name="user_role"))
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class Client(Base):
    __tablename__ = "clients"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    client_type: Mapped[ClientType] = mapped_column(ENUM(ClientType, name="client_type"), default=ClientType.REGULAR)
    total_operations: Mapped[int] = mapped_column(default=0)
    total_volume: Mapped[Numeric] = mapped_column(Numeric(15, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    operations: Mapped[List["Operation"]] = relationship(back_populates="client")

class Operation(Base):
    __tablename__ = "operations"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    pickup_address: Mapped[str] = mapped_column(Text)
    amount_usd: Mapped[Numeric] = mapped_column(Numeric(15, 2))
    commission_rate: Mapped[Numeric] = mapped_column(Numeric(5, 4))
    commission_amount: Mapped[Numeric] = mapped_column(Numeric(15, 2))
    fx_commission: Mapped[Numeric] = mapped_column(Numeric(15, 2))
    net_amount: Mapped[Numeric] = mapped_column(Numeric(15, 2))
    estimated_usdt: Mapped[Numeric] = mapped_column(Numeric(18, 8))
    usdt_wallet: Mapped[str] = mapped_column(String(100))
    actual_usdt: Mapped[Optional[Numeric]] = mapped_column(Numeric(18, 8), nullable=True)
    status: Mapped[OperationStatus] = mapped_column(ENUM(OperationStatus, name="operation_status"))
    collector_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    fx_provider: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="Normal")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    client: Mapped["Client"] = relationship(back_populates="operations")
    collector: Mapped[Optional["User"]] = relationship(foreign_keys=[collector_id])

class OperationLog(Base):
    __tablename__ = "operation_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operations.id"))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[Optional[str]] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

def init_database():
    """Initialize database tables"""
    Base.metadata.create_all(engine)

def create_default_users():
    """Create default users for demo"""
    with SessionLocal() as session:
        # Check if users already exist
        existing_users = session.query(User).all()
        
        if not existing_users:
            default_users = [
                User(
                    username="admin",
                    email="admin@alma.com",
                    password_hash="admin123",
                    role=UserRole.ADMIN,
                    full_name="Administrator",
                    phone="+1234567890"
                ),
                User(
                    username="fx_provider",
                    email="fx@alma.com",
                    password_hash="fx123",
                    role=UserRole.FX_PROVIDER,
                    full_name="FX Provider",
                    phone="+1234567891"
                ),
                User(
                    username="jessica",
                    email="jessica@alma.com",
                    password_hash="jessica123",
                    role=UserRole.COLLECTOR,
                    full_name="Jessica Garcia",
                    phone="+1234567892"
                )
            ]
            
            for user in default_users:
                session.add(user)
            
            session.commit()
            print("✅ Default users created!")

def create_sample_clients():
    """Create sample clients"""
    with SessionLocal() as session:
        existing_clients = session.query(Client).all()
        
        if not existing_clients:
            sample_clients = [
                Client(
                    name="John Smith",
                    phone="+1555001001",
                    email="john.smith@email.com",
                    client_type=ClientType.FREQUENT,
                    total_operations=12,
                    total_volume=150000
                ),
                Client(
                    name="Maria Garcia",
                    phone="+1555001002",
                    email="maria.garcia@email.com",
                    client_type=ClientType.REGULAR,
                    total_operations=3,
                    total_volume=25000
                )
            ]
            
            for client in sample_clients:
                session.add(client)
            
            session.commit()
            print("✅ Sample clients created!")

def setup_database():
    """Complete database setup"""
    print("🔧 Setting up ALMA database...")
    init_database()
    create_default_users()
    create_sample_clients()
    print("✅ Database setup completed!")

if __name__ == "__main__":
    setup_database()