CRS Auto Update (Planned)
This directory is intended for a small, optional script that will keep our WAF's container up to date on the OWASP ModSecurity Core Rule Set. The design here is one of minimal surprise: unless explicitly configured, you stick with the CRS in the image. Opt-in updates.
Approach 

Default pinned: If auto-update isn't enabled, there is no auto-update.
Opt-in updates: when enabled, we install into the existing, expected path within the container (the CRS directory).
Fail open: if update fails, use existing.
No path changes: Apache/ModSecurity include references will continue to be the same relative locations of crs-setup.conf and rules/*.conf.

Future configuration 

CRS_UPDATE - turn the updater on/off (default: false)
CRS_VERSION - the tag/commit/version of CRS to install (default: version pinned in the image)
Optional: HTTPPROXY, HTTPSPROXY, NO_PROXY - For restricted network access.

Assumptions 

CRS must be accessible at the existing, expected path as referenced in include.conf.
The updater must be idempotent and leave the crs-dir either completely in-tact or completely in the new version.
Only runs during container startup (no internal scheduler).

PR Plan 

PR1: Scaffold + Documentation (this file)
PR2: Implement Updater Logic
PR3: Dockerfile Changes (Add dependency + the script)
PR4: Entrypoint Wiring + Runtime Toggles + Basic Logging


No Dockerfile/entrypoint/ModSecurity behavior changes have occurred yet.

Quick check
If you like this plan and approach (small, non-breaking PRs, build toward a functional end), please approve .
