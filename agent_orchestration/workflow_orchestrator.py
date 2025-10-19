# agent_orchestration/workflow_orchestrator.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import asyncio
from datetime import datetime
import langfuse
from langfuse.decorators import observe

class SocialSupportWorkflow:
    def __init__(self):
        self.setup_observability()
        self.workflow = StateGraph(AgentState)
        self.setup_workflow()
    
    def setup_observability(self):
        """Initialize Langfuse for AI observability"""
        self.langfuse_handler = langfuse.Langfuse(
            secret_key="sk-lf-...",  # Would be from environment variables
            public_key="pk-lf-...",
            host="http://localhost:3000"
        )
    
    @observe()
    def setup_workflow(self):
        """Set up the complete agent workflow"""
        # Initialize agents
        self.data_extractor = DataExtractionAgent()
        self.data_validator = DataValidationAgent()
        self.eligibility_assessor = EligibilityAssessmentAgent()
        self.decision_recommender = DecisionRecommendationAgent()
        self.economic_advisor = EconomicSupportAgent()
        
        # Add nodes to workflow
        self.workflow.add_node("data_extraction", self.data_extractor.process)
        self.workflow.add_node("data_validation", self.data_validator.process)
        self.workflow.add_node("eligibility_assessment", self.eligibility_assessor.process)
        self.workflow.add_node("decision_recommendation", self.decision_recommender.process)
        self.workflow.add_node("economic_support", self.economic_advisor.process)
        
        # Define workflow edges
        self.workflow.set_entry_point("data_extraction")
        self.workflow.add_edge("data_extraction", "data_validation")
        self.workflow.add_edge("data_validation", "eligibility_assessment")
        self.workflow.add_edge("eligibility_assessment", "decision_recommendation")
        self.workflow.add_edge("decision_recommendation", "economic_support")
        self.workflow.add_edge("economic_support", END)
        
        self.compiled_workflow = self.workflow.compile()
    
    @observe()
    def process_application(self, application_data: Dict) -> Dict:
        """Process a complete application through the AI workflow"""
        start_time = datetime.now()
        
        try:
            # Initialize state
            initial_state = AgentState(
                application_data=application_data,
                extracted_info={},
                validation_results={},
                eligibility_score=0.0,
                decision_recommendation="",
                economic_support_recommendations=[],
                errors=[],
                processing_log=[]
            )
            
            # Execute workflow
            final_state = self.compiled_workflow.invoke(initial_state)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'success': len(final_state['errors']) == 0,
                'processing_time_seconds': processing_time,
                'eligibility_score': final_state['eligibility_score'],
                'decision': final_state['decision_recommendation'],
                'economic_recommendations': final_state['economic_support_recommendations'],
                'validation_results': final_state['validation_results'],
                'errors': final_state['errors'],
                'processing_log': final_state['processing_log'],
                'timestamp': datetime.now().isoformat()
            }
            
            # Log to observability platform
            self.langfuse_handler.trace(
                name="application_processing",
                input=application_data,
                output=result,
                metadata={
                    'processing_time': processing_time,
                    'eligibility_score': final_state['eligibility_score'],
                    'success': len(final_state['errors']) == 0
                }
            )
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'processing_time_seconds': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            self.langfuse_handler.trace(
                name="application_processing_error",
                input=application_data,
                output=error_result,
                metadata={'error': str(e)}
            )
            
            return error_result

# Singleton instance
workflow_orchestrator = SocialSupportWorkflow()