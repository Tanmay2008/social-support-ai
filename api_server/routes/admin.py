# 5_api_server/routes/admin.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json
import logging

from data_pipeline.database_manager import DatabaseManager
from agent_orchestration.workflow_orchestrator import get_workflow
from ml_models.model_training import ModelTrainer

router = APIRouter()
logger = logging.getLogger(__name__)

# Global components
db_manager = DatabaseManager()
workflow = get_workflow()
model_trainer = ModelTrainer()

# Simple authentication (replace with proper auth in production)
ADMIN_API_KEY = "admin_demo_key_2024"

def verify_admin(api_key: str):
    """Verify admin API key"""
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return True

@router.get("/dashboard")
async def get_admin_dashboard(api_key: str = Depends(verify_admin)):
    """Get comprehensive admin dashboard data"""
    try:
        # Application statistics
        app_stats = db_manager.get_application_stats()
        
        # System performance
        workflow_status = workflow.get_workflow_status()
        agent_performance = workflow.get_agent_performance()
        
        # Model performance
        model_performance = model_trainer.get_model_performance()
        
        # Recent activity
        recent_applications = db_manager.get_applications_by_status('processed', 10)
        
        return {
            "dashboard": {
                "timestamp": datetime.now().isoformat(),
                "application_metrics": app_stats,
                "system_performance": workflow_status,
                "agent_performance": agent_performance,
                "model_performance": model_performance,
                "recent_activity": recent_applications
            }
        }
        
    except Exception as e:
        logger.error(f"Dashboard data retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")

@router.get("/applications/analytics")
async def get_application_analytics(
    api_key: str = Depends(verify_admin),
    days: int = 30
):
    """Get detailed application analytics"""
    try:
        # This would typically query time-series data from the database
        # For prototype, return mock analytics
        
        analytics = {
            "period": f"last_{days}_days",
            "submission_trends": _generate_mock_trends(days),
            "approval_rates": _generate_mock_approval_rates(days),
            "processing_times": _generate_mock_processing_times(),
            "demographic_breakdown": _generate_mock_demographics()
        }
        
        return {
            "analytics": analytics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")

@router.get("/agents/performance")
async def get_agents_performance(api_key: str = Depends(verify_admin)):
    """Get detailed agent performance metrics"""
    try:
        agent_performance = workflow.get_agent_performance()
        
        # Add additional performance metrics
        detailed_performance = {}
        for agent_name, metrics in agent_performance.items():
            detailed_performance[agent_name] = {
                **metrics,
                "health_status": "healthy",  # Would be calculated from error rates
                "resource_usage": {
                    "average_memory_mb": 50,  # Mock data
                    "average_cpu_percent": 15,
                    "peak_usage_timestamp": datetime.now().isoformat()
                },
                "last_incident": None,  # Would track actual incidents
                "recommendations": _generate_agent_recommendations(agent_name)
            }
        
        return {
            "agent_performance": detailed_performance,
            "overall_health": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Agent performance retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent performance retrieval failed: {str(e)}")

@router.post("/models/retrain")
async def retrain_models(
    api_key: str = Depends(verify_admin),
    num_samples: int = 5000
):
    """Retrain ML models with new data"""
    try:
        logger.info(f"Admin requested model retraining with {num_samples} samples")
        
        # Run training pipeline
        training_results = model_trainer.run_training_pipeline(num_samples=num_samples)
        
        return {
            "success": True,
            "training_results": training_results,
            "message": f"Models retrained successfully with {num_samples} samples",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Model retraining failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model retraining failed: {str(e)}")

@router.get("/models/performance")
async def get_models_performance(api_key: str = Depends(verify_admin)):
    """Get detailed model performance metrics"""
    try:
        model_performance = model_trainer.get_model_performance()
        
        # Add additional model metrics
        detailed_performance = {
            **model_performance,
            "drift_monitoring": {
                "data_drift_detected": False,
                "concept_drift_detected": False,
                "last_drift_check": datetime.now().isoformat(),
                "drift_metrics": _generate_mock_drift_metrics()
            },
            "fairness_metrics": {
                "disparate_impact_ratio": 0.95,
                "equal_opportunity_difference": 0.02,
                "average_odds_difference": 0.01,
                "fairness_status": "acceptable"
            },
            "explainability": {
                "feature_importance_available": True,
                "shap_values_computed": True,
                "model_interpretability_score": 0.85
            }
        }
        
        return {
            "model_performance": detailed_performance,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Model performance retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model performance retrieval failed: {str(e)}")

@router.get("/system/health")
async def get_system_health(api_key: str = Depends(verify_admin)):
    """Get comprehensive system health status"""
    try:
        # Check component health
        components_health = {
            "database": _check_database_health(),
            "workflow_orchestrator": _check_workflow_health(),
            "ml_models": _check_models_health(),
            "api_server": _check_api_health(),
            "file_storage": _check_storage_health()
        }
        
        overall_health = "healthy" if all(
            comp["status"] == "healthy" for comp in components_health.values()
        ) else "degraded"
        
        # System metrics
        system_metrics = {
            "active_sessions": len(_get_active_sessions()),
            "memory_usage_percent": 45.2,  # Mock data
            "cpu_usage_percent": 23.1,
            "disk_usage_percent": 67.8,
            "active_connections": 15
        }
        
        return {
            "system_health": {
                "overall_status": overall_health,
                "components": components_health,
                "metrics": system_metrics,
                "last_health_check": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System health check failed: {str(e)}")

@router.post("/system/maintenance")
async def run_system_maintenance(api_key: str = Depends(verify_admin)):
    """Run system maintenance tasks"""
    try:
        maintenance_tasks = {
            "database_cleanup": _run_database_cleanup(),
            "cache_clear": _clear_caches(),
            "log_rotation": _rotate_logs(),
            "temp_files_cleanup": _cleanup_temp_files()
        }
        
        return {
            "success": True,
            "maintenance_tasks": maintenance_tasks,
            "message": "System maintenance completed successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System maintenance failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System maintenance failed: {str(e)}")

@router.get("/audit/logs")
async def get_audit_logs(
    api_key: str = Depends(verify_admin),
    start_date: str = None,
    end_date: str = None,
    level: str = "INFO"
):
    """Get system audit logs"""
    try:
        # In production, this would query actual log storage
        # For prototype, return mock logs
        
        logs = _generate_mock_audit_logs(start_date, end_date, level)
        
        return {
            "audit_logs": logs,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "level": level
            },
            "total_entries": len(logs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Audit logs retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audit logs retrieval failed: {str(e)}")

# Helper functions for mock data generation
def _generate_mock_trends(days: int) -> List[Dict]:
    """Generate mock submission trends"""
    trends = []
    base_date = datetime.now() - timedelta(days=days)
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        submissions = max(10, 50 - i % 7 * 5)  # Mock pattern
        approvals = int(submissions * 0.6)
        
        trends.append({
            "date": date.strftime("%Y-%m-%d"),
            "submissions": submissions,
            "approvals": approvals,
            "approval_rate": approvals / submissions
        })
    
    return trends

def _generate_mock_approval_rates(days: int) -> Dict:
    """Generate mock approval rates by category"""
    return {
        "by_income_level": {
            "low_income": 0.85,
            "medium_income": 0.45,
            "high_income": 0.15
        },
        "by_family_size": {
            "single": 0.35,
            "small_family": 0.55,
            "large_family": 0.75
        },
        "by_employment_status": {
            "unemployed": 0.80,
            "employed": 0.40,
            "student": 0.65
        }
    }

def _generate_mock_processing_times() -> Dict:
    """Generate mock processing time statistics"""
    return {
        "average_processing_time_seconds": 143.2,
        "p95_processing_time_seconds": 287.6,
        "p99_processing_time_seconds": 452.1,
        "fastest_processing_time_seconds": 45.3,
        "slowest_processing_time_seconds": 512.8
    }

def _generate_mock_demographics() -> Dict:
    """Generate mock demographic breakdown"""
    return {
        "age_groups": {
            "18-25": 0.15,
            "26-35": 0.35,
            "36-45": 0.25,
            "46-55": 0.15,
            "56+": 0.10
        },
        "family_sizes": {
            "1": 0.20,
            "2-3": 0.35,
            "4-5": 0.30,
            "6+": 0.15
        },
        "employment_status": {
            "unemployed": 0.45,
            "employed": 0.30,
            "student": 0.15,
            "retired": 0.10
        }
    }

def _generate_agent_recommendations(agent_name: str) -> List[str]:
    """Generate recommendations for agent improvement"""
    recommendations = {
        "data_extraction": [
            "Consider adding support for handwritten documents",
            "Optimize OCR processing for low-quality scans",
            "Add validation for extracted numerical values"
        ],
        "data_validation": [
            "Implement stricter cross-document validation",
            "Add confidence scoring for validation results",
            "Consider external data source verification"
        ],
        "eligibility_assessment": [
            "Retrain model with recent application data",
            "Add explainability for score calculations",
            "Implement bias detection and mitigation"
        ],
        "decision_recommendation": [
            "Add more granular decision categories",
            "Implement confidence-based routing",
            "Add human-in-the-loop for edge cases"
        ],
        "economic_support": [
            "Update training program database",
            "Add personalized recommendation engine",
            "Integrate with job market data"
        ]
    }
    
    return recommendations.get(agent_name, ["No specific recommendations at this time"])

def _generate_mock_drift_metrics() -> Dict:
    """Generate mock data drift metrics"""
    return {
        "feature_drift_scores": {
            "monthly_income": 0.12,
            "family_size": 0.08,
            "employment_status": 0.15,
            "credit_score": 0.05
        },
        "prediction_drift": 0.07,
        "target_drift": 0.03
    }

def _check_database_health() -> Dict:
    """Check database health"""
    return {
        "status": "healthy",
        "response_time_ms": 12.5,
        "connection_pool_usage": 0.35,
        "last_backup": (datetime.now() - timedelta(hours=6)).isoformat()
    }

def _check_workflow_health() -> Dict:
    """Check workflow orchestrator health"""
    return {
        "status": "healthy",
        "active_workflows": 3,
        "average_processing_time": 143.2,
        "error_rate": 0.02
    }

def _check_models_health() -> Dict:
    """Check ML models health"""
    return {
        "status": "healthy",
        "model_accuracy": 0.894,
        "prediction_latency_ms": 45.2,
        "last_training": (datetime.now() - timedelta(days=2)).isoformat()
    }

def _check_api_health() -> Dict:
    """Check API server health"""
    return {
        "status": "healthy",
        "request_rate_per_minute": 12.5,
        "error_rate": 0.015,
        "average_response_time_ms": 89.3
    }

def _check_storage_health() -> Dict:
    """Check file storage health"""
    return {
        "status": "healthy",
        "storage_used_gb": 2.3,
        "storage_available_gb": 97.7,
        "file_count": 1245
    }

def _get_active_sessions() -> List:
    """Get active sessions (mock implementation)"""
    return ["session1", "session2", "session3"]

def _run_database_cleanup() -> Dict:
    """Run database cleanup tasks"""
    return {
        "task": "database_cleanup",
        "status": "completed",
        "cleaned_records": 125,
        "freed_space_mb": 45.2
    }

def _clear_caches() -> Dict:
    """Clear system caches"""
    return {
        "task": "cache_clear",
        "status": "completed",
        "cleared_caches": ["application_cache", "model_cache", "session_cache"]
    }

def _rotate_logs() -> Dict:
    """Rotate system logs"""
    return {
        "task": "log_rotation",
        "status": "completed",
        "rotated_files": 3,
        "archived_size_mb": 12.3
    }

def _cleanup_temp_files() -> Dict:
    """Cleanup temporary files"""
    return {
        "task": "temp_files_cleanup",
        "status": "completed",
        "cleaned_files": 89,
        "freed_space_mb": 156.7
    }

def _generate_mock_audit_logs(start_date: str, end_date: str, level: str) -> List[Dict]:
    """Generate mock audit logs"""
    logs = []
    log_levels = ["INFO", "WARNING", "ERROR"]
    
    if level not in log_levels:
        level = "INFO"
    
    for i in range(50):
        log_level = log_levels[i % 3]
        if log_levels.index(log_level) < log_levels.index(level):
            continue
            
        logs.append({
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "level": log_level,
            "component": f"component_{i % 5}",
            "message": f"Mock audit log message {i}",
            "user_id": f"user_{i % 10}",
            "action": f"action_{i % 8}"
        })
    
    return logs