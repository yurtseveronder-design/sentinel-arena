"""arena validate [dir]                      check submissions only (exit 1 on a bad file)
arena digest                                 compare with the last snapshot, write history/ and known-gaps.jsonl
arena run --guard sentinel-local --out site  score submissions, write site/index.html and site/results.json
Exit codes: 0 ok, 1 invalid submissions, 2 setup/guard error (no verdict is never treated as a pass)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import digest, guards, report
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
    a = p.parse_args(argv)
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
