"""A guard is a function text -> (blocked: bool). If it cannot decide it must raise: no verdict is never a pass."""
from __future__ import annotations

import importlib
import json
import os
import urllib.error
import urllib.request
from typing import Callable

Guard = Callable[[str], bool]


class GuardError(RuntimeError):
    pass


def sentinel_local() -> tuple[Guard, str]:
    """In-process Sentinel: rule shield, plus the keyword semantic router if sentinel-semantic is installed."""
    from importlib import metadata

    from ai_sentinel.core.shield import SecurityShield
    shield = SecurityShield(block_threshold=0.7)
    router = None
    try:
        from sentinel_semantic.router import SemanticRouter
        router = SemanticRouter(engine="keyword")
    except ImportError:
        pass

    def blocked(text: str) -> bool:
        if shield.inspect(prompt=text).action == "BLOCK":
            return True
        return router is not None and router.route(text).guardrail_profile == "maximum_security_block"

    def ver(pkg):
        try:
            return metadata.version(pkg)
        except metadata.PackageNotFoundError:
            return "not installed"
    label = f"ai-sentinel {ver('ai-sentinel')} rules" + (f" + sentinel-semantic {ver('sentinel-semantic')} keyword layer" if router else " (no semantic layer)")
    return blocked, label


def http_guard(url: str) -> tuple[Guard, str]:
    """A running ai-sentinel gateway (POST /v1/scan). API key from SENTINEL_API_KEY."""
    key = os.environ.get("SENTINEL_API_KEY", "")
    endpoint = url.rstrip("/") + "/v1/scan"

    def blocked(text: str) -> bool:
        req = urllib.request.Request(endpoint, data=json.dumps({"prompt": text}).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "X-API-Key": key})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode()).get("action") == "BLOCK"
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise GuardError(f"no verdict from {endpoint}: {e}") from e
    return blocked, f"gateway at {url}"


def python_guard(spec: str) -> tuple[Guard, str]:
    """'module:function' where function(text) -> bool (True = blocked). Lets you score any other guard."""
    mod, _, fn = spec.partition(":")
    if not fn:
        raise ValueError("python guard must look like module:function")
    return getattr(importlib.import_module(mod), fn), f"python:{spec}"


def build(spec: str) -> tuple[Guard, str]:
    kind, _, rest = spec.partition(":")
    if spec == "sentinel-local":
        return sentinel_local()
    if kind == "http":
        return http_guard(rest if rest.startswith("http") else "http:" + rest)
    if kind == "python":
        return python_guard(rest)
    raise ValueError("guard must be sentinel-local, http:<url> or python:<module>:<function>")
