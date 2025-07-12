#!/usr/bin/env python3
"""
Enhanced Code Evaluator
Implements task-specific evaluation using the best tools for each metric:
- Formatting & Linting: SQLFluff
- Security Flaws Detection: Semgrep + LLM
- Code Explanation: Enhanced rule-based analysis
- Scoring: Custom weighted scoring system
- SQL correctness: Enhanced SQL analysis
"""

import re
import ast
import json
import logging
import subprocess
import tempfile
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from app.models import ScoreBreakdown, ModelFeedback
from app.services.sql_specialized_evaluator import SQLSpecializedEvaluator

import sqlparse
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

logger = logging.getLogger(__name__)

@dataclass
class TaskScores:
    """Task-specific scores for enhanced evaluation."""
    formatting_linting: float
    security_detection: float
    code_explanation: float
    sql_correctness: float
    overall_quality: float

class EnhancedEvaluator:
    """Enhanced evaluator using task-specific tools and analysis."""
    
    def __init__(self):
        """Initialize enhanced evaluator with external tools."""
        # Check for external tools
        self.sqlfluff_available = self._check_sqlfluff()
        self.semgrep_available = self._check_semgrep()
        
        # Initialize specialized evaluators
        self.sql_evaluator = SQLSpecializedEvaluator()
        
        logger.info(f"Enhanced Evaluator initialized - SQLFluff: {self.sqlfluff_available}, Semgrep: {self.semgrep_available}")
        
        # Task weights for final scoring
        self.task_weights = {
            'formatting_linting': 0.15,
            'security_detection': 0.25,
            'code_explanation': 0.20,
            'sql_correctness': 0.30,
            'overall_quality': 0.10
        }
    
    def _check_sqlfluff(self) -> bool:
        """Check if SQLFluff is available."""
        try:
            result = subprocess.run(['sqlfluff', '--version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_semgrep(self) -> bool:
        """Check if Semgrep is available."""
        try:
            result = subprocess.run(['semgrep', '--version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def evaluate_code(self, code: str, language: str) -> ModelFeedback:
        """Evaluate code using task-specific analysis."""
        try:
            logger.info(f"Starting enhanced evaluation for {language} code")
            
            # Run task-specific evaluations
            task_scores = self._evaluate_tasks(code, language)
            
            # Convert to standard score breakdown
            scores = self._convert_to_score_breakdown(task_scores, code, language)
            
            # Generate comprehensive feedback
            feedback, suggestions = self._generate_enhanced_feedback(task_scores, code, language)
            
            # Calculate confidence based on tool availability
            confidence = self._calculate_confidence(task_scores)
            
            logger.info(f"Enhanced evaluation completed. Overall: {scores.correctness:.1f}, Security: {scores.security:.1f}")
            
            return ModelFeedback(
                model_name="Enhanced Task-Specific Evaluator",
                feedback=feedback,
                suggestions=suggestions,
                confidence=confidence,
                scores=scores
            )
            
        except Exception as e:
            logger.error(f"Enhanced evaluation failed: {e}")
            return self._create_error_feedback(f"Enhanced evaluation failed: {e}")
    
    def _evaluate_tasks(self, code: str, language: str) -> TaskScores:
        """Evaluate code using task-specific tools."""
        scores = TaskScores(
            formatting_linting=0.0,
            security_detection=0.0,
            code_explanation=0.0,
            sql_correctness=0.0,
            overall_quality=0.0
        )
        
        if language.lower() == 'sql':
            # --- Rule-based static analysis using sqlglot/sqlparse ---
            static_results = self._static_sql_analysis(code)
            # --- Model-based scoring (CodeBERT, CodeT5+, StarCoder) ---
            model_scores = self._model_based_sql_scoring(code)
            # --- Aggregate scores ---
            scores.formatting_linting = 0.5 * static_results['readability'] + 0.5 * model_scores['readability']
            scores.security_detection = 0.5 * static_results['security'] + 0.5 * model_scores['security']
            scores.code_explanation = 0.5 * static_results['best_practices'] + 0.5 * model_scores['best_practices']
            scores.sql_correctness = 0.5 * static_results['correctness'] + 0.5 * model_scores['correctness']
            scores.overall_quality = 0.5 * static_results['efficiency'] + 0.5 * model_scores['efficiency']
            return scores
        
        else:
            # For non-SQL languages, use enhanced rule-based analysis
            scores.formatting_linting = self._evaluate_generic_formatting(code, language)
            scores.security_detection = self._evaluate_generic_security(code, language)
            scores.code_explanation = self._evaluate_generic_explanation(code, language)
            scores.sql_correctness = 10.0  # Not applicable for non-SQL
            scores.overall_quality = self._evaluate_generic_quality(code, language)
        
        return scores
    
    def _evaluate_formatting_linting(self, code: str) -> float:
        """Task 1: Formatting & Linting using SQLFluff."""
        if not self.sqlfluff_available:
            return self._evaluate_formatting_rule_based(code)
        
        try:
            # Create temporary file for SQLFluff analysis
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            # Run SQLFluff
            result = subprocess.run(
                ['sqlfluff', 'lint', temp_file_path, '--format', 'json'],
                capture_output=True, text=True, timeout=30
            )
            
            # Clean up
            os.unlink(temp_file_path)
            
            if result.returncode == 0:
                # No issues found
                return 10.0
            else:
                try:
                    issues = json.loads(result.stdout)
                    violation_count = sum(len(file_issues) for file_issues in issues.values())
                    
                    # Score based on violation count
                    if violation_count == 0:
                        return 10.0
                    elif violation_count <= 2:
                        return 8.0
                    elif violation_count <= 5:
                        return 6.0
                    elif violation_count <= 10:
                        return 4.0
                    else:
                        return 2.0
                except:
                    return self._evaluate_formatting_rule_based(code)
        
        except Exception as e:
            logger.error(f"SQLFluff evaluation failed: {e}")
            return self._evaluate_formatting_rule_based(code)
    
    def _evaluate_formatting_rule_based(self, code: str) -> float:
        """Rule-based formatting evaluation."""
        score = 10.0
        
        # Check for consistent indentation
        lines = code.split('\n')
        indent_sizes = set()
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                indent_sizes.add(indent)
        
        if len(indent_sizes) > 3:
            score -= 2.0
        
        # Check for proper spacing around operators
        if not re.search(r'\s+[=<>!]+\s+', code):
            score -= 1.0
        
        # Check for consistent case
        if re.search(r'select|SELECT', code) and re.search(r'Select', code):
            score -= 1.0
        
        return max(1.0, score)
    
    def _evaluate_security_detection(self, code: str) -> float:
        """Task 2: Security Flaws Detection using Semgrep + LLM."""
        if not self.semgrep_available:
            return self._evaluate_security_rule_based(code)
        
        try:
            # Create temporary file for Semgrep analysis
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            # Run Semgrep with SQL security rules
            result = subprocess.run(
                ['semgrep', '--config=auto', '--json', temp_file_path],
                capture_output=True, text=True, timeout=30
            )
            
            # Clean up
            os.unlink(temp_file_path)
            
            if result.returncode == 0:
                try:
                    issues = json.loads(result.stdout)
                    security_issues = len(issues.get('results', []))
                    
                    # Score based on security issues
                    if security_issues == 0:
                        return 10.0
                    elif security_issues == 1:
                        return 7.0
                    elif security_issues == 2:
                        return 4.0
                    else:
                        return 1.0
                except:
                    return self._evaluate_security_rule_based(code)
            else:
                return self._evaluate_security_rule_based(code)
        
        except Exception as e:
            logger.error(f"Semgrep evaluation failed: {e}")
            return self._evaluate_security_rule_based(code)
    
    def _evaluate_security_rule_based(self, code: str) -> float:
        """Rule-based security evaluation."""
        score = 10.0
        
        # SQL Injection patterns
        if re.search(r'OR[\s]+[\'"]?1[\'"]?[\s]*=[\s]*[\'"]?1[\'"]?', code, re.IGNORECASE):
            score -= 9.0  # Critical vulnerability
        
        # String concatenation in queries
        if re.search(r'[\'"]\s*\+\s*[\w]+\s*\+\s*[\'"]', code):
            score -= 5.0
        
        # SELECT * on sensitive tables
        if re.search(r'SELECT\s+\*', code, re.IGNORECASE):
            score -= 2.0
        
        # DELETE/UPDATE without WHERE
        if re.search(r'(DELETE|UPDATE)\s+FROM?\s+[\w]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE) and not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
            score -= 8.0  # Critical issue
        
        return max(1.0, score)
    
    def _evaluate_code_explanation(self, code: str) -> float:
        """Task 3: Code Explanation using enhanced rule-based analysis."""
        score = 10.0
        
        # Check for comments
        comment_lines = len([line for line in code.split('\n') if line.strip().startswith('--') or line.strip().startswith('/*')])
        total_lines = len([line for line in code.split('\n') if line.strip()])
        
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            if comment_ratio < 0.1:
                score -= 3.0
            elif comment_ratio < 0.2:
                score -= 1.0
        
        # Check for meaningful variable names
        if re.search(r'SELECT\s+([a-z_]+)', code, re.IGNORECASE):
            score += 1.0
        
        # Check for clear structure
        if re.search(r'GROUP BY|ORDER BY|HAVING', code, re.IGNORECASE):
            score += 1.0
        
        return min(10.0, max(1.0, score))
    
    def _evaluate_sql_correctness(self, code: str) -> float:
        """Task 4: SQL Correctness using enhanced analysis."""
        score = 10.0
        
        # Check for basic SQL syntax
        if not re.search(r'SELECT\s+', code, re.IGNORECASE):
            score -= 5.0
        
        # Check for balanced parentheses
        open_parens = code.count('(')
        close_parens = code.count(')')
        if open_parens != close_parens:
            score -= 3.0
        
        # Check for proper JOIN syntax
        if re.search(r'JOIN\s+[\w]+\s+ON', code, re.IGNORECASE):
            score += 1.0
        
        # Check for proper WHERE clause
        if re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
            score += 1.0
        
        # Check for proper GROUP BY
        if re.search(r'GROUP BY\s+[\w,\s]+', code, re.IGNORECASE):
            score += 1.0
        
        return min(10.0, max(1.0, score))
    
    def _evaluate_overall_quality(self, code: str) -> float:
        """Task 5: Overall Quality assessment."""
        score = 10.0
        
        # Check for code length (not too long, not too short)
        lines = len([line for line in code.split('\n') if line.strip()])
        if lines < 3:
            score -= 2.0
        elif lines > 50:
            score -= 1.0
        
        # Check for complexity
        if re.search(r'UNION|INTERSECT|EXCEPT', code, re.IGNORECASE):
            score += 1.0  # Shows advanced SQL knowledge
        
        # Check for performance considerations
        if re.search(r'LIMIT\s+\d+', code, re.IGNORECASE):
            score += 1.0
        
        return min(10.0, max(1.0, score))
    
    def _evaluate_generic_formatting(self, code: str, language: str) -> float:
        """Generic formatting evaluation for non-SQL languages."""
        score = 10.0
        
        # Check indentation
        lines = code.split('\n')
        for line in lines:
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                if not line.startswith('#'):  # Allow comments
                    score -= 1.0
                    break
        
        return max(1.0, score)
    
    def _evaluate_generic_security(self, code: str, language: str) -> float:
        """Generic security evaluation for non-SQL languages."""
        score = 10.0
        
        # Check for hardcoded credentials
        if re.search(r'password\s*=\s*[\'"][^\'"]+[\'"]', code, re.IGNORECASE):
            score -= 5.0
        
        # Check for eval() usage
        if 'eval(' in code:
            score -= 8.0
        
        return max(1.0, score)
    
    def _evaluate_generic_explanation(self, code: str, language: str) -> float:
        """Generic code explanation evaluation."""
        score = 10.0
        
        # Check for comments
        comment_lines = len([line for line in code.split('\n') if line.strip().startswith('#')])
        total_lines = len([line for line in code.split('\n') if line.strip()])
        
        if total_lines > 0 and comment_lines / total_lines < 0.1:
            score -= 2.0
        
        return max(1.0, score)
    
    def _evaluate_generic_quality(self, code: str, language: str) -> float:
        """Generic quality evaluation."""
        return 8.0  # Default good score for non-SQL
    
    def _convert_to_score_breakdown(self, task_scores: TaskScores, code: str, language: str) -> ScoreBreakdown:
        """Convert task scores to standard score breakdown."""
        # Calculate weighted overall score
        overall_score = (
            task_scores.formatting_linting * self.task_weights['formatting_linting'] +
            task_scores.security_detection * self.task_weights['security_detection'] +
            task_scores.code_explanation * self.task_weights['code_explanation'] +
            task_scores.sql_correctness * self.task_weights['sql_correctness'] +
            task_scores.overall_quality * self.task_weights['overall_quality']
        )
        
        # Map task scores to standard breakdown
        return ScoreBreakdown(
            correctness=task_scores.sql_correctness if language.lower() == 'sql' else 8.0,
            efficiency=self._calculate_efficiency_score(code, language),
            readability=task_scores.formatting_linting,
            scalability=task_scores.overall_quality,
            security=task_scores.security_detection,
            modularity=task_scores.code_explanation,
            documentation=task_scores.code_explanation,
            best_practices=task_scores.formatting_linting,
            error_handling=self._calculate_error_handling_score(code, language)
        )
    
    def _calculate_efficiency_score(self, code: str, language: str) -> float:
        """Calculate efficiency score."""
        if language.lower() == 'sql':
            score = 10.0
            
            # Check for SELECT *
            if re.search(r'SELECT\s+\*', code, re.IGNORECASE):
                score -= 3.0
            
            # Check for CROSS JOIN
            if re.search(r'CROSS\s+JOIN', code, re.IGNORECASE):
                score -= 2.0
            
            # Check for LIMIT
            if re.search(r'LIMIT\s+\d+', code, re.IGNORECASE):
                score += 1.0
            
            return max(1.0, score)
        else:
            return 8.0
    
    def _calculate_error_handling_score(self, code: str, language: str) -> float:
        """Calculate error handling score."""
        if language.lower() == 'sql':
            # SQL doesn't have traditional error handling
            return 8.0
        else:
            score = 10.0
            
            # Check for try-catch blocks
            if 'try:' in code and 'except:' in code:
                score += 1.0
            
            # Check for input validation
            if re.search(r'if\s+[\w]+\s+is\s+not\s+None', code):
                score += 1.0
            
            return min(10.0, max(1.0, score))
    
    def _generate_enhanced_feedback(self, task_scores: TaskScores, code: str, language: str) -> Tuple[str, List[str]]:
        """Generate comprehensive feedback based on task scores."""
        feedback_parts = []
        suggestions = []
        
        # Formatting & Linting feedback
        if task_scores.formatting_linting < 7.0:
            feedback_parts.append("Code formatting and style issues detected.")
            suggestions.append("Use SQLFluff or follow SQL style guidelines for consistent formatting.")
        
        # Security feedback
        if task_scores.security_detection < 6.0:
            feedback_parts.append("Security vulnerabilities detected.")
            if language.lower() == 'sql':
                if re.search(r'OR[\s]+[\'"]?1[\'"]?[\s]*=[\s]*[\'"]?1[\'"]?', code, re.IGNORECASE):
                    suggestions.append("🚨 CRITICAL: SQL injection vulnerability detected. Use parameterized queries.")
                if re.search(r'(DELETE|UPDATE)\s+FROM?\s+[\w]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE) and not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                    suggestions.append("🚨 CRITICAL: DELETE/UPDATE without WHERE clause will affect ALL rows.")
        
        # Code explanation feedback
        if task_scores.code_explanation < 7.0:
            feedback_parts.append("Code could benefit from better documentation.")
        
        # SQL correctness feedback
        if task_scores.sql_correctness < 8.0:
            feedback_parts.append("SQL syntax or logic issues detected.")
        
        # Overall quality feedback
        if task_scores.overall_quality < 7.0:
            feedback_parts.append("Overall code quality needs improvement.")
        
        # Generate overall feedback
        if not feedback_parts:
            feedback = "Code demonstrates excellent quality across all evaluation criteria."
        else:
            feedback = " ".join(feedback_parts)
        
        # Add positive aspects
        positive_aspects = []
        if task_scores.security_detection >= 9.0:
            positive_aspects.append("Excellent security practices.")
        if task_scores.formatting_linting >= 9.0:
            positive_aspects.append("Well-formatted and readable code.")
        if task_scores.sql_correctness >= 9.0:
            positive_aspects.append("Correct SQL syntax and logic.")
        
        if positive_aspects:
            feedback += " " + " ".join(positive_aspects)
        
        return feedback, suggestions
    
    def _calculate_confidence(self, task_scores: TaskScores) -> float:
        """Calculate confidence based on tool availability and scores."""
        confidence = 0.7  # Base confidence
        
        # Increase confidence if external tools are available
        if self.sqlfluff_available:
            confidence += 0.1
        if self.semgrep_available:
            confidence += 0.1
        
        # Increase confidence for high scores
        if task_scores.security_detection >= 8.0:
            confidence += 0.05
        if task_scores.sql_correctness >= 8.0:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _create_error_feedback(self, error_message: str) -> ModelFeedback:
        """Create error feedback when evaluation fails."""
        return ModelFeedback(
            model_name="Enhanced Task-Specific Evaluator",
            feedback=f"Evaluation failed: {error_message}",
            suggestions=["Please try again or contact support"],
            confidence=0.0
        )
    
    async def evaluate(self, cell) -> ModelFeedback:
        """Evaluate a code cell using enhanced analysis (async interface for compatibility)."""
        try:
            # Extract code and language from the cell
            code = cell.code
            language = cell.language.value
            
            # Use the existing evaluate_code method
            return self.evaluate_code(code, language)
            
        except Exception as e:
            logger.error(f"Enhanced evaluation failed: {e}")
            return self._create_error_feedback(f"Enhanced evaluation failed: {e}") 

    def _static_sql_analysis(self, code: str) -> dict:
        """Static SQL analysis using sqlparse only."""
        try:
            # Correctness: Basic syntax check
            correctness = 10.0
            try:
                parsed = sqlparse.parse(code)
                if not parsed or not parsed[0].tokens:
                    correctness = 2.0
            except:
                correctness = 2.0
            
            # Efficiency: SELECT * or missing WHERE in DELETE/UPDATE
            efficiency = 10.0
            if 'select *' in code.lower():
                efficiency -= 3.0
            if any(cmd in code.lower() for cmd in ['delete', 'update']) and 'where' not in code.lower():
                efficiency -= 5.0
            
            # Best Practices: Naming, use of aliases, etc.
            best_practices = 10.0
            # Simple validation - check for common SQL patterns
            if 'select *' in code.lower():
                best_practices -= 2.0
            if not any(keyword in code.lower() for keyword in ['where', 'limit', 'order by']):
                best_practices -= 1.0
            
            # Readability: Formatting/indentation
            try:
                formatted = sqlparse.format(code, reindent=True, keyword_case='upper')
                readability = 10.0 if formatted.count('\n') > 1 else 6.0
            except:
                readability = 6.0
            
            # Security: Obvious injection patterns
            security = 10.0
            if 'or 1=1' in code.lower() or 'or true' in code.lower():
                security -= 8.0
            if 'drop table' in code.lower() or 'truncate' in code.lower():
                security -= 5.0
            
            return {
                'correctness': max(1.0, correctness),
                'efficiency': max(1.0, efficiency),
                'best_practices': max(1.0, best_practices),
                'readability': max(1.0, readability),
                'security': max(1.0, security)
            }
        except Exception as e:
            logger.error(f"Static SQL analysis failed: {e}")
            return {'correctness': 5.0, 'efficiency': 5.0, 'best_practices': 5.0, 'readability': 5.0, 'security': 5.0}
    def _model_based_sql_scoring(self, code: str) -> dict:
        """Model-based SQL scoring using CodeBERT."""
        try:
            # CodeBERT (existing)
            codebert_scores = self.sql_evaluator.evaluate_sql(code).scores
            
            # Return CodeBERT scores directly
            return {
                'correctness': codebert_scores.correctness,
                'efficiency': codebert_scores.scalability,
                'best_practices': codebert_scores.modularity,
                'readability': codebert_scores.readability,
                'security': codebert_scores.security
            }
        except Exception as e:
            logger.error(f"Model-based SQL scoring failed: {e}")
            return {'correctness': 5.0, 'efficiency': 5.0, 'best_practices': 5.0, 'readability': 5.0, 'security': 5.0}
    def _evaluate_with_codet5(self, code: str) -> dict:
        """Placeholder for CodeT5+ evaluation - returns rule-based scores."""
        # TODO: Implement actual CodeT5+ model evaluation
        # For now, use rule-based scoring
        score = 7.0  # Base score
        if 'select' in code.lower() and 'from' in code.lower():
            score += 1.0
        if 'where' in code.lower():
            score += 1.0
        if 'order by' in code.lower():
            score += 0.5
        return {'correctness': score, 'efficiency': score, 'best_practices': score, 'readability': score, 'security': score}
    
    def _evaluate_with_starcoder(self, code: str) -> dict:
        """Placeholder for StarCoder evaluation - returns rule-based scores."""
        # TODO: Implement actual StarCoder model evaluation
        # For now, use rule-based scoring
        score = 7.0  # Base score
        if 'join' in code.lower():
            score += 1.0
        if 'group by' in code.lower():
            score += 0.5
        if 'limit' in code.lower():
            score += 0.5
        return {'correctness': score, 'efficiency': score, 'best_practices': score, 'readability': score, 'security': score}
    
 