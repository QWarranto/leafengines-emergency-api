#!/bin/bash
# Final test script for LeafEngines Emergency API

echo "🚀 LeafEngines API Final Test"
echo "============================="

# Default Render URL (update if different)
RENDER_URL="https://leafengines-agricultural-intelligence.onrender.com"

echo ""
echo "📊 Testing endpoints on: $RENDER_URL"
echo ""

# Test 1: Health endpoint
echo "1. Testing /v1/health..."
HEALTH=$(curl -s "$RENDER_URL/v1/health")
if echo "$HEALTH" | grep -q "operational"; then
    echo "✅ Health check PASSED"
    echo "$HEALTH" | jq '.status, .version, .timestamp' 2>/dev/null || echo "$HEALTH"
else
    echo "❌ Health check FAILED"
    echo "$HEALTH"
fi
echo ""

# Test 2: Public monitor
echo "2. Testing /v1/monitor/public..."
MONITOR=$(curl -s "$RENDER_URL/v1/monitor/public")
if echo "$MONITOR" | grep -q "operational"; then
    echo "✅ Monitor PASSED"
    echo "$MONITOR" | jq '.status, .total_requests_24h, .unique_users_24h' 2>/dev/null || echo "$MONITOR"
else
    echo "❌ Monitor FAILED"
    echo "$MONITOR"
fi
echo ""

# Test 3: Test with API key
API_KEY="leaf-test-370df0a2e62e"  # From emergency_keys.csv
echo "3. Testing /v1/soil/analyze with API key: ${API_KEY:0:12}..."
SOIL=$(curl -X POST "$RENDER_URL/v1/soil/analyze" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"location": "Test Farm", "soil_type": "loam"}' \
  -s)
if echo "$SOIL" | grep -q "soil_type"; then
    echo "✅ Soil analysis PASSED"
    echo "$SOIL" | jq '.location, .soil_type, .ph, .calls_remaining' 2>/dev/null || echo "$SOIL"
else
    echo "❌ Soil analysis FAILED"
    echo "$SOIL"
fi
echo ""

# Test 4: Admin stats (should fail without admin token)
echo "4. Testing /v1/admin/stats (should fail without admin token)..."
ADMIN=$(curl -s "$RENDER_URL/v1/admin/stats")
if echo "$ADMIN" | grep -q "Unauthorized"; then
    echo "✅ Admin auth check PASSED (correctly rejected)"
else
    echo "⚠️  Admin check: $ADMIN"
fi
echo ""

echo "🎉 All tests completed!"
echo ""
echo "📋 Next steps:"
echo "1. Share API URL with developers: $RENDER_URL"
echo "2. Update Node-RED/n8n documentation"
echo "3. Announce to Reddit community (1,977 viewers)"
echo "4. Monitor usage: $RENDER_URL/v1/monitor/public"
echo ""
echo "📈 API is now ready for 1,532 waiting developers!"