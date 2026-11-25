#!/usr/bin/env bash
# UserPromptSubmit hook: Remind Claude of the nbr-voice rules on every turn.

jq -n --arg context "nbr-voice: big rocks first, the main point in a line or two, then stop and let Nik ask. Plain words. Every draft in Nik's name goes through the nbr-voice rewrite pass." '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: $context
  }
}'
