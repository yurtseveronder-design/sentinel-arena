"""arena validate [dir]                      check submissions only (exit 1 on a bad file)
arena run --guard sentinel-local --out site  score submissions, write site/index.html and site/results.json
Exit codes: 0 ok, 1 invalid submissions, 2 setup/guard error (no verdict is never treated as a pass)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import guards, report
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
    a = p.parse_args(argv)
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
