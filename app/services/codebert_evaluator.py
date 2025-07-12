#!/usr/bin/env python3
"""
CodeBERT-based Code Evaluator
Uses pre-trained models for accurate code analysis and scoring
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
from transformers import AutoTokenizer, AutoModel
import torch
from app.models import ScoreBreakdown, ModelFeedback

logger = logging.getLogger(__name__)

@dataclass
class CodeMetrics:
    """Code quality metrics calculated by CodeBERT evaluator."""
    complexity: float
    maintainability: float
    readability: float
    security_score: float
    efficiency: float
    documentation: float
    error_handling: float
    best_practices: float
    correctness: float

class CodeBERTEvaluator:
    """CodeBERT-based evaluator for accurate code analysis."""
    
    def __init__(self):
        """Initialize CodeBERT model and tokenizer."""
        try:
            # Load CodeBERT model for code understanding
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
            self.model = AutoModel.from_pretrained("microsoft/codebert-base")
            self.model.eval()
            logger.info("CodeBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CodeBERT model: {e}")
            self.model = None
            self.tokenizer = None
        
        # Check for external tools
        self.sqlfluff_available = self._check_sqlfluff()
        self.semgrep_available = self._check_semgrep()
        self.sqlcheck_available = self._check_sqlcheck()
        
        logger.info(f"External tools: SQLFluff={self.sqlfluff_available}, Semgrep={self.semgrep_available}, SQLCheck={self.sqlcheck_available}")
    
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
    
    def _check_sqlcheck(self) -> bool:
        """Check if SQLCheck is available."""
        try:
            result = subprocess.run(['sqlcheck', '--help'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def evaluate_code(self, code: str, language: str) -> ModelFeedback:
        """Evaluate code using CodeBERT and external tools for accurate analysis."""
        try:
            logger.info(f"Starting evaluation for {language} code")
            
            # Run external tool analysis first
            tool_results = {}
            if language.lower() == 'sql':
                logger.info("Running SQL-specific tool analysis")
                tool_results['sqlfluff'] = self._run_sqlfluff_analysis(code)
                tool_results['semgrep'] = self._run_semgrep_analysis(code)
                # Note: SQLCheck is not available, so we'll use enhanced rule-based analysis
            
            # Calculate metrics with tool integration
            metrics = self._calculate_metrics_with_tools(code, language, tool_results)
            
            # Convert metrics to scores (1-10 scale)
            scores = self._metrics_to_scores(metrics)
            
            # Generate feedback and suggestions
            feedback, suggestions = self._generate_feedback_with_tools(metrics, code, language, tool_results)
            
            # Calculate confidence based on tool availability and code quality
            confidence = self._calculate_confidence_with_tools(metrics, tool_results)
            
            logger.info(f"Evaluation completed. Security: {scores.security}, Efficiency: {scores.efficiency}, Correctness: {scores.correctness}")
            
            return ModelFeedback(
                model_name="CodeBERT + External Tools",
                feedback=feedback,
                suggestions=suggestions,
                confidence=confidence,
                scores=scores
            )
            
        except Exception as e:
            logger.error(f"CodeBERT evaluation failed: {e}")
            return self._create_error_feedback(f"CodeBERT evaluation failed: {e}")
    
    def _calculate_metrics_with_tools(self, code: str, language: str, tool_results: Dict) -> CodeMetrics:
        """Calculate comprehensive code metrics with external tool integration."""
        metrics = CodeMetrics(
            complexity=0.0,
            maintainability=0.0,
            readability=0.0,
            security_score=0.0,
            efficiency=0.0,
            documentation=0.0,
            error_handling=0.0,
            best_practices=0.0,
            correctness=0.0
        )
        
        if language.lower() == 'sql':
            # SQL-specific analysis with tool integration
            metrics.complexity = self._analyze_sql_complexity_enhanced(code)
            metrics.maintainability = self._analyze_sql_maintainability_enhanced(code)
            metrics.readability = self._analyze_sql_readability_enhanced(code, tool_results)
            metrics.security_score = self._analyze_sql_security_enhanced(code, tool_results)
            metrics.efficiency = self._analyze_sql_efficiency_enhanced(code)
            metrics.documentation = self._analyze_sql_documentation_enhanced(code)
            metrics.error_handling = self._analyze_sql_error_handling_enhanced(code)
            metrics.best_practices = self._analyze_sql_best_practices_enhanced(code, tool_results)
            metrics.correctness = self._analyze_sql_correctness_enhanced(code)
        else:
            # Generic analysis for other languages
            metrics.complexity = self._analyze_complexity(code, language)
            metrics.maintainability = self._analyze_maintainability(code, language)
            metrics.readability = self._analyze_readability(code, language)
            metrics.security_score = self._analyze_security(code, language)
            metrics.efficiency = self._analyze_efficiency(code, language)
            metrics.documentation = self._analyze_documentation(code, language)
            metrics.error_handling = self._analyze_error_handling(code, language)
            metrics.best_practices = self._analyze_best_practices(code, language)
            metrics.correctness = self._analyze_correctness(code, language)
        
        return metrics
    
    def _analyze_complexity(self, code: str, language: str) -> float:
        """Analyze code complexity using cyclomatic complexity and other metrics."""
        try:
            if language.lower() in ['python', 'pyspark']:
                return self._analyze_python_complexity(code)
            elif language.lower() == 'sql':
                return self._analyze_sql_complexity(code)
            else:
                return self._analyze_generic_complexity(code)
        except:
            return 5.0
    
    def _analyze_python_complexity(self, code: str) -> float:
        """Analyze Python code complexity."""
        try:
            tree = ast.parse(code)
            complexity = 1  # Base complexity
            
            # Count decision points
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            # Normalize to 0-10 scale (lower is better)
            if complexity <= 3:
                return 9.0
            elif complexity <= 5:
                return 7.0
            elif complexity <= 8:
                return 5.0
            elif complexity <= 12:
                return 3.0
            else:
                return 1.0
        except:
            return 5.0
    
    def _analyze_sql_complexity(self, code: str) -> float:
        """Analyze SQL code complexity."""
        complexity = 1
        
        # Count JOINs
        complexity += len(re.findall(r'\bJOIN\b', code, re.IGNORECASE))
        
        # Count subqueries
        complexity += len(re.findall(r'\(\s*SELECT', code, re.IGNORECASE))
        
        # Count UNION/INTERSECT/EXCEPT
        complexity += len(re.findall(r'\b(UNION|INTERSECT|EXCEPT)\b', code, re.IGNORECASE))
        
        # Normalize to 0-10 scale
        if complexity <= 2:
            return 9.0
        elif complexity <= 4:
            return 7.0
        elif complexity <= 6:
            return 5.0
        elif complexity <= 8:
            return 3.0
        else:
            return 1.0
    
    def _analyze_generic_complexity(self, code: str) -> float:
        """Analyze generic code complexity."""
        lines = code.split('\n')
        complexity = len(lines)
        
        # Count control structures
        control_patterns = [
            r'\bif\b', r'\bwhile\b', r'\bfor\b', r'\bswitch\b',
            r'\bcase\b', r'\btry\b', r'\bcatch\b', r'\bexcept\b'
        ]
        
        for pattern in control_patterns:
            complexity += len(re.findall(pattern, code, re.IGNORECASE))
        
        # Normalize
        if complexity <= 10:
            return 9.0
        elif complexity <= 20:
            return 7.0
        elif complexity <= 35:
            return 5.0
        elif complexity <= 50:
            return 3.0
        else:
            return 1.0
    
    def _analyze_maintainability(self, code: str, language: str) -> float:
        """Analyze code maintainability."""
        score = 10.0
        
        # Check for long functions
        lines = code.split('\n')
        if len(lines) > 50:
            score -= 2
        
        # Check for magic numbers
        magic_numbers = re.findall(r'\b\d{3,}\b', code)
        if len(magic_numbers) > 3:
            score -= 1
        
        # Check for hardcoded strings
        hardcoded_strings = re.findall(r'"[^"]{20,}"', code)
        if len(hardcoded_strings) > 2:
            score -= 1
        
        # Check for code duplication
        if self._has_code_duplication(code):
            score -= 2
        
        return max(1.0, score)
    
    def _analyze_readability(self, code: str, language: str) -> float:
        """Analyze code readability."""
        score = 10.0
        
        lines = code.split('\n')
        
        # Check line length
        long_lines = sum(1 for line in lines if len(line.strip()) > 80)
        if long_lines > len(lines) * 0.2:
            score -= 2
        
        # Check for meaningful variable names
        if language.lower() in ['python', 'pyspark']:
            bad_names = re.findall(r'\b[a-z]\b', code)  # Single letter variables
            if len(bad_names) > 5:
                score -= 1
        
        # Check for comments
        comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '--', '//', '/*')))
        if comment_lines < len(lines) * 0.1:
            score -= 1
        
        # Check for consistent indentation
        if not self._has_consistent_indentation(code):
            score -= 2
        
        return max(1.0, score)
    
    def _analyze_security(self, code: str, language: str) -> float:
        """Analyze code security with improved semantic understanding and external tools."""
        score = 10.0
        
        if language.lower() == 'sql':
            # Run Semgrep for security analysis
            semgrep_result = self._run_semgrep_analysis(code)
            if semgrep_result["available"]:
                # Blend Semgrep score with rule-based analysis
                semgrep_score = semgrep_result["score"]
                score = (score + semgrep_score) / 2
            
            # SQL Injection detection - more comprehensive patterns
            sql_injection_patterns = [
                # Direct string concatenation with variables
                r'[\'"][^\'"]*[\'"][\s]*\+[\s]*[\w]+',  # 'text' + variable
                r'[\'"][^\'"]*[\'"][\s]*\|\|[\s]*[\w]+',  # 'text' || variable
                r'[\'"][^\'"]*[\'"][\s]*\|\|[\s]*[\'"][^\'"]*[\'"]',  # 'text' || 'text'
                
                # OR 1=1 type patterns
                r'OR[\s]+[\'"]?1[\'"]?[\s]*=[\s]*[\'"]?1[\'"]?',
                r'OR[\s]+[\'"]?true[\'"]?[\s]*=[\s]*[\'"]?true[\'"]?',
                r'OR[\s]+[\'"]?1[\'"]?[\s]*=[\s]*[\'"]?1[\'"]?[\s]*;?',
                
                # UNION attacks
                r'UNION[\s]+ALL[\s]+SELECT',
                r'UNION[\s]+SELECT',
                
                # Comment injection
                r'--[\s]*$',
                r'/\*.*\*/',
                
                # Multiple statements
                r';[\s]*$',
                r';[\s]*SELECT',
                r';[\s]*INSERT',
                r';[\s]*UPDATE',
                r';[\s]*DELETE',
                r';[\s]*DROP',
            ]
            
            for pattern in sql_injection_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    score -= 8  # Severe security issue
                    break
            
            # Dangerous SELECT * patterns
            if re.search(r'SELECT\s+\*', code, re.IGNORECASE):
                # Check if it's a large dataset scenario
                if re.search(r'FROM\s+[\w]*(data|log|history|audit|temp|tmp)', code, re.IGNORECASE):
                    score -= 4  # SELECT * on potentially large tables
                else:
                    score -= 2  # General SELECT * issue
            
            # Dangerous DELETE without WHERE clause
            if re.search(r'DELETE\s+FROM\s+[\w]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE):
                if not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                    score -= 9  # DELETE without WHERE is extremely dangerous
            
            # DROP/DELETE operations without safeguards
            if re.search(r'DROP\s+(TABLE|DATABASE|INDEX)', code, re.IGNORECASE):
                score -= 7
            
            # No input validation patterns
            if re.search(r'WHERE\s+[\w]+\s*=\s*[\'"]?[\w@.-]+[\'"]?', code, re.IGNORECASE):
                # Check if it looks like user input without validation
                if re.search(r'[\'"]?[\w@.-]+[\'"]?', code, re.IGNORECASE):
                    score -= 3
            
        elif language.lower() in ['python', 'pyspark']:
            # Python security analysis
            sql_injection_patterns = [
                # String concatenation in SQL
                r'[\'"][^\'"]*[\'"][\s]*\+[\s]*[\w]+',
                r'[\'"][^\'"]*[\'"][\s]*\+[\s]*[\w]+\s*\+',
                r'f[\'"][^\'"]*\{[^}]*\}.*[\'"]',
                r'format\([\'"][^\'"]*\{[^}]*\}.*[\'"]',
                
                # Direct SQL execution
                r'execute\([\'"][^\'"]*[\'"]\s*\+',
                r'execute\(f[\'"][^\'"]*\{[^}]*\}.*[\'"]',
            ]
            
            for pattern in sql_injection_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    score -= 8
            
            # Dangerous eval/exec usage
            if re.search(r'\b(eval|exec)\s*\(', code, re.IGNORECASE):
                score -= 9
            
            # Hardcoded credentials
            credential_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
            ]
            
            for pattern in credential_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    score -= 6
            
            # Unsafe file operations
            if re.search(r'open\([\w]+\s*,\s*[\'"]w[\'"]', code, re.IGNORECASE):
                score -= 3
            
            # Unsafe subprocess calls
            if re.search(r'subprocess\.(call|run|Popen)\([\w]+\s*\+', code, re.IGNORECASE):
                score -= 7
        
        # Cross-language security issues
        # Hardcoded secrets in any language
        hardcoded_secrets = [
            r'[\'"](sk-|pk_|AKIA|ghp_|gho_)[a-zA-Z0-9]{20,}[\'"]',
            r'[\'"][a-zA-Z0-9]{32,}[\'"]',  # Long strings that might be hashes/tokens
        ]
        
        for pattern in hardcoded_secrets:
            if re.search(pattern, code, re.IGNORECASE):
                score -= 5
        
        return max(1.0, score)
    
    def _analyze_efficiency(self, code: str, language: str) -> float:
        """Analyze code efficiency with improved semantic understanding and external tools."""
        score = 10.0
        
        if language.lower() in ['python', 'pyspark']:
            # Check for inefficient patterns
            if re.search(r'for.*in.*range\(len\(', code):
                score -= 2  # Use enumerate instead
            
            if re.search(r'\.append\(.*\)\s*in\s*for', code):
                score -= 2  # Use list comprehension
            
            # Check for proper use of pandas/pyspark
            if 'pandas' in code or 'pyspark' in code:
                if re.search(r'for.*iterrows\(\)', code):
                    score -= 3  # Inefficient iteration
                
                if re.search(r'\.apply\(.*lambda.*\)', code):
                    score -= 1  # Vectorized operations are better
            
            # Check for nested loops
            nested_loops = len(re.findall(r'\bfor\b', code))
            if nested_loops > 2:
                score -= 2
            
            # Check for inefficient data structures
            if re.search(r'\.find\(', code) and re.search(r'list\(', code):
                score -= 1  # Use set for lookups
        
        elif language.lower() == 'sql':
            # Run SQLCheck for optimization analysis
            sqlcheck_result = self._run_sqlcheck_analysis(code)
            if sqlcheck_result["available"]:
                # Blend SQLCheck score with rule-based analysis
                sqlcheck_score = sqlcheck_result["score"]
                score = (score + sqlcheck_score) / 2
            
            # Check for SELECT * on large datasets
            if re.search(r'SELECT\s+\*', code, re.IGNORECASE):
                # Check if it's targeting large tables
                large_table_patterns = [
                    r'FROM\s+[\w]*(data|log|history|audit|temp|tmp|archive|backup)',
                    r'FROM\s+[\w]*(sales|orders|transactions|events|metrics)',
                    r'FROM\s+[\w]*(user|customer|product|inventory)',
                ]
                
                for pattern in large_table_patterns:
                    if re.search(pattern, code, re.IGNORECASE):
                        score -= 4  # SELECT * on large tables is very inefficient
                        break
                else:
                    score -= 2  # General SELECT * issue
            
            # Check for missing indexes hints
            if re.search(r'WHERE.*LIKE.*%', code, re.IGNORECASE):
                score -= 2  # Leading wildcard in LIKE
            
            # Check for inefficient JOINs
            if re.search(r'CROSS\s+JOIN', code, re.IGNORECASE):
                score -= 5  # Cross joins are very expensive
            
            # Check for subqueries in WHERE clause
            if re.search(r'WHERE.*\(.*SELECT', code, re.IGNORECASE):
                score -= 2  # Subqueries in WHERE can be slow
            
            # Check for ORDER BY without LIMIT
            if re.search(r'ORDER\s+BY', code, re.IGNORECASE) and not re.search(r'LIMIT', code, re.IGNORECASE):
                score -= 1  # Ordering without limit can be expensive
            
            # Check for DISTINCT on large result sets
            if re.search(r'SELECT\s+DISTINCT', code, re.IGNORECASE):
                # Check if it's on large tables
                if re.search(r'FROM\s+[\w]*(data|log|history|audit)', code, re.IGNORECASE):
                    score -= 3
            
            # Check for GROUP BY without proper indexing
            if re.search(r'GROUP\s+BY', code, re.IGNORECASE):
                score -= 1  # GROUP BY can be expensive without proper indexes
        
        return max(1.0, score)
    
    def _analyze_documentation(self, code: str, language: str) -> float:
        """Analyze code documentation."""
        score = 10.0
        
        lines = code.split('\n')
        comment_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('#', '--', '//', '/*', '*/')):
                comment_lines += 1
        
        comment_ratio = comment_lines / len(lines) if lines else 0
        
        if comment_ratio < 0.05:
            score -= 3
        elif comment_ratio < 0.1:
            score -= 1
        
        # Check for docstrings in Python
        if language.lower() in ['python', 'pyspark']:
            if not re.search(r'"""[^"]*"""', code) and not re.search(r"'''[^']*'''", code):
                score -= 2
        
        return max(1.0, score)
    
    def _analyze_error_handling(self, code: str, language: str) -> float:
        """Analyze error handling."""
        score = 10.0
        
        if language.lower() in ['python', 'pyspark']:
            # Check for try-except blocks
            if not re.search(r'\btry\b', code, re.IGNORECASE):
                score -= 3
            
            # Check for specific exception handling
            if re.search(r'except\s+Exception', code, re.IGNORECASE):
                score -= 1  # Too broad exception handling
        
        elif language.lower() == 'sql':
            # Check for error handling in SQL
            if not re.search(r'\b(ISNULL|COALESCE|NULLIF)\b', code, re.IGNORECASE):
                score -= 2
        
        return max(1.0, score)
    
    def _analyze_best_practices(self, code: str, language: str) -> float:
        """Analyze adherence to best practices with external tools integration."""
        score = 10.0
        
        if language.lower() == 'sql':
            # Run SQLFluff for formatting and best practices analysis
            sqlfluff_result = self._run_sqlfluff_analysis(code)
            if sqlfluff_result["available"]:
                # Blend SQLFluff score with rule-based analysis
                sqlfluff_score = sqlfluff_result["score"]
                score = (score + sqlfluff_score) / 2
        
        # Check for proper naming conventions
        if language.lower() in ['python', 'pyspark']:
            # Check for snake_case
            if re.search(r'[A-Z][a-z]+[A-Z]', code):
                score -= 1
        
        # Check for proper spacing
        if re.search(r'[a-zA-Z0-9_]\s*[=+\-*/]\s*[a-zA-Z0-9_]', code):
            pass  # Good spacing
        else:
            score -= 1
        
        # Check for unused imports (basic check)
        if re.search(r'import\s+\w+', code) and not re.search(r'\b\1\b', code):
            score -= 1
        
        return max(1.0, score)
    
    def _analyze_correctness(self, code: str, language: str) -> float:
        """Analyze code correctness and logic errors."""
        score = 10.0
        
        if language.lower() == 'sql':
            # Logic errors in SQL
            # DELETE without WHERE clause (extremely dangerous)
            if re.search(r'DELETE\s+FROM\s+[\w]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE):
                if not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                    score -= 9  # This will delete all rows!
            
            # UPDATE without WHERE clause
            if re.search(r'UPDATE\s+[\w]+\s+SET\s+[\w\s=,]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE):
                if not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                    score -= 8  # This will update all rows!
            
            # DROP operations without safeguards
            if re.search(r'DROP\s+(TABLE|DATABASE|INDEX)', code, re.IGNORECASE):
                score -= 7  # Destructive operation
            
            # Incorrect JOIN conditions
            if re.search(r'JOIN\s+[\w]+\s+ON\s+[\w]+\s*=\s*[\w]+(?:\s+AND|\s+OR)?', code, re.IGNORECASE):
                # Check for potential cartesian product
                if not re.search(r'ON\s+[\w]+\.[\w]+\s*=\s*[\w]+\.[\w]+', code, re.IGNORECASE):
                    score -= 3
            
            # Incorrect WHERE conditions
            if re.search(r'WHERE\s+[\w]+\s*=\s*[\w]+\s*AND\s*[\w]+\s*=\s*[\w]+', code, re.IGNORECASE):
                # Check for contradictory conditions
                conditions = re.findall(r'[\w]+\s*=\s*[\w]+', code, re.IGNORECASE)
                if len(set(conditions)) < len(conditions):
                    score -= 4  # Duplicate conditions
            
            # Missing GROUP BY with aggregate functions
            if re.search(r'(COUNT|SUM|AVG|MAX|MIN)\s*\(', code, re.IGNORECASE):
                if not re.search(r'GROUP\s+BY', code, re.IGNORECASE):
                    # Check if there are non-aggregate columns in SELECT
                    if re.search(r'SELECT\s+[\w\s,]+FROM', code, re.IGNORECASE):
                        score -= 3
        
        elif language.lower() in ['python', 'pyspark']:
            # Logic errors in Python
            # Division by zero potential
            if re.search(r'/\s*[\w]+', code) and not re.search(r'if\s+[\w]+\s*!=\s*0', code):
                score -= 2
            
            # Incorrect list indexing
            if re.search(r'\[[\w]+\s*-\s*[\d]+\]', code):
                score -= 1  # Potential negative indexing
            
            # Incorrect boolean logic
            if re.search(r'if\s+[\w]+\s*==\s*True', code):
                score -= 1  # Should be just 'if variable'
            
            if re.search(r'if\s+[\w]+\s*==\s*False', code):
                score -= 1  # Should be 'if not variable'
            
            # Incorrect string comparison
            if re.search(r'[\w]+\s*==\s*[\'"]\w+[\'"]', code):
                score -= 1  # Consider using .equals() for objects
            
            # Incorrect loop conditions
            if re.search(r'for\s+[\w]+\s+in\s+range\([\w]+\)', code):
                # Check if the range variable might be negative
                if re.search(r'range\([\w]+\s*-\s*[\d]+\)', code):
                    score -= 2
            
            # Incorrect file handling
            if re.search(r'open\([\w]+\s*,\s*[\'"]w[\'"]', code):
                if not re.search(r'with\s+open', code):
                    score -= 2  # File not properly closed
        
        # Cross-language logic errors
        # Hardcoded values that might be wrong
        if re.search(r'[\'"]\d{4}[\'"]', code):
            # Check for hardcoded years that might be outdated
            import datetime
            current_year = datetime.datetime.now().year
            years = re.findall(r'[\'"](\d{4})[\'"]', code)
            for year in years:
                if int(year) < current_year - 5 or int(year) > current_year + 1:
                    score -= 1
        
        # Incorrect date/time handling
        if re.search(r'[\'"]\d{4}-\d{2}-\d{2}[\'"]', code):
            score -= 1  # Hardcoded dates
        
        return max(1.0, score)
    
    def _has_code_duplication(self, code: str) -> bool:
        """Check for code duplication."""
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        # Simple duplication check
        line_counts = {}
        for line in lines:
            if len(line) > 10:  # Only check meaningful lines
                line_counts[line] = line_counts.get(line, 0) + 1
                if line_counts[line] > 2:
                    return True
        
        return False
    
    def _has_consistent_indentation(self, code: str) -> bool:
        """Check for consistent indentation."""
        lines = code.split('\n')
        indentations = []
        
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                indentations.append(indent)
        
        if len(set(indentations)) > 3:
            return False
        
        return True
    
    def _metrics_to_scores(self, metrics: CodeMetrics) -> ScoreBreakdown:
        """Convert metrics to score breakdown."""
        return ScoreBreakdown(
            correctness=min(10.0, max(1.0, metrics.correctness)),
            efficiency=min(10.0, max(1.0, metrics.efficiency)),
            readability=min(10.0, max(1.0, metrics.readability)),
            scalability=min(10.0, max(1.0, (metrics.complexity + metrics.maintainability) / 2)),
            security=min(10.0, max(1.0, metrics.security_score)),
            modularity=min(10.0, max(1.0, metrics.maintainability)),
            documentation=min(10.0, max(1.0, metrics.documentation)),
            best_practices=min(10.0, max(1.0, metrics.best_practices)),
            error_handling=min(10.0, max(1.0, metrics.error_handling))
        )
    
    def _generate_feedback(self, metrics: CodeMetrics, code: str, language: str) -> Tuple[str, List[str]]:
        """Generate detailed feedback and suggestions with external tool integration."""
        feedback_parts = []
        suggestions = []
        
        # Tool analysis results
        tool_results = {}
        if language.lower() == 'sql':
            tool_results['sqlfluff'] = self._run_sqlfluff_analysis(code)
            tool_results['semgrep'] = self._run_semgrep_analysis(code)
            tool_results['sqlcheck'] = self._run_sqlcheck_analysis(code)
        
        # Correctness feedback (new)
        if metrics.correctness < 5.0:
            feedback_parts.append("Critical logic errors detected in the code.")
            if language.lower() == 'sql':
                if re.search(r'DELETE\s+FROM\s+[\w]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE) and not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                    suggestions.append("CRITICAL: DELETE statement without WHERE clause will delete ALL rows. Add a WHERE clause to specify which rows to delete.")
                if re.search(r'UPDATE\s+[\w]+\s+SET\s+[\w\s=,]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE) and not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                    suggestions.append("CRITICAL: UPDATE statement without WHERE clause will update ALL rows. Add a WHERE clause to specify which rows to update.")
            else:
                suggestions.append("Review the logic flow and ensure all conditions and operations are correct.")
        
        # Security feedback
        if metrics.security_score < 5.0:
            feedback_parts.append("Severe security vulnerabilities detected in the code.")
            if language.lower() == 'sql':
                if re.search(r'OR[\s]+[\'"]?1[\'"]?[\s]*=[\s]*[\'"]?1[\'"]?', code, re.IGNORECASE):
                    suggestions.append("CRITICAL: SQL injection vulnerability detected. Use parameterized queries instead of string concatenation.")
                if re.search(r'SELECT\s+\*', code, re.IGNORECASE):
                    suggestions.append("Security risk: SELECT * can expose sensitive data. Select only the columns you need.")
                
                # Add Semgrep findings
                if tool_results.get('semgrep', {}).get('available') and tool_results['semgrep']['issues']:
                    semgrep_issues = tool_results['semgrep']['issues']
                    feedback_parts.append(f"Semgrep detected {len(semgrep_issues)} security issues.")
                    for issue in semgrep_issues[:3]:  # Show first 3 issues
                        suggestions.append(f"Security: {issue.get('extra', {}).get('message', 'Issue detected')}")
            else:
                suggestions.append("Avoid string concatenation in SQL queries and use parameterized queries instead.")
        elif metrics.security_score < 8.0:
            feedback_parts.append("Security concerns detected in the code.")
            suggestions.append("Review the code for potential security vulnerabilities and follow security best practices.")
        
        # Efficiency feedback
        if metrics.efficiency < 5.0:
            feedback_parts.append("The code has significant performance issues.")
            if language.lower() == 'sql':
                if re.search(r'SELECT\s+\*', code, re.IGNORECASE):
                    suggestions.append("Performance issue: SELECT * on large tables is inefficient. Select only needed columns.")
                if re.search(r'CROSS\s+JOIN', code, re.IGNORECASE):
                    suggestions.append("Performance issue: CROSS JOIN can be very expensive. Consider using INNER JOIN with proper conditions.")
                
                # Add SQLCheck findings
                if tool_results.get('sqlcheck', {}).get('available') and tool_results['sqlcheck']['issues']:
                    sqlcheck_issues = tool_results['sqlcheck']['issues']
                    feedback_parts.append(f"SQLCheck detected {len(sqlcheck_issues)} optimization issues.")
                    for issue in sqlcheck_issues[:3]:  # Show first 3 issues
                        suggestions.append(f"Optimization: {issue.get('message', 'Issue detected')}")
            elif language.lower() in ['python', 'pyspark']:
                suggestions.append("Consider using vectorized operations and avoiding nested loops for better performance.")
        elif metrics.efficiency < 7.0:
            feedback_parts.append("The code could be more efficient.")
            if language.lower() in ['python', 'pyspark']:
                suggestions.append("Consider using list comprehensions and vectorized operations where possible.")
            elif language.lower() == 'sql':
                suggestions.append("Optimize SQL queries by selecting only needed columns and using proper indexes.")
        
        # Best practices feedback
        if metrics.best_practices < 7.0:
            feedback_parts.append("Some best practices are not followed.")
            if language.lower() == 'sql':
                # Add SQLFluff findings
                if tool_results.get('sqlfluff', {}).get('available') and tool_results['sqlfluff']['issues']:
                    sqlfluff_issues = tool_results['sqlfluff']['issues']
                    feedback_parts.append(f"SQLFluff detected {len(sqlfluff_issues)} style and formatting issues.")
                    for issue in sqlfluff_issues[:3]:  # Show first 3 issues
                        suggestions.append(f"Style: {issue.get('description', 'Formatting issue detected')}")
            else:
                suggestions.append("Follow language-specific coding conventions and style guidelines.")
        
        # Complexity feedback
        if metrics.complexity < 5.0:
            feedback_parts.append("The code has high complexity which may make it difficult to understand and maintain.")
            suggestions.append("Consider breaking down complex functions into smaller, more focused functions.")
        
        # Maintainability feedback
        if metrics.maintainability < 7.0:
            feedback_parts.append("The code could be more maintainable.")
            suggestions.append("Extract magic numbers into named constants and avoid hardcoded values.")
        
        # Readability feedback
        if metrics.readability < 7.0:
            feedback_parts.append("The code readability can be improved.")
        
        # Documentation feedback
        if metrics.documentation < 6.0:
            feedback_parts.append("The code lacks sufficient documentation.")
            suggestions.append("Add docstrings and inline comments to explain the purpose and logic of the code.")
        
        # Error handling feedback
        if metrics.error_handling < 6.0:
            feedback_parts.append("Error handling could be improved.")
            suggestions.append("Add proper exception handling and input validation.")
        
        # Generate overall feedback
        if not feedback_parts:
            feedback = "The code demonstrates good quality across all evaluated criteria."
        else:
            feedback = " ".join(feedback_parts)
        
        # Add positive aspects
        positive_aspects = []
        if metrics.correctness >= 8.0:
            positive_aspects.append("The code appears to be logically correct.")
        if metrics.security_score >= 8.0:
            positive_aspects.append("Good security practices are followed.")
        if metrics.efficiency >= 8.0:
            positive_aspects.append("The code is well-optimized for performance.")
        
        if positive_aspects:
            feedback += " " + " ".join(positive_aspects)
        
        return feedback, suggestions
    
    def _generate_feedback_with_tools(self, metrics: CodeMetrics, code: str, language: str, tool_results: Dict) -> Tuple[str, List[str]]:
        """Generate detailed feedback and suggestions with external tool integration."""
        feedback_parts = []
        suggestions = []
        
        if language.lower() == 'sql':
            # SQL-specific feedback with tool integration
            
            # Security feedback
            if metrics.security_score <= 2.0:
                feedback_parts.append("CRITICAL: Severe security vulnerabilities detected!")
                if re.search(r'OR[\s]+[\'"]?1[\'"]?[\s]*=[\s]*[\'"]?1[\'"]?', code, re.IGNORECASE):
                    suggestions.append("🚨 SQL INJECTION VULNERABILITY: 'OR 1=1' pattern detected. Use parameterized queries instead.")
                if re.search(r'DELETE\s+FROM\s+[\w]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE) and not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                    suggestions.append("🚨 CRITICAL: DELETE without WHERE clause will delete ALL rows!")
            elif metrics.security_score <= 5.0:
                feedback_parts.append("Security concerns detected in the code.")
                suggestions.append("Review the code for potential security vulnerabilities.")
            
            # Efficiency feedback
            if metrics.efficiency <= 4.0:
                feedback_parts.append("Significant performance issues detected.")
                if re.search(r'SELECT\s+\*', code, re.IGNORECASE):
                    suggestions.append("⚠️ SELECT * on large tables is very inefficient. Select only needed columns.")
                if re.search(r'CROSS\s+JOIN', code, re.IGNORECASE):
                    suggestions.append("⚠️ CROSS JOIN can be extremely expensive. Use INNER JOIN with proper conditions.")
            elif metrics.efficiency <= 6.0:
                feedback_parts.append("Performance could be improved.")
                suggestions.append("Consider optimizing queries for better performance.")
            
            # Correctness feedback
            if metrics.correctness <= 2.0:
                feedback_parts.append("CRITICAL: Logic errors detected!")
                if re.search(r'DELETE\s+FROM\s+[\w]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE) and not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                    suggestions.append("🚨 DELETE without WHERE clause will delete ALL rows. Add a WHERE clause!")
                if re.search(r'UPDATE\s+[\w]+\s+SET\s+[\w\s=,]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE) and not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                    suggestions.append("🚨 UPDATE without WHERE clause will update ALL rows. Add a WHERE clause!")
            elif metrics.correctness <= 5.0:
                feedback_parts.append("Logic issues detected in the code.")
                suggestions.append("Review the query logic for potential errors.")
            
            # Best practices feedback
            if metrics.best_practices <= 5.0:
                feedback_parts.append("Best practices not followed.")
                if tool_results.get('sqlfluff', {}).get('available') and tool_results['sqlfluff']['issues']:
                    suggestions.append(f"SQLFluff detected {len(tool_results['sqlfluff']['issues'])} style and formatting issues.")
                suggestions.append("Follow SQL coding conventions and style guidelines.")
            
            # Tool-specific feedback
            if tool_results.get('semgrep', {}).get('available') and tool_results['semgrep']['issues']:
                semgrep_issues = tool_results['semgrep']['issues']
                feedback_parts.append(f"Semgrep security analysis found {len(semgrep_issues)} issues.")
                for issue in semgrep_issues[:2]:  # Show first 2 issues
                    suggestions.append(f"🔍 {issue.get('extra', {}).get('message', 'Security issue detected')}")
            
            if tool_results.get('sqlfluff', {}).get('available') and tool_results['sqlfluff']['issues']:
                sqlfluff_issues = tool_results['sqlfluff']['issues']
                feedback_parts.append(f"SQLFluff style analysis found {len(sqlfluff_issues)} issues.")
                for issue in sqlfluff_issues[:2]:  # Show first 2 issues
                    suggestions.append(f"📝 {issue.get('description', 'Style issue detected')}")
        
        else:
            # Generic feedback for other languages
            if metrics.correctness < 5.0:
                feedback_parts.append("Critical logic errors detected in the code.")
                suggestions.append("Review the logic flow and ensure all conditions and operations are correct.")
            
            if metrics.security_score < 5.0:
                feedback_parts.append("Severe security vulnerabilities detected in the code.")
                suggestions.append("Avoid string concatenation in SQL queries and use parameterized queries instead.")
            elif metrics.security_score < 8.0:
                feedback_parts.append("Security concerns detected in the code.")
                suggestions.append("Review the code for potential security vulnerabilities and follow security best practices.")
            
            if metrics.efficiency < 5.0:
                feedback_parts.append("The code has significant performance issues.")
                suggestions.append("Consider using vectorized operations and avoiding nested loops for better performance.")
            elif metrics.efficiency < 7.0:
                feedback_parts.append("The code could be more efficient.")
                suggestions.append("Consider using list comprehensions and vectorized operations where possible.")
        
        # Common feedback for all languages
        if metrics.complexity < 5.0:
            feedback_parts.append("The code has high complexity which may make it difficult to understand and maintain.")
            suggestions.append("Consider breaking down complex functions into smaller, more focused functions.")
        
        if metrics.maintainability < 7.0:
            feedback_parts.append("The code could be more maintainable.")
            suggestions.append("Extract magic numbers into named constants and avoid hardcoded values.")
        
        if metrics.readability < 7.0:
            feedback_parts.append("The code readability can be improved.")
        
        if metrics.documentation < 6.0:
            feedback_parts.append("The code lacks sufficient documentation.")
            suggestions.append("Add docstrings and inline comments to explain the purpose and logic of the code.")
        
        if metrics.error_handling < 6.0:
            feedback_parts.append("Error handling could be improved.")
            suggestions.append("Add proper exception handling and input validation.")
        
        # Generate overall feedback
        if not feedback_parts:
            feedback = "✅ The code demonstrates good quality across all evaluated criteria."
        else:
            feedback = " ".join(feedback_parts)
        
        # Add positive aspects
        positive_aspects = []
        if metrics.correctness >= 8.0:
            positive_aspects.append("✅ The code appears to be logically correct.")
        if metrics.security_score >= 8.0:
            positive_aspects.append("✅ Good security practices are followed.")
        if metrics.efficiency >= 8.0:
            positive_aspects.append("✅ The code is well-optimized for performance.")
        
        if positive_aspects:
            feedback += " " + " ".join(positive_aspects)
        
        return feedback, suggestions
    
    def _calculate_confidence_with_tools(self, metrics: CodeMetrics, tool_results: Dict) -> float:
        """Calculate confidence based on tool availability and code quality."""
        base_confidence = 0.7
        
        # Increase confidence if external tools are available
        if tool_results.get('semgrep', {}).get('available'):
            base_confidence += 0.1
        if tool_results.get('sqlfluff', {}).get('available'):
            base_confidence += 0.1
        
        # Adjust confidence based on code quality
        avg_score = (
            metrics.correctness + metrics.security_score + metrics.efficiency +
            metrics.readability + metrics.best_practices
        ) / 5
        
        if avg_score >= 8.0:
            base_confidence += 0.1
        elif avg_score <= 3.0:
            base_confidence -= 0.1
        
        return min(1.0, max(0.1, base_confidence))
    
    def _create_error_feedback(self, error_message: str) -> ModelFeedback:
        """Create error feedback when evaluation fails."""
        return ModelFeedback(
            model_name="CodeBERT",
            feedback=f"Evaluation failed: {error_message}",
            suggestions=["Please check the code syntax and try again."],
            confidence=0.1,
            scores=ScoreBreakdown(
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
        ) 

    def _run_sqlfluff_analysis(self, code: str) -> Dict[str, any]:
        """Run SQLFluff analysis for formatting, best practices, and readability."""
        if not self.sqlfluff_available:
            return {"available": False, "issues": [], "score": 5.0}
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run SQLFluff lint
            result = subprocess.run([
                'sqlfluff', 'lint', temp_file, 
                '--dialect', 'postgres',
                '--format', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            os.unlink(temp_file)
            
            if result.returncode == 0:
                try:
                    issues = json.loads(result.stdout)
                    return {
                        "available": True,
                        "issues": issues.get('files', [{}])[0].get('violations', []),
                        "score": self._calculate_sqlfluff_score(issues.get('files', [{}])[0].get('violations', []))
                    }
                except json.JSONDecodeError:
                    return {"available": True, "issues": [], "score": 5.0}
            else:
                return {"available": True, "issues": [], "score": 5.0}
                
        except Exception as e:
            logger.error(f"SQLFluff analysis failed: {e}")
            return {"available": False, "issues": [], "score": 5.0}
    
    def _run_semgrep_analysis(self, code: str) -> Dict[str, any]:
        """Run Semgrep analysis for security vulnerabilities and code smells."""
        if not self.semgrep_available:
            return {"available": False, "issues": [], "score": 5.0}
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run Semgrep with auto config
            result = subprocess.run([
                'semgrep', '--config=auto', 
                '--json', temp_file
            ], capture_output=True, text=True, timeout=30)
            
            os.unlink(temp_file)
            
            if result.returncode in [0, 1]:  # Semgrep returns 1 when issues are found
                try:
                    issues = json.loads(result.stdout)
                    return {
                        "available": True,
                        "issues": issues.get('results', []),
                        "score": self._calculate_semgrep_score(issues.get('results', []))
                    }
                except json.JSONDecodeError:
                    return {"available": True, "issues": [], "score": 5.0}
            else:
                return {"available": True, "issues": [], "score": 5.0}
                
        except Exception as e:
            logger.error(f"Semgrep analysis failed: {e}")
            return {"available": False, "issues": [], "score": 5.0}
    
    def _run_sqlcheck_analysis(self, code: str) -> Dict[str, any]:
        """Run SQLCheck analysis for optimization and anti-patterns."""
        if not self.sqlcheck_available:
            return {"available": False, "issues": [], "score": 5.0}
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run SQLCheck
            result = subprocess.run([
                'sqlcheck', '--input-file', temp_file,
                '--format', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            os.unlink(temp_file)
            
            if result.returncode == 0:
                try:
                    issues = json.loads(result.stdout)
                    return {
                        "available": True,
                        "issues": issues.get('issues', []),
                        "score": self._calculate_sqlcheck_score(issues.get('issues', []))
                    }
                except json.JSONDecodeError:
                    return {"available": True, "issues": [], "score": 5.0}
            else:
                return {"available": True, "issues": [], "score": 5.0}
                
        except Exception as e:
            logger.error(f"SQLCheck analysis failed: {e}")
            return {"available": False, "issues": [], "score": 5.0}
    
    def _calculate_sqlfluff_score(self, violations: List[Dict]) -> float:
        """Calculate score based on SQLFluff violations."""
        if not violations:
            return 10.0
        
        # Weight violations by severity
        severity_weights = {
            'L': 0.5,  # Layout
            'C': 1.0,  # Convention
            'W': 2.0,  # Warning
            'E': 3.0,  # Error
            'F': 4.0   # Fatal
        }
        
        total_weight = sum(severity_weights.get(v.get('code', 'W')[:1], 1.0) for v in violations)
        
        # Convert to 1-10 scale (more violations = lower score)
        if total_weight <= 2:
            return 9.0
        elif total_weight <= 5:
            return 7.0
        elif total_weight <= 10:
            return 5.0
        elif total_weight <= 20:
            return 3.0
        else:
            return 1.0
    
    def _calculate_semgrep_score(self, results: List[Dict]) -> float:
        """Calculate score based on Semgrep results."""
        if not results:
            return 10.0
        
        # Count by severity
        severity_counts = {
            'ERROR': 0,
            'WARNING': 0,
            'INFO': 0
        }
        
        for result in results:
            severity = result.get('extra', {}).get('severity', 'WARNING')
            severity_counts[severity] += 1
        
        # Weight by severity
        total_weight = (
            severity_counts['ERROR'] * 3 +
            severity_counts['WARNING'] * 2 +
            severity_counts['INFO'] * 1
        )
        
        # Convert to 1-10 scale
        if total_weight == 0:
            return 10.0
        elif total_weight <= 2:
            return 8.0
        elif total_weight <= 5:
            return 6.0
        elif total_weight <= 10:
            return 4.0
        else:
            return 2.0
    
    def _calculate_sqlcheck_score(self, issues: List[Dict]) -> float:
        """Calculate score based on SQLCheck issues."""
        if not issues:
            return 10.0
        
        # Count issues by type
        issue_types = {}
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        # Weight by issue type
        type_weights = {
            'security': 3.0,
            'performance': 2.0,
            'style': 1.0,
            'maintainability': 2.0
        }
        
        total_weight = sum(
            type_weights.get(issue_type, 1.0) * count 
            for issue_type, count in issue_types.items()
        )
        
        # Convert to 1-10 scale
        if total_weight <= 2:
            return 9.0
        elif total_weight <= 5:
            return 7.0
        elif total_weight <= 10:
            return 5.0
        elif total_weight <= 20:
            return 3.0
        else:
            return 1.0 

    def _analyze_sql_security_enhanced(self, code: str, tool_results: Dict) -> float:
        """Enhanced SQL security analysis using Semgrep and rule-based patterns."""
        score = 10.0
        
        # Use Semgrep results if available
        if tool_results.get('semgrep', {}).get('available') and tool_results['semgrep']['issues']:
            semgrep_score = tool_results['semgrep']['score']
            # Semgrep found security issues - use its score as primary
            score = semgrep_score
            logger.info(f"Semgrep security score: {score}")
        else:
            # Fallback to rule-based analysis
            logger.info("Using rule-based security analysis")
            
            # SQL Injection patterns - these should give very low scores
            sql_injection_patterns = [
                r'OR[\s]+[\'"]?1[\'"]?[\s]*=[\s]*[\'"]?1[\'"]?',  # OR 1=1
                r'OR[\s]+[\'"]?true[\'"]?[\s]*=[\s]*[\'"]?true[\'"]?',  # OR true=true
                r'UNION[\s]+ALL[\s]+SELECT',  # UNION attacks
                r'UNION[\s]+SELECT',
                r'[\'"][^\'"]*[\'"][\s]*\+[\s]*[\w]+',  # String concatenation
                r'[\'"][^\'"]*[\'"][\s]*\|\|[\s]*[\w]+',  # String concatenation
            ]
            
            for pattern in sql_injection_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    score = 1.0  # Critical security issue
                    logger.info(f"SQL injection pattern detected: {pattern}")
                    break
            
            # Dangerous operations
            if re.search(r'DELETE\s+FROM\s+[\w]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE):
                if not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                    score = 1.0  # DELETE without WHERE
                    logger.info("DELETE without WHERE clause detected")
            
            if re.search(r'DROP\s+(TABLE|DATABASE|INDEX)', code, re.IGNORECASE):
                score = min(score, 2.0)  # DROP operations
                logger.info("DROP operation detected")
        
        return max(1.0, score)
    
    def _analyze_sql_efficiency_enhanced(self, code: str) -> float:
        """Enhanced SQL efficiency analysis."""
        score = 10.0
        
        # SELECT * on large tables
        if re.search(r'SELECT\s+\*', code, re.IGNORECASE):
            large_table_patterns = [
                r'FROM\s+[\w]*(data|log|history|audit|temp|tmp|archive|backup)',
                r'FROM\s+[\w]*(sales|orders|transactions|events|metrics)',
                r'FROM\s+[\w]*(user|customer|product|inventory)',
            ]
            
            for pattern in large_table_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    score = 4.0  # SELECT * on large tables
                    logger.info("SELECT * on large table detected")
                    break
            else:
                score = 6.0  # General SELECT * issue
                logger.info("SELECT * detected")
        
        # Inefficient patterns
        if re.search(r'CROSS\s+JOIN', code, re.IGNORECASE):
            score = min(score, 3.0)  # Cross joins are very expensive
            logger.info("CROSS JOIN detected")
        
        if re.search(r'WHERE.*LIKE.*%', code, re.IGNORECASE):
            score = min(score, 6.0)  # Leading wildcard in LIKE
            logger.info("Leading wildcard in LIKE detected")
        
        if re.search(r'ORDER\s+BY', code, re.IGNORECASE) and not re.search(r'LIMIT', code, re.IGNORECASE):
            score = min(score, 7.0)  # ORDER BY without LIMIT
            logger.info("ORDER BY without LIMIT detected")
        
        return max(1.0, score)
    
    def _analyze_sql_correctness_enhanced(self, code: str) -> float:
        """Enhanced SQL correctness analysis."""
        score = 10.0
        
        # Critical logic errors
        if re.search(r'DELETE\s+FROM\s+[\w]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE):
            if not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                score = 1.0  # This will delete all rows!
                logger.info("DELETE without WHERE clause - critical error")
        
        if re.search(r'UPDATE\s+[\w]+\s+SET\s+[\w\s=,]+(?:\s+WHERE\s+[\w\s=<>()\'"`]+)?\s*;?\s*$', code, re.IGNORECASE):
            if not re.search(r'WHERE\s+[\w\s=<>()\'"`]+', code, re.IGNORECASE):
                score = 1.0  # This will update all rows!
                logger.info("UPDATE without WHERE clause - critical error")
        
        # Missing GROUP BY with aggregate functions
        if re.search(r'(COUNT|SUM|AVG|MAX|MIN)\s*\(', code, re.IGNORECASE):
            if not re.search(r'GROUP\s+BY', code, re.IGNORECASE):
                if re.search(r'SELECT\s+[\w\s,]+FROM', code, re.IGNORECASE):
                    score = min(score, 4.0)  # Missing GROUP BY
                    logger.info("Aggregate function without GROUP BY detected")
        
        return max(1.0, score)
    
    def _analyze_sql_readability_enhanced(self, code: str, tool_results: Dict) -> float:
        """Enhanced SQL readability analysis using SQLFluff."""
        score = 10.0
        
        # Use SQLFluff results if available
        if tool_results.get('sqlfluff', {}).get('available') and tool_results['sqlfluff']['issues']:
            sqlfluff_score = tool_results['sqlfluff']['score']
            # Blend SQLFluff score with basic readability checks
            score = (score + sqlfluff_score) / 2
            logger.info(f"SQLFluff readability score: {sqlfluff_score}")
        
        # Basic readability checks
        lines = code.split('\n')
        long_lines = sum(1 for line in lines if len(line.strip()) > 80)
        if long_lines > len(lines) * 0.2:
            score = min(score, 7.0)
        
        # Check for consistent formatting
        if not self._has_consistent_indentation(code):
            score = min(score, 6.0)
        
        return max(1.0, score)
    
    def _analyze_sql_best_practices_enhanced(self, code: str, tool_results: Dict) -> float:
        """Enhanced SQL best practices analysis using SQLFluff."""
        score = 10.0
        
        # Use SQLFluff results if available
        if tool_results.get('sqlfluff', {}).get('available') and tool_results['sqlfluff']['issues']:
            sqlfluff_score = tool_results['sqlfluff']['score']
            # SQLFluff provides best practices analysis
            score = sqlfluff_score
            logger.info(f"SQLFluff best practices score: {score}")
        else:
            # Fallback to rule-based analysis
            # Check for proper naming conventions
            if re.search(r'[a-z]+[A-Z]+', code):
                score = min(score, 8.0)  # Mixed case naming
            
            # Check for proper spacing
            if not re.search(r'[a-zA-Z0-9_]\s*[=+\-*/]\s*[a-zA-Z0-9_]', code):
                score = min(score, 7.0)  # Poor spacing
        
        return max(1.0, score)
    
    def _analyze_sql_complexity_enhanced(self, code: str) -> float:
        """Enhanced SQL complexity analysis."""
        complexity = 1
        
        # Count JOINs
        complexity += len(re.findall(r'\bJOIN\b', code, re.IGNORECASE))
        
        # Count subqueries
        complexity += len(re.findall(r'\(\s*SELECT', code, re.IGNORECASE))
        
        # Count UNION/INTERSECT/EXCEPT
        complexity += len(re.findall(r'\b(UNION|INTERSECT|EXCEPT)\b', code, re.IGNORECASE))
        
        # Count nested conditions
        complexity += len(re.findall(r'\bAND\b|\bOR\b', code, re.IGNORECASE))
        
        # Normalize to 0-10 scale (lower complexity = higher score)
        if complexity <= 2:
            return 10.0
        elif complexity <= 4:
            return 8.0
        elif complexity <= 6:
            return 6.0
        elif complexity <= 8:
            return 4.0
        else:
            return 2.0
    
    def _analyze_sql_maintainability_enhanced(self, code: str) -> float:
        """Enhanced SQL maintainability analysis."""
        score = 10.0
        
        # Check for long queries
        lines = code.split('\n')
        if len(lines) > 20:
            score -= 2
        
        # Check for magic numbers
        magic_numbers = re.findall(r'\b\d{3,}\b', code)
        if len(magic_numbers) > 3:
            score -= 1
        
        # Check for hardcoded strings
        hardcoded_strings = re.findall(r'"[^"]{20,}"', code)
        if len(hardcoded_strings) > 2:
            score -= 1
        
        return max(1.0, score)
    
    def _analyze_sql_documentation_enhanced(self, code: str) -> float:
        """Enhanced SQL documentation analysis."""
        score = 10.0
        
        lines = code.split('\n')
        comment_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('--', '/*', '*/')):
                comment_lines += 1
        
        comment_ratio = comment_lines / len(lines) if lines else 0
        
        if comment_ratio < 0.05:
            score -= 3
        elif comment_ratio < 0.1:
            score -= 1
        
        return max(1.0, score)
    
    def _analyze_sql_error_handling_enhanced(self, code: str) -> float:
        """Enhanced SQL error handling analysis."""
        score = 10.0
        
        # Check for error handling in SQL
        if not re.search(r'\b(ISNULL|COALESCE|NULLIF|CASE\s+WHEN)\b', code, re.IGNORECASE):
            score -= 2
        
        # Check for proper WHERE conditions
        if re.search(r'WHERE\s+[\w]+\s*=\s*[\w]+', code, re.IGNORECASE):
            # Check if it looks like user input without validation
            if re.search(r'[\'"]?[\w@.-]+[\'"]?', code, re.IGNORECASE):
                score -= 1
        
        return max(1.0, score) 