on run argv
  tell application "Music"
    if (count of argv) > 0 then
      set p to playlist (item 1 of argv)
    else
      set p to library playlist 1
    end if
    set colTitle to name of every track of p
    set colArtist to artist of every track of p
    set colPlays to played count of every track of p
    set colLast to played date of every track of p
    set colAdded to date added of every track of p
    set colAlbum to album of every track of p
  end tell
  set rows to {}
  repeat with i from 1 to count of colTitle
    set end of rows to (item i of colTitle) & tab & (item i of colArtist) & tab & (item i of colPlays) & tab & ((item i of colLast) as text) & tab & ((item i of colAdded) as text) & tab & (item i of colAlbum)
  end repeat
  set AppleScript's text item delimiters to linefeed
  return rows as text
end run
