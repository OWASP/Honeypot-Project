#!/usr/bin/env python3
"""
rule_watcher.py

watches the crs plugin directory for any changes to honeytrap rule files
and triggers an apache graceful reload so new rules take effect without
a container restart.

follows the same watchdog observer pattern as preprocess-modsec-log.py
in the legacy demo stack, applied to rule files instead of log files.

if apachectl graceful fails 3 times in a row, we fall back to a full
container restart so the honeypot is never left in a broken state.
this matches the fallback behavior documented in the gsoc proposal.
"""

import subprocess
import logging
import time
import sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PLUGIN_DIR = "/etc/modsecurity.d/owasp-crs/plugins"
MAX_GRACEFUL_FAILURES = 3

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s][rule_watcher] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/var/log/rule_watcher.log"),
    ],
)
log = logging.getLogger("rule_watcher")


class PluginRuleHandler(FileSystemEventHandler):
    """
    fires on any create, modify, or delete event under the plugin directory.
    only acts on .conf files to avoid reacting to temp editor swap files.
    """

    def __init__(self):
        self._graceful_failures = 0

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".conf"):
            log.info("rule file changed: %s", event.src_path)
            self._reload()

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".conf"):
            log.info("new rule file detected: %s", event.src_path)
            self._reload()

    def on_deleted(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".conf"):
            log.info("rule file removed: %s", event.src_path)
            self._reload()

    def on_moved(self, event):
        if event.is_directory:
            return
        if hasattr(event, 'dest_path') and event.dest_path.endswith(".conf"):
            log.info("rule file moved/renamed: %s -> %s", event.src_path, event.dest_path)
            self._reload()

    def _reload(self):
        """
        attempts an apache graceful reload. if it fails 3 times consecutively
        we give up on graceful and force a full apache restart to guarantee
        the honeypot stays in a consistent state.
        """
        log.info("triggering apachectl graceful reload")
        result = subprocess.run(
            ["apachectl", "graceful"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            log.info("graceful reload succeeded")
            self._graceful_failures = 0
        else:
            self._graceful_failures += 1
            log.warning(
                "graceful reload failed (attempt %d/%d): %s",
                self._graceful_failures,
                MAX_GRACEFUL_FAILURES,
                result.stderr.strip(),
            )

            if self._graceful_failures >= MAX_GRACEFUL_FAILURES:
                log.error(
                    "graceful reload failed %d times in a row, falling back to full restart",
                    MAX_GRACEFUL_FAILURES,
                )
                self._graceful_failures = 0
                restart = subprocess.run(
                    ["apachectl", "restart"],
                    capture_output=True,
                    text=True,
                )
                if restart.returncode == 0:
                    log.info("full restart succeeded")
                else:
                    log.error("full restart also failed: %s", restart.stderr.strip())


if __name__ == "__main__":
    log.info("rule_watcher starting, watching %s", PLUGIN_DIR)

    event_handler = PluginRuleHandler()
    observer = Observer()
    observer.schedule(event_handler, PLUGIN_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("shutting down")
        observer.stop()

    observer.join()
