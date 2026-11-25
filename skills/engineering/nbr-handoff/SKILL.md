---
name: nbr-handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the
work.

## Where to save

Save to the root of the **current working tree**, so the handoff sits next to the work it describes.
Inside a worktree, that is the worktree, not the main checkout:

```sh
ROOT=$(git rev-parse --show-toplevel)
```

Save to `${ROOT}/handoffs/YYYY-MM-DD-<slug>.md`, where `<slug>` is a short kebab-case identifier for
the focus area (e.g. `2026-05-28-brand-color-token.md`).

Before writing:

- Create `${ROOT}/handoffs/` if it does not exist.
- Ensure `handoffs/` is listed in `$(git rev-parse --git-common-dir)/info/exclude`. Handoffs are
  ephemeral and must not be tracked, and a local exclude keeps them out of the user's diff without
  touching the tracked `.gitignore`. In a worktree `.git` is a file, so resolve the path with
  `--git-common-dir`; the exclude then applies to every worktree of the repo.
- Name the branch and worktree path in the handoff itself, so the next agent knows where it is.

A handoff in a worktree is deleted with that worktree. When the next session will run after the
worktree is closed, say so before writing.

Open with the goal and its priority: what Nik needs next, and by when. The order of work follows
from that goal. Where the handoff puts other steps ahead of an urgent goal, it says why in one line,
or marks the order as a question for Nik, so the next session raises it before starting.

Suggest the skills to be used, if any, by the next session.

Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits,
diffs). Reference them by path or URL instead.

If the user passed arguments, treat them as a description of what the next session will focus on and
tailor the doc accordingly.
