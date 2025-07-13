# API Error Handling and Fallback Mechanisms

## Overview

The AI Code Evaluator now includes robust error handling for API failures and automatic fallback mechanisms to ensure evaluations can always complete, even when external API services are unavailable or have quota limits.

## Error Types Handled

### Google Gemini API Errors

1. **Quota Exceeded (429)**
   - Error: `ResourceExhausted` with quota-related messages
   - Handling: Graceful fallback to local models
   - User Message: "API quota exceeded. Please upgrade your plan or try again later. Using fallback evaluation."

2. **Permission Denied**
   - Error: `PermissionDenied`
   - Handling: Clear error message with suggestions
   - User Message: "Permission denied: [details]"

3. **Invalid Arguments**
   - Error: `InvalidArgument`
   - Handling: Detailed error reporting
   - User Message: "Invalid argument: [details]"

### OpenAI API Errors

1. **Rate Limit Exceeded**
   - Error: `RateLimitError`
   - Handling: Graceful fallback to local models
   - User Message: "API rate limit exceeded. Please try again later or upgrade your plan. Using fallback evaluation."

2. **Quota Exceeded**
   - Error: `QuotaExceededError`
   - Handling: Graceful fallback to local models
   - User Message: "API quota exceeded. Please upgrade your plan or try again later. Using fallback evaluation."

3. **Authentication Failed**
   - Error: `AuthenticationError`
   - Handling: Clear error message with suggestions
   - User Message: "Authentication failed: [details]"

4. **Invalid Request**
   - Error: `InvalidRequestError`
   - Handling: Detailed error reporting
   - User Message: "Invalid request: [details]"

## Fallback Mechanisms

### Automatic Fallback

When API models fail, the system automatically:

1. **Continues with Local Models**: Uses Enhanced Evaluator and SQLCoder (if applicable)
2. **Provides Clear Feedback**: Shows which models failed and why
3. **Maintains Evaluation Quality**: Local models provide comprehensive analysis
4. **Suggests Solutions**: Offers specific advice for resolving API issues

### Fallback Configuration

```bash
# Environment variables for fallback behavior
AUTO_FALLBACK_TO_LOCAL=true
FALLBACK_MODELS=["enhanced", "sqlcoder"]
```

### Fallback Models

1. **Enhanced Evaluator**
   - Language: Python, SQL, JavaScript
   - Features: Static analysis, security scanning, best practices
   - Tools: SQLFluff, Semgrep, CodeBERT

2. **SQLCoder Evaluator**
   - Language: SQL only
   - Features: SQL-specific analysis, pattern matching
   - Tools: SQLFluff, semantic analysis

## User Experience

### Dashboard Warnings

The dashboard shows helpful warnings and information:

- ⚠️ API quota exceeded warnings
- 💡 Fallback protection notifications
- 🔧 Specific suggestions for resolving issues

### Error Messages

Error messages include:

- Clear explanation of the problem
- Specific suggestions for resolution
- Information about fallback mechanisms
- Confidence scores (0.0 for failed API calls)

### Suggestions Provided

Based on error type, users receive specific suggestions:

**For Quota/Rate Limit Errors:**
- Upgrade your API plan to increase quota limits
- Wait for quota reset and try again later
- Use local models (Enhanced Evaluator) as fallback
- Contact API provider for quota increase

**For Authentication Errors:**
- Check your API key configuration
- Verify API key is valid and active
- Ensure API key has proper permissions
- Use local models as alternative

**For General Errors:**
- Try using local models (Enhanced Evaluator)
- Check your internet connection
- Verify API service is available
- Contact support if issue persists

## Testing Error Handling

Use the test script to verify error handling:

```bash
python test_api_error_handling.py
```

This script tests:
1. Invalid API keys (triggers fallback)
2. Local models only (normal operation)
3. Mixed scenarios (API + local models)

## Configuration Options

### Environment Variables

```bash
# Fallback settings
AUTO_FALLBACK_TO_LOCAL=true
FALLBACK_MODELS=["enhanced", "sqlcoder"]

# API settings
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
```

### Model Selection

Users can control which models to use:

- **Local Models**: Enhanced Evaluator, SQLCoder (no API keys required)
- **API Models**: OpenAI GPT-4, Google Gemini (require API keys)
- **Mixed Mode**: Use both local and API models with automatic fallback

## Best Practices

1. **Always Enable Local Models**: Ensure Enhanced Evaluator is enabled as fallback
2. **Monitor API Usage**: Check quota limits before large evaluations
3. **Use Mixed Mode**: Combine local and API models for best results
4. **Test API Keys**: Use the dashboard's "Test API Keys" feature
5. **Plan for Failures**: Design workflows that work with local models only

## Troubleshooting

### Common Issues

1. **API Quota Exceeded**
   - Solution: Upgrade plan or wait for reset
   - Workaround: Use local models

2. **Authentication Failed**
   - Solution: Check API key configuration
   - Workaround: Use local models

3. **Rate Limits**
   - Solution: Reduce request frequency
   - Workaround: Use local models

4. **Network Issues**
   - Solution: Check internet connection
   - Workaround: Use local models

### Getting Help

- Check the logs for detailed error information
- Use the dashboard's error reporting
- Test with local models only to isolate issues
- Contact support with specific error messages 