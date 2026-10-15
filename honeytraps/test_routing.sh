#!/bin/bash
# --- Honeytraps: Persona Reverse-Proxy & Active Deception Test ---

TARGET=${1:-http://localhost:9091}

echo "========================================="
echo "🧪 TESTING HONEYTRAP WAF & PERSONA ROUTING: $TARGET"
echo "========================================="

echo -e "\n[1] Testing Active Honeytrap Lure: /robots.txt (should contain injected Disallow)"
curl -s -i "$TARGET/robots.txt" | head -n 15

echo -e "\n[2] Testing Active Honeytrap Lure: /login.php.bak (should return fake credentials)"
curl -s -i "$TARGET/login.php.bak" | head -n 15

echo -e "\n[3] Testing Active Persona Decoy Endpoint: /wp-login.php"
curl -s -i "$TARGET/wp-login.php" | head -n 15

echo -e "\n[4] Testing Active Persona Decoy Endpoint: /phpmyadmin/index.php"
curl -s -i "$TARGET/phpmyadmin/index.php" | head -n 15

echo -e "\n[5] Testing ModSecurity Honeytrap Alert on Fake Port 8000"
curl -s -i "http://localhost:8000/" | head -n 10

echo -e "\n========================================="
echo "✅ ROUTING TEST FINISHED."
echo "========================================="
