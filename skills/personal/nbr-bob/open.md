# Open the day

Run each step for every circle, plus what the circle skill adds to the open.

1. Create today's note in every circle from its template:
   - Carry over the last note's open todos (`[ ]`, `[~]`, `[>]`) with their handoff links. Follow
     "Carry the work, not the history" in [filing.md](filing.md), plus what the circle skill adds.
   - On a new month, create the month's note and move the last one's open items into it.
   - Move into today's note the monthly items Nik plans for the day. Offer the top ones when he
     names none.
   - In a circle with a block calendar, propose the first one or two blocks from the note's focus
     todos. Place them around the day's meetings. Create them on Nik's yes, as
     [blocks.md](blocks.md) says.
2. Run the circle skill's checks (tickets, PR hosts). Then give Nik the news since his last day:
   - what waits on him first
   - then his own PRs, the day's meetings and open invites
   - then the rest, in a line each

   Reviews that wait on him go into the note.
3. Open today's notes in the panes of Bob's `Notes` tab. For each pane labelled `Private note` or
   `Work note` in this Rex session, `rex send-key` Escape. Then `rex send`
   `:e <absolute note path>` with its spaces escaped as `\ `, then Enter. Skip this step outside Rex
   or when the panes are missing.
4. Create the check-in once for the session with `CronCreate`: cron every 30 minutes (for example
   `7,37 * * * *`), with the prompt exactly `Bob check-in` and nothing else. A hook in the circle's
   notes repo matches that literal text. The hook drops the check-in when nothing changed. It also
   drops it while Nik wrote in the last 30 minutes, unless a meeting starts before the next run or
   ended since the last one. Otherwise it injects `checkin.md` and its digest. Never change or extend the prompt text, since the hook then misses it.

Done when every circle's note exists, every carried todo shows its current state, Nik has the news,
and the check-in runs.
