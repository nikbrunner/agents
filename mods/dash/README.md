# dash

A session dashboard in the band above the prompt: repo and branch, changed files, the last commit, model and account, usage limits, cache state and cost, open tasks, and a one-line summary of what the conversation is working on. At 150 columns and wider it splits into two columns.

`/dash` hides and shows it.

## Settings

| Variable     | Does                                                                                              |
| ------------ | ------------------------------------------------------------------------------------------------- |
| `DASH_BADGE` | Shows a red badge with this text next to the account, such as `WORK` for a second login. Optional |

Set it in the `env` block of Claude Code's `settings.json`, or in the shell function that starts that login.

The cache row counts down from one hour, so it matches `"promptCacheTtl": "1h"`. With another cache setting, the countdown is off.

## Cost

The one-line summaries come from small Haiku calls during the session, billed to the Claude account the session runs on.
