#!/bin/sh
# Read-only summary of the Music.app library: genres, artists, decades, loved tracks.
set -e
rows_file=$(mktemp)
trap 'rm -f "$rows_file"' EXIT
osascript > "$rows_file" <<'EOF'
tell application "Music"
  set p to library playlist 1
  set a to artist of every track of p
  set g to genre of every track of p
  set y to year of every track of p
  set c to played count of every track of p
  set f to favorited of every track of p
end tell
set out to {}
repeat with i from 1 to count of a
  set end of out to (item i of a) & tab & (item i of g) & tab & (item i of y) & tab & (item i of c) & tab & (item i of f)
end repeat
set AppleScript's text item delimiters to linefeed
return out as text
EOF
echo "== genres: plays, tracks"
awk -F'\t' '{n[$2]++; p[$2]+=$4} END{for(k in n) printf "%d\t%d\t%s\n",p[k],n[k],k}' "$rows_file" | sort -nr | head -20
echo "== artists: plays, tracks"
awk -F'\t' '{n[$1]++; p[$1]+=$4} END{for(k in n) printf "%d\t%d\t%s\n",p[k],n[k],k}' "$rows_file" | sort -nr | head -40
echo "== decades: tracks, plays"
awk -F'\t' '$3>0{d=int($3/10)*10; n[d]++; p[d]+=$4} END{for(k in n) printf "%s\t%d\t%d\n",k,n[k],p[k]}' "$rows_file" | sort
echo "== loved"
awk -F'\t' '$5=="true"{n[$1]++} END{for(k in n) printf "%d\t%s\n",n[k],k}' "$rows_file" | sort -nr | head -30
