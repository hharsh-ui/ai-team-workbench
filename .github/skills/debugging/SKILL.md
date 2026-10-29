---
name: debugging
description: Systematic debugging - reproduce the problem, check the recorded lessons for known fixes, form and test hypotheses, find the root cause, apply the smallest correct fix, add a regression test and record the lesson. Use for errors, crashes, failing tests, wrong output, "it doesn't work", slowness or flaky behaviour.
---

# Debugging

Find the cause, not just a way to make the symptom disappear. The Tester uses steps 1 to 6 to reproduce and narrow a bug for its report; the Developer does all steps. For hard or recurring bugs, the superpowers systematic-debugging skill goes deeper (root-cause tracing, defense in depth, waiting for conditions instead of fixed delays).

## Steps

1. **Lessons first:** `python scripts/wb.py call lesson_search query="<distinctive words from the error>"`. If a fix is recorded, apply it and verify.
2. **Capture the facts:** the exact error message and stack trace, the command, the inputs, the environment (operating system, versions), what changed recently, and expected versus actual behaviour.
3. **Reproduce** reliably with the smallest possible case. If you cannot reproduce it, collect more evidence (logs, screenshots, exact steps) instead of guessing.
4. **Hypotheses:** list two to four likely causes, most likely first. For each, name a quick check that would prove or disprove it.
5. **Narrow it down:**
   - Read the code path from input to failure.
   - Add temporary logging.
   - Change one thing at a time.
   - For regressions, use `git bisect` to find the commit that broke it (`git bisect start`, `git bisect bad`, `git bisect good <commit>`, …, `git bisect reset`).
6. **Root cause:** explain why it happened, not only where. Keep asking "why?" until you reach something you can fix (the "five whys").
7. **Fix** with the smallest change that removes the cause. Search for the same pattern elsewhere and fix those too, or list them.
8. **Verify:** the reproduction now passes; add a regression test that failed before the fix; run the related tests.
9. **Clean up** temporary logging and experiments.
10. **Record** with `python scripts/wb.py call lesson_add`: status, symptom, cause, fix, and a rule for next time. For tool or setup problems, include everything that was tried and failed.
11. **Report:** cause, fix, evidence, and any remaining risk; log it with `work note`.

## Never

- Change several things at once and keep whatever "works".
- Silence or swallow errors to make them disappear.
- Delete or skip tests to make the suite pass.
- Say "fixed" without re-running the reproduction.

## When stuck

After three disproved hypotheses: stop, write down what is known and unknown, and ask the user for information or for a second opinion (a sub-agent reviewing your reasoning). If the cause is outside your control, record a WORKAROUND lesson with exact steps.
