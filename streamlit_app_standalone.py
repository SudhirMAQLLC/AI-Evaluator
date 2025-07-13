import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="AI Code Evaluator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .score-high { color: #28a745; }
    .score-medium { color: #ffc107; }
    .score-low { color: #dc3545; }
    .status-completed { color: #28a745; }
    .status-processing { color: #ffc107; }
    .status-failed { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

def main():
    """Main dashboard function."""
    st.markdown('<h1 class="main-header">🤖 AI Code Evaluator</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "Upload & Evaluate"
    
    # Sidebar
    with st.sidebar:
        st.header("🔑 API Configuration")
        
        # Model Selection
        st.subheader("🤖 Model Selection")
        
        # Local Models Selection
        st.write("**Local Models (No API Key Required):**")
        if 'use_codebert' not in st.session_state:
            st.session_state.use_codebert = True
        st.session_state.use_codebert = st.checkbox("🧠 Enhanced Task-Specific Evaluator", value=st.session_state.use_codebert, help="Advanced evaluation using best tools for each task (Fast)")
        
        if 'use_sqlcoder' not in st.session_state:
            st.session_state.use_sqlcoder = False
        st.session_state.use_sqlcoder = st.checkbox("🧠 SQLCoder Multi-Model", value=st.session_state.use_sqlcoder, help="Advanced SQL evaluation using multiple models")
        
        # API Models
        st.write("**API Models (Require API Keys):**")
        openai_key = st.text_input("OpenAI API Key", type="password", key="openai_api_key")
        google_key = st.text_input("Google Gemini API Key", type="password", key="google_api_key")
        
        # API Model Selection
        if 'use_openai' not in st.session_state:
            st.session_state.use_openai = False
        st.session_state.use_openai = st.checkbox("🤖 OpenAI GPT-4", value=st.session_state.use_openai, help="Advanced AI evaluation using OpenAI's GPT-4 model")
        
        if 'use_gemini' not in st.session_state:
            st.session_state.use_gemini = False
        st.session_state.use_gemini = st.checkbox("🤖 Google Gemini", value=st.session_state.use_gemini, help="Advanced AI evaluation using Google's Gemini model")
        
        st.markdown("---")
        st.header("Navigation")
        
        page = st.selectbox(
            "Choose a page",
            ["Upload & Evaluate", "Results Dashboard", "Statistics", "API Documentation"],
            index=["Upload & Evaluate", "Results Dashboard", "Statistics", "API Documentation"].index(st.session_state.page)
        )
        
        # Update session state when page changes
        if page != st.session_state.page:
            st.session_state.page = page
            st.rerun()
    
    # Page routing
    if st.session_state.page == "Upload & Evaluate":
        upload_page()
    elif st.session_state.page == "Results Dashboard":
        results_page()
    elif st.session_state.page == "Statistics":
        statistics_page()
    elif st.session_state.page == "API Documentation":
        api_docs_page()

def upload_page():
    """File upload and evaluation page."""
    st.header("📁 Upload & Evaluate")
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["📁 Upload Files", "📝 Paste SQL Code"])
    
    with tab1:
        # File upload section
        st.subheader("Upload Notebooks")
        
        uploaded_file = st.file_uploader(
            "Choose a ZIP file containing Jupyter notebooks",
            type=['zip'],
            help="Upload a ZIP file containing .ipynb files or other code files"
        )
        
        if uploaded_file is not None:
            st.info("File upload functionality will be available when backend is running")
    
    with tab2:
        # Direct SQL code input section
        st.subheader("Paste SQL Code")
        
        sql_code = st.text_area(
            "Paste your SQL code here:",
            height=200,
            placeholder="SELECT * FROM users WHERE active = true;",
            help="Paste your SQL code directly for evaluation"
        )
        
        if sql_code and st.button("🚀 Evaluate SQL Code", type="primary"):
            st.info("SQL evaluation functionality will be available when backend is running")
    
    # Recent evaluations
    st.subheader("🕒 Recent Evaluations")
    st.info("Recent evaluations will be displayed here when backend is running")

def results_page():
    """Results display page."""
    st.header("📊 Results Dashboard")
    st.info("Evaluation results will be displayed here when backend is running")

def statistics_page():
    """Statistics page."""
    st.header("📈 Statistics")
    st.info("Statistics will be displayed here when backend is running")

def api_docs_page():
    """API documentation page."""
    st.header("📚 API Documentation")
    
    st.markdown("""
    ## API Endpoints
    
    ### Health Check
    - **GET** `/api/v1/health`
    - Returns the health status of the API
    
    ### Evaluate Code
    - **POST** `/api/v1/evaluate`
    - Evaluates uploaded code files
    
    ### Get Evaluation Results
    - **GET** `/api/v1/evaluate/{evaluation_id}`
    - Retrieves evaluation results by ID
    
    ## Usage
    
    The AI Code Evaluator provides comprehensive code analysis using multiple AI models:
    
    ### Local Models (No API Key Required)
    - **Enhanced Task-Specific Evaluator**: Advanced evaluation using best tools for each task
    - **SQLCoder Multi-Model**: Advanced SQL evaluation using multiple models
    
    ### API Models (Require API Keys)
    - **OpenAI GPT-4**: Advanced AI evaluation using OpenAI's GPT-4 model
    - **Google Gemini**: Advanced AI evaluation using Google's Gemini model
    
    ## Features
    
    - 📁 **File Upload**: Upload ZIP files containing Jupyter notebooks
    - 📝 **Direct Input**: Paste SQL code directly for evaluation
    - 📊 **Real-time Results**: View evaluation progress and results
    - 📈 **Statistics**: Track evaluation metrics and performance
    - 🔄 **Multiple Models**: Choose from various AI models for evaluation
    """)

if __name__ == "__main__":
    main() 