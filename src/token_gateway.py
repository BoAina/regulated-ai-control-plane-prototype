"""Simple token issuance and validation for mutation gating."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


class TokenValidationError(ValueError):
    """Raised when a commit token cannot be validated."""


@dataclass(frozen=True)
class TokenClaims:
    """Claims that bind approval decisions to posting authorization."""

    token_id: str
    request_id: str
    transaction_id: str
    decision_hash: str
    policy_version_id: str
    state_snapshot_hash: str
    scope: list[str]
    issued_at: str
    expires_at: str
    one_time_use: bool = True

    @classmethod
    def new(
        cls,
        *,
        request_id: str,
        transaction_id: str,
        decision_hash: str,
        policy_version_id: str,
        state_snapshot_hash: str,
        scope: list[str],
        ttl_seconds: int = 300,
    ) -> "TokenClaims":
        now = datetime.now(timezone.utc)
        return cls(
            token_id=f"tok_{uuid.uuid4().hex[:12]}",
            request_id=request_id,
            transaction_id=transaction_id,
            decision_hash=decision_hash,
            policy_version_id=policy_version_id,
            state_snapshot_hash=state_snapshot_hash,
            scope=scope,
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat(),
            one_time_use=True,
        )


def issue_token(claims: TokenClaims, secret: str) -> str:
    """Issue a signed token from token claims."""
    if not secret:
        raise ValueError("secret must not be empty")
    payload_bytes = _serialize_claims(claims)
    signature = _sign(payload_bytes, secret)
    return f"{_b64url_encode(payload_bytes)}.{_b64url_encode(signature)}"


def validate_token(token: str, secret: str, required_scope: str) -> TokenClaims:
    """Validate signature, expiry, and scope before allowing posting."""
    if not token or "." not in token:
        raise TokenValidationError("token format is invalid")
    if not secret:
        raise TokenValidationError("secret must not be empty")

    encoded_payload, encoded_signature = token.split(".", 1)
    payload_bytes = _b64url_decode(encoded_payload)
    supplied_signature = _b64url_decode(encoded_signature)
    expected_signature = _sign(payload_bytes, secret)
    if not hmac.compare_digest(supplied_signature, expected_signature):
        raise TokenValidationError("token signature is invalid")

    payload = json.loads(payload_bytes.decode("utf-8"))
    claims = TokenClaims(**payload)
    _validate_claim_times(claims)
    if required_scope not in claims.scope:
        raise TokenValidationError(f"required scope '{required_scope}' is missing")
    return claims


def _validate_claim_times(claims: TokenClaims) -> None:
    now = datetime.now(timezone.utc)
    try:
        issued_at = datetime.fromisoformat(claims.issued_at)
        expires_at = datetime.fromisoformat(claims.expires_at)
    except ValueError as exc:
        raise TokenValidationError("token timestamps are invalid") from exc

    if issued_at.tzinfo is None or expires_at.tzinfo is None:
        raise TokenValidationError("token timestamps must be timezone-aware")
    if expires_at <= now:
        raise TokenValidationError("token has expired")
    if issued_at > now + timedelta(seconds=10):
        raise TokenValidationError("token issued_at cannot be in the far future")


def _serialize_claims(claims: TokenClaims) -> bytes:
    payload = asdict(claims)
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign(payload: bytes, secret: str) -> bytes:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    pad = "=" * ((4 - len(raw) % 4) % 4)
    try:
        return base64.urlsafe_b64decode(raw + pad)
    except (ValueError, base64.binascii.Error) as exc:
        raise TokenValidationError("token encoding is invalid") from exc

