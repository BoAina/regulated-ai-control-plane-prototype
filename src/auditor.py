"""Deterministic auditor orchestration and data models."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from governance_module import DecisionResult, GovernanceModule, RuleFinding
from grants_governance import GrantsGovernanceModule
from intent_schema import IntentObject


@dataclass(frozen=True)
class GrantSnapshot:
    """Read-model snapshot materialized from ERP source tables."""

    snapshot_id: str
    snapshot_hash: str
    as_of_date: date
    grant_start_date: date
    grant_end_date: date
    budget_remaining: float
    allowed_object_codes: set[str]
    high_dollar_threshold: float = 10000.0
    max_snapshot_age_days: int = 1


@dataclass(frozen=True)
class AuditorDecision:
    """Outcome from deterministic rule evaluation."""

    decision: str
    violations: list[RuleFinding] = field(default_factory=list)
    requires_review: bool = False
    decision_hash: str = ""
    evaluated_at: str = ""
    policy_version_id: str = ""
    state_snapshot_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "violations": [v.to_dict() for v in self.violations],
            "requires_review": self.requires_review,
            "decision_hash": self.decision_hash,
            "evaluated_at": self.evaluated_at,
            "policy_version_id": self.policy_version_id,
            "state_snapshot_id": self.state_snapshot_id,
        }


class Auditor:
    """Core orchestrator that delegates rule evaluation to a governance module."""

    module: GovernanceModule

    def __init__(self, module: GovernanceModule) -> None:
        self.module = module

    def run(
        self,
        *,
        intent: Any,
        snapshot: Any,
        policy_version_id: str,
        now: date | None = None,
    ) -> AuditorDecision:
        result = self.module.evaluate(
            intent=intent,
            snapshot=snapshot,
            policy_version_id=policy_version_id,
            now=now,
        )
        decision_hash = _compute_decision_hash_from_material(result.decision_hash_material)
        evaluated_at = datetime.now(timezone.utc).isoformat()
        return AuditorDecision(
            decision=result.decision,
            violations=list(result.findings),
            requires_review=result.requires_review,
            decision_hash=decision_hash,
            evaluated_at=evaluated_at,
            policy_version_id=result.policy_version_id,
            state_snapshot_id=result.state_snapshot_id,
        )


def evaluate_grant_intent(
    intent: IntentObject,
    snapshot: GrantSnapshot,
    policy_version_id: str,
    now: date | None = None,
) -> AuditorDecision:
    """Evaluate intent against deterministic grant policy rules."""
    return Auditor(module=GrantsGovernanceModule()).run(
        intent=intent,
        snapshot=snapshot,
        policy_version_id=policy_version_id,
        now=now,
    )


def _compute_decision_hash_from_material(material: dict[str, Any]) -> str:
    raw = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
