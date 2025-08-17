
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.orm import selectinload
import uuid

from database import (
    User, Client, Operation, OperationLog, 
    UserRole, ClientType, OperationStatus,
    AsyncSessionLocal
)
from config import calculate_commission

class DatabaseOperations:
    """Database operations class for ALMA"""
    
    @staticmethod
    async def get_session():
        """Get database session"""
        return AsyncSessionLocal()
    
    # User operations
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate user by username and password"""
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(
                User.username == username,
                User.password_hash == password,  # In production, use proper password hashing
                User.is_active == True
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                # Update last login
                user.last_login = datetime.utcnow()
                await session.commit()
            
            return user
    
    @staticmethod
    async def get_users_by_role(role: UserRole) -> List[User]:
        """Get all users by role"""
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(
                User.role == role,
                User.is_active == True
            ).order_by(User.full_name)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def create_user(user_data: Dict[str, Any]) -> User:
        """Create new user"""
        async with AsyncSessionLocal() as session:
            user = User(**user_data)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    
    # Client operations
    @staticmethod
    async def get_all_clients() -> List[Client]:
        """Get all clients"""
        async with AsyncSessionLocal() as session:
            stmt = select(Client).order_by(Client.name)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def get_client_by_id(client_id: uuid.UUID) -> Optional[Client]:
        """Get client by ID"""
        async with AsyncSessionLocal() as session:
            stmt = select(Client).where(Client.id == client_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    @staticmethod
    async def create_client(client_data: Dict[str, Any]) -> Client:
        """Create new client"""
        async with AsyncSessionLocal() as session:
            client = Client(**client_data)
            session.add(client)
            await session.commit()
            await session.refresh(client)
            return client
    
    @staticmethod
    async def update_client_stats(client_id: uuid.UUID, operation_amount: float):
        """Update client statistics after operation"""
        async with AsyncSessionLocal() as session:
            client = await session.get(Client, client_id)
            if client:
                client.total_operations += 1
                client.total_volume += operation_amount
                
                # Update client type based on volume and frequency
                if client.total_operations >= 5 and client.total_volume >= 25000:
                    client.client_type = ClientType.FREQUENT
                
                await session.commit()
    
    # Operation operations
    @staticmethod
    async def get_all_operations() -> List[Operation]:
        """Get all operations with related data"""
        async with AsyncSessionLocal() as session:
            stmt = select(Operation).options(
                selectinload(Operation.client),
                selectinload(Operation.collector)
            ).order_by(desc(Operation.created_at))
            result = await session.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def get_operations_by_status(status: OperationStatus) -> List[Operation]:
        """Get operations by status"""
        async with AsyncSessionLocal() as session:
            stmt = select(Operation).options(
                selectinload(Operation.client),
                selectinload(Operation.collector)
            ).where(Operation.status == status).order_by(desc(Operation.created_at))
            result = await session.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def get_operations_by_date_range(
        start_date: datetime, 
        end_date: datetime
    ) -> List[Operation]:
        """Get operations by date range"""
        async with AsyncSessionLocal() as session:
            stmt = select(Operation).options(
                selectinload(Operation.client),
                selectinload(Operation.collector)
            ).where(
                Operation.created_at >= start_date,
                Operation.created_at <= end_date
            ).order_by(desc(Operation.created_at))
            result = await session.execute(stmt)
            return result.scalars().all()
    
    @staticmethod
    async def create_operation(operation_data: Dict[str, Any]) -> Operation:
        """Create new operation"""
        async with AsyncSessionLocal() as session:
            try:
                # Generate operation ID
                today = datetime.utcnow()
                operation_id = f"MSB-{today.strftime('%Y-%m-%d')}-{str(int(today.timestamp()))[-3:]}"
                
                # Calculate commissions
                amount = float(operation_data['amount_usd'])
                client_type = operation_data.get('client_type', 'regular')
                commission_info = calculate_commission(amount, client_type)
                
                # Create operation
                operation = Operation(
                    operation_id=operation_id,
                    client_id=operation_data['client_id'],
                    pickup_address=operation_data['pickup_address'],
                    amount_usd=amount,
                    commission_rate=commission_info['commission_rate'],
                    commission_amount=commission_info['commission_amount'],
                    fx_commission=commission_info['fx_commission'],
                    net_amount=commission_info['net_amount'],
                    estimated_usdt=commission_info['net_amount'] * 0.95,  # Estimate with 5% for fees
                    usdt_wallet=operation_data['usdt_wallet'],
                    status=OperationStatus.PENDING,
                    collector_id=operation_data.get('collector_id'),
                    fx_provider=operation_data.get('fx_provider'),
                    deadline=operation_data.get('deadline'),
                    priority=operation_data.get('priority', 'Normal'),
                    notes=operation_data.get('notes')
                )
                
                session.add(operation)
                await session.commit()
                await session.refresh(operation)
                
                # Log operation creation
                await DatabaseOperations.log_operation_action(
                    operation.id,
                    operation_data.get('created_by_user_id'),
                    "Operation Created",
                    f"Operation {operation_id} created with amount ${amount:,.2f}"
                )
                
                # Update client stats
                await DatabaseOperations.update_client_stats(operation.client_id, amount)
                
                return operation
                
            except Exception as e:
                await session.rollback()
                raise e
    
    @staticmethod
    async def update_operation_status(
        operation_id: uuid.UUID, 
        new_status: OperationStatus,
        user_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None
    ) -> Operation:
        """Update operation status"""
        async with AsyncSessionLocal() as session:
            operation = await session.get(Operation, operation_id)
            if not operation:
                raise ValueError("Operation not found")
            
            old_status = operation.status
            operation.status = new_status
            
            # Set completion timestamp if completed
            if new_status == OperationStatus.COMPLETED:
                operation.completed_at = datetime.utcnow()
            
            await session.commit()
            
            # Log status change
            await DatabaseOperations.log_operation_action(
                operation_id,
                user_id,
                "Status Updated",
                f"Status changed from {old_status.value} to {new_status.value}" + 
                (f". Notes: {notes}" if notes else "")
            )
            
            return operation
    
    @staticmethod
    async def delete_operation(operation_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> bool:
        """Delete operation (soft delete by setting status to CANCELLED)"""
        async with AsyncSessionLocal() as session:
            operation = await session.get(Operation, operation_id)
            if not operation:
                return False
            
            # Only allow deletion of pending operations
            if operation.status not in [OperationStatus.PENDING, OperationStatus.ASSIGNED]:
                raise ValueError("Cannot delete operation that is already in progress")
            
            operation.status = OperationStatus.CANCELLED
            await session.commit()
            
            # Log cancellation
            await DatabaseOperations.log_operation_action(
                operation_id,
                user_id,
                "Operation Cancelled",
                "Operation cancelled by user"
            )
            
            return True
    
    @staticmethod
    async def get_operation_by_operation_id(operation_id_str: str) -> Optional[Operation]:
        """Get operation by operation ID string"""
        async with AsyncSessionLocal() as session:
            stmt = select(Operation).options(
                selectinload(Operation.client),
                selectinload(Operation.collector)
            ).where(Operation.operation_id == operation_id_str)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    # Operation logging
    @staticmethod
    async def log_operation_action(
        operation_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        action: str,
        details: Optional[str] = None
    ):
        """Log operation action"""
        async with AsyncSessionLocal() as session:
            log_entry = OperationLog(
                operation_id=operation_id,
                user_id=user_id,
                action=action,
                details=details
            )
            session.add(log_entry)
            await session.commit()
    
    @staticmethod
    async def get_operation_logs(operation_id: uuid.UUID) -> List[OperationLog]:
        """Get operation logs"""
        async with AsyncSessionLocal() as session:
            stmt = select(OperationLog).where(
                OperationLog.operation_id == operation_id
            ).order_by(desc(OperationLog.timestamp))
            result = await session.execute(stmt)
            return result.scalars().all()
    
    # Analytics and reporting
    @staticmethod
    async def get_operations_analytics(days: int = 30) -> Dict[str, Any]:
        """Get operations analytics for dashboard"""
        async with AsyncSessionLocal() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total operations in period
            total_ops_stmt = select(func.count(Operation.id)).where(
                Operation.created_at >= cutoff_date
            )
            total_ops = await session.scalar(total_ops_stmt)
            
            # Total volume
            total_volume_stmt = select(func.sum(Operation.amount_usd)).where(
                Operation.created_at >= cutoff_date
            )
            total_volume = await session.scalar(total_volume_stmt) or 0
            
            # Completed operations
            completed_ops_stmt = select(func.count(Operation.id)).where(
                Operation.created_at >= cutoff_date,
                Operation.status == OperationStatus.COMPLETED
            )
            completed_ops = await session.scalar(completed_ops_stmt)
            
            # Active operations
            active_ops_stmt = select(func.count(Operation.id)).where(
                Operation.status.in_([
                    OperationStatus.PENDING,
                    OperationStatus.ASSIGNED, 
                    OperationStatus.COLLECTING,
                    OperationStatus.COLLECTED,
                    OperationStatus.VALIDATED,
                    OperationStatus.FX_PROCESSING
                ])
            )
            active_ops = await session.scalar(active_ops_stmt)
            
            # Total commission
            total_commission_stmt = select(func.sum(Operation.commission_amount)).where(
                Operation.created_at >= cutoff_date,
                Operation.status == OperationStatus.COMPLETED
            )
            total_commission = await session.scalar(total_commission_stmt) or 0
            
            return {
                "total_operations": total_ops or 0,
                "total_volume": float(total_volume),
                "completed_operations": completed_ops or 0,
                "active_operations": active_ops or 0,
                "total_commission": float(total_commission),
                "completion_rate": (completed_ops / total_ops * 100) if total_ops > 0 else 0,
                "average_operation_size": float(total_volume / total_ops) if total_ops > 0 else 0
            }
    
    @staticmethod
    async def get_daily_volume_trend(days: int = 7) -> List[Dict[str, Any]]:
        """Get daily volume trend for charts"""
        async with AsyncSessionLocal() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get daily volumes
            stmt = select(
                func.date(Operation.created_at).label('date'),
                func.sum(Operation.amount_usd).label('volume'),
                func.count(Operation.id).label('count')
            ).where(
                Operation.created_at >= cutoff_date
            ).group_by(
                func.date(Operation.created_at)
            ).order_by(
                func.date(Operation.created_at)
            )
            
            result = await session.execute(stmt)
            return [
                {
                    "date": row.date,
                    "volume": float(row.volume or 0),
                    "count": row.count
                }
                for row in result
            ]

# Initialize database operations instance
db_ops = DatabaseOperations()