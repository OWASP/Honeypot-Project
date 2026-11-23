"""Unit tests for the CHAMELEON-REN Stimulus Engine client-identity handling.

Covers OWASP/Honeypot-Project#111: the engine must only ever key persona
sessions on a validated IP address, namespaced in Redis.

Run:  pip install -r requirements.txt pytest && pytest -v test_stimulus_engine.py
No Redis or WAF is required: both are replaced with in-process fakes.
"""
from unittest import mock

import pytest

import stimulus_engine as engine


class FakeRedis:
    """Minimal in-memory stand-in for the redis-py calls the engine makes."""

    def __init__(self):
        self.store = {}
        self.ttl = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value
        self.ttl[key] = ttl

    def expire(self, key, ttl):
        self.ttl[key] = ttl


@pytest.fixture
def fake_cache(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(engine, "cache", fake)
    return fake


@pytest.fixture
def waf_calls(monkeypatch):
    """Capture what the engine forwards to the WAF instead of making a real request."""
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        resp = mock.Mock()
        resp.content = b"ok"
        resp.status_code = 200
        resp.raw.headers.items.return_value = [("Content-Type", "text/plain")]
        return resp

    monkeypatch.setattr(engine.requests, "request", fake_request)
    return calls


@pytest.fixture
def client():
    engine.app.config["TESTING"] = True
    return engine.app.test_client()


# ---------------------------------------------------------------------------
# resolve_client_ip
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "header, fallback, expected",
    [
        ("203.0.113.7", "172.18.0.2", "203.0.113.7"),            # valid IPv4
        ("2001:db8::1", "172.18.0.2", "2001:db8::1"),            # valid IPv6
        ("  203.0.113.7 ", "172.18.0.2", "203.0.113.7"),         # whitespace trimmed
        ("2001:DB8:0:0::1", "172.18.0.2", "2001:db8::1"),        # IPv6 normalised
        (None, "172.18.0.2", "172.18.0.2"),                      # header missing
        ("", "172.18.0.2", "172.18.0.2"),                        # header empty
        ("not-an-ip", "172.18.0.2", "172.18.0.2"),               # garbage rejected
        ("1.2.3.4, 5.6.7.8", "172.18.0.2", "172.18.0.2"),        # XFF-style list rejected
        ("foo\r\nbar", "172.18.0.2", "172.18.0.2"),              # injection rejected
        ("not-an-ip", "also-bad", "0.0.0.0"),                    # nothing valid
        (None, None, "0.0.0.0"),
    ],
)
def test_resolve_client_ip(header, fallback, expected):
    assert engine.resolve_client_ip(header, fallback) == expected


def test_session_key_is_namespaced():
    assert engine.session_key("203.0.113.7") == "session:203.0.113.7"


# ---------------------------------------------------------------------------
# proxy(): sticky persona sessions
# ---------------------------------------------------------------------------
BROWSER = {"User-Agent": "Mozilla/5.0"}


def test_new_session_is_stored_under_namespaced_key(client, fake_cache, waf_calls):
    client.get("/login/index.php", headers={**BROWSER, "X-Real-IP": "203.0.113.7"})

    assert fake_cache.store == {"session:203.0.113.7": "moodle"}
    assert fake_cache.ttl["session:203.0.113.7"] == engine.SESSION_TTL
    assert waf_calls[0]["headers"]["X-Chameleon-Target"] == "moodle"


def test_session_stays_locked_to_first_persona(client, fake_cache, waf_calls):
    ip = {"X-Real-IP": "203.0.113.7"}
    client.get("/login/index.php", headers={**BROWSER, **ip})      # -> moodle
    client.get("/web/database/manager", headers={**BROWSER, **ip})  # would be odoo
    client.get("/gibbon/", headers={**BROWSER, **ip})               # would be gibbon

    targets = [c["headers"]["X-Chameleon-Target"] for c in waf_calls]
    assert targets == ["moodle", "moodle", "moodle"]
    assert list(fake_cache.store) == ["session:203.0.113.7"]


def test_x_forwarded_for_does_not_influence_identity(client, fake_cache, waf_calls):
    """Rotating XFF from the same peer must NOT create new sessions/personas."""
    for i, path in enumerate(["/login/index.php", "/web/database/manager", "/gibbon/"]):
        client.get(
            path,
            headers={**BROWSER, "X-Real-IP": "203.0.113.7",
                     "X-Forwarded-For": f"198.51.100.{i}"},
        )

    assert list(fake_cache.store) == ["session:203.0.113.7"]
    assert {c["headers"]["X-Chameleon-Target"] for c in waf_calls} == {"moodle"}


def test_garbage_x_real_ip_never_becomes_a_redis_key(client, fake_cache, waf_calls):
    client.get("/", headers={**BROWSER, "X-Real-IP": "AAAA" * 500})

    assert len(fake_cache.store) == 1
    (key,) = fake_cache.store
    assert key.startswith("session:")
    assert "AAAA" not in key


def test_client_cannot_override_routing_header(client, fake_cache, waf_calls):
    client.get(
        "/login/index.php",
        headers={**BROWSER, "X-Real-IP": "203.0.113.7",
                 "X-Chameleon-Target": "odoo", "X-Active-Persona": "spoofed"},
    )
    fwd = waf_calls[0]["headers"]
    assert fwd["X-Chameleon-Target"] == "moodle"
    assert fwd["X-Active-Persona"].startswith("Moodle")
