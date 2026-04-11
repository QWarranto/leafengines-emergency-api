#!/usr/bin/env python3
"""
LeafEngines Emergency Payment Tracker
Track payments from PayPal, Cash App, Venmo
"""

import csv
import json
from datetime import datetime
from typing import Dict, List

class PaymentTracker:
    def __init__(self, keys_file: str = "emergency_keys.csv"):
        self.keys_file = keys_file
        self.payments_file = "emergency_payments.csv"
        self.keys = self.load_keys()
        self.payments = self.load_payments()
        
    def load_keys(self) -> List[Dict]:
        """Load generated keys from CSV"""
        try:
            with open(self.keys_file, 'r') as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            print(f"Warning: {self.keys_file} not found")
            return []
    
    def load_payments(self) -> List[Dict]:
        """Load payment records"""
        try:
            with open(self.payments_file, 'r') as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            return []
    
    def record_payment(self, email: str, amount: float, method: str, 
                      transaction_id: str = "", notes: str = "") -> Dict:
        """Record a payment received"""
        
        # Find the key for this email
        key_record = None
        for key in self.keys:
            if key['email'].lower() == email.lower():
                key_record = key
                break
        
        if not key_record:
            print(f"Warning: No key found for email {email}")
            # Still record payment, might be manual entry
            
        payment = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "amount": amount,
            "method": method,
            "transaction_id": transaction_id,
            "notes": notes,
            "key_assigned": key_record['api_key'] if key_record else "UNKNOWN",
            "status": "verified"
        }
        
        self.payments.append(payment)
        self.save_payments()
        
        # Update key record if found
        if key_record:
            self.update_key_payment(key_record['api_key'], True, method)
        
        return payment
    
    def update_key_payment(self, api_key: str, paid: bool, method: str = None):
        """Update key record with payment status"""
        updated_keys = []
        for key in self.keys:
            if key['api_key'] == api_key:
                key['payment_received'] = str(paid).lower()
                if method:
                    key['payment_method'] = method
            updated_keys.append(key)
        
        # Save updated keys
        with open(self.keys_file, 'w', newline='') as f:
            if updated_keys:
                writer = csv.DictWriter(f, fieldnames=updated_keys[0].keys())
                writer.writeheader()
                writer.writerows(updated_keys)
        
        self.keys = updated_keys
    
    def save_payments(self):
        """Save payment records to CSV"""
        if not self.payments:
            return
            
        with open(self.payments_file, 'w', newline='') as f:
            fieldnames = self.payments[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.payments)
    
    def get_summary(self) -> Dict:
        """Get payment summary"""
        total_received = 0
        pending_keys = 0
        paid_keys = 0
        
        for key in self.keys:
            if key.get('payment_received', 'false').lower() == 'true':
                paid_keys += 1
                try:
                    total_received += float(key.get('amount', 0))
                except ValueError:
                    pass
            else:
                pending_keys += 1
        
        return {
            "total_keys": len(self.keys),
            "paid_keys": paid_keys,
            "pending_keys": pending_keys,
            "total_revenue": total_received,
            "payment_methods": self.get_payment_methods()
        }
    
    def get_payment_methods(self) -> Dict:
        """Count payments by method"""
        methods = {}
        for payment in self.payments:
            method = payment['method']
            methods[method] = methods.get(method, 0) + 1
        return methods
    
    def interactive_add_payment(self):
        """Interactive payment entry"""
        print("💰 LeafEngines Payment Tracker")
        print("=" * 50)
        
        email = input("Customer email: ").strip()
        amount = float(input("Amount ($): ").strip())
        
        print("\nPayment method:")
        print("1. PayPal (teamclreg@gmail.com)")
        print("2. Cash App ($Sumer54)")
        print("3. Venmo (@Reginald-Rice)")
        print("4. Bitcoin (3CRZcQRWznNMKa5XdRMc9j4RBZkkPFFf52)")
        print("5. Ethereum (0x0dAD616c5892b55486f1132ef2BFf7128cd27414)")
        print("6. Other")
        
        method_choice = input("Select method (1-6): ").strip()
        method_map = {
            '1': 'PayPal',
            '2': 'Cash App', 
            '3': 'Venmo',
            '4': 'Bitcoin',
            '5': 'Ethereum',
            '6': 'Other'
        }
        method = method_map.get(method_choice, 'Unknown')
        
        if method == 'Other':
            method = input("Enter method name: ").strip()
        
        transaction_id = input("Transaction ID (optional): ").strip()
        notes = input("Notes (optional): ").strip()
        
        # Record payment
        payment = self.record_payment(
            email=email,
            amount=amount,
            method=method,
            transaction_id=transaction_id,
            notes=notes
        )
        
        print("\n✅ PAYMENT RECORDED")
        print(f"Email: {payment['email']}")
        print(f"Amount: ${payment['amount']}")
        print(f"Method: {payment['method']}")
        print(f"Timestamp: {payment['timestamp']}")
        
        # Show summary
        summary = self.get_summary()
        print("\n📊 CURRENT SUMMARY:")
        print(f"Total Keys: {summary['total_keys']}")
        print(f"Paid Keys: {summary['paid_keys']}")
        print(f"Pending Keys: {summary['pending_keys']}")
        print(f"Total Revenue: ${summary['total_revenue']:,.2f}")
        
        # Ask to continue
        cont = input("\nAdd another payment? (y/n): ").strip().lower()
        if cont == 'y':
            self.interactive_add_payment()

def main():
    """Main interactive interface"""
    tracker = PaymentTracker()
    
    while True:
        print("\n" + "=" * 50)
        print("LeafEngines Emergency Payment System")
        print("=" * 50)
        print("1. Add payment manually")
        print("2. View summary")
        print("3. List all payments")
        print("4. List pending keys (no payment)")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            tracker.interactive_add_payment()
        elif choice == '2':
            summary = tracker.get_summary()
            print("\n📊 PAYMENT SUMMARY")
            print(f"Total API Keys: {summary['total_keys']}")
            print(f"Keys Paid: {summary['paid_keys']}")
            print(f"Keys Pending: {summary['pending_keys']}")
            print(f"Total Revenue: ${summary['total_revenue']:,.2f}")
            print("\nPayment Methods:")
            for method, count in summary['payment_methods'].items():
                print(f"  {method}: {count}")
        elif choice == '3':
            print("\n💰 ALL PAYMENTS")
            for i, payment in enumerate(tracker.payments, 1):
                print(f"{i}. {payment['email']} - ${payment['amount']} via {payment['method']} - {payment['timestamp'][:10]}")
        elif choice == '4':
            print("\n⏳ PENDING KEYS (No Payment)")
            pending_count = 0
            for key in tracker.keys:
                if key.get('payment_received', 'false').lower() != 'true':
                    print(f"• {key['email']} - {key['plan']} - Key: {key['api_key']}")
                    pending_count += 1
            print(f"\nTotal pending: {pending_count}")
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()