# Learning Python (While Building the Prototype)

Last updated: 2026-02-22

## Starting position

The domain knowledge is already there - a decade of ERP implementations in regulated industries, audit trails, posting controls, compliance workflows. What's missing is implementation fluency: Python syntax, type systems, standard library patterns, and the muscle memory of writing code instead of just reading it.

This document is a discipline framework for closing that gap using the prototype as the learning vehicle. Not a curriculum - just rules for making sure AI-assisted speed doesn't come at the cost of real comprehension.

## Core principle

Vibe code to get the shape right fast. Then slow down, deconstruct every line, rewrite what you can't explain, and test what you can.

The prototype was scaffolded with Codex and stabilized with Claude Code. That's the right workflow - but scaffolded code you can't modify under pressure is a liability, not an asset. The hand-refactor pass is where code becomes yours.

## The build-understand loop

Run this loop for each module or feature:

1. **Define one tiny outcome.** Not "refactor the auditor" - more like "rewrite the budget check rule from scratch." Keep scope to one function or one test at a time.

2. **Vibe-code until it works** (if building new). For refactoring existing code, read first, then rewrite without looking at the original.

3. **Explain the flow out loud.** What data comes in? What function transforms it? What does it return? If you can't answer all three without looking at the code, you don't own it yet.

4. **Rewrite one small part manually (no AI).** This is the part that builds real skill. Rename variables to names that make sense to you. Simplify branching. Make function signatures explicit. If the original used a Python pattern you don't recognize, look it up - don't just copy it.

5. **Run the tests.** All 23 should still pass. If they don't, you changed behavior, not just style. Fix it before moving on.

6. **Write down what you learned.** One sentence in the DEV_LOG. Not what you did - what you now understand that you didn't before.

## How to know if you own a module

"Mystery code" is subjective. Use these concrete checks instead:

**You own it if you can:**
- Explain what every function does without reading the code
- Predict what happens when you change a specific line
- Write a new test for an edge case without looking at existing tests
- Modify a rule and have the right tests fail (not random ones)
- Describe the module's job to a non-technical person in one sentence

**You don't own it yet if:**
- You can read it and nod along but couldn't recreate the logic on a whiteboard
- You're not sure which import does what
- You'd need to re-read the function to answer "what happens if the input is missing a field?"
- You skip a section thinking "I'll understand that later"

## Time split (adapts as you progress)

The ratio should shift as your comfort grows:

**Weeks 1-2 (read and follow):** 50% reading and explaining, 30% rewriting, 20% building new. You're mostly deconstructing Codex output right now. That's correct.

**Weeks 3-4 (write with lookups):** 40% building new, 30% rewriting/refactoring, 30% testing and documenting. You should be writing new tests without AI help by this point.

**Weeks 5+ (write confidently):** 60% building new, 20% testing, 20% refactoring old code you now see differently. The ratio flips because you're generating, not just consuming.

If you're still at 50% reading after week 4, slow down and identify which specific patterns are blocking you. It's usually one of: dataclass construction, dictionary unpacking, or exception handling flow.

## Session template (90 minutes)

1. **10 min** - Pick one function or one test to own today. Write down what you think it does before reading it.
2. **30 min** - Read it, run it, break it on purpose (change an input, remove a line), observe what happens.
3. **20 min** - Rewrite it from memory. Don't look at the original. Get it wrong. Compare.
4. **20 min** - Write one new test that the original author didn't write. Edge cases are best.
5. **10 min** - Update DEV_LOG with what you learned. Run `make test` to confirm green.

## Module refactor order

This sequence goes from simplest (no dependencies) to most complex (depends on everything else):

### 1. `intent_schema.py` - Start here
- No imports from other project modules
- Pure validation logic: dict in, IntentObject out, or error
- 12 tests already exist - you'll know immediately if your rewrite works
- **Key patterns to learn:** frozen dataclasses, isinstance checks, date parsing, raising custom exceptions
- **Ownership test:** Write a 13th test for a case the existing suite doesn't cover

### 2. `governance_module.py` - Short but conceptually important
- 62 lines, mostly type definitions
- This is where you learn what a Python Protocol is and why it's not an abstract base class
- **Key patterns to learn:** Protocol, frozen dataclasses with tuple fields, to_dict serialization
- **Ownership test:** Explain in one paragraph why this file exists separately from auditor.py

### 3. `grants_governance.py` - The domain logic you already understand
- This is YOUR domain knowledge expressed in Python. You should be able to rewrite every rule because you know what grant period validation and budget checks actually mean
- **Key patterns to learn:** method organization, building RuleFinding objects, decision routing logic
- **Ownership test:** Add the missing R-ORG-006 (org unit authorization) rule from scratch, with tests

### 4. `auditor.py` - Now just orchestration
- After the stabilization pass, this is only ~100 lines
- It instantiates a governance module and calls evaluate(). That's it.
- **Key patterns to learn:** constructor injection, hash computation, the wrapper function pattern
- **Ownership test:** Swap in a fake governance module that always returns REJECT and verify the auditor handles it correctly

### 5. `token_gateway.py` - Save this for last
- Cryptographic signing, base64url encoding, HMAC verification, constant-time comparison
- This is the most "you need to understand every line" module because getting crypto wrong silently is worse than getting it wrong loudly
- **Key patterns to learn:** hmac module, base64 encoding, timezone-aware datetimes, structured token formats
- **Ownership test:** Explain why validate_token uses hmac.compare_digest instead of == comparison

## Weekly checkpoint questions

Use these honestly. If the answer to any question is "not really," that's your priority for the next week.

1. Which module can I now rewrite from scratch without AI or reference code?
2. Which function would I be nervous to explain in an interview?
3. What did I learn this week that changed how I read the rest of the codebase?
4. Can I run the demo script (`docs/DEMO_SCRIPT.md`) and explain every step without notes?
5. If a test fails tomorrow, can I diagnose it from the error message alone?

## Spaced review

New code makes sense when you just wrote it. The real test is whether it still makes sense two weeks later.

**Every two weeks:** Pick a module you refactored earlier. Read it cold, without context. If anything is unclear, refactor it again - your second pass will be better than your first because you've learned more since then.

**Monthly:** Re-read this document itself. Your learning needs will shift. Update the time split ratios, adjust the module order if something clicked faster than expected, and add new ownership tests based on what you've built since.

## External validation

You don't have a mentor reviewing your code, but you have three feedback mechanisms:

1. **The test suite.** 23 tests don't lie. If they pass after your rewrite, you preserved behavior. If they fail, you changed something you didn't intend to.

2. **The demo script.** `docs/DEMO_SCRIPT.md` is a 10-15 minute walkthrough. If you can deliver it fluently and answer follow-up questions, you own the system. If you stumble on a section, that's the module to revisit.

3. **The AI tools themselves.** After you hand-refactor a module, paste your version into Claude or ChatGPT and ask "what would you change about this code and why?" The suggestions you agree with are style improvements. The suggestions that surprise you are learning opportunities.

## Progress signal

Progress is not how much code you generated. Progress is not how many files you touched. Progress is: how much of this system can you explain, modify, debug, and extend without assistance?

When the answer is "all of it," you're done learning and building at the same time.
