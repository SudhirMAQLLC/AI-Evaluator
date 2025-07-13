"""
Streamlit Dashboard for AI Code Evaluator

Provides an interactive web interface for:
- File upload and evaluation
- Real-time status monitoring
- Results visualization
- Report generation
"""

import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from datetime import datetime
from typing import Dict, List, Optional

# Try to import anthropic for Grok testing
try:
    import anthropic
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

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
    
    # Initialize session state for API keys
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    if 'google_api_key' not in st.session_state:
        st.session_state.google_api_key = ""
    if 'grok_api_key' not in st.session_state:
        st.session_state.grok_api_key = ""
    
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
        st.session_state.use_sqlcoder = st.checkbox("🧠 SQLCoder Multi-Model", value=st.session_state.use_sqlcoder, help="Advanced SQL evaluation using multiple models (StarCoder2, CodeT5+, SecurityBERT, SQLCoder)")
        
        
        
        # API Models
        st.write("**API Models (Require API Keys):**")
        openai_key = st.text_input("OpenAI API Key", type="password", key="openai_api_key")
        google_key = st.text_input("Google Gemini API Key", type="password", key="google_api_key")
        grok_key = st.text_input("Grok API Key", type="password", key="grok_api_key")
        
        # API Model Selection
        if 'use_openai' not in st.session_state:
            st.session_state.use_openai = False
        st.session_state.use_openai = st.checkbox("🤖 OpenAI GPT-4", value=st.session_state.use_openai, help="Advanced AI evaluation using OpenAI's GPT-4 model")
        
        if 'use_gemini' not in st.session_state:
            st.session_state.use_gemini = False
        st.session_state.use_gemini = st.checkbox("🤖 Google Gemini", value=st.session_state.use_gemini, help="Advanced AI evaluation using Google's Gemini model")
        
        if 'use_grok' not in st.session_state:
            st.session_state.use_grok = False
        st.session_state.use_grok = st.checkbox("🤖 Grok (NEW!)", value=st.session_state.use_grok, help="Advanced AI evaluation using Grok model powered by Anthropic")
        
        # Show warnings for missing API keys
        if st.session_state.use_grok and not st.session_state.grok_api_key:
            st.warning("⚠️ Grok selected but no API key provided")
        
        if st.button("Test API Keys"):
            test_api_keys_sync(openai_key, google_key, grok_key)
        
        st.markdown("---")
        st.header("Navigation")
        
        # Initialize page in session state
        if 'page' not in st.session_state:
            st.session_state.page = "Upload & Evaluate"
        
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
    
    # Auto-navigate to results if evaluation ID is set
    if st.session_state.get("current_evaluation_id"):
        st.session_state.page = "Results Dashboard"
        # Clear the evaluation ID after navigation
        evaluation_id = st.session_state.current_evaluation_id
        del st.session_state.current_evaluation_id
        # Auto-load results
        load_evaluation_results(evaluation_id)


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
            handle_file_upload(uploaded_file)
    
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
            handle_sql_code_evaluation(sql_code)
    
    # Recent evaluations
    st.subheader("🕒 Recent Evaluations")
    show_recent_evaluations()


def handle_file_upload(uploaded_file):
    """Handle file upload evaluation."""
    # Display file info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("File Name", uploaded_file.name)
    with col2:
        st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
    with col3:
        st.metric("File Type", uploaded_file.type or "application/zip")
    
    # Show warnings for API models without keys
    if st.session_state.use_openai and not st.session_state.openai_api_key:
        st.warning("⚠️ OpenAI GPT-4 selected but no API key provided")
    if st.session_state.use_gemini and not st.session_state.google_api_key:
        st.warning("⚠️ Google Gemini selected but no API key provided")
    if st.session_state.use_grok and not st.session_state.grok_api_key:
        st.warning("⚠️ Grok selected but no API key provided")
    
    # Show fallback information
    if st.session_state.use_openai or st.session_state.use_gemini or st.session_state.use_grok:
        st.info("💡 **Fallback Protection:** If API models fail (quota exceeded, rate limits, etc.), the system will automatically use local models for evaluation.")

    # Upload button
    if st.button("🚀 Start Evaluation", type="primary"):
        start_evaluation_with_file(uploaded_file)


def handle_sql_code_evaluation(sql_code):
    """Handle direct SQL code evaluation."""
    # Display code info
    st.subheader("📝 SQL Code Analysis")
    
    # Show the code
    st.code(sql_code, language="sql")
    
    # Show warnings for API models without keys
    if st.session_state.use_openai and not st.session_state.openai_api_key:
        st.warning("⚠️ OpenAI GPT-4 selected but no API key provided")
    if st.session_state.use_gemini and not st.session_state.google_api_key:
        st.warning("⚠️ Google Gemini selected but no API key provided")
    if st.session_state.use_grok and not st.session_state.grok_api_key:
        st.warning("⚠️ Grok selected but no API key provided")
    
    # Show fallback information
    if st.session_state.use_openai or st.session_state.use_gemini or st.session_state.use_grok:
        st.info("💡 **Fallback Protection:** If API models fail (quota exceeded, rate limits, etc.), the system will automatically use local models for evaluation.")
    
    # Start evaluation
    start_evaluation_with_sql_code(sql_code)


def start_evaluation_with_file(uploaded_file):
    """Start evaluation with uploaded file."""
    # Check which models are selected
    selected_models = []
    
    if st.session_state.use_codebert:
        selected_models.append("🧠 Enhanced Task-Specific Evaluator")
    
    if st.session_state.use_sqlcoder:
        selected_models.append("🧠 SQLCoder Multi-Model")
    
    if st.session_state.use_openai and st.session_state.openai_api_key:
        selected_models.append("🤖 OpenAI GPT-4")
    if st.session_state.use_gemini and st.session_state.google_api_key:
        selected_models.append("🤖 Google Gemini")
    if st.session_state.use_grok and st.session_state.grok_api_key:
        selected_models.append("🤖 Grok")
    
    if not selected_models:
        st.error("❌ Please select at least one model for evaluation!")
        return
    
    # Show which models will be used
    st.info("🤖 **Models that will be used for evaluation:**")
    for model in selected_models:
        st.write(f"✅ {model}")

    with st.spinner("Uploading and starting evaluation..."):
        try:
            # Prepare the evaluation request
            files = {"file": uploaded_file}
            data = {
                "use_codebert": st.session_state.use_codebert,
                "use_sqlcoder": st.session_state.use_sqlcoder,
                "use_openai": st.session_state.use_openai,
                "use_gemini": st.session_state.use_gemini,
                "use_grok": st.session_state.use_grok
            }
            
            # Add API keys if provided
            if st.session_state.openai_api_key:
                data["openai_api_key"] = st.session_state.openai_api_key
            if st.session_state.google_api_key:
                data["google_api_key"] = st.session_state.google_api_key
            if st.session_state.grok_api_key:
                data["grok_api_key"] = st.session_state.grok_api_key
            
            # Make the API request
            response = requests.post(
                f"{API_BASE_URL}/evaluate",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                evaluation_id = result["evaluation_id"]
                
                st.success(f"✅ Evaluation started successfully!")
                st.info(f"**Evaluation ID:** {evaluation_id}")
                
                # Store evaluation ID in session state
                st.session_state.current_evaluation_id = evaluation_id
                st.session_state.evaluation_status = "pending"
                
                # Start progress monitoring
                st.subheader("📊 Evaluation Progress")
                progress_monitor(evaluation_id)
                
            else:
                st.error(f"❌ Failed to start evaluation: {response.text}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Connection error: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")


def start_evaluation_with_sql_code(sql_code):
    """Start evaluation with direct SQL code."""
    # Check which models are selected
    selected_models = []
    
    if st.session_state.use_codebert:
        selected_models.append("🧠 Enhanced Task-Specific Evaluator")
    
    if st.session_state.use_sqlcoder:
        selected_models.append("🧠 SQLCoder Multi-Model")
    
    if st.session_state.use_openai and st.session_state.openai_api_key:
        selected_models.append("🤖 OpenAI GPT-4")
    if st.session_state.use_gemini and st.session_state.google_api_key:
        selected_models.append("🤖 Google Gemini")
    if st.session_state.use_grok and st.session_state.grok_api_key:
        selected_models.append("🤖 Grok")
    
    if not selected_models:
        st.error("❌ Please select at least one model for evaluation!")
        return
    
    # Show which models will be used
    st.info("🤖 **Models that will be used for evaluation:**")
    for model in selected_models:
        st.write(f"✅ {model}")

    with st.spinner("Evaluating SQL code..."):
        try:
            # Create a temporary file with the SQL code
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                temp_file.write(sql_code)
                temp_file_path = temp_file.name
            
            try:
                # Prepare the evaluation request
                with open(temp_file_path, 'rb') as f:
                    files = {"file": ("sql_code.sql", f, "text/plain")}
                    data = {
                        "use_codebert": st.session_state.use_codebert,
                        "use_sqlcoder": st.session_state.use_sqlcoder,
                        "use_openai": st.session_state.use_openai,
                        "use_gemini": st.session_state.use_gemini,
                        "use_grok": st.session_state.use_grok
                    }
                    
                    # Add API keys if provided
                    if st.session_state.openai_api_key:
                        data["openai_api_key"] = st.session_state.openai_api_key
                    if st.session_state.google_api_key:
                        data["google_api_key"] = st.session_state.google_api_key
                    if st.session_state.grok_api_key:
                        data["grok_api_key"] = st.session_state.grok_api_key
                    
                    # Make the API request
                    response = requests.post(
                        f"{API_BASE_URL}/evaluate",
                        files=files,
                        data=data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        evaluation_id = result["evaluation_id"]
                        
                        st.success(f"✅ Evaluation started successfully!")
                        st.info(f"**Evaluation ID:** {evaluation_id}")
                        
                        # Store evaluation ID in session state
                        st.session_state.current_evaluation_id = evaluation_id
                        st.session_state.evaluation_status = "pending"
                        
                        # Start progress monitoring
                        st.subheader("📊 Evaluation Progress")
                        progress_monitor(evaluation_id)
                        
                    else:
                        st.error(f"❌ Failed to start evaluation: {response.text}")
                        
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Connection error: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")


def progress_monitor(evaluation_id: str):
    """Monitor evaluation progress with enhanced visual feedback."""
    # Create containers for different types of feedback
    progress_container = st.container()
    status_container = st.container()
    details_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        progress_text = st.empty()
    
    with status_container:
        status_text = st.empty()
        time_text = st.empty()
    
    with details_container:
        details_text = st.empty()
    
    start_time = time.time()
    last_progress = 0
    
    while True:
        try:
            response = requests.get(f"{API_BASE_URL}/evaluations/{evaluation_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                
                # Update progress
                progress = status_data.get("progress", 0)
                status = status_data.get("status", "unknown")
                total_cells = status_data.get("total_cells", 0)
                processed_cells = status_data.get("processed_cells", 0)
                
                # Update progress bar with smooth animation
                if progress > last_progress:
                    # For very fast completions, just set the final progress
                    if progress >= 100:
                        progress_bar.progress(1.0)
                        last_progress = 100
                    else:
                        # Smooth animation for partial progress
                        for i in range(last_progress, int(progress) + 1):
                            progress_bar.progress(i / 100)
                            time.sleep(0.1)
                        last_progress = int(progress)
                
                # Update progress text
                progress_text.markdown(f"**Progress: {progress:.1f}%**")
                
                # Update status with emoji
                status_emoji = {
                    "pending": "⏳",
                    "processing": "🔄", 
                    "completed": "✅",
                    "failed": "❌"
                }.get(status, "❓")
                
                status_text.markdown(f"{status_emoji} **Status: {status.upper()}**")
                
                # Show timing information
                elapsed_time = time.time() - start_time
                time_text.markdown(f"⏱️ **Elapsed Time: {elapsed_time:.1f}s**")
                
                # Show detailed progress in a cleaner way
                if total_cells > 0:
                    details_text.markdown(f"📊 **Processing: {processed_cells} of {total_cells} code sections**")
                
                # Check completion
                if status == "completed":
                    status_text.success("🎉 **Evaluation Completed Successfully!**")
                    time_text.success(f"⏱️ **Total Time: {elapsed_time:.1f}s**")
                    st.balloons()
                    
                    # Show completion message
                    st.success("🎉 **Evaluation Complete!**")
                    st.info("📋 **What's Next:**")
                    st.write("• 📊 View detailed results and insights")
                    st.write("• 📥 Download your evaluation report")
                    st.write("• 💡 Review improvement suggestions")
                    
                    # Add a direct link to results
                    if st.button("📊 View Results Now", type="primary"):
                        st.session_state.current_evaluation_id = evaluation_id
                        st.session_state.page = "Results Dashboard"
                        st.rerun()
                    break
                    
                elif status == "failed":
                    status_text.error("💥 **Evaluation Failed**")
                    error_msg = status_data.get("error_message", "An unexpected error occurred")
                    st.error(f"❌ **Issue:** {error_msg}")
                    st.info("💡 **Try again or contact support if the problem persists**")
                    break
                
                time.sleep(1)  # Poll every 1 second for more responsive updates
            else:
                st.error("❌ **Unable to check evaluation status**")
                st.info("💡 **Please try refreshing the page**")
                break
                
        except Exception as e:
            st.error("❌ **Connection issue**")
            st.info("💡 **Please check your connection and try again**")
            break


def show_recent_evaluations():
    """Show recent evaluations."""
    try:
        response = requests.get(f"{API_BASE_URL}/evaluations")
        if response.status_code == 200:
            evaluations = response.json()
            
            if evaluations:
                # Create DataFrame
                df = pd.DataFrame(evaluations)
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['completed_at'] = pd.to_datetime(df['completed_at'])
                
                # Display in a clean, user-friendly format
                for _, eval_data in df.head(5).iterrows():
                    # Create a clean status display
                    status_display = eval_data['status'].title()
                    if eval_data['status'] == 'completed':
                        status_icon = "✅"
                        status_color = "success"
                    elif eval_data['status'] == 'processing':
                        status_icon = "⏳"
                        status_color = "info"
                    elif eval_data['status'] == 'failed':
                        status_icon = "❌"
                        status_color = "error"
                    else:
                        status_icon = "⏸️"
                        status_color = "warning"
                    
                    # Create a clean card-like display
                    with st.container():
                        st.markdown(f"""
                        <div style="
                            border: 1px solid #e0e0e0;
                            border-radius: 10px;
                            padding: 15px;
                            margin: 10px 0;
                            background-color: #fafafa;
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h4 style="margin: 0; color: #333;">📄 {eval_data['filename']}</h4>
                                    <p style="margin: 5px 0; color: #666;">{status_icon} {status_display}</p>
                                </div>
                                <div style="text-align: right;">
                                    <p style="margin: 5px 0; color: #666;">📅 {eval_data['created_at'].strftime('%Y-%m-%d %H:%M')}</p>
                                    {f'<p style="margin: 5px 0; color: #666;">📊 {eval_data["progress"]:.1f}% Complete</p>' if eval_data['status'] != 'completed' else ''}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add action buttons
                        if eval_data['status'] == 'completed':
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                if st.button("📊 View Results", key=f"view_{eval_data['evaluation_id']}", type="primary"):
                                    st.session_state.current_evaluation_id = eval_data['evaluation_id']
                                    st.session_state.page = "Results Dashboard"
                                    st.rerun()
                            with col2:
                                st.write("")
                        elif eval_data['status'] == 'processing':
                            st.info("🔄 Evaluation in progress...")
                        elif eval_data['status'] == 'failed':
                            st.error("💥 Evaluation failed")
                        
                        st.markdown("---")
            else:
                st.info("No evaluations found")
        else:
            st.error("Failed to fetch evaluations")
            
    except Exception as e:
        st.error(f"Error fetching evaluations: {str(e)}")


def results_page():
    """Results dashboard page."""
    st.header("📊 Results Dashboard")
    
    # Check if we have an evaluation ID to auto-load
    auto_load_id = st.session_state.get("current_evaluation_id")
    
    # Auto-load results if we have an evaluation ID
    if auto_load_id:
        load_evaluation_results(auto_load_id)
        # Clear the auto-load ID after loading
        del st.session_state.current_evaluation_id
    else:
        # Show a clean message when no results are loaded
        st.markdown("""
        <div style="
            text-align: center;
            padding: 40px;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin: 20px 0;
        ">
            <h3 style="color: #6c757d; margin-bottom: 20px;">📊 No Results Loaded</h3>
            <p style="color: #6c757d; margin-bottom: 20px;">
                To view evaluation results, go back to the Upload page and click "View Results" 
                on any completed evaluation.
            </p>
            <div style="margin-top: 20px;">
                <a href="#" onclick="window.parent.postMessage({type: 'streamlit:setComponentValue', key: 'nav_button', value: 'Upload & Evaluate'}, '*')">
                    ← Back to Upload
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add a simple back button
        if st.button("← Back to Upload", type="secondary"):
            st.session_state.page = "Upload & Evaluate"
            st.rerun()


def load_evaluation_results(evaluation_id: str):
    """Load and display evaluation results."""
    try:
        response = requests.get(f"{API_BASE_URL}/evaluations/{evaluation_id}/results")
        if response.status_code == 200:
            results = response.json()
            display_evaluation_results(results)
        else:
            st.error(f"Failed to load results: {response.json().get('detail', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"Error loading results: {str(e)}")


def display_evaluation_results(results: Dict):
    """Display evaluation results with visualizations."""
    # Add navigation buttons
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Upload"):
            st.session_state.page = "Upload & Evaluate"
            st.rerun()
    
    st.subheader(f"📋 Evaluation Results: {results['filename']}")
    
    # Project overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        project_score = results.get('project_score')
        if project_score is not None:
            st.metric("Project Score", f"{project_score:.1f}/10")
        else:
            st.metric("Project Score", "N/A")
    with col2:
        st.metric("Total Files", len(results.get('files', [])))
    with col3:
        st.metric("Total Cells", results.get('total_cells', 0))
    with col4:
        if results.get('completed_at') and results.get('created_at'):
            try:
                from datetime import datetime
                created = datetime.fromisoformat(results['created_at'].replace('Z', '+00:00'))
                completed = datetime.fromisoformat(results['completed_at'].replace('Z', '+00:00'))
                duration = completed - created
                st.metric("Processing Time", f"{duration.total_seconds():.1f}s")
            except:
                st.metric("Processing Time", "N/A")
        else:
            st.metric("Processing Time", "N/A")
    
    # Files overview
    st.subheader("📁 Files Overview")
    
    if results['files']:
        # Create files summary
        files_data = []
        for file_data in results['files']:
            files_data.append({
                'Filename': file_data['filename'],
                'Score': file_data['overall_score'],
                'Cells': file_data['cell_count'],
                'Size (KB)': file_data['file_size'] / 1024
            })
        
        files_df = pd.DataFrame(files_data)
        
        # Files score chart
        # Filter out None scores for the chart
        valid_files_df = files_df[files_df['Score'].notna()]
        if not valid_files_df.empty:
            fig = px.bar(
                valid_files_df, 
                x='Filename', 
                y='Score',
                title="File Scores",
                color='Score',
                color_continuous_scale='RdYlGn'
            )
        else:
            st.warning("No valid scores available for chart display")
            return
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, key="files_score_chart")
        
        # Detailed file analysis
        for file_data in results['files']:
            overall_score = file_data.get('overall_score')
            if overall_score is not None:
                score_display = f"{overall_score:.1f}"
            else:
                score_display = "N/A"
            with st.expander(f"📄 {file_data['filename']} - Score: {score_display}"):
                display_file_details(file_data)
    
    # Model Comparison
    st.subheader("🤖 Model Comparison")
    
    # Collect all model scores for comparison
    all_model_scores = {}
    for file_data in results['files']:
        for cell in file_data['cells']:
            if cell['feedback']:
                for model, feedback in cell['feedback'].items():
                    if model not in all_model_scores:
                        all_model_scores[model] = []
                    if feedback.get('scores'):
                        all_model_scores[model].append(feedback['scores'])
    
    if all_model_scores:
        # Calculate average scores for each model
        model_averages = {}
        for model, scores_list in all_model_scores.items():
            if scores_list:
                avg_scores = {}
                for criterion in ['correctness', 'efficiency', 'readability', 'scalability', 'security', 'modularity', 'documentation', 'best_practices', 'error_handling']:
                    values = [score.get(criterion, 5.0) for score in scores_list if score.get(criterion)]
                    avg_scores[criterion] = sum(values) / len(values) if values else 5.0
                model_averages[model] = avg_scores
        
        # Display model comparison chart
        if model_averages:
            model_names = {
                'enhanced': 'Enhanced Task-Specific Evaluator',
                
                'openai': 'OpenAI GPT-4',
                'gemini': 'Google Gemini'
            }
            
            # Create comparison dataframe
            comparison_data = []
            for model, scores in model_averages.items():
                for criterion, score in scores.items():
                    comparison_data.append({
                        'Model': model_names.get(model, model.title()),
                        'Criterion': criterion.replace('_', ' ').title(),
                        'Score': score
                    })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # Create heatmap
            pivot_df = comparison_df.pivot(index='Criterion', columns='Model', values='Score')
            fig = px.imshow(
                pivot_df,
                title="Model Comparison Heatmap",
                color_continuous_scale='RdYlGn',
                aspect='auto'
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True, key="model_comparison_heatmap")
            
            # Show detailed comparison table
            st.write("**Detailed Model Scores:**")
            st.dataframe(pivot_df, use_container_width=True)
    
    # Download results
    st.subheader("💾 Download Results")
    if st.button("📥 Download JSON Report"):
        download_results(results)


def display_file_details(file_data: Dict):
    """Display detailed file analysis."""
    # Score breakdown
    if file_data['score_breakdown']:
        st.subheader("📊 Score Breakdown")
        
        breakdown = file_data['score_breakdown']
        criteria = list(breakdown.keys())
        scores = list(breakdown.values())
        
        # Radar chart
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=criteria,
            fill='toself',
            name='Scores'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            title="Score Breakdown Radar Chart"
        )
        st.plotly_chart(fig, use_container_width=True, key=f"radar_chart_{file_data['filename']}")
        
        # Score table
        score_df = pd.DataFrame({
            'Criterion': criteria,
            'Score': scores
        })
        st.dataframe(score_df, use_container_width=True)
    
    # Cells analysis
    st.subheader("📝 Code Cells")
    
    for cell in file_data['cells']:
        with st.expander(f"🔧 {cell['cell_id']} - {cell['language']} - Score: {cell['overall_score']:.1f}"):
            # Code display
            st.code(cell['code'], language=cell['language'])
            
            # Cell scores
            if cell['scores']:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Scores:**")
                    for criterion, score in cell['scores'].items():
                        st.write(f"- {criterion}: {score:.1f}")
                
                with col2:
                    st.write("**Issues:**")
                    if cell['issues']:
                        for issue in cell['issues']:
                            st.write(f"- ⚠️ {issue}")
                    else:
                        st.write("- No issues detected")
            
            # AI Feedback
            if cell['feedback']:
                st.write("**🤖 AI Model Feedback:**")
                
                # Create tabs for different model categories
                local_models = ['enhanced']
                api_models = ['openai', 'gemini']
                
                # Local Models Tab
                with st.expander("🧠 Local Models (Enhanced Task-Specific Evaluator)"):
                    local_feedback = {k: v for k, v in cell['feedback'].items() if k in local_models}
                    
                    if local_feedback:
                        for model, feedback in local_feedback.items():
                            # Model icon mapping
                            model_icons = {
                                'enhanced': '🧠'
                            }
                            model_names = {
                                'enhanced': 'Enhanced Task-Specific Evaluator (CodeBERT)'
                            }
                            
                            with st.expander(f"{model_icons.get(model, '🤖')} {model_names.get(model, model.title())} Feedback"):
                                st.write(f"**Confidence:** {feedback['confidence']:.2f}")
                                
                                # Show scores if available
                                if feedback.get('scores'):
                                    st.write("**Detailed Scores:**")
                                    scores = feedback['scores']
                                    score_cols = st.columns(3)
                                    with score_cols[0]:
                                        st.metric("Correctness", f"{scores['correctness']:.1f}")
                                        st.metric("Efficiency", f"{scores['efficiency']:.1f}")
                                        st.metric("Readability", f"{scores['readability']:.1f}")
                                    with score_cols[1]:
                                        st.metric("Scalability", f"{scores['scalability']:.1f}")
                                        st.metric("Security", f"{scores['security']:.1f}")
                                        st.metric("Modularity", f"{scores['modularity']:.1f}")
                                    with score_cols[2]:
                                        st.metric("Documentation", f"{scores['documentation']:.1f}")
                                        st.metric("Best Practices", f"{scores['best_practices']:.1f}")
                                        st.metric("Error Handling", f"{scores['error_handling']:.1f}")
                                
                                st.write("**Analysis:**")
                                st.write(feedback['feedback'])
                                
                                if feedback['suggestions']:
                                    st.write("**Suggestions:**")
                                    for suggestion in feedback['suggestions']:
                                        st.write(f"- 💡 {suggestion}")
                    else:
                        st.info("No local model feedback available")
                
                # API Models Tab
                api_feedback = {k: v for k, v in cell['feedback'].items() if k in api_models}
                if api_feedback:
                    with st.expander("🌐 API Models (OpenAI GPT-4, Google Gemini)"):
                        for model, feedback in api_feedback.items():
                            model_icons = {
                                'openai': '🤖',
                                'gemini': '🔮'
                            }
                            model_names = {
                                'openai': 'OpenAI GPT-4',
                                'gemini': 'Google Gemini'
                            }
                            
                            with st.expander(f"{model_icons.get(model, '🤖')} {model_names.get(model, model.title())} Feedback"):
                                st.write(f"**Confidence:** {feedback['confidence']:.2f}")
                                
                                # Show scores if available
                                if feedback.get('scores'):
                                    st.write("**Detailed Scores:**")
                                    scores = feedback['scores']
                                    score_cols = st.columns(3)
                                    with score_cols[0]:
                                        st.metric("Correctness", f"{scores['correctness']:.1f}")
                                        st.metric("Efficiency", f"{scores['efficiency']:.1f}")
                                        st.metric("Readability", f"{scores['readability']:.1f}")
                                    with score_cols[1]:
                                        st.metric("Scalability", f"{scores['scalability']:.1f}")
                                        st.metric("Security", f"{scores['security']:.1f}")
                                        st.metric("Modularity", f"{scores['modularity']:.1f}")
                                    with score_cols[2]:
                                        st.metric("Documentation", f"{scores['documentation']:.1f}")
                                        st.metric("Best Practices", f"{scores['best_practices']:.1f}")
                                        st.metric("Error Handling", f"{scores['error_handling']:.1f}")
                                
                                st.write("**Analysis:**")
                                st.write(feedback['feedback'])
                                
                                if feedback['suggestions']:
                                    st.write("**Suggestions:**")
                                    for suggestion in feedback['suggestions']:
                                        st.write(f"- 💡 {suggestion}")
            
            # Suggestions
            if cell['suggestions']:
                st.write("**💡 Improvement Suggestions:**")
                for suggestion in cell['suggestions']:
                    st.write(f"- {suggestion}")


def download_results(results: Dict):
    """Download results as JSON."""
    json_str = json.dumps(results, indent=2, default=str)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="evaluation_results.json">Download JSON Report</a>'
    st.markdown(href, unsafe_allow_html=True)


def statistics_page():
    """Statistics page."""
    st.header("📈 Statistics")
    
    try:
        response = requests.get(f"{API_BASE_URL}/statistics")
        if response.status_code == 200:
            stats = response.json()
            display_statistics(stats)
        else:
            st.error("Failed to load statistics")
            
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")


def display_statistics(stats: Dict):
    """Display statistics with charts."""
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Evaluations", stats['total_evaluations'])
    with col2:
        st.metric("Completed", stats['completed_evaluations'])
    with col3:
        st.metric("Failed", stats['failed_evaluations'])
    with col4:
        st.metric("Average Score", f"{stats['average_score']:.1f}")
    
    # Languages chart
    if stats['languages_processed']:
        st.subheader("🔤 Languages Processed")
        lang_df = pd.DataFrame([
            {'Language': lang, 'Count': count}
            for lang, count in stats['languages_processed'].items()
        ])
        
        fig = px.pie(
            lang_df, 
            values='Count', 
            names='Language',
            title="Code Languages Distribution"
        )
        st.plotly_chart(fig, use_container_width=True, key="languages_pie_chart")
    
    # Processing time
    st.subheader("⏱️ Processing Performance")
    st.metric("Average Processing Time", f"{stats['processing_time_avg']:.1f} seconds")


def api_docs_page():
    """API documentation page."""
    st.header("📚 API Documentation")
    
    st.markdown("""
    ## API Endpoints
    
    ### Upload and Evaluate
    ```
    POST /api/v1/evaluate
    Content-Type: multipart/form-data
    ```
    
    ### Get Evaluation Status
    ```
    GET /api/v1/evaluations/{evaluation_id}/status
    ```
    
    ### Get Results
    ```
    GET /api/v1/evaluations/{evaluation_id}/results
    ```
    
    ### List Evaluations
    ```
    GET /api/v1/evaluations
    ```
    
    ### Get Statistics
    ```
    GET /api/v1/statistics
    ```
    
    ## Interactive API Documentation
    Visit the FastAPI automatic documentation at: http://localhost:8000/docs
    """)


def test_api_keys_sync(openai_key: str, google_key: str, grok_key: str):
    """Test API keys functionality synchronously."""
    with st.spinner("Testing API keys..."):
        results = []
        
        # Test OpenAI
        if openai_key:
            try:
                import openai
                openai.api_key = openai_key
                # Simple test - just check if key is valid
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                results.append("✅ OpenAI API key is valid")
            except openai.error.RateLimitError as e:
                results.append(f"⚠️ OpenAI API rate limit exceeded: {str(e)}")
                results.append("💡 Consider upgrading your plan or waiting for reset")
            except openai.error.QuotaExceededError as e:
                results.append(f"⚠️ OpenAI API quota exceeded: {str(e)}")
                results.append("💡 Consider upgrading your plan or waiting for reset")
            except openai.error.AuthenticationError as e:
                results.append(f"❌ OpenAI API authentication failed: {str(e)}")
                results.append("💡 Check your API key configuration")
            except Exception as e:
                results.append(f"❌ OpenAI API key error: {str(e)}")
        else:
            results.append("⚠️ OpenAI API key not provided")
        
        # Test Google
        if google_key:
            try:
                import google.generativeai as genai
                from google.api_core import exceptions as google_exceptions
                
                genai.configure(api_key=google_key)
                model = genai.GenerativeModel('gemini-1.5-pro')  # Using latest model
                response = model.generate_content("Hello")
                results.append("✅ Google API key is valid")
            except google_exceptions.ResourceExhausted as e:
                error_msg = str(e)
                if "quota" in error_msg.lower() or "429" in error_msg:
                    results.append(f"⚠️ Google API quota exceeded: {error_msg}")
                    results.append("💡 Consider upgrading your plan or waiting for reset")
                else:
                    results.append(f"⚠️ Google API resource exhausted: {error_msg}")
            except google_exceptions.PermissionDenied as e:
                results.append(f"❌ Google API permission denied: {str(e)}")
                results.append("💡 Check your API key permissions")
            except Exception as e:
                results.append(f"❌ Google API key error: {str(e)}")
        else:
            results.append("⚠️ Google API key not provided")
        
        # Test Grok
        if grok_key:
            if ANTHROPIC_AVAILABLE:
                try:
                    from anthropic import Anthropic
                    # Try to initialize client with minimal arguments
                    try:
                        client = Anthropic(api_key=grok_key)
                    except TypeError as e:
                        if "proxies" in str(e):
                            # Handle proxies argument issue
                            import os
                            # Temporarily remove any proxy environment variables
                            old_proxy_vars = {}
                            for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                                if var in os.environ:
                                    old_proxy_vars[var] = os.environ[var]
                                    del os.environ[var]
                            
                            try:
                                client = Anthropic(api_key=grok_key)
                            finally:
                                # Restore proxy environment variables
                                for var, value in old_proxy_vars.items():
                                    os.environ[var] = value
                        else:
                            raise e
                    
                    response = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=5,
                        messages=[{"role": "user", "content": "Hello"}]
                    )
                    results.append("✅ Grok API key is valid")
                except Exception as e:
                    error_msg = str(e)
                    if "proxies" in error_msg.lower():
                        results.append(f"⚠️ Grok API configuration issue: {error_msg}")
                        results.append("💡 This is a known compatibility issue - Grok will still work during evaluation")
                    elif "rate_limit" in error_msg.lower() or "429" in error_msg:
                        results.append(f"⚠️ Grok API rate limit exceeded: {error_msg}")
                        results.append("💡 Consider upgrading your plan or waiting for reset")
                    elif "quota" in error_msg.lower():
                        results.append(f"⚠️ Grok API quota exceeded: {error_msg}")
                        results.append("💡 Consider upgrading your plan or waiting for reset")
                    elif "authentication" in error_msg.lower() or "401" in error_msg:
                        results.append(f"❌ Grok API authentication failed: {error_msg}")
                        results.append("💡 Check your API key configuration")
                    else:
                        results.append(f"❌ Grok API key error: {error_msg}")
            else:
                results.append("⚠️ Anthropic library not installed - cannot test Grok API key")
        else:
            results.append("⚠️ Grok API key not provided")
        
        # Display results
        for result in results:
            st.write(result)
        
        # Show fallback information
        st.info("💡 **Fallback Information:** If API models fail, the system will automatically use local models (Enhanced Evaluator) for evaluation.")


if __name__ == "__main__":
    main() 