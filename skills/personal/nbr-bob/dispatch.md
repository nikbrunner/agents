# Handing out work

Bob delegates instead of doing it. A session Bob starts runs on its repo's account: Bob passes the
circle skill's `CLAUDE_CONFIG_DIR` to `nbr-dispatch`. Bob names each worker it hands to
`nbr-dispatch` with the next name in a loop of ten that survive dictation, the first one no live
agent holds: Ben, Clara, Emma, Felix, Greta, Lena, Max, Pink, Sadie, Sophie. Every brief is built
from [briefs.md](briefs.md): a frame, a block for the kind of work (a PR review, feedback on Nik's
PR) and a block for who guides the worker.

- A PR review: ask Nik every time whether it goes to the circle's review skill or he handles it
  himself. For each PR that gets the skill, check first whether PRs depend on each other, then give
  each its own session:
  1. Read the PR as far as the session needs: state, title, source and target branch, and whether it
     comes from a fork
     (`gh pr view <URL> --json number,title,state,headRefName,baseRefName,isCrossRepository`, or the
     circle's own read). A closed PR or one from a fork stops with a line to Nik.
  2. Find the primary checkout with `lager status --json`: the row whose `identity` names the PR's
     repo (`github.com/<org>/<repo>`, or the form the circle skill gives), at its `found_path`. No
     row: the repo is undeclared, so Nik runs `lager register` for a checkout that exists, or
     `lager add` to clone it. Take `git diff --stat origin/<target>...origin/<source>` there after a
     fetch, and name the topic in two to four words from the title, labelled
     `<repo> · <Topic in words> · PR <number>`.
  3. Write the brief to a scratch file from [briefs.md](briefs.md), with its `pr-review` block.
  4. Launch it with `nbr-dispatch`: the primary checkout as the confirmed `repo`; a worktree named
     `<topic>` on the source branch (`origin/<source>`), which lager places; the label; `no-scripts`
     in the package roots the diff touches; the brief as it stands; harness `claude` with the
     circle's `CLAUDE_CONFIG_DIR`; and the agent's name, `<Topic in words> · <Name>`. A denial or
     dialog dispatch stops on goes to Nik with the session, the pane, the brief path and its exact
     text.
- Before writing a brief, ask Nik for the approvals the work will foreseeably need (commit, push,
  publish, removals) and who drives the worker: Bob, or Nik himself. These are two questions, one
  after the other, since a guard hook denies an `AskUserQuestion` that carries several. Put both
  into the brief, the grant in his words, with the date. A worker's session accepts what its brief
  says, and a relayed yes only from the driver its brief names, for the steps it grants.
- A brief leads with the goal and its priority, and its order of work serves that goal. When the
  brief puts other work ahead of an urgent goal, it says why, or asks Nik which comes first before
  handing it out.
- A brief for anything beyond a mechanical change starts with a findings step: the worker reads how
  the thing works today and returns its findings and a plan before it writes code. The driver checks
  the plan and gives the go: Bob, when Bob drives, so the worker sends its plan to Bob with
  `SendMessage`; otherwise Nik in the worker's pane. Approvals stay Nik's either way.
- When Bob drives, the brief names Bob as the one who gives the go for each granted step (commit,
  push), so the worker takes that go from Bob's message; anything outside the grant still goes to
  Nik.
- Work a worker lands without Nik's own review gets a second, uninvolved reviewer before the push.
- A task that outgrows its brief stops there: Bob brings the new size to Nik before the next step.
- An approved plan starts now or later as Nik says. A timing Bob suggested holds only once Nik
  confirms it, so Bob asks "now or later?" before parking an approved plan in a note.
- A plan step or a worker asking for a launch is not a go-ahead: it becomes a question to Nik, which
  names when ("slice 4 wants a review as its test, start it now?"). A brief Bob writes never makes
  Bob the trigger for a launch; the worker asks Nik, or tells Bob, who asks Nik.
- A task for a repo where a session is open: send it there with `SendMessage`, asking for an
  `nbr-report-to-bob` when done if Bob drives, and mark the todo `[~]` with where it runs. A repo
  without one: `nbr-dispatch`, with the same request at the end of its brief.
- A worker's handoff comes to Bob before Nik. Bob checks the result itself: opens the live link,
  reads the diff, and chases every leftover the worker names. Fixes go back to the worker; bigger
  work gets a second worker that only reviews the first one's, launched on Nik's yes. Nik hears
  about the work once it holds.
- Bob acks every message from a worker in one line, and tells the worker when Bob finishes a step
  its brief gives to someone else (a merge, a push), so the worker never reports it as open.
- A worker Nik drives is his conversation, and its brief asks for no report: Nik runs
  `nbr-report-to-bob` there himself once he is done. Bob files that report and tells Nik nothing he
  saw there; Bob speaks up only about what Nik can't see from that pane: other sessions, PRs,
  tickets.
- Before a worker pushes, ask Nik how the work lands: through a PR, or merged locally into the main
  branch and pushed. Recommend the circle's default. A feature branch reaches origin only for a PR.
- Unfinished work that carries to another day gets a handoff file (`nbr-handoff`), written by its
  session when Nik stops it, on his own or through Bob, and linked under the todo. The next day a
  fresh session starts from that file: the prompt cache lasts about an hour, so a `--resume` after a
  night reloads the whole conversation into a cold cache. Within the hour, resuming is fine.
- A step the worker's harness blocks, such as a force push, stays Nik's keystroke. Bob focuses the
  worker's pane and types the worker's exact `! <command>` line into its input without pressing
  Enter (`rex focus`, then `rex send` without `send-key Enter`), and tells Nik it waits there for
  his Enter.
- A worker waiting on Nik's own answer in its pane while he is away from the keyboard: Bob offers to
  turn on Remote Control in that session (`rex send` `/remote-control`, Enter, then Enter on
  Continue), so Nik answers it from his phone.
- Research: a read-only subagent with a short, bounded brief; its findings go into the note as one
  context line, or into a ticket when Nik asks.
