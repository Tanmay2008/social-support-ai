"""
LangGraph configuration for AI-Powered Social Support Application System.
Defines the workflow orchestration for multi-agent social support processing.
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
import os
from datetime import datetime


class AgentState(TypedDict):
    """State definition for the social support agent workflow."""
    
    # Input data
    application_data: Dict[str, Any]
    user_query: str
    conversation_history: List[Dict[str, str]]
    
    # Processing stages
    extracted_data: Dict[str, Any]
    validation_results: Dict[str, Any]
    eligibility_score: float
    risk_assessment: Dict[str, Any]
    support_recommendations: List[Dict[str, Any]]
    economic_analysis: Dict[str, Any]
    
    # Agent outputs
    data_extraction_output: Dict[str, Any]
    data_validation_output: Dict[str, Any]
    eligibility_output: Dict[str, Any]
    decision_output: Dict[str, Any]
    economic_output: Dict[str, Any]
    
    # Workflow control
    current_stage: str
    needs_human_review: bool
    rejection_reason: Optional[str]
    next_actions: List[str]
    
    # Metadata
    application_id: str
    timestamp: str
    user_id: str


class LangGraphConfig:
    """Configuration class for the Social Support LangGraph workflow."""
    
    def __init__(
        self, 
        llm, 
        tools: List[Any],
        database_url: str = "sqlite:///checkpoints.db",
        max_iterations: int = 10
    ):
        """
        Initialize the LangGraph configuration.
        
        Args:
            llm: The language model to use
            tools: List of available tools for agents
            database_url: Database URL for checkpointing
            max_iterations: Maximum iterations for cyclic workflows
        """
        self.llm = llm
        self.tools = tools
        self.database_url = database_url
        self.max_iterations = max_iterations
        self.graph = None
        self.memory = SqliteSaver.from_conn_string(database_url)
        
    def create_workflow_graph(self) -> StateGraph:
        """
        Create the complete social support workflow graph.
        
        Returns:
            Configured StateGraph instance
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent in the workflow
        workflow.add_node("extract_data", self._extract_data_node)
        workflow.add_node("validate_data", self._validate_data_node)
        workflow.add_node("assess_eligibility", self._assess_eligibility_node)
        workflow.add_node("recommend_decision", self._recommend_decision_node)
        workflow.add_node("analyze_economic_support", self._analyze_economic_support_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("escalate_human", self._escalate_human_node)
        
        # Set entry point
        workflow.set_entry_point("extract_data")
        
        # Define workflow edges with conditional routing
        workflow.add_conditional_edges(
            "extract_data",
            self._route_after_extraction,
            {
                "validate": "validate_data",
                "escalate": "escalate_human"
            }
        )
        
        workflow.add_conditional_edges(
            "validate_data",
            self._route_after_validation,
            {
                "assess_eligibility": "assess_eligibility",
                "escalate": "escalate_human",
                "reject": "generate_response"
            }
        )
        
        workflow.add_conditional_edges(
            "assess_eligibility",
            self._route_after_eligibility,
            {
                "recommend_decision": "recommend_decision",
                "escalate": "escalate_human",
                "reject": "generate_response"
            }
        )
        
        workflow.add_conditional_edges(
            "recommend_decision",
            self._route_after_decision,
            {
                "analyze_economic": "analyze_economic_support",
                "generate_response": "generate_response",
                "escalate": "escalate_human"
            }
        )
        
        workflow.add_conditional_edges(
            "analyze_economic_support",
            self._route_after_economic_analysis,
            {
                "generate_response": "generate_response",
                "escalate": "escalate_human"
            }
        )
        
        # Add edges for terminal nodes
        workflow.add_edge("generate_response", END)
        workflow.add_edge("escalate_human", END)
        
        # Compile the graph with memory
        self.graph = workflow.compile(
            checkpointer=self.memory,
            interrupt_before=["escalate_human"],
            interrupt_after=["generate_response"]
        )
        
        return self.graph
    
    def _extract_data_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for data extraction from application."""
        from ai_agents.data_extraction_agent import DataExtractionAgent
        
        agent = DataExtractionAgent(self.llm, self.tools)
        result = agent.extract_information(state["application_data"])
        
        return {
            "extracted_data": result["extracted_data"],
            "data_extraction_output": result,
            "current_stage": "data_extraction",
            "needs_human_review": result.get("needs_review", False)
        }
    
    def _validate_data_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for data validation and verification."""
        from ai_agents.data_validation_agent import DataValidationAgent
        
        agent = DataValidationAgent(self.llm, self.tools)
        result = agent.validate_information(state["extracted_data"])
        
        return {
            "validation_results": result["validation_results"],
            "data_validation_output": result,
            "current_stage": "data_validation",
            "needs_human_review": result.get("needs_review", False),
            "rejection_reason": result.get("rejection_reason")
        }
    
    def _assess_eligibility_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for eligibility assessment."""
        from ai_agents.eligibility_assessment_agent import EligibilityAssessmentAgent
        from ml_models.eligibility_predictor import EligibilityPredictor
        
        # Use ML model for prediction
        ml_predictor = EligibilityPredictor()
        ml_score = ml_predictor.predict(state["extracted_data"])
        
        # Use agent for comprehensive assessment
        agent = EligibilityAssessmentAgent(self.llm, self.tools)
        agent_result = agent.assess_eligibility(
            state["extracted_data"], 
            state["validation_results"],
            ml_score
        )
        
        return {
            "eligibility_score": agent_result["eligibility_score"],
            "risk_assessment": agent_result["risk_assessment"],
            "eligibility_output": agent_result,
            "current_stage": "eligibility_assessment",
            "needs_human_review": agent_result.get("needs_review", False),
            "rejection_reason": agent_result.get("rejection_reason")
        }
    
    def _recommend_decision_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for decision recommendation."""
        from ai_agents.decision_recommendation_agent import DecisionRecommendationAgent
        
        agent = DecisionRecommendationAgent(self.llm, self.tools)
        result = agent.recommend_decision(
            state["extracted_data"],
            state["eligibility_score"],
            state["risk_assessment"]
        )
        
        return {
            "support_recommendations": result["recommendations"],
            "decision_output": result,
            "current_stage": "decision_recommendation",
            "needs_human_review": result.get("needs_review", False),
            "next_actions": result.get("next_actions", [])
        }
    
    def _analyze_economic_support_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for economic support analysis."""
        from ai_agents.economic_support_agent import EconomicSupportAgent
        
        agent = EconomicSupportAgent(self.llm, self.tools)
        result = agent.analyze_economic_support(
            state["extracted_data"],
            state["support_recommendations"]
        )
        
        return {
            "economic_analysis": result["economic_analysis"],
            "economic_output": result,
            "current_stage": "economic_analysis",
            "needs_human_review": result.get("needs_review", False)
        }
    
    def _generate_response_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for generating final response to user."""
        from ai_agents.agent_framework import ResponseGenerationAgent
        
        agent = ResponseGenerationAgent(self.llm, self.tools)
        response = agent.generate_final_response(state)
        
        return {
            "current_stage": "response_generation",
            "agent_response": response
        }
    
    def _escalate_human_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for escalating to human review."""
        return {
            "current_stage": "human_escalation",
            "needs_human_review": True,
            "agent_response": {
                "message": "Your application has been escalated for human review.",
                "escalation_reason": state.get("rejection_reason", "Complex case requiring human assessment")
            }
        }
    
    # Routing functions
    def _route_after_extraction(self, state: AgentState) -> str:
        """Route after data extraction."""
        if state.get("needs_human_review", False):
            return "escalate"
        return "validate"
    
    def _route_after_validation(self, state: AgentState) -> str:
        """Route after data validation."""
        if state.get("needs_human_review", False):
            return "escalate"
        if state.get("rejection_reason"):
            return "reject"
        return "assess_eligibility"
    
    def _route_after_eligibility(self, state: AgentState) -> str:
        """Route after eligibility assessment."""
        if state.get("needs_human_review", False):
            return "escalate"
        if state.get("rejection_reason"):
            return "reject"
        
        # Only proceed if eligibility score meets threshold
        if state.get("eligibility_score", 0) >= 0.5:
            return "recommend_decision"
        else:
            return "reject"
    
    def _route_after_decision(self, state: AgentState) -> str:
        """Route after decision recommendation."""
        if state.get("needs_human_review", False):
            return "escalate"
        
        # Check if economic analysis is needed
        recommendations = state.get("support_recommendations", [])
        needs_economic_analysis = any(
            rec.get("type") == "economic" for rec in recommendations
        )
        
        if needs_economic_analysis:
            return "analyze_economic"
        else:
            return "generate_response"
    
    def _route_after_economic_analysis(self, state: AgentState) -> str:
        """Route after economic analysis."""
        if state.get("needs_human_review", False):
            return "escalate"
        return "generate_response"
    
    def format_application_input(
        self, 
        application_data: Dict[str, Any],
        user_id: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Format input for the social support workflow.
        
        Args:
            application_data: User application data
            user_id: Unique user identifier
            conversation_history: Previous conversation messages
            
        Returns:
            Formatted input dictionary for the graph
        """
        application_id = f"app_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "application_data": application_data,
            "user_query": "process_application",
            "conversation_history": conversation_history or [],
            "application_id": application_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "current_stage": "initial",
            "needs_human_review": False,
            "extracted_data": {},
            "validation_results": {},
            "eligibility_score": 0.0,
            "risk_assessment": {},
            "support_recommendations": [],
            "economic_analysis": {},
            "data_extraction_output": {},
            "data_validation_output": {},
            "eligibility_output": {},
            "decision_output": {},
            "economic_output": {},
            "rejection_reason": None,
            "next_actions": []
        }
    
    def get_workflow_status(self, application_id: str) -> Dict[str, Any]:
        """
        Get the current status of a workflow instance.
        
        Args:
            application_id: The application ID to check
            
        Returns:
            Current workflow status
        """
        try:
            thread_config = {"configurable": {"thread_id": application_id}}
            state = self.graph.get_state(thread_config)
            return {
                "application_id": application_id,
                "current_stage": state.values.get("current_stage", "unknown"),
                "needs_human_review": state.values.get("needs_human_review", False),
                "eligibility_score": state.values.get("eligibility_score", 0.0),
                "status": "completed" if state.next else "in_progress",
                "last_updated": state.timestamp.isoformat() if state.timestamp else None
            }
        except Exception as e:
            return {
                "application_id": application_id,
                "status": "not_found",
                "error": str(e)
            }


def create_social_support_config(
    llm, 
    tools: List[Any],
    database_url: str = None
) -> LangGraphConfig:
    """
    Factory function to create Social Support LangGraph configuration.
    
    Args:
        llm: Language model instance
        tools: List of available tools
        database_url: Optional custom database URL
        
    Returns:
        Configured LangGraphConfig instance
    """
    if database_url is None:
        database_url = os.getenv("LANGRAPH_DB_URL", "sqlite:///social_support_checkpoints.db")
    
    return LangGraphConfig(llm, tools, database_url)


# Default tools for social support agents
DEFAULT_TOOLS = [
    "document_parser",
    "data_validator", 
    "eligibility_calculator",
    "risk_assessor",
    "benefit_calculator",
    "database_query",
    "external_api_call"
]

# Workflow configuration constants
WORKFLOW_CONFIG = {
    "max_iterations": 10,
    "eligibility_threshold": 0.5,
    "auto_escalation_threshold": 0.8,
    "supported_languages": ["en", "es", "fr"],
    "timeout_seconds": 300
}