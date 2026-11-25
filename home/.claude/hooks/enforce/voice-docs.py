#!/usr/bin/env python3
"""PostToolUse hook on Write, Edit and MultiEdit: lint the Markdown just written with nbr-voice.

Only .md and .mdx files count, and only the text the tool wrote (Write content, Edit new_string,
each MultiEdit new_string). The linter reads the whole file so code fences keep their context, and
it skips the paths in the [ignore] list of the skill's rules.toml. Scope is document, plus procedure
for agent instructions: SKILL.md, AGENTS.md, CLAUDE.md, HOW_TO_TEST.md, or any file under a skills/
folder. Hard findings block, so the agent fixes them in a follow-up edit; advisory ones return as
context. Any error (no uv, a bad rules file, a crash, a timeout) exits quietly.
"""
import json
import os
import subprocess
import sys

LINT = os.path.expanduser("~/.agents/skills/nbr-voice/scripts/lint.py")
PROCEDURE_FILES = {"SKILL.md", "AGENTS.md", "CLAUDE.md", "HOW_TO_TEST.md"}


def written(tool_input):
    if "content" in tool_input:
        return [tool_input["content"]]
    if "new_string" in tool_input:
        return [tool_input["new_string"]]
    return [edit.get("new_string", "") for edit in tool_input.get("edits") or []]


def scopes(path):
    parts = os.path.normpath(path).split(os.sep)
    procedure = parts[-1] in PROCEDURE_FILES or "skills" in parts[:-1]
    return ["document", "procedure"] if procedure else ["document"]


def lint(path, fragments):
    command = ["uv", "run", "--quiet", "--script", LINT, "--json", "--fragments", "--path", path]
    for scope in scopes(path):
        command += ["--scope", scope]
    stdin = json.dumps(fragments).encode("utf-8")
    result = subprocess.run(command, input=stdin, capture_output=True, timeout=5)
    if result.returncode not in (0, 1):
        return []
    return json.loads(result.stdout.decode("utf-8"))


def listed(findings, limit=10):
    text = "; ".join(
        'line {}: "{}" → {}'.format(f["line"], f["match"], f["use"]) for f in findings[:limit]
    )
    return text + ("; and {} more".format(len(findings) - limit) if len(findings) > limit else "")


def main():
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or ""
    if not path.endswith((".md", ".mdx")) or not os.path.exists(LINT):
        return
    fragments = [text for text in written(tool_input) if text and text.strip()]
    if not fragments:
        return
    findings = lint(path, fragments)
    hard = [f for f in findings if f["severity"] == "hard"]
    advisory = [f for f in findings if f["severity"] != "hard"]
    name = os.path.basename(path)
    if hard:
        reason = (
            "Voice findings in the text just written to {} (nbr-voice): {}. Fix them with a"
            " follow-up edit. A phrase you discuss rather than use goes in backticks.".format(
                name, listed(hard)
            )
        )
        if advisory:
            reason += " Also worth a look: " + listed(advisory) + "."
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    elif advisory:
        context = "Voice advisories for {} (nbr-voice), fix where it reads better: {}.".format(
            name, listed(advisory)
        )
        print(json.dumps({
            "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context},
        }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
