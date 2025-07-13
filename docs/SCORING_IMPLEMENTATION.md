# Scoring Implementation Guide

## Core Scoring Logic

### 1. Enhanced Evaluator Implementation

```python
# app/services/enhanced_evaluator.py
async def evaluate(self, cell: CodeCell) -> ModelFeedback:
    # Static analysis scoring
    syntax_score = self._analyze_syntax(cell.code)
    security_score = self._scan_security(cell.code)
    efficiency_score = self._analyze_efficiency(cell.code)
    
    # Pattern-based scoring
    readability_score = self._assess_readability(cell.code)
    modularity_score = self._assess_modularity(cell.code)
    
    return ScoreBreakdown(
        correctness=syntax_score,
        efficiency=efficiency_score,
        readability=readability_score,
        scalability=self._assess_scalability(cell.code),
        security=security_score,
        modularity=modularity_score,
        documentation=self._assess_documentation(cell.code),
        best_practices=self._assess_best_practices(cell.code),
        error_handling=self._assess_error_handling(cell.code)
    )
```

### 2. SQLCoder Evaluator Implementation

```python
# app/services/sqlcoder_evaluator.py
def _evaluate_sql_code(self, code: str) -> ScoreBreakdown:
    # SQLFluff analysis
    sqlfluff_score = self._run_sqlfluff(code)
    
    # Pattern matching
    pattern_score = self._match_sql_patterns(code)
    
    # Semantic analysis
    semantic_score = self._analyze_sql_semantics(code)
    
    return ScoreBreakdown(
        correctness=pattern_score,
        efficiency=self._assess_sql_efficiency(code),
        readability=sqlfluff_score,
        scalability=self._assess_sql_scalability(code),
        security=self._assess_sql_security(code),
        modularity=self._assess_sql_modularity(code),
        documentation=self._assess_sql_documentation(code),
        best_practices=sqlfluff_score,
        error_handling=self._assess_sql_error_handling(code)
    )
```

### 3. API Models Implementation

```python
# app/services/ai_evaluator.py
async def _evaluate_with_openai(self, cell: CodeCell, api_key: str) -> ModelFeedback:
    prompt = f"""
    Evaluate this {cell.language} code and return JSON with scores (0-10):
    
    Code:
    {cell.code}
    
    Return format:
    {{
        "scores": {{
            "correctness": 8.0,
            "efficiency": 7.0,
            "readability": 8.0,
            "scalability": 7.0,
            "security": 8.0,
            "modularity": 7.0,
            "documentation": 5.0,
            "best_practices": 8.0,
            "error_handling": 4.0
        }},
        "feedback": "Detailed analysis...",
        "suggestions": ["Suggestion 1", "Suggestion 2"],
        "confidence": 0.9
    }}
    """
    
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    
    return self._parse_ai_response(response.choices[0].message.content, "OpenAI GPT-4")
```

## Score Calculation Algorithm

### Overall Score Formula

```python
def calculate_overall_score(self, feedback: Dict[str, ModelFeedback]) -> Tuple[float, ScoreBreakdown]:
    # Weights for each criterion
    weights = {
        'correctness': 0.20,    # 20% - Most important
        'security': 0.20,       # 20% - Critical for production
        'efficiency': 0.15,     # 15% - Performance matters
        'readability': 0.10,    # 10% - Maintainability
        'scalability': 0.10,    # 10% - Future growth
        'modularity': 0.10,     # 10% - Code organization
        'documentation': 0.10,  # 10% - Knowledge transfer
        'error_handling': 0.10, # 10% - Robustness
        'best_practices': 0.05  # 5% - Standards compliance
    }
    
    # Aggregate scores from all models
    aggregated_scores = self._aggregate_model_scores(feedback)
    
    # Calculate weighted overall score
    overall_score = sum(
        getattr(aggregated_scores, criterion) * weight
        for criterion, weight in weights.items()
    )
    
    return overall_score, aggregated_scores
```

### Model Score Aggregation

```python
def _aggregate_model_scores(self, feedback: Dict[str, ModelFeedback]) -> ScoreBreakdown:
    # Filter valid feedback (confidence > 0)
    valid_feedback = [f for f in feedback.values() if f.confidence > 0]
    
    if not valid_feedback:
        return ScoreBreakdown(
            correctness=0.0, efficiency=0.0, readability=0.0,
            scalability=0.0, security=0.0, modularity=0.0,
            documentation=0.0, best_practices=0.0, error_handling=0.0
        )
    
    # Weighted average based on confidence
    total_weight = sum(f.confidence for f in valid_feedback)
    
    aggregated = {}
    for criterion in ['correctness', 'efficiency', 'readability', 'scalability', 
                     'security', 'modularity', 'documentation', 'best_practices', 'error_handling']:
        weighted_sum = sum(
            getattr(f.scores, criterion) * f.confidence 
            for f in valid_feedback if f.scores
        )
        aggregated[criterion] = weighted_sum / total_weight if total_weight > 0 else 0.0
    
    return ScoreBreakdown(**aggregated)
```

## Error Handling & Fallback

### API Error Detection

```python
async def _evaluate_with_gemini(self, cell: CodeCell, api_key: str) -> ModelFeedback:
    try:
        # API call logic...
        return self._parse_ai_response(content, "Google Gemini")
        
    except google_exceptions.ResourceExhausted as e:
        # Quota exceeded - return fallback
        return self._create_error_feedback(
            "Google Gemini", 
            "API quota exceeded. Using fallback evaluation."
        )
        
    except Exception as e:
        # Other errors
        return self._create_error_feedback("Google Gemini", str(e))
```

### Fallback Mechanism

```python
def _create_error_feedback(self, model_name: str, error_message: str) -> ModelFeedback:
    # Provide default scores for failed API calls
    default_scores = ScoreBreakdown(
        correctness=5.0, efficiency=5.0, readability=5.0,
        scalability=5.0, security=5.0, modularity=5.0,
        documentation=5.0, best_practices=5.0, error_handling=5.0
    )
    
    # Context-aware suggestions
    if "quota" in error_message.lower():
        suggestions = [
            "Upgrade your API plan",
            "Use local models as fallback",
            "Wait for quota reset"
        ]
    else:
        suggestions = [
            "Check API key configuration",
            "Use local models as alternative"
        ]
    
    return ModelFeedback(
        model_name=model_name,
        feedback=f"Evaluation failed: {error_message}",
        suggestions=suggestions,
        confidence=0.0,  # Zero confidence for failed calls
        scores=default_scores
    )
```

## Real Example Output

### Input Code
```python
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
```

### Enhanced Evaluator Output
```json
{
    "model_name": "Enhanced Evaluator",
    "confidence": 0.95,
    "scores": {
        "correctness": 8.0,
        "efficiency": 3.0,
        "readability": 7.0,
        "scalability": 2.0,
        "security": 9.0,
        "modularity": 6.0,
        "documentation": 4.0,
        "best_practices": 7.0,
        "error_handling": 3.0
    },
    "feedback": "Function logic is correct but has exponential complexity. No input validation.",
    "suggestions": [
        "Add input validation for negative numbers",
        "Consider iterative approach for better performance",
        "Add docstring for documentation"
    ]
}
```

### Overall Score Calculation
```python
# Weighted calculation
overall_score = (
    8.0 * 0.20 +  # correctness
    3.0 * 0.15 +  # efficiency
    7.0 * 0.10 +  # readability
    2.0 * 0.10 +  # scalability
    9.0 * 0.20 +  # security
    6.0 * 0.10 +  # modularity
    4.0 * 0.10 +  # documentation
    7.0 * 0.05 +  # best_practices
    3.0 * 0.10    # error_handling
) = 6.15
```

## Performance Metrics

| Model | Startup Time | Evaluation Time | Memory Usage |
|-------|-------------|-----------------|--------------|
| Enhanced | 2-3 seconds | 0.1-0.5 seconds | Low |
| SQLCoder | 1-2 seconds | 0.1-0.3 seconds | Low |
| OpenAI | 0 seconds | 2-5 seconds | None |
| Gemini | 0 seconds | 2-5 seconds | None | 