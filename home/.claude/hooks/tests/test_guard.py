#!/usr/bin/env python3
"""Tests for enforce/guard.py. Run with `python3 test_guard.py`."""
import json
import os
import subprocess
import sys
import unittest

ENFORCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "enforce")
sys.dont_write_bytecode = True
sys.path.insert(0, ENFORCE)
import guard  # noqa: E402


def bash(command):
    result = guard.decide({"tool_name": "Bash", "tool_input": {"command": command}})
    return result[0] if result else None


def ask(count):
    question = {"question": "Which?", "header": "Pick", "options": [{"label": "A"}, {"label": "B"}]}
    result = guard.decide({"tool_name": "AskUserQuestion", "tool_input": {"questions": [question] * count}})
    return result[0] if result else None


HEREDOC_COMMIT = """git commit -F - <<'EOF'
Stop using sed -i and git add . in skills

Also git add -A, git worktree add and git push --force.
EOF"""

SUBST_COMMIT = '''git commit -m "$(cat <<'EOF'
Explain why sed -i 's/a/b/' file and git add -u are denied
EOF
)"'''


class Edits(unittest.TestCase):
    def test_sed_inplace_denied(self):
        for command in ("sed -i 's/a/b/' file.txt", "sed -i '' 's/a/b/' src/x.ts", "sed -i.bak -e 's/a/b/' x",
                        "gsed --in-place 's/a/b/' x", "sed -Ei 's/a/b/' x", "sed -Ei.bak 's/a/b/' x",
                        "/usr/bin/sed -i 's/a/b/' x", "LC_ALL=C sed -i 's/a/b/' x"):
            self.assertEqual(bash(command), "deny", command)

    def test_perl_inplace_denied(self):
        for command in ("perl -pi -e 's/a/b/' lib/x.pm", "perl -i -pe 's/a/b/' x", "perl -pi.bak -e 's/a/b/' x",
                        "perl -0pi -e 's/a/b/' x", "perl -Mstrict -pi -e 's/a/b/' x"):
            self.assertEqual(bash(command), "deny", command)

    def test_sed_in_pipelines_denied(self):
        self.assertEqual(bash("rg -l foo | xargs sed -i '' 's/foo/bar/'"), "deny")
        self.assertEqual(bash("rg -l0 foo | xargs -0 -n 1 sed -i '' 's/foo/bar/'"), "deny")
        self.assertEqual(bash("find . -name '*.md' -exec sed -i '' 's/a/b/' {} \\;"), "deny")
        self.assertEqual(bash("find . -name '*.md' -execdir perl -pi -e 's/a/b/' {} +"), "deny")
        self.assertEqual(bash("cd repo && sed -i 's/a/b/' x"), "deny")

    def test_sed_inplace_on_temp_allowed(self):
        self.assertIsNone(bash("sed -i '' 's/a/b/' /tmp/x.txt"))
        self.assertIsNone(bash("sed -i 's/a/b/' /private/tmp/a /var/folders/xy/T/b"))
        self.assertIsNone(bash("perl -pi -e 's/a/b/' /tmp/x"))
        if os.environ.get("TMPDIR", "").startswith("/var/folders/"):
            self.assertIsNone(bash("sed -i '' 's/a/b/' \"$TMPDIR/x\""))

    def test_sed_inplace_mixed_targets_denied(self):
        self.assertEqual(bash("sed -i 's/a/b/' /tmp/x src/y"), "deny")

    def test_sed_read_allowed(self):
        self.assertIsNone(bash("sed -n '1,20p' file.txt"))
        self.assertIsNone(bash("sed 's/a/b/' file.txt > out.txt"))
        self.assertIsNone(bash("grep -n 'sed -i' notes.md"))

    def test_sed_or_perl_as_argument_allowed(self):
        for command in ("rg sed -i", "git log --grep sed -i", "echo sed -i", "perl -Mstrict -e 'print 1'",
                        "perl -Ilib -e 'print 1'", "perl -le 'print 1'"):
            self.assertIsNone(bash(command), command)


class Staging(unittest.TestCase):
    def test_bulk_add_denied(self):
        for command in ("git add -A", "git add .", "git add -u", "git add --all", "git add ./",
                        "git add *", "git add :/", "git add :", "git add ..", "git add ../", "git add ./*",
                        "git add ':(top)'", "git add -- .",
                        "git -C ~/repos/x add -A", "cd repo && git add .", "git status; git add -A",
                        "git status\ngit add ."):
            self.assertEqual(bash(command), "deny", command)

    def test_commit_all_denied(self):
        for command in ("git commit -a -m 'x'", "git commit -am 'x'", "git commit --all -m x",
                        "git commit -m x .", "git commit -m x -- .", "git commit -m x :/"):
            self.assertEqual(bash(command), "deny", command)

    def test_add_by_name_allowed(self):
        self.assertIsNone(bash("git add path/a path/b"))
        self.assertIsNone(bash("git add ../other/file.md"))
        self.assertIsNone(bash("git add 'notes/Daily Note.md' && git commit -m 'chore: backup'"))
        self.assertIsNone(bash("git commit -m . path/a"))

    def test_heredoc_message_not_matched(self):
        self.assertIsNone(bash(HEREDOC_COMMIT))
        self.assertIsNone(bash(SUBST_COMMIT))
        self.assertIsNone(bash(HEREDOC_COMMIT.replace("'EOF'", "'END-MSG'").replace("\nEOF", "\nEND-MSG")))

    def test_quoted_message_not_matched(self):
        self.assertIsNone(bash('git commit -m "Stop using git add . and sed -i"'))

    def test_heredoc_with_apostrophe_then_real_add(self):
        command = "cat > /tmp/m <<'EOF'\nit's done, git add -A\nEOF\ngit add ."
        self.assertEqual(bash(command), "deny")

    def test_unbalanced_quote_in_comment_still_checked(self):
        self.assertEqual(bash("git add -A # it's fine"), "deny")
        self.assertEqual(bash("echo it's\ngit add ."), "deny")


class Worktrees(unittest.TestCase):
    def test_git_worktree_add_denied(self):
        self.assertEqual(bash("git worktree add ../x.worktrees/y -b feat/y"), "deny")
        self.assertEqual(bash("git -C ~/repos/x worktree add ../y"), "deny")

    def test_lager_and_git_worktree_list_allowed(self):
        self.assertIsNone(bash("lager worktree add ~/repos/x 'topic words' --fetch"))
        self.assertIsNone(bash("git worktree list"))


class Push(unittest.TestCase):
    def test_force_push_asks(self):
        for command in ("git push --force", "git push -f origin main", "git push --force-with-lease",
                        "git push --force-with-lease=main:abc origin main", "git push origin +main",
                        "git push origin +HEAD:main"):
            self.assertEqual(bash(command), "ask", command)

    def test_plain_push_passes(self):
        self.assertIsNone(bash("git push origin main"))

    def test_no_verify_asks(self):
        for command in ("git commit --no-verify -m x", "git push --no-verify", "git commit -n -m x",
                        "git commit -nm x"):
            self.assertEqual(bash(command), "ask", command)
        self.assertIsNone(bash("things update --no-verify"))

    def test_deny_wins_over_ask(self):
        self.assertEqual(bash("git push --force && git add -A"), "deny")

    def test_ask_reasons_address_nik(self):
        for command in ("git push --force", "git push --no-verify"):
            reason = guard.decide({"tool_name": "Bash", "tool_input": {"command": command}})[1]
            self.assertTrue(reason.endswith("Confirm?"), reason)


class Questions(unittest.TestCase):
    def test_several_questions_denied(self):
        self.assertEqual(ask(2), "deny")

    def test_one_question_passes(self):
        self.assertIsNone(ask(1))

    def test_other_tools_pass(self):
        self.assertIsNone(guard.decide({"tool_name": "Read", "tool_input": {"file_path": "/x"}}))


class Script(unittest.TestCase):
    def run_hook(self, stdin):
        return subprocess.run([sys.executable, "-B", os.path.join(ENFORCE, "guard.py")],
                              input=stdin.encode(), capture_output=True)

    def test_output_shape(self):
        result = self.run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "git add -A"}}))
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("hunks.py", output["permissionDecisionReason"])

    def test_fails_open(self):
        for stdin in ("not json", json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo 'open"}})):
            result = self.run_hook(stdin)
            self.assertEqual((result.returncode, result.stdout), (0, b""))


if __name__ == "__main__":
    unittest.main()
