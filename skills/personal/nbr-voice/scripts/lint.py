#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Lint prose against a rules file of words, patterns and synonym groups.

Text comes from stdin or from file paths. Each entry in the rules file runs when one of its scopes
is active (--scope, repeatable, default document). Code, URLs, paths, front matter and table rules
are masked before any match. Exit status 1 means a hard finding.

With --fragments, stdin is a JSON list of strings just written into the file named by --path: the
whole file is linted, so code fences keep their context, and only findings inside those strings
are reported.
"""
import argparse
import fnmatch
import json
import os
import re
import sys
import tomllib
from pathlib import Path

SCOPES = ("reply", "document", "procedure")
DEFAULT_RULES = Path(__file__).resolve().parent.parent / "references" / "rules.toml"
KEPT_FENCES = ("markdown", "md")


def blank(text):
    return re.sub(r"[^\n]", " ", text)


def mask_fences(text):
    out, stack = [], []
    for line in text.splitlines(keepends=True):
        if stack:
            fence = stack[-1][0]
            if re.fullmatch(r" {0,3}%s{%d,}\s*" % (re.escape(fence[0]), len(fence)), line):
                stack.pop()
                out.append(blank(line))
                continue
        opening = re.match(r" {0,3}(`{3,}|~{3,})\s*([\w+-]*)", line)
        if opening and all(keep for _, keep in stack):
            stack.append((opening.group(1), opening.group(2).lower() in KEPT_FENCES))
            out.append(blank(line))
            continue
        out.append(line if all(keep for _, keep in stack) else blank(line))
    return "".join(out)


MASKS = [
    # inline code, which may wrap a single line but never cross a blank line
    re.compile(r"``(?:[^\n]|\n(?![ \t]*\n))*?``|`(?:[^`\n]|\n(?![ \t]*\n))+?`"),
    re.compile(r"\]\([^)\n]*\)"),  # link targets
    re.compile(r"^\s*\[[^\]\n]+\]:\s*\S+.*$", re.M),  # reference link definitions
    re.compile(r"https?://\S+|<[a-z]+:[^>\s]+>"),  # URLs
    re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$", re.M),  # table separators
    re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$", re.M),  # horizontal rules
    re.compile(r"(?<=\|)\s*[—–-]\s*(?=\|)"),  # dash-only table cells
    re.compile(r"\d\s?[—–-]\s?\d"),  # numeric ranges
]
SLASH_TOKEN = re.compile(r"(?<!\S)\S*/\S*")
# A path starts with /, ~, ./ or ../, or holds a file extension; and/or stays prose.
PATH_LIKE = re.compile(r"[(\[\"'<]*(?:~|\.{0,2}/)|.*/[^/]*\.\w")


def mask(text):
    """Blank everything that is not prose, keeping offsets and line numbers."""
    text = text.replace("’", "'").replace("‘", "'")
    front = re.match(r"---\n.*?\n---[ \t]*(?:\n|\Z)", text, re.S)
    if front:
        text = blank(front.group()) + text[front.end():]
    text = mask_fences(text)
    for pattern in MASKS:
        text = pattern.sub(lambda m: blank(m.group()), text)
    return SLASH_TOKEN.sub(lambda m: blank(m.group()) if PATH_LIKE.match(m.group()) else m.group(), text)


def phrase(form):
    return r"\s+".join(map(re.escape, form.split()))


def words_regex(forms):
    alternation = "|".join(phrase(f) for f in sorted(forms, key=len, reverse=True))
    return re.compile(r"(?<![^\W_])(?:%s)(?![^\W_])" % alternation, re.I)


def load_rules(path):
    with open(path, "rb") as f:
        data = tomllib.load(f)
    entries = []
    for entry in data.get("rule", []):
        if "forms" in entry:
            regex, name = words_regex(entry["forms"]), entry.get("name", entry["forms"][0])
        else:
            regex, name = re.compile(entry["pattern"], re.I | re.M), entry.get("name", entry["pattern"])
        entries.append({**entry, "kind": "rule", "name": name, "regex": regex})
    for entry in data.get("group", []):
        words = [[w] if isinstance(w, str) else w for w in entry["words"]]
        name = entry.get("name", "/".join(w[0] for w in words))
        regexes = [(w[0], words_regex(w)) for w in words]
        entries.append({**entry, "kind": "group", "name": name, "use": entry["note"], "regexes": regexes})
    return entries, data.get("checks", {}), data.get("ignore", {}).get("paths", [])


def ignored(path, globs):
    full = os.path.abspath(path)
    return any(fnmatch.fnmatch(full, g) or fnmatch.fnmatch(os.path.basename(full), g) for g in globs)


def applies(entry, scopes):
    return bool(set(entry.get("scope", SCOPES)) & scopes)


def units(text):
    """Paragraphs, list items and headings, as (offset, text); table rows are skipped."""
    buf, start, pos = [], 0, 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        marker = re.match(r"(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\|)", stripped)
        if (not stripped or marker) and buf:
            yield start, " ".join(buf)
            buf = []
        if stripped and not stripped.startswith("|"):
            if not buf:
                start = pos + len(line) - len(line.lstrip())
            buf.append(re.sub(r"^(?:#{1,6}|[-*+]|\d+[.)]|>)\s*", "", stripped))
        pos += len(line)
    if buf:
        yield start, " ".join(buf)


def sentences(unit):
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[\"'(\[*_]*[A-Z0-9])", unit) if s.strip()]


def words_in(sentence):
    return re.findall(r"[A-Za-z0-9][\w'-]*", sentence)


def snippet(sentence, count=6):
    words = sentence.split()
    return " ".join(words[:count]) + (" …" if len(words) > count else "")


def code_checks(masked, checks, scopes, keep):
    found = []
    length = checks.get("sentence_length")
    if length:
        limits = [n for s, n in length.get("max_words", {}).items() if s in scopes]
        limit = min(limits) if limits else None
    for start, unit in units(masked):
        if not keep(start):
            continue
        parts = sentences(unit)
        if length and limit and applies(length, scopes):
            for sentence in parts:
                count = len(words_in(sentence))
                if count > limit:
                    found.append((length, "sentence length", start, snippet(sentence),
                                  f"split it: {count} words, limit {limit}"))
        opening = checks.get("same_opening")
        if opening and applies(opening, scopes):
            run = opening.get("run", 3)
            firsts = [(words_in(s) or [""])[0].lower() for s in parts]
            for i in range(len(firsts) - run + 1):
                if firsts[i] and len(set(firsts[i:i + run])) == 1:
                    found.append((opening, "same opening", start, snippet(parts[i]),
                                  f"{run} sentences open with '{firsts[i]}': merge or change the subject"))
                    break
    return found


def lint(text, rules, scopes, spans=None):
    entries, checks, _ = rules
    scopes = set(scopes)
    masked = mask(text)

    def keep(pos):
        return spans is None or any(a <= pos < b for a, b in spans)

    raw = []
    for entry in entries:
        if not applies(entry, scopes):
            continue
        if entry["kind"] == "rule":
            for m in entry["regex"].finditer(masked):
                if keep(m.start()):
                    raw.append((entry, entry["name"], m.start(), m.group(), entry["use"]))
        else:
            hits = {}
            for word, regex in entry["regexes"]:
                m = next((m for m in regex.finditer(masked) if keep(m.start())), None)
                if m:
                    hits[word] = m.start()
            if len(hits) >= 2:
                raw.append((entry, entry["name"], min(hits.values()), ", ".join(hits), entry["use"]))
    raw += code_checks(masked, checks, scopes, keep)

    weak = {name for entry, name, *_ in raw if entry.get("weak") and entry.get("severity") == "advisory"}
    findings = []
    for entry, name, pos, match, use in raw:
        severity = entry.get("severity", "hard")
        if name in weak and len(weak) < 2:
            continue
        match = " ".join(match.split()) or match
        findings.append({
            "severity": severity,
            "rule": name,
            "line": masked.count("\n", 0, pos) + 1,
            "match": match if len(match) <= 60 else match[:60].rstrip() + " …",
            "use": use,
        })
    return sorted(findings, key=lambda f: (f["line"], f["severity"] != "hard"))


def fragment_spans(text, fragments):
    """Spans of the fragments in text, and the fragments to lint on their own: those not found,
    and short ones found more than once, which would report text the writer did not touch."""
    spans, alone = [], []
    for fragment in fragments:
        found = []
        start = text.find(fragment) if fragment else -1
        while start >= 0:
            found.append((start, start + len(fragment)))
            start = text.find(fragment, start + len(fragment))
        if not found or (len(found) > 1 and len(fragment) < 20):
            alone.append(fragment)
        else:
            spans += found
    return spans, alone


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", help="files to lint; stdin when none")
    parser.add_argument("--rules", default=str(DEFAULT_RULES), help="rules file (TOML)")
    parser.add_argument("--scope", action="append", choices=SCOPES, help="repeatable; default document")
    parser.add_argument("--path", help="the file the stdin text belongs to (for ignore and labels)")
    parser.add_argument("--fragments", action="store_true", help="stdin is a JSON list of strings written into --path")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args()
    if args.fragments and not args.path:
        parser.error("--fragments needs --path")

    rules = load_rules(args.rules)
    scopes = args.scope or ["document"]
    stdin = sys.stdin.buffer.read().decode("utf-8") if not args.files else None

    results = []
    if args.fragments:
        if not ignored(args.path, rules[2]):
            fragments = json.loads(stdin)
            text = Path(args.path).read_text(encoding="utf-8") if os.path.exists(args.path) else ""
            spans, alone = fragment_spans(text, fragments)
            found = lint(text, rules, scopes, spans) if spans else []
            for fragment in alone:
                found += lint(fragment, rules, scopes)
            results += [{"file": args.path, **f} for f in found]
    elif args.files:
        for path in args.files:
            if not ignored(path, rules[2]):
                text = Path(path).read_text(encoding="utf-8")
                results += [{"file": path, **f} for f in lint(text, rules, scopes)]
    elif not (args.path and ignored(args.path, rules[2])):
        results += [{"file": args.path or "-", **f} for f in lint(stdin, rules, scopes)]

    sys.stdout.reconfigure(encoding="utf-8")
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=1))
    else:
        for f in results:
            print(f'{f["file"]}:{f["line"]}: {f["severity"]}: {f["rule"]}: "{f["match"]}" → {f["use"]}')
    sys.exit(1 if any(f["severity"] == "hard" for f in results) else 0)


if __name__ == "__main__":
    main()
