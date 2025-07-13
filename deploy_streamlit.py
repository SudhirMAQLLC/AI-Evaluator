#!/usr/bin/env python3
"""
Streamlit Deployment Script
This script helps deploy the Streamlit app to Streamlit Cloud
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_streamlit_installation():
    """Check if Streamlit is installed."""
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__} is installed")
        return True
    except ImportError:
        print("❌ Streamlit is not installed")
        return False

def create_streamlit_app_file():
    """Create a main Streamlit app file for deployment."""
    app_content = '''import streamlit as st
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Import the dashboard
from app.dashboard import main

if __name__ == "__main__":
    main()
'''
    
    with open("streamlit_app.py", "w") as f:
        f.write(app_content)
    
    print("✅ Created streamlit_app.py for deployment")

def create_packages_file():
    """Create packages.txt for system dependencies."""
    packages = [
        "python3-dev",
        "build-essential",
        "libmagic1"
    ]
    
    with open("packages.txt", "w") as f:
        for package in packages:
            f.write(f"{package}\n")
    
    print("✅ Created packages.txt")

def create_secrets_template():
    """Create a template for Streamlit secrets."""
    secrets_template = {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "GOOGLE_API_KEY": "your_google_api_key_here",
        "ANTHROPIC_API_KEY": "your_anthropic_api_key_here"
    }
    
    with open("secrets_template.json", "w") as f:
        json.dump(secrets_template, f, indent=2)
    
    print("✅ Created secrets_template.json")
    print("📝 Copy this to Streamlit Cloud secrets management")

def main():
    """Main deployment setup function."""
    print("🚀 Setting up Streamlit deployment...")
    
    # Check Streamlit installation
    if not check_streamlit_installation():
        print("Please install Streamlit: pip install streamlit")
        return
    
    # Create deployment files
    create_streamlit_app_file()
    create_packages_file()
    create_secrets_template()
    
    print("\n📋 Deployment Setup Complete!")
    print("\nNext steps:")
    print("1. Go to https://share.streamlit.io/")
    print("2. Connect your GitHub repository")
    print("3. Set the main file path to: streamlit_app.py")
    print("4. Add your API keys in the secrets management")
    print("5. Deploy!")
    
    print("\n🔧 Local testing:")
    print("streamlit run streamlit_app.py")

if __name__ == "__main__":
    main() 