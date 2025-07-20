# Troubleshooting Guide

This guide helps you resolve common issues with the AI Assignment Evaluator.

## 🔑 API Key Issues

### "Google API key is required" Error

**Problem**: The application can't find your Google Gemini API key.

**Solutions**:
1. **Set environment variable**:
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```

2. **Create .env file**:
   ```bash
   echo "GOOGLE_API_KEY=your-api-key-here" > .env
   ```

3. **Use CLI with --api-key**:
   ```bash
   python cli.py evaluate --brief brief.yaml --solution submission.zip --api-key YOUR_KEY
   ```

4. **Check API key validity**:
   ```bash
   python cli.py test-connection --api-key YOUR_KEY
   ```

### "Invalid API key" Error

**Problem**: The API key is invalid or expired.

**Solutions**:
1. **Get a new API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Check API key format** - it should start with "AI"
3. **Verify billing** - ensure your Google Cloud account has billing enabled
4. **Check quotas** - ensure you haven't exceeded API limits

## 📁 File Upload Issues

### "No files found in ZIP archive" Error

**Problem**: The ZIP file is empty or corrupted.

**Solutions**:
1. **Check ZIP file contents**:
   ```bash
   unzip -l your_file.zip
   ```

2. **Recreate ZIP file**:
   ```bash
   zip -r new_file.zip your_files/
   ```

3. **Verify file structure** - ensure notebooks are in the root or subdirectories

### "Unsupported file format" Error

**Problem**: The assignment brief format isn't supported.

**Supported formats**:
- **JSON**: `.json` files
- **YAML**: `.yaml` or `.yml` files
- **PDF**: `.pdf` files
- **Text**: `.txt` or `.md` files
- **Word**: `.docx` files

**Solutions**:
1. **Convert to supported format**
2. **Use JSON format** (recommended):
   ```json
   {
     "title": "Assignment Title",
     "description": "Assignment description",
     "requirements": ["Requirement 1", "Requirement 2"],
     "expected_outputs": ["Output 1", "Output 2"]
   }
   ```

## 🌐 Web Interface Issues

### "Connection refused" Error

**Problem**: Can't access the web interface.

**Solutions**:
1. **Check if Streamlit is running**:
   ```bash
   streamlit run gemini_streamlit_app.py
   ```

2. **Verify port**:
   - Default: `http://localhost:8501`
   - Check for port conflicts

3. **Docker issues**:
   ```bash
   docker ps  # Check if container is running
   docker logs ai-assignment-evaluator  # Check logs
   ```

### "Page not found" Error

**Problem**: 404 errors in the web interface.

**Solutions**:
1. **Clear browser cache**
2. **Restart Streamlit**:
   ```bash
   pkill -f streamlit
   streamlit run gemini_streamlit_app.py
   ```

## 🔍 Evaluation Issues

### "Evaluation failed" Error

**Problem**: The evaluation process fails.

**Solutions**:
1. **Check file permissions**:
   ```bash
   chmod 755 uploads/
   chmod 644 your_files/*
   ```

2. **Verify file sizes** - ensure files aren't too large

3. **Check network connectivity** - ensure internet access for API calls

4. **Enable verbose mode**:
   ```bash
   python cli.py evaluate --brief brief.yaml --solution submission.zip --verbose
   ```

### "JSON parsing error" Error

**Problem**: Malformed JSON response from Gemini.

**Solutions**:
1. **Check debug output** in the web interface
2. **Retry evaluation** - sometimes API responses are malformed
3. **Simplify assignment brief** - complex briefs might cause parsing issues
4. **Check API response** in the debug expander

### "Zero scores" Issue

**Problem**: All notebooks show 0/100 scores.

**Possible causes**:
1. **Placeholder code** - notebooks contain only placeholder code
2. **Missing requirements** - notebooks don't implement assignment requirements
3. **API response issues** - malformed JSON causing score calculation problems

**Solutions**:
1. **Check notebook content** - ensure actual implementation exists
2. **Verify assignment brief** - ensure requirements are clear
3. **Review debug output** - check raw API response
4. **Test with sample data** - use provided sample assignments

## 🐳 Docker Issues

### "Container won't start" Error

**Problem**: Docker container fails to start.

**Solutions**:
1. **Check Docker logs**:
   ```bash
   docker logs ai-assignment-evaluator
   ```

2. **Verify environment variables**:
   ```bash
   docker run -e GOOGLE_API_KEY=your-key ai-assignment-evaluator
   ```

3. **Check port conflicts**:
   ```bash
   netstat -tulpn | grep 8501
   ```

4. **Rebuild image**:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

### "Permission denied" in Docker

**Problem**: Permission issues with mounted volumes.

**Solutions**:
1. **Fix volume permissions**:
   ```bash
   sudo chown -R $USER:$USER uploads/ data/ briefs/
   ```

2. **Use Docker volumes** instead of bind mounts:
   ```yaml
   volumes:
     - evaluator_data:/app/data
   ```

## 🔧 Performance Issues

### "Slow evaluation" Problem

**Problem**: Evaluations take too long.

**Solutions**:
1. **Check API quotas** - ensure you haven't hit rate limits
2. **Optimize file sizes** - reduce ZIP file size
3. **Use CLI for batch processing** - more efficient than web interface
4. **Check network latency** - use closer API endpoints if available

### "Memory issues" Problem

**Problem**: Application runs out of memory.

**Solutions**:
1. **Increase Docker memory**:
   ```bash
   docker run -m 4g ai-assignment-evaluator
   ```

2. **Process smaller files** - split large assignments
3. **Restart application** - clear memory cache

## 📊 Debugging

### Enable Debug Mode

**Web Interface**:
1. Open debug expanders in the UI
2. Check "Raw Response" and "Cleaned JSON" sections
3. Review error messages in the console

**CLI**:
```bash
python cli.py evaluate --brief brief.yaml --solution submission.zip --verbose
```

### Common Debug Commands

```bash
# Test API connection
python cli.py test-connection

# List supported types
python cli.py list-types

# Check file contents
unzip -l submission.zip

# Validate JSON
python -m json.tool brief.json

# Check environment
echo $GOOGLE_API_KEY
```

## 📞 Getting Help

If you're still experiencing issues:

1. **Check the logs** for detailed error messages
2. **Search existing issues** on GitHub
3. **Create a new issue** with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python version, etc.)
   - Sample files (if possible)

## 🔄 Common Workarounds

### API Rate Limiting
- **Wait and retry** - API has rate limits
- **Use CLI for batch processing** - more efficient
- **Check API quotas** in Google Cloud Console

### File Format Issues
- **Convert to JSON** - most reliable format
- **Simplify content** - remove complex formatting
- **Use text format** - most compatible

### Network Issues
- **Check firewall settings**
- **Use VPN if needed**
- **Try different network** 