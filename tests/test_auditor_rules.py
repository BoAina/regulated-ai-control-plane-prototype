"""Unit tests for deterministic auditor rules."""

from __future__ import annotations

import unittest
from datetime import date, timedelta

from auditor import GrantSnapshot, evaluate_grant_intent
from grants_governance import DECISION_APPROVE, DECISION_REJECT, DECISION_REQUIRE_REVIEW
from intent_schema import validate_intent

from conftest import base_payload, base_snapshot


class TestAuditorRules(unittest.TestCase):
    def test_approve_clean_transaction(self) -> None:
        intent = validate_intent(base_payload())
        snapshot = base_snapshot()
        decision = evaluate_grant_intent(
            intent, snapshot, policy_version_id="policy_v1", now=date(2026, 2, 20)
        )
        self.assertEqual(decision.decision, DECISION_APPROVE)
        self.assertFalse(decision.requires_review)
        self.assertEqual(decision.violations, [])
        self.assertTrue(decision.decision_hash)

    def test_reject_disallowed_object_code(self) -> None:
        payload = base_payload()
        payload["object_code"] = "TRAVEL"
        intent = validate_intent(payload)
        snapshot = base_snapshot()
        decision = evaluate_grant_intent(
            intent, snapshot, policy_version_id="policy_v1", now=date(2026, 2, 20)
        )
        self.assertEqual(decision.decision, DECISION_REJECT)
        self.assertFalse(decision.requires_review)
        self.assertTrue(any(v.rule_id == "R-ALLOW-003" for v in decision.violations))

    def test_require_review_for_high_dollar(self) -> None:
        payload = base_payload()
        payload["amount"] = 12000.0
        intent = validate_intent(payload)
        snapshot = base_snapshot()
        decision = evaluate_grant_intent(
            intent, snapshot, policy_version_id="policy_v1", now=date(2026, 2, 20)
        )
        self.assertEqual(decision.decision, DECISION_REQUIRE_REVIEW)
        self.assertTrue(decision.requires_review)
        self.assertEqual(decision.violations, [])

    def test_reject_for_stale_snapshot(self) -> None:
        intent = validate_intent(base_payload())
        snapshot = base_snapshot()
        stale_now = snapshot.as_of_date + timedelta(days=3)
        decision = evaluate_grant_intent(
            intent, snapshot, policy_version_id="policy_v1", now=stale_now
        )
        self.assertEqual(decision.decision, DECISION_REJECT)
        self.assertTrue(any(v.rule_id == "R-SNAP-008" for v in decision.violations))


if __name__ == "__main__":
    unittest.main()
