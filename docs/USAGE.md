# AI Code Evaluator - Usage Guide

## Quick Start

### 1. Setup Environment

```bash
# Clone or download the project
cd ai-code-evaluator

# Copy environment template
cp env.example .env

# Edit .env file with your API keys
nano .env
```

### 2. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using the startup script
./start.sh
```

### 3. Start the Application

```bash
# Option 1: Using startup script (recommended)
./start.sh

# Option 2: Manual start
# Terminal 1 - FastAPI
uvicorn app.main:app --reload

# Terminal 2 - Streamlit Dashboard
streamlit run app/dashboard.py

# Option 3: Using Docker
docker-compose up
```

## Web Interface

### Streamlit Dashboard

Access the dashboard at: `http://localhost:8501`

**Features:**
- 📁 **Upload & Evaluate**: Upload ZIP files and start evaluations
- 📊 **Results Dashboard**: View detailed evaluation results with visualizations
- 📈 **Statistics**: View overall statistics and performance metrics
- 📚 **API Documentation**: Quick reference for API endpoints

### FastAPI Documentation

Access the interactive API docs at: `http://localhost:8000/docs`

## Command Line Interface

### Basic Usage

```bash
# Evaluate a file
python -m app.cli evaluate notebooks.zip --output results.json

# List evaluations
python -m app.cli list

# Get evaluation status
python -m app.cli status <evaluation_id>

# Get results
python -m app.cli results <evaluation_id> --output results.json

# Get statistics
python -m app.cli stats
```

### CLI Examples

```bash
# Evaluate without waiting
python -m app.cli evaluate notebooks.zip --no-wait

# Use different API server
python -m app.cli --api-url http://remote-server:8000 evaluate notebooks.zip

# Get help
python -m app.cli --help
python -m app.cli evaluate --help
```

## API Usage

### Upload and Evaluate

```bash
curl -X POST "http://localhost:8000/api/v1/evaluate" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@notebooks.zip"
```

Response:
```json
{
  "evaluation_id": "uuid-here",
  "filename": "notebooks.zip",
  "file_size": 1024,
  "message": "File uploaded and evaluation started successfully",
  "status": "pending"
}
```

### Check Status

```bash
curl "http://localhost:8000/api/v1/evaluations/{evaluation_id}/status"
```

Response:
```json
{
  "evaluation_id": "uuid-here",
  "status": "processing",
  "progress": 45.5,
  "total_cells": 10,
  "processed_cells": 4
}
```

### Get Results

```bash
curl "http://localhost:8000/api/v1/evaluations/{evaluation_id}/results"
```

### List Evaluations

```bash
curl "http://localhost:8000/api/v1/evaluations"
```

### Get Statistics

```bash
curl "http://localhost:8000/api/v1/statistics"
```

## Supported File Formats

### Input Files
- **ZIP archives** containing:
  - Jupyter notebooks (`.ipynb`)
  - Python files (`.py`)
  - SQL files (`.sql`)
  - Scala files (`.scala`) - treated as PySpark
  - R files (`.r`) - treated as Python

### Output Formats
- **JSON**: Detailed results with all scores and feedback
- **PDF**: Formatted reports (planned)
- **HTML**: Web-friendly reports (planned)

## Evaluation Criteria

The system evaluates code across 9 criteria:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| ✅ Correctness | 20% | Code logic and syntax accuracy |
| ⚡ Efficiency | 15% | Performance and resource usage |
| 📐 Readability | 15% | Code clarity and structure |
| 🚀 Scalability | 10% | Ability to handle larger datasets |
| 🔐 Security | 15% | Vulnerability assessment |
| 🧱 Modularity | 10% | Code organization and reusability |
| 💬 Documentation | 5% | Comments and documentation quality |
| 💡 Best Practices | 5% | Industry standards compliance |
| ⚠️ Error Handling | 5% | Robustness and error management |

## AI Models

### OpenAI GPT-4
- **Model**: `gpt-4` (configurable)
- **Max Tokens**: 4000 (configurable)
- **Temperature**: 0.3 (configurable)

### Google Gemini
- **Model**: `gemini-pro` (configurable)
- **Max Output Tokens**: 4000 (configurable)
- **Temperature**: 0.3 (configurable)

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
SECRET_KEY=your_secret_key

# Optional
DEBUG=false
REDIS_URL=redis://localhost:6379
MAX_FILE_SIZE=104857600  # 100MB
UPLOAD_DIR=./uploads
```

### Model Settings

```bash
OPENAI_MODEL=gpt-4
GEMINI_MODEL=gemini-pro
MAX_TOKENS=4000
TEMPERATURE=0.3
TIMEOUT=30
```

## Docker Deployment

### Quick Start

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Custom Configuration

```bash
# Build with custom settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

1. **API Keys Not Set**
   ```
   Error: Please set your API keys in the .env file
   ```
   Solution: Edit `.env` file and add valid API keys

2. **Redis Connection Failed**
   ```
   Error: Redis connection failed
   ```
   Solution: Start Redis server or check Redis configuration

3. **File Too Large**
   ```
   Error: File too large
   ```
   Solution: Increase `MAX_FILE_SIZE` in configuration or split files

4. **Evaluation Timeout**
   ```
   Error: Evaluation timeout
   ```
   Solution: Increase `TIMEOUT` setting or check AI model availability

### Debug Mode

Enable debug mode for detailed logging:

```bash
# In .env file
DEBUG=true

# Or environment variable
export DEBUG=true
```

### Logs

```bash
# Application logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f app

# Streamlit logs
streamlit run app/dashboard.py --logger.level debug
```

## Performance Optimization

### For Large Files
- Increase `MAX_FILE_SIZE` limit
- Use background processing
- Implement file chunking

### For High Throughput
- Scale with multiple instances
- Use Redis clustering
- Implement caching

### For Better AI Results
- Adjust temperature settings
- Increase max tokens
- Use model-specific prompts

## Security Considerations

### File Upload Security
- ZIP bomb protection
- File type validation
- Size limits
- Content sanitization

### API Security
- Rate limiting
- Input validation
- Error handling
- CORS configuration

### Environment Security
- Secure API key storage
- Environment variable management
- Docker security best practices

## Monitoring and Metrics

### Health Checks
```bash
curl http://localhost:8000/health
```

### Statistics
```bash
curl http://localhost:8000/api/v1/statistics
```

### Performance Metrics
- Processing time per cell
- Success/failure rates
- Model response times
- Resource usage

## Extending the Application

### Adding New Languages
1. Update `LanguageType` enum in `app/models.py`
2. Add language detection in `app/services/notebook_parser.py`
3. Update evaluation prompts for new language

### Adding New AI Models
1. Create new model client in `app/services/ai_evaluator.py`
2. Add model configuration in `app/config.py`
3. Update evaluation logic

### Custom Evaluation Criteria
1. Update `ScoreBreakdown` model
2. Modify evaluation prompts
3. Adjust scoring weights

## Support and Contributing

### Getting Help
- Check the troubleshooting section
- Review API documentation
- Run test suite: `python test_app.py`

### Contributing
1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

### Reporting Issues
- Include error messages
- Provide reproduction steps
- Share configuration details
- Include log files 