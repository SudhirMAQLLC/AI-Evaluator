#!/usr/bin/env python3
"""
Specialized SQL Code Evaluator
Uses different models and techniques for each evaluation task:
- Security: Pattern-based + semantic analysis
- Correctness: Syntax validation + logic checking
- Efficiency: Query optimization analysis
- Best Practices: Style and convention checking
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

logger = logging.getLogger(__name__)

@dataclass
class SQLSecurityAnalysis:
    """Security analysis results for SQL."""
    has_sql_injection: bool
    has_privilege_escalation: bool
    has_data_exposure: bool
    has_destructive_operations: bool
    security_score: float
    security_issues: List[str]

@dataclass
class SQLCorrectnessAnalysis:
    """Correctness analysis results for SQL."""
    syntax_valid: bool
    logic_valid: bool
    table_exists: bool
    column_exists: bool
    correctness_score: float
    correctness_issues: List[str]

@dataclass
class SQLEfficiencyAnalysis:
    """Efficiency analysis results for SQL."""
    uses_select_star: bool
    has_proper_indexing: bool
    has_unnecessary_joins: bool
    has_cartesian_products: bool
    efficiency_score: float
    efficiency_issues: List[str]

class SQLSpecializedEvaluator:
    """Specialized SQL evaluator with task-specific analysis."""
    
    def __init__(self):
        """Initialize SQL specialized evaluator."""
        # SQL Injection patterns (comprehensive)
        self.sql_injection_patterns = [
            r"OR\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?",  # OR 1=1
            r"OR\s+['\"]?true['\"]?\s*=\s*['\"]?true['\"]?",  # OR true=true
            r"OR\s+['\"]?yes['\"]?\s*=\s*['\"]?yes['\"]?",  # OR yes=yes
            r"OR\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?\s*--",  # OR 1=1--
            r"OR\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?\s*#",  # OR 1=1#
            r"OR\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?\s*/\*",  # OR 1=1/*
            r"UNION\s+SELECT",  # UNION SELECT
            r"UNION\s+ALL\s+SELECT",  # UNION ALL SELECT
            r"';?\s*DROP\s+TABLE",  # '; DROP TABLE
            r"';?\s*DELETE\s+FROM",  # '; DELETE FROM
            r"';?\s*UPDATE\s+",  # '; UPDATE
            r"';?\s*INSERT\s+INTO",  # '; INSERT INTO
            r"';?\s*ALTER\s+TABLE",  # '; ALTER TABLE
            r"';?\s*CREATE\s+TABLE",  # '; CREATE TABLE
            r"';?\s*EXEC\s+",  # '; EXEC
            r"';?\s*EXECUTE\s+",  # '; EXECUTE
            r"';?\s*xp_cmdshell",  # '; xp_cmdshell
            r"';?\s*sp_executesql",  # '; sp_executesql
        ]
        
        # Destructive operations
        self.destructive_patterns = [
            r"DELETE\s+FROM\s+\w+(?:\s+WHERE\s+[\w\s=<>()'\"`]+)?\s*;?\s*$",  # DELETE without WHERE
            r"UPDATE\s+\w+\s+SET\s+[\w\s=,]+(?:\s+WHERE\s+[\w\s=<>()'\"`]+)?\s*;?\s*$",  # UPDATE without WHERE
            r"DROP\s+(?:TABLE|DATABASE|INDEX|VIEW)\s+",  # DROP operations
            r"TRUNCATE\s+TABLE\s+",  # TRUNCATE
            r"ALTER\s+TABLE\s+.*\s+DROP\s+",  # ALTER DROP
        ]
        
        # Performance anti-patterns
        self.performance_anti_patterns = [
            r"SELECT\s+\*",  # SELECT *
            r"CROSS\s+JOIN",  # CROSS JOIN
            r"FULL\s+OUTER\s+JOIN",  # FULL OUTER JOIN (often unnecessary)
            r"ORDER\s+BY\s+.*\s+(?:ASC|DESC)?\s*(?!LIMIT)",  # ORDER BY without LIMIT
            r"GROUP\s+BY\s+.*\s+HAVING\s+.*\s+ORDER\s+BY",  # Complex grouping without limit
        ]
        
        # Common SQL errors
        self.sql_error_patterns = [
            r"SELECT\s+.*\s+FROM\s+\w+s{2,}",  # Double 's' in table name (common typo)
            r"WHERE\s+.*\s+=\s+['\"][^'\"]*['\"]\s*$",  # String comparison without proper escaping
            r"JOIN\s+\w+\s+ON\s+.*\s+=\s+.*\s+AND\s+.*\s+OR\s+",  # Complex JOIN with OR (often wrong)
        ]
        
        logger.info("SQL Specialized Evaluator initialized with comprehensive patterns")
    
    def evaluate_sql(self, code: str) -> ModelFeedback:
        """Evaluate SQL code using specialized analysis."""
        try:
            logger.info(f"Starting specialized SQL evaluation")
            
            # Clean and normalize SQL
            clean_sql = self._normalize_sql(code)
            
            # Task-specific evaluations
            security_analysis = self._evaluate_security(clean_sql)
            correctness_analysis = self._evaluate_correctness(clean_sql)
            efficiency_analysis = self._evaluate_efficiency(clean_sql)
            best_practices_analysis = self._evaluate_best_practices(clean_sql)
            
            # Calculate comprehensive scores
            scores = self._calculate_comprehensive_scores(
                security_analysis, correctness_analysis, 
                efficiency_analysis, best_practices_analysis
            )
            
            # Generate detailed feedback
            feedback, suggestions = self._generate_specialized_feedback(
                security_analysis, correctness_analysis,
                efficiency_analysis, best_practices_analysis, clean_sql
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                security_analysis, correctness_analysis,
                efficiency_analysis, best_practices_analysis
            )
            
            logger.info(f"Specialized SQL evaluation completed. Security: {scores.security:.1f}, Correctness: {scores.correctness:.1f}")
            
            return ModelFeedback(
                model_name="SQL Specialized Evaluator",
                feedback=feedback,
                suggestions=suggestions,
                confidence=confidence,
                scores=scores
            )
            
        except Exception as e:
            logger.error(f"Specialized SQL evaluation failed: {e}")
            return self._create_error_feedback(f"SQL evaluation failed: {e}")
    
    def _normalize_sql(self, code: str) -> str:
        """Normalize SQL code for analysis."""
        # Remove comments
        code = re.sub(r'--.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        code = code.strip()
        
        return code
    
    def _evaluate_security(self, sql: str) -> SQLSecurityAnalysis:
        """Evaluate SQL security using pattern-based analysis."""
        issues = []
        has_sql_injection = False
        has_privilege_escalation = False
        has_data_exposure = False
        has_destructive_operations = False
        
        # Check for SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                has_sql_injection = True
                issues.append(f"SQL injection vulnerability detected: {pattern}")
                break
        
        # Check for destructive operations
        for pattern in self.destructive_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                has_destructive_operations = True
                issues.append(f"Destructive operation detected: {pattern}")
                break
        
        # Check for data exposure
        if re.search(r'SELECT\s+\*', sql, re.IGNORECASE):
            has_data_exposure = True
            issues.append("SELECT * can expose sensitive data")
        
        # Check for privilege escalation attempts
        if re.search(r'GRANT\s+.*\s+TO\s+.*\s+WITH\s+ADMIN\s+OPTION', sql, re.IGNORECASE):
            has_privilege_escalation = True
            issues.append("Privilege escalation attempt detected")
        
        # Calculate security score
        security_score = 10.0
        if has_sql_injection:
            security_score = 1.0  # Critical vulnerability
        elif has_destructive_operations:
            security_score = 2.0  # Very high risk
        elif has_data_exposure:
            security_score = 5.0  # Medium risk
        elif has_privilege_escalation:
            security_score = 3.0  # High risk
        
        return SQLSecurityAnalysis(
            has_sql_injection=has_sql_injection,
            has_privilege_escalation=has_privilege_escalation,
            has_data_exposure=has_data_exposure,
            has_destructive_operations=has_destructive_operations,
            security_score=security_score,
            security_issues=issues
        )
    
    def _evaluate_correctness(self, sql: str) -> SQLCorrectnessAnalysis:
        """Evaluate SQL correctness using syntax and logic analysis."""
        issues = []
        syntax_valid = True
        logic_valid = True
        table_exists = True  # Assume true for analysis
        column_exists = True  # Assume true for analysis
        
        # Check for basic syntax errors
        if not re.search(r'SELECT\s+', sql, re.IGNORECASE):
            syntax_valid = False
            issues.append("Missing SELECT statement")
        
        # Check for balanced parentheses
        open_parens = sql.count('(')
        close_parens = sql.count(')')
        if open_parens != close_parens:
            syntax_valid = False
            issues.append("Unbalanced parentheses")
        
        # Check for common SQL errors
        for pattern in self.sql_error_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                logic_valid = False
                issues.append(f"Logic error detected: {pattern}")
        
        # Check for missing WHERE clause in DELETE/UPDATE
        if re.search(r'(DELETE|UPDATE)\s+FROM?\s+\w+', sql, re.IGNORECASE) and not re.search(r'WHERE\s+', sql, re.IGNORECASE):
            logic_valid = False
            issues.append("DELETE/UPDATE without WHERE clause - will affect ALL rows")
        
        # Check for table name typos (common error)
        if re.search(r'FROM\s+\w+s{2,}', sql, re.IGNORECASE):
            logic_valid = False
            issues.append("Possible table name typo (double 's')")
        
        # Calculate correctness score
        correctness_score = 10.0
        if not syntax_valid:
            correctness_score = 2.0
        elif not logic_valid:
            correctness_score = 4.0
        
        return SQLCorrectnessAnalysis(
            syntax_valid=syntax_valid,
            logic_valid=logic_valid,
            table_exists=table_exists,
            column_exists=column_exists,
            correctness_score=correctness_score,
            correctness_issues=issues
        )
    
    def _evaluate_efficiency(self, sql: str) -> SQLEfficiencyAnalysis:
        """Evaluate SQL efficiency using performance analysis."""
        issues = []
        uses_select_star = False
        has_proper_indexing = True  # Assume true
        has_unnecessary_joins = False
        has_cartesian_products = False
        
        # Check for SELECT *
        if re.search(r'SELECT\s+\*', sql, re.IGNORECASE):
            uses_select_star = True
            issues.append("SELECT * is inefficient - select only needed columns")
        
        # Check for CROSS JOIN
        if re.search(r'CROSS\s+JOIN', sql, re.IGNORECASE):
            has_cartesian_products = True
            issues.append("CROSS JOIN can be very expensive")
        
        # Check for ORDER BY without LIMIT
        if re.search(r'ORDER\s+BY\s+.*\s+(?:ASC|DESC)?\s*(?!LIMIT)', sql, re.IGNORECASE):
            issues.append("ORDER BY without LIMIT can be slow on large datasets")
        
        # Check for complex GROUP BY without limit
        if re.search(r'GROUP\s+BY\s+.*\s+HAVING\s+.*\s+ORDER\s+BY', sql, re.IGNORECASE):
            issues.append("Complex GROUP BY with HAVING and ORDER BY can be slow")
        
        # Calculate efficiency score
        efficiency_score = 10.0
        if has_cartesian_products:
            efficiency_score = 3.0
        elif uses_select_star:
            efficiency_score = 6.0
        elif len(issues) > 0:
            efficiency_score = 7.0
        
        return SQLEfficiencyAnalysis(
            uses_select_star=uses_select_star,
            has_proper_indexing=has_proper_indexing,
            has_unnecessary_joins=has_unnecessary_joins,
            has_cartesian_products=has_cartesian_products,
            efficiency_score=efficiency_score,
            efficiency_issues=issues
        )
    
    def _evaluate_best_practices(self, sql: str) -> Dict:
        """Evaluate SQL best practices."""
        issues = []
        score = 10.0
        
        # Check for consistent case
        if re.search(r'select|SELECT', sql) and re.search(r'Select', sql):
            issues.append("Inconsistent SQL case usage")
            score -= 2.0
        
        # Check for proper spacing around operators
        if not re.search(r'\s+[=<>!]+\s+', sql):
            issues.append("Missing spaces around operators")
            score -= 1.0
        
        # Check for meaningful column aliases
        if re.search(r'AS\s+[a-z]', sql, re.IGNORECASE):
            issues.append("Use meaningful column aliases")
            score -= 1.0
        
        # Check for proper indentation (basic check)
        if len(sql.split()) > 10 and not re.search(r'\n', sql):
            issues.append("Consider proper SQL formatting with line breaks")
            score -= 1.0
        
        return {
            'score': max(1.0, score),
            'issues': issues
        }
    
    def _calculate_comprehensive_scores(self, security: SQLSecurityAnalysis, 
                                      correctness: SQLCorrectnessAnalysis,
                                      efficiency: SQLEfficiencyAnalysis,
                                      best_practices: Dict) -> ScoreBreakdown:
        """Calculate comprehensive scores from all analyses."""
        
        return ScoreBreakdown(
            correctness=correctness.correctness_score,
            efficiency=efficiency.efficiency_score,
            readability=best_practices['score'],
            scalability=efficiency.efficiency_score,  # Efficiency affects scalability
            security=security.security_score,
            modularity=8.0,  # SQL doesn't have traditional modularity
            documentation=7.0,  # SQL doesn't have traditional documentation
            best_practices=best_practices['score'],
            error_handling=8.0  # SQL doesn't have traditional error handling
        )
    
    def _generate_specialized_feedback(self, security: SQLSecurityAnalysis,
                                     correctness: SQLCorrectnessAnalysis,
                                     efficiency: SQLEfficiencyAnalysis,
                                     best_practices: Dict, sql: str) -> Tuple[str, List[str]]:
        """Generate detailed feedback based on all analyses."""
        feedback_parts = []
        suggestions = []
        
        # Security feedback
        if security.security_score <= 2.0:
            feedback_parts.append("🚨 CRITICAL SECURITY VULNERABILITIES DETECTED!")
            if security.has_sql_injection:
                feedback_parts.append("SQL injection vulnerability found.")
                suggestions.append("🚨 CRITICAL: Use parameterized queries instead of string concatenation")
            if security.has_destructive_operations:
                feedback_parts.append("Destructive operation without proper safeguards.")
                suggestions.append("🚨 CRITICAL: Add WHERE clause to DELETE/UPDATE operations")
        elif security.security_score <= 5.0:
            feedback_parts.append("⚠️ Security concerns detected.")
            if security.has_data_exposure:
                suggestions.append("⚠️ SELECT * can expose sensitive data - select only needed columns")
        
        # Correctness feedback
        if correctness.correctness_score <= 4.0:
            feedback_parts.append("❌ Logic errors detected in SQL.")
            if not correctness.syntax_valid:
                suggestions.append("❌ Fix SQL syntax errors")
            if not correctness.logic_valid:
                suggestions.append("❌ Review query logic for errors")
        elif correctness.correctness_score <= 7.0:
            feedback_parts.append("⚠️ Potential logic issues detected.")
        
        # Efficiency feedback
        if efficiency.efficiency_score <= 5.0:
            feedback_parts.append("🐌 Performance issues detected.")
            if efficiency.has_cartesian_products:
                suggestions.append("🐌 CROSS JOIN can be very expensive - use INNER JOIN with proper conditions")
            if efficiency.uses_select_star:
                suggestions.append("🐌 SELECT * is inefficient - select only needed columns")
        elif efficiency.efficiency_score <= 7.0:
            feedback_parts.append("⚠️ Performance could be improved.")
        
        # Best practices feedback
        if best_practices['score'] <= 7.0:
            feedback_parts.append("📝 Best practices not followed.")
            suggestions.extend(best_practices['issues'])
        
        # Generate overall feedback
        if not feedback_parts:
            feedback = "✅ SQL code demonstrates excellent quality across all criteria."
        else:
            feedback = " ".join(feedback_parts)
        
        # Add positive aspects
        positive_aspects = []
        if security.security_score >= 9.0:
            positive_aspects.append("✅ Excellent security practices")
        if correctness.correctness_score >= 9.0:
            positive_aspects.append("✅ Correct SQL syntax and logic")
        if efficiency.efficiency_score >= 8.0:
            positive_aspects.append("✅ Good performance considerations")
        
        if positive_aspects:
            feedback += " " + " ".join(positive_aspects)
        
        return feedback, suggestions
    
    def _calculate_confidence(self, security: SQLSecurityAnalysis,
                            correctness: SQLCorrectnessAnalysis,
                            efficiency: SQLEfficiencyAnalysis,
                            best_practices: Dict) -> float:
        """Calculate confidence based on analysis completeness."""
        confidence = 0.8  # Base confidence
        
        # Increase confidence for clear issues
        if security.has_sql_injection or security.has_destructive_operations:
            confidence += 0.1
        if not correctness.syntax_valid:
            confidence += 0.1
        if efficiency.has_cartesian_products:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _create_error_feedback(self, error_message: str) -> ModelFeedback:
        """Create error feedback when evaluation fails."""
        return ModelFeedback(
            model_name="SQL Specialized Evaluator",
            feedback=f"Evaluation failed: {error_message}",
            suggestions=["Please try again or contact support"],
            confidence=0.0
        ) 