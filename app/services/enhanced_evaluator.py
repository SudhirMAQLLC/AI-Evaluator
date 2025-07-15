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
            # --- Aggregate scores with normalization ---
            scores.formatting_linting = max(1.0, min(10.0, 0.5 * static_results['readability'] + 0.5 * model_scores['readability']))
            scores.security_detection = max(1.0, min(10.0, 0.5 * static_results['security'] + 0.5 * model_scores['security']))
            scores.code_explanation = max(1.0, min(10.0, 0.5 * static_results['best_practices'] + 0.5 * model_scores['best_practices']))
            scores.sql_correctness = max(1.0, min(10.0, 0.5 * static_results['correctness'] + 0.5 * model_scores['correctness']))
            scores.overall_quality = max(1.0, min(10.0, 0.5 * static_results['efficiency'] + 0.5 * model_scores['efficiency']))
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
        
        return max(1.0, min(10.0, score))
    
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
        
        return max(1.0, min(10.0, score))
    
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
        
        return max(1.0, min(10.0, score))
    
    def _evaluate_generic_security(self, code: str, language: str) -> float:
        """Generic security evaluation for non-SQL languages."""
        score = 10.0
        
        # Check for hardcoded credentials
        if re.search(r'password\s*=\s*[\'"][^\'"]+[\'"]', code, re.IGNORECASE):
            score -= 5.0
        
        # Check for eval() usage
        if 'eval(' in code:
            score -= 8.0
        
        return max(1.0, min(10.0, score))
    
    def _evaluate_generic_explanation(self, code: str, language: str) -> float:
        """Generic code explanation evaluation."""
        score = 10.0
        
        # Check for comments
        comment_lines = len([line for line in code.split('\n') if line.strip().startswith('#')])
        total_lines = len([line for line in code.split('\n') if line.strip()])
        
        if total_lines > 0 and comment_lines / total_lines < 0.1:
            score -= 2.0
        
        return max(1.0, min(10.0, score))
    
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
        
        # Helper function to normalize scores to [1.0, 10.0] range
        def normalize_score(score: float) -> float:
            return max(1.0, min(10.0, score))
        
        # Map task scores to standard breakdown with normalization
        return ScoreBreakdown(
            correctness=normalize_score(task_scores.sql_correctness if language.lower() == 'sql' else 8.0),
            efficiency=normalize_score(self._calculate_efficiency_score(code, language)),
            readability=normalize_score(task_scores.formatting_linting),
            scalability=normalize_score(task_scores.overall_quality),
            security=normalize_score(task_scores.security_detection),
            modularity=normalize_score(task_scores.code_explanation),
            documentation=normalize_score(task_scores.code_explanation),
            best_practices=normalize_score(task_scores.formatting_linting),
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
            
            # Ensure score is within valid range [1.0, 10.0]
            return max(1.0, min(10.0, score))
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
            
            # Ensure score is within valid range [1.0, 10.0]
            return max(1.0, min(10.0, score))
    
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
        """Static SQL analysis using sqlparse only (supports multiple statements)."""
        try:
            # First, validate that this is actually meaningful SQL code
            if not self._is_valid_sql_code(code):
                return {
                    'correctness': 1.0,
                    'efficiency': 1.0,
                    'best_practices': 1.0,
                    'readability': 1.0,
                    'security': 1.0
                }
            
            # Split into individual statements for analysis
            statements = self._split_sql_statements(code)
            
            # Analyze each statement and aggregate scores
            all_scores = []
            for statement in statements:
                if self._is_valid_single_sql_statement(statement):
                    statement_scores = self._analyze_single_statement(statement)
                    all_scores.append(statement_scores)
            
            if not all_scores:
                return {
                    'correctness': 1.0,
                    'efficiency': 1.0,
                    'best_practices': 1.0,
                    'readability': 1.0,
                    'security': 1.0
                }
            
            # Aggregate scores across all statements
            aggregated_scores = {
                'correctness': sum(s['correctness'] for s in all_scores) / len(all_scores),
                'efficiency': sum(s['efficiency'] for s in all_scores) / len(all_scores),
                'best_practices': sum(s['best_practices'] for s in all_scores) / len(all_scores),
                'readability': sum(s['readability'] for s in all_scores) / len(all_scores),
                'security': sum(s['security'] for s in all_scores) / len(all_scores)
            }
            
            # Bonus for multiple well-structured statements
            if len(statements) > 1:
                bonus = min(1.0, len(statements) * 0.1)  # Up to 1 point bonus
                for key in aggregated_scores:
                    aggregated_scores[key] = min(10.0, aggregated_scores[key] + bonus)
            
            return {
                'correctness': max(1.0, min(10.0, aggregated_scores['correctness'])),
                'efficiency': max(1.0, min(10.0, aggregated_scores['efficiency'])),
                'best_practices': max(1.0, min(10.0, aggregated_scores['best_practices'])),
                'readability': max(1.0, min(10.0, aggregated_scores['readability'])),
                'security': max(1.0, min(10.0, aggregated_scores['security']))
            }
        except Exception as e:
            logger.error(f"Static SQL analysis failed: {e}")
            return {'correctness': 5.0, 'efficiency': 5.0, 'best_practices': 5.0, 'readability': 5.0, 'security': 5.0}
    
    def _analyze_single_statement(self, statement: str) -> dict:
        """Enhanced analysis of a single SQL statement with comprehensive checks."""
        # Correctness: Advanced syntax and semantic checks
        correctness = self._analyze_correctness(statement)
        
        # Efficiency: Performance and optimization analysis
        efficiency = self._analyze_efficiency(statement)
        
        # Best Practices: Coding standards and conventions
        best_practices = self._analyze_best_practices(statement)
        
        # Readability: Code formatting and structure
        readability = self._analyze_readability(statement)
        
        # Security: Comprehensive security vulnerability analysis
        security = self._analyze_security(statement)
        
        return {
            'correctness': max(1.0, min(10.0, correctness)),
            'efficiency': max(1.0, min(10.0, efficiency)),
            'best_practices': max(1.0, min(10.0, best_practices)),
            'readability': max(1.0, min(10.0, readability)),
            'security': max(1.0, min(10.0, security))
        }
    
    def _analyze_correctness(self, statement: str) -> float:
        """Comprehensive correctness analysis."""
        score = 10.0
        statement_lower = statement.lower()
        
        # Basic syntax validation
        try:
            parsed = sqlparse.parse(statement)
            if not parsed or not parsed[0].tokens:
                score -= 8.0
        except:
            score -= 8.0
        
        # Case sensitivity and keyword validation
        if not self._check_case_sensitivity(statement):
            score -= 2.0
        
        # SQL command structure validation
        if not self._validate_sql_structure(statement):
            score -= 3.0
        
        # Data type and constraint validation
        if not self._validate_data_types(statement):
            score -= 1.0
        
        # Function and operator validation
        if not self._validate_functions_operators(statement):
            score -= 1.0
        
        return score
    
    def _analyze_efficiency(self, statement: str) -> float:
        """Comprehensive efficiency analysis."""
        score = 10.0
        statement_lower = statement.lower()
        
        # SELECT * analysis
        if 'select *' in statement_lower:
            score -= 3.0
        
        # Missing WHERE clause in DELETE/UPDATE
        if any(cmd in statement_lower for cmd in ['delete', 'update']) and 'where' not in statement_lower:
            score -= 5.0
        
        # Index usage analysis
        if not self._check_index_usage(statement):
            score -= 1.0
        
        # Subquery optimization
        if self._has_inefficient_subqueries(statement):
            score -= 2.0
        
        # JOIN optimization
        if self._has_inefficient_joins(statement):
            score -= 1.0
        
        # DISTINCT usage
        if 'distinct' in statement_lower and self._has_inefficient_distinct(statement):
            score -= 1.0
        
        # LIMIT usage
        if 'limit' in statement_lower:
            score += 0.5
        
        # EXISTS vs IN optimization
        if self._has_inefficient_in_clause(statement):
            score -= 1.0
        
        return score
    
    def _analyze_best_practices(self, statement: str) -> float:
        """Comprehensive best practices analysis."""
        score = 10.0
        statement_lower = statement.lower()
        
        # Naming conventions
        if not self._check_naming_conventions(statement):
            score -= 1.0
        
        # Alias usage
        if self._has_complex_joins(statement) and not self._has_proper_aliases(statement):
            score -= 1.0
        
        # Comment usage
        if self._is_complex_query(statement) and not self._has_comments(statement):
            score -= 0.5
        
        # Consistent formatting
        if not self._check_consistent_formatting(statement):
            score -= 1.0
        
        # Error handling
        if not self._has_error_handling(statement):
            score -= 0.5
        
        # Transaction management
        if self._needs_transaction(statement) and not self._has_transaction_management(statement):
            score -= 1.0
        
        return score
    
    def _analyze_readability(self, statement: str) -> float:
        """Comprehensive readability analysis."""
        score = 10.0
        
        # Formatting analysis
        try:
            formatted = sqlparse.format(statement, reindent=True, keyword_case='upper')
            if formatted.count('\n') > 1:
                score += 1.0
            else:
                score -= 1.0
        except:
            score -= 2.0
        
        # Line length analysis
        if self._has_long_lines(statement):
            score -= 1.0
        
        # Spacing analysis
        if not self._has_proper_spacing(statement):
            score -= 1.0
        
        # Keyword highlighting
        if not self._has_consistent_keyword_case(statement):
            score -= 0.5
        
        # Logical grouping
        if not self._has_logical_grouping(statement):
            score -= 0.5
        
        return score
    
    def _analyze_security(self, statement: str) -> float:
        """Comprehensive security analysis."""
        score = 10.0
        statement_lower = statement.lower()
        
        # SQL Injection patterns
        injection_patterns = [
            'or 1=1', 'or true', 'or 1', 'or 0=0',
            'union select', 'union all select',
            'drop table', 'truncate table', 'delete from',
            'exec ', 'execute ', 'xp_', 'sp_',
            'insert into', 'update set',
            'create table', 'alter table',
            'grant ', 'revoke ',
            'backup database', 'restore database'
        ]
        
        for pattern in injection_patterns:
            if pattern in statement_lower:
                score -= 8.0
                break
        
        # String concatenation vulnerabilities
        if self._has_string_concatenation(statement):
            score -= 3.0
        
        # Dynamic SQL vulnerabilities
        if self._has_dynamic_sql(statement):
            score -= 5.0
        
        # Privilege escalation patterns
        if self._has_privilege_escalation(statement):
            score -= 6.0
        
        # Data exposure patterns
        if self._has_data_exposure(statement):
            score -= 2.0
        
        # Input validation
        if not self._has_input_validation(statement):
            score -= 1.0
        
        return score
    
    # Helper methods for comprehensive analysis
    
    def _check_case_sensitivity(self, statement: str) -> bool:
        """Check for proper case sensitivity in SQL keywords."""
        # Check if keywords are consistently cased
        keywords = ['select', 'from', 'where', 'and', 'or', 'order', 'group', 'by', 'having', 'limit']
        statement_lower = statement.lower()
        
        for keyword in keywords:
            if keyword in statement_lower:
                # Check if the keyword appears in mixed case
                if keyword.upper() in statement and keyword.lower() in statement:
                    return False
        return True
    
    def _validate_sql_structure(self, statement: str) -> bool:
        """Validate SQL command structure."""
        statement_lower = statement.lower()
        
        # SELECT must have FROM
        if 'select' in statement_lower and 'from' not in statement_lower:
            return False
        
        # INSERT must have INTO
        if 'insert' in statement_lower and 'into' not in statement_lower:
            return False
        
        # UPDATE must have SET
        if 'update' in statement_lower and 'set' not in statement_lower:
            return False
        
        # DELETE should have FROM or WHERE
        if 'delete' in statement_lower and 'from' not in statement_lower and 'where' not in statement_lower:
            return False
        
        return True
    
    def _validate_data_types(self, statement: str) -> bool:
        """Validate data types and constraints."""
        # Basic data type validation
        data_types = ['int', 'varchar', 'text', 'date', 'datetime', 'decimal', 'float']
        statement_lower = statement.lower()
        
        # Check for invalid data type usage
        if 'varchar' in statement_lower and not re.search(r'varchar\(\d+\)', statement_lower):
            return False
        
        return True
    
    def _validate_functions_operators(self, statement: str) -> bool:
        """Validate functions and operators."""
        # Check for balanced parentheses
        if statement.count('(') != statement.count(')'):
            return False
        
        # Check for valid operators
        operators = ['=', '<>', '!=', '<', '>', '<=', '>=', 'like', 'in', 'between']
        statement_lower = statement.lower()
        
        # Basic operator validation
        if re.search(r'[=<>!]\s*[=<>!]', statement):
            return False
        
        return True
    
    def _check_index_usage(self, statement: str) -> bool:
        """Check if query would benefit from indexes."""
        statement_lower = statement.lower()
        
        # Check for WHERE clauses that could use indexes
        if 'where' in statement_lower:
            # Look for column comparisons that could use indexes
            if re.search(r'where\s+\w+\s*[=<>!]', statement_lower):
                return True
        
        return True
    
    def _has_inefficient_subqueries(self, statement: str) -> bool:
        """Check for inefficient subqueries."""
        statement_lower = statement.lower()
        
        # Check for correlated subqueries
        if re.search(r'where\s+exists\s*\(', statement_lower):
            return True
        
        # Check for subqueries in SELECT clause
        if re.search(r'select\s+\(.*select', statement_lower, re.DOTALL):
            return True
        
        return False
    
    def _has_inefficient_joins(self, statement: str) -> bool:
        """Check for inefficient JOIN patterns."""
        statement_lower = statement.lower()
        
        # Check for cartesian products
        if 'from' in statement_lower and 'join' not in statement_lower:
            # Multiple tables without JOIN
            tables = re.findall(r'from\s+(\w+)\s*,', statement_lower)
            if len(tables) > 1:
                return True
        
        return False
    
    def _has_inefficient_distinct(self, statement: str) -> bool:
        """Check for inefficient DISTINCT usage."""
        statement_lower = statement.lower()
        
        # DISTINCT on all columns is often inefficient
        if 'distinct *' in statement_lower:
            return True
        
        return False
    
    def _has_inefficient_in_clause(self, statement: str) -> bool:
        """Check for inefficient IN clauses."""
        statement_lower = statement.lower()
        
        # Large IN clauses can be inefficient
        if 'in (' in statement_lower:
            # Count items in IN clause
            in_match = re.search(r'in\s*\(([^)]+)\)', statement_lower)
            if in_match:
                items = in_match.group(1).split(',')
                if len(items) > 10:  # More than 10 items
                    return True
        
        return False
    
    def _check_naming_conventions(self, statement: str) -> bool:
        """Check naming conventions."""
        # Check for consistent naming
        statement_lower = statement.lower()
        
        # Check for snake_case or camelCase consistency
        if re.search(r'[a-z]+_[a-z]+', statement_lower) and re.search(r'[a-z]+[A-Z][a-z]+', statement_lower):
            return False
        
        return True
    
    def _has_complex_joins(self, statement: str) -> bool:
        """Check if query has complex joins."""
        statement_lower = statement.lower()
        return statement_lower.count('join') > 2
    
    def _has_proper_aliases(self, statement: str) -> bool:
        """Check for proper table aliases."""
        statement_lower = statement.lower()
        
        # Check if complex joins have aliases
        if self._has_complex_joins(statement):
            if re.search(r'from\s+\w+\s+as\s+\w+', statement_lower):
                return True
            return False
        
        return True
    
    def _is_complex_query(self, statement: str) -> bool:
        """Check if query is complex."""
        return len(statement.split()) > 20
    
    def _has_comments(self, statement: str) -> bool:
        """Check for comments in complex queries."""
        return '--' in statement or '/*' in statement
    
    def _check_consistent_formatting(self, statement: str) -> bool:
        """Check for consistent formatting."""
        # Check for consistent spacing around operators
        if not re.search(r'\s+[=<>!]+\s+', statement):
            return False
        
        return True
    
    def _has_error_handling(self, statement: str) -> bool:
        """Check for error handling patterns."""
        statement_lower = statement.lower()
        
        # Check for transaction patterns
        if 'begin transaction' in statement_lower or 'rollback' in statement_lower:
            return True
        
        return False
    
    def _needs_transaction(self, statement: str) -> bool:
        """Check if statement needs transaction management."""
        statement_lower = statement.lower()
        
        # Multiple DML operations need transactions
        dml_operations = ['insert', 'update', 'delete']
        operation_count = sum(1 for op in dml_operations if op in statement_lower)
        
        return operation_count > 1
    
    def _has_transaction_management(self, statement: str) -> bool:
        """Check for transaction management."""
        statement_lower = statement.lower()
        
        return 'begin' in statement_lower or 'commit' in statement_lower or 'rollback' in statement_lower
    
    def _has_long_lines(self, statement: str) -> bool:
        """Check for long lines."""
        lines = statement.split('\n')
        return any(len(line) > 80 for line in lines)
    
    def _has_proper_spacing(self, statement: str) -> bool:
        """Check for proper spacing."""
        # Check for proper spacing around keywords
        if not re.search(r'\s+(select|from|where|and|or)\s+', statement, re.IGNORECASE):
            return False
        
        return True
    
    def _has_consistent_keyword_case(self, statement: str) -> bool:
        """Check for consistent keyword case."""
        keywords = ['select', 'from', 'where', 'and', 'or']
        statement_lower = statement.lower()
        
        for keyword in keywords:
            if keyword in statement_lower:
                # Check if keyword appears in different cases
                if keyword.upper() in statement and keyword.lower() in statement:
                    return False
        
        return True
    
    def _has_logical_grouping(self, statement: str) -> bool:
        """Check for logical grouping."""
        # Check for proper indentation and grouping
        lines = statement.split('\n')
        if len(lines) > 1:
            # Check if there's some indentation
            indented_lines = sum(1 for line in lines if line.strip() and line.startswith('    '))
            return indented_lines > 0
        
        return True
    
    def _has_string_concatenation(self, statement: str) -> bool:
        """Check for string concatenation vulnerabilities."""
        # Check for + operator with strings
        if re.search(r'[\'"]\s*\+\s*[\w]+\s*\+\s*[\'"]', statement):
            return True
        
        return False
    
    def _has_dynamic_sql(self, statement: str) -> bool:
        """Check for dynamic SQL vulnerabilities."""
        statement_lower = statement.lower()
        
        # Check for EXEC or EXECUTE
        if 'exec ' in statement_lower or 'execute ' in statement_lower:
            return True
        
        return False
    
    def _has_privilege_escalation(self, statement: str) -> bool:
        """Check for privilege escalation patterns."""
        statement_lower = statement.lower()
        
        # Check for GRANT or REVOKE
        if 'grant ' in statement_lower or 'revoke ' in statement_lower:
            return True
        
        return False
    
    def _has_data_exposure(self, statement: str) -> bool:
        """Check for data exposure patterns."""
        statement_lower = statement.lower()
        
        # Check for SELECT * without WHERE
        if 'select *' in statement_lower and 'where' not in statement_lower:
            return True
        
        return False
    
    def _has_input_validation(self, statement: str) -> bool:
        """Check for input validation patterns."""
        # Check for parameterized queries or validation
        if re.search(r'@\w+', statement):
            return True
        
        return False
    
    def _model_based_sql_scoring(self, code: str) -> dict:
        """Fast rule-based SQL scoring (no heavy models) - supports multiple statements."""
        try:
            # First, validate that this is actually meaningful SQL code
            if not self._is_valid_sql_code(code):
                return {
                    'correctness': 1.0,
                    'efficiency': 1.0,
                    'best_practices': 1.0,
                    'readability': 1.0,
                    'security': 1.0
                }
            
            # Split into individual statements for analysis
            statements = self._split_sql_statements(code)
            
            # Analyze each statement and aggregate scores
            all_scores = []
            for statement in statements:
                if self._is_valid_single_sql_statement(statement):
                    statement_scores = self._score_single_statement(statement)
                    all_scores.append(statement_scores)
            
            if not all_scores:
                return {
                    'correctness': 1.0,
                    'efficiency': 1.0,
                    'best_practices': 1.0,
                    'readability': 1.0,
                    'security': 1.0
                }
            
            # Aggregate scores across all statements
            aggregated_scores = {
                'correctness': sum(s['correctness'] for s in all_scores) / len(all_scores),
                'efficiency': sum(s['efficiency'] for s in all_scores) / len(all_scores),
                'best_practices': sum(s['best_practices'] for s in all_scores) / len(all_scores),
                'readability': sum(s['readability'] for s in all_scores) / len(all_scores),
                'security': sum(s['security'] for s in all_scores) / len(all_scores)
            }
            
            # Bonus for multiple well-structured statements
            if len(statements) > 1:
                bonus = min(1.0, len(statements) * 0.1)  # Up to 1 point bonus
                for key in aggregated_scores:
                    aggregated_scores[key] = min(10.0, aggregated_scores[key] + bonus)
            
            return {
                'correctness': max(1.0, min(10.0, aggregated_scores['correctness'])),
                'efficiency': max(1.0, min(10.0, aggregated_scores['efficiency'])),
                'best_practices': max(1.0, min(10.0, aggregated_scores['best_practices'])),
                'readability': max(1.0, min(10.0, aggregated_scores['readability'])),
                'security': max(1.0, min(10.0, aggregated_scores['security']))
            }
        except Exception as e:
            logger.error(f"Rule-based SQL scoring failed: {e}")
            return {'correctness': 5.0, 'efficiency': 5.0, 'best_practices': 5.0, 'readability': 5.0, 'security': 5.0}
    
    def _score_single_statement(self, statement: str) -> dict:
        """Score a single SQL statement using rule-based approach."""
        # Use only rule-based scoring for speed
        score = 7.0  # Base score
        
        # Correctness checks
        if 'select' in statement.lower() and 'from' in statement.lower():
            score += 1.0
        if 'where' in statement.lower():
            score += 0.5
        if 'order by' in statement.lower():
            score += 0.5
        
        # Efficiency checks
        if 'select *' in statement.lower():
            score -= 2.0
        if 'limit' in statement.lower():
            score += 0.5
        
        # Best practices
        if 'join' in statement.lower():
            score += 0.5
        if 'group by' in statement.lower():
            score += 0.5
        
        # Security checks
        if 'or 1=1' in statement.lower() or 'or true' in statement.lower():
            score -= 5.0
        if 'drop table' in statement.lower() or 'truncate' in statement.lower():
            score -= 3.0
        
        # Readability
        if statement.count('\n') > 2:
            score += 0.5
        
        return {
            'correctness': max(1.0, min(10.0, score)),
            'efficiency': max(1.0, min(10.0, score)),
            'best_practices': max(1.0, min(10.0, score)),
            'readability': max(1.0, min(10.0, score)),
            'security': max(1.0, min(10.0, score))
        }
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
    
    def _is_valid_sql_code(self, code: str) -> bool:
        """Validate that the input is actually meaningful SQL code (supports multiple statements)."""
        if not code or not code.strip():
            return False
        
        code = code.strip()
        
        # Split into individual SQL statements
        statements = self._split_sql_statements(code)
        
        if not statements:
            return False
        
        # Check each statement for validity
        valid_statements = 0
        for statement in statements:
            if self._is_valid_single_sql_statement(statement):
                valid_statements += 1
        
        # At least 50% of statements must be valid
        return valid_statements / len(statements) >= 0.5
    
    def _split_sql_statements(self, code: str) -> List[str]:
        """Split SQL code into individual statements."""
        # Split by semicolon, but be careful with semicolons in strings
        statements = []
        current_statement = ""
        in_string = False
        string_char = None
        
        for char in code:
            if char in ['"', "'"]:
                if not in_string:
                    in_string = True
                    string_char = char
                elif string_char == char:
                    in_string = False
                    string_char = None
            
            if char == ';' and not in_string:
                if current_statement.strip():
                    statements.append(current_statement.strip())
                current_statement = ""
            else:
                current_statement += char
        
        # Add the last statement if it exists
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return statements
    
    def _is_valid_single_sql_statement(self, statement: str) -> bool:
        """Validate a single SQL statement."""
        if not statement or not statement.strip():
            return False
        
        code = statement.strip().lower()
        
        # Check for nonsensical input (random characters, no SQL keywords)
        sql_keywords = [
            'select', 'from', 'where', 'insert', 'update', 'delete', 'create', 'drop', 
            'alter', 'table', 'index', 'view', 'procedure', 'function', 'trigger',
            'join', 'left', 'right', 'inner', 'outer', 'on', 'group', 'by', 'order',
            'having', 'limit', 'offset', 'union', 'all', 'distinct', 'as', 'in',
            'between', 'like', 'is', 'null', 'not', 'and', 'or', 'count', 'sum',
            'avg', 'min', 'max', 'case', 'when', 'then', 'else', 'end'
        ]
        
        # Count how many SQL keywords are present
        keyword_count = sum(1 for keyword in sql_keywords if keyword in code)
        
        # If no SQL keywords found, it's not valid SQL
        if keyword_count == 0:
            return False
        
        # Check for minimum meaningful SQL structure
        # Must have at least a basic SELECT, INSERT, UPDATE, DELETE, or CREATE statement
        basic_commands = ['select', 'insert', 'update', 'delete', 'create', 'drop', 'alter']
        has_basic_command = any(cmd in code for cmd in basic_commands)
        
        if not has_basic_command:
            return False
        
        # Check for random character patterns (like your example "sjbjdbs hbsjdabhbs jhas")
        # If the code has too many random character sequences, it's likely not valid
        words = code.split()
        random_word_count = 0
        
        for word in words:
            # Skip if it's a known SQL keyword
            if word in sql_keywords or word in basic_commands:
                continue
            
            # Check if word looks like random characters (no vowels, too many consonants)
            if len(word) > 3:
                vowels = sum(1 for char in word if char in 'aeiou')
                if vowels == 0 or vowels / len(word) < 0.2:  # Less than 20% vowels
                    random_word_count += 1
        
        # If more than 50% of words look random, reject it
        if len(words) > 0 and random_word_count / len(words) > 0.5:
            return False
        
        # Check for minimum length and structure
        if len(code) < 10:  # Too short to be meaningful SQL
            return False
        
        # Additional check: Must have proper SQL structure
        # For SELECT statements, must have FROM
        if 'select' in code and 'from' not in code:
            return False
        
        # For INSERT statements, must have INTO
        if 'insert' in code and 'into' not in code:
            return False
        
        # For UPDATE statements, must have SET
        if 'update' in code and 'set' not in code:
            return False
        
        # For DELETE statements, should have FROM or WHERE
        if 'delete' in code and 'from' not in code and 'where' not in code:
            return False
        
        return True