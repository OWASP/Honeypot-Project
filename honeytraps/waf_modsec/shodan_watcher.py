#!/usr/bin/env python3
"""
Shodan watcher: poll Shodan (or a local fixture), log host summary, append
JSONL events, optionally POST a webhook or run a hook script for external
orchestration (EIP/region changes, etc.).

Persona swaps remain in-container; infra actions belong in the hook/webhook.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="[shodan-watcher] %(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

SHODAN_API_KEY = os.environ.get("SHODAN_API_KEY", "").strip()
POLL_INTERVAL = int(os.environ.get("SHODAN_POLL_INTERVAL", "300"))
SWAP_SCRIPT = os.environ.get("SWAP_SCRIPT", "/app/scripts/swap_persona.sh")
SHODAN_PERSONAS_RAW = os.environ.get("SHODAN_PERSONAS", "generic,wordpress,drupal")
SHODAN_EVENTS_JSONL = os.environ.get("SHODAN_EVENTS_JSONL", "/tmp/shodan_events.jsonl")
SHODAN_WEBHOOK_URL = os.environ.get("SHODAN_WEBHOOK_URL", "").strip()
SHODAN_HOOK_SCRIPT = os.environ.get("SHODAN_HOOK_SCRIPT", "").strip()
SHODAN_FIXTURE_FILE = os.environ.get("SHODAN_FIXTURE_FILE", "").strip()
SHODAN_TEST_PUBLIC_IP = os.environ.get("SHODAN_TEST_PUBLIC_IP", "").strip()
SHODAN_SINGLE_SHOT = os.environ.get("SHODAN_SINGLE_SHOT", "").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)

HONEYPOT_KEYWORDS = [
    "honeypot",
    "honeynet",
    "cowrie",
    "dionaea",
    "opencanary",
    "glutton",
    "kippo",
]


def personas_rotation() -> list[str]:
    parts = [p.strip() for p in SHODAN_PERSONAS_RAW.split(",")]
    return [p for p in parts if p]


def summarize_host(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    ip = data.get("ip_str") or data.get("ip")
    return {
        "ip": ip,
        "hostnames": data.get("hostnames") or [],
        "country_name": data.get("country_name"),
        "country_code": data.get("country_code"),
        "city": data.get("city"),
        "org": data.get("org"),
        "asn": data.get("asn"),
        "tags": data.get("tags") or [],
        "isp": data.get("isp"),
    }


def classify_exposure(data: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
    """
    Returns (classification, detail).
    classification: clean | fingerprinted
    """
    if not data:
        return "clean", {"reason": "no_data"}

    signals: list[str] = []
    tags = data.get("tags") or []
    if "honeypot" in tags:
        signals.append("tag:honeypot")
        log.warning("Shodan tagged this host as honeypot.")

    for service in data.get("data", []) or []:
        banner = (service.get("data") or "").lower()
        for kw in HONEYPOT_KEYWORDS:
            if kw in banner:
                signals.append(f"banner:{kw}")
                log.warning("Honeypot keyword %r found in Shodan banner.", kw)

    if signals:
        return "fingerprinted", {"signals": signals}
    return "clean", {}


def get_public_ip() -> str:
    if SHODAN_TEST_PUBLIC_IP:
        return SHODAN_TEST_PUBLIC_IP
    try:
        with urllib.request.urlopen(
            "https://api.ipify.org?format=json", timeout=10
        ) as r:
            return json.loads(r.read().decode()).get("ip", "") or ""
    except Exception as e:
        log.warning("Could not get public IP: %s", e)
        return ""


def query_shodan(ip: str) -> dict[str, Any] | None:
    if SHODAN_FIXTURE_FILE:
        try:
            with open(SHODAN_FIXTURE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning("Failed to read SHODAN_FIXTURE_FILE: %s", e)
            return None
    if not SHODAN_API_KEY:
        return None
    url = f"https://api.shodan.io/shodan/host/{ip}?key={SHODAN_API_KEY}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            log.info("IP %s not yet indexed by Shodan.", ip)
        else:
            log.warning("Shodan API error: %s", e.code)
        return None
    except Exception as e:
        log.warning("Shodan query failed: %s", e)
        return None


def next_persona(current: str, rotation: list[str]) -> str:
    if not rotation:
        return current
    idx = rotation.index(current) if current in rotation else 0
    return rotation[(idx + 1) % len(rotation)]


def swap_persona(new_persona: str) -> bool:
    try:
        result = subprocess.run(
            [SWAP_SCRIPT, new_persona],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            log.info("Swap to %r succeeded.", new_persona)
            return True
        log.error("Swap failed: %s", result.stderr)
        return False
    except Exception as e:
        log.error("Failed to run swap script: %s", e)
        return False


def append_event(payload: dict[str, Any]) -> None:
    path = SHODAN_EVENTS_JSONL
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    except OSError:
        pass
    line = json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n"
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        log.warning("Could not append event to %s: %s", path, e)


def post_webhook(payload: dict[str, Any]) -> None:
    if not SHODAN_WEBHOOK_URL:
        return
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SHODAN_WEBHOOK_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status >= 400:
                log.warning("Webhook returned HTTP %s", r.status)
    except Exception as e:
        log.warning("Webhook POST failed: %s", e)


def run_hook(payload: dict[str, Any]) -> None:
    if not SHODAN_HOOK_SCRIPT:
        return
    try:
        proc = subprocess.run(
            [SHODAN_HOOK_SCRIPT],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=120,
        )
        if proc.returncode != 0:
            log.warning(
                "Hook %s exited %s: %s",
                SHODAN_HOOK_SCRIPT,
                proc.returncode,
                (proc.stderr or proc.stdout or "").strip(),
            )
    except Exception as e:
        log.warning("Hook script failed: %s", e)


def build_event(
    *,
    public_ip: str,
    summary: dict[str, Any],
    classification: str,
    detail: dict[str, Any],
    action_taken: str,
    persona_before: str,
    persona_after: str,
) -> dict[str, Any]:
    return {
        "ts": int(time.time()),
        "public_ip": public_ip,
        "summary": summary,
        "classification": classification,
        "detail": detail,
        "action_taken": action_taken,
        "persona_before": persona_before,
        "persona_after": persona_after,
    }


def one_cycle(current_persona: str, rotation: list[str]) -> str:
    ip = get_public_ip()
    if not ip:
        log.warning("No public IP; skipping cycle.")
        append_event(
            build_event(
                public_ip="",
                summary={},
                classification="clean",
                detail={"reason": "no_public_ip"},
                action_taken="none",
                persona_before=current_persona,
                persona_after=current_persona,
            )
        )
        return current_persona

    data = query_shodan(ip)
    summary = summarize_host(data)
    classification, detail = classify_exposure(data)
    action_taken = "none"
    persona_after = current_persona

    if classification == "fingerprinted":
        persona_after = next_persona(current_persona, rotation)
        log.warning(
            "Fingerprinted; swapping persona: %s -> %s",
            current_persona,
            persona_after,
        )
        if swap_persona(persona_after):
            action_taken = "persona_swap"
        else:
            persona_after = current_persona
            action_taken = "persona_swap_failed"

    payload = build_event(
        public_ip=ip,
        summary=summary,
        classification=classification,
        detail=detail,
        action_taken=action_taken,
        persona_before=current_persona,
        persona_after=persona_after,
    )
    append_event(payload)
    post_webhook(payload)
    run_hook(payload)
    return persona_after


def main() -> None:
    # Normal deployments need SHODAN_API_KEY. SHODAN_FIXTURE_FILE alone is for tests/dev.
    if not SHODAN_API_KEY and not SHODAN_FIXTURE_FILE:
        log.warning(
            "SHODAN_API_KEY not set (and no SHODAN_FIXTURE_FILE); exiting."
        )
        return

    rotation = personas_rotation()
    current = os.environ.get("PERSONA", "generic")
    log.info("Shodan watcher started. persona=%s rotation=%s", current, rotation)
    log.info("Poll interval: %ss", POLL_INTERVAL)

    while True:
        try:
            current = one_cycle(current, rotation)
        except Exception as e:
            log.error("Unexpected error: %s", e)
        if SHODAN_SINGLE_SHOT:
            log.info("SHODAN_SINGLE_SHOT set; exiting after one cycle.")
            break
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
