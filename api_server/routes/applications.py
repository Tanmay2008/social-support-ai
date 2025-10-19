# 5_api_server/routes/applications.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
import os
import tempfile
import logging

from agent_orchestration.workflow_orchestrator import get_workflow
from data_pipeline.database_manager import DatabaseManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Global components (would be dependency injected in production)
workflow = get_workflow()
db_manager = DatabaseManager()

@router.post("/submit")
async def submit_application(
    background_tasks: BackgroundTasks,
    application_form: UploadFile = File(..., description="Main application form"),
    bank_statement: UploadFile = File(..., description="Bank statement PDF"),
    emirates_id: UploadFile = File(..., description="Emirates ID image/PDF"),
    resume: UploadFile = File(..., description="Resume/CV PDF"),
    assets_file: UploadFile = File(..., description="Assets & liabilities Excel file"),
    credit_report: UploadFile = File(..., description="Credit report PDF"),
    full_name: str = Form(..., description="Applicant full name"),
    email: str = Form(..., description="Applicant email"),
    phone: str = Form(..., description="Applicant phone number"),
    monthly_income: float = Form(..., description="Monthly income in AED"),
    family_size: int = Form(..., description="Number of family members"),
    emergency_contact: Optional[str] = Form(None, description="Emergency contact name"),
    emergency_phone: Optional[str] = Form(None, description="Emergency contact phone")
):
    """Submit a complete social support application"""
    try:
        # Validate file types
        await _validate_uploaded_files([
            application_form, bank_statement, emirates_id, 
            resume, assets_file, credit_report
        ])
        
        # Save uploaded files temporarily
        file_paths = await _save_uploaded_files([
            application_form, bank_statement, emirates_id,
            resume, assets_file, credit_report
        ])
        
        # Prepare application data
        application_data = {
            'application_id': f"APP{int(datetime.now().timestamp())}",
            'personal_info': {
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'emergency_contact': emergency_contact,
                'emergency_phone': emergency_phone
            },
            'financial_info': {
                'monthly_income': monthly_income,
                'family_size': family_size
            },
            'documents': file_paths,
            'submission_timestamp': datetime.now().isoformat()
        }
        
        # Store application in database
        application_id = db_manager.save_application(application_data)
        
        # Process application in background
        background_tasks.add_task(
            _process_application_background, 
            application_id, 
            application_data, 
            file_paths
        )
        
        return {
            "success": True,
            "application_id": application_id,
            "message": "Application submitted successfully. Processing will begin shortly.",
            "estimated_processing_time": "2-3 minutes",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Application submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Application submission failed: {str(e)}")

@router.post("/quick-submit")
async def quick_submit_application(
    application_data: Dict[str, Any]
):
    """Quick submit with pre-processed application data"""
    try:
        # Validate application data
        is_valid, issues = workflow.validate_application_data(application_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid application data: {issues}")
        
        # Generate application ID if not provided
        if 'application_id' not in application_data:
            application_data['application_id'] = f"APP{int(datetime.now().timestamp())}"
        
        # Store in database
        application_id = db_manager.save_application(application_data)
        
        # Process immediately
        result = workflow.process_application(application_data)
        
        # Update database with results
        db_manager.update_application_processing(application_id, {
            'extracted_data': result.get('extraction_summary', {}),
            'validation_results': result.get('validation_results', {}),
            'eligibility_score': result.get('eligibility_score', 0),
            'decision': result.get('decision', {}),
            'status': 'processed' if result['success'] else 'failed'
        })
        
        # Save economic recommendations
        if result.get('economic_recommendations'):
            db_manager.save_economic_recommendations(
                application_id, 
                result['economic_recommendations']
            )
        
        return {
            "success": True,
            "application_id": application_id,
            "processing_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Quick submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick submission failed: {str(e)}")

@router.get("/status/{application_id}")
async def get_application_status(application_id: str):
    """Get application processing status"""
    try:
        application_status = db_manager.get_application_status(application_id)
        
        if 'error' in application_status:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {
            "application_id": application_id,
            "status": application_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/{application_id}/result")
async def get_application_result(application_id: str):
    """Get final application processing result"""
    try:
        application_status = db_manager.get_application_status(application_id)
        
        if 'error' in application_status:
            raise HTTPException(status_code=404, detail="Application not found")
        
        application = application_status['application']
        
        if application.get('status') != 'processed':
            raise HTTPException(
                status_code=422, 
                detail=f"Application not yet processed. Current status: {application.get('status')}"
            )
        
        return {
            "application_id": application_id,
            "eligibility_score": application.get('eligibility_score', 0),
            "decision": application.get('decision', {}),
            "economic_recommendations": application_status.get('recommendations', []),
            "processing_logs": application_status.get('processing_logs', []),
            "validation_results": application.get('validation_results', {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Result retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Result retrieval failed: {str(e)}")

@router.get("/")
async def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of applications to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """List applications with optional filtering"""
    try:
        if status:
            applications = db_manager.get_applications_by_status(status, limit)
        else:
            # For demo, return recent applications
            applications = db_manager.get_applications_by_status('processed', limit)
        
        return {
            "applications": applications,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(applications)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Applications list failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Applications list failed: {str(e)}")

@router.post("/{application_id}/reprocess")
async def reprocess_application(application_id: str):
    """Reprocess an existing application"""
    try:
        application_data = db_manager.get_application(application_id)
        if not application_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Reprocess application
        result = workflow.process_application(
            json.loads(application_data['applicant_data'])
        )
        
        # Update database
        db_manager.update_application_processing(application_id, {
            'extracted_data': result.get('extraction_summary', {}),
            'validation_results': result.get('validation_results', {}),
            'eligibility_score': result.get('eligibility_score', 0),
            'decision': result.get('decision', {}),
            'status': 'reprocessed' if result['success'] else 'failed'
        })
        
        return {
            "success": True,
            "application_id": application_id,
            "reprocessing_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reprocessing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reprocessing failed: {str(e)}")

# Helper functions
async def _validate_uploaded_files(files: List[UploadFile]):
    """Validate uploaded files for type and size"""
    max_size = 10 * 1024 * 1024  # 10MB
    allowed_types = {
        'application_form': ['pdf', 'doc', 'docx'],
        'bank_statement': ['pdf'],
        'emirates_id': ['jpg', 'jpeg', 'png', 'pdf'],
        'resume': ['pdf', 'doc', 'docx'],
        'assets_file': ['xlsx', 'xls', 'csv'],
        'credit_report': ['pdf']
    }
    
    for file in files:
        # Check file size
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File {file.filename} exceeds maximum size of 10MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Check file type
        file_extension = file.filename.split('.')[-1].lower()
        file_type = next(
            (key for key in allowed_types.keys() if key in file.filename.lower()), 
            'unknown'
        )
        
        if file_type != 'unknown' and file_extension not in allowed_types[file_type]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for {file.filename}. Expected: {allowed_types[file_type]}"
            )

async def _save_uploaded_files(files: List[UploadFile]) -> Dict[str, str]:
    """Save uploaded files to temporary location"""
    file_paths = {}
    
    for file in files:
        # Create temporary file
        file_extension = file.filename.split('.')[-1]
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f'.{file_extension}',
            prefix='social_support_'
        )
        
        # Write file content
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Determine file type
        file_type = next(
            (key for key in ['application_form', 'bank_statement', 'emirates_id', 
                           'resume', 'assets_file', 'credit_report'] 
             if key in file.filename.lower()),
            'unknown'
        )
        
        file_paths[file_type] = temp_file.name
    
    return file_paths

async def _process_application_background(application_id: str, application_data: Dict, file_paths: Dict):
    """Process application in background task"""
    try:
        logger.info(f"Background processing started for {application_id}")
        
        # Update status to processing
        db_manager.update_application_processing(application_id, {
            'status': 'processing'
        })
        
        # Log processing start
        db_manager.log_processing_step(
            application_id, 
            'background_processor', 
            'background_processing_started'
        )
        
        # Process through workflow
        result = workflow.process_application(application_data)
        
        # Update database with results
        db_manager.update_application_processing(application_id, {
            'extracted_data': result.get('extraction_summary', {}),
            'validation_results': result.get('validation_results', {}),
            'eligibility_score': result.get('eligibility_score', 0),
            'decision': result.get('decision', {}),
            'status': 'processed' if result['success'] else 'failed'
        })
        
        # Save economic recommendations
        if result.get('economic_recommendations'):
            db_manager.save_economic_recommendations(
                application_id, 
                result['economic_recommendations']
            )
        
        # Clean up temporary files
        for file_path in file_paths.values():
            try:
                os.unlink(file_path)
            except:
                pass  # Ignore cleanup errors
        
        logger.info(f"Background processing completed for {application_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for {application_id}: {str(e)}")
        
        # Update status to failed
        db_manager.update_application_processing(application_id, {
            'status': 'failed',
            'errors': [str(e)]
        })