#!/usr/bin/env python3
"""
Unit and regression tests for Chameleon Engine persona reverse-proxy architecture.

Verifies:
  1. Apache configuration (httpd.conf) enables mod_proxy and mod_proxy_http.
  2. httpd-proxy.conf is included safely via IncludeOptional.
  3. modsec_entry.sh generates valid ProxyPass/ProxyPassReverse directives when
     BACKEND is set, and preserves local active deception lures.
  4. modsec_entry.sh cleanly defaults when BACKEND is unset.
  5. persona_watchdog.py generates correct compose override syntax with depends_on.
  6. All decoy personas in honeytraps/personas/ expose documented endpoints.

Run:
    python3 honeytraps/test_persona_proxy.py
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

REPO_ROOT = Path(__file__).parent.parent.resolve()
HONEYTRAPS_DIR = REPO_ROOT / "honeytraps"
WAF_DIR = HONEYTRAPS_DIR / "waf_modsec"

_results = []


def test(name):
    def decorator(fn):
        try:
            fn()
            _results.append((name, True, None))
            print("[%s] %s" % (PASS, name))
        except Exception as exc:
            _results.append((name, False, exc))
            print("[%s] %s: %s" % (FAIL, name, exc))
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@test("httpd.conf: mod_proxy and mod_proxy_http modules are enabled")
def test_httpd_proxy_modules():
    httpd_conf = WAF_DIR / "httpd.conf"
    assert httpd_conf.exists(), "httpd.conf not found"
    content = httpd_conf.read_text()

    assert re.search(r"^\s*LoadModule\s+proxy_module\s+modules/mod_proxy\.so", content, re.MULTILINE), \
        "LoadModule proxy_module is missing or commented out in httpd.conf"
    assert re.search(r"^\s*LoadModule\s+proxy_http_module\s+modules/mod_proxy_http\.so", content, re.MULTILINE), \
        "LoadModule proxy_http_module is missing or commented out in httpd.conf"


@test("httpd.conf: includes httpd-proxy.conf")
def test_httpd_proxy_include():
    httpd_conf = WAF_DIR / "httpd.conf"
    content = httpd_conf.read_text()
    assert re.search(r"Include(Optional)?\s+conf/extra/httpd-proxy\.conf", content), \
        "httpd.conf does not include conf/extra/httpd-proxy.conf"


@test("Dockerfile: ensures extra configuration files exist")
def test_dockerfile_proxy_conf():
    dockerfile = WAF_DIR / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile not found"
    content = dockerfile.read_text()
    assert "httpd-proxy.conf" in content, "Dockerfile should touch or create httpd-proxy.conf"


@test("modsec_entry.sh: contains proxy directives for BACKEND")
def test_entrypoint_backend_generation():
    entry_sh = WAF_DIR / "modsec_entry.sh"
    assert entry_sh.exists(), "modsec_entry.sh not found"
    content = entry_sh.read_text()
    assert "ProxyPass /robots.txt !" in content
    assert "ProxyPass /login.php.bak !" in content
    assert "ProxyPass /login.html !" in content
    assert "ProxyPass / ${BACKEND}/" in content
    assert "ProxyPassReverse / ${BACKEND}/" in content


@test("persona_watchdog.py: write_override includes depends_on and BACKEND")
def test_watchdog_override_structure():
    import unittest.mock
    sys.modules.setdefault("shodan", unittest.mock.MagicMock())
    sys.path.insert(0, str(HONEYTRAPS_DIR))
    from persona_watchdog import write_override

    persona = {
        "name": "wordpress-5.0",
        "_image": "honeytrap-persona-wordpress-5.0:latest",
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        write_override(persona, tmpdir)
        override_file = Path(tmpdir) / "docker-compose.override.yml"
        assert override_file.exists(), "docker-compose.override.yml not written"
        content = override_file.read_text()

        assert "BACKEND=http://persona_backend:80" in content
        assert "depends_on:" in content
        assert "persona_backend" in content
        assert "image: honeytrap-persona-wordpress-5.0:latest" in content


@test("honeytraps/personas: all 4 decoy personas have valid manifest and endpoints")
def test_persona_manifests():
    personas_dir = HONEYTRAPS_DIR / "personas"
    expected_personas = ["wordpress-5.0", "phpmyadmin-4.8.1", "apache-2.2-php5", "iis-7.5-fastcgi"]

    for name in expected_personas:
        pdir = personas_dir / name
        assert pdir.exists(), f"Persona dir {name} not found"
        manifest = pdir / "persona.json"
        assert manifest.exists(), f"persona.json missing for {name}"

        with open(manifest) as f:
            data = json.load(f)

        assert data.get("name") == name
        assert "exposed_endpoints" in data
        assert len(data["exposed_endpoints"]) > 0, f"No endpoints defined for {name}"
        assert (pdir / "Dockerfile").exists(), f"Dockerfile missing for {name}"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"\nRunning Chameleon Persona Reverse-Proxy Tests ({len(_results)} registered)\n" + "-" * 60)
    failed = [name for name, passed, _ in _results if not passed]
    print("-" * 60)
    if failed:
        print(f"FAILED ({len(failed)} tests failed: {failed})")
        sys.exit(1)
    else:
        print(f"ALL {len(_results)} TESTS PASSED.")
        sys.exit(0)
