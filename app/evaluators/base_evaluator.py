from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas.evaluation import EvaluationResult, ComponentStatus
import logging

logger = logging.getLogger(__name__)

class BaseEvaluator(ABC):
    """Base class for all assignment evaluators"""
    
    def __init__(self, assignment_brief: Optional[Dict[str, Any]] = None):
        self.assignment_brief = assignment_brief
        self.results: List[EvaluationResult] = []
    
    @abstractmethod
    def evaluate(self, file_path: str) -> List[EvaluationResult]:
        """Evaluate the assignment file and return results"""
        pass
    
    def add_result(self, component_name: str, score: float, max_score: float, 
                   status: ComponentStatus, feedback: str, details: Optional[Dict[str, Any]] = None):
        """Add an evaluation result"""
        result = EvaluationResult(
            component_name=component_name,
            score=score,
            max_score=max_score,
            status=status,
            feedback=feedback,
            details=details
        )
        self.results.append(result)
        logger.info(f"Added result for {component_name}: {score}/{max_score} - {status}")
    
    def get_total_score(self) -> float:
        """Calculate total score from all results"""
        return sum(result.score for result in self.results)
    
    def get_max_score(self) -> float:
        """Calculate maximum possible score"""
        return sum(result.max_score for result in self.results)
    
    def get_overall_status(self) -> ComponentStatus:
        """Determine overall status based on individual results"""
        if not self.results:
            return ComponentStatus.FAILED
        
        failed_count = sum(1 for r in self.results if r.status == ComponentStatus.FAILED)
        partial_count = sum(1 for r in self.results if r.status == ComponentStatus.PARTIAL)
        
        if failed_count == len(self.results):
            return ComponentStatus.FAILED
        elif failed_count > 0 or partial_count > 0:
            return ComponentStatus.PARTIAL
        else:
            return ComponentStatus.PASSED 