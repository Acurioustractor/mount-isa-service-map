-- Add fields to support intelligent research discoveries
-- Run this to enhance your existing services table

-- Add research-specific fields if they don't exist
ALTER TABLE services 
ADD COLUMN IF NOT EXISTS data_source VARCHAR(50) DEFAULT 'manual',
ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(3,2) DEFAULT 0.5,
ADD COLUMN IF NOT EXISTS research_metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS discovery_date TIMESTAMP DEFAULT NOW();

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_services_data_source ON services(data_source);
CREATE INDEX IF NOT EXISTS idx_services_confidence ON services(confidence_score);
CREATE INDEX IF NOT EXISTS idx_services_discovery_date ON services(discovery_date);

-- Create a research log table to track discovery sessions
CREATE TABLE IF NOT EXISTS research_sessions (
    id SERIAL PRIMARY KEY,
    research_type VARCHAR(50) NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    services_discovered INTEGER DEFAULT 0,
    services_saved INTEGER DEFAULT 0,
    processing_time_seconds DECIMAL(8,2),
    status VARCHAR(20) DEFAULT 'running',
    metadata JSONB DEFAULT '{}'
);

-- Add comments for documentation
COMMENT ON COLUMN services.data_source IS 'Source of the service data (manual, intelligent_research, etc.)';
COMMENT ON COLUMN services.confidence_score IS 'Confidence score for automatically discovered services (0.0-1.0)';
COMMENT ON COLUMN services.research_metadata IS 'Additional metadata from research process';
COMMENT ON COLUMN services.discovery_date IS 'When this service was first discovered';

COMMENT ON TABLE research_sessions IS 'Log of intelligent research discovery sessions';

-- Show current table structure
\d services;