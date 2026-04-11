#!/usr/bin/env python3
"""
Test the payment endpoint by making a direct HTTP request
"""
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("PAYMENT ENDPOINT TEST")
print("=" * 60)

# Test 1: Import required modules
print("\n[1] Importing required modules...")
try:
    import requests
    print("✓ requests imported")
except ImportError:
    print("✗ requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    from config.settings import settings
    print("✓ settings imported")
except Exception as e:
    print(f"✗ Failed to import settings: {e}")
    sys.exit(1)

# Test 2: Check if FastAPI server is running
print("\n[2] Checking if FastAPI server is running on http://localhost:8000...")
try:
    response = requests.get("http://localhost:8000/", timeout=5)
    print("✓ FastAPI server is running")
except requests.exceptions.ConnectionError:
    print("✗ FastAPI server is NOT running on http://localhost:8000")
    print("   Start the server with: uvicorn main:app --reload")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error connecting to server: {e}")
    sys.exit(1)

# Test 3: Test config endpoint
print("\n[3] Testing /payment/config-test endpoint...")
try:
    response = requests.get("http://localhost:8000/payment/config-test")
    if response.status_code == 200:
        config = response.json()
        print("✓ Config test endpoint working:")
        for key, value in config.items():
            print(f"  {key}: {value}")
    else:
        print(f"✗ Config test endpoint returned {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error calling config test endpoint: {e}")
    sys.exit(1)

# Test 4: Test payment order creation
print("\n[4] Testing /payment/create-razorpay-order endpoint...")
print("  Note: This test requires authentication")

# First, try to get a test token or create a mock request
test_payload = {
    "loan_application_id": "test_loan_123"
}

try:
    response = requests.post(
        "http://localhost:8000/payment/create-razorpay-order",
        json=test_payload,
        timeout=10
    )
    
    if response.status_code == 200:
        order = response.json()
        print("✓ Order created successfully:")
        print(f"  Order ID: {order.get('order_id')}")
        print(f"  Amount: {order.get('amount')} paise (₹{order.get('amount')/100})")
        print(f"  Key ID: {order.get('key_id', 'N/A')[:20]}...")
    elif response.status_code == 401:
        print("⚠ Got 401 Unauthorized (expected without auth token)")
        print(f"  This is normal - authentication required")
        print(f"  Response: {response.json()}")
    elif response.status_code == 500:
        print("✗ Got 500 Internal Server Error")
        print(f"  Response: {response.json()}")
        print("  Check backend console for error details")
        sys.exit(1)
    else:
        print(f"✗ Unexpected status code: {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)
        
except requests.exceptions.Timeout:
    print("✗ Request timed out")
    print("  The server took too long to respond")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error making request: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ PAYMENT ENDPOINT TESTS COMPLETE")
print("=" * 60)
print("\nTo test with authentication:")
print("1. Log in to the frontend")
print("2. Navigate to a loan application")
print("3. Upload documents")
print("4. Click the payment button")
print("5. Check the backend console for debug output")
