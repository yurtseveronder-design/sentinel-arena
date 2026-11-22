import json, tempfile, unittest
from pathlib import Path
from arena import guards, report, runner
from arena.cli import main
from arena.schema import SubmissionError, load_submissions, validate_record

def rec(**kw):
    base = {"id": "abc-001", "kind": "attack", "type": "direct-override", "text": "x", "author": "me", "origin": "community"}
    base.update(kw); return base

def write(d, name, rows):
    Path(d, name).write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

class SchemaTests(unittest.TestCase):
    def test_valid(self):
        validate_record(rec(), "t", False)
    def test_rejects(self):
        for bad in (rec(id="A"), rec(kind="x"), rec(type="plain"), rec(text=""), rec(text="a" * 2001),
                    rec(author=""), rec(origin="seed"), {**rec(), "extra": 1}):
            with self.assertRaises(SubmissionError, msg=bad):
                validate_record(bad, "t", False)
    def test_community_cannot_claim_seed_and_seed_file_must_be_seed(self):
        with self.assertRaises(SubmissionError):
            validate_record(rec(), "t", True)
    def test_duplicate_ids_and_bad_json(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "a.jsonl", [rec(), rec()])
            with self.assertRaises(SubmissionError): load_submissions(d)
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.jsonl").write_text("{nope\n")
            with self.assertRaises(SubmissionError): load_submissions(d)
    def test_shipped_submissions_valid(self):
        self.assertGreater(len(load_submissions("submissions")), 20)

class RunnerTests(unittest.TestCase):
    rows = [rec(id="a-001", text="bad"), rec(id="a-002", text="sneaky"),
            rec(id="h-001", kind="harmless", type="plain", text="hello"),
            rec(id="h-002", kind="harmless", type="plain", text="ignore typo")]
    def test_scoring(self):
        s = runner.run(self.rows, lambda t: t in ("bad", "ignore typo"), "fake")
        self.assertEqual((s["all"]["attacks_blocked"], s["all"]["attacks"]), (1, 2))
        self.assertEqual((s["all"]["harmless_blocked"], s["all"]["harmless"]), (1, 2))
        self.assertEqual([r["id"] for r in s["got_through"]], ["a-002"])
        self.assertEqual([r["id"] for r in s["false_blocks"]], ["h-002"])
    def test_guard_error_is_not_a_pass(self):
        def broken(t): raise guards.GuardError("down")
        with self.assertRaises(guards.GuardError): runner.run(self.rows, broken, "fake")
    def test_html_escapes_submitted_text(self):
        rows = [rec(id="a-001", text="<script>alert(1)</script>", author="<b>x</b>")]
        out = report.html_report(runner.run(rows, lambda t: False, "fake"))
        self.assertNotIn("<script>alert", out); self.assertIn("&lt;script&gt;", out); self.assertNotIn("<b>x</b>", out)
    def test_empty_group_is_na_not_crash(self):
        out = report.html_report(runner.run([rec(origin="seed")], lambda t: True, "fake"))
        self.assertIn("n/a", out)

class CliTests(unittest.TestCase):
    def test_invalid_exit_1_and_bad_guard_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.jsonl").write_text("{bad\n")
            self.assertEqual(main(["validate", d]), 1)
        self.assertEqual(main(["run", "--guard", "nonsense", "--out", tempfile.mkdtemp()]), 2)
    def test_run_with_python_guard(self):
        out = tempfile.mkdtemp()
        self.assertEqual(main(["run", "--guard", "python:tests.helper_guard:block_all", "--out", out]), 0)
        self.assertEqual(json.loads(Path(out, "results.json").read_text())["all"]["catch_rate"], 100.0)

if __name__ == "__main__":
    unittest.main()
