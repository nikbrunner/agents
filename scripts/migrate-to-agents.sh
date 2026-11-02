#!/usr/bin/env bash
# One-time move of the agent config from dots to nikbrunner/agents, once per machine.
# Run after nikbrunner/skills is renamed to nikbrunner/agents on GitHub and both
# agents-repo branches are merged, with dots still on its pre-merge commit, and with
# Claude Code and Pi closed. The work skills link only where the work repo exists.
set -euo pipefail

repos="$HOME/repos/nikbrunner"
dots="$repos/dots"
agents="$repos/agents"
work="$HOME/repos/imfusion/brunner/agents"
moved_paths=(common/.pi common/.agents common/.claude common/.codex common/.config/opencode common/.config/rpiv-advisor)

step() { printf '\n==> %s\n' "$*"; }

[[ -z $(git -C "$dots" diff --name-only --diff-filter=M HEAD -- "${moved_paths[@]}") ]] || {
    echo "dots has uncommitted changes in the paths that move; commit or stash them first" >&2
    git -C "$dots" diff --name-only --diff-filter=M HEAD -- "${moved_paths[@]}" >&2
    exit 1
}

[[ -f "$dots/common/.claude/settings.json" ]] || {
    echo "dots is already on the new commit; pull happened too early" >&2
    exit 1
}

git -C "$dots" fetch origin
overlap=$(comm -12 <(git -C "$dots" diff --name-only --diff-filter=AM HEAD | sort) <(git -C "$dots" diff --name-only HEAD origin/main | sort))
[[ -z $overlap ]] || {
    printf 'these uncommitted dots files would collide with the pull; commit or stash them first:\n%s\n' "$overlap" >&2
    exit 1
}

step "Renaming the skills clone to agents and pulling"
if [[ -d "$repos/skills" && ! -e "$agents" ]]; then
    mv "$repos/skills" "$agents"
fi
git -C "$agents" remote set-url origin git@github.com:nikbrunner/agents.git
git -C "$agents" fetch origin
git -C "$agents" checkout main
git -C "$agents" pull --ff-only

if [[ -L "$HOME/.pi" && -d "$dots/common/.pi" ]]; then
    step "Making ~/.pi a real folder with Pi's state in it"
    # One rename. The tracked files then go, since the linker links them from agents.
    rm "$HOME/.pi"
    mv "$dots/common/.pi" "$HOME/.pi"
    while IFS= read -r -d '' path; do
        rm -f "$HOME/.pi/${path#common/.pi/}"
    done < <(git -C "$dots" ls-files -z -- common/.pi)
    if [[ -d "$HOME/.pi/agent/extensions/node_modules" ]]; then
        mv "$HOME/.pi/agent/extensions/node_modules" "$agents/home/.pi/agent/extensions/node_modules"
    fi
    find "$HOME/.pi/agent/extensions" "$HOME/.pi/agent/git" -depth -type d -empty -delete 2>/dev/null || true
    ls -a "$HOME/.pi/agent"
fi

step "Moving what's left of untracked state from dots into agents/home"
# Skill links and the mods' generated types are removed: install.sh and Claude
# Code recreate them.
moved=0
while IFS= read -r -d '' path; do
    if [[ $path == common/.claude/mods/* ]] || [[ -L "$dots/$path" && $path == common/.agents/skills/* ]]; then
        rm -f "$dots/$path"
        continue
    fi
    dest="$agents/home/${path#common/}"
    if [[ -e "$dest" ]]; then
        echo "skipped $path: $dest exists"
        continue
    fi
    mkdir -p "$(dirname "$dest")"
    mv "$dots/$path" "$dest"
    moved=$((moved + 1))
    if ((moved % 5000 == 0)); then echo "$moved..."; fi
done < <(
    cd "$dots"
    {
        git ls-files -z --others -- common/.agents common/.claude
        git ls-files -z --others --ignored --exclude-standard -- common/.agents common/.claude
    } | sort -zu
)
echo "$moved file(s) moved"

step "Pulling dots"
git -C "$dots" merge --ff-only origin/main
rm -rf "$dots/common/.claude/mods"
find "$dots/common/.agents" "$dots/common/.claude" -depth -type d -empty -delete 2>/dev/null || true

step "Linking"
DOTS_DIR="$dots" AGENTS_DIR="$agents" "$dots/common/.local/bin/dots" link
"$agents/install.sh"

if [[ -x $work/install.sh ]]; then
    step "Linking the work skills"
    "$work/install.sh"
fi

step "Removing the subagent status line's old links"
rm -f "$HOME/.local/bin/claude-subagent-statusline"
rm -rf "$HOME/.claude/hooks/subagent-progress"

step "Checking"
for link in ~/.pi/agent/settings.json ~/.pi/agent/extensions ~/.agents ~/.claude/settings.json ~/.claude/CLAUDE.md ~/.claude-work/settings.json ~/.codex/config.toml; do
    printf '%-32s -> %s\n' "$link" "$(readlink "$link")"
done
echo
echo "Left in dots (should be nothing):"
find "$dots/common/.agents" "$dots/common/.claude" -not -type d 2>/dev/null | head -20 || true
echo
echo "agents status (should be clean):"
git -C "$agents" status --short | head -20
