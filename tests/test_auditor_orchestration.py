"""Tests for module-driven auditor orchestration."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auditor import (  # noqa: E402
    DECISION_APPROVE,
    Auditor,
    GrantSnapshot,
    GrantsGovernanceModule,
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


class TestAuditorOrchestration(unittest.TestCase):
    def test_orchestrator_matches_wrapper_behavior(self) -> None:
        intent = validate_intent(_base_payload())
        snapshot = _base_snapshot()

        via_wrapper = evaluate_grant_intent(
            intent, snapshot, policy_version_id="policy_v1", now=date(2026, 2, 20)
        )
        via_orchestrator = Auditor(module=GrantsGovernanceModule()).run(
            intent=intent,
            snapshot=snapshot,
            policy_version_id="policy_v1",
            now=date(2026, 2, 20),
        )

        self.assertEqual(via_wrapper.decision, DECISION_APPROVE)
        self.assertEqual(via_orchestrator.decision, via_wrapper.decision)
        self.assertEqual(via_orchestrator.requires_review, via_wrapper.requires_review)
        self.assertEqual(via_orchestrator.state_snapshot_id, via_wrapper.state_snapshot_id)
        self.assertEqual(via_orchestrator.policy_version_id, via_wrapper.policy_version_id)
        self.assertEqual(len(via_orchestrator.violations), len(via_wrapper.violations))


if __name__ == "__main__":
    unittest.main()

