#!/bin/bash
# Test script for LeafEngines Emergency API

echo "🚀 LeafEngines API Test Script"
echo "=============================="

# Wait for Render URL input
read -p "Enter your Render URL (e.g., https://leafengines-agricultural-intelligence.onrender.com): " RENDER_URL

if [ -z "$RENDER_URL" ]; then
    echo "❌ No URL provided. Exiting."
    exit 1
fi

echo ""
echo "📊 Testing endpoints on: $RENDER_URL"
echo ""

# Test 1: Health endpoint
echo "1. Testing /v1/health..."
curl -s "$RENDER_URL/v1/health" | jq '.status, .version, .timestamp' 2>/dev/null || curl -s "$RENDER_URL/v1/health"
echo ""

# Test 2: Public monitor
echo "2. Testing /v1/monitor/public..."
curl -s "$RENDER_URL/v1/monitor/public" | jq '.status, .total_requests_24h, .unique_users_24h' 2>/dev/null || curl -s "$RENDER_URL/v1/monitor/public"
echo ""

# Test 3: Test with API key (from emergency_keys.csv)
API_KEY=$(head -2 emergency_keys.csv | tail -1 | cut -d',' -f1)
echo "3. Testing /v1/soil/analyze with API key: ${API_KEY:0:12}..."
curl -X POST "$RENDER_URL/v1/soil/analyze" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"location": "Test Farm", "soil_type": "loam"}' \
  -s | jq '.location, .soil_type, .ph, .calls_remaining' 2>/dev/null || \
  curl -X POST "$RENDER_URL/v1/soil/analyze" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"location": "Test Farm", "soil_type": "loam"}' -s
echo ""

# Test 4: Admin stats (will fail without admin token)
echo "4. Testing /v1/admin/stats (should fail without admin token)..."
curl -s "$RENDER_URL/v1/admin/stats" | jq '.error // "No error"' 2>/dev/null || curl -s "$RENDER_URL/v1/admin/stats"
echo ""

echo "✅ Tests completed!"
echo ""
echo "📋 Next steps:"
echo "1. Check Render dashboard for deployment status"
echo "2. Use /v1/monitor/public to track API usage"
echo "3. Load API keys via /v1/admin/load-key (admin token: emergency_admin_20260405)"
echo "4. Announce to Reddit community (1,977 viewers)"