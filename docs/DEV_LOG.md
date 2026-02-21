# Development Log (Session-Based)

## Session 2026-02-20

Date: 2026-02-20

Related commits (short SHA):
- `3f93bf9`
- `407af4b`

### What changed
- Added `src/intent_schema.py` to formalize model output into a validated `IntentObject` contract.
- Added `src/auditor.py` to implement deterministic rule evaluation and explicit decision routing (`APPROVE`, `REJECT`, `REQUIRE_REVIEW`).
- Added `src/token_gateway.py` to issue and validate signed commit tokens with scope and expiry checks.
- Added `tests/test_auditor_rules.py` covering approve/reject/review paths and stale snapshot rejection behavior.
- Added `tests/test_token_validation.py` covering signature integrity, scope checks, expiry checks, and tamper rejection.
- Added `docs/DEMO_SCRIPT.md` to standardize an interview/demo sequence around governance enforcement.

### Why it changed
- Needed a strict boundary between probabilistic intent generation and deterministic commit authorization.
- Needed deterministic policy checks to be explicit, testable, and independent of model confidence alone.
- Needed mutation authorization to be cryptographically bound to auditor context (decision hash + policy + snapshot).
- Needed failure behavior to default to safe denial/review rather than silent pass-through.
- Needed early test coverage to lock control invariants before API and persistence layers are added.
- Needed a reusable technical narrative that demonstrates governance architecture, not chatbot behavior.

### Design implications (control-plane impact)
- Control-plane logic now has a separable core that can be reused behind API, queue, or batch execution paths.
- Intent schema validation acts as a mandatory choke point before any rule or token flow is entered.
- Deterministic policy rules are encoded as pure evaluation logic, improving replay and regression predictability.
- Token-gated commit path establishes non-bypassable mutation control as a first-class architectural invariant.
- Tests now define baseline governance behavior and reduce drift as additional rules and data adapters are introduced.
- Model logic can evolve (prompt/model/version) without changing commit authority semantics.

### Next planned steps
- Add FastAPI endpoints for intent validation, auditor evaluation, and token verification.
- Introduce request/decision persistence layer (Postgres) aligned to `control_requests`, `control_decisions`, and token tables.
- Add BigQuery-backed snapshot adapter for grants/PO/invoice/labor read-model ingestion.
- Implement idempotency key enforcement in posting gateway path.
- Add policy version metadata handling and shadow-evaluation hooks.
- Add integration tests covering request -> decision -> token -> mutation-gate sequence.

