# dash

A session dashboard in the band above the prompt: repo and branch, changed files, the last commit, model and account, usage limits, cache state and cost, open tasks, and a one-line summary of what the conversation is working on. At 150 columns and wider it splits into two columns.

On a terminal of 144 columns and wider, the dash sits in a pane beside the transcript (fullscreen mode) and the band steps aside. `/dash side` opens that pane at any width; closing the pane brings the band back.

`/dash` hides and shows it.

The git rows follow a commit, staging, a branch switch, a push or a fetch within a second or two, whoever runs it. A file edited outside the session shows at the next prompt or tool call.

Its **Review** and **Audit** buttons run `/ponytail-review` and `/ponytail-audit` from the ponytail plugin.

Pressing a changed file opens it in the `Editor` block of the current Rex session: in its nvim when one runs there, else as `nvim <file>` in its shell. The Edit tab then takes the focus.

In Rex, a named session (`claude -n` or `/rename`) gives its pane that name, so Rex's session switcher lists the pane by it. An unnamed session leaves the pane's label as it is.

## Settings

| Variable     | Does                                                                                              |
| ------------ | ------------------------------------------------------------------------------------------------- |
| `DASH_BADGE` | Shows a red badge with this text next to the account, such as `WORK` for a second login. Optional |

Set it in the `env` block of Claude Code's `settings.json`, or in the shell function that starts that login.

The cache row counts down from one hour, so it matches `"promptCacheTtl": "1h"`. With another cache setting, the countdown is off.

## Cost

The one-line summaries come from small Haiku calls during the session, billed to the Claude account the session runs on.
