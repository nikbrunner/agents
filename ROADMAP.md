# Roadmap

Where this repo is heading: one home for my agent setup, with dots keeping only machine wiring.

## Port the workflow improvements from work

The project skills in a work repo have moved ahead of their generic versions here. Generic parts to bring over:

- Commit and changelog: a light pre-commit next to a separate CI-parity pass, the changelog checked at commit time,
  breaking changes that still compile, the category read from the diff.
- `nbr-audit-docs`: a change-to-candidate-docs table, "a doc that repeats a code fact points to the code", and a
  fallback to the last five commits.
- Release: approval right before tagging.
- Worktree start and teardown: base branch from `origin/HEAD`, install in a new worktree, rebase-verify-fast-forward
  merges with no merge commits or force pushes.
- `nbr-record-clip`: measure the loop cycle in the page instead of passing it by hand.

## Make the engineering skills read well for colleagues

- `nbr-repo-conventions`, `-setup` and `-audit` speak of "personal projects"; the conventions apply to any TypeScript web
  project I control.
- Descriptions written in my name ("Nik's planning flow") read oddly in someone else's agent.
