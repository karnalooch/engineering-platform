from __future__ import annotations

import unittest

from scripts.ci import assert_nonempty, evaluate_aggregate


class AggregateEvaluatorTests(unittest.TestCase):
    def test_required_jobs_must_succeed(self):
        ok, reasons = evaluate_aggregate.evaluate(
            {"lint": {"result": "success"}, "tests": {"result": "success"}},
            ["lint", "tests"],
        )
        self.assertTrue(ok, reasons)

    def test_missing_required_job_fails_closed(self):
        ok, reasons = evaluate_aggregate.evaluate(
            {"lint": {"result": "success"}},
            ["lint", "tests"],
        )
        self.assertFalse(ok)
        self.assertIn("tests: missing required job result", reasons)

    def test_skipped_required_job_fails_without_explicit_allowance(self):
        ok, reasons = evaluate_aggregate.evaluate(
            {"docs": {"result": "skipped"}},
            ["docs"],
        )
        self.assertFalse(ok)
        self.assertIn("expected success, got skipped", reasons[0])

    def test_explicitly_allowed_skip_can_pass(self):
        ok, reasons = evaluate_aggregate.evaluate(
            {"release": {"result": "skipped"}, "policy": {"result": "success"}},
            ["release", "policy"],
            ["release"],
        )
        self.assertTrue(ok, reasons)

    def test_empty_expected_set_is_rejected(self):
        ok, reasons = evaluate_aggregate.evaluate({}, [])
        self.assertFalse(ok)
        self.assertIn("no-op", reasons[0])


class AntiNoopTests(unittest.TestCase):
    def test_zero_matches_fail_by_default(self):
        ok, detail = assert_nonempty.evaluate(0)
        self.assertFalse(ok)
        self.assertIn("expected at least 1", detail)

    def test_positive_match_count_passes(self):
        ok, detail = assert_nonempty.evaluate(3)
        self.assertTrue(ok)
        self.assertIn("matched 3", detail)


if __name__ == "__main__":
    unittest.main()
