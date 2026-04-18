# Anonymous Session Tracking Deployment Guide

## 🚀 Overview
Privacy-first anonymous session tracking for LeafEngines API that correlates downloads with API usage without collecting PII.

## 📋 Prerequisites

### 1. PostgreSQL Database
```bash
# Create database (if not exists)
createdb leafengines_tracking

# Or via psql
psql -c "CREATE DATABASE leafengines_tracking;"
```

### 2. Environment Variables
Add to your `.env` or Render environment:
```bash
DATABASE_URL=postgresql://username:password@host:port/leafengines_tracking
ADMIN_TOKEN=your_secure_admin_token_here
```

## 🗄️ Database Setup

### Option A: Manual Setup
```bash
# Connect to database
psql leafengines_tracking

# Run schema
\i anonymous_tracking_schema.sql
```

### Option B: Automated Setup (Python)
```python
import psycopg2
import os

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
with conn.cursor() as cur:
    with open('anonymous_tracking_schema.sql', 'r') as f:
        cur.execute(f.read())
    conn.commit()
conn.close()
```

## 🔧 Configuration

### 1. Update API Configuration
The anonymous tracker is automatically initialized in `api.py`:
```python
# Already added to api.py:
try:
    tracker = AnonymousTracker()
    logger.info("Anonymous session tracking enabled")
except Exception as e:
    logger.warning(f"Failed to initialize anonymous tracker: {e}")
    tracker = None
```

### 2. Tracking Behavior
- **Automatic**: All API requests are tracked via `@app.after_request`
- **Anonymous**: No PII collected, only hashed fingerprints
- **Platform Detection**: Auto-detects QGIS, Python, Node.js, browsers, etc.
- **Performance**: Minimal impact (<5ms per request)

## 📊 Usage Statistics Endpoints

### 1. Get Anonymous Usage Stats
```bash
GET /v1/admin/usage-stats?days=7
Headers: X-Admin-Token: your_admin_token
```

**Response:**
```json
{
  "success": true,
  "tracking_enabled": true,
  "stats": {
    "stats": {
      "unique_sessions": 150,
      "total_calls": 1250,
      "avg_response_time": 45.2,
      "successful_calls": 1200,
      "failed_calls": 50
    },
    "platforms": [
      {"platform": "qgis", "sessions": 45, "calls": 320},
      {"platform": "python", "sessions": 32, "calls": 280}
    ],
    "endpoints": [
      {"endpoint": "/v1/soil/analyze", "calls": 650, "avg_time": 52.1},
      {"endpoint": "/v1/crop/recommend", "calls": 450, "avg_time": 38.7}
    ],
    "daily_trend": [
      {"date": "2026-04-11", "unique_sessions": 18, "total_calls": 145}
    ]
  }
}
```

### 2. Correlate Downloads with Usage
```bash
POST /v1/admin/correlate-download
Headers: X-Admin-Token: your_admin_token
Content-Type: application/json

{
  "download_source": "qgis",
  "download_timestamp": "2026-04-18T10:30:00Z",
  "download_country": "US"
}
```

**Response:**
```json
{
  "success": true,
  "correlation": {
    "potential_matches": 8,
    "analysis": {
      "potential_matches": 8,
      "avg_confidence": 0.72,
      "avg_time_to_use": 125.5,
      "high_confidence_matches": 5
    },
    "matches": [
      {
        "session_id": "abc123...",
        "platform": "qgis",
        "country_code": "US",
        "first_api_call": "2026-04-18T11:45:00Z",
        "minutes_after_download": 75,
        "total_calls": 12,
        "unique_endpoints": 3
      }
    ]
  }
}
```

## 🔍 What Gets Tracked (Privacy-First)

### ✅ Tracked (Anonymous):
- Session ID (hashed fingerprint)
- Platform (QGIS, Python, Node.js, etc.)
- Country code (from IP, optional)
- API endpoint usage patterns
- Response times
- Success/failure rates
- Request/response sizes

### ❌ NOT Tracked (PII Protected):
- IP addresses (hashed only)
- User agents (hashed only)
- Email addresses
- Names
- API keys (usage counted, not stored)
- Parameter values (only parameter names hashed)

## 📈 Integration with Existing Systems

### 1. QGIS Plugin Downloads
```python
# After QGIS download spike detection
correlation_data = {
    "download_source": "qgis",
    "download_timestamp": "2026-04-18T14:00:00Z",
    "download_country": "US"
}
# POST to /v1/admin/correlate-download
```

### 2. npm Package Downloads
```python
# After npm download report
correlation_data = {
    "download_source": "npm",
    "download_timestamp": "2026-04-18T09:00:00Z",
    "download_country": None  # npm doesn't provide country
}
```

### 3. GitHub Clones
```python
# After GitHub clone spike
correlation_data = {
    "download_source": "github", 
    "download_timestamp": "2026-04-13T15:30:00Z",
    "download_country": None
}
```

## 🚨 Monitoring & Alerts

### 1. Health Check
```bash
GET /v1/health
```
Includes tracking status in response headers:
```
X-Session-ID: abc123def  # First 8 chars of session ID
```

### 2. Error Monitoring
Check logs for tracking errors:
```bash
grep "Error tracking request" /var/log/leafengines.log
grep "Anonymous session tracking" /var/log/leafengines.log
```

### 3. Performance Impact
Monitor average response time changes:
- Baseline: Track before/after deployment
- Alert threshold: >20ms increase in avg response time

## 🔄 Database Maintenance

### 1. Retention Policy
```sql
-- Keep 90 days of detailed logs
DELETE FROM api_usage_log 
WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days';

-- Keep 180 days of session summaries  
DELETE FROM anonymous_sessions
WHERE last_api_call < CURRENT_TIMESTAMP - INTERVAL '180 days';
```

### 2. Performance Optimization
```sql
-- Monthly vacuum (if not auto-vacuum)
VACUUM ANALYZE api_usage_log;
VACUUM ANALYZE anonymous_sessions;

-- Reindex quarterly
REINDEX TABLE api_usage_log;
REINDEX TABLE anonymous_sessions;
```

### 3. Backup Strategy
```bash
# Daily backup of tracking data
pg_dump -h localhost -U username -d leafengines_tracking \
  -t anonymous_sessions -t api_usage_log -t platform_correlation \
  > tracking_backup_$(date +%Y%m%d).sql
```

## 🐛 Troubleshooting

### Common Issues:

#### 1. Database Connection Failed
```
Error: Anonymous tracking not initialized
```
**Solution:**
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

#### 2. Missing Tables
```
Error: relation "anonymous_sessions" does not exist
```
**Solution:**
```bash
# Run schema
psql $DATABASE_URL -f anonymous_tracking_schema.sql
```

#### 3. Performance Issues
```
Warning: Tracking adding >50ms per request
```
**Solution:**
- Check database indexes
- Monitor connection pooling
- Consider async tracking

#### 4. No Data Appearing
```
Stats always show 0 sessions/calls
```
**Solution:**
- Check `tracker` variable initialization
- Verify `@app.after_request` decorator
- Check for exceptions in logs

## 📊 Analytics Dashboard (Optional)

### Sample Queries for Business Intelligence:

#### 1. User Retention
```sql
SELECT 
    DATE(first_api_call) as cohort_date,
    COUNT(DISTINCT session_id) as new_users,
    COUNT(DISTINCT CASE WHEN last_api_call >= first_api_call + INTERVAL '7 days' 
                   THEN session_id END) as retained_7d,
    COUNT(DISTINCT CASE WHEN last_api_call >= first_api_call + INTERVAL '30 days' 
                   THEN session_id END) as retained_30d
FROM anonymous_sessions
GROUP BY DATE(first_api_call)
ORDER BY cohort_date DESC;
```

#### 2. Platform Adoption Funnel
```sql
SELECT 
    platform,
    COUNT(DISTINCT session_id) as total_sessions,
    AVG(total_calls) as avg_engagement,
    AVG(session_duration_minutes) as avg_session_length,
    COUNT(DISTINCT CASE WHEN total_calls > 10 THEN session_id END) as power_users
FROM anonymous_sessions
WHERE platform IS NOT NULL
GROUP BY platform
ORDER BY total_sessions DESC;
```

#### 3. Geographic Growth
```sql
SELECT 
    country_code,
    COUNT(DISTINCT session_id) as total_sessions,
    COUNT(*) as total_calls,
    MIN(first_api_call) as first_seen,
    MAX(last_api_call) as last_seen
FROM anonymous_sessions
WHERE country_code IS NOT NULL
GROUP BY country_code
ORDER BY total_sessions DESC;
```

## 🚀 Deployment Checklist

- [ ] PostgreSQL database created
- [ ] `DATABASE_URL` environment variable set
- [ ] Schema deployed (`anonymous_tracking_schema.sql`)
- [ ] `psycopg2-binary` added to requirements
- [ ] API restarted with new code
- [ ] Test tracking with sample request
- [ ] Verify `/v1/admin/usage-stats` endpoint
- [ ] Set up correlation for recent downloads
- [ ] Configure retention policies
- [ ] Set up monitoring alerts

## 📞 Support

For issues:
1. Check application logs for tracking errors
2. Verify database connectivity
3. Test with sample correlation data
4. Review privacy compliance requirements

## 🔒 Privacy Compliance

This system is designed for GDPR/CCPA compliance:
- No PII collection
- Right to be forgotten (session deletion available)
- Data minimization principles
- Security by design (hashed identifiers only)