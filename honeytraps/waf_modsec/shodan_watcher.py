#!/usr/bin/env python3
"""
Shodan Watcher — monitors if the honeypot has been fingerprinted by Shodan
and triggers an automatic persona swap if detected.
"""

import os
import time
import logging
import urllib.request
import urllib.error
import json

logging.basicConfig(
    level=logging.INFO,
    format="[shodan-watcher] %(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

SHODAN_API_KEY     = os.environ.get("SHODAN_API_KEY", "")
POLL_INTERVAL      = int(os.environ.get("SHODAN_POLL_INTERVAL", "300"))  # seconds
PERSONA_SWAP_FILE  = os.environ.get("PERSONA_SWAP_FILE", "/tmp/persona_swap")
PERSONAS_DIR       = os.environ.get("PERSONAS_DIR", "/personas")
CURRENT_PERSONA    = os.environ.get("PERSONA", "generic")

# Keywords in Shodan data that suggest honeypot detection
HONEYPOT_KEYWORDS = [
    "honeypot", "honeynet", "cowrie", "dionaea",
    "opencanary", "glutton", "kippo"
]

PERSONA_ROTATION = ["generic", "wordpress", "drupal"]


def get_public_ip():
    """Get container's public IP via ipify."""
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=10) as r:
            data = json.loads(r.read().decode())
            return data.get("ip", "")
    except Exception as e:
        log.warning(f"Could not get public IP: {e}")
        return ""


def query_shodan(ip):
    """Query Shodan host API for the given IP."""
    if not SHODAN_API_KEY:
        log.warning("SHODAN_API_KEY not set — skipping Shodan check.")
        return None

    url = f"https://api.shodan.io/shodan/host/{ip}?key={SHODAN_API_KEY}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            log.info(f"IP {ip} not yet indexed by Shodan.")
        else:
            log.warning(f"Shodan API error: {e.code}")
        return None
    except Exception as e:
        log.warning(f"Shodan query failed: {e}")
        return None


def is_fingerprinted(shodan_data):
    """
    Returns True if Shodan data suggests honeypot has been
    fingerprinted or revealed.
    """
    if not shodan_data:
        return False

    # Check tags
    tags = shodan_data.get("tags", [])
    if "honeypot" in tags:
        log.warning("Shodan has tagged this host as a honeypot.")
        return True

    # Check banner data for honeypot keywords
    for service in shodan_data.get("data", []):
        banner = service.get("data", "").lower()
        for keyword in HONEYPOT_KEYWORDS:
            if keyword in banner:
                log.warning(f"Honeypot keyword '{keyword}' found in Shodan banner.")
                return True

    return False


def next_persona(current):
    """Pick next persona in rotation, skipping current."""
    available = [p for p in PERSONA_ROTATION
                 if os.path.isdir(os.path.join(PERSONAS_DIR, p)) and p != current]
    if not available:
        available = [p for p in PERSONA_ROTATION
                     if os.path.isdir(os.path.join(PERSONAS_DIR, p))]
    return available[0] if available else current


def trigger_swap(new_persona):
    """Write swap file — modsec_entry.sh watches this file."""
    try:
        with open(PERSONA_SWAP_FILE, "w") as f:
            f.write(new_persona)
        log.info(f"Persona swap triggered -> {new_persona}")
    except Exception as e:
        log.error(f"Failed to write swap file: {e}")


def main():
    if not SHODAN_API_KEY:
        log.warning("SHODAN_API_KEY is not set. Watcher running in passive mode.")

    current = CURRENT_PERSONA
    log.info(f"Shodan watcher started. Current persona: {current}")
    log.info(f"Poll interval: {POLL_INTERVAL}s")

    while True:
        try:
            ip = get_public_ip()
            if not ip:
                log.warning("Could not determine public IP. Skipping this cycle.")
                time.sleep(POLL_INTERVAL)
                continue

            log.info(f"Checking Shodan for IP: {ip}")
            data = query_shodan(ip)

            if is_fingerprinted(data):
                new_persona = next_persona(current)
                log.warning(
                    f"Honeypot fingerprinted! Swapping persona: "
                    f"{current} -> {new_persona}"
                )
                trigger_swap(new_persona)
                current = new_persona
            else:
                log.info("No fingerprinting detected. Persona unchanged.")

        except Exception as e:
            log.error(f"Unexpected error in watcher loop: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
