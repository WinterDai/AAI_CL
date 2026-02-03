"""Test script to check registered routes."""

from app import app

print("All registered routes:")
print("=" * 80)
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', ['N/A'])
        print(f"  {route.path:50} {methods}")

print("\n" + "=" * 80)
print(f"Total routes: {len(app.routes)}")
