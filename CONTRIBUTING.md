# Add an attack (or a harmless prompt)

1. Fork the repository.
2. Add one new file: `submissions/community-<your-handle>.jsonl`. One JSON object per line:

```json
{"id":"yourhandle-001","kind":"attack","type":"direct-override","text":"your prompt here","author":"yourhandle","origin":"community"}
```

- `id`: 3-40 characters, `a-z`, `0-9`, `-`; unique across the repository.
- `kind`: `attack` or `harmless`.
- `type` for attacks: direct-override, persona-roleplay, hypothetical-fiction, fake-turns, code-or-data, authority, exfiltration-link, tool-misuse, pasted-content, encoding, lookalike-chars, non-english, prompt-extraction.
- `type` for harmless prompts: plain, security-discussion, instruction-words.
- `text`: up to 2000 characters. `origin` must be `community`.

3. Check it: `pip install . && arena validate submissions`
4. Open a pull request. CI scores it and shows the result in the run summary. The results page updates after merge.

Harmless prompts are as valuable as attacks: a guard that blocks everything is useless. Good harmless prompts look suspicious but are not (for example "please ignore the typo in my last message").

Rules: no real secrets or personal data; nothing that is harmful beyond demonstrating prompt injection; no attempts to attack the repository, CI or other people. A submission that gets through is not a bug in this repo; it is the point. Maintainers may remove entries that break these rules.
