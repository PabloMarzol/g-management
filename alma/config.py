
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Application settings
    APP_NAME = "ALMA - Financial Exchange Control Platform"
    APP_VERSION = "1.0.0"
    
    # Database settings (for future backend integration)
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/alma_db")
    
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # API settings (for future integrations)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
    
    # Business settings
    COMMISSION_RATES = {
        "regular": {
            "low": 0.07,    # < $5,000
            "medium": 0.06, # $5,000 - $20,000
            "high": 0.05    # > $20,000
        },
        "frequent": {
            "low": 0.06,
            "medium": 0.05,
            "high": 0.04
        }
    }
    
    FX_PROVIDER_COMMISSION = 0.015  # 1.5%
    
    # Operation limits
    MAX_OPERATION_AMOUNT = 50000
    MIN_OPERATION_AMOUNT = 100
    
    # Status definitions
    OPERATION_STATUSES = [
        "Pending",
        "Assigned", 
        "Collecting",
        "Collected",
        "Validated",
        "Delivered to FX",
        "FX Processing",
        "Completed",
        "Cancelled",
        "Error"
    ]
    
    # Role definitions
    USER_ROLES = {
        "admin": "Administrator",
        "fx_provider": "FX Provider", 
        "collector": "Collector"
    }

# Utility functions
def calculate_commission(amount: float, client_type: str = "regular") -> dict:
    """Calculate commission based on amount and client type"""
    config = Config()
    
    if amount < 5000:
        rate = config.COMMISSION_RATES[client_type]["low"]
    elif amount <= 20000:
        rate = config.COMMISSION_RATES[client_type]["medium"]
    else:
        rate = config.COMMISSION_RATES[client_type]["high"]
    
    commission = amount * rate
    fx_commission = amount * config.FX_PROVIDER_COMMISSION
    net_amount = amount - commission
    
    return {
        "gross_amount": amount,
        "commission_rate": rate,
        "commission_amount": commission,
        "fx_commission": fx_commission,
        "net_amount": net_amount
    }

def validate_operation_data(data: dict) -> list:
    """Validate operation data and return list of errors"""
    errors = []
    
    if not data.get("client_name"):
        errors.append("Client name is required")
    
    if not data.get("amount") or data["amount"] < Config.MIN_OPERATION_AMOUNT:
        errors.append(f"Amount must be at least ${Config.MIN_OPERATION_AMOUNT}")
    
    if data.get("amount", 0) > Config.MAX_OPERATION_AMOUNT:
        errors.append(f"Amount cannot exceed ${Config.MAX_OPERATION_AMOUNT}")
    
    if not data.get("usdt_wallet"):
        errors.append("USDT wallet address is required")
    
    if not data.get("pickup_address"):
        errors.append("Pickup address is required")
    
    return errors