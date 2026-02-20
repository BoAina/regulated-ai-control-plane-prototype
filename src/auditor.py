"""Deterministic grant expenditure auditor."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from intent_schema import IntentObject


DECISION_APPROVE = "APPROVE"
DECISION_REJECT = "REJECT"
DECISION_REQUIRE_REVIEW = "REQUIRE_REVIEW"


@dataclass(frozen=True)
class Violation:
    """Represents a deterministic policy violation."""

    rule_id: str
    severity: str
    message: str
    actual_value: str
    expected_condition: str

    def to_dict(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "actual_value": self.actual_value,
            "expected_condition": self.expected_condition,
        }


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
    violations: list[Violation] = field(default_factory=list)
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


def evaluate_grant_intent(
    intent: IntentObject,
    snapshot: GrantSnapshot,
    policy_version_id: str,
    now: date | None = None,
) -> AuditorDecision:
    """Evaluate intent against deterministic grant policy rules."""
    evaluation_date = now or date.today()
    violations: list[Violation] = []
    requires_review = False

    # Rule R-PERIOD-001
    if not (snapshot.grant_start_date <= intent.expense_date <= snapshot.grant_end_date):
        violations.append(
            Violation(
                rule_id="R-PERIOD-001",
                severity="high",
                message="Expense date falls outside active grant period.",
                actual_value=intent.expense_date.isoformat(),
                expected_condition=f"{snapshot.grant_start_date.isoformat()} <= expense_date <= {snapshot.grant_end_date.isoformat()}",
            )
        )

    # Rule R-BUDGET-002
    if intent.amount > snapshot.budget_remaining:
        violations.append(
            Violation(
                rule_id="R-BUDGET-002",
                severity="high",
                message="Requested amount exceeds remaining grant budget.",
                actual_value=str(intent.amount),
                expected_condition=f"amount <= {snapshot.budget_remaining}",
            )
        )

    # Rule R-ALLOW-003
    allowed_codes = {code.upper() for code in snapshot.allowed_object_codes}
    if intent.object_code.upper() not in allowed_codes:
        violations.append(
            Violation(
                rule_id="R-ALLOW-003",
                severity="high",
                message="Object code is not allowed for this grant policy.",
                actual_value=intent.object_code,
                expected_condition="object_code in allowed_object_codes",
            )
        )

    # Rule R-DOC-004
    if not intent.evidence_refs:
        violations.append(
            Violation(
                rule_id="R-DOC-004",
                severity="medium",
                message="Supporting evidence is missing.",
                actual_value="[]",
                expected_condition="len(evidence_refs) > 0",
            )
        )

    # Rule R-SNAP-008
    snapshot_age_days = (evaluation_date - snapshot.as_of_date).days
    if snapshot_age_days > snapshot.max_snapshot_age_days:
        violations.append(
            Violation(
                rule_id="R-SNAP-008",
                severity="high",
                message="Snapshot age exceeds freshness threshold.",
                actual_value=str(snapshot_age_days),
                expected_condition=f"snapshot_age_days <= {snapshot.max_snapshot_age_days}",
            )
        )

    # Rule R-THRESH-005
    if intent.amount >= snapshot.high_dollar_threshold:
        requires_review = True

    # Risk and confidence based routing
    if intent.risk_class in {"medium", "high"}:
        requires_review = True
    if intent.model_confidence < 0.85:
        requires_review = True

    decision = DECISION_APPROVE
    if any(v.severity == "high" for v in violations):
        decision = DECISION_REJECT
        requires_review = False
    elif requires_review:
        decision = DECISION_REQUIRE_REVIEW

    evaluated_at = datetime.now(timezone.utc).isoformat()
    decision_hash = _compute_decision_hash(
        decision=decision,
        violations=violations,
        requires_review=requires_review,
        policy_version_id=policy_version_id,
        snapshot_id=snapshot.snapshot_id,
        snapshot_hash=snapshot.snapshot_hash,
        transaction_id=intent.transaction_id,
    )

    return AuditorDecision(
        decision=decision,
        violations=violations,
        requires_review=requires_review,
        decision_hash=decision_hash,
        evaluated_at=evaluated_at,
        policy_version_id=policy_version_id,
        state_snapshot_id=snapshot.snapshot_id,
    )


def _compute_decision_hash(
    *,
    decision: str,
    violations: list[Violation],
    requires_review: bool,
    policy_version_id: str,
    snapshot_id: str,
    snapshot_hash: str,
    transaction_id: str,
) -> str:
    serialized = {
        "decision": decision,
        "violations": [v.to_dict() for v in violations],
        "requires_review": requires_review,
        "policy_version_id": policy_version_id,
        "snapshot_id": snapshot_id,
        "snapshot_hash": snapshot_hash,
        "transaction_id": transaction_id,
    }
    raw = json.dumps(serialized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

