"""arena validate [dir]                      check submissions only (exit 1 on a bad file)
arena digest                                 compare with the last snapshot, write history/ and known-gaps.jsonl
arena propose                                mine candidate block-phrases from dev gaps (read-only)
arena run --guard overlay:FILE               score the guard plus a reviewed phrase list
arena run --guard sentinel-local --out site  score submissions, write site/index.html and site/results.json
arena gate --baseline a.json --candidate b.json  PASS=0, FAIL=1, INCONCLUSIVE=3
Exit codes: 0 ok, 1 invalid submissions, 2 setup/guard error (no verdict is never treated as a pass)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import digest, gate, guards, propose, report
from .runner import run
from .schema import SubmissionError, load_submissions


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="arena")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("dir", nargs="?", default="submissions")
    r = sub.add_parser("run")
    r.add_argument("--dir", default="submissions")
    r.add_argument("--guard", default="sentinel-local")
    r.add_argument("--out", default="site")
    d = sub.add_parser("digest")
    d.add_argument("--results", default="site/results.json")
    d.add_argument("--history", default="history")
    d.add_argument("--gaps", default="known-gaps.jsonl")
    d.add_argument("--date", default=None)
    g = sub.add_parser("gate")
    g.add_argument("--baseline", required=True)
    g.add_argument("--candidate", required=True)
    g.add_argument("--config", default=None, help="optional JSON overriding gate defaults")
    pr = sub.add_parser("propose")
    pr.add_argument("--dir", default="submissions")
    pr.add_argument("--gaps", default="known-gaps.jsonl")
    pr.add_argument("--guard", default="sentinel-local")
    pr.add_argument("--out", default="proposals/candidates.json")
    pr.add_argument("--min-support", type=int, default=2)
    a = p.parse_args(argv)
    if a.cmd == "propose":
        try:
            records = load_submissions(a.dir)
            gap_ids = {json.loads(l)["id"] for l in Path(a.gaps).read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l)["status"] == "got_through"}
            guard, label = guards.build(a.guard)
            cands = propose.mine(records, gap_ids, a.min_support)
            ev = propose.evaluate(records, guard, cands)
        except (SubmissionError, OSError, ValueError, ImportError, KeyError, guards.GuardError) as e:
            print(f"setup error: {e}", file=sys.stderr)
            return 2
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"guard": label, "candidates": cands, "effect": ev,
                                   "note": "Mined from dev gaps only. Not applied anywhere. Review, then test with: arena run --guard overlay:<this file>, then arena gate."}, indent=2), encoding="utf-8")
        print(f"{len(cands)} candidate phrase(s) from dev gaps. Effect if applied as an overlay: {json.dumps(ev)}")
        return 0
    if a.cmd == "gate":
        try:
            base = json.loads(Path(a.baseline).read_text(encoding="utf-8"))
            cand = json.loads(Path(a.candidate).read_text(encoding="utf-8"))
            cfg = json.loads(Path(a.config).read_text(encoding="utf-8")) if a.config else None
            r = gate.compare(base, cand, cfg)
        except (OSError, ValueError, KeyError) as e:
            print(f"setup error: {e}", file=sys.stderr)
            return 2
        print(gate.markdown(r, base, cand))
        return {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 3}[r["verdict"]]
    if a.cmd == "digest":
        import datetime
        try:
            res = json.loads(Path(a.results).read_text(encoding="utf-8"))
            date = a.date or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            md, changed = digest.build(res, Path(a.history), Path(a.gaps), date)
        except (OSError, ValueError, KeyError) as e:
            print(f"setup error: {e}", file=sys.stderr)
            return 2
        print(md)
        return 0
    try:
        records = load_submissions(a.dir)
    except SubmissionError as e:
        print(f"invalid submissions: {e}", file=sys.stderr)
        return 1
    if a.cmd == "validate":
        print(f"{len(records)} submissions OK")
        return 0
    try:
        guard, label = guards.build(a.guard)
        summary = run(records, guard, label)
    except (ValueError, ImportError, guards.GuardError, AttributeError) as e:
        print(f"setup error: {e}", file=sys.stderr)
        return 2
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(report.html_report(summary), encoding="utf-8")
    (out / "results.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(report.markdown_summary(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
