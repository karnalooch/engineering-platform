from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "reusable-governance.yml"


class GovernanceWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_dependabot_exception_is_explicit_opt_in(self):
        self.assertRegex(
            self.text,
            re.compile(
                r"allow_dependabot_high_risk_without_manual_marker:\n"
                r"(?:.*\n){0,5}?\s+default:\s+false",
                re.MULTILINE,
            ),
        )

    def test_dependabot_exception_matches_exact_bot_identity(self):
        self.assertIn('pr_author == "dependabot[bot]"', self.text)
        self.assertNotIn('startswith("dependabot")', self.text)

    def test_manual_marker_contract_still_exists(self):
        self.assertIn(
            "'Auto-merge: manual' in the PR body",
            self.text,
        )

    def test_immutable_ref_scanner_covers_inline_list_uses_syntax(self):
        self.assertIn(
            r"(?:-\s*)?uses:",
            self.text,
        )

    def test_exception_is_forwarded_through_explicit_environment(self):
        self.assertIn(
            "ALLOW_DEPENDABOT_HIGH_RISK_WITHOUT_MANUAL_MARKER:",
            self.text,
        )
        self.assertIn(
            "inputs.allow_dependabot_high_risk_without_manual_marker",
            self.text,
        )


if __name__ == "__main__":
    unittest.main()
