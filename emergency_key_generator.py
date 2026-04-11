#!/usr/bin/env python3
"""
LeafEngines Emergency API Key Generator
For manual processing of 1,532 waiting developers
"""

import secrets
import datetime
import json
import csv
from typing import Dict, List

class EmergencyKeyGenerator:
    def __init__(self):
        self.keys_generated = []
        
    def generate_key(self, email: str, plan: str, urgency: str) -> Dict:
        """Generate an emergency API key"""
        
        # Create unique key
        key_id = secrets.token_hex(6)
        api_key = f"leaf-emergency-{key_id}"
        
        # Set expiration (7 days for emergency)
        expires = datetime.datetime.now() + datetime.timedelta(days=7)
        
        # Set limits based on plan
        if plan.lower() == "emergency pro" or plan.lower() == "pro":
            calls_limit = 10000
            tier = "emergency_pro"
            amount = 299
        else:  # Emergency Starter
            calls_limit = 5000
            tier = "emergency_starter"
            amount = 149
            
        # Create key record
        key_record = {
            "email": email,
            "api_key": api_key,
            "key_id": key_id,
            "plan": plan,
            "tier": tier,
            "amount": amount,
            "calls_limit": calls_limit,
            "calls_used": 0,
            "created": datetime.datetime.now().isoformat(),
            "expires": expires.isoformat(),
            "urgency": urgency,
            "status": "active",
            "payment_received": False,
            "payment_method": None
        }
        
        self.keys_generated.append(key_record)
        return key_record
    
    def save_to_csv(self, filename: str = "emergency_keys.csv"):
        """Save generated keys to CSV for tracking"""
        if not self.keys_generated:
            print("No keys generated yet")
            return
            
        fieldnames = self.keys_generated[0].keys()
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.keys_generated)
            
        print(f"Saved {len(self.keys_generated)} keys to {filename}")
    
    def save_to_json(self, filename: str = "emergency_keys.json"):
        """Save generated keys to JSON"""
        with open(filename, 'w') as f:
            json.dump(self.keys_generated, f, indent=2)
        print(f"Saved {len(self.keys_generated)} keys to {filename}")
    
    def generate_email_response(self, key_record: Dict) -> str:
        """Generate email response text"""
        return f"""Subject: 🚨 LeafEngines Emergency API Key - {key_record['urgency'].upper()}

Dear Developer,

Thank you for your patience. Here is your emergency API access:

API Key: {key_record['api_key']}
Valid Until: {key_record['expires'][:10]}
API Limit: {key_record['calls_limit']:,} calls
Base URL: https://api.soilsidekickpro.com/v1

Plan: {key_record['plan']}
Amount: ${key_record['amount']}

Payment Methods:
- PayPal: teamclreg@gmail.com
- Cash App: $Sumer54  
- Venmo: @Reginald-Rice
- Bitcoin: 3CRZcQRWznNMKa5XdRMc9j4RBZkkPFFf52
- Ethereum: 0x0dAD616c5892b55486f1132ef2BFf7128cd27414

Please include note: "LeafEngines API - {key_record['email']}"

Documentation: https://soilsidekickpro.com/docs

We're building the automated system now. This key gives you immediate access.

Thank you,
The LeafEngines Team
"""

def main():
    """Interactive key generator"""
    print("🚨 LeafEngines Emergency Key Generator")
    print("=" * 50)
    print("Processing requests from 1,532 waiting developers")
    print()
    
    generator = EmergencyKeyGenerator()
    
    while True:
        print("\n" + "=" * 50)
        print("Enter request details (or 'quit' to exit):")
        
        email = input("Email: ").strip()
        if email.lower() == 'quit':
            break
            
        print("\nPlan options:")
        print("1. Emergency Pro ($299/month, 10K calls)")
        print("2. Emergency Starter ($149/month, 5K calls)")
        plan_choice = input("Select plan (1 or 2): ").strip()
        
        if plan_choice == '1':
            plan = "Emergency Pro"
        else:
            plan = "Emergency Starter"
            
        print("\nUrgency levels:")
        print("1. CRITICAL (2 hour response)")
        print("2. HIGH (24 hour response)")
        print("3. STANDARD (48 hour response)")
        urgency_choice = input("Select urgency (1, 2, or 3): ").strip()
        
        urgency_map = {'1': 'CRITICAL', '2': 'HIGH', '3': 'STANDARD'}
        urgency = urgency_map.get(urgency_choice, 'STANDARD')
        
        # Generate key
        key_record = generator.generate_key(email, plan, urgency)
        
        print("\n" + "=" * 50)
        print("✅ KEY GENERATED SUCCESSFULLY")
        print(f"Email: {key_record['email']}")
        print(f"API Key: {key_record['api_key']}")
        print(f"Plan: {key_record['plan']}")
        print(f"Expires: {key_record['expires'][:10]}")
        print(f"Limit: {key_record['calls_limit']:,} calls")
        
        # Show email response
        print("\n" + "=" * 50)
        print("EMAIL RESPONSE (copy and send):")
        print("-" * 50)
        print(generator.generate_email_response(key_record))
        print("-" * 50)
        
        # Ask to continue
        cont = input("\nGenerate another key? (y/n): ").strip().lower()
        if cont != 'y':
            break
    
    # Save all generated keys
    if generator.keys_generated:
        generator.save_to_csv()
        generator.save_to_json()
        print(f"\n📊 Total keys generated: {len(generator.keys_generated)}")
        print("Files saved: emergency_keys.csv, emergency_keys.json")

if __name__ == "__main__":
    main()