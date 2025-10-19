# observability/langfuse_config.py
import langfuse
from langfuse.decorators import observe, langfuse_context
from langfuse.model import CreateTrace, CreateGeneration, CreateSpan, CreateEvent
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangfuseManager:
    """Manager for Langfuse observability and monitoring"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LangfuseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.langfuse_client = None
        self.enabled = False
        self._initialize_langfuse()
        self._initialized = True
    
    def _initialize_langfuse(self):
        """Initialize Langfuse client with environment variables"""
        try:
            # Get credentials from environment (would be from secure config in production)
            secret_key = os.getenv('LANGFUSE_SECRET_KEY', 'sk-lf-demo-123')
            public_key = os.getenv('LANGFUSE_PUBLIC_KEY', 'pk-lf-demo-123')
            host = os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
            
            if secret_key and public_key:
                self.langfuse_client = langfuse.Langfuse(
                    secret_key=secret_key,
                    public_key=public_key,
                    host=host
                )
                self.enabled = True
                logger.info("Langfuse observability initialized successfully")
            else:
                logger.warning("Langfuse credentials not found, observability disabled")
                self.enabled = False
                
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {str(e)}")
            self.enabled = False
    
    @observe()
    def track_application_processing(self, application_id: str, application_data: Dict, result: Dict):
        """Track complete application processing workflow"""
        if not self.enabled:
            return
        
        try:
            trace = self.langfuse_client.trace(
                CreateTrace(
                    id=f"application_{application_id}",
                    name="Social Support Application Processing",
                    input=application_data,
                    output=result,
                    metadata={
                        "application_id": application_id,
                        "processing_time": result.get('processing_time_seconds', 0),
                        "eligibility_score": result.get('eligibility_score', 0),
                        "success": result.get('success', False),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            )
            
            logger.info(f"Tracked application processing: {application_id}")
            return trace
            
        except Exception as e:
            logger.error(f"Failed to track application: {str(e)}")
    
    @observe()
    def track_agent_execution(self, trace_id: str, agent_name: str, input_data: Dict, output_data: Dict, metadata: Dict = None):
        """Track individual agent execution"""
        if not self.enabled:
            return
        
        try:
            span = self.langfuse_client.span(
                CreateSpan(
                    trace_id=trace_id,
                    name=f"Agent: {agent_name}",
                    input=input_data,
                    output=output_data,
                    metadata={
                        "agent_name": agent_name,
                        "execution_time": metadata.get('execution_time', 0) if metadata else 0,
                        "success": metadata.get('success', True) if metadata else True,
                        "errors": metadata.get('errors', []) if metadata else [],
                        "timestamp": datetime.now().isoformat()
                    }
                )
            )
            
            return span
            
        except Exception as e:
            logger.error(f"Failed to track agent execution: {str(e)}")
    
    @observe()
    def track_llm_interaction(self, trace_id: str, model: str, prompt: str, response: str, metadata: Dict = None):
        """Track LLM interactions"""
        if not self.enabled:
            return
        
        try:
            generation = self.langfuse_client.generation(
                CreateGeneration(
                    trace_id=trace_id,
                    name="LLM Interaction",
                    model=model,
                    model_parameters=metadata.get('parameters', {}) if metadata else {},
                    input=prompt,
                    output=response,
                    metadata={
                        "model": model,
                        "token_count": metadata.get('token_count', 0) if metadata else 0,
                        "response_time": metadata.get('response_time', 0) if metadata else 0,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            )
            
            return generation
            
        except Exception as e:
            logger.error(f"Failed to track LLM interaction: {str(e)}")
    
    @observe()
    def track_data_processing(self, trace_id: str, process_type: str, input_data: Dict, output_data: Dict, metadata: Dict = None):
        """Track data processing operations"""
        if not self.enabled:
            return
        
        try:
            event = self.langfuse_client.event(
                CreateEvent(
                    trace_id=trace_id,
                    name=f"Data Processing: {process_type}",
                    input=input_data,
                    output=output_data,
                    metadata={
                        "process_type": process_type,
                        "documents_processed": metadata.get('documents_processed', 0) if metadata else 0,
                        "processing_time": metadata.get('processing_time', 0) if metadata else 0,
                        "success_rate": metadata.get('success_rate', 1.0) if metadata else 1.0,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Failed to track data processing: {str(e)}")
    
    @observe()
    def track_validation(self, trace_id: str, validation_type: str, input_data: Dict, results: Dict, metadata: Dict = None):
        """Track validation operations"""
        if not self.enabled:
            return
        
        try:
            span = self.langfuse_client.span(
                CreateSpan(
                    trace_id=trace_id,
                    name=f"Validation: {validation_type}",
                    input=input_data,
                    output=results,
                    metadata={
                        "validation_type": validation_type,
                        "consistency_score": results.get('consistency_score', 0),
                        "issues_found": len(results.get('issues', [])),
                        "overall_score": results.get('overall_score', 0),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            )
            
            return span
            
        except Exception as e:
            logger.error(f"Failed to track validation: {str(e)}")
    
    @observe()
    def track_decision(self, trace_id: str, decision_data: Dict, recommendation: Dict, metadata: Dict = None):
        """Track decision recommendations"""
        if not self.enabled:
            return
        
        try:
            event = self.langfuse_client.event(
                CreateEvent(
                    trace_id=trace_id,
                    name="Decision Recommendation",
                    input=decision_data,
                    output=recommendation,
                    metadata={
                        "decision": recommendation.get('decision', ''),
                        "confidence": recommendation.get('confidence', ''),
                        "eligibility_score": decision_data.get('eligibility_score', 0),
                        "rules_applied": recommendation.get('rules_applied', []),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Failed to track decision: {str(e)}")
    
    def get_trace_analytics(self, trace_id: str) -> Dict:
        """Get analytics for a specific trace"""
        if not self.enabled:
            return {"error": "Langfuse not enabled"}
        
        try:
            # This would query Langfuse API for trace details
            # For prototype, return mock analytics
            return {
                "trace_id": trace_id,
                "total_spans": 5,
                "total_events": 3,
                "total_generations": 2,
                "processing_time": 143.2,
                "agent_performance": {
                    "data_extraction": {"success": True, "duration": 12.3},
                    "data_validation": {"success": True, "duration": 8.7},
                    "eligibility_assessment": {"success": True, "duration": 15.2},
                    "decision_recommendation": {"success": True, "duration": 10.1},
                    "economic_support": {"success": True, "duration": 7.8}
                },
                "llm_usage": {
                    "total_tokens": 1250,
                    "total_calls": 3,
                    "average_response_time": 2.1
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get trace analytics: {str(e)}")
            return {"error": str(e)}
    
    def get_system_metrics(self, time_range: str = "24h") -> Dict:
        """Get system-wide observability metrics"""
        if not self.enabled:
            return {"error": "Langfuse not enabled"}
        
        try:
            # Mock system metrics - in production, this would aggregate from Langfuse
            return {
                "time_range": time_range,
                "total_applications": 1247,
                "success_rate": 0.95,
                "average_processing_time": 143.2,
                "agent_performance": {
                    "data_extraction": {"success_rate": 0.96, "avg_duration": 12.3},
                    "data_validation": {"success_rate": 0.94, "avg_duration": 8.7},
                    "eligibility_assessment": {"success_rate": 0.92, "avg_duration": 15.2},
                    "decision_recommendation": {"success_rate": 0.89, "avg_duration": 10.1},
                    "economic_support": {"success_rate": 0.95, "avg_duration": 7.8}
                },
                "error_breakdown": {
                    "data_quality": 45,
                    "processing_timeout": 12,
                    "validation_failure": 23,
                    "system_error": 8
                },
                "throughput_metrics": {
                    "applications_per_hour": 52,
                    "peak_concurrent_processing": 8,
                    "average_queue_time": 2.3
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            return {"error": str(e)}
    
    def flush(self):
        """Flush all pending observations"""
        if self.enabled and self.langfuse_client:
            try:
                self.langfuse_client.flush()
                logger.info("Langfuse observations flushed")
            except Exception as e:
                logger.error(f"Failed to flush Langfuse: {str(e)}")

# Global observability manager
observability_manager = LangfuseManager()

# Decorator for easy observability integration
def observe_agent(agent_name: str):
    """Decorator to add observability to agent methods"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            try:
                # Extract state from args (assuming first arg is state for agents)
                state = args[0] if args else {}
                application_id = state.get('application_id', 'unknown') if isinstance(state, dict) else 'unknown'
                
                # Create trace if not exists
                trace_id = f"agent_{application_id}_{agent_name}_{int(datetime.now().timestamp())}"
                
                # Track agent execution start
                observability_manager.track_agent_execution(
                    trace_id=trace_id,
                    agent_name=agent_name,
                    input_data={"method": func.__name__, "args": str(args[1:]) if len(args) > 1 else {}},
                    output_data={"status": "started"},
                    metadata={"timestamp": start_time.isoformat()}
                )
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Track successful completion
                execution_time = (datetime.now() - start_time).total_seconds()
                observability_manager.track_agent_execution(
                    trace_id=trace_id,
                    agent_name=agent_name,
                    input_data={"method": func.__name__},
                    output_data={"status": "completed", "result": "success"},
                    metadata={
                        "execution_time": execution_time,
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                return result
                
            except Exception as e:
                # Track error
                execution_time = (datetime.now() - start_time).total_seconds()
                observability_manager.track_agent_execution(
                    trace_id=trace_id,
                    agent_name=agent_name,
                    input_data={"method": func.__name__},
                    output_data={"status": "failed", "error": str(e)},
                    metadata={
                        "execution_time": execution_time,
                        "success": False,
                        "errors": [str(e)],
                        "timestamp": datetime.now().isoformat()
                    }
                )
                raise
        
        return wrapper
    return decorator

# Example usage
if __name__ == "__main__":
    # Test observability
    manager = LangfuseManager()
    
    if manager.enabled:
        # Track a sample application
        sample_application = {
            "application_id": "TEST123",
            "documents": ["form", "bank_statement", "id"],
            "applicant_data": {"name": "John Doe", "income": 2500}
        }
        
        sample_result = {
            "success": True,
            "eligibility_score": 0.78,
            "processing_time_seconds": 143.2,
            "decision": "APPROVE"
        }
        
        trace = manager.track_application_processing("TEST123", sample_application, sample_result)
        print(f"Tracked application: {trace}")
        
        # Flush observations
        manager.flush()
    else:
        print("Observability not enabled")