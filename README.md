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
  src/
  tests/
  data/
  README.md
```

## Docs

- `docs/PROTOTYPE_SPEC.md` - full build specification, contracts, controls, milestones
- `docs/LEARNING_PYTHON.md` - build-fast/understand-later learning loop used during implementation

## Current status

Spec and architecture are defined. Implementation is being built in phases (safe intake -> grounding -> governance hardening -> evaluation maturity).
