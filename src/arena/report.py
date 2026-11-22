"""Static HTML + Markdown report. No JavaScript, no external requests; all submitted text is escaped."""
from __future__ import annotations

import html

from .schema import ATTACK_TYPES

CSS = """body{font:16px/1.5 system-ui,sans-serif;max-width:820px;margin:0 auto;padding:1rem;color:#1b1f23}
h1{font-size:1.6rem}h2{margin-top:2rem;border-bottom:1px solid #ddd;padding-bottom:.3rem}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:.4rem .6rem;border-bottom:1px solid #eee;vertical-align:top}
.n{font-variant-numeric:tabular-nums}.warn{background:#fff8e1;padding:.7rem 1rem;border-left:4px solid #f0b400}
code,pre{background:#f4f5f7;padding:.1rem .3rem;border-radius:3px;white-space:pre-wrap;word-break:break-word}small{color:#555}"""


def _pct(v):
    return "n/a" if v is None else f"{v}%"


def _list(rows):
    if not rows:
        return "<p>None.</p>"
    out = ["<table><tr><th>Type</th><th>Text</th><th>Author</th></tr>"]
    for r in rows:
        out.append(f"<tr><td>{html.escape(r['type'])}</td><td><code>{html.escape(r['text'])}</code></td><td>{html.escape(r['author'])}<br><small>{html.escape(r['origin'])}</small></td></tr>")
    out.append("</table>")
    return "".join(out)


def html_report(s: dict) -> str:
    a, c, sd = s["all"], s["community"], s["seed"]
    types = "".join(f"<tr><td>{html.escape(ATTACK_TYPES.get(t, t))}</td><td class=n>{v['blocked']} of {v['attacks']}</td></tr>" for t, v in sorted(s["by_type"].items()))
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Sentinel Arena</title><style>{CSS}</style></head><body>
<h1>Sentinel Arena</h1>
<p>Anyone can submit a prompt-injection attack by pull request. This page shows which ones the guard stopped.</p>
<p class=warn><b>Read this first.</b> Scores are a snapshot of one guard configuration on public, self-selected attacks. They are not a security certificate. Attacks are public, so a guard can be tuned to this set; the seed rows were written by the project builder and are not independent. Community rows are shown separately.</p>
<p>Guard tested: <b>{html.escape(s['guard'])}</b><br><small>Generated {html.escape(s['generated_utc'])} UTC &middot; submissions sha256 {html.escape(s['submissions_sha256'][:16])}&hellip;</small></p>
<h2>Scores</h2>
<table><tr><th></th><th>Attacks stopped</th><th>Harmless wrongly blocked</th></tr>
<tr><td>Community submissions</td><td class=n>{c['attacks_blocked']} of {c['attacks']} ({_pct(c['catch_rate'])})</td><td class=n>{c['harmless_blocked']} of {c['harmless']} ({_pct(c['false_block_rate'])})</td></tr>
<tr><td>Seed (builder-written)</td><td class=n>{sd['attacks_blocked']} of {sd['attacks']} ({_pct(sd['catch_rate'])})</td><td class=n>{sd['harmless_blocked']} of {sd['harmless']} ({_pct(sd['false_block_rate'])})</td></tr>
<tr><td>All</td><td class=n>{a['attacks_blocked']} of {a['attacks']} ({_pct(a['catch_rate'])})</td><td class=n>{a['harmless_blocked']} of {a['harmless']} ({_pct(a['false_block_rate'])})</td></tr></table>
<h2>By attack type</h2><table><tr><th>Type</th><th>Stopped</th></tr>{types}</table>
<h2>Attacks that got through ({len(s['got_through'])})</h2>{_list(s['got_through'])}
<h2>Harmless prompts wrongly blocked ({len(s['false_blocks'])})</h2>{_list(s['false_blocks'])}
<h2>Attacks that were stopped ({len(s['caught'])})</h2><details><summary>Show</summary>{_list(s['caught'])}</details>
<h2>Add yours</h2><p>See CONTRIBUTING.md in the repository. One new file, one pull request, and CI scores it.</p>
</body></html>"""


def markdown_summary(s: dict) -> str:
    a, c, sd = s["all"], s["community"], s["seed"]
    return "\n".join([
        f"**Guard:** {s['guard']}  ", f"**Generated:** {s['generated_utc']} UTC", "",
        "| | Attacks stopped | Harmless wrongly blocked |", "|---|---|---|",
        f"| Community | {c['attacks_blocked']}/{c['attacks']} ({_pct(c['catch_rate'])}) | {c['harmless_blocked']}/{c['harmless']} ({_pct(c['false_block_rate'])}) |",
        f"| Seed (builder-written) | {sd['attacks_blocked']}/{sd['attacks']} ({_pct(sd['catch_rate'])}) | {sd['harmless_blocked']}/{sd['harmless']} ({_pct(sd['false_block_rate'])}) |",
        f"| All | {a['attacks_blocked']}/{a['attacks']} ({_pct(a['catch_rate'])}) | {a['harmless_blocked']}/{a['harmless']} ({_pct(a['false_block_rate'])}) |",
        "", f"Got through: {len(s['got_through'])} attacks. Wrongly blocked: {len(s['false_blocks'])} harmless prompts."])
