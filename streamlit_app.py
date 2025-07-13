import streamlit as st
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Import the dashboard
from app.dashboard import main

if __name__ == "__main__":
    main()
