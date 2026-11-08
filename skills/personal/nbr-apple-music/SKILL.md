---
name: nbr-apple-music
description: Curate, clean up and organize Nik's Apple Music through the apple-music MCP. Use when asked to build or refine a playlist, retire stale playlists or tracks, or sort playlists into folders.
compatibility: macOS with Music.app, and the apple-music MCP at --level api.
---

# Apple Music

Every write goes through the `apple-music` MCP, apart from cover art and playlist descriptions, which it has no tool for. Its tool descriptions cover parameters; this skill covers the order of work and what they leave out.

## Curate a playlist

1. **Brief.** Pin down mood, occasion, length and hard exclusions. Read taste from `discover(action="heavy_rotation")`, `library(action="recently_played")` and any playlist Nik names, and look in `playlist(action="folders")` for a playlist already on the topic.
2. **Propose.** Pick a shape from [Playlist shapes](#playlist-shapes) and show the tracklist in listening order, each as title and artist. Revise until Nik approves it. Build a label or discography brief from evidence: album `copyright` in `https://itunes.apple.com/search?entity=album&country=de&limit=200&term=ARTIST` names the label, and `https://itunes.apple.com/lookup?entity=song&country=de&limit=200&id=ALBUM_IDS` returns catalog ids, albums and runtimes.
3. **Resolve.** Run `catalog(action="resolve")` on the approved list, 25 tracks per call, unless the ids came from that lookup. Show Nik any match that differs from the proposal, and keep each track's catalog id and album.
4. **Pin.** `library(action="add", track=["id", ...])` puts the exact editions in the library. A track taken from another playlist can be missing from the library, so pin those too. Continue once the play-history script below shows every title and album pair, usually within a minute.
5. **Write.** Create the playlist, retrying the first add if it reports the playlist is not found yet. Adds append, so send them in listening order, always with `auto_add=False` so a miss fails visibly.
   - A track that collides gets its own call with top-level `track`, `artist` and `album`. It collides when the play-history output holds the same artist with that title on another album or inside a longer title, as `Circles (Mixed)` does for `Circles`.
   - Add `allow_duplicates=True` to that call when the playlist already holds a longer title containing this one. The duplicate check matches substrings, so `Pk` is skipped once `Pk_Amb` is in.
   - Runs of other tracks go as one JSON array of `{"name", "artist"}` objects. An `album` key inside an object is ignored.
   - `auto_add=True` takes the top catalog hit, which can be a remix or another track from the same EP, and adds that wrong track to the library. `dry_run` uses a stricter matcher than the write, so a clean preview cannot rule this out. `playlist(action="add")` refuses catalog ids without a developer token.
6. **Verify.** Done when `playlist(action="tracks")` shows every approved track, in order, with the approved album and runtime. The add response alone proves nothing. That read comes from the cloud and lags after a large remove, so when it disagrees with the play-history script, trust the script. Report each one that failed to land.

To change one track, use `add` with `replace`: the old track goes only after the new one has persisted, and the new one lands at the end. To keep a position, remove everything from that slot on and re-add it in order. Re-sequencing a whole playlist means removing every track from it and re-adding them in the new order.

### Playlist shapes

**Chronological**, for an era, artist or label. The order tells the history.

- Scope it from the catalog lookup in step 2, so the list covers what exists.
- Select by quota per release, so every release is represented: 1 track from a single, 2 from an EP, 4 from an album. Give compilations a higher quota.
- Leave out skits under 3 minutes, a cappellas, and the same title and artist on a second release.
- Order by the album's release date, then track number. Track-level dates can carry the original year of a reissue.

**DJ set**, for a long programmed listen. The order follows energy.

- Music.app holds no tempo or key data for streamed tracks, so sequence from knowledge of the records and tell Nik it is programmed rather than beatmatched.
- Ask how the intro should feel. Then run an arc: Intro, Rising, Groove, Build, Peak, Dark hours, Close. Peak is the longest phase, at about a quarter of the runtime.
- Nik's default intro is dark, moody ambient that slowly builds. The Close mirrors the Intro, ideally with related material.
- Keep the same artist from playing back to back, apart from deliberate runs in the Intro and Close. Spread versions of one tune across phases.
- Add a track when a phase lacks material or a transition needs a bridge, and report what was added.

Re-sequencing can make a playlist's description untrue, so update it along with the order.

### Cover art and description

Make covers with `nbr-images`, always with `aspect_ratio` `"1:1"`: on `"auto"` a 4K finish can come back portrait. Apply a square JPEG of about 3000 pixels through Music.app:

```applescript
set imgData to read (POSIX file "/path/cover.jpg") as «class JPEG»
tell application "Music"
  set p to first user playlist whose persistent ID is "ID"
  try
    set data of artwork 1 of p to imgData
  end try
  try
    make new artwork at p with properties {data:imgData}
  end try
end tell
```

Done when Nik sees the cover in Music. Both commands can return errors and `count of artworks` can stay 0 even when the cover lands, so neither says whether it worked.

Set the description with `set description of p to "..."` and read it back.

## Clean up

`delete` and library `remove` are irreversible, run without a confirmation step, and sync to every device through iCloud. Each one runs from a list Nik approved in this conversation, naming the exact playlist or track.

1. **Inventory.** `playlist(action="list", format="json", full=True, limit=0)` and `playlist(action="folders")`. Leave `smart: true` playlists alone: that covers rule-based playlists and system ones like Music and Favourite Songs. The field appears only with `full=True`.
2. **Gather evidence.** The MCP returns no play history per track, so read it from Music.app:

   ```sh
   osascript ~/.claude/skills/nbr-apple-music/play-history.applescript "PLAYLIST"
   ```

   Leave off the name for the whole library, which takes a few seconds.

   One tab-separated row per track: title, artist, plays, last played, date added, album. This query stays read-only; writes belong to the MCP. `missing value` means no date is recorded, and it shows up in the date-added column too. Play counts only cover what Music.app has recorded, so a zero on a recently added track says little.

3. **Propose.** A table with one row per candidate: the item, the evidence, and the action. Pick the mildest action that does the job: remove from playlist, then delete the playlist, then remove from library. Wait for Nik's approval of the table.
4. **Back up.** Save the play-history output for the whole library to `~/Music/applemusic-backups/library-YYYYMMDD.tsv` as the baseline. `library(action="snapshot")` times out on this library. For each playlist about to be deleted or thinned, run `playlist(action="tracks", playlist="NAME", limit=0, format="none", export="csv")`. The exports land in `~/.cache/applemusic-mcp`, where a cache clear wipes them, and they are the only undo for a delete. Copy them to `~/Music/applemusic-backups/` first.
5. **Apply** in the approved order, naming title and artist on every track removal. A partial title match that hits several tracks must end in Nik choosing one.
6. **Verify.** Run the script again and diff columns 1, 2 and 6 against the baseline, since plays and dates drift. Done when that diff and `config(action="audit-log")` match the approved table exactly. Report any difference.

## Organize

Folders live outside `playlist(action="list")`, so read `playlist(action="folders")` first. Propose the target tree, get approval, then create and move. Done when `folders` matches the approved tree.

## When results look wrong

- **Empty results during bulk work can be a throttle.** The web-player token allows a few hundred requests an hour and a `429` can surface as an empty search. Treat empty as unknown and stop for about an hour, because retries extend the block. For large jobs, suggest `applemusic-mcp login --dev`.
- **Catalog actions start failing:** Nik re-runs `applemusic-mcp login`.
- **"Silently reverted":** a Music.app bug on some playlists. Quit and reopen Music.app, then retry once.
- **Tool needs a higher level:** say which feature needs it. The level is set in Nik's MCP config.
