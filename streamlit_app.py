# streamlit_app.py
import sys
from pathlib import Path

# Add alma directory to Python path
sys.path.append(str(Path(__file__).parent / "alma"))

# Import and run the main app
from alma.alma import main

if __name__ == "__main__":
    main()