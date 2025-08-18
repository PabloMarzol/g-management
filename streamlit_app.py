# streamlit_app.py - Debug version for Streamlit Cloud
import sys
import os
from pathlib import Path
import streamlit as st

# Debug: Show environment info
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Debug: Check file structure
current_dir = Path(__file__).parent
print(f"Current dir: {current_dir}")
print(f"Files in current dir: {list(current_dir.iterdir())}")

alma_dir = current_dir / "alma"
print(f"Alma dir exists: {alma_dir.exists()}")
if alma_dir.exists():
    print(f"Files in alma dir: {list(alma_dir.iterdir())}")

# Add alma directory to Python path
sys.path.insert(0, str(alma_dir))

# Set up environment variables for cloud deployment
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")

# Simple Streamlit test first
st.title("🏦 ALMA - Debug Mode")
st.write("If you can see this, Streamlit is working!")
st.write(f"Python version: {sys.version}")
st.write(f"Current directory: {os.getcwd()}")
st.write(f"Alma directory exists: {alma_dir.exists()}")

try:
    # Try to import alma
    st.write("Attempting to import alma...")
    import alma
    st.success("✅ Successfully imported alma module")
    
    # Try to get the main function
    if hasattr(alma, 'main'):
        st.success("✅ Found main function in alma")
        # Don't run it yet, just test import
    else:
        st.error("❌ No main function found in alma")
        st.write(f"Available attributes: {dir(alma)}")
        
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.write("This is likely the issue!")
except Exception as e:
    st.error(f"❌ Other Error: {e}")

# Test direct file import
try:
    st.write("Attempting direct file import...")
    alma_file = alma_dir / "alma.py"
    if alma_file.exists():
        st.success(f"✅ alma.py file exists at {alma_file}")
    else:
        st.error(f"❌ alma.py file not found at {alma_file}")
        
except Exception as e:
    st.error(f"❌ File check error: {e}")

st.write("---")
st.write("**Next steps:** Once this debug info shows up on Streamlit Cloud, we'll know exactly what's wrong!")