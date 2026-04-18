"""
LeafEngines Stripe Webhook Handler
Handles payment events and issues API keys automatically
"""

import stripe
import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# Import billing config
from billing_config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PAYMENT_LINKS

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory store (replace with database in production)
# TODO: Replace with PostgreSQL database
CUSTOMERS = {}
API_KEYS = {}
FOUNDER_COUNT = 0
MAX_FOUNDERS = 100

def generate_api_key(customer_email, tier):
    """Generate a secure API key for customer"""
    import secrets
    import hashlib
    
    # Generate random key
    raw_key = secrets.token_urlsafe(32)
    
    # Hash for storage (never store raw keys)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    # Store mapping
    API_KEYS[key_hash] = {
        "customer_email": customer_email,
        "tier": tier,
        "created_at": datetime.utcnow(),
        "last_used": None,
        "raw_key": raw_key  # Only stored temporarily for email
    }
    
    logger.info(f"Generated API key for {customer_email} (tier: {tier})")
    return raw_key

def assign_founder_number(customer_email):
    """Assign founder number if within first 100"""
    global FOUNDER_COUNT
    
    if FOUNDER_COUNT < MAX_FOUNDERS:
        FOUNDER_COUNT += 1
        founder_number = FOUNDER_COUNT
        
        # Store founder assignment
        if customer_email not in CUSTOMERS:
            CUSTOMERS[customer_email] = {}
        
        CUSTOMERS[customer_email]["founder_number"] = founder_number
        CUSTOMERS[customer_email]["founder_assigned_at"] = datetime.utcnow()
        
        logger.info(f"Assigned founder #{founder_number} to {customer_email}")
        return founder_number
    
    return None

def send_welcome_email(customer_email, api_key, tier, founder_number=None):
    """Send welcome email with API key"""
    # TODO: Implement email sending (SendGrid, SMTP, etc.)
    # For now, log the email that would be sent
    
    tier_info = STRIPE_PAYMENT_LINKS.get(tier, {})
    
    email_content = f"""
    Subject: Welcome to LeafEngines! Your API Key is Ready
    
    Hi there,
    
    Thank you for subscribing to LeafEngines {tier_info.get('name', tier)}!
    
    Your API Key: {api_key}
    
    Tier: {tier_info.get('name', tier)}
    Monthly Calls: {tier_info.get('calls_per_month', 'N/A'):,}
    Requests/Minute: {tier_info.get('requests_per_minute', 'N/A'):,}
    
    {f'🎉 CONGRATULATIONS! You are Founder #{founder_number} 🎉' if founder_number else ''}
    {f'Your price of ${tier_info.get("monthly_usd", 0):,}/month is locked for life!' if founder_number else ''}
    
    Documentation: https://app.soilsidekickpro.com/docs
    API Endpoint: https://leafengines-agricultural-intelligence.onrender.com
    
    Support: https://github.com/QWarranto/leafengines-claude-mcp/issues
    
    Best regards,
    The LeafEngines Team
    """
    
    logger.info(f"Would send welcome email to {customer_email}")
    logger.info(f"API Key: {api_key}")
    logger.info(f"Tier: {tier}")
    if founder_number:
        logger.info(f"Founder #{founder_number}")
    
    # In production, actually send the email here
    # send_email(customer_email, "Welcome to LeafEngines!", email_content)

def handle_checkout_session_completed(session):
    """Handle successful payment"""
    try:
        # Get customer email from session
        customer_email = session.get('customer_details', {}).get('email')
        if not customer_email:
            logger.error("No email in checkout session")
            return
        
        # Get price ID to determine tier
        line_items = stripe.checkout.Session.list_line_items(session['id'], limit=1)
        if not line_items.data:
            logger.error("No line items in session")
            return
        
        price_id = line_items.data[0].price.id
        
        # Determine tier from price ID
        tier = None
        for tier_name, tier_config in STRIPE_PAYMENT_LINKS.items():
            if tier_config.get('price_id') == price_id:
                tier = tier_name
                break
        
        if not tier:
            logger.error(f"Unknown price ID: {price_id}")
            return
        
        # Check if founder eligible
        founder_number = None
        if tier == "founder_enterprise":
            founder_number = assign_founder_number(customer_email)
            if not founder_number:
                # Beyond 100 founders, downgrade to standard enterprise
                tier = "standard_enterprise"
                logger.info(f"Beyond 100 founders, downgrading {customer_email} to standard enterprise")
        
        # Generate API key
        api_key = generate_api_key(customer_email, tier)
        
        # Store customer info
        CUSTOMERS[customer_email] = {
            "tier": tier,
            "stripe_customer_id": session.get('customer'),
            "subscription_id": session.get('subscription'),
            "created_at": datetime.utcnow(),
            "founder_number": founder_number,
            "api_key_hash": hashlib.sha256(api_key.encode()).hexdigest() if api_key else None
        }
        
        # Send welcome email
        send_welcome_email(customer_email, api_key, tier, founder_number)
        
        logger.info(f"Successfully processed payment for {customer_email} (tier: {tier})")
        
    except Exception as e:
        logger.error(f"Error handling checkout session: {str(e)}")
        raise

def handle_customer_subscription_updated(subscription):
    """Handle subscription updates (cancellations, changes)"""
    try:
        customer_id = subscription.get('customer')
        status = subscription.get('status')
        
        # Find customer by Stripe customer ID
        customer_email = None
        for email, info in CUSTOMERS.items():
            if info.get('stripe_customer_id') == customer_id:
                customer_email = email
                break
        
        if not customer_email:
            logger.warning(f"Unknown customer ID: {customer_id}")
            return
        
        if status in ['canceled', 'unpaid', 'past_due']:
            # Subscription ended or payment failed
            # TODO: Disable API key or downgrade to free tier
            logger.info(f"Subscription {status} for {customer_email}")
            
            # Update customer status
            CUSTOMERS[customer_email]['subscription_status'] = status
            CUSTOMERS[customer_email]['updated_at'] = datetime.utcnow()
            
        elif status == 'active':
            # Subscription active or renewed
            CUSTOMERS[customer_email]['subscription_status'] = 'active'
            CUSTOMERS[customer_email]['updated_at'] = datetime.utcnow()
            logger.info(f"Subscription active for {customer_email}")
            
    except Exception as e:
        logger.error(f"Error handling subscription update: {str(e)}")

def create_webhook_app():
    """Create Flask app for webhook handling"""
    app = Flask(__name__)
    
    @app.route('/stripe/webhook', methods=['POST'])
    def webhook():
        # Get webhook data
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            logger.error(f"Invalid payload: {str(e)}")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(f"Invalid signature: {str(e)}")
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Handle the event
        event_type = event['type']
        logger.info(f"Received Stripe event: {event_type}")
        
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            handle_checkout_session_completed(session)
            
        elif event_type == 'customer.subscription.updated':
            subscription = event['data']['object']
            handle_customer_subscription_updated(subscription)
            
        elif event_type == 'customer.subscription.deleted':
            subscription = event['data']['object']
            handle_customer_subscription_updated(subscription)
            
        elif event_type == 'invoice.payment_failed':
            invoice = event['data']['object']
            logger.warning(f"Payment failed for invoice: {invoice.get('id')}")
            
        elif event_type == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            logger.info(f"Payment succeeded for invoice: {invoice.get('id')}")
            
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        return jsonify({'status': 'success'}), 200
    
    @app.route('/stripe/webhook/test', methods=['GET'])
    def test_webhook():
        """Test endpoint to verify webhook is working"""
        return jsonify({
            'status': 'active',
            'founders_count': FOUNDER_COUNT,
            'max_founders': MAX_FOUNDERS,
            'customers_count': len(CUSTOMERS)
        }), 200
    
    return app

# Composio Retroactive Setup Function
def setup_composio_retroactively():
    """Set up Composio as founder #1 retroactively"""
    try:
        customer_email = "integrations@composio.dev"
        
        # Check if already exists
        if customer_email in CUSTOMERS:
            logger.info(f"Composio already exists in system")
            return CUSTOMERS[customer_email]
        
        # Assign founder number
        global FOUNDER_COUNT
        if FOUNDER_COUNT < MAX_FOUNDERS:
            FOUNDER_COUNT += 1
            founder_number = FOUNDER_COUNT
        else:
            founder_number = None
        
        # Generate API key
        api_key = generate_api_key(customer_email, "founder_enterprise")
        
        # Store customer info
        CUSTOMERS[customer_email] = {
            "tier": "founder_enterprise",
            "stripe_customer_id": "composio_retroactive",  # Placeholder
            "subscription_id": "composio_retroactive_sub",
            "created_at": datetime(2026, 4, 3, 2, 23, 0),  # April 3, 02:23 UTC
            "founder_number": founder_number,
            "api_key_hash": hashlib.sha256(api_key.encode()).hexdigest() if api_key else None,
            "notes": "Retroactively setup from April 3 enterprise key request"
        }
        
        # Send welcome email
        send_welcome_email(customer_email, api_key, "founder_enterprise", founder_number)
        
        logger.info(f"Retroactively setup Composio as founder #{founder_number}")
        
        return CUSTOMERS[customer_email]
        
    except Exception as e:
        logger.error(f"Error setting up Composio retroactively: {str(e)}")
        return None

# For standalone testing
if __name__ == '__main__':
    import hashlib  # Import here for the hash function
    
    # Test the webhook handler
    app = create_webhook_app()
    
    # Setup Composio retroactively
    print("Setting up Composio retroactively...")
    composio_info = setup_composio_retroactively()
    if composio_info:
        print(f"Composio setup: {composio_info}")
    
    print(f"Founder count: {FOUNDER_COUNT}/{MAX_FOUNDERS}")
    print(f"Total customers: {len(CUSTOMERS)}")
    
    # Run the webhook server (for testing)
    print("Starting webhook server on port 5002...")
    app.run(port=5002, debug=True)