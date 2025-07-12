"""
Evaluation Service

Orchestrates the entire evaluation process including:
- File parsing
- AI model evaluation
- Result aggregation and scoring
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from app.models import (
    EvaluationRequest, 
    EvaluationStatus, 
    NotebookFile,
    CodeCell,
    ScoreBreakdown
)
from app.services.notebook_parser import parser
from app.services.ai_evaluator import evaluator
from app.config import settings

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for orchestrating code evaluations."""
    
    def __init__(self):
        """Initialize the evaluation service."""
        self.active_evaluations: Dict[str, EvaluationRequest] = {}
    
    async def start_evaluation(
        self, 
        file_path: str, 
        filename: str,
        openai_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        use_codebert: bool = True,
        use_openai: bool = False,
        use_gemini: bool = False
    ) -> str:
        """Start a new evaluation process."""
        evaluation_id = str(uuid.uuid4())
        
        # Create evaluation request
        evaluation_request = EvaluationRequest(
            evaluation_id=evaluation_id,
            filename=filename,
            file_size=Path(file_path).stat().st_size,
            status=EvaluationStatus.PENDING
        )
        
        # Store in active evaluations
        self.active_evaluations[evaluation_id] = evaluation_request
        
        # Start background evaluation with API keys and model selection
        asyncio.create_task(self._evaluate_file(
            evaluation_id, file_path, openai_api_key, google_api_key,
            use_codebert, use_openai, use_gemini
        ))
        
        logger.info(f"Started evaluation {evaluation_id} for {filename}")
        return evaluation_id
    
    async def _evaluate_file(
        self, 
        evaluation_id: str, 
        file_path: str, 
        openai_api_key: Optional[str] = None, 
        google_api_key: Optional[str] = None,
        use_codebert: bool = True,
        use_openai: bool = False,
        use_gemini: bool = False
    ):
        """Background evaluation process."""
        evaluation = self.active_evaluations[evaluation_id]
        
        try:
            # Update status to processing
            evaluation.status = EvaluationStatus.PROCESSING
            evaluation.updated_at = datetime.utcnow()
            
            # Parse files
            logger.info(f"Parsing files for evaluation {evaluation_id}")
            
            # Determine file type and parse accordingly
            file_ext = Path(file_path).suffix.lower()
            if file_ext == '.zip':
                notebook_files = parser.parse_zip_file(file_path)
            elif file_ext in ['.ipynb', '.py', '.sql', '.scala', '.r']:
                # Parse single file
                notebook_file = parser.supported_extensions[file_ext](file_path, Path(file_path).name)
                notebook_files = [notebook_file] if notebook_file else []
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            if not notebook_files:
                raise ValueError("No valid files found in upload")
            
            evaluation.total_cells = sum(len(f.cells) for f in notebook_files)
            evaluation.progress = 10.0
            
            # Evaluate each file
            evaluated_files = []
            total_cells = evaluation.total_cells
            processed_cells = 0
            
            for notebook_file in notebook_files:
                logger.info(f"Evaluating file {notebook_file.filename}")
                
                # Evaluate each cell in the file
                evaluated_cells = []
                for cell in notebook_file.cells:
                    try:
                        # Evaluate with AI models using provided API keys and model selection
                        feedback = await evaluator.evaluate_code_cell(
                            cell, 
                            openai_api_key, 
                            google_api_key,
                            use_codebert=use_codebert,
                            use_openai=use_openai,
                            use_gemini=use_gemini
                        )
                        
                        # Calculate scores
                        overall_score, scores = evaluator.calculate_overall_score(feedback)
                        
                        # Update cell with results
                        cell.scores = scores
                        cell.overall_score = overall_score
                        cell.feedback = feedback
                        cell.suggestions = evaluator.aggregate_suggestions(feedback)
                        cell.issues = evaluator.identify_issues(feedback)
                        cell.updated_at = datetime.utcnow()
                        
                        evaluated_cells.append(cell)
                        
                        # Update progress
                        processed_cells += 1
                        evaluation.processed_cells = processed_cells
                        evaluation.progress = 10.0 + (80.0 * processed_cells / total_cells)
                        
                        logger.debug(f"Evaluated cell {cell.cell_id} in {notebook_file.filename}")
                        
                    except Exception as e:
                        logger.error(f"Failed to evaluate cell {cell.cell_id}: {e}")
                        # Continue with other cells
                        evaluated_cells.append(cell)
                
                # Calculate file-level scores
                notebook_file.cells = evaluated_cells
                notebook_file.overall_score = self._calculate_file_score(evaluated_cells)
                notebook_file.score_breakdown = self._calculate_file_breakdown(evaluated_cells)
                notebook_file.updated_at = datetime.utcnow()
                
                evaluated_files.append(notebook_file)
            
            # Calculate project-level scores
            evaluation.files = evaluated_files
            evaluation.project_score = self._calculate_project_score(evaluated_files)
            evaluation.progress = 100.0
            evaluation.status = EvaluationStatus.COMPLETED
            evaluation.completed_at = datetime.utcnow()
            evaluation.updated_at = datetime.utcnow()
            
            logger.info(f"Completed evaluation {evaluation_id}")
            
        except Exception as e:
            logger.error(f"Evaluation {evaluation_id} failed: {e}")
            evaluation.status = EvaluationStatus.FAILED
            evaluation.error_message = str(e)
            evaluation.updated_at = datetime.utcnow()
    
    def _calculate_file_score(self, cells: List[CodeCell]) -> float:
        """Calculate overall score for a file."""
        if not cells:
            return 0.0
        
        scores = [cell.overall_score for cell in cells if cell.overall_score is not None]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_file_breakdown(self, cells: List[CodeCell]) -> ScoreBreakdown:
        """Calculate score breakdown for a file."""
        if not cells:
            return ScoreBreakdown(
                correctness=0.0, efficiency=0.0, readability=0.0,
                scalability=0.0, security=0.0, modularity=0.0,
                documentation=0.0, best_practices=0.0, error_handling=0.0
            )
        
        # Aggregate scores from all cells
        total_scores = {
            'correctness': 0.0, 'efficiency': 0.0, 'readability': 0.0,
            'scalability': 0.0, 'security': 0.0, 'modularity': 0.0,
            'documentation': 0.0, 'best_practices': 0.0, 'error_handling': 0.0
        }
        
        valid_cells = 0
        for cell in cells:
            if cell.scores:
                valid_cells += 1
                for criterion in total_scores:
                    total_scores[criterion] += getattr(cell.scores, criterion)
        
        if valid_cells == 0:
            return ScoreBreakdown(
                correctness=0.0, efficiency=0.0, readability=0.0,
                scalability=0.0, security=0.0, modularity=0.0,
                documentation=0.0, best_practices=0.0, error_handling=0.0
            )
        
        # Calculate averages
        avg_scores = {k: v / valid_cells for k, v in total_scores.items()}
        
        return ScoreBreakdown(**avg_scores)
    
    def _calculate_project_score(self, files: List[NotebookFile]) -> float:
        """Calculate overall project score."""
        if not files:
            return 0.0
        
        scores = [f.overall_score for f in files if f.overall_score is not None]
        return sum(scores) / len(scores) if scores else 0.0
    
    def get_evaluation(self, evaluation_id: str) -> Optional[EvaluationRequest]:
        """Get evaluation by ID."""
        return self.active_evaluations.get(evaluation_id)
    
    def get_evaluation_status(self, evaluation_id: str) -> Optional[Dict]:
        """Get evaluation status and progress."""
        evaluation = self.get_evaluation(evaluation_id)
        if not evaluation:
            return None
        
        return {
            "evaluation_id": evaluation.evaluation_id,
            "status": evaluation.status,
            "progress": evaluation.progress,
            "total_cells": evaluation.total_cells,
            "processed_cells": evaluation.processed_cells,
            "created_at": evaluation.created_at,
            "updated_at": evaluation.updated_at,
            "completed_at": evaluation.completed_at,
            "error_message": evaluation.error_message
        }
    
    def list_evaluations(self) -> List[Dict]:
        """List all evaluations."""
        return [
            {
                "evaluation_id": eval_id,
                "filename": eval_req.filename,
                "status": eval_req.status,
                "progress": eval_req.progress,
                "created_at": eval_req.created_at,
                "completed_at": eval_req.completed_at
            }
            for eval_id, eval_req in self.active_evaluations.items()
        ]
    
    def cleanup_old_evaluations(self, max_age_hours: int = 24):
        """Clean up old evaluations to free memory."""
        cutoff_time = datetime.utcnow().replace(hour=datetime.utcnow().hour - max_age_hours)
        
        to_remove = []
        for eval_id, evaluation in self.active_evaluations.items():
            if evaluation.created_at < cutoff_time:
                to_remove.append(eval_id)
        
        for eval_id in to_remove:
            del self.active_evaluations[eval_id]
            logger.info(f"Cleaned up old evaluation {eval_id}")
    
    def delete_evaluation(self, evaluation_id: str) -> bool:
        """Delete an evaluation by ID."""
        if evaluation_id in self.active_evaluations:
            del self.active_evaluations[evaluation_id]
            logger.info(f"Deleted evaluation {evaluation_id}")
            return True
        return False
    
    def get_statistics(self) -> Dict:
        """Get evaluation statistics."""
        total_evaluations = len(self.active_evaluations)
        completed = sum(1 for e in self.active_evaluations.values() if e.status == EvaluationStatus.COMPLETED)
        failed = sum(1 for e in self.active_evaluations.values() if e.status == EvaluationStatus.FAILED)
        
        # Calculate average score
        scores = [e.project_score for e in self.active_evaluations.values() if e.project_score is not None]
        average_score = sum(scores) / len(scores) if scores else 0.0
        
        # Calculate average processing time
        processing_times = []
        for evaluation in self.active_evaluations.values():
            if evaluation.completed_at and evaluation.created_at:
                processing_time = (evaluation.completed_at - evaluation.created_at).total_seconds()
                processing_times.append(processing_time)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
        
        # Count languages
        languages = {}
        for evaluation in self.active_evaluations.values():
            if evaluation.files:
                for notebook_file in evaluation.files:
                    for cell in notebook_file.cells:
                        lang = cell.language.value
                        languages[lang] = languages.get(lang, 0) + 1
        
        return {
            "total_evaluations": total_evaluations,
            "completed_evaluations": completed,
            "failed_evaluations": failed,
            "average_score": average_score,
            "languages_processed": languages,
            "processing_time_avg": avg_processing_time
        }


# Global evaluation service instance
evaluation_service = EvaluationService() 