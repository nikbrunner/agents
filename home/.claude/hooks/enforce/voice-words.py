#!/usr/bin/env python3
"""Stop hook: send a reply back when nbr-voice's linter has a hard finding in it.

The linter is the skill's scripts/lint.py with its references/rules.toml, run with scope reply.
Advisory findings ride along only when a hard one blocks. Any error (no uv, a bad rules file, a
crash, a timeout) lets the reply through without output.
"""
import json
import os
import subprocess
import sys

LINT = os.path.expanduser("~/.agents/skills/nbr-voice/scripts/lint.py")


def lint(text, scopes):
    command = ["uv", "run", "--quiet", "--script", LINT, "--json"]
    for scope in scopes:
        command += ["--scope", scope]
    result = subprocess.run(command, input=text.encode("utf-8"), capture_output=True, timeout=5)
    if result.returncode not in (0, 1):
        return []
    return json.loads(result.stdout.decode("utf-8"))


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


def listed(findings, limit=10):
    text = "; ".join("{} → {}".format(f["match"], f["use"]) for f in findings[:limit])
    return text + ("; and {} more".format(len(findings) - limit) if len(findings) > limit else "")


def main():
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active") or not os.path.exists(LINT):
        return
    reply = payload.get("last_assistant_message")
    if reply is None and payload.get("transcript_path"):
        reply = last_reply(payload["transcript_path"])
    if not reply:
        return
    findings = lint(reply, ["reply"])
    hard = [f for f in findings if f["severity"] == "hard"]
    if not hard:
        return
    reason = (
        "Voice findings in the reply (nbr-voice): " + listed(hard)
        + ". Rewrite those sentences in plain words and send the reply again. A phrase you"
        " discuss rather than use goes in backticks."
    )
    advisory = [f for f in findings if f["severity"] != "hard"]
    if advisory:
        reason += " Also worth a look while you rewrite: " + listed(advisory) + "."
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
