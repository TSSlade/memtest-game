---
name: issue-workflow
description: Use when asked to implement, fix, or otherwise handle a specific GitHub issue in this repository. Takes the issue through isolated worktree development to an open, verified PR. Also use when resuming that work or addressing review feedback. Does not authorize merging.
---

# Issue workflow

Follow `AGENTS.md` for decision authority, testing requirements, commit-history preservation, explanation requirements, and the completion gate. This skill supplies the procedure. If the user requests only investigation or advice, stay within that scope.

## 1. Establish the work and its ownership

Read the issue, relevant comments, parent and sub-issues, and linked PRs. Identify:

- The requested outcome and evidence that would demonstrate it.
- Constraints, dependencies, and decisions already settled.
- Work already completed or being handled elsewhere.

Inspect the repository's actual state: remote, intended base branch, local changes, branches, and registered worktrees. Do not assume the current checkout is the appropriate starting point.

If a matching branch, worktree, or PR exists, determine whether it belongs to this work and can be resumed. An issue number in a branch name alone does not establish ownership. If another session appears to be working on it and ownership is unclear, consult the user before proceeding with competing implementation. Never change another session's checkout, discard its changes, or reset or remove its branches or worktrees. Worktrees share repository metadata: avoid repository-wide configuration changes and other operations that could interfere with concurrent sessions.

Apply the repository's sub-issue rules when work needs decomposition. Do not create issues merely to list steps you are about to perform.

## 2. Create or resume the isolated workspace

Fetch the intended base without switching or modifying the user's checkout.

Create a dedicated branch and worktree, using a descriptive issue-based name such as `codex/issue-123-short-description`. Choose an unused sibling worktree location outside the primary checkout. If the current task is already running in a suitable dedicated worktree, use it.

Verify the resulting worktree's absolute path, branch, starting commit, and clean status. Run subsequent implementation and validation commands with that worktree explicitly selected.

Read applicable instructions inside the worktree. Set up dependencies using the repository's prescribed tools. Keep generated environments and temporary output isolated. If tests or services require ports, databases, or other shared resources, choose independent resources so concurrent sessions do not interfere.

Respect the repository's WSL/Windows boundary rules for file writes and Git mutations.

## 3. Establish the approach and decision checkpoints

Inspect the relevant code and tests before choosing the implementation.

State the intended behavior, initial test scope, and any broader verification likely to be needed. Keep this working plan in the conversation; do not create a repository status file.

For a decision requiring consultation under `AGENTS.md`, present a concrete recommendation with alternatives and implications. Wait before implementing dependent work.

For autonomous architectural or strategic choices:

1. Establish a clean, identifiable pre-decision commit.
2. Keep the implementation of the choice separate from unrelated changes.
3. Record the rationale and alternatives in the commit body or appropriate tracked documentation.
4. Retain the commit references for the final handoff.

An existing clean commit can serve as the checkpoint; do not manufacture empty commits. A checkpoint must contain the work needed to make returning to it useful.

## 4. Implement in tested increments

For each behavior change:

1. Add or adjust a focused behavioral test.
2. Run it and confirm that it fails because the requested behavior is missing or incorrect.
3. Implement the smallest coherent solution.
4. Rerun the focused tests.
5. Refactor and rerun affected checks.
6. Inspect the diff and staged files, then commit the coherent increment.

Do not treat an unrelated setup failure as the expected red test. If the behavior cannot practically be tested automatically, explain why and use reproducible validation appropriate to the change.

Commit at meaningful milestones, especially around decisions. Do not leave all work for one final commit or create a commit for every mechanical edit.

Expand verification when shared code, interfaces, dependencies, configuration, or other changes suggest a broader impact. Run required completion checks at the appropriate milestone; repeated full-suite runs need a reason.

## 5. Prepare the PR and its explanation

Review the complete diff against the intended base. Check for unrelated files, accidental generated output, sensitive material, and changes inherited unintentionally.

Run `doc-staleness-check` when documented behavior changes.

For a code-focused PR, invoke `explain-diff-html` now, while the implementation context is available. Follow its artifact-generation instructions, subject to the mandatory invocation and worktree-local output policy in `AGENTS.md`. Commit the artifact in this branch and prepare its link for the PR body. For exempt maintenance-only PRs, omit it.

Run the completion checks the affected project requires for the kind of change made, as that repository's own instructions define them — `AGENTS.md` here names them per path. Run them against the changed working tree, using the repository's supported procedure rather than an ad-hoc equivalent.

Record which revision was tested and what each check establishes. After a subsequent code change, rerun affected checks rather than relying on results for an older revision.

If the base has advanced, assess whether integration is needed for correctness or required checks. Preserve decision history. Where necessary, merge the updated base into the issue branch and validate the combined result; do not rebase away checkpoints.

## 6. Open and verify the PR

Push the issue branch and open the PR against the verified base.

Write the description for someone who has not seen the conversation. Include:

- The problem and resulting behavior.
- Appropriate closing references for the issues actually completed.
- Verification evidence and material limitations.
- Meaningful decisions, rationale, and checkpoint references.
- The explanation artifact link when required.

For partially completed parent issues, describe the relationship without a closing reference that would incorrectly close the parent.

Read back the published PR. Verify its base, head, description, issue linkage, and artifact link. Check required remote results against the current head commit.

Resolve failures caused by this work and rerun the relevant checks. Treat unrelated or unavailable checks as explicit blockers, not passing evidence. Use a draft PR when a blocker prevents the completion gate, and report what remains unresolved.

Do not merge, enable auto-merge, or manually close the issue.

## 7. Hand off and retain the workspace

Once the PR meets the completion gate, report:

- The PR link and resulting behavior.
- Tests and checks performed, with their outcomes.
- Meaningful decisions, alternatives, tradeoffs, justification, and implications.
- Commit references showing the pre-decision checkpoint and resulting implementation.
- Any limitations and the retained worktree path and branch.

Verify that the intended work is committed and pushed. Identify any intentionally retained local-only material.

Leave the branch and worktree available for review. Do not start a background monitor unless requested.

## 8. Resume review or perform later authorized cleanup

For review revisions, first re-read the PR, new comments, and current local and remote state. Confirm ownership, preserve existing decision commits, and make revisions in additional commits. Update the explanation when the behavior or reasoning changes, then repeat affected verification and the PR completion check.

Cleanup is a separate, later authorized operation. Before removing anything:

1. Verify whether the PR was merged or closed and confirm the intended disposition of its work.
2. Check for uncommitted and unpushed work, including local-only files.
3. Confirm the exact worktree and branch belong to this task.
4. Remove only those resources authorized for cleanup.
5. Read back the remaining worktrees and branches to verify the effect.

Do not force deletion merely because a squash merge makes Git report the branch as unmerged. Verify that its changes were incorporated and that no unique work would be lost before proceeding.
