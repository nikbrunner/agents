# Copy black-atom-default-{dark,light}.json from this folder into ~/.claude/themes before recording.
Output frames/
Set Shell zsh
Set FontSize 20
Set Width 1400
Set Height 1080
Set Framerate 10
Set TypingSpeed 40ms

Hide
Type `cd "$REPO" && env -u CLAUDE_CODE_PLUGIN_DIRS -u CLAUDE_CODE_CHILD_SESSION claude --model haiku --settings "docs/assets/tapes/claude-$CLIP_SCHEME.json"`
Enter
Sleep 8s
Show

Sleep 2s
Type "Spawn three general-purpose subagents in parallel for mods, statusline and scripts. Each works through four steps with sleep 6 between them: list the folder, count its lines, read one file, report one line."
Sleep 500ms
Enter
Sleep 55s
