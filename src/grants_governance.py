"""Grants domain governance module implementing the GovernanceModule protocol."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from governance_module import DecisionResult, GovernanceModule, RuleFinding
from intent_schema import IntentObject

if TYPE_CHECKING:
    from auditor import GrantSnapshot


DECISION_APPROVE = "APPROVE"
DECISION_REJECT = "REJECT"
DECISION_REQUIRE_REVIEW = "REQUIRE_REVIEW"


class GrantsGovernanceModule(GovernanceModule):
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
