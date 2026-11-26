---
name: nbr-dispatch
description:
  Start a coding agent in a repository's Rex session, or close that session once its work is done.
  Use when the user or a skill dispatches, spawns or hands off a task to Claude Code, Pi or Codex,
  or tears a session down.
compatibility: Requires Rex and lager.
---

# Dispatch

Starts a coding agent in a repository's Rex session, or closes that session. Lager creates and
removes worktrees and sessions; Rex finds sessions and panes. Runs inside Rex (`REX_BLOCK` set);
otherwise report blocked, and never do the task inline.

## Inputs

From the caller; a direct dispatch asks the user for what it needs.

- `repo`: the checkout, the `found_path` of its row in `lager status --json`, confirmed by the user.
  The row's `changes` is the pre-existing state.
- `worktree`: none, or its name, with a new branch and its base or an existing local or remote
  branch.
- `install`: `normal`, `no-scripts` or `skip`, with the package roots.
- `brief`: a file. `harness`: the agent CLI, by default the one running this session. `config_dir`,
  `label` and `name` when the caller has them.

## Session

1. Find the live session in Rex: `rex ls --json` lists `.sessions[]` with `session_id` and `label`;
   a pane's `.foreground.cwd` from `rex block call -s "$session" -b <block> process` settles an
   unclear label. An agent already working there: offer `nbr-intercom` instead.
2. None: create it with lager.
   - The checkout as it stands: `lager session create "$repo" --json`.
   - A new worktree: `lager worktree add "$repo" "$name" --fetch --create-session --json` with
     `--new-branch "$branch" --start "origin/$base"`, or with `--branch "origin/$branch"` for a
     pushed branch. That reaches the local branch when one exists, else it creates one that tracks
     the remote branch. With `--branch`, drop the `"$name"` argument to take the branch's last
     segment. The document's `path` is the worktree. When it reports `behind` above 0 and `ahead` 0,
     run `git -C "$path" merge --ff-only "$upstream"`, since lager never moves a branch.
   - A worktree that exists: find its `path` in `lager worktree list "$repo" --json`, run
     `lager session create "$repo" "$name" --json`, and `git -C "$path" pull --ff-only` when it is
     clean.
   - Workaround until lager takes a label: `rex session rename "$session" "$label"`.
3. Install by the repo's `AGENTS.md` in each package root, else the checkout's root. `no-scripts`
   skips lifecycle scripts (`npm ci --ignore-scripts`), and code nobody has reviewed yet, such as a
   PR under review, always gets it.

## Launch

A caller's brief goes as it stands. A direct dispatch writes the task followed by:

```text
You are the dispatched worker. Work only in this repository and pane; start no other agents, worktrees or Rex commands.
Ask before anything hard to undo or outward-facing; a yes typed here or relayed by the dispatching session settles it.
Pre-existing changes: <clean, or the status>. Commit: <only after approval, or as you go>.
When done, reply only with: Repository, Task, Status, Changes, Verification, Remaining issues, Suggested next step.
Report to <this session's name> with SendMessage: "On it" when you start, the handoff when done.
```

The last line goes in only when both sides run Claude Code under the same config dir; this session's
name is the first line of `ListAgents`.

Take the first pane of the session's first tab whose foreground is a shell with an empty prompt
(`rex block ls -s "$session" --json`, `rex block call … process`, `rex capture`); none: ask the
user. Type one line into it:

```sh
line="claude -n '$name' \"\$(cat '$brief')\""    # with config_dir: env CLAUDE_CONFIG_DIR='$config_dir' claude …; Pi or Codex: $harness "$(cat '$brief')"
rex send -s "$session" -b "$block" "$line" && rex send-key -s "$session" -b "$block" Enter
```

Check with `rex capture -s "$session" -b "$block" | tail -25`: a denial or dialog goes back to the
user word for word. Return the session, pane and name, and leave the worker alone.

## Close

Ask each other agent in the session through `nbr-intercom` whether it is done and what is still
open; anything open, or no answer, stops the close. Stop what still runs in its panes (`ctrl+c`, and
`docker compose down` where Compose ran). Then, last, since it ends the session it runs in:

```sh
lager worktree remove "$path" --yes --close-session    # the checkout as it stands: lager session close "$repo"
```

Workaround until lager can let ignored files go: when it refuses over ignored files alone
(`node_modules`), rerun with `--force`; any other loss stops the close. The branch stays.
