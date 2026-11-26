---
name: nbr-intercom
description:
  Intercom between agent sessions running in different repos, through Claude Code cross-session
  messages (ListAgents, SendMessage), with Rex panes to find peers and reach the ones ListAgents
  misses. Use when the user says "intercom" or asks to check with, ask, or get status from another
  session, and when the current work needs an answer from another repo, touches work going on there,
  or turns up an issue that belongs there.
compatibility:
  Requires Claude Code cross-session messaging (ListAgents and SendMessage); the rex CLI to find
  panes and reach Pi, Codex or sessions under another Claude config dir.
---

# Intercom

A **peer** is another agent session already running in some repository. Claude Code memory is per
working directory, so the peer holds context this session lacks: its repo's memory, its
conversation, the files it has read. Talking to it directly keeps the user from relaying messages
between sessions by hand.

A conversation starts one of two ways:

- **The user starts it**: they ask you to sort something out with the session in another repo, or to
  find out where its work stands.
- **The work starts it**: the current work depends on or affects the peer's repo. A question's
  answer lives there, a change here has to be accounted for there, or an issue found here belongs
  there.

Either way, stay in the conversation until the issue or discussion is resolved and every party is in
sync. Ask follow-ups, answer the peer's questions, and loop in a further session when the topic
touches its repo too. Resolved means every party can state the same outcome: close with a message
summing up what was agreed and who does what, and wait for each peer to confirm it or correct it.
Then report to the user.

A plain answer or status check, with nothing agreed and nobody holding a follow-up task, ends
without a closing message. Once you or the user decide something based on what a peer told you, tell
that peer the decision, so its work accounts for it. When it is unclear whether a peer should hear
back, ask the user. Every message serves the work in front of you. When nothing depends on the reply
or the notice, leave the peer alone.

## Find the peer

Run `ListAgents`. It shows the Claude sessions under the same Claude config dir by name, prefixed by
repo: `shop-web-66` runs in shop-web, `iter-nvim-be` in iter.nvim. A listed peer is reached with
`SendMessage`. When several names match, ask the user which one.

In Rex (`REX_BLOCK` is set), Rex shows which session and pane runs which repo, across every config
dir and harness:

1. `rex ls` lists sessions by label (a repo name, or a PR title like
   `PR 20 · Search configuration`).
2. `rex block ls -s <session>` lists its panes; an agent pane carries its current topic and the
   session's persona (`Brush wheel keys · Clara`), or `Agent I`, `Agent II`, … before its first
   prompt.
3. `rex capture -s <session> -b <block> | tail -25` shows the pane's state; a Claude status line
   names the repo and the Claude session (`[Bob]`, `[pr-20-search-config]`).

Use Rex to settle which `ListAgents` name belongs to which repo, to read a peer's state when that
saves a question, and to find a peer `ListAgents` misses: a session under another
`CLAUDE_CONFIG_DIR` (such as `cc work`), or a Pi or Codex agent.

When neither lists a session in that repo, the message has no receiver. Tell the user.

## Write the message

The peer answers in whatever shape it is given, so the message carries the convention:

- A first line naming the asking session and the topic:
  `From the writing session: 3 questions on iter.nvim manuscript annotations`
- Numbered points, so the reply can be numbered to match.
- A length cap for the reply, such as "Reply under 1500 characters."
- A request to mark guesses as guesses, separate from what the peer verified.
- For a notice, say whether you need a reply at all.

A request to change something in the peer's repo is a proposal. The peer decides with its own human
whether to act.

## Send

**A peer in `ListAgents`**: send with `SendMessage`, then end the turn. The reply arrives as a new
message. A peer running in another permission mode holds the message until its human approves it,
and a delivery notice says so.

**A peer only Rex finds**: paste the message into its prompt.

1. Send it as a bracketed paste, so its newlines stay in the input instead of submitting it, then
   submit it: `rex send -s <session> -b <block> $'\e[200~'"$message"$'\e[201~'` and
   `rex send-key -s <session> -b <block> Enter`. Check with `rex capture` that it shows after a `❯`
   prompt.
2. The reply stays in the peer's pane. When you need it, wait with the `Monitor` tool. Its command
   is an until-loop on `rex capture` that exits on the pane's next `· done HH:MM` line (`timeout_ms`
   up to 1800000). When the monitor exits, read the reply from the capture.

Tell the user in one line which Rex session and pane you used.

## Answer

When a peer writes, answer from your own context, numbered, under its cap, with guesses marked.

## Report to the user

When every party has confirmed the outcome, give the user the gist in a few lines: who you talked
to, what was asked or flagged, what came back, what is still a guess. When a decision comes up that
the user should have a say in, ask them right then and tell the peer the topic waits on them.
