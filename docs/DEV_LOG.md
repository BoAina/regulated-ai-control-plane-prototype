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

## Session 2026-02-21

Date: 2026-02-21

Related commits (short SHA):
- `0913ae5`
- `b591232`

### What changed
- Added a governance-pack refactor plan to separate domain policy logic from the generic control-plane engine.
- Defined target split: `src/core/` for orchestration and invariants, `src/domains/` for domain-specific rule packs.
- Specified a `GovernanceModule` contract for policy versioning, required evidence, deterministic evaluation, and token scope mapping.
- Defined extraction path for grants rules from `auditor.py` into `src/domains/grants/rules.py` behind a module adapter.
- Added plan for a `mortgage_trid_respa` stub domain to prove module interchangeability without engine rewrites.
- Added test strategy to validate shared engine invariants and domain-specific behavior independently.

### Why it changed
- Current grants-focused logic is correct but too coupled to a single policy domain.
- Modular policy packs are required to support additional governance contexts (mortgage, HIPAA, legal/regulatory variants) safely.
- The architecture must preserve existing invariants while allowing domain substitution at the rules layer.
- Token authorization semantics need domain-aware scopes without changing core signing/validation mechanics.
- Replay and audit correctness depend on stable, normalized decision-hash material across all domains.
- Refactor sequencing is needed to reduce risk: behavior-preserving extraction first, then new domain introduction.

### Design implications (control-plane impact)
- Commit authority remains centralized in core token-gated controls; domain packs only supply deterministic policy evaluation.
- The auditor becomes orchestration-only, improving maintainability and enabling explicit policy-pack loading per workflow.
- Domain packs can evolve policy logic independently while retaining a consistent decision envelope for audit/replay.
- Token payload should include `module_name`, `policy_version`, and `decision_hash` to prevent cross-context token reuse.
- Cross-domain support becomes a configuration concern rather than a structural rewrite.
- Invariant tests become the primary guardrail against regression during policy-pack expansion.

### Next planned steps
- Introduce `src/core/governance_module.py` with protocol/types for rule findings and decision results.
- Refactor `src/auditor.py` into a generic orchestrator that delegates to a loaded governance module.
- Extract grants rules into `src/domains/grants/` with module wrapper and policy metadata.
- Add `src/domains/mortgage_trid_respa/` stub pack with minimal placeholder rules to validate interchangeability.
- Update tests into `tests/core/` and `tests/domains/` with engine-invariant and per-domain coverage.
- Extend token claim model to bind module and policy context explicitly during issuance/validation.

## Session 2026-02-22

Date: 2026-02-22

### What changed
- Extracted `GrantsGovernanceModule` and decision constants (`DECISION_APPROVE`, `DECISION_REJECT`, `DECISION_REQUIRE_REVIEW`) from `src/auditor.py` into a new `src/grants_governance.py`.
- Eliminated the duplicate `Violation` dataclass from `src/auditor.py`. `AuditorDecision.violations` now uses `RuleFinding` from `governance_module.py` directly, and the `_rule_finding_to_violation()` conversion function is removed.
- Added `pyproject.toml` with `pythonpath = ["src"]` for pytest, replacing the fragile `sys.path.insert()` hack in every test file.
- Added `Makefile` with `test`, `lint`, and `clean` targets.
- Created `tests/conftest.py` with shared `base_payload()` and `base_snapshot()` fixtures, removing identical copies from `test_auditor_rules.py` and `test_auditor_orchestration.py`.
- Added `tests/test_intent_schema.py` with 11 tests covering all validation paths in `validate_intent()` — previously at zero coverage.
- Fixed `issue_token()` in `src/token_gateway.py` to raise `TokenValidationError` instead of a generic `ValueError` when given an empty secret.
- Added typed `module: GovernanceModule` class attribute on `Auditor`.
- Made `GrantsGovernanceModule` explicitly declare its `GovernanceModule` protocol in the class signature.
- Removed `sys.path.insert()` blocks from all three existing test files.

### Why it changed
- `auditor.py` carried five distinct responsibilities in 260 lines: data classes, orchestration, domain-specific policy logic, utility functions, and constants. Splitting it makes each module readable and testable in isolation.
- The `Violation` class was a structural duplicate of `RuleFinding`, connected only by a pointless field-by-field copy function. Removing it reduces maintenance surface and eliminates a source of potential drift.
- The `sys.path.insert()` pattern in every test file was fragile and would break on any directory restructuring. `pyproject.toml` with `pythonpath` handles this correctly at the test runner level.
- `validate_intent()` is the entry point for every intent in the system. Having zero tests on it meant the single most critical validation boundary was unverified.
- `issue_token()` raising a generic `ValueError` was inconsistent with the rest of the token module, which consistently raises `TokenValidationError` for all validation failures.
- Copy-pasted test fixtures across files create silent divergence risk when one copy is updated and the other is not.

### Design implications (control-plane impact)
- `auditor.py` is now orchestration-only: `Auditor`, `GrantSnapshot`, `AuditorDecision`, `evaluate_grant_intent()`, and the decision hash computation. Domain logic lives in its own module.
- `grants_governance.py` uses a `TYPE_CHECKING` guard for `GrantSnapshot` to avoid a circular runtime import while preserving static type safety. This pattern scales to additional governance packs.
- The `GovernanceModule` protocol is now explicitly declared on `GrantsGovernanceModule`, enabling static analysis tools (mypy) to verify protocol compliance.
- Test suite grew from 11 to 23 tests. Schema validation coverage now includes: valid payloads, missing fields, boolean coercion rejection, zero/negative amounts, confidence bounds, invalid risk classes, empty evidence refs, malformed dates, dict serialization, and non-dict payloads.
- All observable behavior is preserved. Existing tests pass with identical assertions. The refactor is purely structural.

### Next planned steps
- Add FastAPI endpoints for intent validation, auditor evaluation, and token verification.
- Introduce Postgres persistence layer for decisions, tokens, and audit chain.
- Add a second governance pack (mortgage TRID-RESPA or HIPAA) to validate the portability of the extracted module architecture.
- Add integration tests covering the full request -> decision -> token -> mutation-gate sequence.
- Consider adding CI workflow (`.github/workflows/test.yml`) to automate test runs on push.
