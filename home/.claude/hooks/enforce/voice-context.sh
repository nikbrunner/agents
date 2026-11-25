#!/usr/bin/env bash
# SessionStart hook: Put the nbr-voice skill in context, so it is in force from the first reply.
# Fires on startup, resume, clear, and compact, so the voice survives compaction.
# The body must stay under the 10,000-character cap on hook context.

set -euo pipefail

SKILL="$HOME/.agents/skills/nbr-voice"
[ -f "$SKILL/SKILL.md" ] || exit 0

body=$(awk 'NR == 1 && /^---$/ { fm = 1; next } fm && /^---$/ { fm = 0; next } !fm' "$SKILL/SKILL.md")

jq -n --arg context "The nbr-voice skill is in force for this session, so it needs no Skill call; its folder is ${SKILL}.

${body}" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $context
  }
}'
