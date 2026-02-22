"""Unit tests for intent schema validation."""

from __future__ import annotations

import unittest
from datetime import date

from intent_schema import IntentValidationError, IntentObject, validate_intent


def _valid_payload() -> dict[str, object]:
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


class TestValidateIntent(unittest.TestCase):
    def test_valid_payload_returns_intent_object(self) -> None:
        intent = validate_intent(_valid_payload())
        self.assertIsInstance(intent, IntentObject)
        self.assertEqual(intent.transaction_id, "txn_001")
        self.assertEqual(intent.grant_id, "GRANT-2026-001")
        self.assertEqual(intent.amount, 5000.0)
        self.assertEqual(intent.model_confidence, 0.95)
        self.assertEqual(intent.risk_class, "low")
        self.assertEqual(intent.evidence_refs, ["file_01"])
        self.assertEqual(intent.currency, "USD")
        self.assertEqual(intent.object_code, "EQUIPMENT")

    def test_missing_required_field_raises(self) -> None:
        payload = _valid_payload()
        del payload["grant_id"]
        with self.assertRaises(IntentValidationError):
            validate_intent(payload)

    def test_amount_as_bool_raises(self) -> None:
        # bool is a subclass of int; validate_intent must reject it
        payload = _valid_payload()
        payload["amount"] = True
        with self.assertRaises(IntentValidationError):
            validate_intent(payload)

    def test_amount_zero_raises(self) -> None:
        payload = _valid_payload()
        payload["amount"] = 0.0
        with self.assertRaises(IntentValidationError):
            validate_intent(payload)

    def test_amount_negative_raises(self) -> None:
        payload = _valid_payload()
        payload["amount"] = -100.0
        with self.assertRaises(IntentValidationError):
            validate_intent(payload)

    def test_model_confidence_above_one_raises(self) -> None:
        payload = _valid_payload()
        payload["model_confidence"] = 1.1
        with self.assertRaises(IntentValidationError):
            validate_intent(payload)

    def test_model_confidence_below_zero_raises(self) -> None:
        payload = _valid_payload()
        payload["model_confidence"] = -0.1
        with self.assertRaises(IntentValidationError):
            validate_intent(payload)

    def test_invalid_risk_class_raises(self) -> None:
        payload = _valid_payload()
        payload["risk_class"] = "critical"
        with self.assertRaises(IntentValidationError):
            validate_intent(payload)

    def test_empty_evidence_refs_raises(self) -> None:
        payload = _valid_payload()
        payload["evidence_refs"] = []
        with self.assertRaises(IntentValidationError):
            validate_intent(payload)

    def test_invalid_expense_date_format_raises(self) -> None:
        payload = _valid_payload()
        payload["expense_date"] = "15-02-2026"
        with self.assertRaises(IntentValidationError):
            validate_intent(payload)

    def test_to_dict_serializes_dates_as_iso_strings(self) -> None:
        intent = validate_intent(_valid_payload())
        output = intent.to_dict()
        self.assertEqual(output["expense_date"], "2026-02-15")
        self.assertEqual(output["posting_date"], "2026-02-20")
        self.assertIsInstance(output["expense_date"], str)
        self.assertIsInstance(output["posting_date"], str)

    def test_non_dict_payload_raises(self) -> None:
        with self.assertRaises(IntentValidationError):
            validate_intent("not a dict")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
