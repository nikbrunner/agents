# Asking Nik

Ask Nik with `AskUserQuestion`, one question per call. It holds the whole session while it waits,
so ask at the end of a turn's work. While a meeting runs, a question waits for its end. While Nik
has said he is away from the keyboard, ask through the Rex palette instead, as the last two
sections describe.

## Writing a question

- Ask the questions `nbr-bob` names, decisions that block work, and the yes a draft waits on.
- A draft (ticket, PR text, commit message) goes into chat. The question that follows asks whether
  to send it, with "Send (Recommended)" and "Change it".
- Chat carries reports, drafts and news. A question that wants more than one line or a screenshot
  back goes into chat too.
- The question is one short, plain sentence.
- Context (session, branch, PR) leads in a few words, such as "Navbar improvements · PR 28: merged,
  tear it down?". Or it sits in an option's description.
- The question stands on its own. A name gets a few words in parentheses, such as "Emma (search
  filters for the settings page)".
- Tickets and PRs carry their titles. Use no labels Nik hasn't seen.
- Options are Nik's answers, in his voice ("No, it asks me first"). Each option says who acts: "I"
  is Nik, "it" the worker, Bob by name. Ask a worker's approvals as a question about the worker:
  "PR 54 worker: may it commit and push alone?"
- The recommended option comes first and says "(Recommended)".
- A yes before an action offers its useful variants as options: "Commit", "Commit with the fixes",
  "Change it".

## Asking through the Rex palette

The `bob_ask` action (dots, `common/.config/rex/bob_ask.lua`) sends a question to the Rex command
palette. Run it in the background. A Glass sound announces it, and every Rex app Nik has connected
shows it. The first answer wins. Act on the answer.

- The palette shows the question as a single title line.
- The question and each option's label fit in about 50 characters, where the palette cuts them off.
  Detail goes into the option's `subtitle`.
- News never goes into the palette.
- The palette holds one prompt at a time, so several questions go one after another.

```sh
rex do bob_ask --timeout 61m --args - <<'JSON'
{"question": "Navbar improvements · PR 28: merged, tear it down?",
 "options": ["Tear down (Recommended)", {"id": "Not yet", "subtitle": "Branch feat/navbar-improvements"}],
 "timeout": 1800}
JSON
# → {"choice":"Tear down (Recommended)"}
```

- `options` are strings or palette items (`id`, `title`, `subtitle`). The answer names the `id`.
  Without options, Nik types one line. `"multi": true` lets him tick several.
- `timeout` counts seconds: 3600 at most, and 3600 by default. Keep `rex do --timeout` longer than
  it. Otherwise `rex do` stops the action and prints nothing.

## Reading the palette's answer

On exit 0:

- `{"choice": "<id>"}`, or a list with `multi`. Nothing ticked prints `{"choice": {}}` and means
  none.
- `{"text": "…"}`: Nik typed instead of picking, and his text is the whole answer. An empty text is
  no answer: ask again.
- `{"reason": "…"}` with `timeout`, `cancelled`, `no_client`, `unsupported` or `failed`: no answer.
  Ask in chat.
- `{"reason": "busy"}`: another prompt is open. Wait a few minutes and ask again.

On exit 1 with "configuration file was reloaded" on stderr, a Rex config reload ended the prompt.
Ask again. Any other exit 1 or 2 with a message on stderr means the call is wrong. Fix it and run it
again.
