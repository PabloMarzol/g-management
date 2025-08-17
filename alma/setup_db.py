# setup_db.py - Database setup script for ALMA
import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path to import our modules
sys.path.append(str(Path(__file__).parent))

from database import setup_database, engine
from sqlalchemy import text

async def check_database_connection():
    """Check if database connection is working"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Please check:")
        print("1. PostgreSQL is running")
        print("2. Database 'gmanagement' exists")
        print("3. Connection string is correct in .env file")
        return False

async def main():
    """Main setup function"""
    print("🏦 ALMA Database Setup")
    print("=" * 50)
    
    # Check database connection first
    if not await check_database_connection():
        return
    
    # Run database setup
    await setup_database()
    
    print("\n🎉 Database setup completed!")
    print("You can now run the Streamlit app:")
    print("streamlit run alma_app.py")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")