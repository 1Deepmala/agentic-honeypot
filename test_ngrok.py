import requests

# PASTE YOUR NGROK URL HERE (from Terminal 2)
NGROK_URL = "https://abc123-def456.ngrok-free.app"  # CHANGE THIS
FULL_URL = f"{NGROK_URL}/api/v1/process"

print(f"🧪 Testing: {FULL_URL}")
print("=" * 50)

try:
    # Test without API key first
    r = requests.post(FULL_URL, timeout=10)
    print(f"Test 1 (no auth): {r.status_code} - {r.text}")
    
    # Test with API key
    headers = {"x-api-key": "test-api-key-123456"}
    r = requests.post(FULL_URL, headers=headers, timeout=10)
    print(f"\nTest 2 (with auth): {r.status_code} - {r.json()}")
    
    if r.status_code == 200:
        print("\n✅ NGROK WORKING!")
        print(f"\nUse in GUVI:")
        print(f"URL: {FULL_URL}")
        print(f"API Key: test-api-key-123456")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("\n💡 Check:")
    print("1. ngrok running? (Terminal 2)")
    print("2. Server running? (Terminal 1)")
    print("3. Correct URL? (from Terminal 2)")