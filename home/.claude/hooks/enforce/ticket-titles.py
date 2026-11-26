#!/usr/bin/env python3
"""Stop hook: block a reply that names a Jira ticket or a PR/issue number bare.

A Jira key or a `#123` number counts as titled when a space and a title follow it
("PROJ-42 Add search", "shop-web #32 (corner radius)") or when it sits in a link whose
text carries the title. A number also counts as titled when a conventional-commit
title follows it ("lazyjira #43 chore(main): release 0.15.1").
Code spans, code blocks and URLs are not checked.

Jira project keys come from ~/.config/agents/ticket-projects, one key per line.
Without that file, only `#123` numbers are checked.
"""
import json
import os
import re
import sys

PROJECTS_FILE = os.path.expanduser("~/.config/agents/ticket-projects")


def load_key_pattern():
    try:
        with open(PROJECTS_FILE) as f:
            projects = [line.strip() for line in f if line.strip()]
    except OSError:
        return None
    if not projects:
        return None
    return re.compile(
        r"(?<![\w/.\[-])(" + "|".join(map(re.escape, projects)) + r")-\d+(?![\w-])"
    )


KEY = load_key_pattern()
NUMBER = re.compile(r"(?<![\w/.\[&#-])#\d+(?![\w-])")
TITLED = re.compile(r"(?:\s+[A-Z`\[(\"“]|,\s*[\"“]|:\s+[A-Z])")
COMMIT_TITLED = re.compile(r"\s+[a-z]+(?:\([^)\n]*\))?!?:\s")


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


def bare_keys(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"\]\([^)]*\)", "]", text)
    text = re.sub(r"https?://\S+", " ", text)
    found = []
    for match in KEY.finditer(text) if KEY else ():
        if not TITLED.match(text, match.end()):
            found.append(match.group(0))
    for match in NUMBER.finditer(text):
        end = match.end()
        if not (TITLED.match(text, end) or COMMIT_TITLED.match(text, end)):
            found.append(match.group(0))
    return sorted(set(found))


def main():
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active"):
        return
    path = payload.get("transcript_path")
    if not path:
        return
    keys = bare_keys(last_reply(path))
    if keys:
        print(json.dumps({
            "decision": "block",
            "reason": "Bare ticket key or PR/issue number in the reply: " + ", ".join(keys)
            + ". Give each its title, e.g. \"PROJ-42 Add search\" or \"shop-web #32 Components follow"
            " the global corner radius\", and send the reply again.",
        }))


if __name__ == "__main__":
    main()
