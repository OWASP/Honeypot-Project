#!/usr/bin/env python3
"""
Profile loader for the OWASP Honeypot Project.

Reads the HONEYPOT_PROFILE environment variable, loads the corresponding
YAML profile from this directory, validates it, and returns the config dict.

Supported profiles: education_research, financial, general (default).

Usage:
    from profiles.profile_loader import load_profile

    cfg = load_profile()
    print(cfg["detection"]["honeyscore_threshold"])

Or run directly to validate a profile:
    python profile_loader.py
    HONEYPOT_PROFILE=financial python profile_loader.py
"""

import json
import logging
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is not installed. Run: pip install pyyaml==6.0.3")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# Directory that contains the YAML profile files.
PROFILES_DIR = os.path.dirname(os.path.abspath(__file__))

# Available profiles. Each maps to a YAML filename in PROFILES_DIR.
VALID_PROFILES = {
    "education_research": "education_research.yaml",
    "financial": "financial.yaml",
    "general": "general.yaml",
}

DEFAULT_PROFILE = "general"

# Valid severity levels in descending order.
SEVERITY_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

# Valid export modes for the MISP exporter.
MISP_MODES = ["batch", "realtime"]


def _validate(cfg, profile_name):
    """
    Validate that a loaded profile dict has all required keys and that
    values are within acceptable ranges. Raises ValueError on any problem.
    """
    errors = []

    # Top-level required keys.
    for key in ("name", "personas", "detection", "export"):
        if key not in cfg:
            errors.append("missing required key: '%s'" % key)

    if errors:
        raise ValueError(
            "Profile '%s' is invalid: %s" % (profile_name, "; ".join(errors))
        )

    # personas must be a non-empty list.
    personas = cfg.get("personas")
    if not isinstance(personas, list) or len(personas) == 0:
        errors.append("'personas' must be a non-empty list")

    # detection section.
    detection = cfg.get("detection", {})
    threshold = detection.get("honeyscore_threshold")
    if threshold is None:
        errors.append("detection.honeyscore_threshold is required")
    elif not isinstance(threshold, (int, float)) or not (0.4 <= threshold <= 0.7):
        errors.append(
            "detection.honeyscore_threshold must be a float between 0.4 and 0.7, "
            "got: %s" % threshold
        )

    poll = detection.get("poll_interval_seconds")
    if poll is None:
        errors.append("detection.poll_interval_seconds is required")
    elif not isinstance(poll, int) or poll < 10:
        errors.append(
            "detection.poll_interval_seconds must be an integer >= 10, got: %s" % poll
        )

    if "rotate_on_honeypot_tag" not in detection:
        errors.append("detection.rotate_on_honeypot_tag is required")

    # export section.
    export = cfg.get("export", {})

    misp = export.get("misp", {})
    if not isinstance(misp.get("enabled"), bool):
        errors.append("export.misp.enabled must be true or false")
    misp_mode = misp.get("mode")
    if misp_mode not in MISP_MODES:
        errors.append(
            "export.misp.mode must be one of %s, got: %s" % (MISP_MODES, misp_mode)
        )
    min_sev = misp.get("min_severity", "").upper()
    if min_sev not in SEVERITY_LEVELS:
        errors.append(
            "export.misp.min_severity must be one of %s, got: %s"
            % (SEVERITY_LEVELS, min_sev)
        )

    stix = export.get("stix", {})
    if not isinstance(stix.get("enabled"), bool):
        errors.append("export.stix.enabled must be true or false")
    if not isinstance(stix.get("taxii_push"), bool):
        errors.append("export.stix.taxii_push must be true or false")
    if stix.get("taxii_push") and not stix.get("taxii_url"):
        errors.append(
            "export.stix.taxii_url must be set when export.stix.taxii_push is true"
        )

    if errors:
        raise ValueError(
            "Profile '%s' is invalid:\n  - %s"
            % (profile_name, "\n  - ".join(errors))
        )


def load_profile(profile_name=None):
    """
    Load and validate a honeypot industry segment profile.

    profile_name defaults to the HONEYPOT_PROFILE environment variable,
    falling back to 'general' if neither is set.

    Returns the profile config as a dict. Exits the process on any error
    so the caller never receives a broken config.
    """
    if profile_name is None:
        profile_name = os.environ.get("HONEYPOT_PROFILE", DEFAULT_PROFILE).lower()

    if profile_name not in VALID_PROFILES:
        sys.exit(
            "Unknown profile '%s'. Valid options: %s"
            % (profile_name, ", ".join(sorted(VALID_PROFILES)))
        )

    yaml_file = os.path.join(PROFILES_DIR, VALID_PROFILES[profile_name])

    try:
        with open(yaml_file, "r") as fh:
            cfg = yaml.safe_load(fh)
    except OSError as exc:
        sys.exit("Could not read profile file %s: %s" % (yaml_file, exc))
    except yaml.YAMLError as exc:
        sys.exit("YAML parse error in %s: %s" % (yaml_file, exc))

    if not isinstance(cfg, dict):
        sys.exit("Profile file %s did not parse to a dict." % yaml_file)

    try:
        _validate(cfg, profile_name)
    except ValueError as exc:
        sys.exit(str(exc))

    log.info("Loaded profile '%s' from %s", profile_name, yaml_file)
    return cfg


if __name__ == "__main__":
    profile = load_profile()
    print(json.dumps(profile, indent=2, default=str))
