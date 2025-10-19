# 4_agent_orchestration/langgraph_config.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from typing import Dict, Any, List
import logging
from .workflow_orchestrator import AgentState

logger = logging.getLogger(__name__)

class LangGraphConfig:
    """Configuration for LangGraph workflow management"""
    
    def __init__(self):
        self.workflows = {}
        self.agent_configs = self._load_agent_configs()
    
    def _load_agent_configs(self) -> Dict[str, Any]:
        """Load agent configurations for LangGraph"""
        return {
            "data_extraction": {
                "name": "Data Extraction Agent",
                "description": "Extracts structured data from multi-modal documents",
                "max_retries": 3,
                "timeout": 60
            },
            "data_validation": {
                "name": "Data Validation Agent", 
                "description": "Validates data consistency across documents",
                "max_retries": 2,
                "timeout": 45
            },
            "eligibility_assessment": {
                "name": "Eligibility Assessment Agent",
                "description": "Assesses eligibility using ML models and rules",
                "max_retries": 2,
                "timeout": 30
            },
            "decision_recommendation": {
                "name": "Decision Recommendation Agent",
                "description": "Provides final decision recommendations",
                "max_retries": 1,
                "timeout": 30
            },
            "economic_support": {
                "name": "Economic Support Agent",
                "description": "Recommends economic enablement options",
                "max_retries": 1,
                "timeout": 30
            }
        }
    
    def create_workflow(self, workflow_name: str) -> StateGraph:
        """Create a LangGraph workflow with the specified configuration"""
        workflow = StateGraph(AgentState)
        
        if workflow_name == "social_support_main":
            return self._create_main_workflow(workflow)
        elif workflow_name == "social_support_fast":
            return self._create_fast_workflow(workflow)
        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")
    
    def _create_main_workflow(self, workflow: StateGraph) -> StateGraph:
        """Create the main social support workflow"""
        logger.info("Creating main social support workflow...")
        
        # Add nodes for each agent
        for agent_name, config in self.agent_configs.items():
            workflow.add_node(agent_name, self._create_agent_function(agent_name, config))
        
        # Define workflow edges
        workflow.set_entry_point("data_extraction")
        
        # Normal flow
        workflow.add_edge("data_extraction", "data_validation")
        workflow.add_edge("data_validation", "eligibility_assessment")
        workflow.add_edge("eligibility_assessment", "decision_recommendation")
        workflow.add_edge("decision_recommendation", "economic_support")
        workflow.add_edge("economic_support", END)
        
        # Add conditional edges for error handling
        workflow.add_conditional_edges(
            "data_extraction",
            self._should_continue_after_extraction,
            {
                "continue": "data_validation",
                "retry": "data_extraction",
                "fail": END
            }
        )
        
        workflow.add_conditional_edges(
            "data_validation",
            self._should_continue_after_validation, 
            {
                "continue": "eligibility_assessment",
                "fail": END
            }
        )
        
        logger.info("Main workflow created successfully")
        return workflow
    
    def _create_fast_workflow(self, workflow: StateGraph) -> StateGraph:
        """Create a faster workflow with fewer validation steps"""
        logger.info("Creating fast social support workflow...")
        
        # Only use essential agents
        essential_agents = ["data_extraction", "eligibility_assessment", "decision_recommendation"]
        
        for agent_name in essential_agents:
            config = self.agent_configs[agent_name]
            workflow.add_node(agent_name, self._create_agent_function(agent_name, config))
        
        # Simplified flow
        workflow.set_entry_point("data_extraction")
        workflow.add_edge("data_extraction", "eligibility_assessment")
        workflow.add_edge("eligibility_assessment", "decision_recommendation")
        workflow.add_edge("decision_recommendation", END)
        
        logger.info("Fast workflow created successfully")
        return workflow
    
    def _create_agent_function(self, agent_name: str, config: Dict[str, Any]):
        """Create a LangGraph-compatible agent function"""
        def agent_function(state: AgentState):
            try:
                # Import and execute the actual agent
                agent_module = __import__(
                    f"2_ai_agents.{agent_name}_agent",
                    fromlist=[f"{agent_name.title().replace('_', '')}Agent"]
                )
                agent_class = getattr(
                    agent_module, 
                    f"{agent_name.title().replace('_', '')}Agent"
                )
                
                agent = agent_class()
                return agent.process(state)
                
            except Exception as e:
                logger.error(f"Agent {agent_name} execution failed: {str(e)}")
                state['errors'].append(f"{agent_name} error: {str(e)}")
                return state
        
        return agent_function
    
    def _should_continue_after_extraction(self, state: AgentState) -> str:
        """Determine if workflow should continue after data extraction"""
        errors = state.get('errors', [])
        extracted_info = state.get('extracted_info', {})
        
        extraction_errors = [e for e in errors if 'extraction' in e.lower()]
        
        if len(extraction_errors) > 2:
            return "fail"
        elif not extracted_info or len(extracted_info) < 2:  # Need at least 2 documents
            return "retry"
        else:
            return "continue"
    
    def _should_continue_after_validation(self, state: AgentState) -> str:
        """Determine if workflow should continue after data validation"""
        validation_results = state.get('validation_results', {})
        consistency_score = validation_results.get('overall_consistency_score', 0)
        
        if consistency_score < 0.5:  # Low consistency
            return "fail"
        else:
            return "continue"
    
    def get_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get configuration for a specific workflow"""
        base_config = {
            "max_execution_time": 300,
            "retry_policy": {
                "max_retries": 3,
                "backoff_factor": 1.5
            },
            "error_handling": {
                "continue_on_error": False,
                "fallback_strategy": "partial_processing"
            }
        }
        
        if workflow_name == "social_support_main":
            base_config.update({
                "description": "Full social support application processing",
                "expected_duration": "2-5 minutes",
                "quality_level": "high"
            })
        elif workflow_name == "social_support_fast":
            base_config.update({
                "description": "Fast social support application processing",
                "expected_duration": "1-2 minutes", 
                "quality_level": "medium",
                "retry_policy": {
                    "max_retries": 1,
                    "backoff_factor": 1.0
                }
            })
        
        return base_config

# Global configuration instance
langgraph_config = LangGraphConfig()