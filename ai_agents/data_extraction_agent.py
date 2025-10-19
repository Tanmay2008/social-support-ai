# ai_agents/data_extraction_agent.py
from .agent_framework import BaseAgent, AgentState, ReActFramework
from typing import Dict, List, Any
import json
import re
from datetime import datetime

class DataExtractionAgent(BaseAgent):
    """Agent responsible for extracting and structuring data from all document types"""
    
    def __init__(self):
        super().__init__(
            name="Data Extraction Agent",
            description="Extracts and structures data from multi-modal documents using OCR and parsing techniques"
        )
        self.react_framework = ReActFramework()
    
    def process(self, state: AgentState) -> AgentState:
        """Extract data from all submitted documents using ReAct framework"""
        self.log_action(state, "starting_data_extraction")
        
        try:
            if not self.validate_input(state, ['application_data']):
                return state
            
            documents = state['application_data'].get('documents', {})
            extracted_data = {}
            
            # Process each document type
            for doc_type, doc_info in documents.items():
                self.log_action(state, f"processing_document", {'document_type': doc_type})
                
                # Use ReAct framework for reasoning and action
                observation = f"Need to extract data from {doc_type}"
                context = {'doc_type': doc_type, 'fields': self._get_expected_fields(doc_type)}
                reasoning = self.react_framework.reason(observation, context)
                action = self.react_framework.act(reasoning, ['extract_structured_data'])
                
                self.log_action(state, "react_reasoning", {
                    'observation': observation,
                    'reasoning': reasoning,
                    'action': action
                })
                
                # Execute extraction based on document type
                if action == 'extract_structured_data':
                    extracted_data[doc_type] = self._extract_from_document_type(doc_type, doc_info)
                else:
                    extracted_data[doc_type] = self._fallback_extraction(doc_type, doc_info)
            
            state['extracted_info'] = extracted_data
            state['current_step'] = 'data_extraction_completed'
            
            self.log_action(state, "data_extraction_completed", {
                'documents_processed': len(documents),
                'extraction_success': True
            })
            
        except Exception as e:
            self.handle_error(state, e, "data_extraction_process")
        
        return state
    
    def _get_expected_fields(self, doc_type: str) -> List[str]:
        """Get expected fields for each document type"""
        field_mapping = {
            'application_form': ['personal_info', 'family_info', 'financial_info', 'education_info'],
            'bank_statement': ['account_holder', 'account_number', 'transactions', 'balances'],
            'emirates_id': ['id_number', 'name', 'nationality', 'expiry_date'],
            'credit_report': ['credit_score', 'accounts', 'payment_history'],
            'resume': ['employment_history', 'education', 'skills'],
            'assets_file': ['assets', 'liabilities', 'net_worth']
        }
        return field_mapping.get(doc_type, [])
    
    def _extract_from_document_type(self, doc_type: str, doc_info: Dict) -> Dict:
        """Extract data based on document type"""
        extraction_methods = {
            'application_form': self._extract_application_form,
            'bank_statement': self._extract_bank_statement,
            'emirates_id': self._extract_emirates_id,
            'credit_report': self._extract_credit_report,
            'resume': self._extract_resume,
            'assets_file': self._extract_assets_file
        }
        
        method = extraction_methods.get(doc_type, self._extract_generic_document)
        return method(doc_info)
    
    def _extract_application_form(self, form_data: Dict) -> Dict:
        """Extract structured data from application form"""
        try:
            # In real implementation, this would parse the actual form data
            # For prototype, we assume form_data is already structured
            return {
                'extraction_method': 'direct_mapping',
                'extraction_timestamp': datetime.now().isoformat(),
                'data': form_data,
                'confidence': 0.95
            }
        except Exception as e:
            return {
                'extraction_method': 'fallback',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _extract_bank_statement(self, bank_data: Dict) -> Dict:
        """Extract financial data from bank statement"""
        try:
            # Parse bank statement text or structured data
            text = bank_data.get('extracted_text', '') if isinstance(bank_data, dict) else str(bank_data)
            
            extracted_data = {
                'extraction_method': 'text_parsing',
                'account_holder': self._extract_account_holder(text),
                'account_number': self._extract_account_number(text),
                'statement_period': self._extract_statement_period(text),
                'opening_balance': self._extract_numeric_value(text, 'opening balance'),
                'closing_balance': self._extract_numeric_value(text, 'closing balance'),
                'transaction_count': len(self._extract_transactions(text)),
                'extraction_timestamp': datetime.now().isoformat(),
                'confidence': 0.85
            }
            
            return extracted_data
            
        except Exception as e:
            return {
                'extraction_method': 'error',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _extract_emirates_id(self, id_data: Dict) -> Dict:
        """Extract data from Emirates ID"""
        try:
            text = id_data.get('extracted_text', '') if isinstance(id_data, dict) else str(id_data)
            
            extracted_data = {
                'extraction_method': 'ocr_parsing',
                'id_number': self._extract_emirates_id_number(text),
                'full_name': self._extract_name(text),
                'nationality': self._extract_nationality(text),
                'date_of_birth': self._extract_dob(text),
                'expiry_date': self._extract_expiry_date(text),
                'extraction_timestamp': datetime.now().isoformat(),
                'confidence': 0.90
            }
            
            return extracted_data
            
        except Exception as e:
            return {
                'extraction_method': 'error',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _extract_credit_report(self, credit_data: Dict) -> Dict:
        """Extract data from credit report"""
        try:
            # Simulate credit report parsing
            return {
                'extraction_method': 'structured_parsing',
                'credit_score': 650 + (hash(credit_data.get('application_id', '')) % 200),
                'accounts_count': 3 + (hash(credit_data.get('application_id', '')) % 5),
                'total_debt': 15000 + (hash(credit_data.get('application_id', '')) % 35000),
                'payment_history_length': 24,
                'extraction_timestamp': datetime.now().isoformat(),
                'confidence': 0.88
            }
        except Exception as e:
            return {
                'extraction_method': 'error',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _extract_resume(self, resume_data: Dict) -> Dict:
        """Extract employment and education data from resume"""
        try:
            text = resume_data.get('extracted_text', '') if isinstance(resume_data, dict) else str(resume_data)
            
            extracted_data = {
                'extraction_method': 'text_analysis',
                'employment_history_years': self._extract_experience_years(text),
                'education_level': self._extract_education_level(text),
                'skills_found': self._extract_skills(text),
                'last_position': self._extract_last_position(text),
                'extraction_timestamp': datetime.now().isoformat(),
                'confidence': 0.80
            }
            
            return extracted_data
            
        except Exception as e:
            return {
                'extraction_method': 'error',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _extract_assets_file(self, assets_data: Dict) -> Dict:
        """Extract assets and liabilities data"""
        try:
            # For prototype, assume structured data
            if isinstance(assets_data, dict) and 'assets_breakdown' in assets_data:
                return {
                    'extraction_method': 'direct_mapping',
                    'total_assets': assets_data.get('total_assets', 0),
                    'total_liabilities': assets_data.get('total_liabilities', 0),
                    'net_worth': assets_data.get('net_worth', 0),
                    'assets_breakdown': assets_data.get('assets_breakdown', {}),
                    'extraction_timestamp': datetime.now().isoformat(),
                    'confidence': 0.95
                }
            else:
                return {
                    'extraction_method': 'estimation',
                    'total_assets': 50000,
                    'total_liabilities': 25000,
                    'net_worth': 25000,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'confidence': 0.60
                }
                
        except Exception as e:
            return {
                'extraction_method': 'error',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _extract_generic_document(self, doc_data: Dict) -> Dict:
        """Fallback extraction for unknown document types"""
        return {
            'extraction_method': 'generic_parsing',
            'content_length': len(str(doc_data)),
            'extraction_timestamp': datetime.now().isoformat(),
            'confidence': 0.50
        }
    
    def _fallback_extraction(self, doc_type: str, doc_info: Dict) -> Dict:
        """Fallback extraction method"""
        return {
            'extraction_method': 'fallback',
            'document_type': doc_type,
            'note': 'Used fallback extraction method',
            'extraction_timestamp': datetime.now().isoformat(),
            'confidence': 0.30
        }
    
    # Helper methods for text extraction
    def _extract_account_holder(self, text: str) -> str:
        """Extract account holder name from text"""
        patterns = [
            r'Account Holder:\s*([^\n]+)',
            r'Customer Name:\s*([^\n]+)',
            r'Name:\s*([^\n]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Unknown"
    
    def _extract_account_number(self, text: str) -> str:
        """Extract account number from text"""
        patterns = [
            r'Account Number:\s*([A-Z0-9-]+)',
            r'Account No\.:\s*([A-Z0-9-]+)',
            r'Acc\. No:\s*([A-Z0-9-]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Unknown"
    
    def _extract_emirates_id_number(self, text: str) -> str:
        """Extract Emirates ID number"""
        patterns = [
            r'\b[0-9]{3}-[0-9]{4}-[0-9]{7}-[0-9]{1}\b',
            r'\b[0-9]{15}\b'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return "Unknown"
    
    def _extract_name(self, text: str) -> str:
        """Extract name from text"""
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['name', 'full name']):
                parts = line.split(':')
                if len(parts) > 1:
                    return parts[1].strip()
        return "Unknown"
    
    def _extract_numeric_value(self, text: str, field_name: str) -> float:
        """Extract numeric value for a specific field"""
        pattern = f"{field_name}.*?([0-9,]+(?:\.[0-9]+)?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '')
            try:
                return float(value_str)
            except ValueError:
                pass
        return 0.0
    
    def _extract_transactions(self, text: str) -> List[Dict]:
        """Extract transactions from bank statement text"""
        # Simplified transaction extraction
        transactions = []
        lines = text.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['aed', 'dh', 'dhs']):
                # Simple transaction detection
                amount_match = re.search(r'([+-]?[0-9,]+(?:\.[0-9]+)?)\s*(?:AED|DH|DHS)', line)
                if amount_match:
                    transactions.append({
                        'description': line,
                        'amount': float(amount_match.group(1).replace(',', '')),
                        'type': 'credit' if '+' in line else 'debit'
                    })
        
        return transactions[:10]  # Return first 10 transactions
    
    def _extract_experience_years(self, text: str) -> int:
        """Extract total years of experience from resume"""
        # Simple heuristic based on date patterns
        year_matches = re.findall(r'(19|20)\d{2}', text)
        if year_matches:
            return min(len(year_matches) // 2, 30)  # Rough estimate
        return 5  # Default
    
    def _extract_education_level(self, text: str) -> str:
        """Extract education level from resume"""
        education_keywords = {
            'phd': 'PhD',
            'master': 'Master', 
            'bachelor': 'Bachelor',
            'diploma': 'Diploma',
            'high school': 'Secondary',
            'secondary': 'Secondary'
        }
        
        text_lower = text.lower()
        for keyword, level in education_keywords.items():
            if keyword in text_lower:
                return level
        
        return 'Unknown'
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume"""
        common_skills = [
            'communication', 'problem solving', 'teamwork', 'leadership',
            'python', 'java', 'sql', 'excel', 'project management',
            'customer service', 'data analysis', 'digital literacy'
        ]
        
        found_skills = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        return found_skills[:5]  # Return top 5 skills
    
    def _extract_last_position(self, text: str) -> str:
        """Extract most recent position from resume"""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(role in line.lower() for role in ['manager', 'engineer', 'analyst', 'specialist', 'assistant']):
                return line.strip()
        return "Unknown Position"

# Register the agent
from .agent_framework import agent_registry
agent_registry.register_agent("data_extraction", DataExtractionAgent)