---
name: prd-writer
description: Write a Product Requirements Document (PRD) before development - problem, users, goals and non-goals, user stories with acceptance criteria, functional and non-functional requirements, success metrics, risks, release plan and open questions. Use for "write a PRD, spec or requirements", "I have an idea for an app or website", or before building anything non-trivial. The PRD is an approval gate before code.
---

# PRD Writer

A PRD says **what** to build and **why**, so that everyone agrees before anyone builds. It does not say how — that is the design.

## Steps

1. **Discovery interview.** Ask in one message, at most seven questions, each with a suggested default answer:
   - What problem are we solving, and for whom? How do they cope today?
   - Who are the users (two or three types)? Who pays, if anyone?
   - What does success look like in three months? How would we measure it?
   - Must-haves versus nice-to-haves?
   - Constraints: budget, deadline, platforms (web, phone, desktop), technology, regulation.
   - What data is involved? Personal data, payments or children's data?
   - Known alternatives or competitors? Is there a document that is the source of truth?
   If big facts are unknown, run the research skill first. If a document is the source of truth, run the pdf-source-of-truth skill first. For a new product or a vague idea, run the gstack office-hours method before these questions (team instructions, Section 15).
2. **Draft** `docs/prd.md` in the work area's checkout from [the PRD template](../../../templates/prd.md).
3. **Write good requirements:**
   - User stories: "As a <type of user>, I want <capability> so that <benefit>."
   - Acceptance criteria in Given / When / Then form. Each must be testable.
   - Number every requirement (R1, R2, …) so that designs, tests and pull requests can refer to it.
   - Prioritize with MoSCoW: Must, Should, Could, Won't (this time).
   - Non-functional requirements with numbers: speed (for example, pages load in under 2 seconds on a phone), availability, security and privacy, accessibility (WCAG 2.2 AA), supported devices and browsers, languages, data retention.
   - Success metrics with a baseline and a target.
   - Non-goals: what we deliberately will not do.
   - Risks and assumptions, each with a mitigation; open questions, each with an owner.
   - **MVP:** the smallest version that tests the riskiest assumption.
   - **Sources:** cite every requirement that comes from a source document (`[source p.12]`); copy needed pictures into `docs/assets/` and embed them; write numbers exactly as the source prints them.
4. **Self-review** before showing it:
   - Is every requirement testable and free of hidden solutions ("use React" is a constraint, not a need)?
   - Any conflicts between requirements?
   - Edge cases: empty states, errors, no network, permissions, deleted accounts, very large inputs.
   - Security and privacy considered? Metrics measurable? MVP small enough?
   - Scope decided on purpose with the gstack plan-ceo-review method: expand, selectively expand, hold or reduce?
5. **Present** a short summary, the requirement list and the open questions, and ask for approval. Do not start building until the user approves, unless they explicitly say to skip it.
6. **Keep it current.** Version the PRD with a change log at the bottom; record every scope change and who agreed to it.
7. **Hand off** to the Developer (system-design, then product-builder).

## Writing style

Plain language, short sentences, one idea per bullet. Define every term a newcomer would not know. Prefer examples to abstractions. Keep implementation details out unless they are real constraints.

## Common mistakes

- Writing the solution instead of the problem.
- Requirements like "fast" or "user-friendly" with no number or test.
- No non-goals, so the scope keeps growing.
- Forgetting the unhappy paths: errors, empty screens, abuse.
- An MVP that is really version 3.
