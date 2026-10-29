---
name: product-builder
description: Build an app, website, API or tool from an approved PRD in small, working and tested vertical slices - scaffolds a minimal project in the work area, implements slice by slice with unit tests and a README, runs it, and hands it to testing. Use for "build, create or make an app, website, API, script or tool", "add a feature" or "turn this PRD into code".
---

# Product Builder

Build in thin slices that work end to end, so there is always something running to show.

## Before you start

- A work area exists for the feature (`python scripts/wb.py work list`) and its status is `ready-for-dev` or `in-dev`.
- **New product:** an approved PRD and design, unless the user explicitly waives them.
- **Small tool or fix:** a five-line mini spec in a `work note` is enough: goal, users, inputs, outputs, done-when.

## Steps

1. **Scaffold minimally** inside the work area's `checkout/`. Prefer the stack's official starter (for example `npm create vite@latest`, `django-admin startproject`, `cargo new`) or a hand-written minimal structure. Add:
   - `README.md`: what it is, how to install, run and test it.
   - `.gitignore`, `.env.example` (empty values) and a lockfile.
   - A test runner with one passing test; the stack's standard formatter or linter.
   - Ask about the license and about CI; do not choose silently.
2. **Walking skeleton.** The thinnest path through every layer (for example page → API → database → page), running locally, with one test. Commit it.
3. **Slices.** For a feature with several tasks, first write the plan with superpowers writing-plans (`docs/plans/YYYY-MM-DD-<topic>.md`); independent tasks can go to sub-agents with subagent-driven-development. For each requirement in priority order:
   1. Restate its acceptance criteria (requirement ID).
   2. Write a failing test, then the smallest change that meets them (superpowers test-driven-development).
   3. Run the tests and the app.
   4. Review your own diff; do a quick security pass (security-review, part B).
   5. Commit locally with a clear message ("Add task list page (R3)"), then `work note <id> --role dev --summary ... --files ... --validation ...`.
4. **Show progress** at meaningful points: how to run it, plus a screenshot or sample output. Ask for feedback before large next steps, not after every line.
5. **Quality gates before handing over:**
   - Tests pass; linter clean; README current; no secrets, debug prints or commented-out code; input validated at the edges; clear error messages.
   - **Websites:** works on phone and desktop widths; keyboard navigation; form labels; enough colour contrast; no errors in the browser console.
   - **APIs:** correct status codes; validation errors that help the caller; authorization tested.
6. **Hand over to testing:** status `ready-for-test` and the handoff note (Developer agent, step 4). Publishing comes after acceptance.

## Defaults when the user has no preference (propose, do not impose)

- **Static website:** plain HTML, CSS and JavaScript, or Vite; host on GitHub Pages or Netlify.
- **Web application:** one framework end to end (for example Next.js, or Django or Flask) with SQLite locally and PostgreSQL later.
- **Command-line tool or script:** Python standard library with `argparse`.
- **Mobile:** start as a responsive web app; go native only when a feature needs it.

## Coding standards

Clear names; small functions; no abstractions before they are needed; errors handled at the boundaries (user input, network, files); no secrets in code; consistent formatting; a new dependency only when it saves real work and passes the research skill's library checks.

**Reuse before writing** (gstack's reuse ladder): stop at the first that works — a helper already in the repository, the standard library, a platform feature (a CSS rule over JavaScript, a database constraint over application code), an installed dependency. Then build the remaining part completely, with tests and error paths.

## Common mistakes

- Building before the requirements are clear.
- One giant first commit; mixing two features in one branch.
- "It works on my machine" with no test and no run instructions.
- Features nobody asked for; ignoring phones and accessibility.
- TODOs that are not written down anywhere.
