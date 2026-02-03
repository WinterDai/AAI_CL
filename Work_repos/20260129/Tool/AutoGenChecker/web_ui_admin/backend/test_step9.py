#!/usr/bin/env python
"""Test script to verify step9_router can be imported and has routes."""

try:
    from api.steps import step9_router
    print("✓ step9_router imported successfully")
    print(f"  Router object: {step9_router}")
    print(f"  Number of routes: {len(step9_router.routes)}")
    print("  Routes:")
    for route in step9_router.routes:
        print(f"    {route.path} - {route.methods}")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()

print("\nNow testing if routes are in the app:")
try:
    from app import app
    step9_routes = [r for r in app.routes if '/step9' in str(r.path)]
    print(f"✓ Found {len(step9_routes)} step9 routes in app")
    for route in step9_routes:
        print(f"    {route.path}")
except Exception as e:
    print(f"✗ App import failed: {e}")
    import traceback
    traceback.print_exc()
