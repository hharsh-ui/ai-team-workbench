---
name: code-review
description: Review code changes, pull requests or diffs for correctness, consistency, security, tests, performance and readability, with actionable findings ranked by severity. Use for "review this PR, diff, branch or code", before handing work to testing, or to check that a change was applied consistently everywhere it should be.
---

# Code Review

Find what would hurt users or future developers, explain why, and suggest the fix.

## Steps

1. **Understand the intent:** the PRD requirement IDs, the work area's changelog, the PR description. If the intent is missing, ask, or infer it and say so.
2. **Get the whole diff:** `git -C <checkout> diff <base>...HEAD`, or `gh pr diff <number>`. List the changed files.
3. **Read in context:** the whole changed function or file and its callers, not just the changed lines.
4. **Consistency sweep:** for every renamed or changed function, constant, configuration key, API field or database column, search all references (code, tests, docs, configuration) and confirm each was updated.
5. **Checklist:**
   - **Correctness:** logic, edge cases, error handling, off-by-one, missing values, concurrency, time zones, rounding of money.
   - **Requirements:** does the change do what the acceptance criteria say, and nothing unasked?
   - **Security:** a quick pass with the security-review skill, part B.
   - **Tests:** added or updated? Do they test behaviour? Would they fail without the change?
   - **Performance:** repeated queries in a loop, unbounded lists, large payloads, blocking calls.
   - **Readability:** names, function size, dead code, duplicated logic, comments that no longer match the code.
   - **Compatibility:** database migrations and API changes are backward compatible; configuration defaults are safe.
   - **Documentation:** README and changelog updated.
   - **Gate integrity:** every weakened or deleted test, raised timeout, new skip, snapshot update or suppressed warning is named in the report (gstack `review/gate-integrity.md`). For a deeper pass, use gstack's `review/checklist.md`.
6. **Report.** Start with a one-line verdict: Approve, Approve with nits, or Changes requested. Then a table: number, severity (Blocking, Should fix, Nit, Question), file and line, finding, suggestion. Mention good parts briefly. The Tester saves the review in `artifacts/test-results/`.
7. **Tone:** specific and kind. Explain why, and show a suggested change when it helps.
8. **Publishing a review** (posting comments, approving or rejecting a PR online) is a public action: ask the user first.

## Reviewing your own work

The Developer runs the same checklist on its own diff before every handoff and fixes what it finds first. When receiving a review, the Developer follows superpowers receiving-code-review: verify each finding before changing code, and push back with evidence when a finding is wrong.

## Common mistakes

- Reviewing only the diff lines and missing broken callers.
- Style nitpicks that bury the one real bug.
- Approving without running or reading the tests.
