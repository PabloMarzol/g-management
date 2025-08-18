from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
import uuid

from database import (
    User, Client, Operation, OperationLog,
    UserRole, ClientType, OperationStatus,
    SessionLocal
)
from config import calculate_commission

class DatabaseOperations:
    """Simple synchronous database operations"""
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user"""
        with SessionLocal() as session:
            user = session.query(User).filter(
                User.username == username,
                User.password_hash == password,
                User.is_active == True
            ).first()
            
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
            
            return user
    
    def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        with SessionLocal() as session:
            return session.query(User).filter(
                User.role == role,
                User.is_active == True
            ).order_by(User.full_name).all()
    
    def get_all_clients(self) -> List[Client]:
        """Get all clients"""
        with SessionLocal() as session:
            return session.query(Client).order_by(Client.name).all()
    
    def get_all_operations(self) -> List[Operation]:
        """Get all operations"""
        with SessionLocal() as session:
            return session.query(Operation).options(
                selectinload(Operation.client),
                selectinload(Operation.collector)
            ).order_by(desc(Operation.created_at)).all()
    
    def get_operations_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get operations analytics"""
        with SessionLocal() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total operations
            total_ops = session.query(func.count(Operation.id)).filter(
                Operation.created_at >= cutoff_date
            ).scalar() or 0
            
            # Total volume
            total_volume = session.query(func.sum(Operation.amount_usd)).filter(
                Operation.created_at >= cutoff_date
            ).scalar() or 0
            
            # Completed operations
            completed_ops = session.query(func.count(Operation.id)).filter(
                Operation.created_at >= cutoff_date,
                Operation.status == OperationStatus.COMPLETED
            ).scalar() or 0
            
            # Active operations
            active_ops = session.query(func.count(Operation.id)).filter(
                Operation.status.in_([
                    OperationStatus.PENDING,
                    OperationStatus.ASSIGNED,
                    OperationStatus.COLLECTING,
                    OperationStatus.COLLECTED,
                    OperationStatus.VALIDATED,
                    OperationStatus.FX_PROCESSING
                ])
            ).scalar() or 0
            
            # Total commission
            total_commission = session.query(func.sum(Operation.commission_amount)).filter(
                Operation.created_at >= cutoff_date,
                Operation.status == OperationStatus.COMPLETED
            ).scalar() or 0
            
            return {
                "total_operations": total_ops,
                "total_volume": float(total_volume),
                "completed_operations": completed_ops,
                "active_operations": active_ops,
                "total_commission": float(total_commission),
                "completion_rate": (completed_ops / total_ops * 100) if total_ops > 0 else 0,
                "average_operation_size": float(total_volume / total_ops) if total_ops > 0 else 0
            }

# Create global instance
db_ops = DatabaseOperations()