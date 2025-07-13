"""
AI Evaluator Service

Handles code evaluation using multiple AI models (OpenAI GPT-4, Google Gemini, and Grok).
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import openai
import google.generativeai as genai
import requests

from app.config import settings
from app.models import (
    ScoreBreakdown, 
    ModelFeedback, 
    LanguageType,
    CodeCell
)
from app.services.codebert_evaluator import CodeBERTEvaluator
from app.services.enhanced_evaluator import EnhancedEvaluator
from app.services.sqlcoder_evaluator import SQLCoderEvaluator

logger = logging.getLogger(__name__)


class AIEvaluator:
    """AI-powered code evaluator using multiple models."""
    
    def __init__(self):
        """Initialize AI evaluator with API clients."""
        # Configure OpenAI API key for v0.x SDK
        openai.api_key = settings.openai_api_key
        genai.configure(api_key=settings.google_api_key)
        self.gemini_model = genai.GenerativeModel(settings.gemini_model)
        
        # Initialize evaluators
        self.codebert_evaluator = CodeBERTEvaluator()
        self.enhanced_evaluator = EnhancedEvaluator()
        # Use singleton for SQLCoderEvaluator
        from app.services.sqlcoder_evaluator import SQLCoderEvaluator
        self.sqlcoder_evaluator = SQLCoderEvaluator()
        
        logger.info("AI Evaluator initialized with CodeBERT, Enhanced Task-Specific Evaluator, SQLCoder, and Grok support")
        
        # Evaluation criteria and weights
        self.criteria = settings.evaluation_criteria
        
        # Evaluation prompts
        self.evaluation_prompt = self._create_evaluation_prompt()
    
    def _create_evaluation_prompt(self) -> str:
        """Create the evaluation prompt for AI models."""
        return """
You are an expert code reviewer and evaluator. Analyze the following code thoroughly and provide a detailed evaluation.

EVALUATION CRITERIA (Score 1-10 for each):

1. **Correctness**: Does the code work correctly? Check for:
   - Syntax errors
   - Logical errors
   - Runtime errors
   - Incorrect algorithms
   - Wrong data types

2. **Efficiency**: Is the code optimized? Consider:
   - Time complexity
   - Space complexity
   - Resource usage
   - Unnecessary operations
   - Algorithm choice

3. **Readability**: Is the code easy to understand? Evaluate:
   - Variable naming
   - Function naming
   - Code structure
   - Indentation
   - Code organization

4. **Scalability**: Can it handle growth? Check:
   - Performance with larger data
   - Memory usage patterns
   - Bottlenecks
   - Design patterns

5. **Security**: Are there vulnerabilities? Look for:
   - SQL injection
   - Input validation
   - Data exposure
   - Authentication issues
   - Authorization problems

6. **Modularity**: Is it well-organized? Consider:
   - Function separation
   - Code reusability
   - Single responsibility
   - Coupling/cohesion

7. **Documentation**: Is it well-documented? Check for:
   - Comments
   - Docstrings
   - README files
   - API documentation

8. **Best Practices**: Does it follow standards? Evaluate:
   - Language conventions
   - Design patterns
   - Code style
   - Industry standards

9. **Error Handling**: Are errors managed? Look for:
   - Try-catch blocks
   - Input validation
   - Graceful degradation
   - User feedback

ANALYSIS INSTRUCTIONS:
1. Read the code carefully
2. Identify specific issues and strengths
3. Score each criterion honestly (1-10)
4. Provide detailed feedback explaining your scores
5. Give specific, actionable suggestions

RESPONSE FORMAT (JSON only):
{
    "scores": {
        "correctness": 8,
        "efficiency": 7,
        "readability": 9,
        "scalability": 6,
        "security": 8,
        "modularity": 7,
        "documentation": 6,
        "best_practices": 8,
        "error_handling": 5
    },
    "feedback": "Detailed analysis explaining what the code does well and what needs improvement. Be specific about issues found.",
    "suggestions": [
        "Specific, actionable improvement suggestion 1",
        "Specific, actionable improvement suggestion 2",
        "Specific, actionable improvement suggestion 3"
    ],
    "confidence": 0.85
}

CODE TO EVALUATE:
Language: {language}
Code:
{code}

CRITICAL: Respond with ONLY valid JSON. No markdown, no code blocks, no extra text. Start with {{ and end with }}. All scores must be numbers 1-10. Do not include any formatting characters like \\n or \\t in the JSON.
"""
    
    async def evaluate_code_cell(
        self, 
        cell: CodeCell, 
        openai_api_key: Optional[str] = None, 
        google_api_key: Optional[str] = None,
        grok_api_key: Optional[str] = None,
        use_codebert: bool = True,
        use_sqlcoder: bool = False,
        use_openai: bool = False,
        use_gemini: bool = False,
        use_grok: bool = False
    ) -> Dict[str, ModelFeedback]:
        """Evaluate a code cell using selected AI models with parallel execution."""
        import threading
        import time
        import asyncio
        
        start_time = time.time()
        logger.info(f"Starting parallel evaluation with models: CodeBERT={use_codebert}, SQLCoder={use_sqlcoder}, OpenAI={use_openai}, Gemini={use_gemini}, Grok={use_grok}")
        
        # Thread-safe dictionary for results
        model_scores = {}
        
        # Define evaluation functions for threading
        def run_enhanced_evaluation():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._evaluate_with_enhanced(cell))
                model_scores['enhanced'] = result
                logger.info("Enhanced evaluation completed")
            except Exception as e:
                logger.error(f"Enhanced evaluation error: {e}")
                model_scores['enhanced'] = self._create_error_feedback('enhanced', str(e))
        
        def run_sqlcoder_evaluation():
            try:
                # Lazy load SQLCoderEvaluator only when needed
                sqlcoder_evaluator = SQLCoderEvaluator()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(sqlcoder_evaluator.evaluate(cell))
                model_scores['sqlcoder'] = result
                del sqlcoder_evaluator  # Release memory
                logger.info("SQLCoder evaluation completed")
            except Exception as e:
                logger.error(f"SQLCoder evaluation error: {e}")
                model_scores['sqlcoder'] = self._create_error_feedback('sqlcoder', str(e))
        
        def run_openai_evaluation():
            try:
                if not openai_api_key:
                    model_scores['openai'] = self._create_error_feedback('OpenAI GPT-4', "No API key provided")
                    return
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._evaluate_with_openai(cell, openai_api_key))
                model_scores['openai'] = result
                logger.info("OpenAI evaluation completed")
            except Exception as e:
                logger.error(f"OpenAI evaluation error: {e}")
                model_scores['openai'] = self._create_error_feedback('OpenAI GPT-4', str(e))
        
        def run_gemini_evaluation():
            try:
                if not google_api_key:
                    model_scores['gemini'] = self._create_error_feedback('Google Gemini', "No API key provided")
                    return
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._evaluate_with_gemini(cell, google_api_key))
                model_scores['gemini'] = result
                logger.info("Gemini evaluation completed")
            except Exception as e:
                logger.error(f"Gemini evaluation error: {e}")
                model_scores['gemini'] = self._create_error_feedback('Google Gemini', str(e))
        
        def run_grok_evaluation():
            try:
                if not grok_api_key:
                    model_scores['grok'] = self._create_error_feedback('Grok', "No API key provided")
                    return
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._evaluate_with_grok(cell, grok_api_key))
                model_scores['grok'] = result
                logger.info("Grok evaluation completed")
            except Exception as e:
                logger.error(f"Grok evaluation error: {e}")
                model_scores['grok'] = self._create_error_feedback('Grok', str(e))
        
        # Start evaluation threads based on selected models
        threads = []
        
        if use_codebert:
            thread = threading.Thread(target=run_enhanced_evaluation)
            threads.append(thread)
            thread.start()
        
        if use_sqlcoder:
            thread = threading.Thread(target=run_sqlcoder_evaluation)
            threads.append(thread)
            thread.start()
        
        if use_openai:
            thread = threading.Thread(target=run_openai_evaluation)
            threads.append(thread)
            thread.start()
        
        if use_gemini:
            thread = threading.Thread(target=run_gemini_evaluation)
            threads.append(thread)
            thread.start()
        
        if use_grok:
            thread = threading.Thread(target=run_grok_evaluation)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        evaluation_time = time.time() - start_time
        logger.info(f"Parallel evaluation completed in {evaluation_time:.2f} seconds")
        
        return model_scores
    
    async def _evaluate_with_openai(self, cell: CodeCell, api_key: str) -> ModelFeedback:
        """Evaluate code using OpenAI GPT-4 with provided API key."""
        try:
            # Use OpenAI v0.x async API
            import openai
            
            openai.api_key = api_key
            
            prompt = self.evaluation_prompt.format(
                language=cell.language.value,
                code=cell.code
            )
            
            response = await openai.ChatCompletion.acreate(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer and evaluator. Analyze the code thoroughly and provide detailed feedback."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            content = response.choices[0].message.content
            return self._parse_ai_response(content, "OpenAI GPT-4")
            
        except openai.error.RateLimitError as e:
            logger.warning(f"OpenAI API rate limit exceeded: {e}")
            return self._create_error_feedback(
                "OpenAI GPT-4", 
                "API rate limit exceeded. Please try again later or upgrade your plan. Using fallback evaluation."
            )
            
        except openai.error.QuotaExceededError as e:
            logger.warning(f"OpenAI API quota exceeded: {e}")
            return self._create_error_feedback(
                "OpenAI GPT-4", 
                "API quota exceeded. Please upgrade your plan or try again later. Using fallback evaluation."
            )
            
        except openai.error.AuthenticationError as e:
            logger.error(f"OpenAI API authentication failed: {e}")
            return self._create_error_feedback("OpenAI GPT-4", f"Authentication failed: {e}")
            
        except openai.error.InvalidRequestError as e:
            logger.error(f"OpenAI API invalid request: {e}")
            return self._create_error_feedback("OpenAI GPT-4", f"Invalid request: {e}")
            
        except Exception as e:
            logger.error(f"OpenAI evaluation error: {e}")
            return self._create_error_feedback("OpenAI GPT-4", str(e))
    
    async def _evaluate_with_gemini(self, cell: CodeCell, api_key: str) -> ModelFeedback:
        """Evaluate code using Google Gemini with provided API key."""
        try:
            # Create model with provided API key
            import google.generativeai as genai
            from google.api_core import exceptions as google_exceptions
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(settings.gemini_model)
            
            prompt = self.evaluation_prompt.format(
                language=cell.language.value,
                code=cell.code
            )
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=settings.max_tokens,
                    temperature=settings.temperature
                )
            )
            
            content = response.text
            return self._parse_ai_response(content, "Google Gemini")
            
        except google_exceptions.ResourceExhausted as e:
            # Handle quota exceeded errors
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                logger.warning(f"Google API quota exceeded: {error_msg}")
                return self._create_error_feedback(
                    "Google Gemini", 
                    "API quota exceeded. Please upgrade your plan or try again later. Using fallback evaluation."
                )
            else:
                logger.error(f"Google API resource exhausted: {error_msg}")
                return self._create_error_feedback("Google Gemini", f"Resource exhausted: {error_msg}")
                
        except google_exceptions.PermissionDenied as e:
            logger.error(f"Google API permission denied: {e}")
            return self._create_error_feedback("Google Gemini", f"Permission denied: {e}")
            
        except google_exceptions.InvalidArgument as e:
            logger.error(f"Google API invalid argument: {e}")
            return self._create_error_feedback("Google Gemini", f"Invalid argument: {e}")
            
        except Exception as e:
            logger.error(f"Gemini evaluation error: {e}")
            return self._create_error_feedback("Google Gemini", str(e))
    
    async def _evaluate_with_enhanced(self, cell: CodeCell) -> ModelFeedback:
        """Evaluate code using Enhanced Task-Specific Evaluator."""
        try:
            # Use the enhanced evaluator for comprehensive analysis
            enhanced_result = await self.enhanced_evaluator.evaluate(cell)
            return enhanced_result
        except Exception as e:
            logger.error(f"Enhanced evaluation failed: {e}")
            return self._create_error_feedback('enhanced', str(e))
    
    async def _evaluate_with_grok(self, cell: CodeCell, api_key: str) -> ModelFeedback:
        """Evaluate code using Grok API with provided API key."""
        try:
            # Use Grok API (powered by Anthropic)
            from anthropic import Anthropic
            
            # Initialize client with proxy handling
            try:
                client = Anthropic(api_key=api_key)
            except TypeError as e:
                if "proxies" in str(e):
                    # Handle proxies argument issue
                    import os
                    # Temporarily remove any proxy environment variables
                    old_proxy_vars = {}
                    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                        if var in os.environ:
                            old_proxy_vars[var] = os.environ[var]
                            del os.environ[var]
                    
                    try:
                        client = Anthropic(api_key=api_key)
                    finally:
                        # Restore proxy environment variables
                        for var, value in old_proxy_vars.items():
                            os.environ[var] = value
                else:
                    raise e
            
            prompt = self.evaluation_prompt.format(
                language=cell.language.value,
                code=cell.code
            )
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Use Claude model for Grok-like evaluation
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = response.content[0].text
            
            return self._parse_ai_response(content, "Grok")
            
        except Exception as e:
            logger.error(f"Grok evaluation error: {e}")
            return self._create_error_feedback("Grok", str(e))
    

    

    

    
    def _parse_ai_response(self, content: str, model_name: str) -> ModelFeedback:
        """Parse AI model response into structured feedback."""
        try:
            # Clean the content - remove extra whitespace and newlines
            content = content.strip()
            logger.info(f"Cleaned content: {repr(content[:200])}")
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = content[json_start:json_end]
            logger.info(f"Extracted JSON: {repr(json_str[:200])}")
            
            # Try to parse the JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as json_error:
                # If JSON parsing fails, try to clean it further
                logger.warning(f"Initial JSON parsing failed for {model_name}, trying to clean response. Error: {json_error}")
                
                # Remove any markdown formatting
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                
                # Try to fix common JSON issues
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                json_str = ' '.join(json_str.split())  # Normalize whitespace
                
                # Try to fix malformed JSON that starts with newlines or has escaped newlines
                json_str = json_str.replace('\\n', '')
                json_str = json_str.replace('\\t', '')
                json_str = json_str.replace('\\r', '')
                
                # Remove any leading/trailing whitespace and quotes
                json_str = json_str.strip().strip('"').strip("'")
                
                logger.info(f"Cleaned JSON: {repr(json_str[:200])}")
                data = json.loads(json_str)
            
            # Extract scores
            scores_data = data.get("scores", {})
            
            # Validate that scores are numeric
            def validate_score(score, default=5.0):
                if isinstance(score, (int, float)):
                    return float(score)
                elif isinstance(score, str):
                    try:
                        return float(score)
                    except ValueError:
                        return default
                return default
            
            # Create ScoreBreakdown object with validated scores
            scores = ScoreBreakdown(
                correctness=validate_score(scores_data.get("correctness"), 5.0),
                efficiency=validate_score(scores_data.get("efficiency"), 5.0),
                readability=validate_score(scores_data.get("readability"), 5.0),
                scalability=validate_score(scores_data.get("scalability"), 5.0),
                security=validate_score(scores_data.get("security"), 5.0),
                modularity=validate_score(scores_data.get("modularity"), 5.0),
                documentation=validate_score(scores_data.get("documentation"), 5.0),
                best_practices=validate_score(scores_data.get("best_practices"), 5.0),
                error_handling=validate_score(scores_data.get("error_handling"), 5.0)
            )
            
            # Extract feedback and suggestions
            feedback_text = data.get("feedback", "No feedback provided")
            suggestions = data.get("suggestions", [])
            confidence = validate_score(data.get("confidence"), 0.5)
            
            return ModelFeedback(
                model_name=model_name,
                feedback=feedback_text,
                suggestions=suggestions,
                confidence=confidence,
                scores=scores
            )
            
        except Exception as e:
            logger.error(f"Failed to parse {model_name} response: {e}")
            logger.error(f"Raw content: {content[:500]}...")  # Log first 500 chars for debugging
            
            # Try to extract some basic information from the response even if JSON parsing fails
            try:
                # Look for any numeric scores in the text
                import re
                score_pattern = r'(\d+(?:\.\d+)?)\s*(?:out of\s*10|/10|score)'
                scores_found = re.findall(score_pattern, content.lower())
                
                if scores_found:
                    # Use the first few scores found
                    scores_list = [float(s) for s in scores_found[:9]]  # Take up to 9 scores
                    while len(scores_list) < 9:
                        scores_list.append(5.0)  # Default score
                    
                    scores = ScoreBreakdown(
                        correctness=scores_list[0] if len(scores_list) > 0 else 5.0,
                        efficiency=scores_list[1] if len(scores_list) > 1 else 5.0,
                        readability=scores_list[2] if len(scores_list) > 2 else 5.0,
                        scalability=scores_list[3] if len(scores_list) > 3 else 5.0,
                        security=scores_list[4] if len(scores_list) > 4 else 5.0,
                        modularity=scores_list[5] if len(scores_list) > 5 else 5.0,
                        documentation=scores_list[6] if len(scores_list) > 6 else 5.0,
                        best_practices=scores_list[7] if len(scores_list) > 7 else 5.0,
                        error_handling=scores_list[8] if len(scores_list) > 8 else 5.0
                    )
                    
                    return ModelFeedback(
                        model_name=model_name,
                        feedback=f"Parsed from text response: {content[:200]}...",
                        suggestions=["Consider improving code structure"],
                        confidence=0.3,
                        scores=scores
                    )
            except Exception as fallback_error:
                logger.error(f"Fallback parsing also failed: {fallback_error}")
            
            return self._create_error_feedback(model_name, f"Failed to parse response: {e}")
    
    def _create_error_feedback(self, model_name: str, error_message: str) -> ModelFeedback:
        """Create error feedback when evaluation fails."""
        # Create default scores for error cases
        default_scores = ScoreBreakdown(
            correctness=5.0,
            efficiency=5.0,
            readability=5.0,
            scalability=5.0,
            security=5.0,
            modularity=5.0,
            documentation=5.0,
            best_practices=5.0,
            error_handling=5.0
        )
        
        # Provide specific suggestions based on error type
        if "quota" in error_message.lower() or "rate limit" in error_message.lower():
            suggestions = [
                "Upgrade your API plan to increase quota limits",
                "Wait for quota reset and try again later",
                "Use local models (Enhanced Evaluator) as fallback",
                "Contact API provider for quota increase"
            ]
        elif "authentication" in error_message.lower():
            suggestions = [
                "Check your API key configuration",
                "Verify API key is valid and active",
                "Ensure API key has proper permissions",
                "Use local models as alternative"
            ]
        else:
            suggestions = [
                "Try using local models (Enhanced Evaluator)",
                "Check your internet connection",
                "Verify API service is available",
                "Contact support if issue persists"
            ]
        
        return ModelFeedback(
            model_name=model_name,
            feedback=f"Evaluation failed: {error_message}",
            suggestions=suggestions,
            confidence=0.0,
            scores=default_scores
        )
    

    
    def calculate_overall_score(self, feedback: Dict[str, ModelFeedback]) -> Tuple[float, ScoreBreakdown]:
        """Calculate overall score and breakdown from model feedback."""
        try:
            # Check if we have valid feedback from any model
            valid_feedback = [f for f in feedback.values() if f.confidence > 0 and "Evaluation failed" not in f.feedback]
            
            if not valid_feedback:
                # No valid feedback available, return error scores
                scores = ScoreBreakdown(
                    correctness=0.0,
                    efficiency=0.0,
                    readability=0.0,
                    scalability=0.0,
                    security=0.0,
                    modularity=0.0,
                    documentation=0.0,
                    best_practices=0.0,
                    error_handling=0.0
                )
                return 0.0, scores
            
            # Use the most confident model's scores
            best_model = max(valid_feedback, key=lambda x: x.confidence)
            
            # Use the actual scores from the model feedback
            if best_model.scores:
                scores = best_model.scores
            else:
                # No scores available from AI models
                scores = ScoreBreakdown(
                    correctness=0.0,
                    efficiency=0.0,
                    readability=0.0,
                    scalability=0.0,
                    security=0.0,
                    modularity=0.0,
                    documentation=0.0,
                    best_practices=0.0,
                    error_handling=0.0
                )
            
            # Calculate overall score as average
            overall_score = sum([
                scores.correctness, scores.efficiency, scores.readability,
                scores.scalability, scores.security, scores.modularity,
                scores.documentation, scores.best_practices, scores.error_handling
            ]) / 9.0
            
            return overall_score, scores
            
        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            # Return error scores
            error_scores = ScoreBreakdown(
                correctness=0.0,
                efficiency=0.0,
                readability=0.0,
                scalability=0.0,
                security=0.0,
                modularity=0.0,
                documentation=0.0,
                best_practices=0.0,
                error_handling=0.0
            )
            return 0.0, error_scores
    
    def aggregate_suggestions(self, feedback: Dict[str, ModelFeedback]) -> List[str]:
        """Aggregate suggestions from all models."""
        suggestions = set()
        
        for model_feedback in feedback.values():
            suggestions.update(model_feedback.suggestions)
        
        return list(suggestions)
    
    def identify_issues(self, feedback: Dict[str, ModelFeedback]) -> List[str]:
        """Identify common issues across model evaluations."""
        issues = []
        
        for model_feedback in feedback.values():
            # Look for common issue patterns in feedback
            if "error" in model_feedback.feedback.lower():
                issues.append("Code contains errors")
            if "security" in model_feedback.feedback.lower() and "vulnerability" in model_feedback.feedback.lower():
                issues.append("Security vulnerabilities detected")
            if "performance" in model_feedback.feedback.lower():
                issues.append("Performance issues identified")
        
        return list(set(issues))


# Global evaluator instance
evaluator = AIEvaluator() 