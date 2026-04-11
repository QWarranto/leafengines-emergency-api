#!/usr/bin/env python3
"""
Generate test API keys for monitoring
"""
import csv
import uuid
from datetime import datetime, timedelta

def generate_test_keys(count=10):
    """Generate test API keys"""
    keys = []
    
    test_emails = [
        "test1@leafengines.com",
        "test2@leafengines.com", 
        "test3@leafengines.com",
        "developer@example.com",
        "farmer@test.com",
        "researcher@test.com",
        "student@test.com",
        "startup@test.com",
        "enterprise@test.com",
        "community@test.com"
    ]
    
    plans = ["Free", "Starter", "Pro", "Enterprise"]
    
    for i in range(min(count, len(test_emails))):
        key = {
            "api_key": f"leaf-test-{uuid.uuid4().hex[:12]}",
            "email": test_emails[i],
            "plan": plans[i % len(plans)],
            "calls_limit": [100, 1000, 10000, 100000][i % 4],
            "payment_received": "true" if i < 5 else "false",
            "payment_method": ["PayPal", "Cash App", "Venmo", "Bitcoin", "Ethereum"][i % 5],
            "amount": [0, 149, 499, 999][i % 4],
            "expires": (datetime.now() + timedelta(days=30)).isoformat(),
            "created": datetime.now().isoformat()
        }
        keys.append(key)
    
    # Write to CSV
    with open('emergency_keys.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys[0].keys())
        writer.writeheader()
        writer.writerows(keys)
    
    print(f"✅ Generated {len(keys)} test API keys")
    print(f"📁 Saved to emergency_keys.csv")
    
    # Print sample
    print("\n📋 Sample keys:")
    for i, key in enumerate(keys[:3]):
        print(f"{i+1}. {key['email']} - {key['plan']} - Key: {key['api_key']}")

if __name__ == "__main__":
    generate_test_keys(10)