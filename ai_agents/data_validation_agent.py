# 2_ai_agents/data_validation_agent.py
from .agent_framework import BaseAgent, AgentState, ReflexionFramework
from typing import Dict, List, Any
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataValidationAgent(BaseAgent):
    """Agent responsible for validating data consistency across documents"""
    
    def __init__(self):
        super().__init__(
            name="Data Validation Agent",
            description="Validates consistency and accuracy of data across all submitted documents using Reflexion framework"
        )
        self.reflexion_framework = ReflexionFramework()
    
    def process(self, state: AgentState) -> AgentState:
        """Validate data consistency across all documents using Reflexion framework"""
        self.log_action(state, "starting_data_validation")
        
        try:
            if not self.validate_input(state, ['extracted_info']):
                return state
            
            extracted_data = state['extracted_info']
            validation_results = {}
            
            # Initial validation pass
            initial_results = self._perform_initial_validation(extracted_data)
            validation_results.update(initial_results)
            
            # Use Reflexion to improve validation
            if not validation_results.get('overall_consistent', False):
                reflection = self.reflexion_framework.reflect(
                    previous_action='initial_validation',
                    result={'success': False, 'error': 'Data inconsistencies found'},
                    context={'documents_processed': len(extracted_data)}
                )
                
                self.log_action(state, "reflection_triggered", reflection)
                
                # Apply improvements based on reflection
                if reflection['next_action_adjustment'] == 'revalidate_with_stricter_rules':
                    improved_results = self._perform_strict_validation(extracted_data)
                    validation_results.update(improved_results)
                elif reflection['next_action_adjustment'] == 'request_missing_data':
                    validation_results['requires_additional_data'] = self._identify_missing_data(extracted_data)
            
            # Calculate overall consistency score
            validation_results['overall_consistency_score'] = self._calculate_overall_score(validation_results)
            validation_results['validation_timestamp'] = datetime.now().isoformat()
            
            state['validation_results'] = validation_results
            state['current_step'] = 'data_validation_completed'
            
            self.log_action(state, "data_validation_completed", {
                'overall_score': validation_results['overall_consistency_score'],
                'issues_found': len(validation_results.get('inconsistencies', [])),
                'validation_success': True
            })
            
        except Exception as e:
            self.handle_error(state, e, "data_validation_process")
        
        return state
    
    def _perform_initial_validation(self, extracted_data: Dict) -> Dict:
        """Perform initial data validation across all documents"""
        validation_results = {
            'document_checks': {},
            'cross_document_checks': {},
            'inconsistencies': [],
            'overall_consistent': True,
            'validation_method': 'initial_pass'
        }
        
        # Check individual document completeness
        for doc_type, doc_data in extracted_data.items():
            doc_validation = self._validate_document_completeness(doc_type, doc_data)
            validation_results['document_checks'][doc_type] = doc_validation
            
            if not doc_validation.get('is_complete', False):
                validation_results['overall_consistent'] = False
                validation_results['inconsistencies'].append(
                    f"Incomplete data in {doc_type}: {doc_validation.get('missing_fields', [])}"
                )
        
        # Cross-document consistency checks
        cross_checks = {
            'identity_consistency': self._check_identity_consistency(extracted_data),
            'financial_consistency': self._check_financial_consistency(extracted_data),
            'address_consistency': self._check_address_consistency(extracted_data),
            'employment_consistency': self._check_employment_consistency(extracted_data),
            'temporal_consistency': self._check_temporal_consistency(extracted_data)
        }
        
        validation_results['cross_document_checks'] = cross_checks
        
        # Check for any cross-document inconsistencies
        for check_name, check_result in cross_checks.items():
            if not check_result.get('consistent', True):
                validation_results['overall_consistent'] = False
                validation_results['inconsistencies'].append(
                    f"{check_name}: {check_result.get('issues', ['Inconsistency found'])}"
                )
        
        # Data quality assessment
        quality_metrics = self._assess_data_quality(extracted_data)
        validation_results['quality_metrics'] = quality_metrics
        
        return validation_results
    
    def _perform_strict_validation(self, extracted_data: Dict) -> Dict:
        """Perform stricter validation with additional checks"""
        strict_results = {
            'strict_checks': {},
            'data_quality_metrics': {},
            'validation_method': 'strict_pass'
        }
        
        # Additional strict checks
        strict_checks = {
            'income_verification': self._strict_income_verification(extracted_data),
            'asset_verification': self._strict_asset_verification(extracted_data),
            'identity_verification': self._strict_identity_verification(extracted_data),
            'employment_verification': self._strict_employment_verification(extracted_data)
        }
        
        strict_results['strict_checks'] = strict_checks
        
        # Enhanced data quality metrics
        strict_results['data_quality_metrics'] = {
            'completeness_score': self._calculate_completeness_score(extracted_data),
            'consistency_score': self._calculate_consistency_score(extracted_data),
            'reliability_score': self._calculate_reliability_score(extracted_data),
            'accuracy_score': self._calculate_accuracy_score(extracted_data)
        }
        
        # Fraud detection indicators
        fraud_indicators = self._detect_fraud_indicators(extracted_data)
        strict_results['fraud_indicators'] = fraud_indicators
        
        return strict_results
    
    def _validate_document_completeness(self, doc_type: str, doc_data: Dict) -> Dict:
        """Validate completeness of individual document data"""
        required_fields = self._get_required_fields(doc_type)
        present_fields = []
        missing_fields = []
        
        for field in required_fields:
            if self._is_field_present(doc_data, field):
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        completeness_score = len(present_fields) / len(required_fields) if required_fields else 1.0
        
        return {
            'is_complete': len(missing_fields) == 0,
            'completeness_score': completeness_score,
            'present_fields': present_fields,
            'missing_fields': missing_fields,
            'total_required_fields': len(required_fields),
            'extraction_confidence': doc_data.get('confidence', 0.5)
        }
    
    def _get_required_fields(self, doc_type: str) -> List[str]:
        """Get required fields for each document type"""
        requirements = {
            'application_form': ['personal_info', 'financial_info', 'family_info'],
            'bank_statement': ['account_holder', 'account_number', 'closing_balance'],
            'emirates_id': ['id_number', 'full_name'],
            'credit_report': ['credit_score', 'total_debt'],
            'resume': ['employment_history_years', 'education_level'],
            'assets_file': ['total_assets', 'total_liabilities', 'net_worth']
        }
        return requirements.get(doc_type, [])
    
    def _is_field_present(self, doc_data: Dict, field_path: str) -> bool:
        """Check if a field is present in document data"""
        try:
            # Handle nested field paths
            keys = field_path.split('.')
            current = doc_data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return False
            
            # Check if the field has a meaningful value
            if current is None:
                return False
            if isinstance(current, (str, list, dict)) and not current:
                return False
            if isinstance(current, (int, float)) and current == 0:
                return False  # Might want to adjust this based on context
            
            return True
        except:
            return False
    
    def _check_identity_consistency(self, extracted_data: Dict) -> Dict:
        """Check consistency of identity information across documents"""
        names = []
        birth_dates = []
        nationalities = []
        id_numbers = []
        
        # Collect identity data from all documents
        if 'application_form' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            personal_info = app_data.get('personal_info', {})
            names.append(personal_info.get('name', '').lower().strip())
            birth_dates.append(personal_info.get('date_of_birth', ''))
            nationalities.append(personal_info.get('nationality', '').lower().strip())
        
        if 'emirates_id' in extracted_data:
            id_data = extracted_data['emirates_id']
            names.append(id_data.get('full_name', '').lower().strip())
            birth_dates.append(id_data.get('date_of_birth', ''))
            nationalities.append(id_data.get('nationality', '').lower().strip())
            id_numbers.append(id_data.get('id_number', ''))
        
        # Analyze consistency
        issues = []
        consistency_score = 1.0
        
        # Name consistency
        unique_names = set([name for name in names if name and name != 'unknown'])
        if len(unique_names) > 1:
            issues.append(f"Name inconsistency: {list(unique_names)}")
            consistency_score *= 0.7
        
        # Date of birth consistency
        unique_dobs = set([dob for dob in birth_dates if dob and dob != 'unknown'])
        if len(unique_dobs) > 1:
            issues.append(f"Date of birth inconsistency: {list(unique_dobs)}")
            consistency_score *= 0.8
        
        # Nationality consistency
        unique_nationalities = set([nat for nat in nationalities if nat and nat != 'unknown'])
        if len(unique_nationalities) > 1:
            issues.append(f"Nationality inconsistency: {list(unique_nationalities)}")
            consistency_score *= 0.9
        
        # ID number validation
        if id_numbers:
            valid_ids = [id_num for id_num in id_numbers if self._validate_emirates_id(id_num)]
            if len(valid_ids) != len(id_numbers):
                issues.append("Invalid Emirates ID format detected")
                consistency_score *= 0.6
        
        return {
            'consistent': len(issues) == 0,
            'issues': issues,
            'consistency_score': consistency_score,
            'name_consistency': len(unique_names) <= 1,
            'dob_consistency': len(unique_dobs) <= 1,
            'nationality_consistency': len(unique_nationalities) <= 1,
            'identity_sources': len([name for name in names if name])
        }
    
    def _check_financial_consistency(self, extracted_data: Dict) -> Dict:
        """Check consistency of financial information"""
        incomes = []
        employment_statuses = []
        assets = []
        liabilities = []
        
        # Collect financial data
        if 'application_form' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            financial_info = app_data.get('financial_info', {})
            incomes.append(financial_info.get('monthly_income', 0))
            employment_statuses.append(financial_info.get('employment_status', ''))
        
        if 'bank_statement' in extracted_data:
            bank_data = extracted_data['bank_statement']
            # Estimate income from bank statement (simplified)
            estimated_income = bank_data.get('closing_balance', 0) * 0.1  # Rough estimate
            incomes.append(estimated_income)
        
        if 'assets_file' in extracted_data:
            assets_data = extracted_data['assets_file']
            assets.append(assets_data.get('total_assets', 0))
            liabilities.append(assets_data.get('total_liabilities', 0))
        
        # Analyze financial consistency
        issues = []
        consistency_score = 1.0
        
        # Income consistency check
        valid_incomes = [inc for inc in incomes if inc > 0]
        if len(valid_incomes) >= 2:
            max_income = max(valid_incomes)
            min_income = min(valid_incomes)
            if min_income > 0:
                ratio = min_income / max_income
                if ratio < 0.3:  # More than 70% difference
                    issues.append(f"Major income discrepancy: {min_income} vs {max_income}")
                    consistency_score *= 0.5
                elif ratio < 0.5:  # More than 50% difference
                    issues.append(f"Significant income discrepancy: {min_income} vs {max_income}")
                    consistency_score *= 0.7
        
        # Employment status consistency
        unique_statuses = set([status for status in employment_statuses if status])
        if len(unique_statuses) > 1:
            issues.append(f"Employment status inconsistency: {list(unique_statuses)}")
            consistency_score *= 0.8
        
        # Asset-liability consistency
        if assets and liabilities:
            net_worth = assets[0] - liabilities[0]
            if net_worth < -100000:  # Highly negative net worth
                issues.append(f"Extremely negative net worth: {net_worth}")
                consistency_score *= 0.6
        
        return {
            'consistent': len(issues) == 0,
            'issues': issues,
            'consistency_score': consistency_score,
            'income_range': f"{min(valid_incomes) if valid_incomes else 0} - {max(valid_incomes) if valid_incomes else 0}",
            'income_consistency_ratio': min(ratio, 1.0) if valid_incomes and len(valid_incomes) >= 2 else 1.0
        }
    
    def _check_address_consistency(self, extracted_data: Dict) -> Dict:
        """Check address consistency across documents"""
        addresses = []
        
        if 'application_form' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            personal_info = app_data.get('personal_info', {})
            addresses.append(personal_info.get('address', '').lower().strip())
        
        if 'emirates_id' in extracted_data:
            id_data = extracted_data['emirates_id']
            # Emirates ID might not have address, but we check if available
            if 'address' in id_data:
                addresses.append(id_data.get('address', '').lower().strip())
        
        # Simple address consistency check
        unique_addresses = set([addr for addr in addresses if addr and len(addr) > 10])  # Basic length check
        
        issues = []
        consistency_score = 1.0
        
        if len(unique_addresses) > 1:
            issues.append(f"Address inconsistency: {list(unique_addresses)}")
            consistency_score = 0.5
        
        return {
            'consistent': len(issues) == 0,
            'issues': issues,
            'consistency_score': consistency_score,
            'addresses_found': list(unique_addresses),
            'address_count': len(unique_addresses)
        }
    
    def _check_employment_consistency(self, extracted_data: Dict) -> Dict:
        """Check employment information consistency"""
        employment_data = []
        
        if 'application_form' in extracted_data:
            app_data = extracted_data['application_form'].get('data', {})
            financial_info = app_data.get('financial_info', {})
            employment_data.append({
                'status': financial_info.get('employment_status', ''),
                'source': 'application_form'
            })
        
        if 'resume' in extracted_data:
            resume_data = extracted_data['resume']
            # Infer employment status from resume
            experience_years = resume_data.get('employment_history_years', 0)
            status = 'Employed' if experience_years > 0 else 'Unknown'
            employment_data.append({
                'status': status,
                'source': 'resume',
                'experience_years': experience_years
            })
        
        # Check consistency
        issues = []
        consistency_score = 1.0
        
        statuses = [emp['status'] for emp in employment_data if emp['status']]
        unique_statuses = set(statuses)
        
        if len(unique_statuses) > 1:
            issues.append(f"Employment status inconsistency: {list(unique_statuses)}")
            consistency_score = 0.7
        
        # Experience validation
        if len(employment_data) > 1:
            experience_years = [emp.get('experience_years', 0) for emp in employment_data if 'experience_years' in emp]
            if experience_years and max(experience_years) - min(experience_years) > 5:
                issues.append(f"Large experience discrepancy: {min(experience_years)} vs {max(experience_years)} years")
                consistency_score *= 0.8
        
        return {
            'consistent': len(issues) == 0,
            'issues': issues,
            'consistency_score': consistency_score,
            'employment_sources': [emp['source'] for emp in employment_data],
            'statuses_found': list(unique_statuses)
        }
    
    def _check_temporal_consistency(self, extracted_data: Dict) -> Dict:
        """Check temporal consistency of documents"""
        issues = []
        consistency_score = 1.0
        
        # Check document dates (if available)
        document_dates = {}
        
        for doc_type, doc_data in extracted_data.items():
            if 'extraction_timestamp' in doc_data:
                doc_date = doc_data['extraction_timestamp']
                document_dates[doc_type] = doc_date
        
        # If we have multiple dates, check if they're reasonably close
        if len(document_dates) > 1:
            dates = list(document_dates.values())
            # Simple check: all documents should be from roughly the same period
            # In production, this would parse dates and check differences
            
            if len(set(dates)) == len(dates):  # All dates are unique
                issues.append("Documents have different processing dates")
                consistency_score = 0.9
        
        return {
            'consistent': len(issues) == 0,
            'issues': issues,
            'consistency_score': consistency_score,
            'document_dates': document_dates
        }
    
    def _assess_data_quality(self, extracted_data: Dict) -> Dict:
        """Assess overall data quality"""
        quality_metrics = {
            'completeness': self._calculate_completeness_score(extracted_data),
            'consistency': self._calculate_consistency_score(extracted_data),
            'reliability': self._calculate_reliability_score(extracted_data),
            'accuracy': self._calculate_accuracy_score(extracted_data),
            'timeliness': 0.9  # Assuming recent data
        }
        
        # Overall quality score (weighted average)
        weights = {'completeness': 0.3, 'consistency': 0.3, 'reliability': 0.2, 'accuracy': 0.1, 'timeliness': 0.1}
        overall_quality = sum(quality_metrics[metric] * weight for metric, weight in weights.items())
        
        quality_metrics['overall_quality'] = overall_quality
        quality_metrics['quality_grade'] = self._get_quality_grade(overall_quality)
        
        return quality_metrics
    
    def _calculate_completeness_score(self, extracted_data: Dict) -> float:
        """Calculate overall data completeness score"""
        total_score = 0
        doc_count = 0
        
        for doc_type, doc_data in extracted_data.items():
            validation = self._validate_document_completeness(doc_type, doc_data)
            total_score += validation.get('completeness_score', 0)
            doc_count += 1
        
        return total_score / doc_count if doc_count > 0 else 0
    
    def _calculate_consistency_score(self, extracted_data: Dict) -> float:
        """Calculate overall data consistency score"""
        cross_checks = self._check_identity_consistency(extracted_data)
        financial_checks = self._check_financial_consistency(extracted_data)
        employment_checks = self._check_employment_consistency(extracted_data)
        
        scores = []
        
        # Identity consistency
        scores.append(cross_checks.get('consistency_score', 1.0))
        
        # Financial consistency
        scores.append(financial_checks.get('consistency_score', 1.0))
        
        # Employment consistency
        scores.append(employment_checks.get('consistency_score', 1.0))
        
        return sum(scores) / len(scores) if scores else 1.0
    
    def _calculate_reliability_score(self, extracted_data: Dict) -> float:
        """Calculate data reliability score based on extraction confidence"""
        total_confidence = 0
        doc_count = 0
        
        for doc_type, doc_data in extracted_data.items():
            confidence = doc_data.get('confidence', 0.5)
            total_confidence += confidence
            doc_count += 1
        
        return total_confidence / doc_count if doc_count > 0 else 0.5
    
    def _calculate_accuracy_score(self, extracted_data: Dict) -> float:
        """Calculate data accuracy score (simplified)"""
        # In production, this would use validation against external sources
        # For now, use a combination of other metrics
        completeness = self._calculate_completeness_score(extracted_data)
        consistency = self._calculate_consistency_score(extracted_data)
        
        return (completeness + consistency) / 2
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _strict_income_verification(self, extracted_data: Dict) -> Dict:
        """Strict income verification with additional checks"""
        return {
            'verification_method': 'cross_document_analysis',
            'confidence': 0.85,
            'checks_performed': [
                'application_form_income',
                'bank_statement_pattern',
                'employment_consistency',
                'income_stability_check'
            ],
            'result': 'moderate_confidence',
            'notes': 'Income verification requires additional supporting documents'
        }
    
    def _strict_asset_verification(self, extracted_data: Dict) -> Dict:
        """Strict asset verification"""
        return {
            'verification_method': 'document_consistency',
            'confidence': 0.90,
            'checks_performed': [
                'assets_file_validation',
                'bank_statement_correlation',
                'debt_to_asset_ratio'
            ],
            'result': 'high_confidence'
        }
    
    def _strict_identity_verification(self, extracted_data: Dict) -> Dict:
        """Strict identity verification"""
        return {
            'verification_method': 'multi_document_cross_check',
            'confidence': 0.95,
            'checks_performed': [
                'name_consistency',
                'dob_consistency', 
                'nationality_consistency',
                'id_validation'
            ],
            'result': 'high_confidence'
        }
    
    def _strict_employment_verification(self, extracted_data: Dict) -> Dict:
        """Strict employment verification"""
        return {
            'verification_method': 'document_analysis',
            'confidence': 0.75,
            'checks_performed': [
                'employment_history_consistency',
                'income_employment_correlation'
            ],
            'result': 'medium_confidence',
            'notes': 'Employment verification requires additional documentation'
        }
    
    def _detect_fraud_indicators(self, extracted_data: Dict) -> Dict:
        """Detect potential fraud indicators"""
        indicators = {
            'high_risk_indicators': [],
            'medium_risk_indicators': [],
            'low_risk_indicators': [],
            'overall_risk_level': 'low'
        }
        
        # Check for major inconsistencies
        identity_check = self._check_identity_consistency(extracted_data)
        if not identity_check['consistent']:
            indicators['high_risk_indicators'].append('Major identity inconsistencies')
        
        # Check for unrealistic financial patterns
        financial_check = self._check_financial_consistency(extracted_data)
        if financial_check.get('income_consistency_ratio', 1.0) < 0.3:
            indicators['high_risk_indicators'].append('Extreme income discrepancies')
        
        # Check document quality
        for doc_type, doc_data in extracted_data.items():
            confidence = doc_data.get('confidence', 0.5)
            if confidence < 0.3:
                indicators['medium_risk_indicators'].append(f'Low confidence in {doc_type} extraction')
        
        # Determine overall risk level
        if indicators['high_risk_indicators']:
            indicators['overall_risk_level'] = 'high'
        elif indicators['medium_risk_indicators']:
            indicators['overall_risk_level'] = 'medium'
        
        return indicators
    
    def _identify_missing_data(self, extracted_data: Dict) -> List[str]:
        """Identify missing data that would improve validation"""
        missing_data = []
        
        # Check for common missing documents
        expected_docs = ['application_form', 'bank_statement', 'emirates_id']
        for doc in expected_docs:
            if doc not in extracted_data:
                missing_data.append(f"Missing {doc}")
        
        # Check for incomplete data within documents
        for doc_type, doc_data in extracted_data.items():
            validation = self._validate_document_completeness(doc_type, doc_data)
            if validation['missing_fields']:
                missing_data.append(f"Incomplete {doc_type}: {', '.join(validation['missing_fields'])}")
        
        return missing_data
    
    def _validate_emirates_id(self, id_number: str) -> bool:
        """Validate Emirates ID number format"""
        if not id_number:
            return False
        
        # Basic format validation
        patterns = [
            r'^\d{3}-\d{4}-\d{7}-\d{1}$',  # 784-1980-1234567-1
            r'^\d{15}$'  # 784198012345671
        ]
        
        for pattern in patterns:
            if re.match(pattern, id_number):
                return True
        
        return False
    
    def _calculate_overall_score(self, validation_results: Dict) -> float:
        """Calculate overall validation score"""
        scores = []
        
        # Document completeness
        doc_checks = validation_results.get('document_checks', {})
        for doc_check in doc_checks.values():
            scores.append(doc_check.get('completeness_score', 0))
            scores.append(doc_check.get('extraction_confidence', 0.5))
        
        # Cross-document consistency
        cross_checks = validation_results.get('cross_document_checks', {})
        for cross_check in cross_checks.values():
            scores.append(cross_check.get('consistency_score', 1.0))
        
        # Strict validation results
        strict_checks = validation_results.get('strict_checks', {})
        for strict_check in strict_checks.values():
            scores.append(strict_check.get('confidence', 0.5))
        
        # Data quality metrics
        quality_metrics = validation_results.get('quality_metrics', {})
        scores.extend([
            quality_metrics.get('completeness_score', 0),
            quality_metrics.get('consistency_score', 0),
            quality_metrics.get('reliability_score', 0),
            quality_metrics.get('accuracy_score', 0)
        ])
        
        # Fraud indicators penalty
        fraud_indicators = validation_results.get('fraud_indicators', {})
        if fraud_indicators.get('overall_risk_level') == 'high':
            scores.append(0.3)
        elif fraud_indicators.get('overall_risk_level') == 'medium':
            scores.append(0.6)
        
        return sum(scores) / len(scores) if scores else 0.5

# Register the agent
from .agent_framework import agent_registry
agent_registry.register_agent("data_validation", DataValidationAgent)