# Time blocks

A circle with a block calendar keeps the day's work in it as events. A block ahead of now is the
plan. A block behind now is the record. The plan reaches one or two blocks ahead. Agents' work
counts too, so parallel work shows as overlapping blocks.

## Creating a block

One block is one piece of work: a todo, a ticket or a PR. Its title is the todo as the note writes
it. Create it with:

```sh
ical add "<title>" -c <block calendar> -s <start> -e <end> --url <the todo's link> --notes "bob" --no-alert
```

`ical add` prints no JSON. Read the new block's `id` back with `ical list`, and write it to the
ledger. A worker started through `nbr-afk-implementation` is an AFK run: its block's notes add a
line `afk`.

Nik may say a meeting runs past its end. Continue it in a block with the meeting's title, from the
meeting's end to the next check-in. Bob owns that block. The meeting itself stays as its
organizer set it.

## Keeping the blocks in line

Read the signals of each piece of work without interrupting it:

- `ListAgents`: busy or idle.
- `rex capture`: output moving.
- `lager status --json`: dirty files.
- Commits, reports, merges and Nik's messages.

Then bring the blocks in line with the signals:

1. Stretch the block of running work to the next check-in: `ical update --id <id> -e <end>`.
2. Start a block for new work at its first signal.
3. End the block of finished work at its last signal.
4. Move the next planned block when the running one pushes it.

Tell Nik about a stretch that would run into a meeting. Tell him also about a planned block whose
start passed with no signal.

## The ledger

The ledger `blocks/YYYY-MM-DD.json` in the circle's `bob/` folder holds each block Bob created: the
event `id`, the link, `afk`, and the title, start and end Bob last wrote. Bob changes only blocks in
the ledger. The file is a JSON array with one entry per block, its times in ISO 8601 with the zone:

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

Compare the title, start and end with the calendar's. A difference means Nik changed the block, and
his change stands. Work that runs past the end he set continues in a new block. The circle skill
names fields its calendar changes on its own; they are no signal.
