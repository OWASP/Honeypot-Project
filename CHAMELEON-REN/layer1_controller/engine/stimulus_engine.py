import os
import time
import redis
from flask import Flask, request, Response
import requests

app = Flask(__name__)

print("=======================================", flush=True)
print("🧠 CHAMELEON ROBUST ENGINE ONLINE 🧠", flush=True)
print("=======================================", flush=True)

# ---------------------------------------------------------
# 1. CONNECT TO REDIS (THE 30-MINUTE MEMORY)
# ---------------------------------------------------------
try:
    cache = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    cache.ping()
    print("[*] Successfully connected to Redis cache.", flush=True)
except Exception as e:
    print(f"[!] Error connecting to Redis: {e}", flush=True)

# ---------------------------------------------------------
# 2. CONFIGURATION & RULES
# ---------------------------------------------------------
WAF_URL = "http://waf:8080"
SESSION_TTL = 1800  # 30 minutes in seconds
DEFAULT_PERSONA = "wordpress"

# The "Naughty List" - Known automated hacking tools
MALICIOUS_AGENTS = ["wpscan", "sqlmap", "nikto", "nmap", "curl", "python-requests", "zgrab", "masscan"]

def determine_persona(path, user_agent):
    """Analyzes the URI path and User-Agent to determine the target persona."""
    path = path.lower()
    user_agent = user_agent.lower()

    # Category 3: Scanner Detected via User-Agent
    if any(bot in user_agent for bot in MALICIOUS_AGENTS):
        print("🚨 SCANNER DETECTED via User-Agent! Routing to WordPress...", flush=True)
        return "wordpress"

    # Category 3/4: Targeted Application Probing via Path
    if any(keyword in path for keyword in ["/moodle/", "/login/token.php", "/login/index.php", "mimetex"]):
        return "moodle"

    if any(keyword in path for keyword in ["/web/database/manager", "auth_oauth", ".pdf"]):
        return "odoo"

    if any(keyword in path for keyword in ["/gibbon/", "rubrics_visualise_saveajax.php"]):
        return "gibbon"

    if any(keyword in path for keyword in ["/wp-admin", "/wp-login", "wp-content"]):
        return "wordpress"

    # Category 2: Broad Reconnaissance (The Fallback Rule)
    return DEFAULT_PERSONA

# ---------------------------------------------------------
# 3. THE CORE TRAFFIC ROUTER
# ---------------------------------------------------------
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'])
def proxy(path):
    # Get the attacker's real IP (passed down from Nginx)
    attacker_ip = request.headers.get('X-Real-IP', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')

    # Check Redis to see if this attacker is already locked to a persona
    active_persona = cache.get(attacker_ip)

    if active_persona:
        print(f"[*] SESSION ACTIVE: {attacker_ip} is locked to {active_persona.upper()}. Resetting 30-min timer.", flush=True)
        # Reset the 30-minute countdown timer
        cache.expire(attacker_ip, SESSION_TTL)
    else:
        # Brand new attacker (or their 30 mins expired). Run the rules!
        active_persona = determine_persona(request.path, user_agent)
        print(f"[*] NEW TARGET: {attacker_ip} assigned to {active_persona.upper()}.", flush=True)
        
        # Lock them in the Redis room for 30 minutes
        cache.setex(attacker_ip, SESSION_TTL, active_persona)

    # ---------------------------------------------------------
    # 4. FORWARD TO LAYER 2 (WAF)
    # ---------------------------------------------------------
    # Reconstruct the target URL
    target_url = f"{WAF_URL}/{path}"
    if request.query_string:
        target_url = f"{target_url}?{request.query_string.decode('utf-8')}"

    # Copy headers, but add our secret routing flag for the WAF
    headers = {key: value for (key, value) in request.headers}
    headers['X-Chameleon-Target'] = active_persona

    # ==========================================
    # UPDATE 2: DYNAMIC PERSONA TRACKING
    # ==========================================
    # Format the persona into an executive-friendly label for Logstash
    persona_labels = {
        "moodle": "Moodle VLE (Partial/Weaponization Trap)",
        "gibbon": "Gibbon SIS (Full/Data Trap)",
        "odoo": "Odoo ERP (Full/Data Trap)",
        "wordpress": "WordPress Portal (Full/Data Trap)"
    }
    # Inject the header so Logstash logs the active sticky session, not just the URI
    headers['X-Active-Persona'] = persona_labels.get(active_persona, "Unknown Persona")

    try:
        # Fire the request down to the WAF
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )

        # Exclude certain hop-by-hop headers from the response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for (name, value) in resp.raw.headers.items()
                            if name.lower() not in excluded_headers]

        # Send the WAF's response back to the attacker
        return Response(resp.content, resp.status_code, response_headers)

    except requests.exceptions.RequestException as e:
        print(f"[!] WAF Connection Error: {e}", flush=True)
        return "502 Bad Gateway: Honeypot Core Offline", 502

if __name__ == "__main__":
    # Run the Flask app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
