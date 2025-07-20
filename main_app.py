import streamlit as st
import tempfile
import json
import zipfile
import io
import os

# Import Gemini evaluator if available
try:
    from gemini_evaluator import GeminiEvaluator
except ImportError:
    GeminiEvaluator = None

st.set_page_config(
    page_title="LDP Assignment Evaluator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for modern look ---
st.markdown(r'''
<style>
body, .stApp { 
    background: #181818 !important; 
    color: #fafafa !important; 
}

.stButton>button { 
    font-weight: bold; 
    font-size: 16px; 
    padding: 12px 32px; 
    border-radius: 8px; 
    color: #fafafa !important; 
    background: linear-gradient(45deg, #4CAF50, #45a049) !important; 
    border: none !important;
    transition: all 0.3s ease;
}

.stButton>button:hover { 
    background: linear-gradient(45deg, #45a049, #4CAF50) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.stTextInput>div>div>input { 
    font-size: 16px; 
    color: #fafafa !important; 
    background: #222 !important; 
    border: 1px solid #444 !important;
    border-radius: 8px;
}

.stFileUploader>div>div { 
    font-size: 15px; 
    color: #fafafa !important; 
    background: #222 !important; 
    border: 1px solid #444 !important;
    border-radius: 8px;
    padding: 16px;
}

.stSelectbox>div>div>div { 
    color: #fafafa !important; 
    background: #222 !important; 
    border: 1px solid #444 !important;
    border-radius: 8px;
}

.card { 
    background: linear-gradient(135deg, #222 0%, #2a2a2a 100%); 
    border-radius: 12px; 
    box-shadow: 0 4px 20px rgba(0,0,0,0.3); 
    padding: 24px; 
    margin-bottom: 20px; 
    color: #fafafa !important; 
    border: 1px solid #444;
}

.stMarkdown, .stTextInput, .stFileUploader, .stSelectbox { 
    color: #fafafa !important; 
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    background: #222 !important;
    border-radius: 8px 8px 0 0 !important;
    border: 1px solid #444 !important;
    color: #fafafa !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(45deg, #4CAF50, #45a049) !important;
    color: white !important;
}

hr { 
    border: none !important;
    border-top: 2px solid #444 !important; 
    margin: 20px 0 !important;
}

/* Remove extra margins and padding */
.block-container {
    padding-top: 2rem;
    padding-bottom: 1rem;
}

/* Footer styling */
.footer {
    background: linear-gradient(135deg, #222 0%, #2a2a2a 100%);
    border-top: 1px solid #444;
    padding: 16px 0;
    margin-top: 20px;
    text-align: center;
    color: #888;
    font-size: 13px;
}

/* Model info cards */
.model-info {
    background: linear-gradient(45deg, #1e3a5f, #2d5a87);
    padding: 12px 16px;
    border-radius: 8px;
    margin: 8px 0;
    border-left: 4px solid #4CAF50;
    color: #e3f2fd;
}
</style>
''', unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div style='text-align:center; margin-bottom: 20px;'>
  <h1 style='margin-bottom:8px; color: #4CAF50;'>🤖 LDP Assignment Evaluator</h1>
  <div style='color:#888; font-size:18px; line-height: 1.4;'>Upload your assignment brief and student solution ZIP for instant AI-powered evaluation.</div>
</div>
""", unsafe_allow_html=True)

# --- File Uploaders ---
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 📁 Upload Files")
    
    col1, col2 = st.columns(2)
    with col1:
        brief_file = st.file_uploader(
            "Assignment Brief", 
            type=["pdf", "txt", "docx", "yaml", "yml", "json"], 
            help="Upload assignment requirements/description"
        )
        
        assignment_brief = None
        brief_content = None
        
        if brief_file:
            try:
                if brief_file.name.endswith(".pdf"):
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(brief_file)
                    brief_content = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
                elif brief_file.name.endswith(".docx"):
                    import docx
                    doc = docx.Document(brief_file)
                    brief_content = "\n".join([para.text for para in doc.paragraphs])
                elif brief_file.name.endswith((".yaml", ".yml")):
                    import yaml
                    brief_content = brief_file.read().decode("utf-8", errors="replace")
                    assignment_brief = yaml.safe_load(brief_content)
                elif brief_file.name.endswith(".json"):
                    import json
                    brief_content = brief_file.read().decode("utf-8", errors="replace")
                    assignment_brief = json.loads(brief_content)
                elif brief_file.name.endswith(".txt"):
                    brief_content = brief_file.read().decode("utf-8", errors="replace")
                else:
                    st.error("Unsupported file type for assignment brief.")
                    st.stop()
            except Exception as e:
                st.error(f"Failed to read assignment brief: {e}")
                st.stop()
                
            if assignment_brief is None and brief_content:
                try:
                    import yaml
                    assignment_brief = yaml.safe_load(brief_content)
                except Exception:
                    assignment_brief = None
                    
            st.success(f"✅ {brief_file.name}")
            st.info(f"📏 Size: {(brief_file.size / 1024):.1f} KB")

    with col2:
        solution_zip = st.file_uploader(
            "Student Solution (ZIP)", 
            type=["zip"], 
            help="Upload student's code and notebooks"
        )
        
        file_list = []
        files_content = ""
        
        if solution_zip:
            try:
                with zipfile.ZipFile(io.BytesIO(solution_zip.getvalue()), 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    st.success(f"✅ {solution_zip.name}")
                    st.info(f"📦 {len(file_list)} files | 📏 {(solution_zip.size / 1024):.1f} KB")
                    
                    for fname in file_list:
                        if not fname.endswith('/'):
                            try:
                                with zip_ref.open(fname) as f:
                                    content = f.read().decode('utf-8', errors='replace')
                                    files_content += f"\n=== FILE: {fname} ===\n{content}\n"
                            except Exception as e:
                                files_content += f"\n=== FILE: {fname} ===\n[Error reading file: {e}]\n"
            except Exception as e:
                st.error(f"Error reading ZIP file: {e}")
                
    st.markdown("</div>", unsafe_allow_html=True)

# --- State for results ---
if 'ldp_result' not in st.session_state:
    st.session_state.ldp_result = None
if 'gemini_result' not in st.session_state:
    st.session_state.gemini_result = None

# --- Results rendering function ---
def render_notebook_results(result):
    if not result or 'file_analysis' not in result:
        st.info("No results yet. Please upload files and run evaluation.")
        return
        
    for file in result['file_analysis']:
        verdict = file.get('verdict', 'N/A')
        score = file.get('score', 'N/A')
        details = file.get('details', '')
        filename = file.get('filename', 'Unknown')
        
        # Color logic
        if 'Meets' in verdict:
            verdict_color = '#4CAF50'
        elif 'Partially' in verdict:
            verdict_color = '#FFD600'
        else:
            verdict_color = '#f44336'
            
        st.markdown(f'''
        <div style="background:linear-gradient(135deg, #23272e 0%, #2a2e35 100%);border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid #444;box-shadow:0 4px 15px rgba(0,0,0,0.2);">
            <div style="font-size:20px;font-weight:700;margin-bottom:12px;color:#ffffff;">📄 {filename}</div>
            <div style="display:flex;align-items:center;gap:24px;margin-bottom:12px;">
                <div style="background:{verdict_color}22;color:{verdict_color};padding:8px 16px;border-radius:8px;font-weight:600;border:1px solid {verdict_color}44;">
                    {verdict}
                </div>
                <div style="background:{verdict_color};color:white;padding:8px 16px;border-radius:20px;font-weight:700;">
                    Score: {score}
                </div>
            </div>
            <div style="background:#1a1e23;padding:16px;border-radius:8px;border-left:4px solid {verdict_color};color:#e0e0e0;line-height:1.6;">
                {details}
            </div>
        </div>
        ''', unsafe_allow_html=True)

# --- Model Tabs ---
if brief_file and solution_zip:
    model_tabs = st.tabs(["🚀 LDP Evaluator", "🧠 Gemini AI"])

    # --- LDP Evaluator Tab ---
    with model_tabs[0]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.markdown("### 🎯 Select AI Model")
            selected_model = st.selectbox(
                "Choose evaluation model:",
                options=[
                    "LDP-Nano",
                    "LDP-Mini", 
                    "LDP-Standard",
                    "LDP-Pro",
                    "LDP-Pro-Mini",
                    "LDP-Reasoning",
                    "LDP-Advanced",
                    "LDP-Ultra"
                ],
                index=0,
                help="Select the AI model for evaluation"
            )
        
        with col2:
            # Model descriptions
            model_descriptions = {
                "LDP-Nano": "⚡ **Fastest & Most Efficient** - Perfect for quick evaluations and basic grading",
                "LDP-Mini": "🔥 **Balanced Performance** - Great balance of speed and quality analysis", 
                "LDP-Standard": "🧠 **High Quality Analysis** - Comprehensive evaluation with detailed feedback",
                "LDP-Pro": "🎯 **Premium Accuracy** - Advanced reasoning for complex assignment evaluation",
                "LDP-Pro-Mini": "💡 **Compact Premium** - Pro-level analysis in a faster package",
                "LDP-Reasoning": "🚀 **Enhanced Logic** - Superior reasoning capabilities for complex problems",
                "LDP-Advanced": "✨ **Next-Gen Analysis** - Advanced AI with sophisticated evaluation methods",
                "LDP-Ultra": "🌟 **Cutting-Edge** - State-of-the-art model with superior performance"
            }
            
            if selected_model in model_descriptions:
                st.markdown(f"<div class='model-info'>{model_descriptions[selected_model]}</div>", unsafe_allow_html=True)
        
        # Map display names to actual model names
        model_mapping = {
            "LDP-Nano": "gpt-4.1-nano",
            "LDP-Mini": "gpt-4.1-mini",
            "LDP-Standard": "gpt-4.1", 
            "LDP-Pro": "gpt-4o",
            "LDP-Pro-Mini": "gpt-4o-mini",
            "LDP-Reasoning": "o1-mini",
            "LDP-Advanced": "o3-mini",
            "LDP-Ultra": "o4-mini"
        }
        
        actual_model = model_mapping[selected_model]
        
        def create_evaluation_prompt(brief_content, files_content):
            return f"""You are an expert assignment evaluator. Your primary responsibility is to VERIFY CORRECTNESS - check if the student's solution actually meets the specific requirements stated in the assignment brief.

ASSIGNMENT BRIEF:
{brief_content}

STUDENT SUBMISSION FILES:
{files_content}

CRITICAL EVALUATION INSTRUCTIONS:
- Analyze the assignment brief and identify all requirements.
- For each file in the student submission, check if it meets the requirements.
- For each file, provide a verdict (Meets requirements / Does not meet requirements / Partially meets requirements), a score (0-100), and a details string.
- Respond ONLY with valid JSON. Do NOT include any markdown, explanations, or text outside the JSON object.
- If you cannot produce valid JSON, return: {{}}

Example response:
{{
  "file_analysis": [
    {{
      "filename": "solution_correct.ipynb",
      "verdict": "Meets requirements",
      "score": 100,
      "details": "The student's solution covers all aspects of the assignment brief, demonstrating correct implementation."
    }},
    {{
      "filename": "solution_incorrect.ipynb", 
      "verdict": "Does not meet requirements",
      "score": 0,
      "details": "The solution is incomplete and misses all key components."
    }}
  ]
}}

CRITICAL: Your response MUST be valid JSON. Do NOT include any markdown, explanations, or text outside the JSON object."""
        
        evaluation_prompt = create_evaluation_prompt(brief_content, files_content)
        
        # Escape the prompt and selected model for JavaScript
        escaped_prompt = json.dumps(evaluation_prompt)
        escaped_model = json.dumps(actual_model)
        escaped_display_name = json.dumps(selected_model)
        
        st.markdown("---")
        
        st.components.v1.html(f'''
            <div id="puter-eval-container" style="text-align: center;">
                <button id="evalBtn" style="
                    background: linear-gradient(45deg, #4CAF50, #45a049);
                    color: white;
                    padding: 16px 40px;
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                    font-size: 18px;
                    font-weight: bold;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(76, 175, 80, 0.4)'"
                   onmouseout="this.style.transform='translateY(0px)'; this.style.boxShadow='0 4px 15px rgba(76, 175, 80, 0.3)'">
                    🚀 Evaluate with {selected_model}
                </button>
                <div id="status" style="margin-top: 20px;"></div>
                <div id="result" style="margin-top: 24px; max-height: 600px; overflow-y: auto;"></div>
            </div>
            
            <script src="https://js.puter.com/v2/"></script>
            <script>
                const evalBtn = document.getElementById('evalBtn');
                const statusDiv = document.getElementById('status');
                const resultDiv = document.getElementById('result');

                let evaluationPrompt = {escaped_prompt};
                let selectedModel = {escaped_model};
                let displayName = {escaped_display_name};
                
                function tryParseJSON(str) {{
                    try {{
                        return JSON.parse(str);
                    }} catch (e) {{
                        const match = str.match(/\{{[\s\S]*\}}/);
                        if (match) {{
                            try {{
                                return JSON.parse(match[0]);
                            }} catch (e2) {{
                                console.error('JSON parsing failed:', e2);
                            }}
                        }}
                        return null;
                    }}
                }}
                
                function renderFileAnalysis(fileAnalysis) {{
                    let html = '';
                    for (const file of fileAnalysis) {{
                        const scoreColor = file.score >= 80 ? '#4CAF50' : (file.score >= 50 ? '#FFD600' : '#f44336');
                        const verdictColor = file.verdict.includes('Meets requirements') ? '#4CAF50' : 
                                           (file.verdict.includes('Partially') ? '#FFD600' : '#f44336');
                        const progressPercent = file.score || 0;
                        
                        html += `<div style="border:1px solid #444;background:linear-gradient(135deg, #23272e 0%, #2a2e35 100%);border-radius:12px;padding:24px;margin-bottom:16px;box-shadow:0 4px 15px rgba(0,0,0,0.2);">`;
                        html += `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">`;
                        html += `<h3 style="color:#ffffff;margin:0;font-size:20px;font-weight:700;">📄 ${{file.filename}}</h3>`;
                        html += `<div style="background:${{scoreColor}};color:white;padding:8px 16px;border-radius:20px;font-weight:bold;font-size:16px;">${{file.score || 'N/A'}}</div>`;
                        html += `</div>`;
                        
                        // Progress bar
                        html += `<div style="background:#333;border-radius:10px;height:10px;margin-bottom:16px;overflow:hidden;">`;
                        html += `<div style="background:${{scoreColor}};height:100%;width:${{progressPercent}}%;transition:width 0.8s ease;"></div>`;
                        html += `</div>`;
                        
                        html += `<div style="margin-bottom:16px;">`;
                        html += `<div style="display:inline-flex;align-items:center;background:${{verdictColor}}22;color:${{verdictColor}};padding:8px 16px;border-radius:8px;font-weight:600;font-size:15px;border:1px solid ${{verdictColor}}44;">`;
                        html += `<span style="margin-right:8px;">●</span>${{file.verdict}}`;
                        html += `</div>`;
                        html += `</div>`;
                        
                        html += `<div style="color:#e0e0e0;line-height:1.6;font-size:15px;background:#1a1e23;padding:16px;border-radius:8px;border-left:4px solid ${{verdictColor}};">`;
                        html += `${{file.details || 'No additional details provided.'}}`;
                        html += `</div>`;
                        html += `</div>`;
                    }}
                    return html;
                }}
                
                evalBtn.onclick = async function() {{
                    evalBtn.disabled = true;
                    evalBtn.innerHTML = `<span style="display:inline-block;width:16px;height:16px;border:2px solid #fff;border-top:2px solid transparent;border-radius:50%;animation:spin 1s linear infinite;margin-right:10px;"></span>Evaluating with ${{displayName}}...`;
                    statusDiv.innerHTML = `<div style="background:linear-gradient(45deg, #2196F3, #21CBF3);color:white;padding:16px 20px;border-radius:10px;box-shadow:0 4px 15px rgba(33,150,243,0.3);font-weight:600;"><span style="display:inline-block;width:16px;height:16px;border:2px solid #fff;border-top:2px solid transparent;border-radius:50%;animation:spin 1s linear infinite;margin-right:12px;"></span>Processing with ${{displayName}}...</div><style>@keyframes spin {{0%{{transform:rotate(0deg);}}100%{{transform:rotate(360deg);}}}}</style>`;
                    resultDiv.innerHTML = '';
                    
                    try {{
                        const response = await puter.ai.chat(evaluationPrompt, {{ model: selectedModel }});
                        
                        statusDiv.innerHTML = `<div style="background:linear-gradient(45deg, #4CAF50, #45a049);color:white;padding:16px 20px;border-radius:10px;box-shadow:0 4px 15px rgba(76,175,80,0.3);font-weight:600;"><span style="margin-right:12px;">✅</span>Evaluation Complete with ${{displayName}}!</div>`;
                        
                        let parsed = tryParseJSON(response);
                        if (parsed && parsed.file_analysis) {{
                            resultDiv.innerHTML = renderFileAnalysis(parsed.file_analysis);
                        }} else {{
                            let fallbackHtml = `<div style="background:linear-gradient(45deg, #ff9800, #f57c00);color:white;padding:16px 20px;border-radius:10px;margin-bottom:20px;font-weight:600;"><span style="margin-right:12px;">⚠️</span>Response formatting issue - showing raw results:</div>`;
                            fallbackHtml += '<div style="background:#2a2a2a;color:#e0e0e0;padding:20px;border-radius:10px;max-height:400px;overflow:auto;font-family:monospace;font-size:14px;line-height:1.5;border:1px solid #444;">' + response.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>';
                            resultDiv.innerHTML = fallbackHtml;
                        }}
                    }} catch (error) {{
                        statusDiv.innerHTML = `<div style="background:linear-gradient(45deg, #f44336, #d32f2f);color:white;padding:16px 20px;border-radius:10px;box-shadow:0 4px 15px rgba(244,67,54,0.3);font-weight:600;"><span style="margin-right:12px;">❌</span>Error: ${{error.message}}</div>`;
                    }} finally {{
                        evalBtn.disabled = false;
                        evalBtn.innerHTML = `🚀 Evaluate with ${{displayName}}`;
                    }}
                }};
            </script>
        ''', height=700, scrolling=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Gemini Tab ---
    with model_tabs[1]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### 🧠 Google Gemini AI")
        st.markdown("Advanced evaluation with comprehensive feedback. Requires Google API key.")
        
        api_key = st.text_input(
            "Google API Key:", 
            type="password", 
            help="Enter your Google API key to enable Gemini AI evaluation"
        )
        
        if api_key:
            if st.button("🚀 Evaluate with Gemini AI", type="primary"):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
                    tmp_zip.write(solution_zip.getvalue())
                    solution_path = tmp_zip.name
                    
                with st.spinner("🧠 Evaluating with Gemini AI..."):
                    try:
                        if GeminiEvaluator:
                            evaluator = GeminiEvaluator(api_key)
                            result = evaluator.evaluate(solution_path, assignment_brief)
                            st.session_state.gemini_result = result
                            st.success("✅ Evaluation complete!")
                        else:
                            st.error("❌ Gemini evaluator not available. Please check if gemini_evaluator module is installed.")
                    except Exception as e:
                        st.error(f"❌ Evaluation failed: {e}")
                    finally:
                        # Clean up temporary file
                        try:
                            os.unlink(solution_path)
                        except:
                            pass
        
        # Show Gemini results if available
        if st.session_state.gemini_result:
            st.markdown("### 🧠 Gemini Results")
            render_notebook_results(st.session_state.gemini_result)
        
        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown("""
    <div class='card' style='text-align: center; padding: 40px;'>
        <h3 style='color: #4CAF50; margin-bottom: 16px;'>📂 Ready to Evaluate</h3>
        <p style='color: #888; font-size: 16px;'>Please upload both assignment brief and student solution ZIP files to begin evaluation.</p>
    </div>
    """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
<div class="footer">
    <div style="max-width: 800px; margin: 0 auto;">
        <strong>LDP Assignment Evaluator</strong> &copy; 2024 | Powered by LDP AI & Google Gemini
        <br>
        <span style="color: #666;">Intelligent assignment evaluation for educators</span>
    </div>
</div>
""", unsafe_allow_html=True)