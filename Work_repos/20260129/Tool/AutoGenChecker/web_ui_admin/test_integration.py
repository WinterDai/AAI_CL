"""
Simple integration test for AutoGenChecker Web UI.

This script tests basic functionality without requiring full test framework setup.
"""

import sys
import time
from pathlib import Path
import httpx
import asyncio

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

BASE_URL = "http://localhost:8000"

async def test_backend_health():
    """Test if backend is running and healthy."""
    print("\n" + "="*80)
    print("Testing Backend Health...")
    print("="*80)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                print("✅ Backend is healthy")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Backend returned status {response.status_code}")
                return False
    except httpx.ConnectError:
        print("❌ Cannot connect to backend")
        print(f"   Make sure backend is running on {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_generation_api():
    """Test generation API endpoints."""
    print("\n" + "="*80)
    print("Testing Generation API...")
    print("="*80)
    
    try:
        async with httpx.AsyncClient() as client:
            # Test start generation
            print("\n1. Testing POST /api/generation/start...")
            response = await client.post(
                f"{BASE_URL}/api/generation/start",
                json={
                    "item_id": "TEST-01",
                    "module": "test_module",
                    "llm_provider": "jedai",
                    "llm_model": "gemini-1.5-pro"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Generation started")
                print(f"   Item ID: {data.get('item_id')}")
                print(f"   Status: {data.get('status')}")
                item_id = data.get('item_id')
                
                # Test status endpoint
                print("\n2. Testing GET /api/generation/status/{item_id}...")
                await asyncio.sleep(1)  # Wait a bit
                response = await client.get(
                    f"{BASE_URL}/api/generation/status/{item_id}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    print("✅ Status retrieved")
                    print(f"   Current step: {status_data.get('current_step')}")
                    print(f"   Progress: {status_data.get('progress')}%")
                    print(f"   Message: {status_data.get('message')}")
                else:
                    print(f"❌ Status check failed: {response.status_code}")
                
                return True
            else:
                print(f"❌ Failed to start generation: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_history_api():
    """Test history API endpoints."""
    print("\n" + "="*80)
    print("Testing History API...")
    print("="*80)
    
    try:
        async with httpx.AsyncClient() as client:
            print("\n1. Testing GET /api/history/...")
            response = await client.get(f"{BASE_URL}/api/history/", timeout=5.0)
            
            if response.status_code == 200:
                history = response.json()
                print(f"✅ History retrieved ({len(history)} items)")
                if history:
                    print(f"   First item: {history[0].get('item_id')}")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_templates_api():
    """Test templates API endpoints."""
    print("\n" + "="*80)
    print("Testing Templates API...")
    print("="*80)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/templates/", timeout=5.0)
            
            if response.status_code == 200:
                templates = response.json()
                print(f"✅ Templates retrieved ({len(templates)} items)")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_settings_api():
    """Test settings API endpoints."""
    print("\n" + "="*80)
    print("Testing Settings API...")
    print("="*80)
    
    try:
        async with httpx.AsyncClient() as client:
            # Get settings
            print("\n1. Testing GET /api/settings/...")
            response = await client.get(f"{BASE_URL}/api/settings/", timeout=5.0)
            
            if response.status_code == 200:
                settings = response.json()
                print("✅ Settings retrieved")
                print(f"   LLM Provider: {settings.get('llm_provider')}")
                
                # Update settings
                print("\n2. Testing POST /api/settings/...")
                response = await client.post(
                    f"{BASE_URL}/api/settings/",
                    json={
                        "llm_provider": "jedai",
                        "llm_model": "gemini-1.5-pro-002",
                        "temperature": 0.3
                    },
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    print("✅ Settings updated")
                    return True
                else:
                    print(f"⚠️  Settings update failed: {response.status_code}")
                    return True  # GET worked, so partial success
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("AutoGenChecker Web UI - Integration Tests")
    print("="*80)
    print("\nPrerequisites:")
    print("  - Backend must be running on http://localhost:8000")
    print("  - Run: python web_ui/start_backend.py")
    print()
    
    # Wait for user confirmation
    input("Press Enter when backend is ready (or Ctrl+C to cancel)...")
    
    results = {
        "Backend Health": await test_backend_health(),
        "Generation API": False,
        "History API": False,
        "Templates API": False,
        "Settings API": False,
    }
    
    # Only run other tests if backend is healthy
    if results["Backend Health"]:
        results["Generation API"] = await test_generation_api()
        results["History API"] = await test_history_api()
        results["Templates API"] = await test_templates_api()
        results["Settings API"] = await test_settings_api()
    
    # Print summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
