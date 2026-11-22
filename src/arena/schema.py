"""Submission format and validation. One JSON object per line in submissions/*.jsonl."""
from __future__ import annotations

import json
import re
from pathlib import Path

ATTACK_TYPES = {
    "direct-override": "Tell the model to ignore its rules",
    "persona-roleplay": "Persona, role-play or 'developer mode' framing",
    "hypothetical-fiction": "Hypothetical, story or fiction framing",
    "fake-turns": "Fake conversation turns or fake system messages",
    "code-or-data": "Instruction hidden inside code or structured data",
    "authority": "Pretending to be an authority (admin, CEO, security team)",
    "exfiltration-link": "Leaking data through a link or an image",
    "tool-misuse": "Misusing an agent's tools",
    "pasted-content": "Instruction hidden in pasted content (email, ticket, web page)",
    "encoding": "Encoded or obfuscated text",
    "lookalike-chars": "Look-alike letters and other character tricks",
    "non-english": "Non-English phrasing",
    "prompt-extraction": "Trying to reveal the system prompt",
}
HARMLESS_TYPES = {
    "plain": "Ordinary harmless request",
    "security-discussion": "Harmless text that discusses attacks or security",
    "instruction-words": "Harmless text that uses words like 'ignore', 'system' or 'override'",
}
KINDS = ("attack", "harmless")
ORIGINS = ("seed", "community")
MAX_TEXT = 2000
_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,39}$")
_FIELDS = {"id", "kind", "type", "text", "author", "origin"}


class SubmissionError(ValueError):
    pass


def validate_record(rec: dict, where: str, seed_file: bool) -> None:
    if not isinstance(rec, dict):
        raise SubmissionError(f"{where}: each line must be a JSON object")
    extra, missing = set(rec) - _FIELDS, _FIELDS - set(rec)
    if missing:
        raise SubmissionError(f"{where}: missing fields {sorted(missing)}")
    if extra:
        raise SubmissionError(f"{where}: unknown fields {sorted(extra)}")
    if not isinstance(rec["id"], str) or not _ID.match(rec["id"]):
        raise SubmissionError(f"{where}: id must be 3-40 chars of a-z, 0-9 and '-'")
    if rec["kind"] not in KINDS:
        raise SubmissionError(f"{where}: kind must be one of {KINDS}")
    allowed = ATTACK_TYPES if rec["kind"] == "attack" else HARMLESS_TYPES
    if rec["type"] not in allowed:
        raise SubmissionError(f"{where}: type {rec['type']!r} is not allowed for kind {rec['kind']!r}; choose from {sorted(allowed)}")
    if not isinstance(rec["text"], str) or not rec["text"].strip() or len(rec["text"]) > MAX_TEXT:
        raise SubmissionError(f"{where}: text must be 1-{MAX_TEXT} characters")
    if not isinstance(rec["author"], str) or not 1 <= len(rec["author"]) <= 40:
        raise SubmissionError(f"{where}: author must be 1-40 characters (a GitHub handle is fine)")
    if rec["origin"] not in ORIGINS:
        raise SubmissionError(f"{where}: origin must be one of {ORIGINS}")
    if seed_file and rec["origin"] != "seed":
        raise SubmissionError(f"{where}: seed files must use origin 'seed'")
    if not seed_file and rec["origin"] != "community":
        raise SubmissionError(f"{where}: only seed*.jsonl files may use origin 'seed'; use 'community'")


def load_submissions(directory: str | Path) -> list[dict]:
    records, seen = [], {}
    for path in sorted(Path(directory).glob("*.jsonl")):
        seed_file = path.name.startswith("seed")
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            where = f"{path.name}:{n}"
            try:
                rec = json.loads(line)
            except ValueError as e:
                raise SubmissionError(f"{where}: invalid JSON ({e})") from e
            validate_record(rec, where, seed_file)
            if rec["id"] in seen:
                raise SubmissionError(f"{where}: duplicate id {rec['id']!r} (also in {seen[rec['id']]})")
            seen[rec["id"]] = where
            records.append(rec)
    if not records:
        raise SubmissionError(f"no submissions found in {directory}")
    return records
