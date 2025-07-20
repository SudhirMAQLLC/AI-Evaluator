# AI-Powered Assignment Evaluator

A production-ready system for evaluating student assignments using **Google Gemini AI** and **GPT-4.1 nano via Puter AI**. This tool provides detailed, automated feedback on coding assignments with support for multiple file formats and real-time evaluation.

## 🚀 Features

- **Dual AI Evaluation**: Choose between Google Gemini AI or GPT-4.1 nano (Puter AI)
- **AI-Powered Evaluation**: Uses advanced AI models for intelligent assignment assessment
- **Multi-Format Support**: Handles ZIP files, Jupyter notebooks, Python scripts, and more
- **Detailed Scoring**: Individual notebook scoring across multiple metrics:
  - Code Implementation (0-30 points)
  - Code Quality (0-25 points)
  - Documentation (0-20 points)
  - Problem Solving (0-25 points)
- **Correctness Verification**: Thorough checking of requirement compliance and solution accuracy
- **Real-time Feedback**: Instant evaluation with detailed feedback and suggestions
- **Assignment Brief Support**: Upload custom assignment briefs in PDF, TXT, DOCX, YAML, or JSON formats
- **Clean UI**: Modern Streamlit interface with expandable sections and detailed breakdowns
- **Production Ready**: Docker support, proper error handling, and scalable architecture

## 🤖 AI Models Supported

### 1. Google Gemini AI
- **File**: `gemini_streamlit_app.py` / `gemini_evaluator.py`
- **CLI**: `cli.py`
- **API**: Google Generative AI
- **Best for**: Comprehensive evaluation with detailed feedback

### 2. GPT-4.1 nano (Puter AI)
- **File**: `gpt_streamlit_app.py` / `gpt_evaluator.py`
- **CLI**: `gpt_cli.py`
- **API**: Puter AI
- **Best for**: Fast, cost-effective evaluation
- **Demo**: `puter_demo.html`

## 📋 Prerequisites

- Python 3.8+
- Google Gemini API key (for Gemini evaluator)
- Puter AI API key (for GPT evaluator)
- Docker (optional, for containerized deployment)

## 🛠️ Installation

### Option 1: Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-assignment-evaluator.git
   cd ai-assignment-evaluator
   ```

2. **Create a virtual environment**
```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
```bash
pip install -r requirements.txt
   ```

4. **Set up your API keys**
   ```bash
   # For Gemini AI
   export GOOGLE_API_KEY="your-gemini-api-key-here"
   
   # For GPT-4.1 nano (Puter AI)
   export PUTER_API_KEY="your-puter-api-key-here"
   ```
   Or create a `.env` file:
   ```
   GOOGLE_API_KEY=your-gemini-api-key-here
   PUTER_API_KEY=your-puter-api-key-here
   ```

### Option 2: Docker Installation

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or build manually**
   ```bash
   docker build -t ai-assignment-evaluator .
   docker run -p 8501:8501 -e GOOGLE_API_KEY=your-api-key ai-assignment-evaluator
```

## 🚀 Usage

### Web Interface

#### Gemini AI Evaluator
```bash
streamlit run gemini_streamlit_app.py
```

#### GPT-4.1 nano Evaluator
```bash
streamlit run gpt_streamlit_app.py
```

#### HTML Demo (Puter AI)
Open `puter_demo.html` in your browser for a quick demo.

### Command Line Interface

#### Gemini AI CLI
```bash
# Evaluate with Gemini AI
python cli.py evaluate solution.zip --type snowflake --api-key YOUR_GEMINI_KEY

# List assignment types
python cli.py list-types

# Test API connection
python cli.py test-api --api-key YOUR_GEMINI_KEY
```

#### GPT-4.1 nano CLI
```bash
# Evaluate with GPT-4.1 nano
python gpt_cli.py evaluate solution.zip --type snowflake --api-key YOUR_PUTER_KEY

# List assignment types
python gpt_cli.py list-types

# Test API connection
python gpt_cli.py test-api --api-key YOUR_PUTER_KEY
```

## 📁 Project Structure

```
ai-assignment-evaluator/
├── gemini_streamlit_app.py      # Gemini AI Streamlit app
├── gemini_evaluator.py          # Gemini AI evaluation logic
├── gpt_streamlit_app.py         # GPT-4.1 nano Streamlit app
├── gpt_evaluator.py             # GPT-4.1 nano evaluation logic
├── cli.py                       # Gemini AI CLI
├── gpt_cli.py                   # GPT-4.1 nano CLI
├── puter_demo.html              # HTML demo for Puter AI
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── docker-compose.yml          # Docker Compose setup
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
├── tests/                      # Test suite
│   ├── test_evaluator.py
│   └── test_streamlit_app.py
├── app/                        # FastAPI backend (optional)
│   ├── main.py
│   ├── config.py
│   └── schemas/
├── data/                       # Sample data
├── uploads/                    # Upload directory
└── briefs/                     # Sample assignment briefs
```

## 🔧 Configuration

### Environment Variables

- `GOOGLE_API_KEY`: Your Google Gemini API key (for Gemini evaluator)
- `PUTER_API_KEY`: Your Puter AI API key (for GPT evaluator)
- `STREAMLIT_SERVER_PORT`: Port for Streamlit (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Address for Streamlit (default: 0.0.0.0)

### API Key Setup

#### Google Gemini AI
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Set as `GOOGLE_API_KEY` environment variable

#### Puter AI (GPT-4.1 nano)
1. Visit [Puter AI](https://puter.com)
2. Sign up and get your API key
3. Set as `PUTER_API_KEY` environment variable

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_evaluator.py
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

## 🔄 Comparison: Gemini AI vs GPT-4.1 nano

| Feature | Gemini AI | GPT-4.1 nano |
|---------|-----------|--------------|
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
docker run -p 8501:8501 -e GOOGLE_API_KEY=your-key ai-assignment-evaluator
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

- **Issues**: [GitHub Issues](https://github.com/yourusername/ai-assignment-evaluator/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/ai-assignment-evaluator/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ai-assignment-evaluator/discussions)

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## 📞 Contact

- **Email**: your-email@example.com
- **Twitter**: [@yourusername](https://twitter.com/yourusername)
- **LinkedIn**: [Your Name](https://linkedin.com/in/yourusername) 