---
name: testing
description: Plan and run testing - a risk-based test plan traced to the PRD's acceptance criteria, unit, integration and end-to-end tests, manual test scripts, edge cases, bug reports and a test report with evidence. Use for "test this", "write tests", "is it ready?", before a pull request or release, or when acceptance criteria need verifying. Scales the effort to the risk and asks before costly testing.
---

# Testing

Tests prove that the requirements are met and keep them met. Spend effort where failure would hurt most.

## Steps

1. **Scope by risk.** What can break, how badly, and how likely? Propose a scope with an effort estimate. If it is costly (new tools, fixtures or long runs), ask: now, or later?
2. **Plan and trace.** Write `docs/test-plan.md` from [the test plan template](../../../templates/test-plan.md): requirement ID → acceptance criterion → test name → type → status.
3. **Use the test pyramid:**
   - Many **unit** tests: fast checks of pure logic.
   - Some **integration** tests: real database, file system or API boundaries.
   - Few **end-to-end** tests: the critical user journeys.
   - **Manual exploratory** testing for look, feel and surprises; write the steps down so they can be repeated.
4. **Write good tests:**
   - Arrange, Act, Assert; one behaviour per test; a name that says what should happen.
   - Deterministic: fixed clocks and random seeds; no real network unless that is the point.
   - Fake data only; never real personal data.
   - Edge cases: empty, missing, zero, negative, maximum length, unusual characters (emoji, accents), duplicates, two users at once, no permission (user A must not see user B's data), slow or failed network, errors from dependencies, dates around midnight and daylight-saving changes.
   - Calculations: reproduce every worked example from the source exactly ("golden examples"), plus boundaries and rounding.
5. **Run them** and record the command, the pass and fail counts and the failures. Never report tests as passing if you did not run them.
6. **Bugs:** one report per defect from [the bug report template](../../../templates/bug-report.md), saved in `artifacts/test-results/`. For a flaky test, find the cause instead of re-running until it passes.
7. **Regression rule:** every fixed bug gets a test that failed before the fix.
8. **Report:** `artifacts/test-results/test-report-<YYYY-MM-DD>.md` — verdict, requirement table with evidence, bugs, what was not tested and why, remaining risks.

## Checklists

- **Web pages:** phone and desktop widths; keyboard only; screen-reader labels; colour contrast; loading, empty and error states; browser console free of errors; slow network.
- **APIs:** correct status codes (200, 201, 400, 401, 403, 404, 409, 422, 500); validation messages; authorization; pagination; repeating the same request; time zones.
- **Command-line tools:** help text; wrong arguments; missing files; exit codes; paths with spaces and non-English characters.
- **Exploratory testing:** the gstack qa-only method — one evidence note per probe, effects kept inside a local fixture, every finding with the exact command or steps.
- **Suite health:** the gstack test-audit method finds tests that cost more than they protect (duplicates, tests without assertions); report them, do not delete them on your own.
- **Documents generated from a source:** `python scripts/wb.py call source_check_numbers pack_dir=<pack> text_file=<document>`; every citation points to the right page; required pictures are present.

## Common mistakes

- Testing the implementation instead of the behaviour (tests break on every refactor).
- Deleting or skipping a failing test to make the run "green".
- Only happy paths.
- Huge end-to-end suites that are slow and flaky.
