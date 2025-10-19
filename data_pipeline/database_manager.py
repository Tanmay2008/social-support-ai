# data_pipeline/database_manager.py
import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "data/applications.db"):
        self.db_path = db_path
        self.setup_databases()
    
    def setup_databases(self):
        """Initialize all database connections"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Initialize Qdrant (in-memory for prototype)
        self.qdrant_client = QdrantClient(":memory:")
        
        self.create_tables()
        logger.info("Database connections established")
    
    def create_tables(self):
        """Create all necessary tables"""
        cursor = self.conn.cursor()
        
        tables = {
            'applications': '''
                CREATE TABLE IF NOT EXISTS applications (
                    application_id TEXT PRIMARY KEY,
                    applicant_data TEXT NOT NULL,
                    extracted_data TEXT,
                    validation_results TEXT,
                    eligibility_score REAL DEFAULT 0.0,
                    decision TEXT,
                    status TEXT DEFAULT 'submitted',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'documents': '''
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    application_id TEXT,
                    doc_type TEXT NOT NULL,
                    file_path TEXT,
                    extracted_text TEXT,
                    processing_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications (application_id)
                )
            ''',
            'processing_logs': '''
                CREATE TABLE IF NOT EXISTS processing_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id TEXT,
                    agent_name TEXT,
                    action TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (application_id) REFERENCES applications (application_id)
                )
            ''',
            'economic_recommendations': '''
                CREATE TABLE IF NOT EXISTS economic_recommendations (
                    rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id TEXT,
                    recommendation_type TEXT,
                    recommendation_text TEXT,
                    confidence_score REAL,
                    implemented BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications (application_id)
                )
            '''
        }
        
        for table_name, table_sql in tables.items():
            cursor.execute(table_sql)
        
        self.conn.commit()
        logger.info("Database tables created/verified")
    
    def save_application(self, application_data: Dict) -> str:
        """Save new application to database"""
        cursor = self.conn.cursor()
        application_id = application_data.get('applicant_id')
        
        if not application_id:
            application_id = f"APP{int(datetime.now().timestamp())}"
            application_data['applicant_id'] = application_id
        
        cursor.execute('''
            INSERT INTO applications (application_id, applicant_data, status)
            VALUES (?, ?, ?)
        ''', (application_id, json.dumps(application_data), 'submitted'))
        
        self.conn.commit()
        logger.info(f"Application saved: {application_id}")
        return application_id
    
    def update_application_processing(self, application_id: str, updates: Dict):
        """Update application with processing results"""
        cursor = self.conn.cursor()
        
        update_fields = []
        update_values = []
        
        for field, value in updates.items():
            if field in ['extracted_data', 'validation_results', 'decision']:
                update_fields.append(f"{field} = ?")
                update_values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
            elif field in ['eligibility_score', 'status']:
                update_fields.append(f"{field} = ?")
                update_values.append(value)
        
        update_fields.append("updated_at = ?")
        update_values.append(datetime.now())
        update_values.append(application_id)
        
        query = f'''
            UPDATE applications 
            SET {', '.join(update_fields)}
            WHERE application_id = ?
        '''
        
        cursor.execute(query, update_values)
        self.conn.commit()
        logger.info(f"Application updated: {application_id}")
    
    def get_application(self, application_id: str) -> Optional[Dict]:
        """Retrieve application by ID"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM applications WHERE application_id = ?
        ''', (application_id,))
        
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_application_documents(self, application_id: str) -> List[Dict]:
        """Retrieve all documents for an application"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM documents WHERE application_id = ?
        ''', (application_id,))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def log_processing_step(self, application_id: str, agent_name: str, action: str, metadata: Dict = None):
        """Log processing step for observability"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO processing_logs (application_id, agent_name, action, metadata)
            VALUES (?, ?, ?, ?)
        ''', (application_id, agent_name, action, json.dumps(metadata or {})))
        
        self.conn.commit()
    
    def save_economic_recommendations(self, application_id: str, recommendations: List[Dict]):
        """Save economic support recommendations"""
        cursor = self.conn.cursor()
        
        for rec in recommendations:
            cursor.execute('''
                INSERT INTO economic_recommendations 
                (application_id, recommendation_type, recommendation_text, confidence_score)
                VALUES (?, ?, ?, ?)
            ''', (
                application_id,
                rec.get('type', 'general'),
                rec.get('text', ''),
                rec.get('confidence', 0.5)
            ))
        
        self.conn.commit()
        logger.info(f"Saved {len(recommendations)} recommendations for {application_id}")
    
    def get_application_status(self, application_id: str) -> Dict:
        """Get comprehensive application status"""
        application = self.get_application(application_id)
        if not application:
            return {'error': 'Application not found'}
        
        documents = self.get_application_documents(application_id)
        logs = self.get_processing_logs(application_id)
        recommendations = self.get_economic_recommendations(application_id)
        
        return {
            'application': application,
            'documents': documents,
            'processing_logs': logs,
            'recommendations': recommendations,
            'status_summary': self._generate_status_summary(application, documents)
        }
    
    def get_processing_logs(self, application_id: str) -> List[Dict]:
        """Get processing logs for an application"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM processing_logs 
            WHERE application_id = ? 
            ORDER BY timestamp DESC
        ''', (application_id,))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_economic_recommendations(self, application_id: str) -> List[Dict]:
        """Get economic recommendations for an application"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM economic_recommendations 
            WHERE application_id = ? 
            ORDER BY confidence_score DESC
        ''', (application_id,))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def _row_to_dict(self, row) -> Dict:
        """Convert database row to dictionary"""
        return {key: row[key] for key in row.keys()}
    
    def _generate_status_summary(self, application: Dict, documents: List[Dict]) -> Dict:
        """Generate status summary for application"""
        doc_status = {}
        for doc in documents:
            doc_status[doc['doc_type']] = doc['processing_status']
        
        return {
            'application_status': application.get('status', 'unknown'),
            'document_status': doc_status,
            'eligibility_score': application.get('eligibility_score', 0),
            'decision': application.get('decision', 'pending'),
            'last_updated': application.get('updated_at')
        }
    
    def get_applications_by_status(self, status: str, limit: int = 100) -> List[Dict]:
        """Get applications by status"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM applications 
            WHERE status = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (status, limit))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_application_stats(self) -> Dict:
        """Get application statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total applications
        cursor.execute('SELECT COUNT(*) as total FROM applications')
        stats['total_applications'] = cursor.fetchone()['total']
        
        # Applications by status
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM applications 
            GROUP BY status
        ''')
        stats['applications_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Average processing time (simplified)
        cursor.execute('''
            SELECT AVG(eligibility_score) as avg_score 
            FROM applications 
            WHERE eligibility_score > 0
        ''')
        stats['average_eligibility_score'] = cursor.fetchone()['avg_score'] or 0
        
        return stats
    
    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()