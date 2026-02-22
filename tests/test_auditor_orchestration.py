"""Tests for module-driven auditor orchestration."""

from __future__ import annotations

import unittest
from datetime import date

from auditor import Auditor, GrantSnapshot, evaluate_grant_intent
from grants_governance import DECISION_APPROVE, GrantsGovernanceModule
from intent_schema import validate_intent

from conftest import base_payload, base_snapshot


class TestAuditorOrchestration(unittest.TestCase):
    def test_orchestrator_matches_wrapper_behavior(self) -> None:
        intent = validate_intent(base_payload())
        snapshot = base_snapshot()

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
