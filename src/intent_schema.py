"""Structured intent contract and validation helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


ALLOWED_RISK_CLASSES = {"low", "medium", "high"}


class IntentValidationError(ValueError):
    """Raised when an intent payload fails validation."""


@dataclass(frozen=True)
class IntentObject:
    """Typed representation of model-generated intent."""

    transaction_id: str
    grant_id: str
    org_unit: str
    amount: float
    currency: str
    object_code: str
    expense_date: date
    posting_date: date
    description: str
    evidence_refs: list[str]
    model_confidence: float
    risk_class: str
    rationale_summary: str

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the intent."""
        output = asdict(self)
        output["expense_date"] = self.expense_date.isoformat()
        output["posting_date"] = self.posting_date.isoformat()
        return output


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise IntentValidationError(f"{field} must be a non-empty string")
    return value.strip()


def _required_float(payload: dict[str, Any], field: str) -> float:
    value = payload.get(field)
    if isinstance(value, bool):  # bool is a subclass of int
        raise IntentValidationError(f"{field} must be a numeric value")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise IntentValidationError(f"{field} must be a numeric value") from exc
    return number


def _required_date(payload: dict[str, Any], field: str) -> date:
    value = _required_string(payload, field)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise IntentValidationError(f"{field} must be in YYYY-MM-DD format") from exc


def validate_intent(payload: dict[str, Any]) -> IntentObject:
    """Validate raw model output and return a typed intent object."""
    if not isinstance(payload, dict):
        raise IntentValidationError("payload must be a dictionary")

    amount = _required_float(payload, "amount")
    if amount <= 0:
        raise IntentValidationError("amount must be greater than 0")

    model_confidence = _required_float(payload, "model_confidence")
    if model_confidence < 0 or model_confidence > 1:
        raise IntentValidationError("model_confidence must be between 0 and 1")

    risk_class = _required_string(payload, "risk_class").lower()
    if risk_class not in ALLOWED_RISK_CLASSES:
        allowed = ", ".join(sorted(ALLOWED_RISK_CLASSES))
        raise IntentValidationError(f"risk_class must be one of: {allowed}")

    evidence_refs_raw = payload.get("evidence_refs", [])
    if not isinstance(evidence_refs_raw, list):
        raise IntentValidationError("evidence_refs must be a list of strings")
    evidence_refs = [x.strip() for x in evidence_refs_raw if isinstance(x, str) and x.strip()]
    if not evidence_refs:
        raise IntentValidationError("at least one evidence reference is required")

    return IntentObject(
        transaction_id=_required_string(payload, "transaction_id"),
        grant_id=_required_string(payload, "grant_id"),
        org_unit=_required_string(payload, "org_unit"),
        amount=amount,
        currency=_required_string(payload, "currency").upper(),
        object_code=_required_string(payload, "object_code").upper(),
        expense_date=_required_date(payload, "expense_date"),
        posting_date=_required_date(payload, "posting_date"),
        description=_required_string(payload, "description"),
        evidence_refs=evidence_refs,
        model_confidence=model_confidence,
        risk_class=risk_class,
        rationale_summary=_required_string(payload, "rationale_summary"),
    )

