from __future__ import annotations

import datetime
import hashlib
import json
import statistics
import time

from .schema import split_of


def run(records: list[dict], guard, guard_label: str) -> dict:
    rows, times = [], []
    for rec in records:
        t0 = time.perf_counter()
        blocked = bool(guard(rec["text"]))  # a guard that cannot decide raises and aborts the run
        times.append((time.perf_counter() - t0) * 1000)
        rows.append({**rec, "split": split_of(rec["id"]), "blocked": blocked})
    out = summarise(rows, guard_label)
    ts = sorted(times)
    out["latency_ms"] = {"median": round(statistics.median(ts), 3), "p95": round(ts[min(len(ts) - 1, int(len(ts) * 0.95))], 3)}
    return out


def _rate(num: int, den: int):
    return round(100 * num / den, 1) if den else None


def _group(rows: list[dict]) -> dict:
    a = [r for r in rows if r["kind"] == "attack"]
    h = [r for r in rows if r["kind"] == "harmless"]
    return {"attacks": len(a), "attacks_blocked": sum(r["blocked"] for r in a), "catch_rate": _rate(sum(r["blocked"] for r in a), len(a)),
            "harmless": len(h), "harmless_blocked": sum(r["blocked"] for r in h), "false_block_rate": _rate(sum(r["blocked"] for r in h), len(h))}


def summarise(rows: list[dict], guard_label: str) -> dict:
    by_type: dict[str, dict] = {}
    for r in rows:
        if r["kind"] == "attack":
            t = by_type.setdefault(r["type"], {"attacks": 0, "blocked": 0})
            t["attacks"] += 1
            t["blocked"] += r["blocked"]
    digest = hashlib.sha256(json.dumps(sorted(({k: r[k] for k in ("id", "kind", "type", "text")} for r in rows), key=lambda x: x["id"]), sort_keys=True).encode()).hexdigest()
    return {
        "guard": guard_label,
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "submissions_sha256": digest,
        "all": _group(rows),
        "community": _group([r for r in rows if r["origin"] == "community"]),
        "seed": _group([r for r in rows if r["origin"] == "seed"]),
        "dev": _group([r for r in rows if r["split"] == "dev"]),
        "holdout": _group([r for r in rows if r["split"] == "holdout"]),
        "by_type": by_type,
        "got_through": [r for r in rows if r["kind"] == "attack" and not r["blocked"]],
        "caught": [r for r in rows if r["kind"] == "attack" and r["blocked"]],
        "false_blocks": [r for r in rows if r["kind"] == "harmless" and r["blocked"]],
    }
