"""Read-only digest: what changed since the last snapshot. It never edits a guard or its rules."""
from __future__ import annotations

import json
from pathlib import Path


def _gaps(results: dict) -> dict[str, dict]:
    out = {}
    for r in results["got_through"]:
        out[r["id"]] = {"id": r["id"], "kind": "attack", "status": "got_through", "type": r["type"], "split": r["split"], "origin": r["origin"]}
    for r in results["false_blocks"]:
        out[r["id"]] = {"id": r["id"], "kind": "harmless", "status": "false_block", "type": r["type"], "split": r["split"], "origin": r["origin"]}
    return out


def _latest(history: Path):
    files = sorted(history.glob("*.json")) if history.exists() else []
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def build(results: dict, history: Path, gaps_file: Path, date: str) -> tuple[str, bool]:
    """Returns (markdown, changed). Writes history/<date>.json and gaps_file only when something changed."""
    cur = _gaps(results)
    prev = _latest(history)
    snap = {"date": date, "guard": results["guard"], "submissions_sha256": results["submissions_sha256"],
            "counts": {k: results[k] for k in ("all", "community", "seed", "dev", "holdout")}, "gap_ids": sorted(cur)}
    prev_ids = set(prev["gap_ids"]) if prev else set()
    new = sorted(set(cur) - prev_ids)
    fixed = sorted(prev_ids - set(cur))
    guard_changed = bool(prev) and prev["guard"] != results["guard"]
    sub_changed = bool(prev) and prev["submissions_sha256"] != results["submissions_sha256"]
    changed = prev is None or bool(new) or bool(fixed) or guard_changed or sub_changed
    old_first = {}
    if gaps_file.exists():
        for line in gaps_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                old_first[rec["id"]] = rec.get("first_seen", date)
    if changed:
        history.mkdir(parents=True, exist_ok=True)
        (history / f"{date}.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")
        with gaps_file.open("w", encoding="utf-8") as f:
            for i in sorted(cur):
                f.write(json.dumps({**cur[i], "first_seen": old_first.get(i, date)}, ensure_ascii=False) + "\n")
    L = [f"# Arena digest {date}", "", f"Guard: {results['guard']}", ""]
    if prev is None:
        L.append("First snapshot; nothing to compare with.")
    elif not changed:
        L.append("No change since the last snapshot.")
    else:
        if guard_changed:
            L.append(f"**Guard changed** since {prev['date']}: `{prev['guard']}` -> `{results['guard']}`. Differences below may come from the guard, not from new submissions.")
        if sub_changed:
            L.append("The submission set changed.")
        L += ["", f"New gaps: {len(new)}. Fixed since last time: {len(fixed)}."]
        for i in new:
            L.append(f"- NEW {cur[i]['status']} `{i}` ({cur[i]['type']}, {cur[i]['split']}, {cur[i]['origin']})")
        for i in fixed:
            L.append(f"- fixed `{i}`")
    c, d, h = results["all"], results["dev"], results["holdout"]
    L += ["", f"Now: {c['attacks_blocked']}/{c['attacks']} attacks stopped, {c['harmless_blocked']}/{c['harmless']} harmless wrongly blocked.",
          f"Dev {d['attacks_blocked']}/{d['attacks']} attacks stopped, holdout {h['attacks_blocked']}/{h['attacks']}.",
          "", "Review checklist for a human: is each new gap a real miss or a bad submission? Do not tune a guard on holdout entries. No guard was changed by this job."]
    return "\n".join(L) + "\n", changed
