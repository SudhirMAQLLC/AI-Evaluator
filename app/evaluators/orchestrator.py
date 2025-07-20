import os
import zipfile
import tempfile
import shutil
from typing import List, Dict, Any, Optional
import subprocess
import json
import yaml

from app.evaluators.base_evaluator import BaseEvaluator
from app.schemas.evaluation import EvaluationResult, ComponentStatus, AssignmentType
import logging

logger = logging.getLogger(__name__)

class AssignmentOrchestrator(BaseEvaluator):
    """Orchestrates evaluation using Otter-Grader and PyEvalAI"""
    
    def __init__(self, assignment_brief: Optional[Dict[str, Any]] = None):
        super().__init__(assignment_brief)
        self.extracted_path = None
        self.test_config = None
    
    def evaluate(self, file_path: str) -> List[EvaluationResult]:
        """Evaluate a ZIP file containing assignment materials"""
        try:
            # Extract ZIP file
            self.extracted_path = self._extract_zip(file_path)
            
            # Generate test configuration based on assignment type
            self.test_config = self._generate_test_config()
            
            # Run evaluations
            self._evaluate_file_structure()
            self._evaluate_with_otter_grader()
            self._evaluate_with_pyevalai()
            self._evaluate_specific_requirements()
            
            return self.results
            
        except Exception as e:
            self.add_result(
                "orchestration",
                0.0,
                10.0,
                ComponentStatus.FAILED,
                f"Failed to orchestrate evaluation: {str(e)}"
            )
            return self.results
        finally:
            # Cleanup
            if self.extracted_path and os.path.exists(self.extracted_path):
                shutil.rmtree(self.extracted_path)
    
    def _extract_zip(self, file_path: str) -> str:
        """Extract ZIP file to temporary directory"""
        temp_dir = tempfile.mkdtemp()
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        logger.info(f"Extracted ZIP to {temp_dir}")
        return temp_dir
    
    def _generate_test_config(self) -> Dict[str, Any]:
        """Generate test configuration based on assignment brief"""
        config = {
            'assignment_type': self.assignment_brief.get('type', 'general') if self.assignment_brief else 'general',
            'tests': [],
            'notebook_tests': [],
            'sql_tests': [],
            'file_requirements': []
        }
        
        if self.assignment_brief:
            # Add tests based on assignment requirements
            requirements = self.assignment_brief.get('requirements', [])
            
            for req in requirements:
                if 'snowflake' in req.lower():
                    config['tests'].extend([
                        {
                            'name': 'snowflake_connection',
                            'type': 'sql',
                            'query': 'SELECT CURRENT_VERSION()',
                            'expected': 'contains_version'
                        },
                        {
                            'name': 'warehouse_creation',
                            'type': 'sql',
                            'pattern': r'CREATE\s+WAREHOUSE',
                            'description': 'Warehouse creation found'
                        },
                        {
                            'name': 'schema_creation',
                            'type': 'sql',
                            'pattern': r'CREATE\s+SCHEMA',
                            'description': 'Schema creation found'
                        }
                    ])
                
                if 'masking' in req.lower():
                    config['tests'].append({
                        'name': 'masking_policy',
                        'type': 'sql',
                        'pattern': r'CREATE\s+MASKING\s+POLICY',
                        'description': 'Masking policy found'
                    })
                
                if 'rls' in req.lower() or 'row access' in req.lower():
                    config['tests'].append({
                        'name': 'row_access_policy',
                        'type': 'sql',
                        'pattern': r'CREATE\s+ROW\s+ACCESS\s+POLICY',
                        'description': 'Row access policy found'
                    })
                
                if 'task' in req.lower():
                    config['tests'].append({
                        'name': 'task_creation',
                        'type': 'sql',
                        'pattern': r'CREATE\s+TASK',
                        'description': 'Task creation found'
                    })
        
        return config
    
    def _evaluate_file_structure(self):
        """Evaluate the structure of submitted files"""
        score = 0.0
        max_score = 15.0
        feedback = []
        
        if not self.extracted_path:
            feedback.append("No files extracted")
        else:
            files = []
            for root, dirs, filenames in os.walk(self.extracted_path):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
            
            if files:
                score += 5.0
                feedback.append(f"Found {len(files)} files")
            
            # Check for specific file types
            file_types = {
                '.ipynb': 'Jupyter notebooks',
                '.sql': 'SQL scripts',
                '.csv': 'CSV data files',
                '.pbix': 'Power BI files',
                '.py': 'Python scripts'
            }
            
            found_types = []
            for ext, desc in file_types.items():
                matching_files = [f for f in files if f.endswith(ext)]
                if matching_files:
                    found_types.append(desc)
                    score += 2.0
                    feedback.append(f"Found {len(matching_files)} {desc}")
            
            # Check for README or documentation
            readme_files = [f for f in files if 'readme' in f.lower() or 'doc' in f.lower()]
            if readme_files:
                score += 2.0
                feedback.append("Contains documentation files")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.6 else ComponentStatus.PARTIAL
        self.add_result("file_structure", score, max_score, status, "; ".join(feedback))
    
    def _evaluate_with_otter_grader(self):
        """Use Otter-Grader to evaluate notebooks"""
        score = 0.0
        max_score = 30.0
        feedback = []
        
        try:
            # Find notebook files
            notebook_files = []
            for root, dirs, filenames in os.walk(self.extracted_path):
                for filename in filenames:
                    if filename.endswith('.ipynb'):
                        notebook_files.append(os.path.join(root, filename))
            
            if not notebook_files:
                feedback.append("No notebook files found")
            else:
                score += 5.0
                feedback.append(f"Found {len(notebook_files)} notebook files")
                
                # Create Otter-Grader test configuration
                test_config_path = self._create_otter_config(notebook_files)
                
                # Run Otter-Grader for each notebook
                for notebook_file in notebook_files:
                    notebook_score = self._run_otter_grader(notebook_file, test_config_path)
                    score += notebook_score
                
                # Cleanup
                if os.path.exists(test_config_path):
                    os.remove(test_config_path)
        
        except Exception as e:
            feedback.append(f"Otter-Grader evaluation failed: {str(e)}")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.5 else ComponentStatus.PARTIAL
        self.add_result("otter_grader", score, max_score, status, "; ".join(feedback))
    
    def _create_otter_config(self, notebook_files: List[str]) -> str:
        """Create Otter-Grader test configuration"""
        config = {
            'notebooks': notebook_files,
            'tests': self.test_config.get('tests', []),
            'grading': {
                'points_possible': 100,
                'show_hidden': False,
                'seed': 42
            }
        }
        
        config_path = os.path.join(self.extracted_path, 'otter_config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_path
    
    def _run_otter_grader(self, notebook_path: str, config_path: str) -> float:
        """Run Otter-Grader on a single notebook"""
        try:
            # Create test cells for the notebook
            test_cells = self._generate_test_cells()
            
            # Run Otter-Grader
            cmd = [
                'otter', 'grade',
                '--path', notebook_path,
                '--config', config_path,
                '--output-dir', os.path.join(self.extracted_path, 'otter_results')
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Parse results
                results_file = os.path.join(self.extracted_path, 'otter_results', 'results.json')
                if os.path.exists(results_file):
                    with open(results_file, 'r') as f:
                        results = json.load(f)
                    return results.get('score', 0.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Otter-Grader failed for {notebook_path}: {str(e)}")
            return 0.0
    
    def _generate_test_cells(self) -> List[Dict[str, Any]]:
        """Generate test cells based on assignment requirements"""
        test_cells = []
        
        if self.assignment_brief:
            requirements = self.assignment_brief.get('requirements', [])
            
            for req in requirements:
                if 'snowflake' in req.lower():
                    test_cells.append({
                        'type': 'code',
                        'source': [
                            'import snowflake.connector\n',
                            'conn = snowflake.connector.connect(\n',
                            '    user=os.getenv("SNOWFLAKE_USER"),\n',
                            '    password=os.getenv("SNOWFLAKE_PASSWORD"),\n',
                            '    account=os.getenv("SNOWFLAKE_ACCOUNT")\n',
                            ')\n',
                            'assert conn is not None, "Snowflake connection failed"'
                        ]
                    })
                
                if 'table' in req.lower():
                    test_cells.append({
                        'type': 'code',
                        'source': [
                            'cursor = conn.cursor()\n',
                            'cursor.execute("SHOW TABLES")\n',
                            'tables = cursor.fetchall()\n',
                            'assert len(tables) > 0, "No tables found"'
                        ]
                    })
        
        return test_cells
    
    def _evaluate_with_pyevalai(self):
        """Use PyEvalAI to evaluate notebooks with AI assistance"""
        score = 0.0
        max_score = 25.0
        feedback = []
        
        try:
            # Find notebook files
            notebook_files = []
            for root, dirs, filenames in os.walk(self.extracted_path):
                for filename in filenames:
                    if filename.endswith('.ipynb'):
                        notebook_files.append(os.path.join(root, filename))
            
            if notebook_files:
                score += 5.0
                feedback.append(f"Evaluating {len(notebook_files)} notebooks with PyEvalAI")
                
                for notebook_file in notebook_files:
                    notebook_score = self._run_pyevalai(notebook_file)
                    score += notebook_score
            else:
                feedback.append("No notebooks found for PyEvalAI evaluation")
        
        except Exception as e:
            feedback.append(f"PyEvalAI evaluation failed: {str(e)}")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.4 else ComponentStatus.PARTIAL
        self.add_result("pyevalai", score, max_score, status, "; ".join(feedback))
    
    def _run_pyevalai(self, notebook_path: str) -> float:
        """Run PyEvalAI on a notebook"""
        try:
            # Create PyEvalAI configuration
            config = {
                'notebook_path': notebook_path,
                'assignment_brief': self.assignment_brief,
                'evaluation_criteria': {
                    'code_quality': 0.3,
                    'correctness': 0.4,
                    'documentation': 0.2,
                    'completeness': 0.1
                }
            }
            
            # Run PyEvalAI (simplified - in real implementation, use actual PyEvalAI API)
            # For now, we'll simulate the evaluation
            score = 0.0
            
            # Check if notebook contains expected elements
            with open(notebook_path, 'r') as f:
                content = f.read()
            
            if 'snowflake' in content.lower():
                score += 5.0
            if 'create' in content.lower() and 'table' in content.lower():
                score += 5.0
            if 'masking' in content.lower():
                score += 5.0
            if 'task' in content.lower():
                score += 5.0
            if 'procedure' in content.lower():
                score += 5.0
            
            return score
            
        except Exception as e:
            logger.error(f"PyEvalAI failed for {notebook_path}: {str(e)}")
            return 0.0
    
    def _evaluate_specific_requirements(self):
        """Evaluate specific assignment requirements"""
        score = 0.0
        max_score = 30.0
        feedback = []
        
        if not self.assignment_brief:
            feedback.append("No assignment brief provided")
        else:
            requirements = self.assignment_brief.get('requirements', [])
            expected_outputs = self.assignment_brief.get('expected_outputs', [])
            
            # Check each requirement
            for req in requirements:
                if self._check_requirement(req):
                    score += 5.0
                    feedback.append(f"Requirement met: {req}")
                else:
                    feedback.append(f"Requirement not met: {req}")
            
            # Check expected outputs
            for output in expected_outputs:
                if self._check_expected_output(output):
                    score += 3.0
                    feedback.append(f"Expected output found: {output}")
                else:
                    feedback.append(f"Expected output not found: {output}")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.6 else ComponentStatus.PARTIAL
        self.add_result("specific_requirements", score, max_score, status, "; ".join(feedback))
    
    def _check_requirement(self, requirement: str) -> bool:
        """Check if a specific requirement is met"""
        if not self.extracted_path:
            return False
        
        # Search through all files for the requirement
        for root, dirs, filenames in os.walk(self.extracted_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for requirement patterns
                    if 'warehouse' in requirement.lower() and 'warehouse' in content.lower():
                        return True
                    if 'schema' in requirement.lower() and 'schema' in content.lower():
                        return True
                    if 'masking' in requirement.lower() and 'masking' in content.lower():
                        return True
                    if 'task' in requirement.lower() and 'task' in content.lower():
                        return True
                    if 'procedure' in requirement.lower() and 'procedure' in content.lower():
                        return True
                    
                except Exception:
                    continue
        
        return False
    
    def _check_expected_output(self, output: str) -> bool:
        """Check if an expected output is present"""
        if not self.extracted_path:
            return False
        
        # Search through all files for the expected output
        for root, dirs, filenames in os.walk(self.extracted_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if output.lower() in content.lower():
                        return True
                    
                except Exception:
                    continue
        
        return False 