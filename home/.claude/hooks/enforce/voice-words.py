#!/usr/bin/env python3
"""Stop hook: block a reply that uses a word from nbr-voice's forbidden list.

The list is the table under "## Forbidden" in the skill's references/words.md. Words match
whole and case-insensitive. Code spans, code blocks, URLs and paths are not checked; a fenced
markdown block is, since that is where drafts go.
"""
import json
import os
import re
import sys

WORDS = os.path.expanduser("~/.agents/skills/nbr-voice/references/words.md")


def forbidden():
    entries = []
    section = False
    with open(WORDS) as f:
        for line in f:
            if line.startswith("## "):
                section = line.strip() == "## Forbidden"
                continue
            if not section or not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 2 or cells[0] == "Forms" or set(cells[0]) <= set("-: "):
                continue
            for form in cells[0].split(","):
                words = form.strip().split()
                if words:
                    pattern = r"(?<!\w)" + r"\s+".join(map(re.escape, words)) + r"(?!\w)"
                    entries.append((form.strip(), cells[1], re.compile(pattern, re.I)))
    return entries


def last_reply(transcript_path):
    texts = []
    with open(transcript_path) as f:
        lines = f.readlines()
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        kind = entry.get("type")
        if kind == "user":
            content = entry.get("message", {}).get("content")
            if isinstance(content, str) or any(
                block.get("type") == "text" for block in content or [] if isinstance(block, dict)
            ):
                break
            continue
        if kind != "assistant":
            continue
        for block in entry.get("message", {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
    return "\n".join(reversed(texts))


def prose(text):
    text = re.sub(
        r"```(\w*)[^\n]*\n(.*?)```",
        lambda m: m.group(2) if m.group(1).lower() in ("markdown", "md") else " ",
        text,
        flags=re.S,
    )
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"\]\([^)]*\)", "]", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\S*/\S+", " ", text)
    return text.replace("’", "'")


def main():
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active") or not os.path.exists(WORDS):
        return
    reply = payload.get("last_assistant_message")
    if reply is None and payload.get("transcript_path"):
        reply = last_reply(payload["transcript_path"])
    text = prose(reply or "")
    found = [f"{form} → {use}" for form, use, pattern in forbidden() if pattern.search(text)]
    if found:
        print(json.dumps({
            "decision": "block",
            "reason": "Forbidden words in the reply (nbr-voice): " + "; ".join(found)
            + ". Rewrite those sentences in plain words and send the reply again. A word you"
            " discuss rather than use goes in backticks.",
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
