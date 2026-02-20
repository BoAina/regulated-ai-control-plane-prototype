# Demo Script (10-15 Minutes)

This script demonstrates deterministic governance around probabilistic model output.

## 1) Setup (1 minute)

- Open architecture diagram and key files:
  - `docs/PROTOTYPE_SPEC.md`
  - `src/intent_schema.py`
  - `src/auditor.py`
  - `src/token_gateway.py`
- State the system invariant:
  - model can propose intent
  - deterministic controls decide mutations
  - posting requires signed token

## 2) Show structured intent validation (2 minutes)

- Present a valid `IntentObject` payload.
- Run validation and explain required fields:
  - `transaction_id`, `grant_id`, `amount`, `object_code`, dates
  - `model_confidence`, `risk_class`, `evidence_refs`
- Show one invalid payload example and explain fail-closed behavior.

Talking point:

> Schema validation is the first governance choke point. Invalid/missing structure never reaches commit path.

## 3) Show deterministic policy evaluation (3 minutes)

- Walk through rules in `src/auditor.py`:
  - `R-PERIOD-001`
  - `R-BUDGET-002`
  - `R-ALLOW-003`
  - `R-DOC-004`
  - `R-SNAP-008`
  - high-dollar review path (`R-THRESH-005`)
- Show three outcomes:
  - `APPROVE` clean request
  - `REQUIRE_REVIEW` high-dollar request
  - `REJECT` policy violation

Talking point:

> Model confidence is advisory. Deterministic rules are authoritative.

## 4) Show token-gated mutation control (2 minutes)

- Issue a token from approved decision claims.
- Validate token with required scope.
- Show rejection for:
  - invalid signature
  - expired token
  - missing scope

Talking point:

> Without a valid token bound to decision hash and policy context, posting is denied.

## 5) Show test evidence (2 minutes)

Run:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Highlight:

- deterministic rules are tested
- token controls are tested
- reject/review/approve paths are explicit

## 6) Close with architecture positioning (1-2 minutes)

Close statement:

> This prototype proves a deployable control-plane pattern: probabilistic reasoning for interpretation, deterministic governance for commit authority, and auditable replay for regulated environments.

## Optional stretch demo

- Show how changing `high_dollar_threshold` changes routing to `REQUIRE_REVIEW` without changing model behavior.
- Show how stale snapshot handling forces a safe reject.

