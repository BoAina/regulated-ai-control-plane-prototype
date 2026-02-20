"""Unit tests for token issuance and validation."""

from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from token_gateway import (  # noqa: E402
    TokenClaims,
    TokenValidationError,
    issue_token,
    validate_token,
)


class TestTokenValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = "dev-secret-123"
        self.claims = TokenClaims.new(
            request_id="req_001",
            transaction_id="txn_001",
            decision_hash="sha256:decision123",
            policy_version_id="policy_v1",
            state_snapshot_hash="sha256:snap123",
            scope=["post_grant_expense"],
            ttl_seconds=300,
        )

    def test_issue_and_validate_success(self) -> None:
        token = issue_token(self.claims, self.secret)
        validated = validate_token(token, self.secret, required_scope="post_grant_expense")
        self.assertEqual(validated.request_id, self.claims.request_id)
        self.assertEqual(validated.transaction_id, self.claims.transaction_id)

    def test_reject_invalid_signature(self) -> None:
        token = issue_token(self.claims, self.secret)
        with self.assertRaises(TokenValidationError):
            validate_token(token, "wrong-secret", required_scope="post_grant_expense")

    def test_reject_missing_scope(self) -> None:
        token = issue_token(self.claims, self.secret)
        with self.assertRaises(TokenValidationError):
            validate_token(token, self.secret, required_scope="post_invoice")

    def test_reject_expired_token(self) -> None:
        expired_claims = TokenClaims(
            token_id="tok_expired",
            request_id="req_002",
            transaction_id="txn_002",
            decision_hash="sha256:old",
            policy_version_id="policy_v1",
            state_snapshot_hash="sha256:snapold",
            scope=["post_grant_expense"],
            issued_at=(datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
            expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            one_time_use=True,
        )
        token = issue_token(expired_claims, self.secret)
        with self.assertRaises(TokenValidationError):
            validate_token(token, self.secret, required_scope="post_grant_expense")

    def test_reject_malformed_token(self) -> None:
        with self.assertRaises(TokenValidationError):
            validate_token("not-a-token", self.secret, required_scope="post_grant_expense")

    def test_reject_tampered_payload(self) -> None:
        token = issue_token(self.claims, self.secret)
        payload_b64, signature_b64 = token.split(".", 1)

        payload = json.loads(_b64decode_for_test(payload_b64).decode("utf-8"))
        payload["request_id"] = "req_tampered"
        tampered_payload_b64 = _b64encode_for_test(json.dumps(payload).encode("utf-8"))
        tampered_token = f"{tampered_payload_b64}.{signature_b64}"

        with self.assertRaises(TokenValidationError):
            validate_token(tampered_token, self.secret, required_scope="post_grant_expense")


def _b64decode_for_test(value: str) -> bytes:
    import base64

    pad = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + pad)


def _b64encode_for_test(value: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


if __name__ == "__main__":
    unittest.main()

