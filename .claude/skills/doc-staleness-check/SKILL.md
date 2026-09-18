---
name: doc-staleness-check
description: Use before opening or updating a pull request for a change that touches documented behavior, to check whether README, docs, help text, or usage examples now state something the change makes false. Skip for typo fixes, dependency bumps, and changes that don't touch documented behavior.
---

# Doc staleness check

Before opening or updating a pull request for a change that touches documented
behavior, check whether the change makes any repository-facing document say
something false. This applies in any repository, to any agent working in it —
nothing here depends on a specific tool's features.

**The test:** would a reader hit a statement this change makes false and act
on it? Most changes don't touch anything a document describes — skip this for
typo fixes, dependency bumps, and internal refactors with no behavior change.

## Scope

- files the branch touched, and repository-facing material near them
- `README.md`
- pages under `docs/`, **except** `docs/decisions/` if the repository has one — see below
- CLI help text and usage examples
- issue or PR references the diff makes inaccurate

## Look for

- behavior descriptions the diff falsifies
- setup, run, or recovery instructions that no longer match
- "disabled" / "pending" / "proposed" / "temporary" language the diff resolves
- statements that something has or hasn't happened, where the branch changes that fact

## Do not

- copyedit prose unrelated to the change
- rewrite anything under `docs/decisions/` (if present) to match the current
  state. That directory's job is the opposite: it records *why* a past
  decision was made, including rejected options — its test is "will this
  still be true in a year," not "does this match today." Leave it alone
  unless it presents itself as current guidance rather than a historical
  record.
- open, close, or edit an issue labeled `known-limitation` (if the repository
  uses that label) for any reason. A stale-looking reference there is a
  decision for a person to make, not something this check resolves — flag it
  in your summary instead.
- use a finding here as license for a broad rewrite. Prefer the smallest
  in-scope correction; apply it in the same change when the fix is clear,
  otherwise note it as a recommendation.

## Output

For each finding: file path, the stale statement, and the correction —
applied, if in scope for this change, or recommended, if not. If nothing
applies, say so; a clean result is a valid outcome, not a gap.

Summarize the result as a short prose note in the pull request description
(or the commit message, for a direct push) — not a checkbox. A checked box
records that the step was presented, not that it happened.
