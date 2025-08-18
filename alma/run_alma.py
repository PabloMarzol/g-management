
import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        "streamlit",
        "pandas", 
        "plotly",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Installing missing packages...")
        
        for package in missing_packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        print("✅ All packages installed successfully!")
    else:
        print("✅ All required packages are installed!")

def setup_environment():
    """Setup environment and configuration"""
    print("🔧 Setting up ALMA environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# ALMA Configuration
DATABASE_URL=postgresql://localhost/gmanagement
SECRET_KEY=dev-secret-key-change-in-production
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
"""
        with open(".env", "w") as f:
            f.write(env_content)
        print("📄 Created .env configuration file")
    
    # Create streamlit config directory
    streamlit_dir = Path(".streamlit")
    streamlit_dir.mkdir(exist_ok=True)
    
    # Create streamlit config
    config_content = """[general]
dataFrameSerialization = "legacy"

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
headless = false
port = 8501
enableCORS = false
enableXsrfProtection = false
"""
    
    config_file = streamlit_dir / "config.toml"
    with open(config_file, "w") as f:
        f.write(config_content)
    
    print("⚙️ Streamlit configuration created")

def run_application():
    """Run the ALMA Streamlit application"""
    print("🚀 Starting ALMA Financial Exchange Control Platform...")
    print("📱 The application will open in your default web browser")
    print("🔗 URL: http://localhost:8501")
    print("\n" + "="*50)
    print("ALMA - Cash to USDT Exchange Control Platform")
    print("="*50)
    print("🔐 Login Credentials (for demo):")
    print("   Username: admin")
    print("   Password: admin123")
    print("   Role: Administrator")
    print("\n   Username: fx_provider") 
    print("   Password: fx123")
    print("   Role: FX Provider")
    print("="*50)
    print("\n⏹️  To stop the application, press Ctrl+C")
    print("\n")
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "alma.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 ALMA application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")

def main():
    """Main startup function"""
    print("🏦 ALMA - Financial Exchange Control Platform")
    print("=" * 50)
    
    try:
        # Check and install requirements
        check_requirements()
        
        # Setup environment
        setup_environment()
        
        # Run the application
        run_application()
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()