# ai_agents/agent_framework.py
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    application_id: str
    application_data: Dict[str, Any]
    extracted_info: Dict[str, Any]
    validation_results: Dict[str, Any]
    eligibility_score: float
    decision_recommendation: str
    economic_support_recommendations: List[str]
    errors: List[str]
    processing_log: List[str]
    current_step: str
    metadata: Dict[str, Any]

class BaseAgent(ABC):
    """Base class for all AI agents with common functionality"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{name}")
    
    def log_action(self, state: AgentState, action: str, metadata: Dict = None):
        """Log agent actions for observability"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'agent': self.name,
            'action': action,
            'metadata': metadata or {}
        }
        state['processing_log'].append(log_entry)
        self.logger.info(f"{action} - {metadata or ''}")
    
    def handle_error(self, state: AgentState, error: Exception, context: str = ""):
        """Handle errors consistently across all agents"""
        error_msg = f"{self.name} error{': ' + context if context else ''}: {str(error)}"
        state['errors'].append(error_msg)
        self.log_action(state, "error_occurred", {
            'error': str(error),
            'context': context,
            'type': type(error).__name__
        })
        self.logger.error(error_msg)
    
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """Main processing method to be implemented by each agent"""
        pass
    
    def validate_input(self, state: AgentState, required_fields: List[str]) -> bool:
        """Validate that required fields are present in state"""
        for field in required_fields:
            if not state.get(field):
                self.handle_error(
                    state, 
                    ValueError(f"Missing required field: {field}"),
                    "input_validation"
                )
                return False
        return True
    
    def update_metadata(self, state: AgentState, updates: Dict[str, Any]):
        """Update agent-specific metadata in state"""
        if 'agent_metadata' not in state['metadata']:
            state['metadata']['agent_metadata'] = {}
        state['metadata']['agent_metadata'][self.name] = updates

class ReActFramework:
    """Implementation of ReAct (Reasoning + Acting) framework"""
    
    @staticmethod
    def reason(observation: str, context: Dict) -> str:
        """Generate reasoning based on observation and context"""
        # In production, this would use an LLM
        reasoning_templates = {
            'data_extraction': "I need to extract structured information from the {doc_type} document. Looking for key fields like {fields}.",
            'validation': "I need to validate consistency between {documents}. Checking for mismatches in {fields}.",
            'eligibility': "Based on the applicant's {criteria}, I need to calculate an eligibility score considering factors like {factors}."
        }
        
        doc_type = context.get('doc_type', 'unknown')
        if 'extract' in observation.lower():
            return reasoning_templates['data_extraction'].format(
                doc_type=doc_type,
                fields=context.get('fields', 'relevant information')
            )
        elif 'valid' in observation.lower():
            return reasoning_templates['validation'].format(
                documents=context.get('documents', 'submitted documents'),
                fields=context.get('fields', 'key data points')
            )
        
        return f"Reasoning about: {observation}"
    
    @staticmethod
    def act(reasoning: str, available_actions: List[str]) -> str:
        """Choose action based on reasoning"""
        reasoning_lower = reasoning.lower()
        
        if any(word in reasoning_lower for word in ['extract', 'parse', 'read']):
            return 'extract_data'
        elif any(word in reasoning_lower for word in ['valid', 'check', 'verify']):
            return 'validate_data'
        elif any(word in reasoning_lower for word in ['score', 'assess', 'evaluate']):
            return 'calculate_score'
        elif any(word in reasoning_lower for word in ['decide', 'recommend']):
            return 'make_recommendation'
        
        return available_actions[0] if available_actions else 'unknown_action'

class ReflexionFramework:
    """Implementation of Reflexion framework for self-reflection and improvement"""
    
    @staticmethod
    def reflect(previous_action: str, result: Dict, context: Dict) -> Dict:
        """Reflect on previous action and result to improve future actions"""
        reflection = {
            'previous_action': previous_action,
            'success': result.get('success', False),
            'issues_identified': [],
            'improvements_suggested': [],
            'next_action_adjustment': None
        }
        
        # Analyze common issues
        if not result.get('success', False):
            error = result.get('error', '')
            if 'inconsistent' in error.lower():
                reflection['issues_identified'].append('Data inconsistency detected')
                reflection['improvements_suggested'].append('Apply stricter validation rules')
                reflection['next_action_adjustment'] = 'revalidate_with_stricter_rules'
            elif 'missing' in error.lower():
                reflection['issues_identified'].append('Missing required data')
                reflection['improvements_suggested'].append('Request additional information')
                reflection['next_action_adjustment'] = 'request_missing_data'
            elif 'format' in error.lower():
                reflection['issues_identified'].append('Data format issue')
                reflection['improvements_suggested'].append('Improve data parsing logic')
                reflection['next_action_adjustment'] = 'reparse_with_alternative_method'
        
        return reflection

class PlanAndSolveFramework:
    """Implementation of Plan-and-Solve reasoning framework"""
    
    @staticmethod
    def plan(goal: str, constraints: List[str], available_data: Dict) -> Dict:
        """Create a plan to achieve the goal"""
        plan = {
            'goal': goal,
            'constraints': constraints,
            'steps': [],
            'estimated_difficulty': 'medium',
            'risk_factors': []
        }
        
        if 'eligibility' in goal.lower():
            plan['steps'] = [
                'extract_financial_data',
                'validate_income_information', 
                'assess_family_situation',
                'calculate_composite_score',
                'apply_business_rules'
            ]
            plan['risk_factors'] = ['data_quality', 'calculation_complexity']
        
        elif 'decision' in goal.lower():
            plan['steps'] = [
                'review_eligibility_score',
                'check_policy_compliance',
                'assess_risk_factors',
                'generate_recommendation',
                'apply_confidence_threshold'
            ]
            plan['risk_factors'] = ['policy_interpretation', 'edge_cases']
        
        return plan
    
    @staticmethod
    def solve(plan: Dict, state: AgentState) -> Dict:
        """Execute the plan and return results"""
        results = {
            'plan_executed': plan['goal'],
            'steps_completed': [],
            'results': {},
            'issues_encountered': []
        }
        
        for step in plan['steps']:
            try:
                # Simulate step execution
                step_result = f"Executed {step}"
                results['steps_completed'].append(step)
                results['results'][step] = step_result
            except Exception as e:
                results['issues_encountered'].append(f"{step}: {str(e)}")
        
        return results

class AgentRegistry:
    """Registry for managing all agents"""
    
    _instance = None
    _agents = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
        return cls._instance
    
    def register_agent(self, name: str, agent_class: type):
        """Register an agent class"""
        self._agents[name] = agent_class
        logger.info(f"Registered agent: {name}")
    
    def get_agent(self, name: str):
        """Get an agent instance by name"""
        if name not in self._agents:
            raise ValueError(f"Agent not found: {name}")
        return self._agents[name]()
    
    def list_agents(self) -> List[str]:
        """List all registered agents"""
        return list(self._agents.keys())

# Global agent registry
agent_registry = AgentRegistry()