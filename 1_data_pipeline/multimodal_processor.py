# 1_data_pipeline/multimodal_processor.py
import pandas as pd
import numpy as np
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import easyocr
import json
from typing import Dict, List, Any
import sqlite3
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

class MultiModalDataProcessor:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])
        self.setup_databases()
    
    def setup_databases(self):
        """Initialize all required databases"""
        # PostgreSQL for structured data
        self.pg_conn = sqlite3.connect('data/applications.db')  # Using SQLite for prototype
        
        # Qdrant for vector storage
        self.qdrant_client = QdrantClient(":memory:")  # In-memory for prototype
        self.qdrant_client.create_collection(
            collection_name="document_embeddings",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        
    def process_application_form(self, form_data: Dict) -> Dict:
        """Process interactive application form data"""
        processed_data = {
            'applicant_id': form_data.get('applicant_id'),
            'personal_info': {
                'name': form_data.get('full_name'),
                'email': form_data.get('email'),
                'phone': form_data.get('phone'),
                'address': form_data.get('address'),
                'date_of_birth': form_data.get('date_of_birth'),
                'nationality': form_data.get('nationality')
            },
            'family_info': {
                'marital_status': form_data.get('marital_status'),
                'family_size': form_data.get('family_size'),
                'dependents': form_data.get('dependents')
            },
            'financial_info': {
                'employment_status': form_data.get('employment_status'),
                'monthly_income': form_data.get('monthly_income'),
                'income_source': form_data.get('income_source'),
                'housing_type': form_data.get('housing_type'),
                'monthly_rent': form_data.get('monthly_rent')
            },
            'education_info': {
                'education_level': form_data.get('education_level'),
                'skills': form_data.get('skills', [])
            }
        }
        return processed_data
    
    def extract_text_from_documents(self, document_path: str, doc_type: str) -> Dict:
        """Extract text from various document types using OCR"""
        extracted_data = {}
        
        try:
            if doc_type == 'emirates_id':
                # Process Emirates ID image
                extracted_text = self.reader.readtext(document_path)
                text_combined = ' '.join([text[1] for text in extracted_text])
                extracted_data = self.parse_emirates_id_text(text_combined)
                
            elif doc_type == 'bank_statement':
                # Process bank statement PDF
                if document_path.endswith('.pdf'):
                    doc = fitz.open(document_path)
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    extracted_data = self.parse_bank_statement_text(text)
                
            elif doc_type == 'credit_report':
                # Process credit report PDF
                doc = fitz.open(document_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                extracted_data = self.parse_credit_report_text(text)
                
            elif doc_type == 'resume':
                # Process resume PDF
                doc = fitz.open(document_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                extracted_data = self.parse_resume_text(text)
                
        except Exception as e:
            print(f"Error processing {doc_type}: {str(e)}")
            extracted_data = {'error': str(e)}
        
        return extracted_data
    
    def process_tabular_data(self, file_path: str) -> Dict:
        """Process Excel files for assets/liabilities"""
        try:
            df = pd.read_excel(file_path)
            processed_data = {
                'total_assets': df.get('total_assets', [0])[0] if 'total_assets' in df.columns else 0,
                'total_liabilities': df.get('total_liabilities', [0])[0] if 'total_liabilities' in df.columns else 0,
                'net_worth': df.get('net_worth', [0])[0] if 'net_worth' in df.columns else 0,
                'assets_breakdown': df.to_dict('records')
            }
            return processed_data
        except Exception as e:
            return {'error': str(e)}
    
    def validate_data_consistency(self, all_extracted_data: Dict) -> Dict:
        """Cross-validate information across all documents"""
        validation_results = {
            'address_consistency': self.check_address_consistency(all_extracted_data),
            'income_consistency': self.check_income_consistency(all_extracted_data),
            'identity_consistency': self.check_identity_consistency(all_extracted_data),
            'family_consistency': self.check_family_consistency(all_extracted_data)
        }
        
        return validation_results
    
    def check_address_consistency(self, data: Dict) -> Dict:
        """Check address consistency across documents"""
        addresses = []
        if 'application_form' in data:
            addresses.append(data['application_form']['personal_info']['address'])
        if 'emirates_id' in data:
            addresses.append(data['emirates_id'].get('address', ''))
        
        consistency_score = len(set(addresses)) == 1 if addresses else False
        return {
            'consistent': consistency_score,
            'addresses_found': addresses,
            'score': 1.0 if consistency_score else 0.0
        }