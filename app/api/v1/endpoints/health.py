#!/usr/bin/env python3
"""
Health check endpoints
"""

import time
from fastapi import APIRouter, Request
from app.config import get_logger, settings

logger = get_logger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    logger.info("Health check requested")
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "services": {
            "api": "running",
            "evaluation_service": "running"
        }
    }
    
    return health_status

@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes."""
    logger.info("Readiness check requested")
    
    return {
        "status": "ready",
        "timestamp": time.time(),
        "version": settings.app_version
    } 