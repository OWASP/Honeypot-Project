#!/usr/bin/env python3
"""
persona_watchdog.py

polls the shodan honeyscore api for the host's public ip every interval
seconds. when the score exceeds the configured threshold or the host is
explicitly tagged as a honeypot by shodan, rotates the active persona.

rotation mechanism:
  1. select the next persona from the library (round-robin, skips current)
  2. write docker-compose.override.yml pointing persona_backend at the new image
  3. run docker compose up -d -- only persona_backend is recreated, the waf
     stays up the entire time
  4. run apachectl graceful inside the waf to flush cached proxy connections
     to the old backend

every rotation event is appended as a json line to rotation_log.jsonl for
audit and downstream analysis. the format matches the v1.0 event schema
from the json schema migration.

shodan scores are cached in .watchdog_state.json between polls. if the api
is unreachable the cached score is used, so a network blip never causes a
false rotation. exponential backoff is applied on all shodan api calls.

requires SHODAN_API_KEY in the environment. run from honeytraps/:

    python3 persona_watchdog.py [--threshold 0.4] [--interval 60]
    python3 persona_watchdog.py --force-rotate
"""


import argparse
import json
import logging
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    import shodan
except ImportError:
    print("shodan library not installed -- run: pip install shodan", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# paths and constants
# ---------------------------------------------------------------------------

HERE = Path(__file__).parent
PERSONAS_DIR = HERE / "personas"
STATE_FILE = HERE / ".watchdog_state.json"
ROTATION_LOG = HERE / "rotation_log.jsonl"
LOG_FILE = HERE / "persona_watchdog.log"

DEFAULT_THRESHOLD = 0.4
DEFAULT_INTERVAL = 60
DEFAULT_COMPOSE_DIR = HERE / "waf_modsec"
WAF_CONTAINER = "modsec_app"

# lower values rotate more aggressively; 0.7 keeps a persona alive longer
# to maximise attacker engagement time before triggering a rotation.
THRESHOLD_MIN = 0.4
THRESHOLD_MAX = 0.7

# how many times to retry a shodan api call before giving up
MAX_API_RETRIES = 5
# base for exponential backoff in seconds
BACKOFF_BASE = 2

# ---------------------------------------------------------------------------
# logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s][persona_watchdog] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE)),
    ],
)
log = logging.getLogger("persona_watchdog")


# ---------------------------------------------------------------------------
# persona library
# ---------------------------------------------------------------------------

def load_personas():
    """
    reads all persona.json manifests under honeytraps/personas/ and returns
    a list of persona dicts sorted by name. any persona directory that is
    missing a persona.json is skipped with a warning so partial work-in-progress
    entries don't break the rotation cycle.
    """
    personas = []
    if not PERSONAS_DIR.exists():
        log.error("personas directory not found: %s", PERSONAS_DIR)
        sys.exit(1)

    for entry in sorted(PERSONAS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        manifest = entry / "persona.json"
        if not manifest.exists():
            log.warning("skipping %s: no persona.json found", entry.name)
            continue
        try:
            with manifest.open() as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            log.warning("skipping %s: invalid persona.json (%s)", entry.name, e)
            continue

        data["_path"] = str(entry)
        personas.append(data)

    if not personas:
        log.error("no valid personas found under %s -- cannot start", PERSONAS_DIR)
        sys.exit(1)

    log.info("loaded %d personas: %s", len(personas), [p["name"] for p in personas])
    return personas


def pre_build_personas(personas):
    """
    builds all persona container images at startup, tagging each as
    honeytrap-persona-{name}:latest. pre-building at startup means rotations
    are instant: docker compose up -d only swaps the running container with
    no image build step during the rotation itself.
    """
    log.info("pre-building %d persona images", len(personas))
    for persona in personas:
        tag = "honeytrap-persona-{}:latest".format(persona["name"])
        log.info("building %s from %s", tag, persona["_path"])
        result = subprocess.run(
            ["docker", "build", "-t", tag, persona["_path"]],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            log.error("failed to build %s:\n%s", tag, result.stderr.strip())
            sys.exit(1)
        persona["_image"] = tag
        log.info("built %s", tag)


def next_persona(personas, current_name):
    """
    returns the next persona in the round-robin cycle, always skipping the
    one that is currently active. if only one persona exists in the library
    it is returned unchanged (rotation is a no-op in that case).
    """
    if len(personas) == 1:
        return personas[0]
    names = [p["name"] for p in personas]
    if current_name not in names:
        return personas[0]
    idx = (names.index(current_name) + 1) % len(personas)
    return personas[idx]


# ---------------------------------------------------------------------------
# state persistence
# ---------------------------------------------------------------------------

def load_state():
    """
    reads the watchdog state from STATE_FILE. state survives restarts so the
    watchdog picks up from where it left off rather than rotating unnecessarily.
    returns sensible defaults if the file doesn't exist yet.
    """
    if STATE_FILE.exists():
        try:
            with STATE_FILE.open() as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            log.warning("could not read state file (%s), starting fresh", e)
    return {
        "current_persona": None,
        "last_score": None,
        "last_score_time": 0,
    }


def save_state(state):
    with STATE_FILE.open("w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# shodan
# ---------------------------------------------------------------------------

def get_public_ip():
    """
    resolves the host's public ip via api.ipify.org. this is the ip that
    shodan indexes, so it must be the public-facing address, not a private
    network address.
    """
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=8) as resp:
            return resp.read().decode().strip()
    except Exception as e:
        log.warning("public ip lookup failed: %s", e)
        return None


def query_honeyscore(api, ip):
    """
    fetches the shodan honeyscore for ip with exponential backoff on failures.
    returns the score as a float, or None if all retries are exhausted.
    """
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            score = api.honeyscore(ip)
            return float(score)
        except shodan.APIError as e:
            wait = BACKOFF_BASE ** attempt
            log.warning(
                "shodan api error (attempt %d/%d): %s -- retrying in %ds",
                attempt, MAX_API_RETRIES, e, wait,
            )
            if attempt < MAX_API_RETRIES:
                time.sleep(wait)
    log.error("honeyscore lookup failed after %d attempts", MAX_API_RETRIES)
    return None


def query_host_tags(api, ip):
    """
    fetches the tags from the shodan host record for ip. used to check for an
    explicit 'honeypot' tag in addition to the numeric score. returns an empty
    list on failure so a tag lookup error never blocks the rotation check.
    """
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            host = api.host(ip)
            return [t.lower() for t in host.get("tags", [])]
        except shodan.APIError as e:
            wait = BACKOFF_BASE ** attempt
            log.warning(
                "shodan host lookup error (attempt %d/%d): %s -- retrying in %ds",
                attempt, MAX_API_RETRIES, e, wait,
            )
            if attempt < MAX_API_RETRIES:
                time.sleep(wait)
    return []


# ---------------------------------------------------------------------------
# rotation
# ---------------------------------------------------------------------------

def write_override(persona, compose_dir):
    """
    writes docker-compose.override.yml into compose_dir.

    the override does two things:
      - sets BACKEND on the waf service so it proxies all traffic to
        persona_backend. this only causes a waf restart on the very first
        rotation; subsequent rotations leave BACKEND unchanged so the waf
        is never touched again.
      - defines the persona_backend service using the pre-built image so
        docker compose up -d only recreates that one container, not the waf.

    written as a plain string rather than through pyyaml to avoid the extra
    dependency; the structure is fixed so templating is safe here.
    """
    image = persona.get("_image", "honeytrap-persona-{}:latest".format(persona["name"]))

    content = (
        "# generated by persona_watchdog.py -- do not edit by hand\n"
        "# active persona: {name}\n"
        "# rotated at: {ts}\n"
        "services:\n"
        "  modsec_crs:\n"
        "    environment:\n"
        "      - BACKEND=http://persona_backend:80\n"
        "      - PARANOIA=5\n"
        "  persona_backend:\n"
        "    image: {image}\n"
        "    container_name: persona_backend\n"
    ).format(
        name=persona["name"],
        ts=datetime.now(timezone.utc).isoformat(),
        image=image,
    )

    override_path = Path(compose_dir) / "docker-compose.override.yml"
    with override_path.open("w") as f:
        f.write(content)
    log.info("wrote override: %s (persona: %s)", override_path, persona["name"])


def apply_rotation(persona, compose_dir, current_name):
    """
    writes the compose override, runs docker compose up -d to apply it, then
    issues apachectl graceful inside the waf container to flush cached proxy
    connections to the old backend.

    on the first rotation the waf restarts once to pick up the BACKEND env
    var. all subsequent rotations only recreate persona_backend; the waf
    itself is never touched again.

    returns True on success, False if docker compose failed.
    """
    write_override(persona, compose_dir)

    log.info(
        "applying rotation: %s -> %s",
        current_name or "(none)",
        persona["name"],
    )

    result = subprocess.run(
        ["docker", "compose", "up", "-d"],
        cwd=str(compose_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error("docker compose up -d failed:\n%s", result.stderr.strip())
        return False

    log.info("docker compose up succeeded")

    # flush the waf proxy cache so it immediately connects to the new backend
    graceful = subprocess.run(
        ["docker", "exec", WAF_CONTAINER, "apachectl", "graceful"],
        capture_output=True,
        text=True,
    )
    if graceful.returncode == 0:
        log.info("apachectl graceful succeeded in %s", WAF_CONTAINER)
    else:
        log.warning(
            "apachectl graceful returned non-zero (waf may not have the new backend yet): %s",
            graceful.stderr.strip(),
        )

    return True


def log_rotation_event(persona, score, trigger):
    """
    appends a json line to rotation_log.jsonl. one record per rotation.
    the structure is consistent with the v1.0 event schema so downstream
    logstash pipelines can consume it without a separate format translation.
    """
    event = {
        "event_type": "persona_rotation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "persona": {
            "name": persona["name"],
            "version": persona.get("version", "unknown"),
            "cve": persona.get("cve", []),
            "profile": persona.get("profile", "general"),
            "shodan_fingerprint": persona.get("shodan_fingerprint", ""),
        },
        "shodan_honeyscore": score,
        "trigger": trigger,
    }
    with ROTATION_LOG.open("a") as f:
        f.write(json.dumps(event) + "\n")
    log.info(
        "rotation event logged (trigger=%s persona=%s score=%s)",
        trigger, persona["name"], score,
    )


# ---------------------------------------------------------------------------
# main watchdog loop
# ---------------------------------------------------------------------------

def run_watchdog(args):
    api_key = os.environ.get("SHODAN_API_KEY")
    if not api_key:
        log.error("SHODAN_API_KEY env var is not set")
        sys.exit(1)

    threshold = float(os.environ.get("WATCHDOG_THRESHOLD", args.threshold))
    interval = int(os.environ.get("WATCHDOG_INTERVAL", args.interval))
    compose_dir = Path(os.environ.get("WATCHDOG_COMPOSE", args.compose_dir))

    if not (THRESHOLD_MIN <= threshold <= THRESHOLD_MAX):
        log.error(
            "threshold %.2f is outside the allowed range %.1f-%.1f",
            threshold, THRESHOLD_MIN, THRESHOLD_MAX,
        )
        sys.exit(1)

    if not compose_dir.exists():
        log.error("compose dir does not exist: %s", compose_dir)
        sys.exit(1)

    log.info(
        "persona_watchdog starting (threshold=%.2f interval=%ds compose=%s)",
        threshold, interval, compose_dir,
    )

    api = shodan.Shodan(api_key)
    personas = load_personas()
    pre_build_personas(personas)
    state = load_state()

    # on a fresh start set the initial persona before entering the poll loop
    if state["current_persona"] is None:
        initial = personas[0]
        log.info("no active persona in state, initialising with %s", initial["name"])
        if apply_rotation(initial, compose_dir, None):
            log_rotation_event(initial, None, "initial_startup")
            state["current_persona"] = initial["name"]
            save_state(state)

    public_ip = get_public_ip()
    if not public_ip:
        log.error("could not resolve public ip -- watchdog cannot poll shodan")
        sys.exit(1)
    log.info("resolved public ip: %s", public_ip)

    log.info("entering poll loop (interval=%ds)", interval)

    while True:
        score = query_honeyscore(api, public_ip)

        if score is not None:
            state["last_score"] = score
            state["last_score_time"] = time.time()
            save_state(state)
            tags = query_host_tags(api, public_ip)
        else:
            # api is down; use the cached score rather than triggering a false rotation
            score = state.get("last_score")
            tags = []
            log.warning(
                "shodan unreachable, using cached score: %s (last seen %ds ago)",
                score,
                int(time.time() - state.get("last_score_time", 0)),
            )

        log.info(
            "poll result: score=%s threshold=%.2f tags=%s current_persona=%s",
            score, threshold, tags, state["current_persona"],
        )

        score_exceeded = (score is not None) and (score > threshold)
        honeypot_tagged = "honeypot" in tags

        if score_exceeded or honeypot_tagged:
            trigger = "score_exceeded" if score_exceeded else "honeypot_tag"
            log.info(
                "rotation triggered by %s (score=%s threshold=%.2f)",
                trigger, score, threshold,
            )
            target = next_persona(personas, state["current_persona"])
            if apply_rotation(target, compose_dir, state["current_persona"]):
                log_rotation_event(target, score, trigger)
                state["current_persona"] = target["name"]
                save_state(state)
        else:
            log.info("score within threshold, no rotation needed")

        time.sleep(interval)


def force_rotate(args):
    """
    immediately rotates to the next persona without querying shodan.
    intended for testing the rotation pipeline end-to-end and for manual
    recovery when the current persona is known to be compromised.
    """
    compose_dir = Path(os.environ.get("WATCHDOG_COMPOSE", args.compose_dir))
    personas = load_personas()
    pre_build_personas(personas)
    state = load_state()

    target = next_persona(personas, state["current_persona"])
    log.info("force rotating to %s", target["name"])

    if apply_rotation(target, compose_dir, state["current_persona"]):
        log_rotation_event(target, None, "manual_force_rotate")
        state["current_persona"] = target["name"]
        save_state(state)
        log.info("force rotation complete")
    else:
        log.error("force rotation failed")
        sys.exit(1)


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "polls shodan honeyscore and rotates the active honeypot persona "
            "when the score exceeds the configured threshold"
        )
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="honeyscore threshold that triggers rotation, 0.4-0.7 (default: 0.4)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help="shodan poll interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--compose-dir",
        default=str(DEFAULT_COMPOSE_DIR),
        help="path to the waf docker compose directory (default: ./waf_modsec)",
    )
    parser.add_argument(
        "--force-rotate",
        action="store_true",
        help="immediately rotate to the next persona without querying shodan",
    )
    args = parser.parse_args()

    if args.force_rotate:
        force_rotate(args)
    else:
        run_watchdog(args)
