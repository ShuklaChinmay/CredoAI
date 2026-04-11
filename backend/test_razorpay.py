#!/usr/bin/env python3
"""
Quick test script to verify Razorpay SDK installation and configuration
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("RAZORPAY SDK TEST SCRIPT")
print("=" * 60)

# Test 1: Import razorpay package
print("\n[1] Testing razorpay package import...")
try:
    import razorpay
    print("✓ razorpay package imported successfully")
    print(f"  Version: {razorpay.__version__ if hasattr(razorpay, '__version__') else 'version info not available'}")
except ImportError as e:
    print(f"✗ Failed to import razorpay: {e}")
    print("  Run: pip install razorpay")
    sys.exit(1)

# Test 2: Load settings
print("\n[2] Loading Razorpay settings from .env...")
try:
    from config.settings import settings
    print("✓ Settings loaded successfully")
except Exception as e:
    print(f"✗ Failed to load settings: {e}")
    sys.exit(1)

# Test 3: Check credentials
print("\n[3] Checking Razorpay credentials...")
if not settings.RAZORPAY_KEY_ID:
    print("✗ RAZORPAY_KEY_ID not set")
    sys.exit(1)
print(f"✓ RAZORPAY_KEY_ID: {settings.RAZORPAY_KEY_ID[:10]}...")

if not settings.RAZORPAY_KEY_SECRET:
    print("✗ RAZORPAY_KEY_SECRET not set")
    sys.exit(1)
print(f"✓ RAZORPAY_KEY_SECRET: {settings.RAZORPAY_KEY_SECRET[:10]}...")

# Test 4: Initialize Razorpay client
print("\n[4] Initializing Razorpay client...")
try:
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
    print("✓ Razorpay client initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize client: {e}")
    sys.exit(1)

# Test 5: Create test order
print("\n[5] Creating test order...")
try:
    test_order = client.order.create({
        "amount": 19900,  # ₹199 in paise
        "currency": "INR",
        "receipt": "test_receipt_001",
        "payment_capture": 1,
    })
    print("✓ Test order created successfully")
    print(f"  Order ID: {test_order['id']}")
    print(f"  Amount: {test_order['amount']} paise")
    print(f"  Status: {test_order['status']}")
except Exception as e:
    print(f"✗ Failed to create test order: {e}")
    import traceback
    print(f"\nFull traceback:")
    print(traceback.format_exc())
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED - Razorpay SDK is working correctly!")
print("=" * 60)
