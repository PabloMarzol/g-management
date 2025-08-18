# test_alma_fixes.py - Test the fixed ALMA application
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

async def test_database_operations():
    """Test database operations to ensure they work correctly"""
    print("🧪 Testing ALMA Database Operations...")
    
    try:
        # Import the fixed modules
        from database import check_database_health, AsyncSessionLocal
        from crud import DatabaseOperations
        
        # Test database connection
        print("1. Testing database connection...")
        health_check = await check_database_health()
        if health_check:
            print("   ✅ Database connection successful")
        else:
            print("   ❌ Database connection failed")
            return False
        
        # Test database operations
        print("2. Testing database operations...")
        db_ops = DatabaseOperations()
        
        # Test get all operations
        operations = await db_ops.get_all_operations()
        print(f"   ✅ Retrieved {len(operations)} operations")
        
        # Test analytics
        analytics = await db_ops.get_operations_analytics()
        print(f"   ✅ Analytics data: {analytics}")
        
        print("🎉 All database tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all fixed files are in the alma/ directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🏦 ALMA Application Fix Test")
    print("=" * 40)
    
    try:
        # Run async tests
        result = asyncio.run(test_database_operations())
        
        if result:
            print("\n✅ All tests passed! Your fixes should work.")
            print("\nNext steps:")
            print("1. Replace your original files with the fixed versions")
            print("2. Run: streamlit run alma.py")
            print("3. Test the Dashboard, Operations List, and Analytics tabs")
        else:
            print("\n❌ Tests failed. Please check the error messages above.")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")

if __name__ == "__main__":
    main()