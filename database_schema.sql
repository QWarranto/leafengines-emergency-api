-- LeafEngines PostgreSQL Database Schema
-- Run this after creating PostgreSQL database in Render

-- Enable UUID extension for secure IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===== CORE TABLES =====

-- Customers table (linked to Stripe)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) UNIQUE,
    tier VARCHAR(50) NOT NULL DEFAULT 'free',
    founder_number INTEGER,
    founder_assigned_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Tier-specific limits
    daily_call_limit INTEGER DEFAULT 100,
    requests_per_minute INTEGER DEFAULT 10,
    
    -- Metadata
    channel VARCHAR(50),  -- github, npm, qgis, etc.
    notes TEXT,
    
    CHECK (tier IN ('free', 'starter', 'pro', 'founder_enterprise', 'standard_enterprise'))
);

-- API Keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 hash of API key
    raw_key TEXT NOT NULL,  -- Encrypted raw key (for email delivery)
    tier VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Rate limiting counters (reset daily)
    calls_today INTEGER DEFAULT 0,
    calls_this_minute INTEGER DEFAULT 0,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    last_reset_minute TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions table (linked to Stripe)
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_price_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (status IN ('active', 'canceled', 'unpaid', 'past_due', 'trialing'))
);

-- ===== USAGE TRACKING =====

-- Daily usage logs (for analytics and rate limiting)
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Monthly usage summaries (for billing)
CREATE TABLE monthly_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    year_month CHAR(7) NOT NULL,  -- Format: YYYY-MM
    total_calls INTEGER DEFAULT 0,
    unique_endpoints INTEGER DEFAULT 0,
    average_response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(customer_id, year_month)
);

-- ===== FOUNDER TRACKING =====

-- Founder assignments (first 100 customers)
CREATE TABLE founder_assignments (
    founder_number INTEGER PRIMARY KEY CHECK (founder_number BETWEEN 1 AND 100),
    customer_id UUID UNIQUE NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(255) DEFAULT 'system'
);

-- Founder waitlist (beyond 100)
CREATE TABLE founder_waitlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    channel VARCHAR(50),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notified_at TIMESTAMP WITH TIME ZONE,
    position INTEGER  -- Calculated position in waitlist
);

-- ===== PAYMENT & BILLING =====

-- Payment records (from Stripe)
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    stripe_payment_intent_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_invoice_id VARCHAR(255),
    amount INTEGER NOT NULL,  -- In cents
    currency VARCHAR(3) DEFAULT 'usd',
    status VARCHAR(50) NOT NULL,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (status IN ('succeeded', 'failed', 'processing', 'requires_action'))
);

-- ===== INDEXES FOR PERFORMANCE =====

-- Customers indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_stripe_customer_id ON customers(stripe_customer_id);
CREATE INDEX idx_customers_tier ON customers(tier);
CREATE INDEX idx_customers_founder_number ON customers(founder_number);

-- API Keys indexes
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_customer_id ON api_keys(customer_id);
CREATE INDEX idx_api_keys_last_used ON api_keys(last_used_at);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);

-- Subscriptions indexes
CREATE INDEX idx_subscriptions_customer_id ON subscriptions(customer_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_period_end ON subscriptions(current_period_end);

-- Usage logs indexes
CREATE INDEX idx_usage_logs_api_key_id ON usage_logs(api_key_id);
CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at);
CREATE INDEX idx_usage_logs_endpoint ON usage_logs(endpoint);

-- Monthly usage indexes
CREATE INDEX idx_monthly_usage_customer_id ON monthly_usage(customer_id);
CREATE INDEX idx_monthly_usage_year_month ON monthly_usage(year_month);

-- ===== FUNCTIONS & TRIGGERS =====

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_monthly_usage_updated_at BEFORE UPDATE ON monthly_usage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to get next founder number
CREATE OR REPLACE FUNCTION get_next_founder_number()
RETURNS INTEGER AS $$
DECLARE
    next_number INTEGER;
BEGIN
    SELECT COALESCE(MAX(founder_number), 0) + 1 INTO next_number
    FROM founder_assignments;
    
    IF next_number > 100 THEN
        RETURN NULL;  -- Beyond 100 founders
    END IF;
    
    RETURN next_number;
END;
$$ language 'plpgsql';

-- Function to check rate limits
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_api_key_hash VARCHAR(64),
    p_daily_limit INTEGER,
    p_minute_limit INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
    v_key_record api_keys%ROWTYPE;
    v_current_date DATE := CURRENT_DATE;
    v_current_minute TIMESTAMP := date_trunc('minute', CURRENT_TIMESTAMP);
BEGIN
    -- Get API key record
    SELECT * INTO v_key_record
    FROM api_keys
    WHERE key_hash = p_api_key_hash AND is_active = TRUE;
    
    IF NOT FOUND THEN
        RETURN FALSE;  -- Invalid API key
    END IF;
    
    -- Reset daily counter if new day
    IF v_key_record.last_reset_date < v_current_date THEN
        UPDATE api_keys
        SET calls_today = 0,
            last_reset_date = v_current_date
        WHERE id = v_key_record.id;
        
        v_key_record.calls_today := 0;
    END IF;
    
    -- Reset minute counter if new minute
    IF v_key_record.last_reset_minute < v_current_minute THEN
        UPDATE api_keys
        SET calls_this_minute = 0,
            last_reset_minute = v_current_minute
        WHERE id = v_key_record.id;
        
        v_key_record.calls_this_minute := 0;
    END IF;
    
    -- Check limits
    IF v_key_record.calls_today >= p_daily_limit THEN
        RETURN FALSE;  -- Daily limit exceeded
    END IF;
    
    IF v_key_record.calls_this_minute >= p_minute_limit THEN
        RETURN FALSE;  -- Minute limit exceeded
    END IF;
    
    -- Increment counters
    UPDATE api_keys
    SET calls_today = calls_today + 1,
        calls_this_minute = calls_this_minute + 1,
        last_used_at = CURRENT_TIMESTAMP
    WHERE id = v_key_record.id;
    
    RETURN TRUE;  -- Within limits
END;
$$ language 'plpgsql';

-- ===== INITIAL DATA =====

-- Insert Composio as founder #1 (retroactive)
INSERT INTO customers (email, tier, founder_number, founder_assigned_at, channel, notes)
VALUES (
    'integrations@composio.dev',
    'founder_enterprise',
    1,
    '2026-04-03 02:23:00 UTC',
    'direct_enterprise',
    'Retroactively assigned as first enterprise customer from April 3, 2026'
) ON CONFLICT (email) DO NOTHING;

-- Insert into founder assignments
INSERT INTO founder_assignments (founder_number, customer_id, assigned_by)
SELECT 1, id, 'retroactive_system'
FROM customers 
WHERE email = 'integrations@composio.dev'
ON CONFLICT (founder_number) DO NOTHING;

-- ===== VIEWS FOR REPORTING =====

-- Customer summary view
CREATE VIEW customer_summary AS
SELECT 
    c.email,
    c.tier,
    c.founder_number,
    c.created_at as customer_since,
    s.status as subscription_status,
    s.current_period_end,
    COALESCE(mu.total_calls, 0) as calls_this_month,
    ak.last_used_at as last_api_activity
FROM customers c
LEFT JOIN subscriptions s ON c.id = s.customer_id AND s.status = 'active'
LEFT JOIN monthly_usage mu ON c.id = mu.customer_id 
    AND mu.year_month = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
LEFT JOIN api_keys ak ON c.id = ak.customer_id
ORDER BY c.created_at DESC;

-- Founder status view
CREATE VIEW founder_status AS
SELECT 
    fa.founder_number,
    c.email,
    c.created_at as joined_date,
    c.channel,
    EXTRACT(DAY FROM CURRENT_TIMESTAMP - c.created_at) as days_as_founder
FROM founder_assignments fa
JOIN customers c ON fa.customer_id = c.id
ORDER BY fa.founder_number;

-- ===== COMMENTS =====

COMMENT ON TABLE customers IS 'LeafEngines customers with Stripe integration';
COMMENT ON TABLE api_keys IS 'API keys for customer authentication';
COMMENT ON TABLE subscriptions IS 'Stripe subscription records';
COMMENT ON TABLE usage_logs IS 'API usage tracking for rate limiting and analytics';
COMMENT ON TABLE founder_assignments IS 'First 100 founder customers with lifetime pricing';

-- ===== GRANT PERMISSIONS =====
-- Note: Render handles permissions automatically
-- These would be needed for manual PostgreSQL setup:

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_database_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_database_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_database_user;