# Filing rules

Every change to a note follows these rules, whether it comes from a report, a paste, a check-in or
Nik.

## Where a point goes

- **Forget by default, then ask when.** Like a person's memory, Bob keeps what will matter later
  and lets the rest go. Everything Bob writes, in Nik's notes or in its own files, first passes two
  questions:
  1. Will Nik or Bob need this again? Most of a report fails, so "nowhere" is the most common home.
  2. When does it happen? Something to do now goes straight to Nik in chat and is not captured. It
     comes with a draft when it is a message ("write to the reviewer: …"). Important but not urgent
     goes to its ticket or the next weekly. Nik's work for today, or work with a date or someone
     waiting, goes into the daily note. The rest of his own work goes into the monthly note.

  Context, the time of day and the day's plan usually answer both. When they don't, ask Nik with a
  suggestion before filing. A carried todo passes the two questions again.

- **Every kept point gets one home**, chosen on purpose. A report or a paste is material, not a todo
  list. The homes:
  - nowhere: most points; tiny details, things already known or done
  - now: Nik in chat
  - the ticket it belongs to, as a comment or a line in its description, drafted for Nik's yes.
    Tickets are the source of truth, and a small point rarely needs a new ticket.
  - the next weekly of the work circle whose code it concerns, as a discussion point: another
    team's issue, or something the team should hear
  - Bob's own file in the circle's `bob/` folder: detail Bob may need later and nobody else reads
  - the design artifact it concerns, asked first. It is a static list artboard on the canvas's
    `Todos` page: a title and one row per todo with a drawn box, nothing else. A done row gets the
    class `done`, which fills the box and strikes the text. Nik ticks rows there through the
    canvas's Claude. The note keeps one todo linking the canvas.
  - the monthly note: Nik's own backlog, with no date and nobody waiting
  - the daily note: Nik's own work for today, or work with a date or someone waiting, one line
- **Others' changes are a heads-up.** A ticket a colleague moved or a review someone else left goes
  to Nik in chat. Never file it as his work.
- **Credit by authorship.** Who opened a PR does not decide whose work it is; `git shortlog` on its
  branch does.

## Daily and monthly notes

- **A todo lives in one note at a time.** Pulling a monthly todo into a daily note moves it there.
  Done work is ticked in the daily note only, so the monthly note holds open items alone. New
  backlog goes to the bottom of its heading with Bob's effort estimate. Nik sets the order.
- **The daily note stays as small as possible.** It is Nik's map of the day: to cross off, to
  glance at, to write in himself. One point per line: a piece of work or a separate step of it,
  never several points folded into one line. Todos about the same PR or ticket share one parent. A
  larger project, such as a release, is a heading over the day's todos for it. Its tickets hold the
  rest, and the heading carries with its open todos.
- **Update in place.** A report about a todo already in the daily or monthly note changes that
  todo. A monthly todo the report shows in progress moves into the daily note. Each new outcome
  adds a new todo, even when one report or one release brings several. File it in its circle's
  note, under the heading its shape gives the repo.
- **Nik writes too.** He keeps his notes by hand as well. What he adds, rewords or reorders stands:
  Bob files around it, in his wording and order. A fault Bob spots in his lines (a broken link, a
  stale state, a misfiled todo) goes to Nik as a suggested fix.
- **Weeklies stay live.** A weekly written on its meeting day stays open until Nik presents it.
  Each check-in and each report that finishes or starts work in its circle updates it: finished
  work as an achievement, started work under the plan. A changed plan goes to Nik as a suggestion.

## Todos and checkboxes

- **A checkbox is Nik's own task.** Context under it (what he pushed, who it waits on, what was
  left as follow-up) is a plain bullet of one or two lines. A bullet saying what a todo waits on
  does not count as a child. Context that seems to need more is either too much, so cut it, or a
  real issue for its ticket or Bob's own file. Questions for a PR's author or another team stay out
  of the note.
- **Only actionable work gets a checkbox.** Bob keeps Nik's day focused. A follow-up tied to an
  open-ended future ("with the next release", "someday") is no todo and never keeps a parent open.
- **Links carry the real title.** A PR or ticket link uses the real title with its square brackets
  removed ("PROJ-42 Add search"). Nested brackets break the rendering.
- **Nik's part decides the box.** A started todo is `[~]`. It is `[x]` once Nik's part is over, at
  least for today, even when others still have to act. A nested bullet then says what it waits on,
  such as `waits on review`.
- **Parents follow children.** All children ticked: tick the parent. A child reopened or added: the
  parent goes back to `[~]`. Done work takes no new children: a merged PR or a resolved ticket stays
  `[x]`, whatever follow-ups come after it.
- **Every task event reorders the list.** Whenever a todo is ticked, started, added or picked for
  now, sort its list again: done `[x]` first, then in progress `[~]`, then open `[ ]`. Within a
  group, what Nik picked for now goes first.
- **Focus and optional.** Under each repo heading of a daily note, the focus comes first. Work Nik
  may pick up when time allows sits below it under `#### Optional`. The order above holds within
  each part, and a todo Nik picks moves from Optional into the focus. The weeklies stay out of this
  split.
- **Deferred work** with a date or someone waiting is `[>]` and carries into the next note. Backlog
  Nik defers goes to its place in the monthly note, with an effort tag.

## Keeping lines short

- **Plain and short.** Every line Bob writes in a note goes through the `nbr-voice` rewrite pass.
  It says the least that still holds: plain words, short lines, nothing said twice, readable at a
  glance. A worker's wording never lands in a note as it stands: say what Nik sees, in his words.
- **Tracking lines are temporary.** While work runs, a context line may say where it runs: a
  worker, a Rex pane, who it waits on.
- **An open PR speaks for itself.** Once a PR and its description are written, its todo sheds the
  context the PR already holds (what changed, versions, screenshots). It keeps only who it waits on
  and Nik's open checkboxes.
- **Carry the work, not the history.** A todo that moves to another day takes its open children
  with it. Done children and spent context stay behind. When the open children are the work list of
  a design artifact, a plan or a ticket, they move there by the homes above. The note then keeps the
  parent with its link. A day Nik takes off gets only what happens that day. The rest goes straight
  to the next working day's note.
- **Done shrinks.** A ticked todo sheds its tracking lines and spent context. A todo that is a
  ticket or PR link shrinks to the link alone, since its title already says what was done. Any other
  todo keeps one line of prose. Shrinking folds a todo's own children only; separate todos stay
  separate lines.
