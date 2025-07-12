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
        
        # API Models
        st.write("**API Models (Require API Keys):**")
        openai_key = st.text_input("OpenAI API Key", type="password", key="openai_api_key")
        google_key = st.text_input("Google Gemini API Key", type="password", key="google_api_key")
        
        # API Model Selection
        if 'use_openai' not in st.session_state:
            st.session_state.use_openai = False
        if 'use_gemini' not in st.session_state:
            st.session_state.use_gemini = False
            
        st.session_state.use_openai = st.checkbox("🤖 OpenAI GPT-4", value=st.session_state.use_openai, disabled=not openai_key, help="OpenAI's GPT-4 model")
        st.session_state.use_gemini = st.checkbox("🤖 Google Gemini", value=st.session_state.use_gemini, disabled=not google_key, help="Google's Gemini model")
        
        if st.button("Test API Keys"):
            test_api_keys_sync(openai_key, google_key)
        
        st.markdown("---")
        st.header("Navigation")
        page = st.selectbox(
            "Choose a page",
            ["Upload & Evaluate", "Results Dashboard", "Statistics", "API Documentation"]
        )
    
    # Page routing
    if page == "Upload & Evaluate":
        upload_page()
    elif page == "Results Dashboard":
        results_page()
    elif page == "Statistics":
        statistics_page()
    elif page == "API Documentation":
        api_docs_page()


def upload_page():
    """File upload and evaluation page."""
    st.header("📁 Upload & Evaluate")
    
    # File upload section
    st.subheader("Upload Notebooks")
    
    uploaded_file = st.file_uploader(
        "Choose a ZIP file containing Jupyter notebooks",
        type=['zip'],
        help="Upload a ZIP file containing .ipynb files or other code files"
    )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("File Type", uploaded_file.type or "application/zip")
        
        # Upload button
        if st.button("🚀 Start Evaluation", type="primary"):
            # Check which models are selected
            selected_models = []
            
            if st.session_state.use_codebert:
                selected_models.append("🧠 Enhanced Task-Specific Evaluator")
            if st.session_state.use_openai and st.session_state.openai_api_key:
                selected_models.append("🤖 OpenAI GPT-4")
            if st.session_state.use_gemini and st.session_state.google_api_key:
                selected_models.append("🤖 Google Gemini")
            
            if not selected_models:
                st.error("❌ Please select at least one model for evaluation!")
                return
            
            # Show which models will be used
            st.info("🤖 **Models that will be used for evaluation:**")
            for model in selected_models:
                st.write(f"✅ {model}")
            
            # Show warnings for API models without keys
            if st.session_state.use_openai and not st.session_state.openai_api_key:
                st.warning("⚠️ OpenAI GPT-4 selected but no API key provided")
            if st.session_state.use_gemini and not st.session_state.google_api_key:
                st.warning("⚠️ Google Gemini selected but no API key provided")

            with st.spinner("Uploading and starting evaluation..."):
                try:
                    # Upload file with API keys and model selection
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    data = {
                        "openai_api_key": st.session_state.openai_api_key,
                        "google_api_key": st.session_state.google_api_key,
                        "use_codebert": st.session_state.use_codebert,
                        "use_openai": st.session_state.use_openai,
                        "use_gemini": st.session_state.use_gemini
                    }
                    response = requests.post(f"{API_BASE_URL}/evaluate", files=files, data=data)

                    if response.status_code == 200:
                        result = response.json()
                        evaluation_id = result["evaluation_id"]

                        st.success(f"✅ Evaluation started successfully!")
                        st.info(f"Evaluation ID: `{evaluation_id}`")

                        # Store evaluation ID in session state
                        st.session_state.current_evaluation_id = evaluation_id

                        # Show progress monitoring
                        st.subheader("📊 Evaluation Progress")
                        progress_monitor(evaluation_id)

                    else:
                        st.error(f"❌ Upload failed: {response.json().get('detail', 'Unknown error')}")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Recent evaluations
    st.subheader("🕒 Recent Evaluations")
    show_recent_evaluations()


def progress_monitor(evaluation_id: str):
    """Monitor evaluation progress."""
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    while True:
        try:
            response = requests.get(f"{API_BASE_URL}/evaluations/{evaluation_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                
                # Update progress bar
                progress = status_data.get("progress", 0)
                progress_placeholder.progress(progress / 100)
                
                # Update status
                status = status_data.get("status", "unknown")
                status_placeholder.info(f"Status: {status.upper()} - {progress:.1f}%")
                
                # Check if completed
                if status == "completed":
                    status_placeholder.success("✅ Evaluation completed!")
                    st.balloons()
                    break
                elif status == "failed":
                    status_placeholder.error("❌ Evaluation failed!")
                    break
                
                time.sleep(2)  # Poll every 2 seconds
            else:
                st.error("Failed to get evaluation status")
                break
                
        except Exception as e:
            st.error(f"Error monitoring progress: {str(e)}")
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
                
                # Display in a table
                for _, eval_data in df.head(5).iterrows():
                    with st.expander(f"📄 {eval_data['filename']} - {eval_data['status']}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**ID:** {eval_data['evaluation_id']}")
                            st.write(f"**Status:** {eval_data['status']}")
                        with col2:
                            st.write(f"**Progress:** {eval_data['progress']:.1f}%")
                            st.write(f"**Created:** {eval_data['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        with col3:
                            if eval_data['status'] == 'completed':
                                st.success("✅ Completed")
                                if st.button(f"View Results", key=f"view_{eval_data['evaluation_id']}"):
                                    st.session_state.current_evaluation_id = eval_data['evaluation_id']
                                    st.rerun()
            else:
                st.info("No evaluations found")
        else:
            st.error("Failed to fetch evaluations")
            
    except Exception as e:
        st.error(f"Error fetching evaluations: {str(e)}")


def results_page():
    """Results dashboard page."""
    st.header("📊 Results Dashboard")
    
    # Evaluation selection
    evaluation_id = st.text_input(
        "Enter Evaluation ID",
        value=st.session_state.get("current_evaluation_id", ""),
        help="Enter the evaluation ID to view results"
    )
    
    if evaluation_id:
        if st.button("🔍 Load Results"):
            load_evaluation_results(evaluation_id)
    else:
        st.info("Please enter an evaluation ID to view results")


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
    st.subheader(f"📋 Evaluation Results: {results['filename']}")
    
    # Project overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Project Score", f"{results['project_score']:.1f}/10")
    with col2:
        st.metric("Total Files", len(results['files']))
    with col3:
        st.metric("Total Cells", results['total_cells'])
    with col4:
        if results['completed_at'] and results['created_at']:
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
        fig = px.bar(
            files_df, 
            x='Filename', 
            y='Score',
            title="File Scores",
            color='Score',
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed file analysis
        for file_data in results['files']:
            with st.expander(f"📄 {file_data['filename']} - Score: {file_data['overall_score']:.1f}"):
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
            st.plotly_chart(fig, use_container_width=True)
            
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
        st.plotly_chart(fig, use_container_width=True)
        
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
                                'enhanced': 'Enhanced Task-Specific Evaluator'
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
        st.plotly_chart(fig, use_container_width=True)
    
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


def test_api_keys_sync(openai_key: str, google_key: str):
    """Test API keys functionality synchronously."""
    with st.spinner("Testing API keys..."):
        results = []
        
        # Test OpenAI
        if openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                # Simple test - just check if key is valid
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                results.append("✅ OpenAI API key is valid")
            except Exception as e:
                results.append(f"❌ OpenAI API key error: {str(e)}")
        else:
            results.append("⚠️ OpenAI API key not provided")
        
        # Test Google
        if google_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                model = genai.GenerativeModel('gemini-1.5-pro')  # Using latest model
                response = model.generate_content("Hello")
                results.append("✅ Google API key is valid")
            except Exception as e:
                results.append(f"❌ Google API key error: {str(e)}")
        else:
            results.append("⚠️ Google API key not provided")
        
        # Display results
        for result in results:
            st.write(result)


if __name__ == "__main__":
    main() 