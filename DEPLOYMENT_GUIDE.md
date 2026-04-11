# 🚀 LeafEngines Emergency API Deployment Guide

## **Situation:**
1,532 developers are waiting for API access. We must deploy a working API within 24 hours.

## **Deployment Options:**

### **Option 1: Render (Easiest, Free Tier)**
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - Name: `leafengines-emergency`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn leafengines_emergency_api:app --bind 0.0.0.0:$PORT`
5. Add Environment Variables from `.env`
6. Deploy

### **Option 2: Fly.io (Global, Good Free Tier)**
1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. Login: `flyctl auth login`
3. Launch: `flyctl launch`
4. Follow prompts, use `leafengines-emergency` as app name
5. Deploy: `flyctl deploy`

### **Option 3: Railway (Simple, Good Free Tier)**
1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select repository
4. Auto-detects Python, deploys automatically

### **Option 4: DigitalOcean App Platform ($5/month)**
1. Go to https://cloud.digitalocean.com/apps
2. Create App → GitHub
3. Select repository
4. Configure as Python app
5. Deploy

## **Testing After Deployment:**

```bash
# Test health endpoint
curl https://your-app-url.herokuapp.com/v1/health

# Should return:
# {"status": "operational", "version": "emergency_1.0", ...}
```

## **Loading API Keys:**

After deployment, use the admin endpoint to load keys:

```bash
# Generate a key first
python3 emergency_key_generator.py

# Then load it via admin endpoint
curl -X POST https://your-app-url/v1/admin/load-key \
  -H "X-Admin-Token: emergency_admin_20260405" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "leaf-emergency-abc123",
    "plan": "Emergency Pro",
    "calls_limit": 10000,
    "expires": "2026-04-12T10:00:00",
    "email": "developer@example.com"
  }'
```

## **Next Steps:**

1. **Deploy API** (choose one platform above)
2. **Test endpoints** (confirm they work)
3. **Load test keys** (for pilot users)
4. **Announce to 1,532 developers** (API is ready)
5. **Start accepting payments** (6 methods available)
