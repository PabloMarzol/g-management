
import asyncio
from datetime import datetime
from typing import Optional, List
import uuid
from enum import Enum
from sqlalchemy import String, Numeric, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, ENUM
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# Enums
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

# Models
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
    
    # Relationships
    operations: Mapped[List["Operation"]] = relationship(back_populates="client")

class Operation(Base):
    __tablename__ = "operations"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    # Client information
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    pickup_address: Mapped[str] = mapped_column(Text)
    
    # Financial details
    amount_usd: Mapped[Numeric] = mapped_column(Numeric(15, 2))
    commission_rate: Mapped[Numeric] = mapped_column(Numeric(5, 4))
    commission_amount: Mapped[Numeric] = mapped_column(Numeric(15, 2))
    fx_commission: Mapped[Numeric] = mapped_column(Numeric(15, 2))
    net_amount: Mapped[Numeric] = mapped_column(Numeric(15, 2))
    estimated_usdt: Mapped[Numeric] = mapped_column(Numeric(18, 8))
    
    # USDT details
    usdt_wallet: Mapped[str] = mapped_column(String(100))
    actual_usdt: Mapped[Optional[Numeric]] = mapped_column(Numeric(18, 8), nullable=True)
    
    # Status and assignments
    status: Mapped[OperationStatus] = mapped_column(ENUM(OperationStatus, name="operation_status"))
    collector_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    fx_provider: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Additional fields
    priority: Mapped[str] = mapped_column(String(20), default="Normal")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
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

# Database operations
async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_database():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_default_users():
    """Create default users for demo"""
    async with AsyncSessionLocal() as session:
        try:
            # Check if users already exist
            from sqlalchemy import select
            result = await session.execute(select(User))
            existing_users = result.scalars().all()
            
            if not existing_users:
                # Create default users
                default_users = [
                    User(
                        username="admin",
                        email="admin@alma.com",
                        password_hash="admin123",  # In production, use proper hashing
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
                    ),
                    User(
                        username="carlos",
                        email="carlos@alma.com",
                        password_hash="carlos123",
                        role=UserRole.COLLECTOR,
                        full_name="Carlos Rodriguez",
                        phone="+1234567893"
                    )
                ]
                
                for user in default_users:
                    session.add(user)
                
                await session.commit()
                print("✅ Default users created successfully!")
            else:
                print("ℹ️ Users already exist in database")
                
        except Exception as e:
            print(f"❌ Error creating default users: {e}")
            await session.rollback()

async def create_sample_clients():
    """Create sample clients"""
    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select
            result = await session.execute(select(Client))
            existing_clients = result.scalars().all()
            
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
                    ),
                    Client(
                        name="David Chen",
                        phone="+1555001003",
                        email="david.chen@email.com",
                        client_type=ClientType.FREQUENT,
                        total_operations=8,
                        total_volume=85000
                    ),
                    Client(
                        name="Sarah Johnson",
                        phone="+1555001004",
                        email="sarah.johnson@email.com",
                        client_type=ClientType.REGULAR,
                        total_operations=2,
                        total_volume=18000
                    )
                ]
                
                for client in sample_clients:
                    session.add(client)
                
                await session.commit()
                print("✅ Sample clients created successfully!")
            else:
                print("ℹ️ Clients already exist in database")
                
        except Exception as e:
            print(f"❌ Error creating sample clients: {e}")
            await session.rollback()

# Helper function to run async setup
async def setup_database():
    """Complete database setup"""
    print("🔧 Setting up ALMA database...")
    await init_database()
    await create_default_users()
    await create_sample_clients()
    print("✅ Database setup completed!")

def run_database_setup():
    """Run database setup synchronously"""
    asyncio.run(setup_database())

if __name__ == "__main__":
    run_database_setup()