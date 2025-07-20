from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AssignmentType(str, Enum):
    SNOWFLAKE = "snowflake"
    PYSPARK = "pyspark"
    POWERBI = "powerbi"
    GENERAL = "general"

class EvaluationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ComponentStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"

class AssignmentBrief(BaseModel):
    title: str
    description: str
    requirements: List[str]
    expected_outputs: List[str]
    scoring_criteria: Dict[str, float]
    file_types: List[str]

class EvaluationResult(BaseModel):
    component_name: str
    score: float
    max_score: float
    status: ComponentStatus
    feedback: str
    details: Optional[Dict[str, Any]] = None

class Evaluation(BaseModel):
    id: Optional[int] = None
    student_id: str
    assignment_type: AssignmentType
    file_path: str
    total_score: float = 0.0
    max_score: float = 100.0
    status: EvaluationStatus = EvaluationStatus.PENDING
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    results: List[EvaluationResult] = []

class EvaluationRequest(BaseModel):
    student_id: str
    assignment_type: AssignmentType
    assignment_brief: Optional[AssignmentBrief] = None

class EvaluationResponse(BaseModel):
    evaluation_id: int
    status: EvaluationStatus
    total_score: float
    max_score: float
    results: List[EvaluationResult]
    feedback: str
    created_at: datetime
    completed_at: Optional[datetime] = None 