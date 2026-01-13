#!/bin/bash
# Script to check if the deployed code matches local changes
# Run this on the PRODUCTION SERVER

echo "============================================================"
echo "Checking Deployed Code on Production Server"
echo "============================================================"

# Adjust this path to match your production deployment
PROJECT_DIR="/path/to/drive_africa_api"  # CHANGE THIS!

echo ""
echo "1. Checking api_router.py for require_roles_or_jwt in analytics..."
grep -A 10 "analytics_router" "$PROJECT_DIR/safedrive/api/v1/api_router.py" | grep -E "(require_roles_or_jwt|require_roles)"

echo ""
echo "2. Checking if get_current_client_or_driver is imported in security.py..."
grep "def get_current_client_or_driver" "$PROJECT_DIR/safedrive/core/security.py"

echo ""
echo "3. Checking analytics.py for require_roles_or_jwt import..."
grep "require_roles_or_jwt" "$PROJECT_DIR/safedrive/api/v1/endpoints/analytics.py" | head -1

echo ""
echo "4. Checking auth.py for get_current_client_or_driver..."
grep "get_current_client_or_driver" "$PROJECT_DIR/safedrive/api/v1/endpoints/auth.py"

echo ""
echo "5. Git status and last commit..."
cd "$PROJECT_DIR"
git log -1 --oneline
git status

echo ""
echo "6. Checking for __pycache__ directories (should be minimal)..."
find "$PROJECT_DIR/safedrive" -name __pycache__ -type d | wc -l

echo ""
echo "============================================================"
echo "Done!"
echo "============================================================"
