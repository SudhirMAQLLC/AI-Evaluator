# AI-Powered Assignment Evaluator

A production-ready system for evaluating student assignments using **Google Gemini AI** and **Puter AI GPT models**. This tool provides detailed, automated feedback on coding assignments with support for multiple file formats and real-time evaluation.

## 🚀 Features

- **Unified AI Evaluation**: Choose between Google Gemini AI or any supported Puter GPT model (including GPT-4.1 nano, GPT-4, GPT-4 Turbo, GPT-3.5 Turbo, etc.) from a single interface.
- **Modern UI**: Clean, production-ready Streamlit app (`main_app.py`) for all evaluation workflows.
- **Multi-Format Support**: Handles ZIP files, Jupyter notebooks, Python scripts, and more
- **Detailed Scoring**: Individual notebook scoring across multiple metrics
- **Production Ready**: Docker support, robust error handling, and scalable architecture

## 🤖 AI Models Supported

- **Google Gemini AI** (API key required)
- **Puter AI GPT Models** (browser-based, no server key required)

## 📋 Prerequisites

- Python 3.8+
- Google Gemini API key (for Gemini evaluator)
- Puter AI account (for GPT models)
- Docker (optional, for containerized deployment)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SudhirMAQLLC/AI-Evaluator.git
   cd AI-Evaluator
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API keys**
   ```bash
   export GOOGLE_API_KEY="your-gemini-api-key-here"
   # Puter AI models do not require a server-side API key for browser-based evaluation.
   ```

## 🚀 Usage

### Web Interface (Unified)

```bash
streamlit run main_app.py
```

- Upload your assignment brief and student solution ZIP.
- Select your preferred AI model (Gemini or any Puter GPT model) in the UI.
- Click the evaluation button to get instant, color-coded feedback.

## 📁 Project Structure

```
AI-Evaluator/
├── main_app.py                # Unified Streamlit app (production)
├── gemini_evaluator.py        # Gemini AI evaluation logic
├── gpt_evaluator.py           # Puter GPT evaluation logic
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
├── README.md                  # This file
├── app/                       # FastAPI backend (optional)
├── briefs/                    # Sample assignment briefs
└── tests/                     # Test suite
```

## 🏭 Production Branch

This code is maintained on the [`production-cleanup`](https://github.com/SudhirMAQLLC/AI-Evaluator/tree/production-cleanup) branch.  
All development and deployment should use this branch for the latest, production-ready code.

## 🔧 Configuration

### Environment Variables

- `GOOGLE_API_KEY`: Your Google Gemini API key (for Gemini evaluator)
- `STREAMLIT_SERVER_PORT`: Port for Streamlit (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Address for Streamlit (default: 0.0.0.0)

### API Key Setup

#### Google Gemini AI
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Set as `GOOGLE_API_KEY` environment variable

#### Puter AI (GPT Models)
- No server-side API key required for browser-based evaluation.

## 🧪 Testing

```bash
pytest
```

## 📊 Evaluation Metrics

Both evaluators use the same comprehensive scoring system:

### 1. Code Implementation (0-30 points)
- **CORRECTNESS**: Does the code actually solve the assigned problem?
- **REQUIREMENT COMPLIANCE**: Are all specific requirements implemented?
- **FUNCTIONALITY**: Does the code execute and produce expected outputs?
- **SPECIFIC CHECKS**: Look for exact tables, functions, procedures mentioned in requirements

### 2. Code Quality (0-25 points)
- Code structure and organization
- Best practices implementation
- Error handling and robustness
- Performance considerations

### 3. Documentation (0-20 points)
- Code comments and explanations
- Markdown cell quality
- Implementation documentation
- README quality (if applicable)

### 4. Problem Solving (0-25 points)
- **COMPLETENESS**: Does the solution address ALL requirements?
- **LOGICAL APPROACH**: Is the solution approach sound?
- **EDGE CASES**: Are edge cases handled appropriately?

## ✅ Correctness Verification

Both evaluators include thorough correctness checking:

- **Requirement Verification**: Explicitly checks each requirement is implemented
- **Output Validation**: Confirms expected deliverables are present
- **Specific Checks**: Verifies exact table names, column names, data types
- **Penalty System**: Harsh scoring for incorrect/off-topic solutions
- **Overall Assessment**: Clear indication if solution is correct or not

## 🔄 Comparison: Gemini AI vs Puter GPT Models

| Feature | Gemini AI | Puter GPT Models |
|---------|-----------|-----------------|
| **Speed** | Fast | Very Fast |
| **Cost** | Moderate | Low |
| **Accuracy** | High | High |
| **Detail Level** | Very Detailed | Detailed |
| **API Stability** | Very Stable | Stable |
| **Best For** | Comprehensive evaluation | Quick evaluation |

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run
docker-compose up --build

# Or run individual services
# docker run -p 8501:8501 -e GOOGLE_API_KEY=your-key ai-assignment-evaluator
```

### Production Deployment

1. **Set up environment variables**
2. **Configure reverse proxy (nginx)**
3. **Set up SSL certificates**
4. **Configure monitoring and logging**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/SudhirMAQLLC/AI-Evaluator/issues)

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes. 