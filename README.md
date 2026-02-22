# Regulated AI Control Plane Prototype

A working prototype of deterministic governance controls for probabilistic LLM systems in regulated industries. Starting with grants expenditure as the first domain, but the architecture is designed to be portable across any regulated workflow.

## The problem this solves

LLM outputs are probabilistic. They can be wrong. In regulated financial and healthcare workflows, a wrong answer isn't just a bad experience, it can become an irreversible system mutation with compliance consequences: an unallowable grant expense gets posted, an out-of-period transaction commits, missing documentation gets bypassed.

Most AI demos ignore this. This prototype confronts it directly.

## Core architectural thesis

Probabilistic AI may propose, but deterministic controls must approve before anything posts.

The system enforces six invariants:

1. No direct model-to-ERP writes
2. Every proposed mutation is schema-validated before evaluation
3. Every decision is policy-versioned and snapshot-bound
4. High-risk ambiguity routes to human review
5. The posting endpoint rejects requests without a valid signed token
6. Every decision is replayable from logged artifacts

## What's implemented

The prototype currently covers the first phase: safe intake and deterministic gating.

**Schema validation** (`src/intent_schema.py`) — Strict `IntentObject` contract with field-level validation. The model must conform to this structure or the request fails. Enforces type constraints, value ranges, required fields, and immutability via frozen dataclasses.

**Governance module interface** (`src/governance_module.py`) — A Protocol-based interface that lets domain-specific rule packs plug into the same evaluation engine. Defines `RuleFinding`, `DecisionResult`, and the `GovernanceModule` contract. This is what makes the architecture portable across domains.

**Deterministic auditor** (`src/auditor.py`) — The core rule engine. Implements a `GrantsGovernanceModule` with deterministic rules for period validation, budget checks, allowability, documentation requirements, snapshot freshness, and high-dollar review thresholds. Routes every request to `APPROVE`, `REJECT`, or `REQUIRE_REVIEW`. Produces a decision hash for auditability.

**Token gateway** (`src/token_gateway.py`) — HMAC-SHA256 signed token issuance and validation. Tokens bind an approval decision to a specific request, transaction, policy version, and snapshot. They have scoped permissions, expiry windows, and are verified with constant-time comparison. No valid token, no mutation.

**Tests** — 11 unit tests covering approval paths, rejection on disallowed codes, review routing for high-dollar transactions, stale snapshot rejection, token tampering, signature validation, expiry enforcement, and orchestrator consistency.

## What's designed but not yet built

The full specification is in `docs/PROTOTYPE_SPEC.md`. Planned phases include:

- FastAPI endpoints for the control-plane services
- Postgres persistence for decisions, tokens, workflow state, and audit chain
- BigQuery integration as the ERP read-model and snapshot layer
- Policy corpus ingestion with retrieval-augmented citations
- Human-in-the-loop review workflow
- Moderation and injection screening
- Replay and evaluation harness
- Additional domain governance packs (grants implemented first; add mortgage/TRID-RESPA and HIPAA packs to prove portability)

## Governance packs

The control plane is domain-agnostic. Domain-specific policy logic is loaded as a governance pack — a pluggable module that provides rules, evidence requirements, scope mappings, and policy metadata. The engine evaluates any pack with the same orchestration, token binding, and audit semantics.

The first pack is grants expenditure, with rules covering:

- `R-PERIOD-001` — expense date within grant period
- `R-BUDGET-002` — amount within available budget
- `R-ALLOW-003` — object code in approved categories
- `R-DOC-004` — required evidence present
- `R-SNAP-008` — snapshot freshness check
- `R-THRESH-005` — high-dollar review routing

But the same engine handles other regulated domains by swapping the pack. Replace "grant period" with "coverage period" and "allowability" with "medical necessity" and you get claims adjudication. Replace grant rules with TRID/RESPA constraints and you get mortgage governance. Replace them with HIPAA access controls and you get PHI disclosure governance. One engine, many packs.

## Data architecture

Hybrid design with clear trust boundaries:

- **BigQuery** — Analytical read model representing ERP entities (grants, purchase orders, invoices, labor costs, allocations). Provides evaluation context and snapshot manifests. Does not grant commit authority.
- **Postgres** — Authoritative transactional store for control-plane state: requests, decisions, review actions, tokens, idempotency keys, and the audit event chain.

## Repository layout

```
src/
  intent_schema.py        # IntentObject contract and validation
  governance_module.py     # GovernanceModule protocol and shared types
  auditor.py               # Rule engine and grants governance module
  token_gateway.py         # Signed token issuance and validation
tests/
  test_auditor_rules.py    # Policy rule evaluation coverage
  test_auditor_orchestration.py  # Orchestrator interface consistency
  test_token_validation.py       # Token security coverage
docs/
  PROTOTYPE_SPEC.md        # Full build specification
  DEMO_SCRIPT.md           # Interview/demo walkthrough
  DEV_LOG.md               # Development session log
  LEARNING_PYTHON.md       # Learning process documentation
data/                      # Golden test cases (planned)
```

## Run tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## How this was built

The initial scaffolding was generated with AI-assisted tooling (Codex), then hand-refactored module by module for understanding and ownership. The approach is deliberate: vibe code to get the shape right fast, then slow down, deconstruct every line, rewrite what I can't explain, and test what I can. The development session log (`docs/DEV_LOG.md`) tracks that process, and `docs/LEARNING_PYTHON.md` documents the learning discipline behind it.

## Background

This prototype comes from a decade of enterprise ERP implementation work in regulated industries. The goal is not model training — it's building the governance layer that makes LLM systems safe enough for enterprise posting paths where compliance consequences are real and irreversible.
