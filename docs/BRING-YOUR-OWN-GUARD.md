# Bring your own guard

Sentinel Arena can score any prompt filter, not just Sentinel. It runs your guard on the same public attacks and harmless prompts and tells you what it stops, what it misses, and what it wrongly blocks. You need Python 3.10+ and nothing else.

## 1. Write a function

A guard is one function: take the prompt text, return `True` to block, `False` to allow.

```python
# my_guard.py
def blocked(text: str) -> bool:
    return "ignore previous instructions" in text.lower()
```

If your guard cannot decide (a model call times out, an API is down), **raise an exception**. The arena aborts the run rather than counting "no answer" as a pass, so a flaky guard cannot look better than it is.

## 2. Score it

```bash
git clone https://github.com/yurtseveronder-design/sentinel-arena
cd sentinel-arena
pip install .
arena run --guard python:/path/to/my_guard.py:blocked --out my-results
```

Open `my-results/index.html` (a static page, no JavaScript) or read `my-results/results.json`. A working example is in `examples/my_guard.py`:

```bash
arena run --guard python:examples/my_guard.py:blocked --out example-results
```

Other guard types: `--guard http:<url>` for a running ai-sentinel gateway, `--guard python:package.module:function` for an installed module.

## 3. Compare two guards

Run the arena once per guard into two folders, then:

```bash
arena gate --baseline guard-a/results.json --candidate guard-b/results.json
```

The gate fails if the candidate lets through an attack the baseline stopped, adds a wrongly blocked harmless prompt, is much slower, or stops no additional holdout attack. It returns INCONCLUSIVE when the holdout sample is too small to decide, which is the usual answer today.

## 4. Read the result honestly

- **Both numbers matter.** A guard that blocks everything scores 100% on attacks and fails the harmless prompts.
- **The attacks are public.** Tuning your guard to this set will raise your score without making it more robust. Use the `dev` split (shown on the results page) for any tuning and treat `holdout` only as a check. About 20% of entries are holdout, chosen by a hash of the prompt text plus a salt.
- **Most seed attacks were written by the project builder** and are not independent. Community entries are reported separately.
- **Small numbers are noisy.** With a few dozen entries, a difference of one or two prompts is not a real difference.
- **Prompts only.** This does not test retrieval pipelines, tool use or a real model behind the guard.

## 5. Add what you found

If your guard stops something Sentinel misses, or the other way round, that is the interesting part. [Open the Try an attack form](https://github.com/yurtseveronder-design/sentinel-arena/issues/new?template=try-an-attack.yml) or send a pull request (see CONTRIBUTING.md).
