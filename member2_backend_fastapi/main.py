"""
NETHRA Backend - FastAPI Main Application
Behavior-Based Continuous Authentication System
"""

import os
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from api.endpoints import router as api_router
from api.auth_endpoints import router as auth_router
from api.trust_endpoints import router as trust_router
from services.ai_interface import AIModelInterface
from services.trust_service import TrustService
from services.behavioral_analyzer import BehavioralAnalyzer
from services.tamper_detection import TamperDetector
from services.mirage_controller import MirageController
from utils.security_utils import SecurityUtils
from utils.privacy_utils import PrivacyUtils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
ai_interface = None
trust_service = None
behavioral_analyzer = None
tamper_detector = None
mirage_controller = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown"""
    global ai_interface, trust_service, behavioral_analyzer, tamper_detector, mirage_controller
    
    logger.info("🚀 Starting NETHRA Backend Services...")
    
    # Initialize AI interface
    ai_interface = AIModelInterface()
    await ai_interface.initialize()
    
    # Initialize core services
    trust_service = TrustService(ai_interface)
    behavioral_analyzer = BehavioralAnalyzer(ai_interface)
    tamper_detector = TamperDetector()
    mirage_controller = MirageController()
    
    # Store services in app state
    app.state.ai_interface = ai_interface
    app.state.trust_service = trust_service
    app.state.behavioral_analyzer = behavioral_analyzer
    app.state.tamper_detector = tamper_detector
    app.state.mirage_controller = mirage_controller
    
    logger.info("✅ All NETHRA services initialized successfully!")
    
    yield
    
    # Cleanup
    logger.info("🔄 Shutting down NETHRA Backend Services...")
    await ai_interface.cleanup()
    logger.info("✅ NETHRA Backend shutdown complete!")

# Create FastAPI app
app = FastAPI(
    title="NETHRA - Behavior-Based Authentication API",
    description="Continuous authentication system for mobile banking security",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependency injection
def get_ai_interface() -> AIModelInterface:
    return app.state.ai_interface

def get_trust_service() -> TrustService:
    return app.state.trust_service

def get_behavioral_analyzer() -> BehavioralAnalyzer:
    return app.state.behavioral_analyzer

def get_tamper_detector() -> TamperDetector:
    return app.state.tamper_detector

def get_mirage_controller() -> MirageController:
    return app.state.mirage_controller

# Request models
class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    timestamp: str
    version: str = "1.0.0"
    services: Dict[str, str]

# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthCheckResponse(
        timestamp=datetime.now().isoformat(),
        services={
            "ai_interface": "healthy",
            "trust_service": "healthy",
            "behavioral_analyzer": "healthy",
            "tamper_detector": "healthy",
            "mirage_controller": "healthy"
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "NETHRA - Where Trust Meets Intelligence!",
        "description": "Behavior-Based Continuous Authentication API",
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "active"
    }

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(trust_router, prefix="/api/v1/trust")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error responses"""
    logger.error(f"Global exception: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

# Custom middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )