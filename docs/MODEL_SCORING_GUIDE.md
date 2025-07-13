# Model Scoring Guide

## Overview
Each model uses different approaches to score code across 9 criteria (0-10 scale).

## 1. Enhanced Evaluator (Local Model)

### Scoring Method
- **Static Analysis**: Code structure, syntax, patterns
- **Security Scanning**: SQLFluff + Semgrep integration
- **Best Practices**: Industry standards compliance
- **Performance**: Code efficiency analysis

### Example Scores
```python
# Python Code Example
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Enhanced Evaluator Scores:
{
    "correctness": 8.0,      # ✅ Logic is correct
    "efficiency": 3.0,       # ❌ Exponential complexity
    "readability": 7.0,      # ✅ Clear structure
    "scalability": 2.0,      # ❌ Poor for large n
    "security": 9.0,         # ✅ No security issues
    "modularity": 6.0,       # ✅ Simple function
    "documentation": 4.0,    # ❌ No docstring
    "best_practices": 7.0,   # ✅ Follows Python style
    "error_handling": 3.0    # ❌ No input validation
}
```

## 2. SQLCoder Evaluator (Local Model)

### Scoring Method
- **Pattern Matching**: SQL syntax and structure analysis
- **SQLFluff Integration**: SQL formatting and style
- **Semantic Analysis**: Query logic evaluation
- **Best Practices**: SQL standards compliance

### Example Scores
```sql
-- SQL Code Example
SELECT * FROM users WHERE id = 1;

-- SQLCoder Evaluator Scores:
{
    "correctness": 7.0,      # ✅ Valid SQL syntax
    "efficiency": 6.0,       # ⚠️ Could use indexes
    "readability": 8.0,      # ✅ Clear and simple
    "scalability": 5.0,      # ⚠️ Limited to single user
    "security": 4.0,         # ❌ Potential SQL injection
    "modularity": 6.0,       # ✅ Simple query
    "documentation": 5.0,    # ⚠️ No comments
    "best_practices": 6.0,   # ⚠️ Basic query
    "error_handling": 5.0    # ⚠️ No error handling
}
```

## 3. OpenAI GPT-4 (API Model)

### Scoring Method
- **AI Analysis**: Deep understanding of code semantics
- **Context Awareness**: Industry best practices
- **Comprehensive Review**: Multiple aspects evaluation
- **Detailed Feedback**: Specific improvement suggestions

### Example Scores
```python
# Python Code Example
def process_data(data_list):
    result = []
    for item in data_list:
        if item > 0:
            result.append(item * 2)
    return result

# OpenAI GPT-4 Scores:
{
    "correctness": 9.0,      # ✅ Logic is sound
    "efficiency": 7.0,       # ✅ Linear complexity
    "readability": 8.0,      # ✅ Clear variable names
    "scalability": 7.0,      # ✅ Handles any list size
    "security": 8.0,         # ✅ No security issues
    "modularity": 7.0,       # ✅ Single responsibility
    "documentation": 5.0,    # ❌ Missing docstring
    "best_practices": 8.0,   # ✅ Good practices
    "error_handling": 4.0    # ❌ No input validation
}
```

## 4. Google Gemini (API Model)

### Scoring Method
- **AI-Powered Analysis**: Advanced code understanding
- **Pattern Recognition**: Identifies code patterns
- **Quality Assessment**: Comprehensive evaluation
- **Modern Standards**: Current best practices

### Example Scores
```javascript
// JavaScript Code Example
function calculateTotal(items) {
    let total = 0;
    for (let i = 0; i < items.length; i++) {
        total += items[i].price;
    }
    return total;
}

// Google Gemini Scores:
{
    "correctness": 8.0,      # ✅ Logic is correct
    "efficiency": 7.0,       # ✅ Linear time complexity
    "readability": 7.0,      # ✅ Clear variable names
    "scalability": 7.0,      # ✅ Handles any array size
    "security": 8.0,         # ✅ No obvious vulnerabilities
    "modularity": 7.0,       # ✅ Single purpose function
    "documentation": 4.0,    # ❌ No JSDoc comments
    "best_practices": 7.0,   # ✅ Good practices
    "error_handling": 3.0    # ❌ No error handling
}
```

## Scoring Criteria Breakdown

### 1. Correctness (0-10)
- **10**: Perfect logic, handles all edge cases
- **7-9**: Correct logic, minor issues
- **4-6**: Mostly correct, some bugs
- **0-3**: Major logic errors

### 2. Efficiency (0-10)
- **10**: Optimal algorithm, minimal resources
- **7-9**: Good performance, reasonable complexity
- **4-6**: Acceptable performance
- **0-3**: Poor performance, high complexity

### 3. Readability (0-10)
- **10**: Crystal clear, self-documenting
- **7-9**: Easy to understand, good naming
- **4-6**: Understandable with effort
- **0-3**: Confusing, poor structure

### 4. Scalability (0-10)
- **10**: Handles massive scale efficiently
- **7-9**: Scales well for typical use cases
- **4-6**: Limited scalability
- **0-3**: Poor scaling characteristics

### 5. Security (0-10)
- **10**: No vulnerabilities, secure by design
- **7-9**: Good security practices
- **4-6**: Some security concerns
- **0-3**: Major security vulnerabilities

### 6. Modularity (0-10)
- **10**: Perfect separation of concerns
- **7-9**: Good modular design
- **4-6**: Some modularity issues
- **0-3**: Monolithic, tightly coupled

### 7. Documentation (0-10)
- **10**: Comprehensive documentation
- **7-9**: Good documentation
- **4-6**: Basic documentation
- **0-3**: No documentation

### 8. Best Practices (0-10)
- **10**: Follows all industry standards
- **7-9**: Good adherence to practices
- **4-6**: Some best practices followed
- **0-3**: Poor practices

### 9. Error Handling (0-10)
- **10**: Comprehensive error handling
- **7-9**: Good error handling
- **4-6**: Basic error handling
- **0-3**: No error handling

## Model Comparison

| Model | Speed | Accuracy | Cost | Best For |
|-------|-------|----------|------|----------|
| Enhanced | Fast | High | Free | Quick analysis |
| SQLCoder | Fast | High | Free | SQL-specific |
| OpenAI | Slow | Very High | Paid | Deep analysis |
| Gemini | Slow | Very High | Paid | Comprehensive review |

## Implementation Details

### Score Calculation
```python
# Overall score calculation
overall_score = sum([
    scores.correctness * 0.2,
    scores.efficiency * 0.15,
    scores.readability * 0.1,
    scores.scalability * 0.1,
    scores.security * 0.2,
    scores.modularity * 0.1,
    scores.documentation * 0.1,
    scores.best_practices * 0.05,
    scores.error_handling * 0.1
])
```

### Confidence Scoring
- **1.0**: High confidence in evaluation
- **0.7-0.9**: Good confidence
- **0.4-0.6**: Moderate confidence
- **0.0-0.3**: Low confidence (API failures)

## Fallback Mechanism

When API models fail:
1. **Local models continue** evaluation
2. **API models return** error feedback
3. **Overall score** calculated from available models
4. **User notified** of fallback usage

## Usage Examples

### Local Models Only
```bash
# Fast, free evaluation
curl -X POST "http://localhost:8000/api/v1/evaluate" \
  -F "file=@code.ipynb" \
  -F "use_codebert=true" \
  -F "use_sqlcoder=true"
```

### API Models with Fallback
```bash
# Comprehensive evaluation with fallback
curl -X POST "http://localhost:8000/api/v1/evaluate" \
  -F "file=@code.ipynb" \
  -F "use_codebert=true" \
  -F "use_openai=true" \
  -F "openai_api_key=your_key"
``` 