# Sentinel Arena

A public challenge: **submit a prompt-injection attack by pull request and see whether the guard stops it.**

**Live results: https://yurtseveronder-design.github.io/sentinel-arena/**

CI scores every submission against the guard and publishes a static results page listing what was stopped, what got through, and which harmless prompts were wrongly blocked.

## Why this exists

The Sentinel guard was built and measured by one person with AI help, on attacks the builders wrote themselves. That is a weak test. This repository invites other people to write the attacks, and keeps the results public, including the failures.

## How it works

- `submissions/*.jsonl`: attacks and harmless prompts (format in CONTRIBUTING.md). `seed-*.jsonl` are written by the project builder; `community-*.jsonl` come from pull requests.
- `arena run` scores every submission with a guard and writes `site/index.html` and `site/results.json`.
- Default guard: in-process [ai-sentinel](https://github.com/yurtseveronder-design/ai-sentinel) rules plus the keyword layer of [sentinel-semantic](https://github.com/yurtseveronder-design/sentinel-semantic), installed from their `main` branches in CI. The optional trained classifier is not enabled, matching Sentinel's default.
- Any other guard can be scored: `--guard python:mymodule:myfunc` (function takes text, returns True if blocked) or `--guard http:<gateway-url>`. A guard that cannot give a verdict aborts the run; no verdict is never counted as a pass.
- Results page: no JavaScript, no external requests, all submitted text escaped.

```bash
pip install .
arena validate submissions
arena run --guard sentinel-local --out site   # open site/index.html
python -m unittest discover -s tests -t .
```

## Limits (read these)

- Results are a snapshot of one guard version on public, self-selected prompts. They are **not** a security certificate and say nothing about a different configuration or a real LLM behind the guard.
- The attacks are public. A guard can be tuned to this set, so scores can rise without real robustness improving. Treat a rising score as weak evidence.
- Seed rows were written by the project builder (with AI help) and are not independent. Community rows are reported separately; with few submissions the percentages are noise.
- The guard under test is scored on its main branch at CI time, so numbers on the page can change between runs. Each page shows its generation time and a hash of the submission set.
- Prompts only. This does not test output scanning, retrieval pipelines, or tool use end to end (see sentinel-support-assistant for an application-level test).
- Entries are not reviewed for novelty or for how realistic they are.

## AI assistance

The idea was developed by the repository owner in a long brainstorm with Gemini; Grok and Gemini gave opinions on decisions; the code, tests and seed prompts were written with Claude. The owner made the decisions and directs the project.

MIT licensed.
