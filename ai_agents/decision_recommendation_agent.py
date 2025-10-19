# 2_ai_agents/decision_recommendation_agent.py
from .agent_framework import BaseAgent, AgentState, ReActFramework
from typing import Dict, List, Any
from datetime import datetime

class DecisionRecommendationAgent(BaseAgent):
    """Agent responsible for providing final decision recommendations"""
    
    def __init__(self):
        super().__init__(
            name="Decision Recommendation Agent",
            description="Provides final decision recommendations based on eligibility assessment and business rules"
        )
        self.react_framework = ReActFramework()
    
    def process(self, state: AgentState) -> AgentState:
        """Provide final decision recommendation using ReAct framework"""
        self.log_action(state, "starting_decision_recommendation")
        
        try:
            if not self.validate_input(state, ['eligibility_score', 'extracted_info', 'validation_results']):
                return state
            
            eligibility_score = state['eligibility_score']
            extracted_data = state['extracted_info']
            validation_results = state['validation_results']
            
            # Use ReAct framework for decision reasoning
            observation = f"Eligibility score: {eligibility_score:.2f}. Need to make final decision recommendation."
            context = {
                'eligibility_score': eligibility_score,
                'data_quality': validation_results.get('overall_consistency_score', 0.5),
                'documents_processed': len(extracted_data)
            }
            
            reasoning = self.react_framework.reason(observation, context)
            action = self.react_framework.act(reasoning, ['generate_recommendation'])
            
            self.log_action(state, "decision_reasoning", {
                'observation': observation,
                'reasoning': reasoning,
                'action': action
            })
            
            # Generate recommendation
            if action == 'generate_recommendation':
                recommendation = self._generate_decision_recommendation(
                    eligibility_score, extracted_data, validation_results
                )
            else:
                recommendation = self._fallback_recommendation(eligibility_score)
            
            state['decision_recommendation'] = recommendation
            state['current_step'] = 'decision_recommendation_completed'
            
            self.log_action(state, "decision_recommendation_completed", {
                'recommendation': recommendation,
                'eligibility_score': eligibility_score
            })
            
        except Exception as e:
            self.handle_error(state, e, "decision_recommendation_process")
        
        return state
    
    def _generate_decision_recommendation(self, eligibility_score: float, 
                                        extracted_data: Dict, 
                                        validation_results: Dict) -> str:
        """Generate comprehensive decision recommendation"""
        
        # Base recommendation based on score
        if eligibility_score >= 0.8:
            base_recommendation = "APPROVE - Full Support"
            support_level = "Full"
            confidence = "High"
        elif eligibility_score >= 0.6:
            base_recommendation = "APPROVE - Partial Support"
            support_level = "Partial"
            confidence = "Medium"
        elif eligibility_score >= 0.4:
            base_recommendation = "SOFT DECLINE - Conditional Approval Possible"
            support_level = "Conditional"
            confidence = "Low"
        else:
            base_recommendation = "DECLINE - Not Eligible"
            support_level = "None"
            confidence = "High"
        
        # Adjust based on data quality
        data_quality = validation_results.get('overall_consistency_score', 0.5)
        if data_quality < 0.6:
            if "APPROVE" in base_recommendation:
                base_recommendation += " (Pending Data Verification)"
                confidence = "Medium"
            elif "SOFT DECLINE" in base_recommendation:
                base_recommendation = "PENDING - Additional Documentation Required"
        
        # Add specific justifications
        justifications = self._generate_justifications(eligibility_score, extracted_data, validation_results)
        
        # Compile final recommendation
        recommendation = {
            'decision': base_recommendation,
            'support_level': support_level,
            'confidence': confidence,
            'eligibility_score': round(eligibility_score, 3),
            'justifications': justifications,
            'recommendation_timestamp': datetime.now().isoformat(),
            'next_steps': self._generate_next_steps(base_recommendation, extracted_data)
        }
        
        return recommendation
    
    def _generate_justifications(self, eligibility_score: float, 
                               extracted_data: Dict, 
                               validation_results: Dict) -> List[str]:
        """Generate specific justifications for the decision"""
        justifications = []
        
        # Score-based justifications
        if eligibility_score >= 0.8:
            justifications.append("High eligibility score indicates strong need for support")
        elif eligibility_score >= 0.6:
            justifications.append("Moderate eligibility score suggests appropriate support level")
        elif eligibility_score >= 0.4:
            justifications.append("Borderline eligibility score requires careful consideration")
        else:
            justifications.append("Low eligibility score does not meet support criteria")
        
        # Financial justifications
        financial_justification = self._get_financial_justification(extracted_data)
        if financial_justification:
            justifications.append(financial_justification)
        
        # Family situation justifications
        family_justification = self._get_family_justification(extracted_data)
        if family_justification:
            justifications.append(family_justification)
        
        # Employment justifications
        employment_justification = self._get_employment_justification(extracted_data)
        if employment_justification:
            justifications.append(employment_justification)
        
        # Data quality justifications
        data_quality = validation_results.get('overall_consistency_score', 0.5)
        if data_quality < 0.7:
            justifications.append("Data quality concerns noted in validation")
        elif data_quality >= 0.9:
            justifications.append("High data quality supports confident decision")
        
        return justifications
    
    def _get_financial_justification(self, extracted_data: Dict) -> str:
        """Generate financial-based justification"""
        try:
            monthly_income = 0
            family_size = 1
            
            if 'application_form' in extracted_data:
                app_data = extracted_data['application_form'].get('data', {})
                financial_info = app_data.get('financial_info', {})
                family_info = app_data.get('family_info', {})
                monthly_income = financial_info.get('monthly_income', 0)
                family_size = max(family_info.get('family_size', 1), 1)
            
            income_per_capita = monthly_income / family_size
            
            if income_per_capita < 2000:
                return f"Low income per capita (AED {income_per_capita:.0f}) indicates financial need"
            elif income_per_capita < 4000:
                return f"Moderate income per capita (AED {income_per_capita:.0f}) suggests limited financial capacity"
            else:
                return f"Adequate income per capita (AED {income_per_capita:.0f}) reduces support urgency"
                
        except:
            return "Financial assessment completed with available data"
    
    def _get_family_justification(self, extracted_data: Dict) -> str:
        """Generate family situation-based justification"""
        try:
            family_size = 1
            dependents = 0
            
            if 'application_form' in extracted_data:
                app_data = extracted_data['application_form'].get('data', {})
                family_info = app_data.get('family_info', {})
                family_size = family_info.get('family_size', 1)
                dependents = family_info.get('dependents', 0)
            
            if family_size >= 5:
                return f"Large family size ({family_size} members) increases support need"
            elif dependents >= 3:
                return f"Multiple dependents ({dependents}) indicates higher household expenses"
            elif family_size <= 2:
                return "Small household size reduces support urgency"
            else:
                return "Standard family situation assessed"
                
        except:
            return "Family situation evaluated based on provided information"
    
    def _get_employment_justification(self, extracted_data: Dict) -> str:
        """Generate employment-based justification"""
        try:
            employment_status = "Unknown"
            
            if 'application_form' in extracted_data:
                app_data = extracted_data['application_form'].get('data', {})
                financial_info = app_data.get('financial_info', {})
                employment_status = financial_info.get('employment_status', 'Unknown')
            
            if employment_status == 'Unemployed':
                return "Unemployment status significantly increases support need"
            elif employment_status == 'Student':
                return "Student status suggests limited earning capacity"
            elif employment_status == 'Retired':
                return "Retirement may indicate fixed income situation"
            elif employment_status == 'Employed':
                return "Employment provides some financial stability"
            else:
                return "Employment situation considered in assessment"
                
        except:
            return "Employment status factored into decision"
    
    def _generate_next_steps(self, recommendation: str, extracted_data: Dict) -> List[str]:
        """Generate next steps based on the recommendation"""
        next_steps = []
        
        if "APPROVE" in recommendation:
            next_steps.extend([
                "Proceed with support package allocation",
                "Schedule orientation session",
                "Assign case manager for ongoing support"
            ])
        elif "SOFT DECLINE" in recommendation or "PENDING" in recommendation:
            next_steps.extend([
                "Request additional documentation",
                "Schedule follow-up interview",
                "Review with senior case officer"
            ])
        elif "DECLINE" in recommendation:
            next_steps.extend([
                "Prepare decline notification",
                "Document decision rationale",
                "Provide information on appeal process"
            ])
        
        # Add document-specific next steps
        if 'assets_file' not in extracted_data and "APPROVE" in recommendation:
            next_steps.append("Request assets declaration for complete assessment")
        
        if 'credit_report' not in extracted_data:
            next_steps.append("Consider credit report for future assessments")
        
        return next_steps
    
    def _fallback_recommendation(self, eligibility_score: float) -> str:
        """Generate fallback recommendation when primary method fails"""
        if eligibility_score > 0.5:
            return {
                'decision': 'PENDING - Manual Review Required',
                'support_level': 'Unknown',
                'confidence': 'Low',
                'eligibility_score': eligibility_score,
                'justifications': ['System encountered processing issue', 'Manual review recommended'],
                'recommendation_timestamp': datetime.now().isoformat(),
                'next_steps': ['Escalate to human case officer', 'Review all submitted documents']
            }
        else:
            return {
                'decision': 'PENDING - Additional Assessment Needed',
                'support_level': 'Unknown', 
                'confidence': 'Low',
                'eligibility_score': eligibility_score,
                'justifications': ['Incomplete assessment', 'Further verification required'],
                'recommendation_timestamp': datetime.now().isoformat(),
                'next_steps': ['Request additional information', 'Schedule applicant interview']
            }

# Register the agent
from .agent_framework import agent_registry
agent_registry.register_agent("decision_recommendation", DecisionRecommendationAgent)