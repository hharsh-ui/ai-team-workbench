---
name: system-design
description: Turn an approved PRD into a technical design - architecture, technology choices, data model, APIs, key flows, deployment, observability and Architecture Decision Records (ADRs). Use for "how should we build it", choosing a stack, designing a database or an API, planning a migration or reviewing an architecture. Keeps designs as simple as the requirements allow.
---

# System Design

The design explains **how** the PRD will be met, which options were considered, and why the chosen ones won.

## Steps

1. **Inputs.** Read the PRD (requirement IDs), constraints, expected scale, budget and who will run the system. If there is no PRD, write a five-line problem statement and confirm it first.
2. **Find the hard parts.** List what is risky or unknown (a third-party API, real-time updates, offline use, payments, exact calculations). For a big unknown, propose a time-boxed spike: a throwaway experiment that answers one question.
3. **Decide, with options.** For each major decision (front end, back end, database, hosting, login, payments) compare two or three options against the criteria, choose one and write an ADR. Defaults for small teams: well-documented, widely used technology; one deployable application before microservices; managed services for login and databases when allowed; one language end to end when possible.
4. **Architecture diagram** in Mermaid: components, data flows and trust boundaries (where data crosses from a less trusted to a more trusted zone).
5. **Data model:** entities, fields and types, relationships, who owns each record, retention, and which fields are personal data.
6. **Interfaces:** API endpoints or commands with inputs, outputs, errors, the permission each needs, rate limits and versioning.
7. **Key flows:** sequence diagrams for the two or three most important journeys.
8. **Exact calculations:** where the PRD or a source document defines formulas, design a dedicated module with decimal arithmetic, the rounding rule, and golden tests from the source's worked examples.
9. **Non-functional design:** performance budget, scaling assumptions, availability, backups and restore, observability (logs, metrics and alerts without personal data), cost estimate.
10. **Security by design:** run the security-review skill's threat model (part A) and fold the mitigations into the design.
11. **Delivery:** environments (local, staging, production), deployment and rollback, the testing approach, and the order of vertical slices — each slice names the requirement IDs it covers.
12. **Review before approval:** apply the gstack plan-eng-review method (architecture, data flow, edge cases, test matrix); for user interfaces add plan-design-review, for APIs and command lines plan-devex-review (team instructions, Section 15). Fix what they find.
13. **Save and ask for approval:** `docs/design.md` (from [the design template](../../../templates/design-doc.md)), `docs/adr/0001-<title>.md` and `docs/threat-model.md` in the checkout.

## ADR format

Title; Status (proposed, accepted, superseded by ADR-N); Context; Decision; Consequences (good and bad); Alternatives considered and why they lost. One decision per ADR. Never edit an accepted ADR's decision; supersede it with a new one.

## Common mistakes

- Over-engineering: microservices, queues or Kubernetes for an MVP.
- Designing without requirements, or ignoring the non-functional ones.
- Personal data with no retention or deletion plan.
- No rollback plan, or technology nobody on the team can operate.
- Diagrams that disagree with the text.
