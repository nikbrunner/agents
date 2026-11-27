# Close the day

Run each step for every circle.

1. Settle the open reports: ask each live session with unreported work for its state. A session
   whose work carries to tomorrow writes a handoff with `nbr-handoff`; link the file under the
   matching todo.
2. End the running blocks at their last signal, as [blocks.md](blocks.md) says. Check every open
   todo of the daily and monthly notes against each circle's activity skill, and tick what is
   already done: merged PRs, pushed commits, lifted reviews. A todo whose work someone else finished
   gets a context line saying so and does not carry. Then settle each routine check and open step
   from evidence first (activity, shell history, pane captures, Nik's own edits to the note), and
   ask Nik only about what no source shows; tick what he did.
3. Offer to tear down each session Bob launched whose work merged, with the Close section of
   `nbr-dispatch`; tear down only on Nik's yes.
4. Prune today's notes: done todos shrink by the "Done shrinks" rule in [filing.md](filing.md), and
   context that has served its purpose goes. Sort each list done first, then `[~]`, then `[ ]`.
5. Log the private day with `nbr-log`, and run what the circle skills add to the close.
6. Move each open todo of today's notes without a date or anyone waiting back to its place in the
   monthly note. Then create tomorrow's notes the way step 1 of [open.md](open.md) does, so the
   morning starts from them, and name tomorrow's first meeting to Nik; preparation it needs becomes
   a todo in tomorrow's note. Carried context names dates, never "today" or "yesterday". Then mark
   every carried todo `[>]` in today's notes; a template's routine checks stay as they are.
7. Reflect on the day with `nbr-self-reflection`: the corrections Nik made, the calls that went
   wrong and the ones that held. Bring the proposals to Nik and change a skill only on his yes.
8. Ask Nik with `AskUserQuestion` whether to commit each circle's notes repo as `chore: backup` and
   push it. This question is the `nbr-git-commit` approval for that commit, so Nik is asked once. On
   his yes, stage each changed and new note file by name. Read them from
   `git status --porcelain -z --untracked-files=all` and quote every path, since note names hold
   spaces. Then commit and push.
9. Stop the check-in with `CronDelete`.

Done when every circle's day is closed, the reflection went to Nik, tomorrow's notes hold every
dated or waiting task, the monthly notes the rest, and each notes repo is pushed or Nik declined the
backup.
