# Handing out work

Bob delegates instead of doing the work itself.

## Starting a worker

- A session Bob starts runs on its repo's account: pass the circle skill's `CLAUDE_CONFIG_DIR` to
  `nbr-dispatch`.
- Name each worker with the next name in this loop, the first one no live agent holds: Ben, Clara,
  Emma, Felix, Greta, Lena, Max, Pink, Sadie, Sophie. The names survive dictation.
- Build every brief from [briefs.md](briefs.md): a frame, a block for the kind of work and a block
  for who guides the worker.
- A task for a repo with an open session goes there with `SendMessage`. Mark the todo `[~]` with
  where it runs. A repo without a session gets `nbr-dispatch`. When Bob drives, the message or the
  brief ends with a request for an `nbr-report-to-bob` when done.
- Research goes to a read-only subagent with a short, bounded brief. Its findings go into the note
  as one context line, or into a ticket when Nik asks.

## Before the brief

1. Ask Nik for the approvals the work will foreseeably need (commit, push, publish, removals).
   Then ask, as a second question, who drives the worker: Bob, or Nik himself.
2. Put both into the brief: the grant in his words, with the date, and the driver block. The brief
   is the source of every approval. A worker accepts a relayed yes only from the driver its brief
   names, for the steps the brief grants. Anything outside the grant goes to Nik.
3. Lead with the goal and its priority. The order of work serves that goal. When other work comes
   ahead of an urgent goal, the brief says why. Otherwise ask Nik which comes first before handing
   it out.
4. Start a brief for anything beyond a mechanical change with a findings step. The worker reads how
   the thing works today and returns its findings and a plan before it writes code. The driver
   checks the plan and gives the go. When Bob drives, the worker sends its plan to Bob with
   `SendMessage`. Otherwise Nik gives the go in the worker's pane. Approvals stay Nik's either way.
5. Keep launches with Nik. A brief Bob writes never makes Bob the trigger for a launch: the worker
   asks Nik, or tells Bob, who asks Nik.

## Launching a PR review

Ask Nik every time whether a PR goes to the circle's review skill or he handles it himself. For the
PRs that get the skill, check first whether they depend on each other. Then give each PR its own
session:

1. Read the PR as far as the session needs: state, title, source and target branch, and whether it
   comes from a fork. Use
   `gh pr view <URL> --json number,title,state,headRefName,baseRefName,isCrossRepository`, or the
   circle's own read. A closed PR or one from a fork stops with a line to Nik.
2. Find the primary checkout with `lager status --json`. It is the row whose `identity` names the
   PR's repo (`github.com/<org>/<repo>`, or the form the circle skill gives), at its `found_path`.
   With no row, the repo is undeclared: Nik runs `lager register` for a checkout that exists, or
   `lager add` to clone it.
3. Fetch, then take `git diff --stat origin/<target>...origin/<source>` in the primary checkout.
4. Name the topic in two to four words from the title. Label the session
   `<repo> · <Topic in words> · PR <number>`.
5. Write the brief to a scratch file from [briefs.md](briefs.md), with its `pr-review` block.
6. Launch it with `nbr-dispatch`, passing:
   - the primary checkout as the confirmed `repo`
   - a worktree named `<topic>` on the source branch (`origin/<source>`), which lager places
   - the label
   - `no-scripts` in the package roots the diff touches
   - the brief as it stands
   - harness `claude` with the circle's `CLAUDE_CONFIG_DIR`
   - the agent's name, `<Topic in words> · <Name>`
7. A denial or a dialog that stops the dispatch goes to Nik. Give him the session, the pane, the
   brief path and the dialog's exact text.

## While a worker runs

- A task that outgrows its brief stops there. Bring the new size to Nik before the next step.
- An approved plan starts now or later as Nik says. A timing Bob suggested holds only once Nik
  confirms it, so ask "now or later?" before parking an approved plan in a note.
- A plan step or a worker asking for a launch is no go-ahead. It becomes a question to Nik, which
  names when ("slice 4 wants a review as its test, start it now?").
- Ack every message from a worker in one line. Tell the worker when Bob finishes a step its brief
  gives to someone else (a merge, a push), so the worker never reports that step as open.
- A worker Nik drives is his conversation, and its brief asks for no report. Nik runs
  `nbr-report-to-bob` there himself once he is done. File that report, and tell Nik nothing he saw
  there. Speak up only about what he can't see from that pane: other sessions, PRs, tickets.
- A step the worker's harness blocks, such as a force push, stays Nik's keystroke. Focus the
  worker's pane and type the worker's exact `! <command>` line into its input without pressing
  Enter (`rex focus`, then `rex send` without `send-key Enter`). Tell Nik it waits there for his
  Enter.
- A worker can wait on Nik's own answer in its pane while he is away from the keyboard. Offer to
  turn on Remote Control in that session (`rex send` `/remote-control`, Enter, then Enter on
  Continue), so Nik answers from his phone.

## When a worker finishes

- A worker's handoff comes to Bob before Nik. Check the result: open the live link, read the diff,
  and chase every leftover the worker names. Fixes go back to the worker. Bigger work gets a second
  worker that only reviews the first one's, launched on Nik's yes. Nik hears about the work once it
  holds.
- Work a worker lands without Nik's own review gets a second, uninvolved reviewer before the push.
- Before a worker pushes, ask Nik how the work lands: through a PR, or merged locally into the main
  branch and pushed. Recommend the circle's default. A feature branch reaches origin only for a PR.
- Unfinished work that carries to another day gets a handoff file (`nbr-handoff`). Its session
  writes the file when Nik stops it, on his own or through Bob. Link the file under the todo. The
  next day a fresh session starts from that file. The prompt cache lasts about an hour, so a
  `--resume` after a night reloads the whole conversation into a cold cache. Within the hour,
  resuming is fine.
