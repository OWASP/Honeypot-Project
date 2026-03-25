
#!/usr/bin/env python3
"""
Shodan Watcher — polls Shodan API and triggers persona container swap
when the honeypot is detected/fingerprinted.
"""

import json
import logging
import os
import subprocess
import time
import urllib.error
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="[shodan-watcher] %(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

SHODAN_API_KEY = os.environ.get("SHODAN_API_KEY", "")
POLL_INTERVAL = int(os.environ.get("SHODAN_POLL_INTERVAL", "300"))
SWAP_SCRIPT = os.environ.get("SWAP_SCRIPT", "/app/scripts/swap_persona.sh")
PERSONAS_ROTATION = ["generic", "wordpress", "drupal"]

HONEYPOT_KEYWORDS = [
    "honeypot",
    "honeynet",
    "cowrie",
    "dionaea",
    "opencanary",
    "glutton",
    "kippo",
]


def get_public_ip() -> str:
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=10) as r:
            return json.loads(r.read().decode()).get("ip", "")
    except Exception as e:
        log.warning(f"Could not get public IP: {e}")
        return ""


def query_shodan(ip: str):
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


def is_fingerprinted(data) -> bool:
    if not data:
        return False

    if "honeypot" in data.get("tags", []):
        log.warning("Shodan tagged this host as honeypot.")
        return True

    for service in data.get("data", []):
        banner = (service.get("data") or "").lower()
        for kw in HONEYPOT_KEYWORDS:
            if kw in banner:
                log.warning(f"Honeypot keyword '{kw}' found in Shodan banner.")
                return True

    return False


def next_persona(current: str) -> str:
    idx = PERSONAS_ROTATION.index(current) if current in PERSONAS_ROTATION else 0
    return PERSONAS_ROTATION[(idx + 1) % len(PERSONAS_ROTATION)]


def swap_persona(new_persona: str) -> None:
    try:
        result = subprocess.run(
            [SWAP_SCRIPT, new_persona],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            log.info(f"Swap to '{new_persona}' succeeded.")
        else:
            log.error(f"Swap failed: {result.stderr.strip()}")
    except Exception as e:
        log.error(f"Failed to run swap script: {e}")


def main() -> None:
    if not SHODAN_API_KEY:
        log.warning("SHODAN_API_KEY not set. Watcher running in passive mode.")

    current = os.environ.get("PERSONA", "generic")
    log.info(f"Shodan watcher started. Current persona: {current}")
    log.info(f"Poll interval: {POLL_INTERVAL}s")

    while True:
        try:
            ip = get_public_ip()
            if not ip:
                log.warning("Could not get public IP. Skipping cycle.")
                time.sleep(POLL_INTERVAL)
                continue

            log.info(f"Checking Shodan for IP: {ip}")
            data = query_shodan(ip)

            if is_fingerprinted(data):
                new = next_persona(current)
                log.warning(f"Fingerprinted! Swapping: {current} -> {new}")
                swap_persona(new)
                current = new
            else:
                log.info("No fingerprinting detected.")
        except Exception as e:
            log.error(f"Unexpected error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
