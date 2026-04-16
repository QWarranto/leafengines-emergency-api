"""
LeafEngines Unified Billing Configuration
Centralized Stripe configuration for all channels
"""

import os
from datetime import datetime

# Stripe API Key (from environment)
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_...')

# Payment Links for All Channels
STRIPE_PAYMENT_LINKS = {
    # Founder Enterprise - $1,999/month locked for life (first 100)
    "founder_enterprise": {
        "name": "LeafEngines Founder Enterprise",
        "price_id": "price_founder_1999",  # Create in Stripe Dashboard
        "payment_link": "https://buy.stripe.com/eVqaEXfNkajZ6Vk0gmaMU06",  # Enterprise Plan - Founder pricing
        "monthly_usd": 1999,
        "calls_per_month": 500000,
        "requests_per_minute": 5000,
        "white_label": True,
        "support": "standard",
        "founder_benefits": True,
        "max_customers": 100
    },
    
    # Standard Enterprise - $1,999/month (after 100 founders)
    "standard_enterprise": {
        "name": "LeafEngines Enterprise",
        "price_id": "price_standard_1999",
        "payment_link": "https://buy.stripe.com/eVqaEXfNkajZ6Vk0gmaMU06",  # Enterprise Plan - Standard pricing
        "monthly_usd": 1999,
        "calls_per_month": 500000,
        "requests_per_minute": 5000,
        "white_label": True,
        "support": "standard",
        "founder_benefits": False
    },
    
    # Pro Tier - $49/month intro → $149/month after 100 founders
    "pro": {
        "name": "LeafEngines Pro",
        "price_id": "price_pro_49",
        "payment_link": "https://buy.stripe.com/cNi3cv1WuajZcfE7IOaMU03",  # Pro Tier
        "monthly_usd": 49,
        "calls_per_month": 50000,
        "requests_per_minute": 500,
        "white_label": "basic",
        "support": "community",
        "intro_pricing": True,
        "intro_until_founders": 100
    },
    
    # Starter Tier - $10/month intro → $49/month after 100 founders
    "starter": {
        "name": "LeafEngines Starter",
        "price_id": "price_starter_10",
        "payment_link": "https://buy.stripe.com/14A7sL30y8bR2F4fbgaMU02",  # Starter Tier
        "monthly_usd": 10,
        "calls_per_month": 10000,
        "requests_per_minute": 100,
        "white_label": False,
        "support": "community",
        "intro_pricing": True,
        "intro_until_founders": 100
    },
    
    # Agent API Starter - $10/month (alternative naming)
    "agent_api_starter": {
        "name": "LeafEngines Agent API - Starter Plan",
        "price_id": "price_agent_starter_10",
        "payment_link": "https://buy.stripe.com/5kQ6oHcB88bR93s8MSaMU04",
        "monthly_usd": 10,
        "calls_per_month": 10000,
        "requests_per_minute": 100,
        "white_label": False,
        "support": "community",
        "agent_api": True
    },
    
    # Agent API Pro - $49/month (alternative naming)
    "agent_api_pro": {
        "name": "LeafEngines Agent API - Pro Plan",
        "price_id": "price_agent_pro_49",
        "payment_link": "https://buy.stripe.com/14A6oH7gO3VBcfE1kqaMU05",
        "monthly_usd": 49,
        "calls_per_month": 50000,
        "requests_per_minute": 500,
        "white_label": "basic",
        "support": "community",
        "agent_api": True
    },
    
    # Pay-as-you-go Tiers
    "payg_exclusive": {
        "name": "LeafEngines AI Agent API - Exclusive Tier",
        "price_id": "price_payg_exclusive_10",
        "payment_link": "https://buy.stripe.com/6oU4gzbx40Jp6Vk1kqaMU0a",
        "one_time_usd": 10,
        "calls_included": 1000,
        "pay_as_you_go": True
    },
    "payg_proprietary": {
        "name": "LeafEngines AI Agent API - Proprietary Tier",
        "price_id": "price_payg_proprietary_5",
        "payment_link": "https://buy.stripe.com/3cIeVd9oW1NtgvU1kqaMU09",
        "one_time_usd": 5,
        "calls_included": 500,
        "pay_as_you_go": True
    },
    "payg_enhanced": {
        "name": "LeafEngines AI Agent API - Enhanced Tier",
        "price_id": "price_payg_enhanced_1_50",
        "payment_link": "https://buy.stripe.com/7sY28reJg1NtenM8MSaMU0b",
        "one_time_usd": 1.50,
        "calls_included": 150,
        "pay_as_you_go": True
    },
    "payg_commoditized": {
        "name": "LeafEngines AI Agent API - Commoditized Tier",
        "price_id": "price_payg_commoditized_0_50",
        "payment_link": "https://buy.stripe.com/8x2fZh1Wu8bR4Nc9QWaMU08",
        "one_time_usd": 0.50,
        "calls_included": 50,
        "pay_as_you_go": True
    }
        "support": "community",
        "intro_pricing": True,
        "intro_until_founders": 100
    }
}

# Founder Tracking
FOUNDER_CUTOFF = 100  # First 100 customers get founder pricing
FOUNDER_LAUNCH_DATE = datetime(2026, 4, 12)  # Revenue portal launch
FOUNDER_WINDOW_DAYS = 30  # Founder pricing available for 30 days from launch

# API Tier Limits
TIER_LIMITS = {
    "founder_enterprise": {
        "daily_calls": 16666,  # 500,000 / 30
        "minute_calls": 5000,
        "concurrent_requests": 100
    },
    "standard_enterprise": {
        "daily_calls": 16666,
        "minute_calls": 5000,
        "concurrent_requests": 100
    },
    "pro": {
        "daily_calls": 1666,  # 50,000 / 30
        "minute_calls": 500,
        "concurrent_requests": 50
    },
    "starter": {
        "daily_calls": 333,  # 10,000 / 30
        "minute_calls": 100,
        "concurrent_requests": 20
    },
    "free": {
        "daily_calls": 100,
        "minute_calls": 10,
        "concurrent_requests": 5
    }
}

# Channel Configuration
CHANNELS = {
    "github": {
        "name": "GitHub",
        "docs_url": "https://github.com/QWarranto/leafengines-claude-mcp",
        "payment_param": "source=github"
    },
    "npm": {
        "name": "npm",
        "docs_url": "https://www.npmjs.com/package/@ancientwhispers54/leafengines-mcp-server",
        "payment_param": "source=npm"
    },
    "qgis": {
        "name": "QGIS Plugin",
        "docs_url": "https://plugins.qgis.org/plugins/qgis_leafengines/",
        "payment_param": "source=qgis"
    },
    "n8n": {
        "name": "n8n",
        "docs_url": "https://www.npmjs.com/package/n8n-nodes-leafengines",
        "payment_param": "source=n8n"
    },
    "node_red": {
        "name": "Node-RED",
        "docs_url": "https://flows.nodered.org/node/node-red-contrib-leafengines",
        "payment_param": "source=nodered"
    },
    "clawhub": {
        "name": "Clawhub",
        "docs_url": "https://clawhub.ai/skills/leafengines-clawhub-skill",
        "payment_param": "source=clawhub"
    },
    "direct": {
        "name": "Direct API",
        "docs_url": "https://app.soilsidekickpro.com",
        "payment_param": "source=direct"
    }
}

# Utility Functions
def get_payment_link(tier, channel="direct"):
    """Get payment link with channel attribution"""
    base_link = STRIPE_PAYMENT_LINKS[tier]["payment_link"]
    channel_param = CHANNELS.get(channel, {}).get("payment_param", "source=direct")
    return f"{base_link}?{channel_param}"

def is_founder_eligible(created_at):
    """Check if customer qualifies for founder pricing"""
    if not created_at:
        return False
    
    # Within 30 days of launch
    days_since_launch = (created_at - FOUNDER_LAUNCH_DATE).days
    if days_since_launch > FOUNDER_WINDOW_DAYS:
        return False
    
    # Within first 100 founders
    # This will be checked against database count
    return True

def get_tier_limits(tier):
    """Get rate limits for a tier"""
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])

# Composio Special Handling
COMPOSIO_CONFIG = {
    "email": "integrations@composio.dev",
    "enterprise_key_created": datetime(2026, 4, 3, 2, 23, 0),  # April 3, 02:23 UTC
    "channel": "direct",
    "founder_number": 1,  # To be assigned
    "retroactive_setup_required": True
}