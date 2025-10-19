# 2_ai_agents/agent_framework.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
from agno.agent import Agent
from agno.models.ollama import Ollama
import json
from datetime import datetime

class AgentState(TypedDict):
    application_data: dict
    extracted_info: dict
    validation_results: dict
    eligibility_score: float
    decision_recommendation: str
    economic_support_recommendations: List[str]
    errors: List[str]
    processing_log: List[str]

class BaseAgent:
    def __init__(self, name: str, model: str = "llama2"):
        self.name = name
        self.model = Ollama(model=model)
        self.agent = Agent(
            name=name,
            model=self.model,
            markdown=True
        )
    
    def log_action(self, state: AgentState, action: str):
        """Log agent actions for observability"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} - {self.name}: {action}"
        state['processing_log'].append(log_entry)

class DataExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__("Data Extraction Agent")
    
    def process(self, state: AgentState) -> AgentState:
        """Extract and structure data from all input sources using ReAct framework"""
        self.log_action(state, "Starting data extraction")
        
        try:
            # Thought: I need to extract data from all submitted documents
            documents = state['application_data'].get('documents', {})
            extracted_data = {}
            
            # Reason: Process each document type with appropriate methods
            for doc_type, doc_path in documents.items():
                if doc_type == 'application_form':
                    extracted_data[doc_type] = self.process_application_form(doc_path)
                elif doc_type == 'bank_statement':
                    extracted_data[doc_type] = self.extract_financial_data(doc_path)
                elif doc_type == 'emirates_id':
                    extracted_data[doc_type] = self.extract_identity_data(doc_path)
                elif doc_type == 'resume':
                    extracted_data[doc_type] = self.extract_employment_data(doc_path)
                elif doc_type == 'assets_file':
                    extracted_data[doc_type] = self.extract_assets_data(doc_path)
                elif doc_type == 'credit_report':
                    extracted_data[doc_type] = self.extract_credit_data(doc_path)
            
            # Action: Store extracted data in state
            state['extracted_info'] = extracted_data
            self.log_action(state, f"Successfully extracted data from {len(documents)} documents")
            
        except Exception as e:
            state['errors'].append(f"Data extraction error: {str(e)}")
            self.log_action(state, f"Data extraction failed: {str(e)}")
        
        return state

class DataValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Data Validation Agent")
    
    def process(self, state: AgentState) -> AgentState:
        """Validate data consistency across documents using Reflexion framework"""
        self.log_action(state, "Starting data validation")
        
        try:
            extracted_data = state['extracted_info']
            validation_results = {}
            
            # Initial validation attempt
            validation_results = self.perform_initial_validation(extracted_data)
            
            # Reflexion: Learn from validation results and improve
            if not validation_results.get('overall_consistent', False):
                validation_results = self.reflect_and_revalidate(extracted_data, validation_results)
            
            state['validation_results'] = validation_results
            self.log_action(state, f"Validation completed with score: {validation_results.get('consistency_score', 0)}")
            
        except Exception as e:
            state['errors'].append(f"Data validation error: {str(e)}")
            self.log_action(state, f"Data validation failed: {str(e)}")
        
        return state
    
    def perform_initial_validation(self, data: Dict) -> Dict:
        """Perform initial data validation"""
        # Implementation for cross-document validation
        return {
            'address_consistency': self.validate_addresses(data),
            'income_consistency': self.validate_income(data),
            'identity_consistency': self.validate_identity(data),
            'overall_consistent': True,  # Simplified for prototype
            'consistency_score': 0.95
        }

class EligibilityAssessmentAgent(BaseAgent):
    def __init__(self):
        super().__init__("Eligibility Assessment Agent")
    
    def process(self, state: AgentState) -> AgentState:
        """Assess eligibility using ML models and rules"""
        self.log_action(state, "Starting eligibility assessment")
        
        try:
            extracted_data = state['extracted_info']
            validation_results = state['validation_results']
            
            # Calculate eligibility score
            eligibility_score = self.calculate_eligibility_score(extracted_data, validation_results)
            
            state['eligibility_score'] = eligibility_score
            self.log_action(state, f"Eligibility score calculated: {eligibility_score}")
            
        except Exception as e:
            state['errors'].append(f"Eligibility assessment error: {str(e)}")
            self.log_action(state, f"Eligibility assessment failed: {str(e)}")
        
        return state
    
    def calculate_eligibility_score(self, data: Dict, validation: Dict) -> float:
        """Calculate comprehensive eligibility score"""
        # Implement scoring logic based on business rules
        score = 0.0
        
        # Income-based scoring (40%)
        income_score = self.assess_income_eligibility(data)
        score += income_score * 0.4
        
        # Family situation scoring (30%)
        family_score = self.assess_family_situation(data)
        score += family_score * 0.3
        
        # Employment status scoring (20%)
        employment_score = self.assess_employment_status(data)
        score += employment_score * 0.2
        
        # Data consistency scoring (10%)
        consistency_score = validation.get('consistency_score', 0)
        score += consistency_score * 0.1
        
        return min(score, 1.0)

class DecisionRecommendationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Decision Recommendation Agent")
    
    def process(self, state: AgentState) -> AgentState:
        """Provide final decision recommendation using PaS (Plan-and-Solve)"""
        self.log_action(state, "Starting decision recommendation")
        
        try:
            eligibility_score = state['eligibility_score']
            extracted_data = state['extracted_info']
            
            # Plan: Determine the decision strategy
            decision_plan = self.plan_decision_strategy(eligibility_score, extracted_data)
            
            # Solve: Execute the plan and generate recommendation
            recommendation = self.execute_decision_plan(decision_plan, extracted_data)
            
            state['decision_recommendation'] = recommendation
            self.log_action(state, f"Decision recommendation: {recommendation}")
            
        except Exception as e:
            state['errors'].append(f"Decision recommendation error: {str(e)}")
            self.log_action(state, f"Decision recommendation failed: {str(e)}")
        
        return state
    
    def plan_decision_strategy(self, score: float, data: Dict) -> Dict:
        """Plan the decision strategy based on eligibility score"""
        if score >= 0.8:
            return {'action': 'approve', 'confidence': 'high', 'type': 'full_support'}
        elif score >= 0.6:
            return {'action': 'approve', 'confidence': 'medium', 'type': 'partial_support'}
        elif score >= 0.4:
            return {'action': 'soft_decline', 'confidence': 'medium', 'type': 'conditional'}
        else:
            return {'action': 'decline', 'confidence': 'high', 'type': 'ineligible'}

class EconomicSupportAgent(BaseAgent):
    def __init__(self):
        super().__init__("Economic Support Agent")
    
    def process(self, state: AgentState) -> AgentState:
        """Recommend economic enablement support options"""
        self.log_action(state, "Starting economic support recommendations")
        
        try:
            extracted_data = state['extracted_info']
            eligibility_score = state['eligibility_score']
            
            recommendations = self.generate_support_recommendations(extracted_data, eligibility_score)
            
            state['economic_support_recommendations'] = recommendations
            self.log_action(state, f"Generated {len(recommendations)} economic support recommendations")
            
        except Exception as e:
            state['errors'].append(f"Economic support recommendation error: {str(e)}")
            self.log_action(state, f"Economic support recommendation failed: {str(e)}")
        
        return state
    
    def generate_support_recommendations(self, data: Dict, score: float) -> List[str]:
        """Generate personalized economic support recommendations"""
        recommendations = []
        
        # Job matching recommendations
        if data.get('employment_status') in ['Unemployed', 'Underemployed']:
            recommendations.extend([
                "Job matching with local employers based on skills",
                "Career counseling sessions",
                "Interview preparation workshops"
            ])
        
        # Training recommendations
        education_level = data.get('education_level', '')
        if education_level in ['Secondary', 'Diploma']:
            recommendations.extend([
                "Vocational training programs",
                "Digital skills certification",
                "Industry-specific skill development"
            ])
        
        # Financial enablement
        if score >= 0.6:
            recommendations.extend([
                "Micro-entrepreneurship support",
                "Small business grants",
                "Financial literacy workshops"
            ])
        
        return recommendations