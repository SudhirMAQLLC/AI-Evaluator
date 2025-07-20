import nbformat
from nbclient import NotebookClient
import tempfile
import os
from typing import List, Dict, Any, Optional
import json
import re

from app.evaluators.base_evaluator import BaseEvaluator
from app.schemas.evaluation import EvaluationResult, ComponentStatus

class NotebookEvaluator(BaseEvaluator):
    """Evaluates Jupyter notebooks for code quality, execution, and outputs"""
    
    def __init__(self, assignment_brief: Optional[Dict[str, Any]] = None):
        super().__init__(assignment_brief)
        self.notebook = None
        self.executed_notebook = None
    
    def evaluate(self, file_path: str) -> List[EvaluationResult]:
        """Evaluate a Jupyter notebook file"""
        try:
            # Load notebook
            self.notebook = nbformat.read(file_path, as_version=4)
            
            # Evaluate different aspects
            self._evaluate_structure()
            self._evaluate_code_quality()
            self._evaluate_execution()
            self._evaluate_outputs()
            self._evaluate_documentation()
            
            return self.results
            
        except Exception as e:
            self.add_result(
                "notebook_parsing",
                0.0,
                10.0,
                ComponentStatus.FAILED,
                f"Failed to parse notebook: {str(e)}"
            )
            return self.results
    
    def _evaluate_structure(self):
        """Evaluate notebook structure and organization"""
        score = 0.0
        max_score = 10.0
        feedback = []
        
        # Check if notebook has cells
        if not self.notebook.cells:
            feedback.append("No cells found in notebook")
        else:
            score += 2.0
            feedback.append("Notebook contains cells")
        
        # Check for markdown cells (documentation)
        markdown_cells = [cell for cell in self.notebook.cells if cell.cell_type == 'markdown']
        if markdown_cells:
            score += 3.0
            feedback.append(f"Contains {len(markdown_cells)} markdown cells for documentation")
        else:
            feedback.append("No markdown documentation found")
        
        # Check for code cells
        code_cells = [cell for cell in self.notebook.cells if cell.cell_type == 'code']
        if code_cells:
            score += 3.0
            feedback.append(f"Contains {len(code_cells)} code cells")
        else:
            feedback.append("No code cells found")
        
        # Check for outputs
        cells_with_outputs = [cell for cell in code_cells if cell.outputs]
        if cells_with_outputs:
            score += 2.0
            feedback.append(f"{len(cells_with_outputs)} cells have outputs")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.7 else ComponentStatus.PARTIAL
        self.add_result("notebook_structure", score, max_score, status, "; ".join(feedback))
    
    def _evaluate_code_quality(self):
        """Evaluate code quality in notebook cells"""
        score = 0.0
        max_score = 20.0
        feedback = []
        
        code_cells = [cell for cell in self.notebook.cells if cell.cell_type == 'code']
        
        for i, cell in enumerate(code_cells):
            cell_score = 0.0
            cell_feedback = []
            
            # Check for comments
            if '#' in cell.source:
                cell_score += 1.0
                cell_feedback.append("Contains comments")
            
            # Check for imports
            if 'import' in cell.source or 'from' in cell.source:
                cell_score += 1.0
                cell_feedback.append("Contains imports")
            
            # Check for SQL queries
            if 'SELECT' in cell.source.upper() or 'CREATE' in cell.source.upper():
                cell_score += 2.0
                cell_feedback.append("Contains SQL queries")
            
            # Check for proper variable naming
            if re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*=', cell.source):
                cell_score += 1.0
                cell_feedback.append("Proper variable naming")
            
            score += cell_score
            if cell_feedback:
                feedback.append(f"Cell {i+1}: {'; '.join(cell_feedback)}")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.6 else ComponentStatus.PARTIAL
        self.add_result("code_quality", score, max_score, status, "; ".join(feedback))
    
    def _evaluate_execution(self):
        """Evaluate notebook execution (if possible)"""
        score = 0.0
        max_score = 30.0
        feedback = []
        
        try:
            # Create a temporary notebook for execution
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
                nbformat.write(self.notebook, f.name)
                temp_path = f.name
            
            # Execute notebook
            client = NotebookClient(self.notebook, timeout=60)
            self.executed_notebook = client.execute()
            
            # Check execution results
            executed_cells = [cell for cell in self.executed_notebook.cells 
                            if cell.cell_type == 'code' and cell.execution_count]
            
            if executed_cells:
                score += 15.0
                feedback.append(f"{len(executed_cells)} cells executed successfully")
            
            # Check for errors
            error_cells = [cell for cell in self.executed_notebook.cells 
                          if cell.cell_type == 'code' and 
                          any('error' in str(output).lower() for output in cell.outputs)]
            
            if not error_cells:
                score += 15.0
                feedback.append("No execution errors found")
            else:
                feedback.append(f"{len(error_cells)} cells have execution errors")
            
            # Clean up
            os.unlink(temp_path)
            
        except Exception as e:
            feedback.append(f"Could not execute notebook: {str(e)}")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.5 else ComponentStatus.PARTIAL
        self.add_result("execution", score, max_score, status, "; ".join(feedback))
    
    def _evaluate_outputs(self):
        """Evaluate notebook outputs against expected results"""
        score = 0.0
        max_score = 25.0
        feedback = []
        
        if not self.executed_notebook:
            feedback.append("Notebook not executed, cannot evaluate outputs")
        else:
            # Check for data outputs
            data_outputs = []
            for cell in self.executed_notebook.cells:
                if cell.cell_type == 'code':
                    for output in cell.outputs:
                        if output.output_type == 'execute_result':
                            data_outputs.append(output)
            
            if data_outputs:
                score += 10.0
                feedback.append(f"Found {len(data_outputs)} data outputs")
            
            # Check for visualization outputs
            viz_outputs = []
            for cell in self.executed_notebook.cells:
                if cell.cell_type == 'code':
                    for output in cell.outputs:
                        if output.output_type == 'display_data':
                            viz_outputs.append(output)
            
            if viz_outputs:
                score += 10.0
                feedback.append(f"Found {len(viz_outputs)} visualization outputs")
            
            # Check for specific expected outputs from assignment brief
            if self.assignment_brief and 'expected_outputs' in self.assignment_brief:
                expected_outputs = self.assignment_brief['expected_outputs']
                found_outputs = 0
                
                for expected in expected_outputs:
                    for cell in self.executed_notebook.cells:
                        if expected.lower() in str(cell.outputs).lower():
                            found_outputs += 1
                            break
                
                if found_outputs > 0:
                    score += 5.0
                    feedback.append(f"Found {found_outputs}/{len(expected_outputs)} expected outputs")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.4 else ComponentStatus.PARTIAL
        self.add_result("outputs", score, max_score, status, "; ".join(feedback))
    
    def _evaluate_documentation(self):
        """Evaluate documentation quality"""
        score = 0.0
        max_score = 15.0
        feedback = []
        
        markdown_cells = [cell for cell in self.notebook.cells if cell.cell_type == 'markdown']
        
        if markdown_cells:
            score += 5.0
            feedback.append(f"Contains {len(markdown_cells)} documentation cells")
        
        # Check for title/header
        has_title = any('# ' in cell.source for cell in markdown_cells)
        if has_title:
            score += 3.0
            feedback.append("Contains title/header")
        
        # Check for code comments
        code_cells = [cell for cell in self.notebook.cells if cell.cell_type == 'code']
        commented_cells = [cell for cell in code_cells if '#' in cell.source]
        
        if commented_cells:
            score += 4.0
            feedback.append(f"{len(commented_cells)}/{len(code_cells)} code cells have comments")
        
        # Check for markdown formatting
        formatted_cells = [cell for cell in markdown_cells 
                          if any(marker in cell.source for marker in ['**', '*', '`', '```'])]
        
        if formatted_cells:
            score += 3.0
            feedback.append("Contains formatted markdown")
        
        status = ComponentStatus.PASSED if score >= max_score * 0.6 else ComponentStatus.PARTIAL
        self.add_result("documentation", score, max_score, status, "; ".join(feedback)) 