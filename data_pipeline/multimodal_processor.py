# 1_data_pipeline/multimodal_processor.py
import pandas as pd
import numpy as np
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import easyocr
import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib

class MultiModalDataProcessor:
    def __init__(self, db_path: str = "data/applications.db"):
        self.db_path = db_path
        self.reader = easyocr.Reader(['en'])
        self.setup_databases()
    
    def setup_databases(self):
        """Initialize all required databases"""
        # SQLite for structured data (PostgreSQL in production)
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()
        
        # Qdrant for vector storage
        self.qdrant_client = QdrantClient(":memory:")
        self.qdrant_client.create_collection(
            collection_name="document_embeddings",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
    
    def create_tables(self):
        """Create necessary database tables"""
        cursor = self.conn.cursor()
        
        # Applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                application_id TEXT PRIMARY KEY,
                applicant_data TEXT,
                extracted_data TEXT,
                validation_results TEXT,
                eligibility_score REAL,
                decision TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                application_id TEXT,
                doc_type TEXT,
                file_path TEXT,
                extracted_text TEXT,
                processing_status TEXT,
                FOREIGN KEY (application_id) REFERENCES applications (application_id)
            )
        ''')
        
        self.conn.commit()
    
    def process_application_form(self, form_data: Dict) -> Dict:
        """Process interactive application form data"""
        try:
            processed_data = {
                'applicant_id': form_data.get('applicant_id', self.generate_applicant_id()),
                'personal_info': {
                    'name': form_data.get('full_name', ''),
                    'email': form_data.get('email', ''),
                    'phone': form_data.get('phone', ''),
                    'address': form_data.get('address', ''),
                    'date_of_birth': form_data.get('date_of_birth', ''),
                    'nationality': form_data.get('nationality', '')
                },
                'family_info': {
                    'marital_status': form_data.get('marital_status', ''),
                    'family_size': form_data.get('family_size', 1),
                    'dependents': form_data.get('dependents', 0)
                },
                'financial_info': {
                    'employment_status': form_data.get('employment_status', ''),
                    'monthly_income': float(form_data.get('monthly_income', 0)),
                    'income_source': form_data.get('income_source', ''),
                    'housing_type': form_data.get('housing_type', ''),
                    'monthly_rent': float(form_data.get('monthly_rent', 0))
                },
                'education_info': {
                    'education_level': form_data.get('education_level', ''),
                    'skills': form_data.get('skills', [])
                },
                'support_requested': form_data.get('support_type_requested', ''),
                'submission_date': datetime.now().isoformat()
            }
            
            # Store in database
            self.store_application_data(processed_data)
            
            return processed_data
            
        except Exception as e:
            raise Exception(f"Error processing application form: {str(e)}")
    
    def extract_text_from_documents(self, document_path: str, doc_type: str, application_id: str) -> Dict:
        """Extract text from various document types using OCR"""
        try:
            extracted_data = {'doc_type': doc_type, 'application_id': application_id}
            
            if doc_type == 'emirates_id':
                extracted_data.update(self.process_emirates_id(document_path))
            elif doc_type == 'bank_statement':
                extracted_data.update(self.process_bank_statement(document_path))
            elif doc_type == 'credit_report':
                extracted_data.update(self.process_credit_report(document_path))
            elif doc_type == 'resume':
                extracted_data.update(self.process_resume(document_path))
            else:
                # Generic document processing
                extracted_data.update(self.process_generic_document(document_path))
            
            # Store document in database
            self.store_document_data(application_id, doc_type, document_path, extracted_data)
            
            return extracted_data
            
        except Exception as e:
            return {'error': f"Failed to process {doc_type}: {str(e)}"}
    
    def process_emirates_id(self, image_path: str) -> Dict:
        """Process Emirates ID card"""
        try:
            # OCR extraction
            ocr_result = self.reader.readtext(image_path)
            full_text = ' '.join([text[1] for text in ocr_result])
            
            # Parse specific fields using regex
            parsed_data = {
                'document_type': 'Emirates ID',
                'full_text': full_text,
                'id_number': self.extract_id_number(full_text),
                'name': self.extract_name(full_text),
                'nationality': self.extract_nationality(full_text),
                'date_of_birth': self.extract_dob(full_text),
                'expiry_date': self.extract_expiry_date(full_text)
            }
            
            return parsed_data
            
        except Exception as e:
            return {'error': f"Emirates ID processing failed: {str(e)}"}
    
    def process_bank_statement(self, pdf_path: str) -> Dict:
        """Process bank statement PDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            
            parsed_data = {
                'document_type': 'Bank Statement',
                'full_text': text,
                'account_holder': self.extract_account_holder(text),
                'account_number': self.extract_account_number(text),
                'period': self.extract_statement_period(text),
                'opening_balance': self.extract_opening_balance(text),
                'closing_balance': self.extract_closing_balance(text),
                'transactions': self.extract_transactions(text)
            }
            
            return parsed_data
            
        except Exception as e:
            return {'error': f"Bank statement processing failed: {str(e)}"}
    
    def process_tabular_data(self, file_path: str, application_id: str) -> Dict:
        """Process Excel files for assets/liabilities"""
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                return {'error': 'Unsupported file format'}
            
            processed_data = {
                'document_type': 'Assets/Liabilities',
                'total_assets': float(df.get('total_assets', [0])[0]) if 'total_assets' in df.columns else 0,
                'total_liabilities': float(df.get('total_liabilities', [0])[0]) if 'total_liabilities' in df.columns else 0,
                'net_worth': float(df.get('net_worth', [0])[0]) if 'net_worth' in df.columns else 0,
                'assets_breakdown': df.to_dict('records'),
                'summary_stats': {
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'data_types': dict(df.dtypes)
                }
            }
            
            self.store_document_data(application_id, 'assets_liabilities', file_path, processed_data)
            
            return processed_data
            
        except Exception as e:
            return {'error': f"Tabular data processing failed: {str(e)}"}
    
    def validate_data_consistency(self, all_data: Dict) -> Dict:
        """Cross-validate information across all documents"""
        validation_results = {
            'address_consistency': self.check_address_consistency(all_data),
            'income_consistency': self.check_income_consistency(all_data),
            'identity_consistency': self.check_identity_consistency(all_data),
            'family_consistency': self.check_family_consistency(all_data),
            'overall_score': 0.0
        }
        
        # Calculate overall consistency score
        scores = [result.get('score', 0) for result in validation_results.values() if isinstance(result, dict)]
        if scores:
            validation_results['overall_score'] = sum(scores) / len(scores)
        
        return validation_results
    
    def check_address_consistency(self, data: Dict) -> Dict:
        """Check address consistency across documents"""
        addresses = []
        
        if 'application_form' in data:
            app_address = data['application_form'].get('personal_info', {}).get('address', '')
            if app_address:
                addresses.append(app_address.lower().strip())
        
        if 'emirates_id' in data:
            id_address = data['emirates_id'].get('address', '')
            if id_address:
                addresses.append(id_address.lower().strip())
        
        if len(set(addresses)) <= 1:
            return {'consistent': True, 'score': 1.0, 'addresses_found': addresses}
        else:
            return {'consistent': False, 'score': 0.3, 'addresses_found': addresses}
    
    def check_income_consistency(self, data: Dict) -> Dict:
        """Check income consistency across documents"""
        incomes = []
        
        if 'application_form' in data:
            app_income = data['application_form'].get('financial_info', {}).get('monthly_income', 0)
            if app_income > 0:
                incomes.append(app_income)
        
        if 'bank_statement' in data:
            # Extract income patterns from bank statements
            bank_income = self.estimate_income_from_bank_statement(data.get('bank_statement', {}))
            if bank_income > 0:
                incomes.append(bank_income)
        
        if len(incomes) < 2:
            return {'consistent': True, 'score': 0.8, 'incomes_found': incomes}
        
        # Check if incomes are within reasonable range
        max_income = max(incomes)
        min_income = min(incomes)
        ratio = min_income / max_income if max_income > 0 else 0
        
        consistent = ratio > 0.5  # Within 50% of each other
        score = ratio if consistent else 0.3
        
        return {'consistent': consistent, 'score': score, 'incomes_found': incomes}
    
    # Helper methods for text extraction
    def extract_id_number(self, text: str) -> str:
        """Extract Emirates ID number"""
        patterns = [
            r'\b[0-9]{3}-[0-9]{4}-[0-9]{7}-[0-9]{1}\b',
            r'\b[0-9]{15}\b'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return ""
    
    def extract_name(self, text: str) -> str:
        """Extract name from text"""
        # Simple name extraction - would be enhanced in production
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['name', 'full name']):
                return line.split(':')[-1].strip()
        return ""
    
    def extract_account_holder(self, text: str) -> str:
        """Extract account holder name from bank statement"""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['account holder', 'customer name', 'name']):
                return lines[i + 1] if i + 1 < len(lines) else line
        return ""
    
    def estimate_income_from_bank_statement(self, bank_data: Dict) -> float:
        """Estimate monthly income from bank statement patterns"""
        try:
            transactions = bank_data.get('transactions', [])
            if not transactions:
                return 0.0
            
            # Simple heuristic: look for regular deposits
            deposits = [t for t in transactions if t.get('type') == 'credit' and t.get('amount', 0) > 1000]
            if deposits:
                return sum(t.get('amount', 0) for t in deposits) / len(deposits)
            
            return 0.0
        except:
            return 0.0
    
    def store_application_data(self, application_data: Dict):
        """Store application data in database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO applications 
            (application_id, applicant_data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (
            application_data['applicant_id'],
            json.dumps(application_data),
            datetime.now(),
            datetime.now()
        ))
        self.conn.commit()
    
    def store_document_data(self, application_id: str, doc_type: str, file_path: str, extracted_data: Dict):
        """Store document data in database"""
        cursor = self.conn.cursor()
        doc_id = hashlib.md5(f"{application_id}_{doc_type}".encode()).hexdigest()
        
        cursor.execute('''
            INSERT OR REPLACE INTO documents 
            (doc_id, application_id, doc_type, file_path, extracted_text, processing_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            doc_id,
            application_id,
            doc_type,
            file_path,
            json.dumps(extracted_data),
            'processed'
        ))
        self.conn.commit()
    
    def generate_applicant_id(self) -> str:
        """Generate unique applicant ID"""
        return f"APP{int(datetime.now().timestamp())}{np.random.randint(1000, 9999)}"
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'conn'):
            self.conn.close()