"""
Data models for the AI Code Evaluator application.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class LanguageType(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    SQL = "sql"
    PYSPARK = "pyspark"
    UNKNOWN = "unknown"


class EvaluationStatus(str, Enum):
    """Evaluation status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScoreBreakdown(BaseModel):
    """Individual score breakdown for each criterion."""
    correctness: float = Field(..., ge=0, le=10, description="Code logic and syntax accuracy")
    efficiency: float = Field(..., ge=0, le=10, description="Performance and resource usage")
    readability: float = Field(..., ge=0, le=10, description="Code clarity and structure")
    scalability: float = Field(..., ge=0, le=10, description="Ability to handle larger datasets")
    security: float = Field(..., ge=0, le=10, description="Vulnerability assessment")
    modularity: float = Field(..., ge=0, le=10, description="Code organization and reusability")
    documentation: float = Field(..., ge=0, le=10, description="Comments and documentation quality")
    best_practices: float = Field(..., ge=0, le=10, description="Industry standards compliance")
    error_handling: float = Field(..., ge=0, le=10, description="Robustness and error management")


class ModelFeedback(BaseModel):
    """Feedback from a specific AI model."""
    model_name: str
    feedback: str
    suggestions: List[str]
    confidence: float = Field(..., ge=0, le=1)
    scores: Optional[ScoreBreakdown] = None
    
    class Config:
        protected_namespaces = ()


class CodeCell(BaseModel):
    """Individual code cell from a notebook."""
    cell_id: str
    language: LanguageType
    code: str
    line_count: int
    execution_count: Optional[int] = None
    
    # Evaluation results
    scores: Optional[ScoreBreakdown] = None
    overall_score: Optional[float] = None
    feedback: Optional[Dict[str, ModelFeedback]] = None
    suggestions: Optional[List[str]] = None
    issues: Optional[List[str]] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotebookFile(BaseModel):
    """Jupyter notebook file with evaluation results."""
    filename: str
    file_size: int
    cell_count: int
    cells: List[CodeCell]
    
    # Aggregated scores
    overall_score: Optional[float] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluationRequest(BaseModel):
    """Request for code evaluation."""
    evaluation_id: str
    filename: str
    file_size: int
    status: EvaluationStatus = EvaluationStatus.PENDING
    progress: float = Field(default=0.0, ge=0, le=100)
    
    # Results
    files: Optional[List[NotebookFile]] = None
    project_score: Optional[float] = None
    total_cells: int = 0
    processed_cells: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class EvaluationResponse(BaseModel):
    """Response for evaluation request."""
    evaluation_id: str
    status: EvaluationStatus
    message: str
    progress: float = 0.0
    estimated_completion: Optional[datetime] = None


class ReportRequest(BaseModel):
    """Request for report generation."""
    evaluation_id: str
    format: str = Field(default="json", pattern="^(json|pdf|html)$")
    include_details: bool = True
    include_suggestions: bool = True


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UploadResponse(BaseModel):
    """Response for file upload."""
    evaluation_id: str
    filename: str
    file_size: int
    message: str
    status: EvaluationStatus


class StatsResponse(BaseModel):
    """Statistics response."""
    total_evaluations: int
    completed_evaluations: int
    failed_evaluations: int
    average_score: float
    languages_processed: Dict[str, int]
    processing_time_avg: float 