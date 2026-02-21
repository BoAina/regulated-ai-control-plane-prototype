"""Interfaces and shared types for pluggable governance modules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol


Decision = str  # APPROVE | REJECT | REQUIRE_REVIEW


@dataclass(frozen=True)
class RuleFinding:
    """Normalized rule-level finding emitted by domain evaluators."""

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
class DecisionResult:
    """Deterministic result envelope emitted by a governance module."""

    decision: Decision
    findings: tuple[RuleFinding, ...]
    requires_review: bool
    policy_version_id: str
    state_snapshot_id: str
    decision_hash_material: dict[str, Any]


class GovernanceModule(Protocol):
    """Contract for domain-specific policy packs."""

    name: str

    def evaluate(
        self,
        *,
        intent: Any,
        snapshot: Any,
        policy_version_id: str,
        now: date | None = None,
    ) -> DecisionResult:
        """Evaluate a request and produce a deterministic decision result."""

    def token_scope_for(self, *, intent: Any, decision: DecisionResult) -> list[str]:
        """Return token scopes that this module authorizes for an APPROVE decision."""

