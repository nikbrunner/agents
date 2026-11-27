# agents

My agent setup: skills, hooks, mods and harness config. The README says what each part is.

## This repo is public

Nothing from my employer goes in: no company name, host, repo, ticket key, colleague or work path.
Work-specific values live in my work repo, which installs private files that the public files read,
such as `~/.config/agents/ticket-projects`. Examples in skills and tests use neutral values
(`shop-web`, `PROJ-42`). Git history stays public, so a slip is published for good.

## Hook logic stays harness-neutral

Every hook, extension or mod that checks or enforces something keeps its logic in a plain CLI. The
CLI takes text or JSON on stdin or as arguments, prints findings, and sets an exit code. A Claude
Code hook, a Pi extension or a Codex hook is a thin adapter around that CLI. A rule never lives
only inside one harness's hook format.

Examples: `skills/personal/nbr-voice/scripts/lint.py`, which `voice-words.py` and `voice-docs.py`
call, and `skills/personal/nbr-bob/scripts/checkin.py`, which a circle's hook calls.
