# infrastructure/init-db.sql
-- Initialize Social Support Database
CREATE DATABASE IF NOT EXISTS social_support;
CREATE DATABASE IF NOT EXISTS langfuse;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Social Support Application Tables
\c social_support;

-- Applications table
CREATE TABLE applications (
    application_id VARCHAR(50) PRIMARY KEY,
    applicant_data JSONB NOT NULL,
    extracted_data JSONB,
    validation_results JSONB,
    eligibility_score DECIMAL(3,2) DEFAULT 0.00,
    decision JSONB,
    status VARCHAR(20) DEFAULT 'submitted',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE documents (
    doc_id VARCHAR(50) PRIMARY KEY,
    application_id VARCHAR(50) REFERENCES applications(application_id),
    doc_type VARCHAR(50) NOT NULL,
    file_path TEXT,
    extracted_text TEXT,
    processing_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Processing logs table
CREATE TABLE processing_logs (
    log_id SERIAL PRIMARY KEY,
    application_id VARCHAR(50) REFERENCES applications(application_id),
    agent_name VARCHAR(100),
    action TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Economic recommendations table
CREATE TABLE economic_recommendations (
    rec_id SERIAL PRIMARY KEY,
    application_id VARCHAR(50) REFERENCES applications(application_id),
    recommendation_type VARCHAR(50),
    recommendation_text TEXT,
    confidence_score DECIMAL(3,2),
    implemented BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System metrics table
CREATE TABLE system_metrics (
    metric_id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_created_at ON applications(created_at);
CREATE INDEX idx_applications_eligibility_score ON applications(eligibility_score);
CREATE INDEX idx_documents_application_id ON documents(application_id);
CREATE INDEX idx_processing_logs_application_id ON processing_logs(application_id);
CREATE INDEX idx_processing_logs_timestamp ON processing_logs(timestamp);
CREATE INDEX idx_recommendations_application_id ON economic_recommendations(application_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to applications table
CREATE TRIGGER update_applications_updated_at 
    BEFORE UPDATE ON applications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert initial data
INSERT INTO system_metrics (metric_name, metric_value) VALUES
('system_version', '{"version": "2.0.0", "deployed_at": "2024-01-01"}'),
('performance_baseline', '{"avg_processing_time": 143.2, "success_rate": 0.95}');

-- Create read-only user for analytics
CREATE USER analytics_user WITH PASSWORD 'analytics_password';
GRANT CONNECT ON DATABASE social_support TO analytics_user;
GRANT USAGE ON SCHEMA public TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;

-- Create admin user
CREATE USER admin_user WITH PASSWORD 'admin_password';
GRANT ALL PRIVILEGES ON DATABASE social_support TO admin_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin_user;