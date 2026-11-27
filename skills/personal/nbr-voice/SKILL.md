---
name: nbr-voice
description:
  How agents talk to Nik and write prose in his name, private and at work. Use for every reply, and
  run every draft (PR description, ticket, commit, doc, note, Slack message) through its rewrite
  pass before it goes out.
---

# Voice

How you talk to me, and how prose you write in my name reads. It holds for every reply and every
draft, in my own projects and at work.

## Guides

Read the guide for what you write before you write it:

- A reply to me: [`references/conversation.md`](references/conversation.md), with big rocks first
  and how we talk. In Claude Code a session-start hook has already put it in your context.
- A draft in my name (PR description, ticket, commit, doc, note, Slack message):
  [`references/drafts.md`](references/drafts.md), with its rewrite pass.
- Steps, runbooks, how-to-test lists and instructions for agents:
  [`references/instructions.md`](references/instructions.md).

## Plain words

Machine-written text has fingerprints, and they count in replies to me as much as in drafts. In
every reply: the plainest word that survives (`use` for `leverage`), a comma or a full stop where an
em-dash wants to go, sentences of uneven length, a position taken, an ending on a point. In lists
and notes: one thing per bullet, so three changes are three bullets; and the actual items in plain
words, with no umbrella label (`foundations`, `improvements`, `polish`) standing in for them.

[`references/rules.toml`](references/rules.toml) lists the words and patterns that mark
machine-written text, each with its plain fix. Read it before a draft or durable prose goes out.
`scripts/lint.py` runs those rules. In Claude Code a Stop hook runs it on every reply, and a
document hook runs it on every Markdown file an agent writes. A phrase you discuss rather than use
goes in backticks.
