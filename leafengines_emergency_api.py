#!/usr/bin/env python3
"""
LeafEngines Emergency API - Minimal Viable Service
Must be deployed BEFORE issuing any API keys
"""

from flask import Flask, jsonify, request
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

app = Flask(__name__)

# In-memory storage for emergency phase
# In production, use Redis or database
API_KEYS = {}
USAGE_TRACKER = {}

class EmergencyAPI:
    def __init__(self):
        self.base_url = os.getenv('LEAFENGINES_API_URL', 'https://api.soilsidekickpro.com')
        
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate API key and check limits"""
        if api_key not in API_KEYS:
            return None
            
        key_info = API_KEYS[api_key]
        
        # Check if expired
        expires = datetime.fromisoformat(key_info['expires'])
        if datetime.now() > expires:
            return None
            
        # Check usage limits
        usage = USAGE_TRACKER.get(api_key, 0)
        if usage >= key_info['calls_limit']:
            return None
            
        return key_info
    
    def track_usage(self, api_key: str):
        """Track API usage"""
        if api_key not in USAGE_TRACKER:
            USAGE_TRACKER[api_key] = 0
        USAGE_TRACKER[api_key] += 1

api = EmergencyAPI()

@app.route('/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "operational",
        "version": "emergency_1.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/v1/soil/analyze",
            "/v1/crop/recommend", 
            "/v1/health",
            "/v1/auth/validate"
        ],
        "message": "LeafEngines Emergency API - Building while serving"
    })

@app.route('/v1/auth/validate', methods=['POST'])
def validate_key():
    """Validate an API key"""
    data = request.get_json() or {}
    api_key = data.get('api_key') or request.headers.get('X-API-Key')
    
    if not api_key:
        return jsonify({"error": "API key required"}), 400
        
    key_info = api.validate_api_key(api_key)
    if not key_info:
        return jsonify({"error": "Invalid or expired API key"}), 401
        
    return jsonify({
        "valid": True,
        "plan": key_info['plan'],
        "calls_used": USAGE_TRACKER.get(api_key, 0),
        "calls_limit": key_info['calls_limit'],
        "expires": key_info['expires']
    })

@app.route('/v1/soil/analyze', methods=['POST'])
def analyze_soil():
    """Basic soil analysis endpoint"""
    # Validate API key
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({"error": "X-API-Key header required"}), 400
        
    key_info = api.validate_api_key(api_key)
    if not key_info:
        return jsonify({"error": "Invalid API key"}), 401
    
    # Get request data
    data = request.get_json() or {}
    location = data.get('location', 'Unknown')
    soil_type = data.get('soil_type', 'loam')
    
    # Track usage
    api.track_usage(api_key)
    
    # Basic soil analysis (expand with real logic later)
    analysis = {
        "location": location,
        "soil_type": soil_type,
        "ph": 6.8,
        "organic_matter": "medium",
        "nutrients": {
            "nitrogen": "medium",
            "phosphorus": "high", 
            "potassium": "low",
            "calcium": "adequate",
            "magnesium": "adequate"
        },
        "recommendations": [
            "Add potassium fertilizer (0-0-60)",
            "Maintain current nitrogen levels",
            "Consider cover cropping for organic matter"
        ],
        "suitable_crops": ["corn", "soybeans", "wheat", "alfalfa"],
        "analysis_date": datetime.now().isoformat(),
        "api_version": "emergency_1.0",
        "calls_remaining": key_info['calls_limit'] - USAGE_TRACKER.get(api_key, 0)
    }
    
    return jsonify(analysis)

@app.route('/v1/crop/recommend', methods=['POST'])
def recommend_crop():
    """Crop recommendation endpoint"""
    # Validate API key
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({"error": "X-API-Key header required"}), 400
        
    key_info = api.validate_api_key(api_key)
    if not key_info:
        return jsonify({"error": "Invalid API key"}), 401
    
    # Get request data
    data = request.get_json() or {}
    location = data.get('location', 'Unknown')
    soil_ph = data.get('ph', 6.5)
    season = data.get('season', 'summer')
    
    # Track usage
    api.track_usage(api_key)
    
    # Basic crop recommendations
    recommendations = {
        "location": location,
        "soil_ph": soil_ph,
        "season": season,
        "recommended_crops": self._get_crops_for_conditions(soil_ph, season),
        "planting_tips": [
            "Test soil before planting",
            "Rotate crops annually",
            "Consider cover crops for soil health"
        ],
        "analysis_date": datetime.now().isoformat(),
        "api_version": "emergency_1.0",
        "calls_remaining": key_info['calls_limit'] - USAGE_TRACKER.get(api_key, 0)
    }
    
    return jsonify(recommendations)

def _get_crops_for_conditions(self, ph: float, season: str) -> list:
    """Get crops based on conditions"""
    crops = []
    
    if 6.0 <= ph <= 7.0:
        crops.extend(["corn", "soybeans", "wheat"])
    if 5.5 <= ph <= 6.5:
        crops.extend(["potatoes", "blueberries", "strawberries"])
    
    if season == "spring":
        crops.extend(["lettuce", "spinach", "peas"])
    elif season == "summer":
        crops.extend(["tomatoes", "peppers", "cucumbers"])
    elif season == "fall":
        crops.extend(["kale", "broccoli", "carrots"])
    
    return list(set(crops))  # Remove duplicates

@app.route('/v1/admin/load-key', methods=['POST'])
def load_api_key():
    """Admin endpoint to load an API key (for emergency processing)"""
    # Simple authentication for admin
    admin_token = request.headers.get('X-Admin-Token')
    if admin_token != os.getenv('ADMIN_TOKEN', 'emergency_admin_2026'):
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    if not data or 'api_key' not in data:
        return jsonify({"error": "API key data required"}), 400
    
    # Store the key
    API_KEYS[data['api_key']] = {
        'plan': data.get('plan', 'Emergency Starter'),
        'calls_limit': data.get('calls_limit', 5000),
        'expires': data.get('expires', (datetime.now() + timedelta(days=7)).isoformat()),
        'email': data.get('email', ''),
        'created': datetime.now().isoformat()
    }
    
    return jsonify({
        "success": True,
        "message": f"API key loaded for {data.get('email', 'unknown')}",
        "expires": API_KEYS[data['api_key']]['expires'],
        "limit": API_KEYS[data['api_key']]['calls_limit']
    })

@app.route('/v1/admin/stats', methods=['GET'])
def get_stats():
    """Get API statistics (admin only)"""
    admin_token = request.headers.get('X-Admin-Token')
    if admin_token != os.getenv('ADMIN_TOKEN', 'emergency_admin_2026'):
        return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify({
        "total_keys": len(API_KEYS),
        "total_usage": sum(USAGE_TRACKER.values()),
        "active_keys": [k for k, v in API_KEYS.items() 
                       if datetime.now() < datetime.fromisoformat(v['expires'])],
        "usage_by_key": USAGE_TRACKER,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"🚀 Starting LeafEngines Emergency API on port {port}")
    print(f"📊 Endpoints available:")
    print(f"  GET  /v1/health")
    print(f"  POST /v1/soil/analyze")
    print(f"  POST /v1/crop/recommend")
    print(f"  POST /v1/auth/validate")
    print(f"  POST /v1/admin/load-key (admin)")
    print(f"  GET  /v1/admin/stats (admin)")
    print(f"\n🔑 API keys must be loaded via /v1/admin/load-key")
    print(f"🌍 Service must be deployed before issuing keys to developers")
    
    app.run(host='0.0.0.0', port=port, debug=debug)