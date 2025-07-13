#!/usr/bin/env python3
"""
Evaluation endpoints
Handles file upload, evaluation, and results retrieval
"""

import os
import tempfile
import time
from pathlib import Path
from typing import List, Optional
import uuid

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse

from app.config import get_logger, settings
from app.services.evaluation_service import evaluation_service
from app.services.notebook_parser import parser
from app.models import EvaluationResponse

logger = get_logger(__name__)
router = APIRouter()

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_code(
    file: UploadFile = File(...),
    openai_api_key: Optional[str] = Form(None),
    google_api_key: Optional[str] = Form(None),
    grok_api_key: Optional[str] = Form(None),
    use_codebert: bool = Form(True),
    use_sqlcoder: bool = Form(False),
    use_openai: bool = Form(False),
    use_gemini: bool = Form(False),
    use_grok: bool = Form(False)
):
    """Evaluate uploaded code files using selected AI models."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {settings.max_file_size} bytes"
            )
        
        # Save uploaded file
        file_path = f"uploads/{uuid.uuid4()}_{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Start evaluation
        evaluation_id = await evaluation_service.start_evaluation(
            file_path=file_path,
            filename=file.filename,
            openai_api_key=openai_api_key,
            google_api_key=google_api_key,
            grok_api_key=grok_api_key,
            use_codebert=use_codebert,
            use_sqlcoder=use_sqlcoder,
            use_openai=use_openai,
            use_gemini=use_gemini,
            use_grok=use_grok
        )
        
        logger.info(f"Started evaluation {evaluation_id} for {file.filename}")
        
        return EvaluationResponse(
            evaluation_id=evaluation_id,
            filename=file.filename,
            file_size=len(content),
            message="File uploaded and evaluation started successfully",
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"Evaluation request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@router.get("/")
async def list_evaluations():
    """List all evaluations."""
    logger.info("Listing evaluations")
    
    try:
        evaluations = evaluation_service.list_evaluations()
        logger.info(f"Retrieved {len(evaluations)} evaluations")
        return evaluations
    except Exception as e:
        logger.error(f"Failed to list evaluations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list evaluations")

@router.get("/{evaluation_id}/status")
async def get_evaluation_status(evaluation_id: str):
    """Get evaluation status and progress."""
    logger.info(f"Getting status for evaluation: {evaluation_id}")
    
    try:
        status = evaluation_service.get_evaluation_status(evaluation_id)
        if not status:
            logger.warning(f"Evaluation not found: {evaluation_id}")
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        logger.info(f"Evaluation status: {evaluation_id} - {status.get('status', 'unknown')}")
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evaluation status: {evaluation_id} - Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get evaluation status")

@router.get("/{evaluation_id}/results")
async def get_evaluation_results(evaluation_id: str):
    """Get evaluation results."""
    logger.info(f"Getting results for evaluation: {evaluation_id}")
    
    try:
        evaluation = evaluation_service.get_evaluation(evaluation_id)
        if not evaluation:
            logger.warning(f"Evaluation not found: {evaluation_id}")
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        if evaluation.status != "completed":
            logger.warning(f"Evaluation not completed: {evaluation_id} - Status: {evaluation.status}")
            raise HTTPException(
                status_code=400, 
                detail=f"Evaluation not completed. Current status: {evaluation.status}"
            )
        
        logger.info(f"Retrieved results for evaluation: {evaluation_id}")
        return evaluation.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evaluation results: {evaluation_id} - Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get evaluation results")

@router.delete("/{evaluation_id}")
async def delete_evaluation(evaluation_id: str):
    """Delete an evaluation."""
    logger.info(f"Deleting evaluation: {evaluation_id}")
    
    try:
        success = evaluation_service.delete_evaluation(evaluation_id)
        if not success:
            logger.warning(f"Evaluation not found for deletion: {evaluation_id}")
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        logger.info(f"Evaluation deleted successfully: {evaluation_id}")
        return {"message": "Evaluation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete evaluation: {evaluation_id} - Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete evaluation")

@router.post("/cleanup")
async def cleanup_old_evaluations(background_tasks: BackgroundTasks):
    """Clean up old evaluations."""
    logger.info("Starting cleanup of old evaluations")
    
    try:
        background_tasks.add_task(evaluation_service.cleanup_old_evaluations)
        logger.info("Cleanup task started")
        return {"message": "Cleanup task started"}
        
    except Exception as e:
        logger.error(f"Failed to start cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to start cleanup") 