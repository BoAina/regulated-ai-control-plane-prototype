# Regulated AI Control Plane Prototype

Compliance-first reference prototype for using probabilistic LLM reasoning inside deterministic enterprise controls.

## Problem

LLM outputs are probabilistic. ERP and financial posting paths must be deterministic, auditable, and replayable.

This project demonstrates a control-plane pattern where:

- model outputs are advisory only
- deterministic rules evaluate mutation requests
- posting is blocked unless a signed approval token is present
- every decision is recorded for replay

## Scope

Initial domain focus:

- grants expenditure workflows in healthcare/life sciences finance operations

Core entities represented in the ERP read model:

- grants
- purchase orders
- invoices
- labor costs
- invoice cost allocations

## Architecture (High level)

- Intake service for request normalization and trace IDs
- LLM interpreter with structured outputs
- Schema validator
- Deterministic auditor + policy engine
- Confidence/risk routing + HITL review queue
- Signed token issuer
- Posting gateway (token required)
- Audit/replay service

## Data strategy

Hybrid approach:

- BigQuery: ERP-style analytical read model and snapshots
- Postgres: authoritative control-plane state (decisions, tokens, idempotency, audit chain)

## API usage

Primary model path:

- OpenAI Responses API (structured outputs)

Phase expansion:

- Files API
- Embeddings API
- Vector Stores API
- Moderations API
- Batch API
- Models API (allowlist + traceability)

## Repository layout

```text
regulated-ai-control-plane-prototype/
  docs/
    PROTOTYPE_SPEC.md
    LEARNING_PYTHON.md
    DEMO_SCRIPT.md
  src/
  tests/
  data/
  README.md
```

## Docs

- `docs/PROTOTYPE_SPEC.md` - full build specification, contracts, controls, milestones
- `docs/LEARNING_PYTHON.md` - build-fast/understand-later learning loop used during implementation
- `docs/DEMO_SCRIPT.md` - step-by-step walkthrough for interview/demo delivery

## Current status

Spec and architecture are defined, with first implementation modules and unit tests added.

## Implemented modules

- `src/governance_module.py`: pluggable governance module interface (`GovernanceModule`, `DecisionResult`, `RuleFinding`)
- `src/intent_schema.py`: typed `IntentObject` and strict payload validation
- `src/auditor.py`: auditor orchestration + grants module adapter + deterministic decision routing
- `src/token_gateway.py`: signed token issuance and validation
- `tests/test_auditor_rules.py`: approve/reject/review rule coverage
- `tests/test_auditor_orchestration.py`: module-driven orchestration behavior coverage
- `tests/test_token_validation.py`: signature/expiry/scope validation coverage

## Run tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
