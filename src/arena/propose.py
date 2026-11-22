"""Slow learning plane, step 1: propose candidate block-phrases from DEV gaps only. Deterministic; no LLM, no network.
A candidate is a word n-gram that (a) appears in at least `min_support` distinct dev attacks that currently get through,
(b) appears in NO harmless prompt (any split), and (c) is not made only of common words. Candidates are only ever
used as an additive overlay (they can add blocks, never allow anything) and must pass `arena gate` and human review."""
from __future__ import annotations

import re

from .schema import split_of

STOP = set("a an the and or of to in on for with is are was were be it this that you your i me my we our as at by from not no do does please can will would just if so".split())
_WORD = re.compile(r"[a-z0-9']+")


def normalise(text: str) -> str:
    return " ".join(_WORD.findall(text.lower()))


def _grams(text: str, lo: int, hi: int) -> set[str]:
    w = _WORD.findall(text.lower())
    return {" ".join(w[i:i + n]) for n in range(lo, hi + 1) for i in range(len(w) - n + 1)}


def mine(records: list[dict], gap_ids: set[str], min_support: int = 2, lo: int = 2, hi: int = 4) -> list[dict]:
    dev_gaps = [r for r in records if r["kind"] == "attack" and r["id"] in gap_ids and split_of(r["id"]) == "dev"]
    harmless = [normalise(r["text"]) for r in records if r["kind"] == "harmless"]
    support: dict[str, set[str]] = {}
    for r in dev_gaps:
        for g in _grams(r["text"], lo, hi):
            if all(w in STOP for w in g.split()):
                continue
            support.setdefault(g, set()).add(r["id"])
    out = []
    for g, ids in support.items():
        if len(ids) < min_support:
            continue
        pat = f" {g} "
        if any(pat in f" {h} " for h in harmless):
            continue
        out.append({"phrase": g, "support": sorted(ids)})
    # prefer longer, better supported phrases; drop phrases contained in a kept longer one with the same support
    out.sort(key=lambda c: (-len(c["support"]), -len(c["phrase"].split()), c["phrase"]))
    kept: list[dict] = []
    for c in out:
        if any(c["phrase"] in k["phrase"] and set(c["support"]) <= set(k["support"]) for k in kept):
            continue
        kept.append(c)
    return kept[:50]


def overlay_guard(base_guard, phrases: list[str]):
    pats = [f" {normalise(p)} " for p in phrases if normalise(p)]

    def blocked(text: str) -> bool:
        if base_guard(text):
            return True
        n = f" {normalise(text)} "
        return any(p in n for p in pats)
    return blocked


def evaluate(records, base_guard, candidates: list[dict]) -> dict:
    """What would the overlay change? Reported per split so dev and holdout are never mixed up."""
    phrases = [c["phrase"] for c in candidates]
    ov = overlay_guard(base_guard, phrases)
    res = {"dev": {"newly_stopped": 0, "new_false_blocks": 0}, "holdout": {"newly_stopped": 0, "new_false_blocks": 0}}
    for r in records:
        sp = split_of(r["id"])
        b, o = base_guard(r["text"]), ov(r["text"])
        if r["kind"] == "attack" and o and not b:
            res[sp]["newly_stopped"] += 1
        if r["kind"] == "harmless" and o and not b:
            res[sp]["new_false_blocks"] += 1
    return res
