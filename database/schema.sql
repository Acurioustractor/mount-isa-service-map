-- Mount Isa Service Map Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Service categories table
CREATE TABLE service_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id UUID REFERENCES service_categories(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Services table
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES service_categories(id),
    address TEXT,
    suburb VARCHAR(100),
    state VARCHAR(10) DEFAULT 'QLD',
    postcode VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    facebook VARCHAR(255),
    twitter VARCHAR(255),
    instagram VARCHAR(255),
    eligibility_criteria TEXT,
    service_hours TEXT,
    availability TEXT,
    cost TEXT,
    referral_required BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service locations table (for services with multiple locations)
CREATE TABLE service_locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    name VARCHAR(255),
    address TEXT,
    suburb VARCHAR(100),
    state VARCHAR(10) DEFAULT 'QLD',
    postcode VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service contacts table
CREATE TABLE service_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    name VARCHAR(255),
    title VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(255),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data sources table (track where information came from)
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service data source mapping
CREATE TABLE service_data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    source_id UUID REFERENCES data_sources(id),
    source_url VARCHAR(255),
    last_scraped TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin users table
CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_super_admin BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(50) NOT NULL,
    record_id UUID,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    user_id UUID REFERENCES admin_users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default categories
INSERT INTO service_categories (name, description) VALUES
('Disability Support', 'Services supporting people with disabilities'),
('Health Services', 'Medical and health-related services'),
('Youth Support', 'Services specifically for young people'),
('Mental Health', 'Mental health and wellbeing services'),
('Housing & Accommodation', 'Housing assistance and accommodation services'),
('Justice & Legal', 'Legal aid and justice services'),
('Education & Training', 'Educational and vocational training services'),
('Emergency Services', 'Emergency response services'),
('Community Support', 'General community support services'),
('Recreation & Activities', 'Sports, arts and recreational activities');

-- Locations table for geographic organization
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- 'suburb', 'community', 'region'
    parent_id UUID REFERENCES locations(id),
    coordinates POINT,
    population INTEGER,
    remoteness_category VARCHAR(50)
);

-- Community interviews main table
CREATE TABLE community_interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID REFERENCES locations(id),
    interviewer_id UUID REFERENCES admin_users(id),
    interview_date TIMESTAMP NOT NULL,
    duration_seconds INTEGER,
    recording_url TEXT,
    recording_type VARCHAR(20), -- 'audio', 'video', 'notes'
    transcript TEXT,
    ai_summary TEXT,
    language VARCHAR(50) DEFAULT 'en',
    participant_count INTEGER DEFAULT 1,
    consent_obtained BOOLEAN DEFAULT true,
    validation_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interview participants (anonymous)
CREATE TABLE interview_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID REFERENCES community_interviews(id),
    demographic_category VARCHAR(100), -- 'youth', 'elder', 'parent', etc
    is_service_user BOOLEAN,
    is_service_provider BOOLEAN
);

-- Master theme categories
CREATE TABLE theme_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES theme_categories(id),
    color_code VARCHAR(7) -- For visualization
);

-- Extracted themes from interviews
CREATE TABLE interview_themes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID REFERENCES community_interviews(id),
    theme_category_id UUID REFERENCES theme_categories(id),
    theme_text TEXT,
    confidence_score DECIMAL(3,2),
    validated_by_community BOOLEAN DEFAULT false
);

-- Service gaps identified
CREATE TABLE identified_gaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_type VARCHAR(255),
    location_id UUID REFERENCES locations(id),
    description TEXT,
    severity_score INTEGER CHECK (severity_score BETWEEN 1 AND 10),
    people_affected_estimate INTEGER,
    first_identified DATE,
    last_mentioned DATE,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'addressed', 'in_progress'
    resolution_notes TEXT
);

-- Link interviews to gaps
CREATE TABLE interview_gap_evidence (
    interview_id UUID REFERENCES community_interviews(id),
    gap_id UUID REFERENCES identified_gaps(id),
    relevant_quote TEXT,
    PRIMARY KEY (interview_id, gap_id)
);

-- Community feedback on playback
CREATE TABLE playback_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID REFERENCES community_interviews(id),
    feedback_type VARCHAR(50), -- 'validation', 'correction', 'addition'
    feedback_text TEXT,
    submitted_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Action items from insights
CREATE TABLE action_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    gap_id UUID REFERENCES identified_gaps(id),
    responsible_organization VARCHAR(255),
    target_date DATE,
    status VARCHAR(50) DEFAULT 'proposed',
    outcome_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_services_category ON services(category_id);
CREATE INDEX idx_services_name ON services(name);
CREATE INDEX idx_services_suburb ON services(suburb);
CREATE INDEX idx_services_active ON services(is_active);
CREATE INDEX idx_service_locations_service ON service_locations(service_id);
CREATE INDEX idx_service_contacts_service ON service_contacts(service_id);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_record ON audit_logs(record_id);

-- Additional indexes for new tables
CREATE INDEX idx_community_interviews_location ON community_interviews(location_id);
CREATE INDEX idx_community_interviews_date ON community_interviews(interview_date);
CREATE INDEX idx_interview_themes_interview ON interview_themes(interview_id);
CREATE INDEX idx_interview_themes_category ON interview_themes(theme_category_id);
CREATE INDEX idx_identified_gaps_location ON identified_gaps(location_id);
CREATE INDEX idx_identified_gaps_status ON identified_gaps(status);
CREATE INDEX idx_action_items_status ON action_items(status);
CREATE INDEX idx_action_items_target_date ON action_items(target_date);
