# 2_ai_agents/economic_support_agent.py
from .agent_framework import BaseAgent, AgentState, PlanAndSolveFramework
from typing import Dict, List, Any
from datetime import datetime

class EconomicSupportAgent(BaseAgent):
    """Agent responsible for recommending economic enablement support options"""
    
    def __init__(self):
        super().__init__(
            name="Economic Support Agent",
            description="Recommends economic enablement support including training, job matching, and career counseling"
        )
        self.plan_solve_framework = PlanAndSolveFramework()
    
    def process(self, state: AgentState) -> AgentState:
        """Generate economic support recommendations using Plan-and-Solve framework"""
        self.log_action(state, "starting_economic_support_recommendations")
        
        try:
            if not self.validate_input(state, ['extracted_info', 'eligibility_score', 'decision_recommendation']):
                return state
            
            extracted_data = state['extracted_info']
            eligibility_score = state['eligibility_score']
            decision = state['decision_recommendation']
            
            # Create plan for economic support recommendations
            plan = self.plan_solve_framework.plan(
                goal="Generate personalized economic enablement recommendations",
                constraints=[
                    "Consider applicant's skills and background",
                    "Align with local job market opportunities",
                    "Focus on practical, achievable outcomes",
                    "Provide multiple support options"
                ],
                available_data=extracted_data
            )
            
            self.log_action(state, "economic_support_plan_created", plan)
            
            # Generate recommendations
            recommendations = self._generate_economic_recommendations(
                extracted_data, eligibility_score, decision
            )
            
            state['economic_support_recommendations'] = recommendations
            state['current_step'] = 'economic_support_completed'
            
            self.log_action(state, "economic_support_recommendations_completed", {
                'recommendations_generated': len(recommendations),
                'primary_categories': list(set([rec['category'] for rec in recommendations]))
            })
            
        except Exception as e:
            self.handle_error(state, e, "economic_support_recommendation_process")
        
        return state
    
    def _generate_economic_recommendations(self, extracted_data: Dict, 
                                         eligibility_score: float, 
                                         decision: Dict) -> List[Dict]:
        """Generate personalized economic support recommendations"""
        recommendations = []
        
        # 1. Employment-related recommendations
        employment_recs = self._generate_employment_recommendations(extracted_data)
        recommendations.extend(employment_recs)
        
        # 2. Training and education recommendations
        training_recs = self._generate_training_recommendations(extracted_data)
        recommendations.extend(training_recs)
        
        # 3. Financial enablement recommendations
        financial_recs = self._generate_financial_recommendations(extracted_data, eligibility_score)
        recommendations.extend(financial_recs)
        
        # 4. Social support recommendations
        social_recs = self._generate_social_recommendations(extracted_data, decision)
        recommendations.extend(social_recs)
        
        # Sort by priority score
        recommendations.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _generate_employment_recommendations(self, extracted_data: Dict) -> List[Dict]:
        """Generate employment-related recommendations"""
        recommendations = []
        
        employment_status = "Unknown"
        skills = []
        experience_years = 0
        
        # Extract employment information
        if 'application_form' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            financial_info = app_data.get('financial_info', {})
            employment_status = financial_info.get('employment_status', 'Unknown')
        
        if 'resume' in extracted_data:
            resume_data = extracted_data['resume']
            skills = resume_data.get('skills_found', [])
            experience_years = resume_data.get('employment_history_years', 0)
        
        # Generate recommendations based on employment status
        if employment_status == 'Unemployed':
            recommendations.extend([
                {
                    'category': 'Employment',
                    'type': 'Job Matching',
                    'title': 'Immediate Job Placement Assistance',
                    'description': 'Connect with employers seeking candidates with your profile',
                    'priority_score': 9,
                    'urgency': 'High',
                    'estimated_duration': '2-4 weeks',
                    'provider': 'National Employment Program',
                    'eligibility': 'All unemployed applicants',
                    'expected_outcome': 'Job placement within 30 days'
                },
                {
                    'category': 'Employment', 
                    'type': 'Career Counseling',
                    'title': 'Career Assessment and Planning',
                    'description': 'Professional assessment of skills and career path guidance',
                    'priority_score': 8,
                    'urgency': 'Medium',
                    'estimated_duration': '4-6 sessions',
                    'provider': 'Career Development Center',
                    'eligibility': 'All applicants',
                    'expected_outcome': 'Clear career development plan'
                }
            ])
        
        # Skills-based recommendations
        if not skills or len(skills) < 3:
            recommendations.append({
                'category': 'Training',
                'type': 'Skills Development',
                'title': 'Essential Skills Training',
                'description': 'Develop fundamental employment skills including communication and teamwork',
                'priority_score': 7,
                'urgency': 'Medium',
                'estimated_duration': '6 weeks',
                'provider': 'Skills Development Institute',
                'eligibility': 'Limited skills profile',
                'expected_outcome': 'Enhanced employability skills'
            })
        
        # Experience-based recommendations
        if experience_years < 2:
            recommendations.append({
                'category': 'Employment',
                'type': 'Internship',
                'title': 'Paid Internship Program',
                'description': 'Gain practical work experience through structured internship',
                'priority_score': 7,
                'urgency': 'Medium', 
                'estimated_duration': '3-6 months',
                'provider': 'Youth Employment Initiative',
                'eligibility': 'Limited work experience',
                'expected_outcome': 'Practical work experience and references'
            })
        
        return recommendations
    
    def _generate_training_recommendations(self, extracted_data: Dict) -> List[Dict]:
        """Generate training and education recommendations"""
        recommendations = []
        
        education_level = "Unknown"
        skills = []
        
        # Extract education information
        if 'application_form' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            education_info = app_data.get('education_info', {})
            education_level = education_info.get('education_level', 'Unknown')
        
        if 'resume' in extracted_data:
            resume_data = extracted_data['resume']
            skills = resume_data.get('skills_found', [])
        
        # Education level-based recommendations
        if education_level in ['No Formal Education', 'Primary']:
            recommendations.extend([
                {
                    'category': 'Education',
                    'type': 'Literacy Program',
                    'title': 'Adult Literacy and Numeracy',
                    'description': 'Basic reading, writing, and mathematics skills development',
                    'priority_score': 9,
                    'urgency': 'High',
                    'estimated_duration': '6-12 months',
                    'provider': 'Community Education Center',
                    'eligibility': 'Limited formal education',
                    'expected_outcome': 'Functional literacy and numeracy'
                }
            ])
        elif education_level in ['Secondary', 'Diploma']:
            recommendations.extend([
                {
                    'category': 'Training',
                    'type': 'Vocational Training',
                    'title': 'Vocational Skills Certification',
                    'description': 'Hands-on training in high-demand trades and technical skills',
                    'priority_score': 8,
                    'urgency': 'Medium',
                    'estimated_duration': '3-9 months',
                    'provider': 'Technical Training Institute',
                    'eligibility': 'Secondary education completed',
                    'expected_outcome': 'Industry-recognized certification'
                }
            ])
        
        # Digital skills recommendations
        digital_skills = any(skill.lower() in ['computer', 'digital', 'technical', 'software'] 
                           for skill in skills)
        if not digital_skills:
            recommendations.append({
                'category': 'Training',
                'type': 'Digital Literacy',
                'title': 'Digital Skills Fundamentals',
                'description': 'Essential computer and internet skills for modern workplaces',
                'priority_score': 8,
                'urgency': 'Medium',
                'estimated_duration': '4 weeks',
                'provider': 'Digital Skills Academy',
                'eligibility': 'All applicants',
                'expected_outcome': 'Basic digital proficiency'
            })
        
        # Industry-specific training
        industry_skills = self._identify_industry_training_needs(skills)
        recommendations.extend(industry_skills)
        
        return recommendations
    
    def _generate_financial_recommendations(self, extracted_data: Dict, 
                                          eligibility_score: float) -> List[Dict]:
        """Generate financial enablement recommendations"""
        recommendations = []
        
        monthly_income = 0
        employment_status = "Unknown"
        
        # Extract financial information
        if 'application_form' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            financial_info = app_data.get('financial_info', {})
            monthly_income = financial_info.get('monthly_income', 0)
            employment_status = financial_info.get('employment_status', 'Unknown')
        
        # Financial literacy for all applicants
        recommendations.append({
            'category': 'Financial',
            'type': 'Financial Education',
            'title': 'Financial Literacy Workshop',
            'description': 'Learn budgeting, saving, and debt management strategies',
            'priority_score': 7,
            'urgency': 'Medium',
            'estimated_duration': '4 sessions',
            'provider': 'Financial Education Center',
            'eligibility': 'All applicants',
            'expected_outcome': 'Improved financial management skills'
        })
        
        # Micro-entrepreneurship for eligible applicants
        if eligibility_score >= 0.6 and employment_status in ['Unemployed', 'Self-Employed']:
            recommendations.append({
                'category': 'Financial',
                'type': 'Entrepreneurship',
                'title': 'Micro-Business Startup Support',
                'description': 'Training and small grant for starting micro-enterprise',
                'priority_score': 8,
                'urgency': 'Medium',
                'estimated_duration': '8 weeks + 6 months mentoring',
                'provider': 'Entrepreneurship Development Program',
                'eligibility': 'Moderate to high eligibility score',
                'expected_outcome': 'Sustainable micro-enterprise'
            })
        
        # Emergency financial assistance
        if monthly_income < 2000 and eligibility_score >= 0.7:
            recommendations.append({
                'category': 'Financial',
                'type': 'Immediate Support',
                'title': 'Emergency Financial Assistance',
                'description': 'Immediate financial support for basic needs',
                'priority_score': 10,
                'urgency': 'High',
                'estimated_duration': 'Immediate',
                'provider': 'Social Support Fund',
                'eligibility': 'High need + high eligibility score',
                'expected_outcome': 'Basic needs met while pursuing long-term solutions'
            })
        
        return recommendations
    
    def _generate_social_recommendations(self, extracted_data: Dict, decision: Dict) -> List[Dict]:
        """Generate social support recommendations"""
        recommendations = []
        
        family_size = 1
        dependents = 0
        housing_type = "Unknown"
        
        # Extract social information
        if 'application_form' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            family_info = app_data.get('family_info', {})
            financial_info = app_data.get('financial_info', {})
            family_size = family_info.get('family_size', 1)
            dependents = family_info.get('dependents', 0)
            housing_type = financial_info.get('housing_type', 'Unknown')
        
        # Family support recommendations
        if family_size >= 4 or dependents >= 2:
            recommendations.extend([
                {
                    'category': 'Social',
                    'type': 'Family Support',
                    'title': 'Family Counseling Services',
                    'description': 'Support for family dynamics and parenting challenges',
                    'priority_score': 7,
                    'urgency': 'Medium',
                    'estimated_duration': 'Ongoing',
                    'provider': 'Family Support Center',
                    'eligibility': 'Families with children',
                    'expected_outcome': 'Improved family wellbeing'
                },
                {
                    'category': 'Social',
                    'type': 'Childcare Support',
                    'title': 'Childcare Assistance Program',
                    'description': 'Subsidized childcare to enable employment and training',
                    'priority_score': 8,
                    'urgency': 'Medium',
                    'estimated_duration': '6-12 months',
                    'provider': 'Child Development Services',
                    'eligibility': 'Families with young children',
                    'expected_outcome': 'Enabled participation in employment/training'
                }
            ])
        
        # Housing support
        if housing_type == 'Rented' and "APPROVE" in decision.get('decision', ''):
            recommendations.append({
                'category': 'Social',
                'type': 'Housing Support',
                'title': 'Rental Assistance Program',
                'description': 'Temporary rental subsidy while achieving financial stability',
                'priority_score': 9,
                'urgency': 'High',
                'estimated_duration': '3-6 months',
                'provider': 'Housing Support Department',
                'eligibility': 'Approved applicants + rental housing',
                'expected_outcome': 'Housing stability during transition'
            })
        
        # Healthcare access
        recommendations.append({
            'category': 'Social',
            'type': 'Healthcare',
            'title': 'Healthcare Access Support',
            'description': 'Assistance accessing government healthcare services',
            'priority_score': 6,
            'urgency': 'Low',
            'estimated_duration': 'Ongoing',
            'provider': 'Health Services Department',
            'eligibility': 'All eligible applicants',
            'expected_outcome': 'Improved health access'
        })
        
        return recommendations
    
    def _identify_industry_training_needs(self, skills: List[str]) -> List[Dict]:
        """Identify industry-specific training needs based on existing skills"""
        industry_mapping = {
            'customer service': {
                'title': 'Advanced Customer Service Training',
                'description': 'Specialized training for retail and service industries',
                'provider': 'Service Excellence Institute'
            },
            'technical': {
                'title': 'IT Support Specialist Training',
                'description': 'Technical support and IT helpdesk skills development',
                'provider': 'Technology Training Center'
            },
            'healthcare': {
                'title': 'Healthcare Assistant Certification',
                'description': 'Training for entry-level healthcare support roles',
                'provider': 'Medical Training Institute'
            },
            'construction': {
                'title': 'Construction Skills Training',
                'description': 'Safety and skills training for construction industry',
                'provider': 'Construction Skills Academy'
            }
        }
        
        recommendations = []
        
        # Match existing skills to industry training
        skill_categories = {
            'customer service': any(skill.lower() in ['communication', 'customer', 'service'] for skill in skills),
            'technical': any(skill.lower() in ['technical', 'computer', 'software'] for skill in skills),
            'healthcare': any(skill.lower() in ['healthcare', 'medical', 'care'] for skill in skills),
            'construction': any(skill.lower() in ['construction', 'technical', 'manual'] for skill in skills)
        }
        
        for category, has_skills in skill_categories.items():
            if has_skills:
                industry_info = industry_mapping.get(category, {})
                recommendations.append({
                    'category': 'Training',
                    'type': 'Industry Specialization',
                    'title': industry_info.get('title', f'{category.title()} Skills Training'),
                    'description': industry_info.get('description', f'Advanced training in {category}'),
                    'priority_score': 7,
                    'urgency': 'Medium',
                    'estimated_duration': '8-12 weeks',
                    'provider': industry_info.get('provider', 'Industry Training Partner'),
                    'eligibility': 'Relevant background or interest',
                    'expected_outcome': f'Industry-specific certification in {category}'
                })
        
        return recommendations

# Register the agent
from .agent_framework import agent_registry
agent_registry.register_agent("economic_support", EconomicSupportAgent)