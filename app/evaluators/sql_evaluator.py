import sqlparse
import re
from typing import List, Dict, Any, Optional
import os

from app.evaluators.base_evaluator import BaseEvaluator
from app.schemas.evaluation import EvaluationResult, ComponentStatus

class SQLEvaluator(BaseEvaluator):
    """Evaluates SQL scripts for Snowflake assignments"""
    
    def __init__(self, assignment_brief: Optional[Dict[str, Any]] = None):
        super().__init__(assignment_brief)
        self.sql_content = ""
        self.parsed_statements = []
    
    def evaluate(self, file_path: str) -> List[EvaluationResult]:
        """Evaluate a SQL file"""
        try:
            # Read SQL file
            with open(file_path, 'r', encoding='utf-8') as f:
                self.sql_content = f.read()
            
            # Parse SQL statements
            self.parsed_statements = sqlparse.parse(self.sql_content)
            
            # Evaluate different aspects
            self._evaluate_syntax()
            self._evaluate_snowflake_features()
            self._evaluate_best_practices()
            self._evaluate_security()
            self._evaluate_automation()
            
            return self.results
            
        except Exception as e:
            self.add_result(
                "sql_parsing",
                0.0,
                10.0,
                ComponentStatus.FAILED,
                f"Failed to parse SQL file: {str(e)}"
            )
            return self.results
    
    def _evaluate_syntax(self):
        """Evaluate SQL syntax correctness"""
        score = 0.0
        max_score = 15.0
        feedback = []
        
        if not self.parsed_statements:
            feedback.append("No SQL statements found")
        else:
            score += 5.0
            feedback.append(f"Found {len(self.parsed_statements)} SQL statements")
        
        # Check for basic SQL keywords
        sql_keywords = ['SELECT', 'CREATE', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER']
        found_keywords = []
        
        for keyword in sql_keywords:
            if keyword in self.sql_content.upper():
                found_keywords.append(keyword)
        
        if found_keywords:
            score += 5.0
            feedback.append(f"Contains SQL keywords: {', '.join(found_keywords)}")
        
        # Check for proper statement termination
        if self.sql_content.strip().endswith(';'):
            score += 5.0
            feedback.append("Statements properly terminated")
        else:
            feedback.append("Missing statement termination")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.7 else ComponentStatus.PARTIAL
        self.add_result("sql_syntax", score, max_score, status, "; ".join(feedback))
    
    def _evaluate_snowflake_features(self):
        """Evaluate Snowflake-specific features"""
        score = 0.0
        max_score = 25.0
        feedback = []
        
        # Check for Snowflake-specific syntax
        snowflake_features = {
            'warehouse': r'CREATE\s+WAREHOUSE|USE\s+WAREHOUSE',
            'database': r'CREATE\s+DATABASE|USE\s+DATABASE',
            'schema': r'CREATE\s+SCHEMA|USE\s+SCHEMA',
            'table': r'CREATE\s+TABLE|CREATE\s+OR\s+REPLACE\s+TABLE',
            'view': r'CREATE\s+VIEW|CREATE\s+OR\s+REPLACE\s+VIEW',
            'secure_view': r'CREATE\s+SECURE\s+VIEW',
            'stored_procedure': r'CREATE\s+PROCEDURE|CREATE\s+OR\s+REPLACE\s+PROCEDURE',
            'task': r'CREATE\s+TASK|CREATE\s+OR\s+REPLACE\s+TASK',
            'masking_policy': r'CREATE\s+MASKING\s+POLICY',
            'row_access_policy': r'CREATE\s+ROW\s+ACCESS\s+POLICY',
            'role': r'CREATE\s+ROLE|GRANT\s+.*\s+TO\s+ROLE',
            'user': r'CREATE\s+USER|GRANT\s+.*\s+TO\s+USER'
        }
        
        found_features = []
        for feature_name, pattern in snowflake_features.items():
            if re.search(pattern, self.sql_content, re.IGNORECASE):
                found_features.append(feature_name)
                score += 2.0
        
        if found_features:
            feedback.append(f"Found Snowflake features: {', '.join(found_features)}")
        
        # Check for specific assignment requirements
        if self.assignment_brief:
            requirements = self.assignment_brief.get('requirements', [])
            for req in requirements:
                if 'warehouse' in req.lower() and 'warehouse' in found_features:
                    score += 3.0
                    feedback.append("Warehouse creation/usage found")
                elif 'schema' in req.lower() and 'schema' in found_features:
                    score += 3.0
                    feedback.append("Schema creation/usage found")
                elif 'table' in req.lower() and 'table' in found_features:
                    score += 3.0
                    feedback.append("Table creation found")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.5 else ComponentStatus.PARTIAL
        self.add_result("snowflake_features", score, max_score, status, "; ".join(feedback))
    
    def _evaluate_best_practices(self):
        """Evaluate SQL best practices"""
        score = 0.0
        max_score = 20.0
        feedback = []
        
        # Check for proper naming conventions
        if re.search(r'CREATE\s+TABLE\s+[A-Z_][A-Z0-9_]*', self.sql_content, re.IGNORECASE):
            score += 3.0
            feedback.append("Proper table naming convention")
        
        # Check for comments
        if '--' in self.sql_content or '/*' in self.sql_content:
            score += 3.0
            feedback.append("Contains SQL comments")
        
        # Check for proper data types
        data_types = ['STRING', 'INT', 'FLOAT', 'DATE', 'TIMESTAMP', 'BOOLEAN']
        found_types = [dt for dt in data_types if dt in self.sql_content.upper()]
        if found_types:
            score += 3.0
            feedback.append(f"Uses appropriate data types: {', '.join(found_types)}")
        
        # Check for constraints
        constraints = ['PRIMARY KEY', 'FOREIGN KEY', 'NOT NULL', 'UNIQUE']
        found_constraints = [c for c in constraints if c in self.sql_content.upper()]
        if found_constraints:
            score += 4.0
            feedback.append(f"Uses constraints: {', '.join(found_constraints)}")
        
        # Check for proper JOIN syntax
        if re.search(r'JOIN\s+.*\s+ON\s+', self.sql_content, re.IGNORECASE):
            score += 3.0
            feedback.append("Uses proper JOIN syntax")
        
        # Check for WHERE clauses
        if 'WHERE' in self.sql_content.upper():
            score += 2.0
            feedback.append("Uses WHERE clauses for filtering")
        
        # Check for ORDER BY
        if 'ORDER BY' in self.sql_content.upper():
            score += 2.0
            feedback.append("Uses ORDER BY for sorting")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.6 else ComponentStatus.PARTIAL
        self.add_result("best_practices", score, max_score, status, "; ".join(feedback))
    
    def _evaluate_security(self):
        """Evaluate security features"""
        score = 0.0
        max_score = 20.0
        feedback = []
        
        # Check for masking policies
        if 'MASKING POLICY' in self.sql_content.upper():
            score += 5.0
            feedback.append("Uses masking policies")
        
        # Check for row access policies
        if 'ROW ACCESS POLICY' in self.sql_content.upper():
            score += 5.0
            feedback.append("Uses row access policies")
        
        # Check for secure views
        if 'SECURE VIEW' in self.sql_content.upper():
            score += 5.0
            feedback.append("Uses secure views")
        
        # Check for role-based access
        if 'GRANT' in self.sql_content.upper() and 'ROLE' in self.sql_content.upper():
            score += 3.0
            feedback.append("Uses role-based access control")
        
        # Check for proper user management
        if 'CREATE USER' in self.sql_content.upper():
            score += 2.0
            feedback.append("Creates users")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.4 else ComponentStatus.PARTIAL
        self.add_result("security", score, max_score, status, "; ".join(feedback))
    
    def _evaluate_automation(self):
        """Evaluate automation features"""
        score = 0.0
        max_score = 20.0
        feedback = []
        
        # Check for tasks
        if 'CREATE TASK' in self.sql_content.upper():
            score += 8.0
            feedback.append("Uses Snowflake tasks for automation")
        
        # Check for stored procedures
        if 'CREATE PROCEDURE' in self.sql_content.upper():
            score += 6.0
            feedback.append("Uses stored procedures")
        
        # Check for scheduled execution
        if 'SCHEDULE' in self.sql_content.upper():
            score += 3.0
            feedback.append("Uses scheduled execution")
        
        # Check for data loading
        if 'COPY INTO' in self.sql_content.upper() or 'PUT' in self.sql_content.upper():
            score += 3.0
            feedback.append("Uses data loading commands")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.4 else ComponentStatus.PARTIAL
        self.add_result("automation", score, max_score, status, "; ".join(feedback)) 