"""Deterministic auditor orchestration and grants module adapter."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from governance_module import DecisionResult, GovernanceModule, RuleFinding
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


class Auditor:
    """Core orchestrator that delegates rule evaluation to a governance module."""

    def __init__(self, module: GovernanceModule):
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
        violations = [_rule_finding_to_violation(f) for f in result.findings]
        return AuditorDecision(
            decision=result.decision,
            violations=violations,
            requires_review=result.requires_review,
            decision_hash=decision_hash,
            evaluated_at=evaluated_at,
            policy_version_id=result.policy_version_id,
            state_snapshot_id=result.state_snapshot_id,
        )


class GrantsGovernanceModule:
    """Domain module for grants governance policy checks."""

    name = "grants"

    def evaluate(
        self,
        *,
        intent: IntentObject,
        snapshot: GrantSnapshot,
        policy_version_id: str,
        now: date | None = None,
    ) -> DecisionResult:
        evaluation_date = now or date.today()
        findings: list[RuleFinding] = []
        requires_review = False

        # Rule R-PERIOD-001
        if not (snapshot.grant_start_date <= intent.expense_date <= snapshot.grant_end_date):
            findings.append(
                RuleFinding(
                    rule_id="R-PERIOD-001",
                    severity="high",
                    message="Expense date falls outside active grant period.",
                    actual_value=intent.expense_date.isoformat(),
                    expected_condition=f"{snapshot.grant_start_date.isoformat()} <= expense_date <= {snapshot.grant_end_date.isoformat()}",
                )
            )

        # Rule R-BUDGET-002
        if intent.amount > snapshot.budget_remaining:
            findings.append(
                RuleFinding(
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
            findings.append(
                RuleFinding(
                    rule_id="R-ALLOW-003",
                    severity="high",
                    message="Object code is not allowed for this grant policy.",
                    actual_value=intent.object_code,
                    expected_condition="object_code in allowed_object_codes",
                )
            )

        # Rule R-DOC-004
        if not intent.evidence_refs:
            findings.append(
                RuleFinding(
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
            findings.append(
                RuleFinding(
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
        if any(v.severity == "high" for v in findings):
            decision = DECISION_REJECT
            requires_review = False
        elif requires_review:
            decision = DECISION_REQUIRE_REVIEW

        decision_hash_material = {
            "decision": decision,
            "violations": [v.to_dict() for v in findings],
            "requires_review": requires_review,
            "policy_version_id": policy_version_id,
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_hash": snapshot.snapshot_hash,
            "transaction_id": intent.transaction_id,
        }
        return DecisionResult(
            decision=decision,
            findings=tuple(findings),
            requires_review=requires_review,
            policy_version_id=policy_version_id,
            state_snapshot_id=snapshot.snapshot_id,
            decision_hash_material=decision_hash_material,
        )

    def token_scope_for(self, *, intent: IntentObject, decision: DecisionResult) -> list[str]:
        if decision.decision == DECISION_APPROVE:
            return ["post_grant_expense"]
        return []


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


def _rule_finding_to_violation(finding: RuleFinding) -> Violation:
    return Violation(
        rule_id=finding.rule_id,
        severity=finding.severity,
        message=finding.message,
        actual_value=finding.actual_value,
        expected_condition=finding.expected_condition,
    )


def _compute_decision_hash_from_material(material: dict[str, Any]) -> str:
    raw = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
