# Asking Nik

Ask Nik with `AskUserQuestion`, one question per call. It holds the whole session while it waits, so
ask at the end of a turn's work. While a meeting runs, a question waits for its end. While Nik has
said he is away from the keyboard, ask through the Rex palette instead, as the last two sections
describe.

- What goes into a question: the asks this skill names elsewhere, decisions that block work, and the
  yes a draft waits on.
- A draft (ticket, PR text, commit message) goes into chat; then Bob asks "Send the draft above?"
  with "Send (Recommended)" and "Change it".
- Chat carries reports and drafts. A question goes to chat only when it wants more than one line or
  a screenshot back. News never goes into a question.

## Writing a question

- It is one short, plain sentence.
- Context (session, branch, PR) leads in a few words, such as "Navbar improvements · PR 28: merged,
  tear it down?", or sits in an option's description.
- It stands on its own: names get a few words in parentheses, such as "Emma (UI components for the
  editor)".
- Tickets and PRs carry their titles. No labels Nik hasn't seen.
- Options are Nik's answers, in his voice ("No, it asks me first"), and each says who acts: "I" is
  Nik, "it" the worker, Bob by name. A worker's approvals are asked as a question about the worker:
  "PR 54 worker: may it commit and push alone?"
- The recommended option comes first and says "(Recommended)".
- A gate offers useful variants as options: "Commit", "Commit with the fixes", "Change it".

## Asking through the Rex palette

While Nik has said he is away from the keyboard, every question Bob asks Nik goes to the Rex command
palette through the `bob_ask` action (dots, `common/.config/rex/bob_ask.lua`), run in the
background. A Glass sound announces it, and every Rex app Nik has connected shows it; the first
answer wins. Bob acts on the answer.

- The palette shows the question as a single title line.
- The question and each option's label fit in about 50 characters, where the palette cuts them off;
  detail goes into the option's `subtitle`.
- One question per call. The palette holds one prompt at a time, so several questions go one after
  another.
- No answer (`timeout`, `cancelled`, `no_client`, `unsupported`, `failed`): ask in chat. `busy`
  means another prompt is open: wait a few minutes and ask again.

```sh
rex do bob_ask --timeout 61m --args - <<'JSON'
{"question": "Navbar improvements · PR 28: merged, tear it down?",
 "options": ["Tear down (Recommended)", {"id": "Not yet", "subtitle": "Branch PROJ-324-navbar-improvements"}],
 "timeout": 1800}
JSON
# → {"choice":"Tear down (Recommended)"}
```

- `options` are strings or palette items (`id`, `title`, `subtitle`); the answer names the `id`.
  Without options Nik types one line; `"multi": true` lets him tick several.
- `timeout` counts seconds, 3600 at most and by default. `rex do --timeout` outlasts it, or `rex do`
  stops the action and prints nothing.

## Reading the answer (exit 0)

- `{"choice": "<id>"}`, or a list with `multi`. Nothing ticked prints `{"choice": {}}` and means
  none.
- `{"text": "…"}`: he typed instead of picking, and his text is the whole answer. An empty text is
  no answer: ask again.
- `{"reason": "…"}`: no answer, handled as above.
- Exit 1 with "configuration file was reloaded" on stderr: a Rex config reload ended the prompt. Ask
  again.
- Any other exit 1 or 2 with a message on stderr: the call is wrong. Fix it and run it again.
