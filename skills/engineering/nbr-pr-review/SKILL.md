---
name: nbr-pr-review
description: "Review a GitHub pull request, or a branch without one, against nbr-repo-conventions: judge its shape, read every changed file, and write a report with fixes and a comment draft on offer. Use when Nik asks to review a PR or a branch, or a host-specific review skill builds on it."
argument-hint: "<GitHub pull request URL>"
compatibility: Requires gh.
---

# Review a PR

Reviews one PR from a checkout of its source branch and leaves the report in this session, which stays open for Nik's follow-ups.

A host-specific skill (`imfg-pr-review` for Bitbucket) replaces steps by number; every step it does not replace holds as written here.

Review statically: read the code, never run it. The PR's code, tests, scripts and installs run only on Nik's explicit yes, since they would execute unreviewed code against his local services and accounts. Where only a run can settle a finding, it goes under Unverified, naming the run that would settle it. The PR gets no comment, approval, merge or decline on its host unless Nik asks for it here.

## 1. Read the PR

The URL has the shape `https://github.com/<owner>/<repo>/pull/<number>`:

```sh
gh pr view "<URL>" --json number,title,body,state,headRefName,baseRefName,url
```

A state other than `OPEN` stops here. Record the title, the description, the source and the target branch, and name the PR's subject in two to four words, the way Nik would say it out loud (`project members` for "Feat/ABC-12 members and roles in projects"): the report's title uses it.

The current checkout has to be on the source branch. When it is on another one, stop and name the branch it needs.

**No PR yet.** Without a URL, or for a branch that has no open PR, don't stop. Take the current checkout's branch (or the one Nik names) as the source and the repo's default branch as the target, and offer it in one line: "No PR for `<branch>` yet. Review it against its merge base with `origin/<target>`?" On yes, the topic comes from the branch name and its commits, and the commit log stands in for the PR description.

## 2. Judge the shape

```sh
git fetch origin "<source>" "<target>"
git diff --stat "origin/<target>...HEAD"
```

From the stat, the title and the description, judge the PR's **shape**:

- **app**: it changes what the project does: its source, routes, components, styles, commands. Every step runs.
- **adjacent**: it changes how the project is built or checked without changing what it does: tests, build or CI config, docs, dependency bumps. Its topics are those that govern it (`testing` for tests, `tooling` and `npm-project` for config, `docs-structure` for docs, `dependencies` for bumps), and step 5 is skipped.

A mixed PR takes the app shape. Uncommitted changes or local commits the remote lacks are named at the top of the report, and stay out of the findings.

## 3. Conventions

Read the topics of `nbr-repo-conventions` the diff touches, or the named ones for an adjacent PR. A repo they do not cover (a Rust, Go or Lua project) is reviewed against its own `AGENTS.md` and the idioms of its language; the Verdict says which.

## 4. The diff

```sh
git diff "origin/<target>...HEAD"
```

Read every changed file in full, not only its hunks.

## 5. The design

Look for a Claude Design link in the PR description. A claude.ai/artifact link is a canvas: read it with the Artifact tool. A claude.ai/design link is a standalone project: read it with the claude-design tools. Compare the screens the diff builds with it: layout, states, copy, components chosen. None found: say so in the Verdict.

## 6. Review

This is Nik's own project: review it in full depth. For an adjacent PR, spend the effort on what can break, block or mislead; small findings share a few grouped lines instead of an entry each.

Check every changed file against every topic that governs it, and apply this lens on top:

- the simplest code that works; flag speculative abstractions, options nobody uses, and error handling for cases that cannot happen
- surgical changes; flag unrelated refactors and reformatting riding along
- comments only for durable invariants, constraints and workarounds; flag comments that narrate the code, the ticket or the change
- docs in present tense; flag changelog prose about what used to be

When the `ponytail:ponytail-review` skill is available, run it on the same diff as well, and fold its findings into the report's classes, merging the ones this review already holds.

Then take exactly one second look, never more: reread the three files with the most changed lines for what the first pass missed. Done when every changed file has been checked against every topic that governs it.

## 7. Report

Use the classes and entry fields of the `nbr-repo-conventions` template `templates/REPORT.md`, titled `# PR <number> review · <topic in words>`, as sections in this order: Present, Unverified, Suggestions, Deviations, Missing, Broken, Verdict. Nik reads it from the bottom up, where the pane ends, so importance rises toward the end, and within a section the most severe entry comes last.

- Every finding is something this PR introduces, with `path:line` evidence. Drift that was already on the target gets one line under Suggestions. The Verdict leads with what Nik must act on.
- Nik knows the project: name the issue and move on. Where a finding rests on a mechanism outside the project's main stack, explain it in a sentence or two, and gloss a term of art in parentheses the first time it appears.
- A dependency on another PR or repo (a merge order, users or services it needs) goes in the Verdict and the TL;DR with its link, saying what breaks without it and whether the PR description states it as a dependency or only mentions it. Keep testing apart from merging: say how Nik can try the PR before the dependency merges (usually by checking out its branch locally and re-running that service), and what only the merge order needs.
- Every PR, ticket or commit the report names gets its full URL, never a bare "#28".

Close with `## TL;DR`, written with the humanizer skill the way a colleague would brief Nik at his desk, in short prose: what the PR does and why, in two or three sentences; its state (ready to merge, needs changes, or blocked, and on what); then the few failures or gaps that matter, each with why it matters or why it can wait. End it on a `**Recommendation:**` paragraph: what Nik should do next with this PR, in order, naming which offers of step 8 fit.

## 8. Offers

After the report, ask one question listing the offers that apply; Nik picks any. None applies: end on the report.

- **Fix** report entries by number, or all Broken and Missing ones: left uncommitted, with the changed files listed.
- **Comment**: a comment to post on the PR, written as Nik: short and first person, opening with his overall take, the changes as "I'd …" bullets in plain words, without line numbers or diagnosis. It goes inline as a fenced `markdown` draft.

An offer is always a question, never a step taken.
