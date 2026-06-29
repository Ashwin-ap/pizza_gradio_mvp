---
description: Create a branch + self-contained spec file for the next session in mvp-design.md
argument-hint: "Session number, e.g. 2 (or S2)"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

You are a senior engineer preparing the next build **session** for the SliceMatic
Stage 2 Gradio MVP. The authoritative plan is `mvp-design.md` (the session specs in §5,
the frozen contracts in §4, conventions in §1), backed by `STAGE2_PLAN.md`.

Your job is ONLY to (a) create the session's git branch and (b) write a self-contained
spec file under `.claude/specs/`. **DO NOT implement the feature** — implementation happens
in a separate session the user opens later.

User input: $ARGUMENTS

## Step 1 — Parse the session number
From $ARGUMENTS extract integer `N` (accept `2`, `S2`, `s2`, `session 2`). Valid range **1–8**.
- `NN` = zero-padded 2 digits (1 → `01`).
If you cannot determine `N`, or it is out of range, stop and ask the user to clarify.

## Step 2 — Load the session spec from mvp-design.md
Read `mvp-design.md`. Locate the `### S{N} —` block in **§5**. Extract every field:
`title`, `Branch`, `Objective`, `Reasoning`, `Prerequisites`, `Reads`, `Creates`/`Modifies`,
`Tasks`, `Interface produced`, `Acceptance`, `DoD`.
Also read **§4 (Frozen contracts)** and **§1 (Conventions)** — you will embed the relevant parts.
- Use the `Branch` value from mvp-design.md **exactly** (e.g. `feat/02-menu-parser`).
- `feature_slug` = the branch with the `feat/NN-` prefix stripped (e.g. `menu-parser`).
If there is no `S{N}` block, stop and tell the user.

## Step 3 — Ensure a clean, committed baseline
Run `git status --porcelain`.
- If there are staged/unstaged changes to **tracked** files → stop; tell the user to commit or stash first.
- If the repo has **no commits yet** (unborn HEAD) → create a baseline so branches have a base:
  `git add -A && git commit -m "chore: planning docs baseline"`.
- Untracked files alongside an otherwise-clean tracked tree are fine (git carries them across branch switches).
Determine the integration branch `BASE`: detect the current default branch — `master` or `main`
(`git symbolic-ref --short HEAD` on a fresh repo, or `git branch --list master main`). Use whichever exists.

## Step 4 — Verify prerequisites are on BASE
mvp-design.md lists this session's `Prerequisites` (e.g. S4 needs S2 merged). For each prerequisite,
sanity-check its work is present on `BASE` (e.g. the expected function exists in `core.py`, or the
prereq branch was merged). If a prerequisite is clearly missing, warn the user and ask whether to proceed.

## Step 5 — Create the branch
- `git checkout BASE`
- `branch_name` = the session's `Branch`. If it already exists (`git branch --list`), append `-02`, `-03`, …
- `git checkout -b <branch_name>`
No remote operations — this is a local repo (no `origin`).

## Step 6 — Write the spec file (self-contained)
Save to `.claude/specs/<NN>-<feature_slug>.md` with **exactly** this structure:

---
# Spec — Session {N}: {title}

## Kickoff prompt (paste into a NEW session)
> Read `mvp-design.md` in full (especially §1 Conventions, §4 Frozen contracts, and the `S{N}` block in §5),
> then read this spec file `.claude/specs/<NN>-<feature_slug>.md`. Implement **Session {N}** to completion.
> Implement strictly to the frozen contracts — do not change any signature or data shape. Touch only the
> files listed under "Files". When done, run the verification command and confirm every Definition-of-Done
> item, then report results. Commit your work on the current branch `<branch_name>`.

## Objective
{Objective, verbatim from mvp-design.md}

## Why this session (reasoning)
{Reasoning, verbatim}

## Prerequisites
{Prerequisites} — confirmed present on `{BASE}`.

## Branch
`{branch_name}`  (base: `{BASE}`)

## Source references to read
- `mvp-design.md` → §1 conventions, §4 frozen contracts, the `S{N}` block in §5
- `STAGE2_PLAN.md` → {the section numbers named in this session's "Reads"}
- {any provided data files this session needs, e.g. Types_of_*.txt}

## Frozen contracts relevant to this session
{Embed the exact data shapes and/or function signatures from §4 that THIS session implements or calls —
copy them so the implementer never has to guess. Include the validator return convention if relevant.}

## Files
- **Create:** {files to create, from Creates}
- **Modify:** {files to modify, from Modifies}
- Do not create or modify any other files.

## Implementation tasks
{The session's `Tasks`, expanded into an ordered, checkable list.}

## Rules for implementation
- Implement to the §4 frozen contracts exactly; a contract change requires editing `mvp-design.md` first.
- `core.py` must not import `gradio` (pure logic) — applies to core sessions.
- Money: `float` + `round(…, 2)`; never hardcode menu data.
- Gradio pinned at `5.49.1`; Python 3.10–3.12.
- Conventional commits (`feat:`, `test:`, `chore:`); commit at working checkpoints.
- {Any session-specific rule, e.g.: keep validation in the primary `.click()` handler, never `.success()`;
  return the exact §2 error strings; raise `gr.Error` on invalid input.}

## Definition of done
A testable checklist built from this session's `Acceptance` + `DoD`:
- [ ] {acceptance item 1}
- [ ] {acceptance item 2}
- [ ] Verification command passes (see below)
- [ ] Work committed on `{branch_name}`; ready to merge into `{BASE}`

## Verification command
{`pytest -q` for logic sessions; for UI sessions: `python app.py` then the listed browser checks.}
---

## Step 6.5 — Commit the spec on the branch
`git add .claude/specs/<NN>-<feature_slug>.md` then
`git commit -m "docs: spec for session {N} — {title}"`.
This keeps the working tree clean so the implementing session starts fresh.

## Step 7 — Report to the user
Print this summary (and nothing more from the spec body unless asked):
```
Branch:    <branch_name>
Base:      <BASE>
Spec file: .claude/specs/<NN>-<feature_slug>.md
Session:   S{N} — {title}
```
Then tell the user:
"Open a NEW session and paste the **Kickoff prompt** from the spec to implement Session {N}.
After it finishes and every Definition-of-Done item passes, merge `<branch_name>` into `<BASE>`,
then run `/create-spec {N+1}` for the next session."
