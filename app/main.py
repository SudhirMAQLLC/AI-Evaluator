#!/usr/bin/env python3
"""
AI Code Evaluator - Main FastAPI Application
Production-ready API server with comprehensive logging and error handling
"""

import os
import sys
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import redis.asyncio as redis

from app.config import settings, get_logger, validate_settings
from app.api.v1.api import api_router
from app.services.evaluation_service import EvaluationService

# Setup logging
logger = get_logger(__name__)

# Global Redis connection
redis_client: redis.Redis = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"Max file size: {settings.max_file_size} bytes")
    
    # Validate settings
    try:
        validate_settings()
        logger.info("Settings validation completed successfully")
    except Exception as e:
        logger.error(f"Settings validation failed: {e}")
        sys.exit(1)
    
    # Initialize Redis connection
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Running without Redis.")
        redis_client = None
    
    # Initialize evaluation service
    try:
        # EvaluationService.initialize(redis_client)
        # logger.info("Evaluation service initialized successfully")
        pass  # Placeholder for future initialization
    except Exception as e:
        logger.error(f"Evaluation service initialization failed: {e}")
        sys.exit(1)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Close Redis connection
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")
    
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered code evaluation system with comprehensive analysis",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and their processing time."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - Process time: {process_time:.3f}s")
        
        # Add process time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        logger.error(f"Request failed: {request.method} {request.url.path} - Error: {e} - Process time: {process_time:.3f}s")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    logger.error(f"Request: {request.method} {request.url.path}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    logger.warning(f"Request: {request.method} {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )

@app.get("/")
async def root():
    """Root endpoint with application information."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else None,
        "health_check": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "services": {}
    }
    
    # Check Redis
    if redis_client:
        try:
            await redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        except Exception as e:
            health_status["services"]["redis"] = f"unhealthy: {e}"
            health_status["status"] = "degraded"
    else:
        health_status["services"]["redis"] = "not_configured"
    
    # Check upload directory
    try:
        upload_path = Path(settings.upload_dir)
        if upload_path.exists() and upload_path.is_dir():
            health_status["services"]["upload_dir"] = "healthy"
        else:
            health_status["services"]["upload_dir"] = "unhealthy: directory not found"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["upload_dir"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint for monitoring."""
    evaluation_service = EvaluationService()
    return {
        "evaluations_total": evaluation_service.get_total_evaluations(),
        "evaluations_in_progress": evaluation_service.get_in_progress_count(),
        "uptime": time.time() - getattr(app.state, 'start_time', time.time()),
        "version": settings.app_version
    }

if __name__ == "__main__":
    # Set start time for metrics
    app.state.start_time = time.time()
    
    # Run with uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
        access_log=True,
        reload=settings.debug
    ) 