-- Anonymous Session Tracking Schema for LeafEngines API
-- Run this on your PostgreSQL database

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Anonymous sessions table
CREATE TABLE IF NOT EXISTS anonymous_sessions (
    session_id VARCHAR(64) PRIMARY KEY DEFAULT md5(uuid_generate_v4()::text || random()::text),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    first_api_call TIMESTAMP WITH TIME ZONE,
    last_api_call TIMESTAMP WITH TIME ZONE,
    total_calls INTEGER DEFAULT 0,
    platform VARCHAR(32),  -- 'qgis', 'npm', 'clawhub', 'github', 'direct', 'unknown'
    country_code VARCHAR(2),
    user_agent_hash VARCHAR(64),
    ip_hash VARCHAR(64),  -- Hashed IP for privacy
    is_first_session BOOLEAN DEFAULT TRUE,
    session_duration_minutes INTEGER DEFAULT 0
);

-- API usage log table
CREATE TABLE IF NOT EXISTS api_usage_log (
    log_id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(64) REFERENCES anonymous_sessions(session_id),
    endpoint VARCHAR(100),
    method VARCHAR(10),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    response_code INTEGER,
    processing_time_ms INTEGER,
    parameters_hash VARCHAR(64),  -- Anonymous parameter fingerprint
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER
);

-- Platform detection table (for correlating downloads with usage)
CREATE TABLE IF NOT EXISTS platform_correlation (
    correlation_id BIGSERIAL PRIMARY KEY,
    download_source VARCHAR(50),  -- 'qgis', 'npm', 'github', 'clawhub'
    download_timestamp TIMESTAMP WITH TIME ZONE,
    download_country VARCHAR(2),
    first_api_call_timestamp TIMESTAMP WITH TIME ZONE,
    session_id VARCHAR(64) REFERENCES anonymous_sessions(session_id),
    time_to_first_use_minutes INTEGER,
    correlation_score FLOAT  -- 0-1 confidence score
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_created ON anonymous_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_platform ON anonymous_sessions(platform);
CREATE INDEX IF NOT EXISTS idx_sessions_country ON anonymous_sessions(country_code);
CREATE INDEX IF NOT EXISTS idx_usage_session ON api_usage_log(session_id);
CREATE INDEX IF NOT EXISTS idx_usage_endpoint ON api_usage_log(endpoint);
CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON api_usage_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_correlation_download ON platform_correlation(download_timestamp);
CREATE INDEX IF NOT EXISTS idx_correlation_session ON platform_correlation(session_id);

-- Create view for daily usage summary
CREATE OR REPLACE VIEW daily_usage_summary AS
SELECT 
    DATE(timestamp) as usage_date,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(*) as total_calls,
    COUNT(DISTINCT endpoint) as unique_endpoints,
    AVG(processing_time_ms) as avg_response_time,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_calls,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_calls
FROM api_usage_log
GROUP BY DATE(timestamp)
ORDER BY usage_date DESC;

-- Create view for platform adoption analysis
CREATE OR REPLACE VIEW platform_adoption AS
SELECT 
    platform,
    COUNT(DISTINCT session_id) as total_sessions,
    AVG(total_calls) as avg_calls_per_session,
    AVG(session_duration_minutes) as avg_session_duration,
    MIN(created_at) as first_seen,
    MAX(last_api_call) as last_seen
FROM anonymous_sessions
WHERE platform IS NOT NULL
GROUP BY platform
ORDER BY total_sessions DESC;

-- Create view for geographic usage patterns
CREATE OR REPLACE VIEW geographic_usage AS
SELECT 
    country_code,
    COUNT(DISTINCT session_id) as total_sessions,
    COUNT(*) as total_calls,
    AVG(total_calls) as avg_calls_per_session,
    MIN(created_at) as first_seen,
    MAX(last_api_call) as last_seen
FROM anonymous_sessions
WHERE country_code IS NOT NULL
GROUP BY country_code
ORDER BY total_sessions DESC;

-- Insert function for new anonymous session
CREATE OR REPLACE FUNCTION create_anonymous_session(
    p_platform VARCHAR(32),
    p_country_code VARCHAR(2),
    p_user_agent_hash VARCHAR(64),
    p_ip_hash VARCHAR(64)
) RETURNS VARCHAR(64) AS $$
DECLARE
    v_session_id VARCHAR(64);
BEGIN
    -- Generate session ID
    v_session_id := md5(uuid_generate_v4()::text || random()::text || extract(epoch from now())::text);
    
    -- Insert new session
    INSERT INTO anonymous_sessions (
        session_id, 
        platform, 
        country_code, 
        user_agent_hash, 
        ip_hash,
        first_api_call,
        last_api_call
    ) VALUES (
        v_session_id,
        p_platform,
        p_country_code,
        p_user_agent_hash,
        p_ip_hash,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );
    
    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql;

-- Update function for session activity
CREATE OR REPLACE FUNCTION update_session_activity(
    p_session_id VARCHAR(64)
) RETURNS VOID AS $$
BEGIN
    UPDATE anonymous_sessions 
    SET 
        last_api_call = CURRENT_TIMESTAMP,
        total_calls = total_calls + 1,
        session_duration_minutes = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - first_api_call)) / 60
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;