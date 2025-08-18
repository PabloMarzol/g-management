# streamlit_app.py - Main entry point for Streamlit Cloud
import sys
import os
from pathlib import Path

# Add alma directory to Python path
current_dir = Path(__file__).parent
alma_dir = current_dir / "alma"
sys.path.insert(0, str(alma_dir))

# Set up environment variables for cloud deployment
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")  # Fallback for cloud

try:
    # Import the main function from alma.py
    from alma import main
    
    # Run the main application
    if __name__ == "__main__":
        main()
    else:
        # When imported by Streamlit Cloud, just run main
        main()
        
except ImportError as e:
    import streamlit as st
    st.error(f"Import Error: {e}")
    st.error("Please check that all required files are present in the alma/ directory")
    st.stop()
except Exception as e:
    import streamlit as st
    st.error(f"Application Error: {e}")
    st.error("There was an error starting the application")
    st.stop()