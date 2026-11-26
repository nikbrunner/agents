# Close the day

Run each step for every circle.

1. Settle the open reports. Ask each live session with unreported work for its state. A session
   whose work carries to tomorrow writes a handoff with `nbr-handoff`. Link the file under the
   matching todo.
2. End the running time blocks at their last signal, as [blocks.md](blocks.md) says. Read
   [filing.md](filing.md) before the next steps touch the notes.
3. Check every open todo of the daily and monthly notes against each circle's activity skill. Tick
   what is already done: merged PRs, pushed commits, lifted reviews. A todo whose work someone else
   finished gets a context line saying so, and it does not carry.
4. Settle each routine check and open step from evidence first: activity, shell history, pane
   captures, Nik's own edits to the note. Ask Nik only about what no source shows. Tick what he did.
5. Offer to tear down each session Bob launched whose work merged, with the Close section of
   `nbr-dispatch`. Tear down only on Nik's yes.
6. Prune today's notes. Done todos shrink by the "Done shrinks" rule of filing.md. Context that
   has served its purpose goes. Sort each list: done first, then `[~]`, then `[ ]`.
7. Log the private day with `nbr-log`.
8. Run what each circle skill adds to the close.
9. Move each open todo of today's notes without a date or anyone waiting back to its place in the
   monthly note.
10. Create tomorrow's notes the way step 1 of [open.md](open.md) does, so the morning starts from
    them. Name tomorrow's first meeting to Nik. Preparation it needs becomes a todo in tomorrow's
    note. Carried context names dates, never "today" or "yesterday".
11. Mark every carried todo `[>]` in today's notes. A template's routine checks stay as they are.
12. Reflect on the day with `nbr-self-reflection`: the corrections Nik made, the calls that went
    wrong and the ones that held. Bring the proposals to Nik. Change a skill only on his yes.
13. Ask Nik with `AskUserQuestion` whether to commit each circle's notes repo as `chore: backup` and
    push it. This question is the `nbr-git-commit` approval for that commit, so Nik is asked once.
    On his yes, stage each changed and new note file by name. Read them from
    `git status --porcelain -z --untracked-files=all` and quote every path, since note names hold
    spaces. Then commit and push.
14. Stop the check-in once with `CronDelete`.

Done when every circle's day is closed and the reflection went to Nik. Tomorrow's notes hold every
dated or waiting task, the monthly notes hold the rest, and each notes repo is pushed or Nik
declined the backup.
