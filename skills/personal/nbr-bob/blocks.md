# Time blocks

A circle with a block calendar keeps the day's work in it as events. A block ahead of now is the
plan, a block behind now is the record; the plan reaches one or two blocks ahead. Agents' work
counts, so parallel work shows as overlapping blocks.

- One block is one piece of work (a todo, ticket or PR), titled as the note writes the todo. Create
  it with
  `ical add "<title>" -c <block calendar> -s <start> -e <end> --url <the todo's link> --notes "bob" --no-alert`.
  `ical add` prints no JSON: read the new block's `id` back with `ical list`. A worker started
  through `nbr-afk-implementation` is an AFK run: its block's notes add a line `afk`.
- A meeting Nik says runs past its end continues in a block with the meeting's title, from the
  meeting's end to the next run. Bob owns that block; the meeting itself stays as its organizer set
  it.
- Signals per piece of work, read without interrupting it: `ListAgents` busy or idle, `rex capture`
  output moving, dirty files in `lager status --json`, commits, reports, merges, Nik's messages.
- Each check-in brings the blocks in line with the signals. Running work stretches its block to the
  next run (`ical update --id <id> -e <end>`); new work starts a block at its first signal; finished
  work ends its block at its last signal; the next planned block moves when the running one pushes
  it.
- Nik hears about a stretch that would run into a meeting, and about a planned block whose start
  passed with no signal.
- The ledger `blocks/YYYY-MM-DD.json` in the circle's `bob/` folder holds each block Bob created:
  event `id`, link, `afk`, and the title, start and end Bob last wrote. Bob touches only blocks in
  the ledger. A title, start or end in the calendar that differs from the ledger's means Nik changed
  the block: it stands, and work that runs past its end continues in a new block. The circle skill
  names fields its calendar changes on its own; they are no signal.

The ledger is a JSON array with one entry per block, its times in ISO 8601 with the zone:

```json
[
  {
    "id": "<event id from ical list>",
    "title": "PROJ-42 Add search",
    "link": "https://example.com/PROJ-42",
    "afk": false,
    "start": "2026-11-26T09:30:00+01:00",
    "end": "2026-11-26T11:00:00+01:00"
  }
]
```
