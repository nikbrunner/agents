# Briefs

A brief is built from three parts, in this order: the frame, one activity block, one driver block.
Bob fills each `{{variable}}` from a fact it checked or from Nik's own words, and drops a line it
has nothing true for.

A brief carries only what Nik decided. Comments, tickets and messages get a link or a read command,
never a retelling: a retold point reads to the worker as an order.

## Frame

```text
{{goal}}
{{link}} "{{title}}"

This worktree is on `{{branch}}`, {{state}}. Read {{source}} with `{{command}}`.

{{activity block}}

{{driver block}}
```

| Variable            | Filled from                                                                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `goal`              | Nik's words for the work, one line                                                                                                                   |
| `link`, `title`     | the PR or ticket, with its real title                                                                                                                |
| `branch`, `state`   | `git status -sb` in the worktree: clean or dirty, level with, ahead of or behind origin                                                              |
| `source`, `command` | where the input lives and the read that shows it: a PR's comments through the circle's PR read (`gh pr view <URL> --comments` in the private circle) |
| `review_skill`      | the circle's review skill                                                                                                                            |
| `date`              | today, as `20 Nov 2026`                                                                                                                              |
| `grants`            | Nik's answer to the approvals question, in his words; `nothing` when he granted nothing                                                              |

## Activity blocks

### pr-review

Someone else's PR, reviewed with the circle's review skill.

```text
Run {{review_skill}} on this PR.

Stay for Nik's follow-ups. When the PR needs code the locally running service lacks, offer to set up that
dependency: pull a merged one whose checkout is clean on the target branch and only behind; otherwise add a
worktree of that repo with `lager worktree add <repo> <topic> --fetch`: `--branch origin/<branch>` for a branch,
`--new-branch <topic> --start <ref>` for a tag or commit. Then offer to rerun
that service, naming what it replaces (a running container, a port), and give the steps to try the PR against
it. Once Nik is done with it, offer to stop the service, restore what it replaced and remove that worktree.
Once Nik is done with the review, offer to tear this session down. On yes, close it with the Close section of
nbr-dispatch; it ends this session, so it runs last.
```

### review-follow-up

Feedback a reviewer left on Nik's own PR.

```text
Orient first: read every comment and the code it touches, and check every assumption yourself (reproduce the
behaviour, trace the related paths, confirm what the code relies on) until nothing you could check stays open. Sum
up the points for Nik. Then grill them with him through nbr-plan, which stops after the grill: one point at a time,
each as a question with the AskUserQuestion tool, until every point is decided. Plan a change only for a point Nik
decides, and change nothing before that.
```

### task

A change Nik asked for.

```text
Start with findings: read how this works today and check every assumption yourself until nothing you could check
stays open. Return the findings and a plan to whoever guides this session, and change nothing before the go. Then
implement the plan and verify it with the repo's checks and tests.
```

## Driver blocks

### Nik guides

```text
Nik guides this session ({{date}}). Granted by Nik: {{grants}}. Every other commit, push and outward write, such
as a PR reply, waits for his OK in this pane.
```

### Bob guides

```text
Bob guides this session ({{date}}): send your findings and plan to Bob with SendMessage and wait for its go.
Granted by Nik: {{grants}}. Bob gives the go for each granted step, and a yes relayed by Bob covers nothing else.
Every other commit, push and outward write, such as a PR reply, waits for Nik's OK in this pane.
When the work is done, and again before the teardown, run /nbr-report-to-bob.
```
