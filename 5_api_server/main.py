# 5_api_server/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import json
import os
from typing import List, Optional
import asyncio

from 4_agent_orchestration.workflow_orchestrator import workflow_orchestrator
from 1_data_pipeline.multimodal_processor import MultiModalDataProcessor

app = FastAPI(
    title="Social Support AI Assistant API",
    description="AI-powered workflow automation for social support applications",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
data_processor = MultiModalDataProcessor()

@app.post("/api/v1/submit-application")
async def submit_application(
    application_form: UploadFile = File(...),
    bank_statement: UploadFile = File(...),
    emirates_id: UploadFile = File(...),
    resume: UploadFile = File(...),
    assets_file: UploadFile = File(...),
    credit_report: UploadFile = File(...)
):
    """Main endpoint for submitting complete application"""
    try:
        # Save uploaded files temporarily
        file_paths = await save_uploaded_files([
            application_form, bank_statement, emirates_id,
            resume, assets_file, credit_report
        ])
        
        # Prepare application data
        application_data = {
            'documents': {
                'application_form': file_paths['application_form'],
                'bank_statement': file_paths['bank_statement'],
                'emirates_id': file_paths['emirates_id'],
                'resume': file_paths['resume'],
                'assets_file': file_paths['assets_file'],
                'credit_report': file_paths['credit_report']
            },
            'submission_timestamp': datetime.now().isoformat()
        }
        
        # Process through AI workflow
        result = workflow_orchestrator.process_application(application_data)
        
        # Clean up temporary files
        await cleanup_files(file_paths.values())
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Application processing failed: {str(e)}")

@app.get("/api/v1/application-status/{application_id}")
async def get_application_status(application_id: str):
    """Get status of a submitted application"""
    # Implementation for status checking
    return {"status": "processed", "application_id": application_id}

@app.post("/api/v1/chat")
async def chat_with_agent(
    message: str,
    session_id: Optional[str] = None,
    application_id: Optional[str] = None
):
    """Interactive chat endpoint with AI assistant"""
    try:
        # Process chat message through AI agents
        response = await process_chat_message(message, session_id, application_id)
        
        return JSONResponse(content={
            "response": response,
            "session_id": session_id or generate_session_id(),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

async def save_uploaded_files(files: List[UploadFile]) -> Dict[str, str]:
    """Save uploaded files to temporary location"""
    file_paths = {}
    
    for file in files:
        file_extension = os.path.splitext(file.filename)[1]
        temp_path = f"/tmp/{file.filename}"
        
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_paths[file.filename.split('.')[0]] = temp_path
    
    return file_paths

async def cleanup_files(file_paths: List[str]):
    """Clean up temporary files"""
    for path in file_paths:
        try:
            os.remove(path)
        except:
            pass  # Ignore cleanup errors

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )