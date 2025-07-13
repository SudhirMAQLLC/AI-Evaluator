# AI Code Evaluator - Deployment Guide

## 🚀 Streamlit Cloud Deployment

### Prerequisites
- GitHub repository with the code
- API keys for AI services (OpenAI, Google, Anthropic)

### Step-by-Step Deployment

#### 1. Prepare Your Repository
✅ **Already Done**: The repository is ready with all necessary files:
- `streamlit_app.py` - Main Streamlit app entry point
- `packages.txt` - System dependencies
- `.streamlit/config.toml` - Streamlit configuration
- `requirements.txt` - Python dependencies

#### 2. Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**: https://share.streamlit.io/
2. **Sign in** with your GitHub account
3. **Click "New app"**
4. **Configure your app**:
   - **Repository**: `SudhirMAQLLC/AI-Evaluator`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - **App URL**: Choose your preferred URL

#### 3. Configure Secrets

In Streamlit Cloud, go to your app settings and add these secrets:

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
GOOGLE_API_KEY = "your_google_api_key_here"
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"
```

#### 4. Deploy

Click "Deploy" and wait for the build to complete.

### 🔧 Local Development

#### Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

#### Alternative: Use Minimal Requirements
If you encounter dependency conflicts:
```bash
# Install minimal dependencies
pip install -r requirements-minimal.txt

# Run the app
streamlit run streamlit_app.py
```

#### Test the App
```bash
# Test on different port
streamlit run streamlit_app.py --server.port 8502
```

### 📁 Project Structure

```
AI-Evaluator/
├── app/
│   ├── dashboard.py          # Main Streamlit dashboard
│   ├── services/             # AI evaluation services
│   └── ...
├── streamlit_app.py          # Deployment entry point
├── packages.txt              # System dependencies
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml          # Streamlit configuration
└── DEPLOYMENT.md            # This file
```

### 🛠️ Troubleshooting

#### Common Issues

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **API Key Errors**: Verify secrets are correctly set in Streamlit Cloud
3. **Model Loading**: The app uses lightweight models for fast startup
4. **Dependency Conflicts**: If you encounter installation errors, try using `requirements-minimal.txt` instead
5. **Memory Issues**: The app is optimized for Streamlit Cloud's memory constraints

#### Debug Mode
```bash
# Run with debug logging
streamlit run streamlit_app.py --logger.level debug
```

### 🔄 Updates

To update the deployed app:
1. Make changes to your code
2. Commit and push to GitHub
3. Streamlit Cloud will automatically redeploy

### 📊 Monitoring

- **Logs**: Available in Streamlit Cloud dashboard
- **Performance**: Monitor app usage and response times
- **Errors**: Check logs for any deployment issues

### 🎯 Features Deployed

✅ **SQL Code Evaluation**: Upload SQL files or paste SQL code
✅ **Multi-Model Analysis**: Enhanced evaluator with comprehensive checks
✅ **Beautiful UI**: Modern card-based interface
✅ **Progress Tracking**: Real-time evaluation progress
✅ **Results Display**: Detailed scoring and feedback
✅ **History**: View recent evaluations

### 🔗 Useful Links

- **Streamlit Cloud**: https://share.streamlit.io/
- **Documentation**: https://docs.streamlit.io/
- **GitHub Repository**: https://github.com/SudhirMAQLLC/AI-Evaluator

---

**Deployment Status**: ✅ Ready for deployment
**Last Updated**: July 2024 