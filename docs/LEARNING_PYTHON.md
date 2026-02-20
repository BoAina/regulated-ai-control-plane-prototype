# Learning Python (While Building the Prototype)

Last updated: 2026-02-20

## Core approach

Yes, it is fine to vibe-code first for momentum.  
The key is to always follow with an explicit understanding pass.

Use this rule:

> Build fast first, then slow down and make sure you can explain every important part.

## The build-understand loop

Run this loop for each small feature:

1. Define one tiny outcome.
- Examples: parse `IntentObject`, run one deterministic rule, write one audit event.

2. Vibe-code until it works.
- Keep scope narrow and avoid jumping between many files.

3. Explain it in your own words.
- What data comes in?
- What function transforms it?
- What output is produced?

4. Rewrite one small part manually (no AI).
- Rename variables.
- Simplify branching.
- Make function inputs/outputs explicit.

5. Add 1-2 tests.
- One success case.
- One failure/edge case.

6. Keep only code you can explain tomorrow.
- If it feels like mystery code, refactor until it makes sense.

## Time split while learning

Recommended split:

- 60% building fast
- 40% deconstructing, rewriting, and testing

This keeps momentum without sacrificing real skill growth.

## Non-negotiable guardrails

1. No mystery code in the final prototype.
2. Every important function should have a one-line purpose statement.
3. Every control-path module should have tests (especially rule evaluation and token checks).
4. Refactor small and often; do not wait for a giant cleanup phase.

## Session template (90 minutes)

1. 10 min: choose one tiny feature goal.
2. 30 min: build it quickly.
3. 20 min: explain and map the flow.
4. 20 min: manual rewrite/refactor.
5. 10 min: add tests and note what you learned.

## Prototype-first learning order

Follow this sequence so learning maps directly to interview evidence:

1. Python basics for data handling
- dicts/lists, loops, functions, modules, exceptions

2. API and JSON handling
- request/response structure, schema validation, parsing

3. Deterministic control logic
- pure functions, rule evaluation, clear return types

4. Persistence and audit writes
- insert/update flows, idempotency concepts

5. Testing
- `pytest` unit tests for rules, contracts, and failure paths

## Weekly checkpoint questions

Use these every week:

1. What can I now build without AI help?
2. Which files still feel like black boxes?
3. Which function did I rewrite manually this week?
4. Which 3 tests prove my control plane is safer than last week?
5. Can I explain the full request -> decision -> token -> post flow in 2 minutes?

## Progress signal that matters

Progress is not “how much code I generated.”  
Progress is “how much code I can explain, modify, and test confidently.”

