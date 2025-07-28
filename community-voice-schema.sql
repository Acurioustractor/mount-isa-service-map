-- Community Voice System Database Schema
-- Supporting multi-user access with AI analysis capabilities

-- User management and authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('community', 'service_provider', 'community_leader', 'admin')),
    organization VARCHAR(255),
    cultural_background VARCHAR(100),
    age_group VARCHAR(50),
    location VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Interview recordings and data
CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interviewer_id UUID REFERENCES users(id),
    participant_id UUID REFERENCES users(id), -- NULL if anonymous
    interview_type VARCHAR(100) NOT NULL,
    title VARCHAR(255),
    description TEXT,
    audio_file_path VARCHAR(500),
    transcript TEXT,
    duration_seconds INTEGER,
    location VARCHAR(255),
    is_anonymous BOOLEAN DEFAULT false,
    consent_given BOOLEAN DEFAULT false,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Analysis results storage
CREATE TABLE interview_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id),
    analysis_type VARCHAR(100) NOT NULL,
    analysis_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    processing_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service feedback and ratings
CREATE TABLE service_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id),
    service_id UUID REFERENCES services(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    feedback_category VARCHAR(100),
    is_positive BOOLEAN,
    urgency_level VARCHAR(50) CHECK (urgency_level IN ('low', 'medium', 'high', 'critical')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Identified service gaps
CREATE TABLE service_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gap_title VARCHAR(255) NOT NULL,
    gap_description TEXT,
    service_category VARCHAR(100),
    priority_score DECIMAL(3,2),
    frequency_mentioned INTEGER DEFAULT 1,
    affected_demographics JSONB,
    geographic_area VARCHAR(255),
    status VARCHAR(50) DEFAULT 'identified' CHECK (status IN ('identified', 'under_review', 'in_progress', 'resolved')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Themes and insights extraction
CREATE TABLE community_themes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    theme_name VARCHAR(255) NOT NULL,
    theme_category VARCHAR(100),
    description TEXT,
    sentiment_score DECIMAL(3,2),
    frequency_count INTEGER DEFAULT 1,
    first_identified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_mentioned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trend_direction VARCHAR(50) CHECK (trend_direction IN ('increasing', 'stable', 'decreasing')),
    related_services JSONB
);

-- User access permissions
CREATE TABLE access_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    permission_level VARCHAR(50) NOT NULL CHECK (permission_level IN ('read', 'write', 'admin')),
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Interview tags for categorization
CREATE TABLE interview_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id),
    tag_name VARCHAR(100) NOT NULL,
    tag_category VARCHAR(50),
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics and reporting cache
CREATE TABLE analytics_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    user_role VARCHAR(50),
    organization VARCHAR(255),
    analytics_data JSONB NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_interviews_created_at ON interviews(created_at);
CREATE INDEX idx_interviews_type ON interviews(interview_type);
CREATE INDEX idx_interviews_status ON interviews(status);
CREATE INDEX idx_analysis_interview_id ON interview_analysis(interview_id);
CREATE INDEX idx_analysis_type ON interview_analysis(analysis_type);
CREATE INDEX idx_feedback_service_id ON service_feedback(service_id);
CREATE INDEX idx_feedback_rating ON service_feedback(rating);
CREATE INDEX idx_gaps_priority ON service_gaps(priority_score DESC);
CREATE INDEX idx_gaps_category ON service_gaps(service_category);
CREATE INDEX idx_themes_frequency ON community_themes(frequency_count DESC);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_permissions_user ON access_permissions(user_id);

-- Sample data for development
INSERT INTO users (username, email, password_hash, role, organization, cultural_background, age_group, location) VALUES
('admin', 'admin@mountisa.gov.au', '$2b$12$hashed_password', 'admin', 'Mount Isa City Council', null, '30-45', 'Mount Isa'),
('community_member_1', 'member1@example.com', '$2b$12$hashed_password', 'community', null, 'Aboriginal', '25-35', 'Mount Isa'),
('health_worker', 'health@nwhhs.qld.gov.au', '$2b$12$hashed_password', 'service_provider', 'North West Hospital and Health Service', null, '35-50', 'Mount Isa'),
('elder_leader', 'elder@community.org', '$2b$12$hashed_password', 'community_leader', 'Kalkadoon Community Centre', 'Torres Strait Islander', '55-70', 'Mount Isa');