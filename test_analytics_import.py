#!/usr/bin/env python3
import sys
sys.path.insert(0, '/var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com')

try:
    from safedrive.api.v1.endpoints import analytics
    print("✓ Analytics module imported successfully")
    print(f"✓ Router: {analytics.router}")
    print(f"✓ Routes: {len(analytics.router.routes)}")
    for route in analytics.router.routes:
        print(f"  - {route.path} [{','.join(route.methods)}]")
except Exception as e:
    print(f"✗ Error importing analytics: {e}")
    import traceback
    traceback.print_exc()
