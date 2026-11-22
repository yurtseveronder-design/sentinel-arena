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

## Weekly digest (read-only)

A scheduled job (`.github/workflows/digest.yml`, Mondays, or run it by hand) scores everything again and compares with the last snapshot. If anything changed it commits `history/<date>.json` and `known-gaps.jsonl` (every attack that currently gets through and every harmless prompt wrongly blocked, with the date first seen) and opens an issue for a human to review. It never changes a guard or its rules.

Each submission is assigned to a `dev` or `holdout` split by a hash of its id (about 20% holdout; submitters cannot choose). If you ever tune or draft rules from these gaps, use `dev` only and use `holdout` to check whether it helped. Be careful anyway: the attacks are public, so a rising score can mean overfitting.

```bash
arena digest --results site/results.json   # after `arena run --out site`
```

## Learning loop (proposals only; Sentinel is not touched)

`arena propose` mines candidate block-phrases from `dev` gaps only: a word sequence must appear in at least two gap attacks and in no harmless prompt. Output goes to `proposals/candidates.json` and is applied nowhere. To see what a reviewed list would do: `arena run --guard overlay:proposals/candidates.json --out site2`, then `arena gate`. An overlay can only add blocks, never allow anything. Adopting a phrase into `ai-sentinel` itself is a separate, deliberate, human-made release.

Honest warning: with the current builder-written seed set the miner mostly memorises my own test wording (for example the fake domain `evil.example`). It stops dev attacks but not holdout ones, which is exactly what the gate is there to expose. It becomes useful only with many independent community submissions.

## Promotion gate (read-only)

`arena gate --baseline base/results.json --candidate cand/results.json` compares two runs of the same submission set (run `arena run` once in an environment with the current guard, once with a candidate change). Exit code 0 = PASS, 1 = FAIL, 3 = INCONCLUSIVE.

- FAIL: any attack the baseline stopped now gets through; any new wrongly blocked harmless prompt (default allowed: 0); median latency over budget (default max 2x baseline and 50 ms); the submission sets differ.
- INCONCLUSIVE: fewer than 30 holdout attacks or 15 holdout harmless prompts. Never promote on INCONCLUSIVE. Today the holdout is far smaller than that.
- The holdout is a public hash split, not a sealed set, so repeated gating against it overfits. A sealed holdout would have to be kept privately by the maintainer.
- The gate only reports. It does not change or deploy anything, and a human still merges.

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
