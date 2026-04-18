"""
Anonymous Session Tracking for LeafEngines API
Privacy-first usage analytics without PII
"""

import hashlib
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
import os

logger = logging.getLogger(__name__)

class AnonymousTracker:
    """Privacy-first anonymous session tracking"""
    
    def __init__(self, db_connection_string: Optional[str] = None):
        """
        Initialize anonymous tracker
        
        Args:
            db_connection_string: PostgreSQL connection string
                                  If None, uses DATABASE_URL from environment
        """
        self.db_conn_string = db_connection_string or os.getenv('DATABASE_URL')
        if not self.db_conn_string:
            logger.warning("No database connection string provided. Tracking will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            
        # Platform detection patterns
        self.platform_patterns = {
            'qgis': ['QGIS', 'qgis', 'Qgis'],
            'python': ['python-requests', 'Python', 'python'],
            'node': ['node', 'Node.js', 'axios'],
            'curl': ['curl', 'libcurl'],
            'postman': ['PostmanRuntime'],
            'browser': ['Mozilla', 'Chrome', 'Safari', 'Firefox'],
            'clawhub': ['OpenClaw', 'clawhub'],
            'github': ['GitHub', 'github']
        }
        
    def _get_db_connection(self):
        """Get database connection"""
        if not self.enabled:
            return None
        try:
            conn = psycopg2.connect(self.db_conn_string, cursor_factory=RealDictCursor)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def _hash_string(self, text: str) -> str:
        """Create SHA256 hash of a string (one-way, no PII recovery)"""
        if not text:
            return ''
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def detect_platform(self, user_agent: Optional[str]) -> str:
        """
        Detect platform from user agent without storing PII
        
        Args:
            user_agent: User-Agent header value
            
        Returns:
            Platform identifier or 'unknown'
        """
        if not user_agent:
            return 'unknown'
            
        user_agent_lower = user_agent.lower()
        for platform, patterns in self.platform_patterns.items():
            for pattern in patterns:
                if pattern.lower() in user_agent_lower:
                    return platform
        return 'unknown'
    
    def extract_country_from_ip(self, ip_address: str) -> Optional[str]:
        """
        Extract country code from IP (simplified version)
        In production, use GeoIP database or service
        
        Args:
            ip_address: Client IP address
            
        Returns:
            Country code (2-letter) or None
        """
        # Simplified implementation - in production, use:
        # 1. MaxMind GeoIP database
        # 2. ipapi.co or similar service
        # 3. Cloudflare headers (CF-IPCountry)
        
        # For now, return None to avoid false data
        return None
    
    def create_session_id(self, request) -> str:
        """
        Create anonymous session ID from request data
        
        Args:
            request: Flask request object
            
        Returns:
            Anonymous session ID (hashed, no PII)
        """
        # Collect anonymous fingerprint data
        fingerprint_data = {
            'user_agent_hash': self._hash_string(request.user_agent.string if request.user_agent else ''),
            'ip_hash': self._hash_string(request.remote_addr),
            'accept_language_hash': self._hash_string(request.headers.get('Accept-Language', '')),
            'accept_hash': self._hash_string(request.headers.get('Accept', '')),
            'timestamp': datetime.utcnow().isoformat()[:10]  # Date only for rotation
        }
        
        # Create deterministic but anonymous session ID
        fingerprint_json = json.dumps(fingerprint_data, sort_keys=True)
        session_id = self._hash_string(fingerprint_json)
        
        return session_id
    
    def track_request(self, request, endpoint: str, response_code: int, 
                     processing_time_ms: int, success: bool = True,
                     error_message: Optional[str] = None) -> Optional[str]:
        """
        Track API request anonymously
        
        Args:
            request: Flask request object
            endpoint: API endpoint called
            response_code: HTTP response code
            processing_time_ms: Processing time in milliseconds
            success: Whether the request was successful
            error_message: Error message if any
            
        Returns:
            Session ID if tracking successful, None otherwise
        """
        if not self.enabled:
            return None
            
        try:
            # Get or create session ID
            session_id = self.create_session_id(request)
            
            # Detect platform
            platform = self.detect_platform(request.user_agent.string if request.user_agent else None)
            
            # Extract country (simplified)
            country = self.extract_country_from_ip(request.remote_addr)
            
            # Hash parameters for usage pattern analysis (without values)
            params = {}
            if request.method == 'GET':
                params = request.args.to_dict()
            elif request.method in ['POST', 'PUT', 'PATCH']:
                if request.is_json:
                    params = request.get_json() or {}
                else:
                    params = request.form.to_dict()
            
            # Remove actual values, keep parameter names for pattern analysis
            param_names = list(params.keys())
            params_hash = self._hash_string(json.dumps(sorted(param_names), sort_keys=True))
            
            # Get request/response sizes
            request_size = len(request.data) if request.data else 0
            # Response size would need to be passed separately
            
            conn = self._get_db_connection()
            if not conn:
                return None
                
            with conn.cursor() as cur:
                # Check if session exists
                cur.execute("""
                    SELECT session_id FROM anonymous_sessions 
                    WHERE session_id = %s
                """, (session_id,))
                
                if cur.fetchone():
                    # Update existing session
                    cur.execute("""
                        UPDATE anonymous_sessions 
                        SET 
                            last_api_call = CURRENT_TIMESTAMP,
                            total_calls = total_calls + 1,
                            session_duration_minutes = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - first_api_call)) / 60
                        WHERE session_id = %s
                    """, (session_id,))
                else:
                    # Create new session
                    cur.execute("""
                        INSERT INTO anonymous_sessions (
                            session_id, 
                            platform, 
                            country_code, 
                            user_agent_hash, 
                            ip_hash,
                            first_api_call,
                            last_api_call,
                            total_calls
                        ) VALUES (
                            %s, %s, %s, %s, %s, 
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1
                        )
                    """, (
                        session_id,
                        platform,
                        country,
                        self._hash_string(request.user_agent.string if request.user_agent else ''),
                        self._hash_string(request.remote_addr)
                    ))
                
                # Log the API call
                cur.execute("""
                    INSERT INTO api_usage_log (
                        session_id,
                        endpoint,
                        method,
                        response_code,
                        processing_time_ms,
                        parameters_hash,
                        success,
                        error_message,
                        request_size_bytes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id,
                    endpoint,
                    request.method,
                    response_code,
                    processing_time_ms,
                    params_hash,
                    success,
                    error_message,
                    request_size
                ))
                
                conn.commit()
                
            conn.close()
            return session_id
            
        except Exception as e:
            logger.error(f"Error tracking request: {e}")
            return None
    
    def get_usage_stats(self, days: int = 7) -> Optional[Dict[str, Any]]:
        """
        Get anonymous usage statistics
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with usage statistics or None
        """
        if not self.enabled:
            return None
            
        try:
            conn = self._get_db_connection()
            if not conn:
                return None
                
            with conn.cursor() as cur:
                # Get basic stats
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT session_id) as unique_sessions,
                        COUNT(*) as total_calls,
                        AVG(processing_time_ms) as avg_response_time,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_calls,
                        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_calls
                    FROM api_usage_log 
                    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                """, (days,))
                stats = cur.fetchone()
                
                # Get platform distribution
                cur.execute("""
                    SELECT 
                        platform,
                        COUNT(DISTINCT session_id) as sessions,
                        COUNT(*) as calls
                    FROM anonymous_sessions 
                    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                    AND platform IS NOT NULL
                    GROUP BY platform
                    ORDER BY sessions DESC
                """, (days,))
                platforms = cur.fetchall()
                
                # Get endpoint popularity
                cur.execute("""
                    SELECT 
                        endpoint,
                        COUNT(*) as calls,
                        AVG(processing_time_ms) as avg_time
                    FROM api_usage_log 
                    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                    GROUP BY endpoint
                    ORDER BY calls DESC
                    LIMIT 10
                """, (days,))
                endpoints = cur.fetchall()
                
                # Get daily trend
                cur.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(DISTINCT session_id) as unique_sessions,
                        COUNT(*) as total_calls
                    FROM api_usage_log 
                    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (days,))
                daily_trend = cur.fetchall()
                
            conn.close()
            
            return {
                'stats': dict(stats) if stats else {},
                'platforms': [dict(p) for p in platforms],
                'endpoints': [dict(e) for e in endpoints],
                'daily_trend': [dict(d) for d in daily_trend],
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return None
    
    def correlate_with_downloads(self, download_source: str, download_timestamp: datetime,
                               download_country: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Attempt to correlate downloads with API usage
        
        Args:
            download_source: Source of download ('qgis', 'npm', 'github', 'clawhub')
            download_timestamp: When download occurred
            download_country: Country of download (optional)
            
        Returns:
            Correlation analysis or None
        """
        if not self.enabled:
            return None
            
        try:
            conn = self._get_db_connection()
            if not conn:
                return None
                
            with conn.cursor() as cur:
                # Find sessions that started around download time
                time_window_hours = 24  # Look for sessions within 24 hours of download
                
                cur.execute("""
                    SELECT 
                        s.session_id,
                        s.platform,
                        s.country_code,
                        s.first_api_call,
                        EXTRACT(EPOCH FROM (s.first_api_call - %s)) / 60 as minutes_after_download,
                        COUNT(l.log_id) as total_calls,
                        COUNT(DISTINCT l.endpoint) as unique_endpoints
                    FROM anonymous_sessions s
                    LEFT JOIN api_usage_log l ON s.session_id = l.session_id
                    WHERE s.first_api_call BETWEEN %s - INTERVAL '%s hours' 
                                             AND %s + INTERVAL '%s hours'
                    AND (%s IS NULL OR s.country_code = %s)
                    GROUP BY s.session_id, s.platform, s.country_code, s.first_api_call
                    ORDER BY minutes_after_download
                """, (
                    download_timestamp,
                    download_timestamp, time_window_hours,
                    download_timestamp, time_window_hours,
                    download_country, download_country
                ))
                
                potential_matches = cur.fetchall()
                
                # Store correlation attempt
                for match in potential_matches:
                    match_dict = dict(match)
                    minutes_after = match_dict.get('minutes_after_download', 9999)
                    
                    # Calculate correlation score (simplified)
                    # Closer in time = higher score
                    # Same country = higher score
                    # Platform match = higher score
                    time_score = max(0, 1 - (abs(minutes_after) / (24 * 60)))  # 0-1 based on 24h window
                    country_score = 1.0 if download_country and match_dict.get('country_code') == download_country else 0.5
                    platform_score = 1.0 if match_dict.get('platform') == download_source else 0.3
                    
                    correlation_score = (time_score * 0.4 + country_score * 0.3 + platform_score * 0.3)
                    
                    cur.execute("""
                        INSERT INTO platform_correlation (
                            download_source,
                            download_timestamp,
                            download_country,
                            first_api_call_timestamp,
                            session_id,
                            time_to_first_use_minutes,
                            correlation_score
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        download_source,
                        download_timestamp,
                        download_country,
                        match_dict.get('first_api_call'),
                        match_dict.get('session_id'),
                        minutes_after,
                        correlation_score
                    ))
                
                conn.commit()
                
                # Return correlation analysis
                cur.execute("""
                    SELECT 
                        COUNT(*) as potential_matches,
                        AVG(correlation_score) as avg_confidence,
                        AVG(time_to_first_use_minutes) as avg_time_to_use,
                        COUNT(CASE WHEN correlation_score > 0.7 THEN 1 END) as high_confidence_matches
                    FROM platform_correlation 
                    WHERE download_source = %s 
                    AND download_timestamp = %s
                """, (download_source, download_timestamp))
                
                analysis = cur.fetchone()
                
            conn.close()
            
            return {
                'potential_matches': len(potential_matches),
                'analysis': dict(analysis) if analysis else {},
                'matches': [dict(m) for m in potential_matches[:10]]  # Top 10 matches
            }
            
        except Exception as e:
            logger.error(f"Error correlating downloads: {e}")
            return None