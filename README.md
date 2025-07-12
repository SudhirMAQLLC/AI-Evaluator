# AI Code Evaluator

A production-ready AI-powered code evaluation system that provides comprehensive analysis of SQL, Python, and Jupyter notebook code using multiple AI models and specialized evaluators.

## 🚀 Features

- **Multi-Model Evaluation**: CodeBERT, OpenAI GPT, and Google Gemini integration
- **Specialized SQL Analysis**: Pattern-based security detection, correctness validation, and efficiency analysis
- **Enhanced Evaluators**: Task-specific evaluation using the best tools for each metric
- **Comprehensive Logging**: Production-ready logging with rotation and structured output
- **RESTful API**: FastAPI-based API with automatic documentation
- **Streamlit Dashboard**: Interactive web interface for code evaluation
- **Docker Support**: Containerized deployment with Docker and Docker Compose
- **Production Ready**: Environment configuration, health checks, and monitoring

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Production Deployment](#production-deployment)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Redis (optional, for caching)
- Docker (optional, for containerized deployment)

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SudhirMAQLLC/AI-Evaluator.git
   cd AI-Evaluator
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment**
   ```bash
   cp env.production .env
   # Edit .env with your configuration
   ```

5. **Start Redis (optional)**
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:alpine
   
   # Or install locally
   sudo apt-get install redis-server  # Ubuntu/Debian
   ```

## 🚀 Quick Start

### Development Mode

1. **Start the FastAPI server**
   ```bash
   source venv/bin/activate
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the Streamlit dashboard**
   ```bash
   source venv/bin/activate
   streamlit run app/dashboard.py --server.port 8501 --server.address 0.0.0.0
   ```

3. **Access the application**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Dashboard: http://localhost:8501

### Production Mode

Use the production startup script:

```bash
# Setup the application
./start_production.sh setup

# Start the application
./start_production.sh start

# Check status
./start_production.sh status

# View logs
./start_production.sh logs

# Stop the application
./start_production.sh stop
```

### Docker Deployment

1. **Using Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Using Docker directly**
   ```bash
   # Build the image
   docker build -t ai-evaluator .
   
   # Run the container
   docker run -p 8000:8000 -p 8501:8501 ai-evaluator
   ```

## 🏭 Production Deployment

### Environment Configuration

Copy the production environment file and configure it:

```bash
cp env.production .env
```

Key configuration options:

```env
# Application settings
APP_NAME=AI Code Evaluator
DEBUG=false

# Server settings
HOST=0.0.0.0
PORT=8000
WORKERS=4

# File upload settings
MAX_FILE_SIZE=104857600  # 100MB
UPLOAD_DIR=./uploads

# Redis settings
REDIS_URL=redis://localhost:6379

# AI Model settings
OPENAI_API_KEY=your-openai-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key

# Logging settings
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# Security settings
SECRET_KEY=your-super-secret-key
```

### Production Startup

The production startup script provides comprehensive process management:

```bash
# Full setup and start
./start_production.sh setup
./start_production.sh start

# Monitor the application
./start_production.sh status
./start_production.sh logs

# Restart for updates
./start_production.sh restart
```

### Health Checks

The application provides health check endpoints:

- **Health Check**: `GET /health`
- **Readiness Check**: `GET /api/v1/health/ready`
- **Metrics**: `GET /metrics`

### Logging

Production logging is configured with:

- **Rotating file logs**: Automatic log rotation with size limits
- **Structured logging**: JSON-formatted logs for easy parsing
- **Multiple log levels**: DEBUG, INFO, WARNING, ERROR
- **Request logging**: All HTTP requests and responses logged

Log files are stored in `./logs/` with automatic rotation.

## 📚 API Documentation

### Core Endpoints

#### Upload and Evaluate
```http
POST /api/v1/evaluations/evaluate
Content-Type: multipart/form-data

file: <file>
openai_api_key: <optional>
google_api_key: <optional>
use_codebert: true
use_openai: false
use_gemini: false
```

#### Get Evaluation Status
```http
GET /api/v1/evaluations/{evaluation_id}/status
```

#### Get Evaluation Results
```http
GET /api/v1/evaluations/{evaluation_id}/results
```

#### List Evaluations
```http
GET /api/v1/evaluations
```

#### Delete Evaluation
```http
DELETE /api/v1/evaluations/{evaluation_id}
```

### Health and Monitoring

#### Health Check
```http
GET /health
```

#### Metrics
```http
GET /metrics
```

### Interactive Documentation

Access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | AI Code Evaluator |
| `DEBUG` | Debug mode | false |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |
| `WORKERS` | Number of workers | 4 |
| `MAX_FILE_SIZE` | Maximum file size | 100MB |
| `UPLOAD_DIR` | Upload directory | ./uploads |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379 |
| `LOG_LEVEL` | Logging level | INFO |
| `LOG_FILE` | Log file path | ./logs/app.log |

### AI Model Configuration

The system supports multiple AI models:

- **CodeBERT**: Default model for code analysis
- **OpenAI GPT**: Requires `OPENAI_API_KEY`
- **Google Gemini**: Requires `GOOGLE_API_KEY`

### Evaluation Settings

- **Evaluation Timeout**: 5 minutes per evaluation
- **Concurrent Evaluations**: 5 simultaneous evaluations
- **File Types**: .ipynb, .py, .sql, .zip

## 🧪 Development

### Project Structure

```
AI-Evaluator/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── api.py
│   │       └── endpoints/
│   ├── services/
│   │   ├── ai_evaluator.py
│   │   ├── enhanced_evaluator.py
│   │   ├── sql_specialized_evaluator.py
│   │   └── evaluation_service.py
│   ├── models/
│   ├── config.py
│   ├── main.py
│   └── dashboard.py
├── logs/
├── uploads/
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── start_production.sh
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

### Code Quality

```bash
# Install development dependencies
pip install black flake8 mypy

# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## 📊 Monitoring and Logging

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General application information
- **WARNING**: Warning messages
- **ERROR**: Error messages

### Log Format

Logs are structured with timestamps and context:

```
2025-07-12 12:30:45 - app.main - INFO - Starting AI Code Evaluator v1.0.0
2025-07-12 12:30:45 - app.main - INFO - Upload directory: ./uploads
2025-07-12 12:30:45 - app.main - INFO - Max file size: 104857600 bytes
```

### Metrics

The application provides basic metrics:

- Total evaluations
- Evaluations in progress
- Application uptime
- Version information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Use meaningful commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue on GitHub
- Check the documentation
- Review the logs for debugging

## 🔄 Changelog

### v1.0.0
- Initial production release
- Multi-model AI evaluation
- Specialized SQL analysis
- Production-ready logging
- Docker support
- Comprehensive API documentation 