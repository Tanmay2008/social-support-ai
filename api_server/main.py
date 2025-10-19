# api_server/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

from .routes import applications, chat, admin
from .middleware import LoggingMiddleware, RateLimitMiddleware
from agent_orchestration.workflow_orchestrator import get_workflow
from data_pipeline.multimodal_processor import MultiModalDataProcessor
from data_pipeline.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Social Support AI Assistant API",
    description="AI-powered workflow automation for social support applications",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=3600)  # 100 calls per hour

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

# Global components
workflow = None
data_processor = None
db_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global workflow, data_processor, db_manager
    
    logger.info("Starting Social Support AI API Server...")
    
    try:
        # Initialize components
        workflow = get_workflow()
        data_processor = MultiModalDataProcessor()
        db_manager = DatabaseManager()
        
        logger.info("All components initialized successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Social Support AI API Server...")

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Social Support AI Assistant API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "applications": "/api/v1/applications",
            "chat": "/api/v1/chat", 
            "admin": "/api/v1/admin",
            "docs": "/api/docs"
        }
    }

@app.get("/api/health")
async def health_check():
    """Comprehensive health check endpoint"""
    components_status = {
        "workflow_orchestrator": workflow is not None,
        "data_processor": data_processor is not None,
        "database": db_manager is not None
    }
    
    all_healthy = all(components_status.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "components": components_status,
        "version": "2.0.0"
    }

@app.get("/api/status")
async def system_status():
    """Detailed system status endpoint"""
    if workflow is None:
        raise HTTPException(status_code=503, detail="System not fully initialized")
    
    workflow_status = workflow.get_workflow_status()
    agent_performance = workflow.get_agent_performance()
    
    return {
        "system": "Social Support AI Assistant",
        "status": "operational",
        "uptime": "0",  # Would be calculated from startup time
        "workflow_status": workflow_status,
        "agent_performance": agent_performance,
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(), 
            "path": request.url.path
        }
    )

# File download endpoints
@app.get("/api/v1/download/{file_type}")
async def download_file(file_type: str, application_id: str):
    """Download generated reports or documents"""
    valid_types = ["report", "decision", "recommendations"]
    
    if file_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # In a real implementation, this would generate and return actual files
    return {
        "message": f"Download {file_type} for {application_id}",
        "file_type": file_type,
        "application_id": application_id,
        "download_url": f"/api/v1/files/{application_id}/{file_type}.pdf"  # Placeholder
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Disable in production
        log_level="info",
        workers=4  # Adjust based on system resources
    )