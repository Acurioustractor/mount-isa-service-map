-- Mount Isa Service Map - Scraping System Integration Schema Extensions

-- Add new columns to existing services table for scraping integration
ALTER TABLE services ADD COLUMN IF NOT EXISTS validation_score DECIMAL(3,2);
ALTER TABLE services ADD COLUMN IF NOT EXISTS last_validated TIMESTAMP;
ALTER TABLE services ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50);
ALTER TABLE services ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(3,2);
ALTER TABLE services ADD COLUMN IF NOT EXISTS needs_validation BOOLEAN DEFAULT false;
ALTER TABLE services ADD COLUMN IF NOT EXISTS reviewer_notes TEXT;
ALTER TABLE services ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
ALTER TABLE services ADD COLUMN IF NOT EXISTS validation_notes TEXT;

-- Service validations tracking table
CREATE TABLE IF NOT EXISTS service_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    task_id VARCHAR(255) NOT NULL, -- Reference to Python validation system task
    validation_score DECIMAL(3,2),
    validation_summary JSONB,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Discovery tasks tracking table
CREATE TABLE IF NOT EXISTS discovery_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) NOT NULL, -- Reference to Python discovery system task
    url TEXT NOT NULL,
    max_depth INTEGER DEFAULT 2,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    services_found INTEGER DEFAULT 0,
    services_integrated INTEGER DEFAULT 0,
    processing_time DECIMAL(6,3),
    error_message TEXT,
    submitted_by UUID REFERENCES admin_users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Discovered services pending review
CREATE TABLE IF NOT EXISTS discovered_services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discovery_task_id UUID REFERENCES discovery_tasks(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    address TEXT,
    suburb VARCHAR(100),
    postcode VARCHAR(10),
    state VARCHAR(10) DEFAULT 'QLD',
    operating_hours TEXT,
    services_offered TEXT[],
    source_url TEXT,
    extraction_method VARCHAR(50),
    confidence_score DECIMAL(3,2),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'integrated'
    integrated_service_id UUID REFERENCES services(id),
    reviewer_id UUID REFERENCES admin_users(id),
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP
);

-- Scraping system configuration
CREATE TABLE IF NOT EXISTS scraping_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    updated_by UUID REFERENCES admin_users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent monitoring logs
CREATE TABLE IF NOT EXISTS agent_monitoring (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(255),
    agent_type VARCHAR(50), -- 'discovery', 'validation'
    status VARCHAR(50),
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    last_heartbeat TIMESTAMP,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service data quality scores
CREATE TABLE IF NOT EXISTS service_quality_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    completeness_score DECIMAL(3,2), -- How complete is the service information
    accuracy_score DECIMAL(3,2), -- How accurate is the information
    freshness_score DECIMAL(3,2), -- How recent is the information
    validation_score DECIMAL(3,2), -- Automated validation score
    overall_score DECIMAL(3,2), -- Weighted overall quality score
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- URL crawl queue for systematic discovery
CREATE TABLE IF NOT EXISTS crawl_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    domain VARCHAR(255),
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
    max_depth INTEGER DEFAULT 2,
    scheduled_for TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'queued', -- 'queued', 'processing', 'completed', 'failed', 'skipped'
    last_crawled TIMESTAMP,
    crawl_frequency_days INTEGER DEFAULT 30, -- How often to re-crawl
    added_by UUID REFERENCES admin_users(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Validation rules configuration
CREATE TABLE IF NOT EXISTS validation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(100) NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'required', 'format', 'range', 'custom'
    rule_pattern TEXT, -- Regex pattern or validation logic
    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    error_message TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System integration logs
CREATE TABLE IF NOT EXISTS integration_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_type VARCHAR(50), -- 'discovery', 'validation', 'sync'
    operation_id VARCHAR(255), -- Reference to external system task/operation
    status VARCHAR(50), -- 'started', 'completed', 'failed'
    details JSONB,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default scraping configuration
INSERT INTO scraping_config (key, value, description) VALUES
('scraping_api_url', 'http://localhost:8000/api/v1', 'Base URL for Python scraping system API'),
('discovery_batch_size', '10', 'Maximum URLs to process in a single discovery batch'),
('validation_threshold', '0.7', 'Minimum validation score for auto-approval'),
('crawl_delay_seconds', '1', 'Delay between HTTP requests during crawling'),
('max_concurrent_discoveries', '3', 'Maximum concurrent discovery tasks'),
('auto_integrate_threshold', '0.9', 'Confidence threshold for automatic service integration')
ON CONFLICT (key) DO NOTHING;

-- Insert default validation rules
INSERT INTO validation_rules (rule_name, field_name, rule_type, rule_pattern, severity, error_message) VALUES
('required_name', 'name', 'required', NULL, 'critical', 'Service name is required'),
('required_description', 'description', 'required', NULL, 'high', 'Service description is required'),
('phone_format', 'phone', 'format', '^(?:\+?61\s?)?(?:\(0[2-9]\)|0[2-9])\s?\d{4}\s?\d{4}$|^(?:\+?61\s?)?4\d{2}\s?\d{3}\s?\d{3}$', 'medium', 'Invalid Australian phone number format'),
('email_format', 'email', 'format', '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 'medium', 'Invalid email address format'),
('website_format', 'website', 'format', '^https?://[^\s<>"{}|\\^`\[\]]+$', 'low', 'Invalid website URL format'),
('postcode_qld', 'postcode', 'format', '^4\d{3}$', 'medium', 'Invalid Queensland postcode format')
ON CONFLICT (rule_name) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_service_validations_service ON service_validations(service_id);
CREATE INDEX IF NOT EXISTS idx_service_validations_task ON service_validations(task_id);
CREATE INDEX IF NOT EXISTS idx_service_validations_status ON service_validations(status);

CREATE INDEX IF NOT EXISTS idx_discovery_tasks_status ON discovery_tasks(status);
CREATE INDEX IF NOT EXISTS idx_discovery_tasks_created ON discovery_tasks(created_at);

CREATE INDEX IF NOT EXISTS idx_discovered_services_status ON discovered_services(status);
CREATE INDEX IF NOT EXISTS idx_discovered_services_task ON discovered_services(discovery_task_id);
CREATE INDEX IF NOT EXISTS idx_discovered_services_integrated ON discovered_services(integrated_service_id);

CREATE INDEX IF NOT EXISTS idx_agent_monitoring_agent ON agent_monitoring(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_monitoring_type ON agent_monitoring(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_monitoring_recorded ON agent_monitoring(recorded_at);

CREATE INDEX IF NOT EXISTS idx_service_quality_service ON service_quality_scores(service_id);
CREATE INDEX IF NOT EXISTS idx_service_quality_overall ON service_quality_scores(overall_score);

CREATE INDEX IF NOT EXISTS idx_crawl_queue_status ON crawl_queue(status);
CREATE INDEX IF NOT EXISTS idx_crawl_queue_scheduled ON crawl_queue(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_crawl_queue_priority ON crawl_queue(priority);

CREATE INDEX IF NOT EXISTS idx_integration_logs_type ON integration_logs(operation_type);
CREATE INDEX IF NOT EXISTS idx_integration_logs_status ON integration_logs(status);
CREATE INDEX IF NOT EXISTS idx_integration_logs_created ON integration_logs(created_at);

-- Add validation score to services for better searching
CREATE INDEX IF NOT EXISTS idx_services_validation_score ON services(validation_score);
CREATE INDEX IF NOT EXISTS idx_services_confidence_score ON services(confidence_score);
CREATE INDEX IF NOT EXISTS idx_services_needs_validation ON services(needs_validation);

-- Update existing services to set default values
UPDATE services SET 
    needs_validation = true,
    validation_score = 0.5
WHERE validation_score IS NULL;