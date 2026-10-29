---
name: security-review
description: Security checks for designs and code - threat modeling with STRIDE, an OWASP Top 10 review, secret and dependency checks, authentication and authorization, input validation, privacy and secure defaults. Use before building anything with users, personal data, payments or internet exposure, before a release, when reviewing code for security, or when asked "is this secure?". Produces a threat model and prioritized findings with fixes.
---

# Security Review

Three parts: **A** threat model for a design (Developer), **B** security review of code (Tester, and the Developer on its own diff), **C** pre-release checklist (Tester). Always use fake data, and test only systems you own or are authorized to test.

## A. Threat model (before building)

Use [the threat model template](../../../templates/threat-model.md) and save it as `docs/threat-model.md`.

1. **Describe the system:** assets (accounts, personal data, money, availability, reputation), actors (users, admins, outsiders, attackers), entry points (pages, APIs, uploads, webhooks) and trust boundaries. Draw them in Mermaid.
2. **STRIDE** for each component and flow:
   - **S**poofing — pretending to be someone else (weak login, stolen sessions).
   - **T**ampering — changing data or code (unvalidated input, unsigned updates).
   - **R**epudiation — denying an action (no audit log).
   - **I**nformation disclosure — leaking data (verbose errors, open storage buckets).
   - **D**enial of service — making it unavailable (no rate limits, huge uploads).
   - **E**levation of privilege — doing more than allowed (missing authorization checks).
3. For each threat note likelihood and impact (Low, Medium, High), the mitigation and its status. Handle High-High first. Mitigations become requirements (PRD IDs or backlog items).
4. **Privacy:** collect the minimum, define retention and deletion, encrypt in transit and at rest, record consent where needed, and flag legal questions (for example GDPR) for an expert. You do not give legal advice.

## B. Code review checklist (OWASP Top 10, 2021)

- **A01 Broken access control:** authorization on the server for every request; users reach only their own records (try changing an ID in the URL); deny by default; strict CORS.
- **A02 Cryptographic failures:** HTTPS everywhere; passwords hashed with Argon2 or bcrypt; no home-made cryptography; no sensitive data in URLs or logs; secrets from the environment or a secret store.
- **A03 Injection:** parameterized queries or an ORM; no `eval` or `exec` on user input; output escaped against cross-site scripting; shell commands never built from user input.
- **A04 Insecure design:** a threat model exists; rate limits; business-logic abuse (negative quantities, replayed coupons, skipped steps).
- **A05 Security misconfiguration:** debug mode off in production; default passwords removed; security headers (Content-Security-Policy, Strict-Transport-Security, X-Content-Type-Options, frame-ancestors); least-privilege cloud permissions; errors without stack traces.
- **A06 Vulnerable components:** lockfiles committed; dependencies pinned and audited (`npm audit`, `pip-audit`, `osv-scanner`); unused packages removed.
- **A07 Authentication failures:** rate limits or lockout on login; secure session cookies (HttpOnly, Secure, SameSite); session expiry; single-use, short-lived reset tokens; a multi-factor option for sensitive apps.
- **A08 Integrity failures:** no deserialization of untrusted data (for example Python `pickle`); verified downloads; protected CI secrets.
- **A09 Logging and monitoring:** security events (logins, failures, permission denials) are logged without secrets or personal data, and someone gets alerted.
- **A10 Server-side request forgery:** outgoing URLs validated against an allowlist; internal addresses blocked.
- **Also:** file uploads (type and size checks, stored outside the web root); CSRF protection when cookies are used; open redirects; secrets in Git (search the code and the history); AI features (prompt injection, unsafe use of model output, private data leaking into prompts).

Useful tools, if installed or approved to install: `pip-audit`, `npm audit`, `bandit` for Python, `semgrep`, `gitleaks`. Never upload code to an unknown online scanner without approval. For a deeper audit, apply the static parts of the gstack cso method (application model, attack-surface census, evidence for every finding).

**Report findings** in a table: ID, severity (Critical, High, Medium, Low, Info), file and line, issue, impact, concrete fix, status. Critical and High block acceptance.

## C. Pre-release checklist

Threat model up to date · all Critical and High findings fixed · dependencies audited · no secrets in the repository or its history · backups made and a restore tested · logging and alerts working · a privacy notice if personal data is collected · a named contact for security problems.

## If a secret is exposed

Tell the user immediately. The fix is to **rotate** the secret (revoke it and issue a new one); deleting the file is not enough, because Git history keeps it. Rewriting history is a separate step that needs explicit approval.
