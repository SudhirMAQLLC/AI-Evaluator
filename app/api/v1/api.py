#!/usr/bin/env python3
"""
API v1 Router
Main router that includes all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1.endpoints import evaluations, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])

# Add evaluate endpoint at root level for dashboard compatibility
from app.api.v1.endpoints.evaluations import upload_and_evaluate
api_router.add_api_route("/evaluate", upload_and_evaluate, methods=["POST"], tags=["evaluations"]) 