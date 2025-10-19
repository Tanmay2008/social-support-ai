# 2_ai_agents/eligibility_assessment_agent.py
from .agent_framework import BaseAgent, AgentState, PlanAndSolveFramework
from typing import Dict, List, Any
import numpy as np
from datetime import datetime

class EligibilityAssessmentAgent(BaseAgent):
    """Agent responsible for assessing eligibility using ML models and business rules"""
    
    def __init__(self):
        super().__init__(
            name="Eligibility Assessment Agent",
            description="Assesses applicant eligibility using machine learning models and business rules"
        )
        self.plan_solve_framework = PlanAndSolveFramework()
    
    def process(self, state: AgentState) -> AgentState:
        """Assess eligibility using Plan-and-Solve framework"""
        self.log_action(state, "starting_eligibility_assessment")
        
        try:
            if not self.validate_input(state, ['extracted_info', 'validation_results']):
                return state
            
            extracted_data = state['extracted_info']
            validation_results = state['validation_results']
            
            # Create assessment plan
            plan = self.plan_solve_framework.plan(
                goal="Assess applicant eligibility for social support",
                constraints=[
                    "Use validated data only",
                    "Apply business rules consistently", 
                    "Consider all relevant factors",
                    "Generate explainable results"
                ],
                available_data=extracted_data
            )
            
            self.log_action(state, "assessment_plan_created", plan)
            
            # Execute the plan
            assessment_results = self.plan_solve_framework.solve(plan, state)
            
            # Calculate eligibility score
            eligibility_score = self._calculate_eligibility_score(extracted_data, validation_results)
            
            # Apply business rules
            final_assessment = self._apply_business_rules(eligibility_score, extracted_data)
            
            state['eligibility_score'] = eligibility_score
            state['metadata']['eligibility_assessment'] = {
                'plan': plan,
                'execution_results': assessment_results,
                'business_rules_applied': final_assessment['rules_applied'],
                'assessment_timestamp': datetime.now().isoformat()
            }
            state['current_step'] = 'eligibility_assessment_completed'
            
            self.log_action(state, "eligibility_assessment_completed", {
                'eligibility_score': eligibility_score,
                'final_decision': final_assessment['preliminary_decision'],
                'confidence': final_assessment['confidence']
            })
            
        except Exception as e:
            self.handle_error(state, e, "eligibility_assessment_process")
        
        return state
    
    def _calculate_eligibility_score(self, extracted_data: Dict, validation_results: Dict) -> float:
        """Calculate comprehensive eligibility score"""
        scores = []
        weights = []
        
        # 1. Income-based scoring (30% weight)
        income_score = self._assess_income_eligibility(extracted_data)
        scores.append(income_score)
        weights.append(0.3)
        
        # 2. Family situation scoring (25% weight)
        family_score = self._assess_family_situation(extracted_data)
        scores.append(family_score)
        weights.append(0.25)
        
        # 3. Employment status scoring (20% weight)
        employment_score = self._assess_employment_status(extracted_data)
        scores.append(employment_score)
        weights.append(0.2)
        
        # 4. Assets and liabilities scoring (15% weight)
        assets_score = self._assess_assets_liabilities(extracted_data)
        scores.append(assets_score)
        weights.append(0.15)
        
        # 5. Data quality scoring (10% weight)
        data_quality_score = self._assess_data_quality(validation_results)
        scores.append(data_quality_score)
        weights.append(0.1)
        
        # Calculate weighted score
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))
        
        # Apply non-linear scaling to emphasize very low/high scores
        final_score = self._apply_non_linear_scaling(weighted_score)
        
        return min(max(final_score, 0.0), 1.0)
    
    def _assess_income_eligibility(self, extracted_data: Dict) -> float:
        """Assess eligibility based on income level"""
        try:
            # Extract income information
            monthly_income = 0
            family_size = 1
            
            if 'application_form' in extracted_data:
                app_data = extracted_data['application_form'].get('data', {})
                financial_info = app_data.get('financial_info', {})
                monthly_income = financial_info.get('monthly_income', 0)
                family_info = app_data.get('family_info', {})
                family_size = max(family_info.get('family_size', 1), 1)
            
            # Calculate income per capita
            income_per_capita = monthly_income / family_size if family_size > 0 else monthly_income
            
            # UAE-specific poverty line consideration (simplified)
            # These thresholds would be based on actual government guidelines
            poverty_line = 2000  # AED per month per person (example)
            comfort_line = 5000  # AED per month per person (example)
            
            if income_per_capita <= poverty_line:
                return 1.0  # Highest eligibility
            elif income_per_capita <= comfort_line:
                # Linear decay between poverty line and comfort line
                return max(0.0, 1.0 - (income_per_capita - poverty_line) / (comfort_line - poverty_line))
            else:
                return 0.1  # Minimal eligibility for high income
            
        except Exception as e:
            self.logger.warning(f"Income assessment error: {str(e)}")
            return 0.5  # Neutral score on error
    
    def _assess_family_situation(self, extracted_data: Dict) -> float:
        """Assess eligibility based on family situation"""
        try:
            family_size = 1
            dependents = 0
            marital_status = "Unknown"
            
            if 'application_form' in extracted_data:
                app_data = extracted_data['application_form'].get('data', {})
                family_info = app_data.get('family_info', {})
                family_size = family_info.get('family_size', 1)
                dependents = family_info.get('dependents', 0)
                marital_status = family_info.get('marital_status', 'Unknown')
            
            score = 0.0
            
            # Family size factor (larger families get higher scores)
            if family_size >= 5:
                score += 0.4
            elif family_size >= 3:
                score += 0.3
            elif family_size >= 2:
                score += 0.2
            else:
                score += 0.1
            
            # Dependents factor
            if dependents >= 3:
                score += 0.4
            elif dependents >= 2:
                score += 0.3
            elif dependents >= 1:
                score += 0.2
            
            # Marital status factor
            if marital_status in ['Single Parent', 'Widowed', 'Divorced']:
                score += 0.2
            elif marital_status == 'Married':
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.warning(f"Family situation assessment error: {str(e)}")
            return 0.5
    
    def _assess_employment_status(self, extracted_data: Dict) -> float:
        """Assess eligibility based on employment status"""
        try:
            employment_status = "Unknown"
            experience_years = 0
            
            if 'application_form' in extracted_data:
                app_data = extracted_data['application_form'].get('data', {})
                financial_info = app_data.get('financial_info', {})
                employment_status = financial_info.get('employment_status', 'Unknown')
            
            if 'resume' in extracted_data:
                resume_data = extracted_data['resume']
                experience_years = resume_data.get('employment_history_years', 0)
            
            score = 0.0
            
            # Employment status scoring
            employment_scores = {
                'Unemployed': 1.0,
                'Student': 0.8,
                'Retired': 0.7,
                'Part-time': 0.6,
                'Self-Employed': 0.5,
                'Employed': 0.3,
                'Unknown': 0.5
            }
            
            score += employment_scores.get(employment_status, 0.5)
            
            # Experience adjustment (more experience might mean better job prospects)
            if experience_years > 10:
                score -= 0.2  # Reduce eligibility for highly experienced
            elif experience_years < 2:
                score += 0.1  # Increase eligibility for inexperienced
            
            return max(0.0, min(score, 1.0))
            
        except Exception as e:
            self.logger.warning(f"Employment assessment error: {str(e)}")
            return 0.5
    
    def _assess_assets_liabilities(self, extracted_data: Dict) -> float:
        """Assess eligibility based on assets and liabilities"""
        try:
            total_assets = 0
            total_liabilities = 0
            net_worth = 0
            
            if 'assets_file' in extracted_data:
                assets_data = extracted_data['assets_file']
                total_assets = assets_data.get('total_assets', 0)
                total_liabilities = assets_data.get('total_liabilities', 0)
                net_worth = assets_data.get('net_worth', 0)
            
            score = 0.0
            
            # Net worth based scoring
            if net_worth <= 0:
                score += 0.8  # Negative or zero net worth
            elif net_worth <= 50000:
                score += 0.6  # Low net worth
            elif net_worth <= 100000:
                score += 0.4  # Moderate net worth
            elif net_worth <= 250000:
                score += 0.2  # Medium net worth
            else:
                score += 0.1  # High net worth
            
            # Debt-to-asset ratio
            if total_assets > 0:
                debt_ratio = total_liabilities / total_assets
                if debt_ratio > 0.8:
                    score += 0.2  # High debt burden
                elif debt_ratio > 0.5:
                    score += 0.1  # Moderate debt burden
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.warning(f"Assets assessment error: {str(e)}")
            return 0.5
    
    def _assess_data_quality(self, validation_results: Dict) -> float:
        """Assess eligibility based on data quality and consistency"""
        try:
            # Use validation results to assess data quality
            overall_score = validation_results.get('overall_consistency_score', 0.5)
            
            # Penalize low data quality but don't reward excessively for high quality
            if overall_score >= 0.8:
                return 1.0
            elif overall_score >= 0.6:
                return 0.8
            elif overall_score >= 0.4:
                return 0.6
            else:
                return 0.3
                
        except Exception as e:
            self.logger.warning(f"Data quality assessment error: {str(e)}")
            return 0.5
    
    def _apply_non_linear_scaling(self, score: float) -> float:
        """Apply non-linear scaling to emphasize extremes"""
        # Use a sigmoid-like function to emphasize very low and very high scores
        if score <= 0.3:
            return score * 1.2  # Boost very low scores
        elif score >= 0.7:
            return 0.7 + (score - 0.7) * 1.3  # Boost very high scores
        else:
            return score
    
    def _apply_business_rules(self, eligibility_score: float, extracted_data: Dict) -> Dict:
        """Apply business rules to finalize eligibility assessment"""
        rules_applied = []
        preliminary_decision = "Further Review Needed"
        confidence = "Medium"
        
        # Rule 1: Minimum score threshold
        if eligibility_score >= 0.8:
            preliminary_decision = "Highly Eligible"
            confidence = "High"
            rules_applied.append("Minimum score threshold met")
        elif eligibility_score >= 0.6:
            preliminary_decision = "Eligible"
            confidence = "Medium"
            rules_applied.append("Moderate eligibility score")
        elif eligibility_score >= 0.4:
            preliminary_decision = "Conditionally Eligible"
            confidence = "Low"
            rules_applied.append("Low eligibility score - conditional approval")
        else:
            preliminary_decision = "Not Eligible"
            confidence = "High"
            rules_applied.append("Below minimum eligibility threshold")
        
        # Rule 2: Check for critical disqualifiers
        critical_issues = self._check_critical_issues(extracted_data)
        if critical_issues:
            preliminary_decision = "Not Eligible - Critical Issues"
            confidence = "High"
            rules_applied.append(f"Critical issues found: {critical_issues}")
        
        # Rule 3: Special circumstances
        special_circumstances = self._check_special_circumstances(extracted_data)
        if special_circumstances and eligibility_score >= 0.3:
            preliminary_decision = "Eligible - Special Circumstances"
            confidence = "Medium"
            rules_applied.append(f"Special circumstances applied: {special_circumstances}")
        
        return {
            'preliminary_decision': preliminary_decision,
            'confidence': confidence,
            'rules_applied': rules_applied,
            'final_score': eligibility_score
        }
    
    def _check_critical_issues(self, extracted_data: Dict) -> List[str]:
        """Check for critical issues that would disqualify applicant"""
        critical_issues = []
        
        # Check for extremely high assets
        if 'assets_file' in extracted_data:
            assets_data = extracted_data['assets_file']
            total_assets = assets_data.get('total_assets', 0)
            if total_assets > 1000000:  # 1 million AED
                critical_issues.append("Extremely high assets")
        
        # Check for fraudulent patterns (simplified)
        if self._detect_fraudulent_patterns(extracted_data):
            critical_issues.append("Potential fraudulent patterns detected")
        
        # Check for incomplete critical documentation
        required_docs = ['application_form', 'emirates_id']
        missing_docs = [doc for doc in required_docs if doc not in extracted_data]
        if missing_docs:
            critical_issues.append(f"Missing critical documents: {missing_docs}")
        
        return critical_issues
    
    def _check_special_circumstances(self, extracted_data: Dict) -> List[str]:
        """Check for special circumstances that might increase eligibility"""
        special_circumstances = []
        
        # Check for large family with single income
        if 'application_form' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            family_info = app_data.get('family_info', {})
            financial_info = app_data.get('financial_info', {})
            
            family_size = family_info.get('family_size', 1)
            employment_status = financial_info.get('employment_status', '')
            
            if family_size >= 5 and employment_status in ['Unemployed', 'Student']:
                special_circumstances.append("Large family with limited income")
        
        # Check for medical conditions (would require additional data)
        # Check for recent job loss (would require employment history)
        
        return special_circumstances
    
    def _detect_fraudulent_patterns(self, extracted_data: Dict) -> bool:
        """Detect potential fraudulent patterns in application data"""
        # Simplified fraud detection - in production, this would be much more sophisticated
        
        inconsistencies_count = 0
        
        # Check for major inconsistencies between documents
        if 'application_form' in extracted_data and 'emirates_id' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            id_data = extracted_data['emirates_id']
            
            app_name = app_data.get('personal_info', {}).get('name', '').lower()
            id_name = id_data.get('full_name', '').lower()
            
            if app_name and id_name and app_name != id_name:
                inconsistencies_count += 1
        
        # Check for unrealistic financial patterns
        if 'application_form' in extracted_data and 'bank_statement' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            bank_data = extracted_data['bank_statement']
            
            app_income = app_data.get('financial_info', {}).get('monthly_income', 0)
            bank_balance = bank_data.get('closing_balance', 0)
            
            # If declared income is very low but bank balance is very high
            if app_income < 1000 and bank_balance > 50000:
                inconsistencies_count += 1
        
        return inconsistencies_count >= 2  # Flag if multiple major inconsistencies

# Register the agent
from .agent_framework import agent_registry
agent_registry.register_agent("eligibility_assessment", EligibilityAssessmentAgent)