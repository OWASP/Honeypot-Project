#!/usr/bin/env python3
"""
Shodan Watcher — polls Shodan API and triggers persona container swap
when the honeypot is detected/fingerprinted.
"""

import os
import time
import logging
import subprocess
import urllib.request
import urllib.error
import json
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format="[shodan-watcher] %(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

SHODAN_API_KEY    = os.environ.get("SHODAN_API_KEY", "")
POLL_INTERVAL     = int(os.environ.get("SHODAN_POLL_INTERVAL", "300"))
SWAP_SCRIPT       = os.environ.get("SWAP_SCRIPT", "/app/scripts/swap_persona.sh")
PERSONAS_ROTATION_RAW = os.environ.get("PERSONAS_ROTATION", "generic,wordpress,drupal")
PERSONAS_ROTATION = [p.strip() for p in PERSONAS_ROTATION_RAW.split(",") if p.strip()]
if not PERSONAS_ROTATION:
    PERSONAS_ROTATION = ["generic", "wordpress", "drupal"]

HONEYPOT_KEYWORDS = [
    "honeypot", "honeynet", "cowrie", "dionaea",
    "opencanary", "glutton", "kippo"
]


def get_public_ip():
    try:
        with urllib.request.urlopen(
            "https://api.ipify.org?format=json", timeout=10
        ) as r:
            return json.loads(r.read().decode()).get("ip", "")
    except Exception as e:
        log.warning(f"Could not get public IP: {e}")
        return ""


def query_shodan(ip):
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


def is_fingerprinted(data):
    if not data:
        return False
    if "honeypot" in data.get("tags", []):
        log.warning("Shodan tagged this host as honeypot.")
        return True
    for service in data.get("data", []):
        banner = service.get("data", "").lower()
        for kw in HONEYPOT_KEYWORDS:
            if kw in banner:
                log.warning(f"Honeypot keyword '{kw}' found in Shodan banner.")
                return True
    return False


def next_persona(current):
    idx = PERSONAS_ROTATION.index(current) if current in PERSONAS_ROTATION else 0
    return PERSONAS_ROTATION[(idx + 1) % len(PERSONAS_ROTATION)]

def stable_persona_for_context(context_key: str) -> str:
    """
    Deterministically choose a persona for the given context.
    This lets Shodan context (hosting/location/org/IP signals) influence persona selection.
    """
    digest = hashlib.sha256((context_key or "").encode("utf-8")).hexdigest()
    idx = int(digest, 16) % len(PERSONAS_ROTATION)
    return PERSONAS_ROTATION[idx]

def context_key_from_shodan(data: dict) -> str:
    """
    Build a stable string from Shodan response fields that tend to correlate with hosting context.
    Defensive: missing fields simply reduce key entropy.
    """
    try:
        loc = data.get("location") or {}
        country = loc.get("country_code") or loc.get("country") or ""
        region = loc.get("region") or ""
        city = loc.get("city") or ""
        org = data.get("org") or ""
        asn = str(data.get("asn") or "")
        hostnames = ",".join(sorted([h for h in (data.get("hostnames") or []) if h])) if data.get("hostnames") else ""

        # Extract lightweight service port markers.
        services = data.get("data") or []
        service_ports = []
        for svc in services[:10]:
            port = svc.get("port")
            if port is not None:
                service_ports.append(str(port))
        service_ports_s = ",".join(sorted(service_ports))

        return "|".join([country, region, city, org, asn, hostnames, service_ports_s])
    except Exception:
        return ""


def swap_persona(new_persona):
    try:
        result = subprocess.run(
            [SWAP_SCRIPT, new_persona],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            log.info(f"Swap to '{new_persona}' succeeded.")
        else:
            log.error(f"Swap failed: {result.stderr}")
    except Exception as e:
        log.error(f"Failed to run swap script: {e}")


def main():
    if not SHODAN_API_KEY:
        log.warning("SHODAN_API_KEY not set. Watcher running in passive mode.")

    current = os.environ.get("PERSONA", PERSONAS_ROTATION[0] if PERSONAS_ROTATION else "generic")
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
                context_key = context_key_from_shodan(data or {})
                chosen = stable_persona_for_context(context_key)
                # Safety net: if chosen equals current (rare), fall back to rotation.
                new = chosen if chosen != current else next_persona(current)
                log.warning(f"Fingerprinted! Swapping: {current} -> {new} (context='{context_key}')")
                swap_persona(new)
                current = new
            else:
                log.info("No fingerprinting detected.")

        except Exception as e:
            log.error(f"Unexpected error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
