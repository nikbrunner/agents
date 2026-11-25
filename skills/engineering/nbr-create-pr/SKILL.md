---
name: nbr-create-pr
description:
  "Write or update a pull request in a fixed shape: a slice title, a flat trigger-word list for what
  changed, tests added (e2e per scenario), how to test, optional screenshots and design-file
  changes, open decisions. Drafts locally, waits for approval, then publishes."
compatibility: Requires the gh CLI for GitHub or bkt for Bitbucket, and the nbr-voice skill.
argument-hint: "[optional PR number or URL]"
user-invocable: true
metadata:
  argument-hint: "[optional PR number or URL]"
  user-invocable: true
---

# nbr-create-pr

A PR description is **durable**: it states what the PR is and does, and still reads true after
merge. Everything in it is a short bullet a reviewer scans top to bottom.

## Steps

1. **Gather.** Read the diff against the base, hunk by hunk, then the branch's commits, the ticket
   (key, title, link), the test files the diff adds or changes, and the existing PR body if there is
   one (`bkt pr view <n>` on Bitbucket, `gh pr view <n>` on GitHub). The diff is the source of
   truth; a commit message is a claim to check against it. Done when you can name every user-visible
   change, each traced to a hunk, and every added test scenario.
2. **Close the gaps.** List anything transient the draft would have to admit: a known bug, a missing
   spec, a decided but unbuilt change, unpushed commits. Fix what was already decided, ask about the
   rest. A commit message the diff contradicts (it claims a change the base already has, misses one,
   or gets its scope wrong) goes to the user with what the diff shows, and an offer to reword it or
   to rebuild the run with `/nbr-git-commit-rebuild`, which the user starts. On a pushed branch,
   either needs a force push the user approves. Done when the list holds only genuine open decisions
   for reviewers.
3. **Draft** using the template below, then run the `nbr-voice` rewrite pass on it. Done when every
   section is filled or deliberately omitted.
4. **Show and wait.** Put the title and the body into the reply as one fenced `markdown` block,
   copy-ready, and stop. Apply the user's edits in the next reply the same way until they approve
   the text. Write the body to a gitignored scratch file (the project's `tmp/` or the session
   scratchpad) only to hand it to the platform CLI when publishing.
5. **Publish** only after explicit approval: push the branch if commits are local (ask first), set
   the title and body with the platform CLI, and give the PR link.

## Template

Title, set as the PR title and never repeated in the body:
`[TICKET] <what this PR delivers; for a slice, name the slice>`

```markdown
- <Slice of | Implements> [TICKET <ticket title>](<ticket link>)
- Scope: <what is in>
- Later PRs: <what follows> (slices only)
- <Review hint, e.g. review commit by commit; which commits are mechanical>

## What changed

- New: <one thing that exists now>
- Updated: <one thing that works differently>
- Fixed: <one thing that was wrong>
- Removed: <one thing that is gone>
- Unchanged: <the one thing a reviewer needs to hear stayed the same>

## Tests added

End to end, <n> tests in `<dir>` (`<command>`):

- <Area or project>
  - <case>: <result>

Unit: <one line on what they cover>

## How to test

Setup

- <command or URL per line>

Steps

1. <Area>
   - <action>: <result>

## Screenshots

| State                   | Image   |
| ----------------------- | ------- |
| <state or before/after> | <image> |

## Design file

- <frame or row>: <what changed on the design source>

## Open decision

<Topic>

- <current state>
- <option>: <consequence>
```

## Section rules

- **Bullets**: one idea each, about a line long. Results read `case: result`. Tests added and How to
  test group their bullets under a parent by area; What changed stays flat.
- **What changed**: one flat list of user-visible behaviour and the conventions a reviewer must
  know, in the product's language. Every line starts with its trigger word, `New:`, `Updated:`,
  `Fixed:`, `Removed:` or `Unchanged:`, in that order, and holds one change in one short sentence.
  Two facts joined by "and" or a semicolon are two lines. A new skill, command, page or export gets
  its own `New:` line. How a thing works belongs in How to test or the docs. Code shape stays in the
  commits: write lists, never diffs, file trees or call graphs.
- **Shortening**: cut whole lines. Merging two lines into one sentence hides the second.
- **Tests added**: every new end-to-end scenario, named by what the user does and sees. Unit tests
  get one line.
- **How to test**: a setup block, then numbered steps a tester can follow without reading code.
- **Screenshots**: only for a visual change with images at hand, else omit the heading. A table, one
  row per image: what it shows on the left, the image on the right. Where the agent cannot upload,
  the right cell holds the image's file name only, `01-<state>.png`, never its folder or path; Nik
  replaces it with the upload. A folder named `<repo>-pr-<topic>` from before the PR existed is
  renamed to `<repo>-pr-<n>` once the PR has its number.
- **Design file**: only when the design source (Figma, Claude Design board) changed with this PR.
  Link it in the intro.
- **Open decision**: only questions reviewers or colleagues still have to settle. Settled choices
  belong in What changed. A choice the author already made is settled, even where a reviewer could
  disagree, and a point the user was never asked about goes to the user first.
