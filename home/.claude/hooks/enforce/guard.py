#!/usr/bin/env python3
"""PreToolUse hook: hold Bash and AskUserQuestion calls to the hard rules of AGENTS.md and
nbr-git-commit.

Bash commands are split into segments on `&&`, `||`, `;`, `|`, `&`, parentheses and newlines.
Heredoc bodies are dropped first, and quoted strings stay single tokens, so a commit message that
mentions a command never matches. A command that does not tokenize whole is checked line by line,
with `#` comments dropped. Deny wins over ask across segments. Any error lets the call through
without output.
"""
import json
import os
import re
import shlex
import sys

HUNKS = "~/.agents/skills/nbr-git-commit/scripts/hunks.py"
TMP = ("/tmp/", "/private/tmp/", "/var/folders/")
HEREDOC = re.compile(
    r"(?<!<)<<-?(?!<)\s*(['\"]?)([^\s'\"<>|;&()]+)\1([^\n]*)\n.*?\n[ \t]*\2[ \t]*(?=\n|$)", re.S)
PREFIX = {"env", "sudo", "time", "command", "nohup", "exec", "xargs"}
PREFIX_ARGS = {"-I", "-n", "-L", "-P", "-d", "-E", "-s", "-u"}
BULK = re.compile(r"\.{1,2}/?|\.{0,2}/?\*|:/?|:\(.*")
INPLACE = re.compile(r"-[a-zA-Z0-9]*i|--in-place")
SCRIPT = {"sed": ("-e", "-f", "--expression", "--file"), "perl": ("-e", "-E")}
ARGS = {"sed": ("-l",), "perl": ("-M", "-m", "-I")}

EDIT = "Change files with Edit or Write, never sed -i or perl -i (temp files under /tmp excepted)."
STAGE = ("Stage by name (git add path/a path/b), or by hunk with nbr-git-commit's hunks.py ("
         + HUNKS + "). Never git add -A, ., *, :/ or -u, and never git commit -a or with ., * or :/ as its path.")
WORKTREE = "lager creates worktrees: run `lager worktree add <repo> <name>`, never git worktree add."
FORCE = "Force push. Confirm?"
NO_VERIFY = "--no-verify skips the git hooks. Confirm?"
ONE_QUESTION = ("Ask one question, then wait for the answer. Facets of one decision go into one"
                " question's options; the next question comes after the answer.")


def segments(command, comments=False):
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()<>\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    lex.commenters = "#" if comments else ""
    current = []
    for token in lex:
        if token and all(c in ";&|()<>\n" for c in token) and not set(token) & set("<>"):
            if current:
                yield current
            current = []
        else:
            current.append(token)
    if current:
        yield current


def all_segments(command):
    command = HEREDOC.sub(lambda m: m.group(3), command).replace("\\\n", " ")
    try:
        return list(segments(command))
    except ValueError:
        found = []
        for line in command.splitlines():
            try:
                found += segments(line, comments=True)
            except ValueError:
                pass
        return found


def strip(words):
    in_prefix, skip = False, False
    while words:
        word = words[0]
        if skip:
            skip = False
        elif word in PREFIX:
            in_prefix = True
        elif re.match(r"\w+=", word):
            pass
        elif in_prefix and word.startswith("-"):
            skip = word in PREFIX_ARGS
        else:
            break
        words = words[1:]
    return words


def commands(words):
    yield strip(words)
    for i, word in enumerate(words):
        if word in ("-exec", "-execdir"):
            yield strip(words[i + 1:])


def short(arg, letter):
    return re.fullmatch(r"-[a-zA-Z]+", arg) is not None and letter in arg


def edits_outside_tmp(name, args):
    targets, script_given, skip = [], False, False
    for arg in args:
        if skip:
            skip = False
        elif arg in SCRIPT[name] or arg in ARGS[name]:
            script_given = script_given or arg in SCRIPT[name]
            skip = True
        elif arg.startswith("-") or arg == "":
            script_given = script_given or arg.startswith(("--expression=", "--file="))
        else:
            targets.append(arg)
    if not script_given:
        targets = targets[1:]
    paths = [os.path.expanduser(os.path.expandvars(t)) for t in targets]
    return not paths or not all(p.startswith(TMP) for p in paths)


def check_edit(words):
    name = os.path.basename(words[0]) if words else ""
    name = "sed" if name == "gsed" else name
    if name not in SCRIPT:
        return None
    args = words[1:]
    options = [a for a in args if not (name == "perl" and a.startswith(("-M", "-m", "-I")))]
    if any(INPLACE.match(a) for a in options) and edits_outside_tmp(name, args):
        return "deny", EDIT
    return None


def check_git(words):
    if not words or os.path.basename(words[0]) != "git":
        return None
    words = words[1:]
    while words and words[0].startswith("-"):
        words = words[2:] if words[0] in ("-C", "-c", "--git-dir", "--work-tree") else words[1:]
    if not words:
        return None
    sub, args = words[0], words[1:]
    if sub == "add" and any(BULK.fullmatch(a) or a in ("--all", "--update") or short(a, "A") or short(a, "u")
                            for a in args):
        return "deny", STAGE
    if sub == "commit":
        positional, skip = [], False
        for arg in args:
            if skip:
                skip = False
            elif re.fullmatch(r"-[a-zA-Z]+", arg) and arg[-1] in "mFCc":
                skip = True
            elif not arg.startswith("-"):
                positional.append(arg)
        if "--all" in args or any(short(a, "a") for a in args) or any(BULK.fullmatch(p) for p in positional):
            return "deny", STAGE
    if sub == "worktree" and args[:1] == ["add"]:
        return "deny", WORKTREE
    if sub == "push" and any(a.startswith(("--force", "+")) or short(a, "f") for a in args):
        return "ask", FORCE
    if sub in ("commit", "push") and ("--no-verify" in args or (sub == "commit" and any(short(a, "n") for a in args))):
        return "ask", NO_VERIFY
    return None


def decide(payload):
    tool, data = payload.get("tool_name"), payload.get("tool_input") or {}
    if tool == "AskUserQuestion":
        return ("deny", ONE_QUESTION) if len(data.get("questions") or []) > 1 else None
    if tool != "Bash":
        return None
    found = [d for words in all_segments(data.get("command") or "") for command in commands(words)
             for d in (check_edit(command), check_git(command)) if d]
    deny = [d for d in found if d[0] == "deny"]
    return (deny or found or [None])[0]


def main():
    result = decide(json.load(sys.stdin))
    if result:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": result[0],
            "permissionDecisionReason": result[1],
        }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
