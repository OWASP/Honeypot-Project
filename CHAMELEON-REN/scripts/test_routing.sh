#!/bin/bash
# --- CHAMELEON-REN: End-to-End Routing & WAF Test ---

# Usage: ./test_routing.sh [TARGET_IP]
# If no IP is provided, it defaults to localhost
TARGET=${1:-http://localhost}

echo "========================================="
echo "🧪 STARTING E2E HONEYPOT TEST AGAINST: $TARGET"
echo "========================================="

echo -e "\n[1] Testing Fallback Route (Category 2) -> Expecting WordPress"
curl -A "Mozilla/5.0 Chrome/120.0" -I $TARGET/

echo -e "\n[2] Testing VLE Probe (Category 3/4) -> Expecting Moodle"
curl -A "Mozilla/5.0 Chrome/120.0" -I $TARGET/moodle/

echo -e "\n[3] Testing ERP Probe (Category 3/4) -> Expecting Odoo"
curl -A "Mozilla/5.0 Chrome/120.0" -I $TARGET/web/database/manager

echo -e "\n[4] Testing SIS Probe (Category 3/4) -> Expecting Gibbon"
curl -A "Mozilla/5.0 Chrome/120.0" -I $TARGET/gibbon/

echo -e "\n[5] Testing WAF Payload Capture (XSS) -> Firing Trap..."
curl -A "Mozilla/5.0 Chrome/120.0" -X POST $TARGET/ -d "<script>alert('E2E_TEST_PAYLOAD')</script>"

echo -e "\n========================================="
echo "✅ TEST SUITE COMPLETE."
echo "Check Layer 4 Telemetry to verify the XSS payload was logged!"
echo "========================================="