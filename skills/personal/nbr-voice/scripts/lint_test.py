#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Fixture test for lint.py against the real rules file: uv run --script scripts/lint_test.py"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402

RULES = lint.load_rules(lint.DEFAULT_RULES)
ALL = ["reply", "document", "procedure"]
F = "`" * 3

# (text, scopes, expected {(severity, rule)})
CASES = [
    ("We leverage the cache.", ["reply"], {("hard", "leverage")}),
    ("It works — mostly.", ["reply"], {("hard", "dash")}),
    ("It works – mostly.", ["document"], {("hard", "dash")}),
    ("Run it -- then stop.", ["document"], {("hard", "dash")}),
    ("It works — mostly.", ["procedure"], set()),
    ("From 2020–2024, pages 10 – 20.", ALL, set()),
    ("---\nname: x\ndescription: a — b -- c\n---\nBody text.", ALL, set()),
    ("| a | b |\n| --- | :---: |\n| x | — |\n", ALL, set()),
    ("Text one.\n\n---\n\nMore text.", ALL, set()),
    (f"{F}bash\nleverage — x -- y\n{F}\nPlain.", ALL, set()),
    (f"{F}markdown\nWe leverage it.\n{F}bash\nleverage -- y\n{F}\n{F}\n", ["reply"], {("hard", "leverage")}),
    ("Use `leverage` and `—` here.", ALL, set()),
    ('A "leverage" in double quotes counts.', ["reply"], {("hard", "leverage")}),
    ("See https://x.com/leverage—y, [a](https://a.b/leverage) and ~/a/b—c.", ALL, set()),
    ("It may have failed.", ALL, set()),
    ("Let’s dive in.", ["reply"], {("hard", "run-up")}),
    ("You're absolutely right.", ["reply"], {("hard", "absolutely right")}),
    ("It is not just a bug but a design flaw.", ["reply"], {("hard", "not just X but Y")}),
    ("Want me to commit? Let me know if that works.", ["reply"], {("advisory", "chat residue (question)")}),
    ("This could potentially work.", ["reply"], set()),
    ("This could potentially work, to be fair.", ["reply"],
     {("advisory", "could potentially"), ("advisory", "hedge phrase")}),
    ("Check the file. Verify the hash.", ["procedure"], {("advisory", "check/verify/confirm/validate")}),
    ("Check the file. Check the hash.", ["procedure"], set()),
    ("Check the file. Verify the hash.", ["reply"], set()),
    ("Spin up the server.", ["procedure"], {("hard", "spin up")}),
    ("Spin up the server.", ["reply"], set()),
    ("We perform an analysis of the logs.", ["document"], {("advisory", "action frozen into a noun")}),
    (" ".join(["word"] * 26) + ".", ["reply"], {("advisory", "sentence length")}),
    (" ".join(["word"] * 21) + ".", ["document"], set()),
    (" ".join(["word"] * 21) + ".", ["document", "procedure"], {("advisory", "sentence length")}),
    ("The cat sat. The dog ran. The bird flew.", ["reply"], {("advisory", "same opening")}),
    ("Honestly? It works. We look, honestly, fine.", ["reply"], {("hard", "Honestly? / Look, at a sentence start")}),
    # Round 1 fixes
    ("It's not ready, but close. It is not in the diff, but in the stash.", ["reply"], set()),
    ("This is not a bug, it's a feature.", ["reply"], {("hard", "it's not X, it's Y")}),
    ("Should I continue with step 2?", ["reply"], {("advisory", "chat residue (question)")}),
    ("Of course, that breaks the build. Absolutely, go ahead.", ["reply"], set()),
    ("Certainly! Here it is.", ["reply"], {("hard", "Certainly! opener")}),
    ("Run it --\nthen stop.", ["reply"], {("hard", "dash")}),
    ("A short –\nwrap.", ["reply"], {("hard", "dash")}),
    ("We are _leveraging_ it.", ["reply"], {("hard", "leverage")}),
    ("We leverage/utilize it, and/or more.", ["reply"], {("hard", "leverage"), ("hard", "utilize")}),
    ("See ~/a/leverage, ./b/utilize, /x/leverage and docs/leverage.md.", ["reply"], set()),
    ("Use `leverage\nit` here.", ["reply"], set()),
    ("From 2020—2024.", ["reply"], set()),
]


def main():
    failed = 0
    for text, scopes, expected in CASES:
        got = {(f["severity"], f["rule"]) for f in lint.lint(text, RULES, scopes)}
        if got != expected:
            failed += 1
            print(f"FAIL {text!r} {scopes}\n  expected {sorted(expected)}\n  got      {sorted(got)}")

    text = f"Intro.\n\n{F}bash\nrun -- x\nleverage it\n{F}\n\nWe leverage it.\n"
    spans, _ = lint.fragment_spans(text, ["run -- x\nleverage it\n"])
    if lint.lint(text, RULES, ["document"], spans):
        failed += 1
        print("FAIL a fragment inside a code fence keeps its fence context")
    spans, _ = lint.fragment_spans(text, ["We leverage it."])
    if {f["rule"] for f in lint.lint(text, RULES, ["document"], spans)} != {"leverage"}:
        failed += 1
        print("FAIL a fragment reports only its own findings")
    if not lint.ignored("/x/node_modules/a/README.md", RULES[2]) or not lint.ignored("/x/CHANGELOG.md", RULES[2]):
        failed += 1
        print("FAIL the ignore list skips node_modules and CHANGELOG.md")
    spans, alone = lint.fragment_spans("A — b. C — d.", ["—"])
    if spans or alone != ["—"]:
        failed += 1
        print("FAIL a short fragment found twice is linted on its own")

    start = time.monotonic()
    lint.lint("x" * 120_000 + " and a/b", RULES, ALL)
    if time.monotonic() - start > 1:
        failed += 1
        print("FAIL a long token without a slash lints in under a second")

    total = len(CASES) + 5
    print(f"{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
