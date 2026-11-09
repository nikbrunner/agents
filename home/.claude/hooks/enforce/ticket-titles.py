#!/usr/bin/env python3
"""Stop hook: block a reply that names a Jira ticket by its bare key.

A key counts as titled when a space and a title follow it ("CP-244 Sign-in page",
"CP-244 (sign-in page)") or when it sits in a link whose text carries the title.
Code spans, code blocks and URLs are not checked.
"""
import json
import re
import sys

PROJECTS = ("WEBSDK", "CP", "LABELS", "LS", "AS")
KEY = re.compile(r"(?<![\w/.\[-])(" + "|".join(PROJECTS) + r")-\d+(?![\w-])")
TITLED = re.compile(r"(?:\s+[A-Z`\[(\"“]|,\s*[\"“]|:\s+[A-Z])")


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
    for match in KEY.finditer(text):
        if not TITLED.match(text, match.end()):
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
            "reason": "Bare ticket key in the reply: " + ", ".join(keys)
            + ". Give each ticket its title, e.g. \"CP-244 Sign-in page\", and send the reply again.",
        }))


if __name__ == "__main__":
    main()
