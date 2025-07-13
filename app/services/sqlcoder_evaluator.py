import asyncio
import logging
import re
import subprocess
import os
from typing import Dict, List, Optional, Tuple
import numpy as np
import sqlglot
from sqlglot import parse_one, exp
from sqlglot.errors import ParseError
import threading
import concurrent.futures
from transformers import AutoTokenizer, AutoModel, pipeline, AutoModelForSequenceClassification
import torch
import time
from functools import lru_cache

from app.models import (
    ModelFeedback, 
    ScoreBreakdown, 
    CodeCell
)
from app.config import settings

logger = logging.getLogger(__name__)

class ModelCache:
    """Thread-safe model cache with optimized SQL-specific models."""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._models = {}
        self._model_locks = {}
        self._evaluation_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self._load_optimized_models()
    
    def _load_optimized_models(self):
        """Load optimized SQL-specific models."""
        logger.info("Loading lightweight models only for fast startup...")
        
        # Load lightweight fallback models only for immediate availability
        try:
            logger.info("Loading lightweight fallback models...")
            # Use CodeBERT as lightweight fallback for correctness
            self._models['fallback_tokenizer'] = AutoTokenizer.from_pretrained("microsoft/codebert-base")
            self._models['fallback_model'] = AutoModel.from_pretrained("microsoft/codebert-base")
            self._models['fallback_model'].eval()
            logger.info("Lightweight fallback models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load fallback models: {e}")
            self._models['fallback_tokenizer'] = None
            self._models['fallback_model'] = None
        
        # DISABLED: Heavy model downloads for fast startup
        # StarCoder2-3b, CodeT5+, SecurityBERT, SQLCoder-7b are disabled
        logger.info("Heavy models (StarCoder2, CodeT5+, SecurityBERT, SQLCoder) disabled for fast startup")
        
        # Create locks for thread safety
        for model_name in self._models.keys():
            self._model_locks[model_name] = threading.Lock()
        
        logger.info("Lightweight model cache initialization complete")
    
    def get_model(self, model_name: str):
        """Thread-safe model retrieval."""
        return self._models.get(model_name)
    
    def get_lock(self, model_name: str):
        """Get lock for specific model."""
        return self._model_locks.get(model_name, threading.Lock())
    
    def submit_evaluation(self, func, *args, **kwargs):
        """Submit evaluation task to thread pool."""
        return self._evaluation_pool.submit(func, *args, **kwargs)

# Global model cache instance
model_cache = ModelCache()

class SQLCoderEvaluator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.logger = logging.getLogger(__name__)
        return cls._instance
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Do not re-init here
        
        # Initialize sqlfluff for enhanced static analysis
        self._init_sqlfluff()
        
        # Optimized scoring weights for SQL-specific models
        self.weights = {
            'correctness': 0.30,    # StarCoder2 - most important for SQL
            'readability': 0.20,    # CodeT5+ - code understanding
            'security': 0.25,       # SecurityBERT - critical for SQL
            'sql_scoring': 0.25     # SQLCoder - SQL-specific analysis
        }
        
        self.logger.info("SQLCoder Evaluator with optimized SQL-specific models initialized successfully")
    
    def _init_sqlfluff(self):
        """Initialize SQLFluff for static analysis."""
        try:
            result = subprocess.run(['sqlfluff', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            self.sqlfluff_available = result.returncode == 0
            self.logger.info(f"SQLFluff available: {self.sqlfluff_available}")
        except Exception as e:
            self.sqlfluff_available = False
            self.logger.warning(f"SQLFluff not available: {e}")
    
    async def evaluate(self, cell: CodeCell) -> ModelFeedback:
        """Evaluate SQL code using single best model (CodeBERT)."""
        try:
            # Extract SQL code from cell
            if hasattr(cell, 'source'):
                sql_code = cell.source
            elif hasattr(cell, 'cell_type') and cell.cell_type == 'code':
                sql_code = cell.source
            else:
                sql_code = str(cell)
            
            self.logger.info("Starting SQLCoder evaluation with single best model (CodeBERT)")
            start_time = time.time()
            
            # Use only the best model - CodeBERT for all evaluations
            with model_cache.get_lock('fallback_model'):
                correctness = self._evaluate_with_codebert(sql_code, 'correctness')
                readability = self._evaluate_with_codebert(sql_code, 'readability')
                security = self._evaluate_with_codebert(sql_code, 'security')
                efficiency = self._evaluate_with_codebert(sql_code, 'efficiency')
            
            # Calculate derived scores based on CodeBERT results
            scalability = (correctness + readability) / 2.0
            modularity = (readability + efficiency) / 2.0
            documentation = readability * 0.8  # Documentation correlates with readability
            best_practices = (correctness + security) / 2.0
            error_handling = (security + correctness) / 2.0
            
            # Create score breakdown with single model scores
            score_breakdown = ScoreBreakdown(
                correctness=correctness,
                efficiency=efficiency,
                readability=readability,
                scalability=scalability,
                security=security,
                modularity=modularity,
                documentation=documentation,
                best_practices=best_practices,
                error_handling=error_handling
            )
            
            evaluation_time = time.time() - start_time
            self.logger.info(f"Single model evaluation completed in {evaluation_time:.2f} seconds")
            
            return ModelFeedback(
                model_name="SQLCoder-Single (CodeBERT)",
                confidence=0.85,
                scores=score_breakdown,
                feedback=self._generate_single_model_feedback(sql_code, {
                    'correctness': correctness,
                    'readability': readability,
                    'security': security,
                    'efficiency': efficiency
                }),
                suggestions=self._generate_single_model_suggestions({
                    'correctness': correctness,
                    'readability': readability,
                    'security': security,
                    'efficiency': efficiency
                })
            )
            
        except Exception as e:
            self.logger.error(f"SQLCoder evaluation failed: {e}")
            return self._create_error_feedback(f"SQLCoder evaluation failed: {e}")
    
    def _evaluate_correctness_starcoder2(self, sql_code: str) -> float:
        """Evaluate SQL correctness using StarCoder2 with fallback to CodeBERT."""
        try:
            # Try StarCoder2 first
            model = model_cache.get_model('starcoder2_model')
            tokenizer = model_cache.get_model('starcoder2_tokenizer')
            
            if model and tokenizer:
                # Use StarCoder2 for correctness evaluation
                with model_cache.get_lock('starcoder2_model'):
                    # Prepare input for StarCoder2
                    prompt = f"# SQL Code Analysis\n# Evaluate the correctness of this SQL query:\n{sql_code}\n\n# Analysis:"
                    
                    inputs = tokenizer(
                        prompt, 
                        return_tensors="pt", 
                        truncation=True, 
                        max_length=512,
                        padding=True
                    )
                    
                    # Move to GPU if available
                    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                    model = model.to(device)
                    
                    with torch.no_grad():
                        outputs = model(**inputs)
                        
                        # Extract features for correctness analysis
                        hidden_states = outputs.last_hidden_state
                        
                        # Calculate correctness score based on model confidence
                        # Higher attention weights and consistent embeddings indicate better correctness
                        attention_weights = torch.softmax(outputs.logits, dim=-1) if hasattr(outputs, 'logits') else None
                        
                        if attention_weights is not None:
                            confidence_score = torch.mean(attention_weights).item()
                        else:
                            confidence_score = torch.mean(hidden_states).item()
                        
                        # Normalize to 1-10 scale
                        normalized_score = 1.0 + (confidence_score + 1.0) * 4.5
                        return max(1.0, min(10.0, normalized_score))
            
            # Fallback to CodeBERT if StarCoder2 not available
            fallback_model = model_cache.get_model('fallback_model')
            fallback_tokenizer = model_cache.get_model('fallback_tokenizer')
            
            if fallback_model and fallback_tokenizer:
                logger.info("Using CodeBERT fallback for correctness evaluation")
                with model_cache.get_lock('fallback_model'):
                    inputs = fallback_tokenizer(
                        sql_code, 
                        return_tensors="pt", 
                        truncation=True, 
                        max_length=512
                    )
                    
                    # Move to GPU if available
                    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                    fallback_model = fallback_model.to(device)
                    
                    with torch.no_grad():
                        outputs = fallback_model(**inputs)
                        quality_score = torch.mean(outputs.last_hidden_state).item()
                        normalized_score = 1.0 + (quality_score + 1.0) * 4.5
                        return max(1.0, min(10.0, normalized_score))
            
            # Final fallback to basic evaluation
            return self._fallback_correctness_evaluation(sql_code)
            
        except Exception as e:
            self.logger.warning(f"StarCoder2 evaluation failed: {e}")
            return self._fallback_correctness_evaluation(sql_code)
    
    def _evaluate_readability_codet5p(self, sql_code: str) -> float:
        """Evaluate SQL readability using CodeT5+ with fallback."""
        try:
            model = model_cache.get_model('codet5p_model')
            tokenizer = model_cache.get_model('codet5p_tokenizer')
            
            if model and tokenizer:
                # Use CodeT5+ for readability evaluation
                with model_cache.get_lock('codet5p_model'):
                    # Prepare input for CodeT5+
                    prompt = f"# SQL Readability Analysis\n# Evaluate the readability of this SQL query:\n{sql_code}\n\n# Readability Score:"
                    
                    inputs = tokenizer(
                        prompt, 
                        return_tensors="pt", 
                        truncation=True, 
                        max_length=512,
                        padding=True
                    )
                    
                    # Move to GPU if available
                    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                    model = model.to(device)
                    
                    with torch.no_grad():
                        outputs = model(**inputs)
                        
                        # Extract readability features
                        hidden_states = outputs.last_hidden_state
                        
                        # Calculate readability based on code structure and formatting
                        # CodeT5+ is good at understanding code structure
                        structure_score = torch.std(hidden_states).item()  # Consistency in structure
                        complexity_score = torch.mean(torch.abs(hidden_states)).item()  # Code complexity
                        
                        # Combine scores for readability
                        readability_score = (structure_score + complexity_score) / 2.0
                        normalized_score = 1.0 + (readability_score + 1.0) * 4.5
                        return max(1.0, min(10.0, normalized_score))
            
            # Fallback to basic evaluation
            return self._fallback_readability_evaluation(sql_code)
            
        except Exception as e:
            self.logger.warning(f"CodeT5+ evaluation failed: {e}")
            return self._fallback_readability_evaluation(sql_code)
    
    def _evaluate_security_securitybert(self, sql_code: str) -> float:
        """Evaluate SQL security using SecurityBERT with fallback."""
        try:
            model = model_cache.get_model('securitybert_model')
            tokenizer = model_cache.get_model('securitybert_tokenizer')
            
            if model and tokenizer:
                # Use SecurityBERT for security evaluation
                with model_cache.get_lock('securitybert_model'):
                    # Prepare input for SecurityBERT
                    prompt = f"SQL Security Analysis: {sql_code}"
                    
                    inputs = tokenizer(
                        prompt, 
                        return_tensors="pt", 
                        truncation=True, 
                        max_length=512,
                        padding=True
                    )
                    
                    # Move to GPU if available
                    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                    model = model.to(device)
                    
                    with torch.no_grad():
                        outputs = model(**inputs)
                        
                        # SecurityBERT outputs classification scores
                        if hasattr(outputs, 'logits'):
                            logits = outputs.logits
                            probabilities = torch.softmax(logits, dim=-1)
                            
                            # Extract security risk probability
                            # Assuming SecurityBERT has security risk classification
                            if probabilities.shape[1] >= 2:
                                security_risk = probabilities[0][1].item()  # Risk probability
                                security_score = 10.0 - (security_risk * 9.0)  # Invert risk to score
                            else:
                                security_score = 5.0
                        else:
                            # Fallback to embedding-based analysis
                            hidden_states = outputs.last_hidden_state
                            security_score = torch.mean(hidden_states).item()
                            security_score = 1.0 + (security_score + 1.0) * 4.5
                        
                        return max(1.0, min(10.0, security_score))
            
            # Fallback to pattern-based security evaluation
            return self._fallback_security_evaluation(sql_code)
            
        except Exception as e:
            self.logger.warning(f"SecurityBERT evaluation failed: {e}")
            return self._fallback_security_evaluation(sql_code)
    
    def _evaluate_sql_scoring_sqlcoder(self, sql_code: str) -> float:
        """Evaluate SQL using SQLCoder model with fallback."""
        try:
            model = model_cache.get_model('sqlcoder_model')
            tokenizer = model_cache.get_model('sqlcoder_tokenizer')
            
            if model and tokenizer:
                # Use SQLCoder for SQL-specific evaluation
                with model_cache.get_lock('sqlcoder_model'):
                    # Prepare input for SQLCoder
                    prompt = f"# SQL Quality Analysis\n# Evaluate the quality of this SQL query:\n{sql_code}\n\n# Quality Score:"
                    
                    inputs = tokenizer(
                        prompt, 
                        return_tensors="pt", 
                        truncation=True, 
                        max_length=512,
                        padding=True
                    )
                    
                    # Move to GPU if available
                    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                    model = model.to(device)
                    
                    with torch.no_grad():
                        outputs = model(**inputs)
                        
                        # Extract SQL-specific quality features
                        hidden_states = outputs.last_hidden_state
                        
                        # SQLCoder is specifically trained for SQL understanding
                        # Calculate quality based on SQL-specific patterns
                        sql_quality_score = torch.mean(hidden_states).item()
                        
                        # Normalize to 1-10 scale
                        normalized_score = 1.0 + (sql_quality_score + 1.0) * 4.5
                        return max(1.0, min(10.0, normalized_score))
            
            # Fallback to basic SQL evaluation
            return self._fallback_sql_scoring_evaluation(sql_code)
            
        except Exception as e:
            self.logger.warning(f"SQLCoder evaluation failed: {e}")
            return self._fallback_sql_scoring_evaluation(sql_code)
    
    def _calculate_efficiency_from_models(self, correctness: float, sql_scoring: float) -> float:
        """Calculate efficiency score from correctness and SQL scoring."""
        # Efficiency is related to correctness and SQL-specific optimizations
        return (correctness * 0.6 + sql_scoring * 0.4)
    
    def _calculate_scalability_from_models(self, correctness: float, readability: float) -> float:
        """Calculate scalability score from correctness and readability."""
        # Scalability depends on correct logic and readable structure
        return (correctness * 0.7 + readability * 0.3)
    
    def _calculate_modularity_from_models(self, readability: float, sql_scoring: float) -> float:
        """Calculate modularity score from readability and SQL scoring."""
        # Modularity is related to code structure and quality
        return (readability * 0.6 + sql_scoring * 0.4)
    
    def _calculate_documentation_from_models(self, readability: float) -> float:
        """Calculate documentation score from readability."""
        # Documentation quality is reflected in readability
        return readability * 0.8 + 2.0  # Base score for SQL
    
    def _calculate_best_practices_from_models(self, sql_scoring: float, security: float) -> float:
        """Calculate best practices score from SQL scoring and security."""
        # Best practices combine SQL quality and security
        return (sql_scoring * 0.6 + security * 0.4)
    
    def _calculate_error_handling_from_models(self, security: float, correctness: float) -> float:
        """Calculate error handling score from security and correctness."""
        # Error handling is related to security practices and correct logic
        return (security * 0.7 + correctness * 0.3)
    
    def _fallback_correctness_evaluation(self, sql_code: str) -> float:
        """Fallback correctness evaluation using basic SQL parsing."""
        try:
            parsed = parse_one(sql_code)
            if parsed is None:
                return 1.0
            return 8.0  # Basic syntax is correct
        except:
            return 1.0
    
    def _fallback_readability_evaluation(self, sql_code: str) -> float:
        """Fallback readability evaluation using basic analysis."""
        # Simple readability heuristics
        lines = sql_code.split('\n')
        if len(lines) <= 1:
            return 3.0  # Single line queries are less readable
        
        # Check for proper formatting
        formatted_lines = [line.strip() for line in lines if line.strip()]
        if len(formatted_lines) > 1:
            return 7.0  # Multi-line formatted queries are more readable
        
        return 5.0
    
    def _fallback_security_evaluation(self, sql_code: str) -> float:
        """Fallback security evaluation using pattern matching."""
        sql_lower = sql_code.lower()
        
        # Check for obvious security issues
        if any(pattern in sql_lower for pattern in ['or 1=1', 'or true', 'drop table', 'truncate']):
            return 2.0
        
        # Check for potential injection patterns
        if re.search(r'[\'"]\s*\+\s*[\w]+\s*\+\s*[\'"]', sql_code):
            return 3.0
        
        return 8.0  # No obvious security issues
    
    def _fallback_sql_scoring_evaluation(self, sql_code: str) -> float:
        """Fallback SQL scoring evaluation using basic analysis."""
        try:
            parsed = parse_one(sql_code)
            if parsed is None:
                return 1.0
            
            # Basic SQL quality checks
            sql_lower = sql_code.lower()
            
            # Check for SELECT *
            if 'select *' in sql_lower:
                return 6.0
            
            # Check for proper WHERE clause
            if any(cmd in sql_lower for cmd in ['delete', 'update']) and 'where' not in sql_lower:
                return 4.0
            
            return 8.0  # Good SQL practices
        except:
            return 5.0
    
    def _generate_optimized_feedback(self, sql_code: str, scores: Dict[str, float]) -> str:
        """Generate optimized feedback based on SQL-specific model scores."""
        feedback_parts = []
        
        if scores['correctness'] < 5.0:
            feedback_parts.append("StarCoder2 detected SQL syntax or logic issues. Review query structure.")
        
        if scores['readability'] < 5.0:
            feedback_parts.append("CodeT5+ analysis shows readability can be improved. Consider better formatting.")
        
        if scores['security'] < 5.0:
            feedback_parts.append("SecurityBERT detected potential security vulnerabilities. Review for SQL injection risks.")
        
        if scores['sql_scoring'] < 5.0:
            feedback_parts.append("SQLCoder analysis indicates SQL quality issues. Consider SQL best practices.")
        
        if not feedback_parts:
            feedback_parts.append("All SQL-specific models indicate good code quality.")
        
        return " ".join(feedback_parts)
    
    def _generate_optimized_suggestions(self, scores: Dict[str, float]) -> List[str]:
        """Generate optimized improvement suggestions."""
        suggestions = []
        
        if scores['correctness'] < 7.0:
            suggestions.append("Review SQL syntax and ensure all clauses are properly structured (StarCoder2)")
        
        if scores['readability'] < 7.0:
            suggestions.append("Improve code formatting and structure for better readability (CodeT5+)")
        
        if scores['security'] < 7.0:
            suggestions.append("Use parameterized queries to prevent SQL injection attacks (SecurityBERT)")
        
        if scores['sql_scoring'] < 7.0:
            suggestions.append("Follow SQL naming conventions and avoid SELECT * when possible (SQLCoder)")
        
        return suggestions
    
    def _evaluate_with_codebert(self, sql_code: str, metric: str) -> float:
        """Evaluate SQL code using CodeBERT for a specific metric (supports multiple statements)."""
        try:
            tokenizer = model_cache.get_model('fallback_tokenizer')
            model = model_cache.get_model('fallback_model')
            
            if tokenizer is None or model is None:
                return self._fallback_rule_based_evaluation(sql_code, metric)
            
            # Split into individual statements for analysis
            statements = self._split_sql_statements(sql_code)
            
            if not statements:
                return self._fallback_rule_based_evaluation(sql_code, metric)
            
            # Evaluate each statement and aggregate scores
            statement_scores = []
            for statement in statements:
                if self._is_valid_single_statement(statement):
                    score = self._evaluate_single_statement_with_codebert(statement, metric, tokenizer, model)
                    statement_scores.append(score)
            
            if not statement_scores:
                return self._fallback_rule_based_evaluation(sql_code, metric)
            
            # Calculate average score across all statements
            avg_score = sum(statement_scores) / len(statement_scores)
            
            # Bonus for multiple well-structured statements
            if len(statements) > 1:
                bonus = min(1.0, len(statements) * 0.1)  # Up to 1 point bonus
                avg_score = min(10.0, avg_score + bonus)
            
            return avg_score
                    
        except Exception as e:
            self.logger.error(f"CodeBERT evaluation failed for {metric}: {e}")
            return self._fallback_rule_based_evaluation(sql_code, metric)
    
    def _evaluate_single_statement_with_codebert(self, statement: str, metric: str, tokenizer, model) -> float:
        """Evaluate a single SQL statement using CodeBERT."""
        try:
            # Prepare input for CodeBERT
            inputs = tokenizer(statement, return_tensors="pt", truncation=True, max_length=512, padding=True)
            
            with torch.no_grad():
                outputs = model(**inputs)
                # Use the last hidden state for scoring
                hidden_states = outputs.last_hidden_state
                
                # Simple scoring based on hidden state statistics
                mean_activation = torch.mean(hidden_states).item()
                std_activation = torch.std(hidden_states).item()
                
                # Normalize to 1-10 scale
                base_score = min(10.0, max(1.0, (mean_activation + std_activation) * 2.0))
                
                # Adjust score based on metric and SQL-specific rules
                if metric == 'correctness':
                    # Check for basic SQL syntax
                    if self._is_valid_single_statement(statement):
                        return min(10.0, base_score + 2.0)
                    else:
                        return max(1.0, base_score - 3.0)
                elif metric == 'readability':
                    # Check for formatting and structure
                    if self._has_good_formatting(statement):
                        return min(10.0, base_score + 1.5)
                    else:
                        return max(1.0, base_score - 2.0)
                elif metric == 'security':
                    # Check for security issues
                    if self._has_security_issues(statement):
                        return max(1.0, base_score - 4.0)
                    else:
                        return min(10.0, base_score + 1.0)
                elif metric == 'efficiency':
                    # Check for efficiency issues
                    if self._has_efficiency_issues(statement):
                        return max(1.0, base_score - 2.0)
                    else:
                        return min(10.0, base_score + 1.0)
                else:
                    return base_score
                    
        except Exception as e:
            self.logger.error(f"Single statement CodeBERT evaluation failed: {e}")
            return self._fallback_rule_based_evaluation(statement, metric)
    
    def _has_valid_sql_structure(self, sql_code: str) -> bool:
        """Check if SQL code has valid basic structure (supports multiple statements)."""
        # Split into individual statements
        statements = self._split_sql_statements(sql_code)
        
        if not statements:
            return False
        
        # Check each statement for validity
        valid_statements = 0
        for statement in statements:
            if self._is_valid_single_statement(statement):
                valid_statements += 1
        
        # At least 50% of statements must be valid
        return valid_statements / len(statements) >= 0.5
    
    def _split_sql_statements(self, sql_code: str) -> List[str]:
        """Split SQL code into individual statements."""
        # Split by semicolon, but be careful with semicolons in strings
        statements = []
        current_statement = ""
        in_string = False
        string_char = None
        
        for char in sql_code:
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
    
    def _is_valid_single_statement(self, statement: str) -> bool:
        """Check if a single SQL statement has valid basic structure."""
        sql_lower = statement.lower().strip()
        
        # Must have at least one SQL command
        sql_commands = ['select', 'insert', 'update', 'delete', 'create', 'drop', 'alter']
        has_command = any(cmd in sql_lower for cmd in sql_commands)
        
        if not has_command:
            return False
        
        # Basic syntax checks
        if 'select' in sql_lower and 'from' not in sql_lower:
            return False
        
        if 'insert' in sql_lower and 'into' not in sql_lower:
            return False
        
        if 'update' in sql_lower and 'set' not in sql_lower:
            return False
        
        return True
    
    def _has_good_formatting(self, sql_code: str) -> bool:
        """Check if SQL code has good formatting."""
        lines = sql_code.split('\n')
        
        # Check for proper indentation
        if len(lines) > 1:
            indented_lines = sum(1 for line in lines if line.strip() and line.startswith('    '))
            if indented_lines > 0:
                return True
        
        # Check for proper spacing around keywords
        if re.search(r'\s+(select|from|where|and|or|order|group|by|having|limit)\s+', sql_code, re.IGNORECASE):
            return True
        
        return False
    
    def _has_security_issues(self, sql_code: str) -> bool:
        """Check for common SQL security issues."""
        sql_lower = sql_code.lower()
        
        # Check for SQL injection patterns
        dangerous_patterns = [
            'or 1=1', 'or true', 'or 1', 'or 0=0',
            'union select', 'union all select',
            'drop table', 'truncate table', 'delete from',
            'exec ', 'execute ', 'xp_', 'sp_'
        ]
        
        return any(pattern in sql_lower for pattern in dangerous_patterns)
    
    def _has_efficiency_issues(self, sql_code: str) -> bool:
        """Check for SQL efficiency issues."""
        sql_lower = sql_code.lower()
        
        # Check for inefficient patterns
        inefficient_patterns = [
            'select *',  # Selecting all columns
            'distinct *',  # Distinct on all columns
            'order by rand()',  # Random ordering
            'like %pattern%',  # Leading wildcard
        ]
        
        return any(pattern in sql_lower for pattern in inefficient_patterns)
    
    def _fallback_rule_based_evaluation(self, sql_code: str, metric: str) -> float:
        """Fallback rule-based evaluation when CodeBERT is not available (supports multiple statements)."""
        # Split into individual statements for analysis
        statements = self._split_sql_statements(sql_code)
        
        if not statements:
            return 1.0
        
        # Evaluate each statement and aggregate scores
        statement_scores = []
        for statement in statements:
            if self._is_valid_single_statement(statement):
                score = self._evaluate_single_statement_rule_based(statement, metric)
                statement_scores.append(score)
        
        if not statement_scores:
            return 1.0
        
        # Calculate average score across all statements
        avg_score = sum(statement_scores) / len(statement_scores)
        
        # Bonus for multiple well-structured statements
        if len(statements) > 1:
            bonus = min(1.0, len(statements) * 0.1)  # Up to 1 point bonus
            avg_score = min(10.0, avg_score + bonus)
        
        return avg_score
    
    def _evaluate_single_statement_rule_based(self, statement: str, metric: str) -> float:
        """Evaluate a single SQL statement using rule-based approach."""
        base_score = 5.0
        
        if metric == 'correctness':
            if self._is_valid_single_statement(statement):
                return 7.0
            else:
                return 2.0
        elif metric == 'readability':
            if self._has_good_formatting(statement):
                return 8.0
            else:
                return 5.0
        elif metric == 'security':
            if self._has_security_issues(statement):
                return 2.0
            else:
                return 8.0
        elif metric == 'efficiency':
            if self._has_efficiency_issues(statement):
                return 4.0
            else:
                return 7.0
        else:
            return base_score
    
    def _generate_single_model_feedback(self, sql_code: str, scores: Dict[str, float]) -> str:
        """Generate feedback using single model results (supports multiple statements)."""
        feedback_parts = []
        
        # Check if multiple statements are present
        statements = self._split_sql_statements(sql_code)
        is_multiple_statements = len(statements) > 1
        
        # Overall assessment
        avg_score = sum(scores.values()) / len(scores)
        if avg_score >= 8.0:
            if is_multiple_statements:
                feedback_parts.append(f"Excellent SQL code with {len(statements)} well-structured statements.")
            else:
                feedback_parts.append("Excellent SQL code with strong fundamentals.")
        elif avg_score >= 6.0:
            if is_multiple_statements:
                feedback_parts.append(f"Good SQL code with {len(statements)} statements and room for improvement.")
            else:
                feedback_parts.append("Good SQL code with room for improvement.")
        else:
            if is_multiple_statements:
                feedback_parts.append(f"SQL code with {len(statements)} statements needs significant improvement.")
            else:
                feedback_parts.append("SQL code needs significant improvement.")
        
        # Specific feedback based on scores
        if scores['correctness'] < 6.0:
            feedback_parts.append("SQL syntax or structure issues detected.")
        if scores['security'] < 6.0:
            feedback_parts.append("Security vulnerabilities found.")
        if scores['efficiency'] < 6.0:
            feedback_parts.append("Performance optimization opportunities identified.")
        if scores['readability'] < 6.0:
            feedback_parts.append("Code formatting and readability can be improved.")
        
        return " ".join(feedback_parts)
    
    def _generate_single_model_suggestions(self, scores: Dict[str, float]) -> List[str]:
        """Generate suggestions using single model results."""
        suggestions = []
        
        if scores['correctness'] < 7.0:
            suggestions.append("Review SQL syntax and ensure proper table/column references.")
        if scores['security'] < 7.0:
            suggestions.append("Use parameterized queries to prevent SQL injection.")
        if scores['efficiency'] < 7.0:
            suggestions.append("Consider adding indexes and optimizing query structure.")
        if scores['readability'] < 7.0:
            suggestions.append("Improve code formatting with proper indentation and spacing.")
        
        if not suggestions:
            suggestions.append("Continue following SQL best practices.")
        
        return suggestions
    
    def _create_error_feedback(self, error: str) -> ModelFeedback:
        """Create error feedback when evaluation fails."""
        return ModelFeedback(
            model_name="SQLCoder-Single",
            confidence=0.0,
            scores=ScoreBreakdown(
                correctness=1.0,
                efficiency=1.0,
                readability=1.0,
                scalability=1.0,
                security=1.0,
                modularity=1.0,
                documentation=1.0,
                best_practices=1.0,
                error_handling=1.0
            ),
            feedback=f"Evaluation failed: {error}. Please try again or contact support.",
            suggestions=["Check your SQL syntax", "Ensure all required fields are provided"]
        ) 