"""
AI Evaluator Service

Handles code evaluation using multiple AI models (OpenAI GPT-4 and Google Gemini).
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import openai
import google.generativeai as genai

from app.config import settings
from app.models import (
    ScoreBreakdown, 
    ModelFeedback, 
    LanguageType,
    CodeCell
)
from app.services.codebert_evaluator import CodeBERTEvaluator
from app.services.enhanced_evaluator import EnhancedEvaluator

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
        
        logger.info("AI Evaluator initialized with CodeBERT and Enhanced Task-Specific Evaluator")
        
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

CRITICAL: Respond with ONLY valid JSON. No markdown, no code blocks, no extra text. Start with { and end with }. All scores must be numbers 1-10.
"""
    
    async def evaluate_code_cell(
        self, 
        cell: CodeCell, 
        openai_api_key: Optional[str] = None, 
        google_api_key: Optional[str] = None,
        use_codebert: bool = True,
        use_openai: bool = False,
        use_gemini: bool = False
    ) -> Dict[str, ModelFeedback]:
        """Evaluate a code cell using selected AI models."""
        feedback = {}
        
        try:
            # Enhanced Task-Specific Evaluator (CodeBERT + Enhanced)
            if use_codebert:
                try:
                    enhanced_feedback = await self._evaluate_with_enhanced(cell)
                    feedback['enhanced'] = enhanced_feedback
                except Exception as e:
                    logger.error(f"Enhanced evaluation error: {e}")
                    feedback['enhanced'] = self._create_error_feedback('enhanced', str(e))
            

            # OpenAI GPT-4
            if use_openai and openai_api_key:
                try:
                    openai_feedback = await self._evaluate_with_openai(cell, openai_api_key)
                    feedback['openai'] = openai_feedback
                except Exception as e:
                    logger.error(f"OpenAI evaluation error: {e}")
                    feedback['openai'] = self._create_error_feedback('openai', str(e))
            
            # Google Gemini
            if use_gemini and google_api_key:
                try:
                    gemini_feedback = await self._evaluate_with_gemini(cell, google_api_key)
                    feedback['gemini'] = gemini_feedback
                except Exception as e:
                    logger.error(f"Gemini evaluation error: {e}")
                    feedback['gemini'] = self._create_error_feedback('gemini', str(e))
            
            # If no models selected, use enhanced by default
            if not feedback:
                try:
                    enhanced_feedback = await self._evaluate_with_enhanced(cell)
                    feedback['enhanced'] = enhanced_feedback
                except Exception as e:
                    logger.error(f"Default enhanced evaluation error: {e}")
                    feedback['enhanced'] = self._create_error_feedback('enhanced', str(e))
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            feedback['error'] = self._create_error_feedback('system', str(e))
        
        return feedback
    
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
            
        except Exception as e:
            logger.error(f"OpenAI evaluation error: {e}")
            return self._create_error_feedback("OpenAI GPT-4", str(e))
    
    async def _evaluate_with_gemini(self, cell: CodeCell, api_key: str) -> ModelFeedback:
        """Evaluate code using Google Gemini with provided API key."""
        try:
            # Create model with provided API key
            import google.generativeai as genai
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
                
                # Try to fix malformed JSON that starts with newlines
                if json_str.startswith('\\n'):
                    json_str = json_str.replace('\\n', '')
                
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
        return ModelFeedback(
            model_name=model_name,
            feedback=f"Evaluation failed: {error_message}",
            suggestions=["Please try again or contact support"],
            confidence=0.0
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