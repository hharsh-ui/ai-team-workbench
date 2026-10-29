---
name: learning-loop
description: Turn mistakes, corrections and finished work into lasting improvements - record lessons, run retrospectives, and propose updates to skills, agents, the team instructions, memory or project knowledge with approval. Also the guide for creating or editing skills, agents and prompt files safely. Use after a correction or failure, at the end of a project, for "what did we learn", or when creating or changing a skill, agent or prompt.
---

# Learning Loop

The goal: the same mistake never happens twice, and good ways of working spread to every future task.

## A. Right after a mistake (small and immediate)

1. Acknowledge it plainly, without excuses.
2. Fix the immediate problem.
3. Record it: `python scripts/wb.py call lesson_add title="<short name>" status=RULE symptom="<what went wrong>" cause="<why>" fix="<what fixed it>" rule="<what to do next time, as an instruction>"`.
4. Route the lesson:

| Lesson | Destination | Approval |
|---|---|---|
| A specific error and its fix | `knowledge_base/lessons.md` | Not needed |
| A better way to do a recurring kind of task | The matching skill | Needed |
| A rule for one role | That agent file | Needed |
| A rule for everyone | `.github/copilot-instructions.md` | Needed |
| A preference of the user | Memory, or the team instructions | Confirm |
| A fact about a project | `knowledge_base/project_knowledge.md` | Confirm important facts |

5. Tell the user in one line what was recorded and what is proposed.

## B. Retrospective (end of a project or a painful task, about ten minutes)

Use [the retrospective template](../../../templates/retro.md): goal versus outcome; what went well; what went wrong (facts, not blame); root causes; lessons; actions with an owner and a destination. Look at the whole pipeline: were the PRD's criteria testable, did the design hold, how many test rounds were needed and why. Save it as `artifacts/retro-<date>.md` in the work area, record the key lessons, and propose the skill or instruction updates. For numbers from the Git history (commit types, hotspots, test health), use the gstack retro method.

## C. Changing skills, agents or the team instructions

1. Commit or back up the workbench first (`git add -A`, then `git commit -m "Before <change>"`).
2. Propose the exact text to add or change, why, and the lesson it comes from.
3. After approval, edit the file. Keep each change small.
4. Validate: `python scripts/check_workbench.py` must pass.
5. Add a session-log entry: "Skill updated: <name> — <what changed>", and commit.

Keep skills focused: steps, checklists, short examples, under 500 lines. Remove stale content. A one-line rule beats a long story.

## D. Creating a new skill

Create one when a kind of task has come up three or more times with a stable method, or needs special knowledge.

- Folder name in lowercase with hyphens: `.github/skills/<name>/`. The file is always `SKILL.md`; extra material can sit next to it (`scripts/`, `references/`, `assets/`) and is linked with relative paths.
- The frontmatter `name` equals the folder name. The `description` says what the skill does and when to use it, with trigger words, in at most 1024 characters, without a colon followed by a space (or put the whole description in quotes).
- Skeleton:

```markdown
---
name: api-design
description: Design clear, consistent HTTP APIs - resources, endpoints, errors, versioning and pagination. Use when designing or reviewing an API.
---

# API Design

## When to use
## Steps
## Checklist
## Common mistakes
```

- Add it to the skills table in `.github/copilot-instructions.md` (Section 14) and to the skill list of the agents that should use it; run the checks. The tests fail if a skill is not mentioned in the team instructions.
- Test it like code (superpowers writing-skills): try a few realistic tasks without the skill, then with it, and keep it only if the behaviour clearly improves.

## E. Creating or editing an agent

- File: `.github/agents/<Name>.agent.md`; frontmatter `name` equal to the file name without `.agent.md`, a `description` with trigger words, optional `argument-hint` and `handoffs` (each with `label`, `agent`, `prompt`, `send: false`). Handoffs may only point to agents that exist. Do not set `model`; the user picks it.
- Body: the role's mission, skills, what it never does, a numbered process, its handoff rules and a quality checklist. Shared rules stay in the team instructions — do not copy them into agents.

## F. Creating a prompt file (slash command)

`.github/prompts/<name>.prompt.md` with a `description`, optionally `agent: <AgentName>` and `argument-hint`. The body is one focused task. The user runs it by typing `/<name>` in the chat.

## G. Memory hygiene

Short bullets. No secrets. Fix or remove entries that turn out wrong. User scope holds preferences; repository scope holds verified facts and commands; session scope holds the current plan.

## H. Periodic review (monthly, or when the lessons pass about 50 entries)

Merge duplicates; mark outdated lessons OBSOLETE (never delete them); promote RULE lessons that keep recurring into the relevant skill; check that pending items in the session log are still pending.
