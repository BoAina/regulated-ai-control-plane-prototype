"""Unit tests for deterministic auditor rules."""

from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auditor import (  # noqa: E402
    DECISION_APPROVE,
    DECISION_REJECT,
    DECISION_REQUIRE_REVIEW,
    GrantSnapshot,
    evaluate_grant_intent,
)
from intent_schema import validate_intent  # noqa: E402


def _base_payload() -> dict[str, object]:
    return {
        "transaction_id": "txn_001",
        "grant_id": "GRANT-2026-001",
        "org_unit": "HLS-ONC",
        "amount": 5000.0,
        "currency": "USD",
        "object_code": "EQUIPMENT",
        "expense_date": "2026-02-15",
        "posting_date": "2026-02-20",
        "description": "PCR thermal cycler replacement",
        "evidence_refs": ["file_01"],
        "model_confidence": 0.95,
        "risk_class": "low",
        "rationale_summary": "Allowable under sponsor category and period.",
    }


def _base_snapshot() -> GrantSnapshot:
    return GrantSnapshot(
        snapshot_id="snap_2026_02_20",
        snapshot_hash="sha256:snapshot123",
        as_of_date=date(2026, 2, 20),
        grant_start_date=date(2026, 1, 1),
        grant_end_date=date(2026, 12, 31),
        budget_remaining=25000.0,
        allowed_object_codes={"EQUIPMENT", "SUPPLIES"},
        high_dollar_threshold=10000.0,
        max_snapshot_age_days=1,
    )


class TestAuditorRules(unittest.TestCase):
    def test_approve_clean_transaction(self) -> None:
        intent = validate_intent(_base_payload())
        snapshot = _base_snapshot()
        decision = evaluate_grant_intent(
            intent, snapshot, policy_version_id="policy_v1", now=date(2026, 2, 20)
        )
        self.assertEqual(decision.decision, DECISION_APPROVE)
        self.assertFalse(decision.requires_review)
        self.assertEqual(decision.violations, [])
        self.assertTrue(decision.decision_hash)

    def test_reject_disallowed_object_code(self) -> None:
        payload = _base_payload()
        payload["object_code"] = "TRAVEL"
        intent = validate_intent(payload)
        snapshot = _base_snapshot()
        decision = evaluate_grant_intent(
            intent, snapshot, policy_version_id="policy_v1", now=date(2026, 2, 20)
        )
        self.assertEqual(decision.decision, DECISION_REJECT)
        self.assertFalse(decision.requires_review)
        self.assertTrue(any(v.rule_id == "R-ALLOW-003" for v in decision.violations))

    def test_require_review_for_high_dollar(self) -> None:
        payload = _base_payload()
        payload["amount"] = 12000.0
        intent = validate_intent(payload)
        snapshot = _base_snapshot()
        decision = evaluate_grant_intent(
            intent, snapshot, policy_version_id="policy_v1", now=date(2026, 2, 20)
        )
        self.assertEqual(decision.decision, DECISION_REQUIRE_REVIEW)
        self.assertTrue(decision.requires_review)
        self.assertEqual(decision.violations, [])

    def test_reject_for_stale_snapshot(self) -> None:
        intent = validate_intent(_base_payload())
        snapshot = _base_snapshot()
        stale_now = snapshot.as_of_date + timedelta(days=3)
        decision = evaluate_grant_intent(
            intent, snapshot, policy_version_id="policy_v1", now=stale_now
        )
        self.assertEqual(decision.decision, DECISION_REJECT)
        self.assertTrue(any(v.rule_id == "R-SNAP-008" for v in decision.violations))


if __name__ == "__main__":
    unittest.main()

