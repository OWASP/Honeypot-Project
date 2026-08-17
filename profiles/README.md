# profiles

Industry segment profiles for the OWASP Honeypot Project.

Each profile is a YAML file that controls which personas the chameleon
engine cycles through, the Shodan detection threshold, and the threat
intelligence export settings. Switching profiles requires only setting
one environment variable, no code changes.

## Directory structure

```
profiles/
├── education_research.yaml   # university labs and research networks
├── financial.yaml            # financial services and ERP environments
├── general.yaml              # balanced defaults, loaded when no profile is set
├── profile_loader.py         # loads and validates the active profile
├── requirements.txt
└── README.md
```

## Setup

```bash
cd profiles
pip install -r requirements.txt
```

## Selecting a profile

Set the `HONEYPOT_PROFILE` environment variable before starting the
honeypot stack. The loader defaults to `general` if the variable is not
set.

```bash
# Education/research deployment
export HONEYPOT_PROFILE=education_research

# Financial services deployment
export HONEYPOT_PROFILE=financial

# Default (no variable needed)
export HONEYPOT_PROFILE=general
```

## What each profile controls

| Setting | education_research | financial | general |
|---|---|---|---|
| Personas | moodle, gibbon, wordpress | odoo, wordpress | all four |
| Honeyscore threshold | 0.55 | 0.40 | 0.60 |
| Shodan poll interval | 90s | 60s | 90s |
| MISP mode | batch | realtime | batch |
| Min severity | LOW | HIGH | MEDIUM |
| STIX output | enabled | enabled | enabled |

## Validating a profile

Run `profile_loader.py` directly to confirm a profile parses and validates
without errors:

```bash
# Validate the default (general) profile
python profile_loader.py

# Validate a specific profile
HONEYPOT_PROFILE=financial python profile_loader.py
```

If anything is wrong (missing key, out-of-range value, bad YAML) the
script exits with a clear error message.

## Loading a profile in code

```python
from profiles.profile_loader import load_profile

cfg = load_profile()

# Detection settings
threshold = cfg["detection"]["honeyscore_threshold"]
poll = cfg["detection"]["poll_interval_seconds"]

# Export settings
misp_mode = cfg["export"]["misp"]["mode"]
min_sev = cfg["export"]["misp"]["min_severity"]
stix_out = cfg["export"]["stix"]["output_file"]
```

## Adding a new profile

1. Copy `general.yaml` and rename it to match the new segment.
2. Adjust the values for your use case.
3. Add the new filename to `VALID_PROFILES` in `profile_loader.py`.

No other code changes are needed.
