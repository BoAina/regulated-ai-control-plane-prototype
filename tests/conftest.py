"""Shared test fixtures for auditor tests."""

from __future__ import annotations

from datetime import date

from auditor import GrantSnapshot


def base_payload() -> dict[str, object]:
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


def base_snapshot() -> GrantSnapshot:
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
