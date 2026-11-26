#!/usr/bin/env python3
"""Bob's check-in hook: gather the signals itself and decide whether a check-in reaches Bob.

`checkin.py prompt` runs as a UserPromptSubmit hook. The prompt `Bob check-in` is a check-in;
any other prompt from Nik records the time of his last message. A check-in is dropped while
Nik wrote within QUIET and no meeting starts before the next run or ended since the last
run, and again when nothing changed since the last run and no flag is raised. Otherwise Bob gets `../checkin.md` and the
digest as additional context.

`checkin.py stop` runs as a Stop hook. On a check-in turn that raised a block flag, it holds
the turn once when no Bash call ran `ical add` or `ical update`.

Signals, each in its own thread with its own timeout: Rex panes and the state their agent
reports (`working`, `idle`, ...), `lager status --json`, today's events in every --calendar,
the day's block ledger, and every --extra command (run by bash with pipefail). Each signal is
a set of lines; news is every line added or removed since the last run (a merged PR is a line
gone from the open list). A signal seen for the first time is stored without news. A
checkout has one line for its branch and one while it is dirty, so a moving count of changed
files is no news.

Flags:
- meeting: a timed, accepted or open event that is not Bob's block starts before the next run.
- meeting-ended: such an event ended since the last run, so the news Bob held during it
  reaches him. While one runs, the digest says until when.
- block-ended: a ledger block ended since the last run while a circle session works and no
  block covers now. Its work probably still runs.
- no-block: a circle session works while no ledger block covers now and none ended since the
  last run. Raised only when a session joins that uncovered set, so a block Bob declined
  does not come back every run.
A circle session is a pane whose agent Rex reports `working` and whose cwd lies under a
--repos-root; Bob's own pane ($REX_BLOCK) never counts. A block that ends within
COVER_SLACK no longer covers now, so a block stretched to this run counts as ended.
block-ended and no-block are the block flags the Stop hook checks.

Fail open: a signal that errs or times out becomes one digest line and keeps its last state.
A new error passes the check-in like news; the same error on the next run does not. A crash
on a check-in still hands Bob checkin.md with a `hook failed` line.
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import threading
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

CHECKIN = "Bob check-in"
NOT_NIK = (
    "<agent-message", "<cross-session", "<task-notification", "<system-reminder", "<local-command",
    "Another Claude session", "[SYSTEM", "[Cross-session", "[Request interrupted",
    "[Your previous response", "Stop hook feedback", "This session is being continued",
)
INTERVAL = timedelta(minutes=30)
QUIET = timedelta(minutes=30)
COVER_SLACK = timedelta(minutes=2)
SIGNAL_TIMEOUT = 20
MAX_CONTEXT = 6000
PROCEDURE = Path(__file__).resolve().parent.parent / "checkin.md"
DROP = {"decision": "block", "reason": "",
        "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "suppressOriginalPrompt": True}}


def now():
    return datetime.now().astimezone()


def parse_time(value):
    dt = datetime.fromisoformat(re.sub(r"([+-]\d\d)(\d\d)$", r"\1:\2", value.replace("Z", "+00:00")))
    return dt if dt.tzinfo else dt.astimezone()


def hhmm(dt):
    return dt.astimezone().strftime("%H:%M")


def run(cmd, timeout=SIGNAL_TIMEOUT):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL, text=True, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise RuntimeError("timed out")
    if proc.returncode:
        lines = (err or out).strip().splitlines()
        raise RuntimeError(lines[-1] if lines else "exit %d" % proc.returncode)
    return out


def load_state(path):
    try:
        state = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def save_state(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1))
    tmp.replace(path)


def procedure():
    return PROCEDURE.read_text() if PROCEDURE.exists() else ""


# Signals: each returns raw data; a raised exception becomes a digest line.

def rex_panes():
    own = os.environ.get("REX_BLOCK")
    panes = {}
    for session in json.loads(run(["rex", "ls", "--json"], 5))["sessions"]:
        sid = session["session_id"]
        for block in json.loads(run(["rex", "block", "ls", "-s", sid, "--json"], 5))["blocks"]:
            bid = block["block_id"]
            if bid == own:
                continue
            status = run(["rex", "block", "call", "-s", sid, "-b", bid, "program_status"], 5)
            records = [r for r in json.loads(status)["records"] if "id" not in r]
            if not records:
                continue
            state, cwd = records[0].get("state", "?"), ""
            if state == "working":
                process = json.loads(run(["rex", "block", "call", "-s", sid, "-b", bid, "process"], 5))
                cwd = (process.get("foreground") or {}).get("cwd", "")
            panes[bid] = {"name": "%s › %s" % (session["label"], block["label"]), "state": state, "cwd": cwd}
    return panes


def checkouts():
    lines = []
    for row in json.loads(run(["lager", "status", "--json"]))["rows"]:
        if row.get("found_path"):
            lines.append("%s on %s" % (row["found_path"], (row.get("branch") or {}).get("value")))
            if (row.get("changes") or {}).get("state") == "dirty":
                lines.append("%s dirty" % row["found_path"])
    return lines


def calendar(names):
    today = now().strftime("%Y-%m-%d")
    cmd = ["ical", "list", "-f", today, "-t", today, "-o", "json"] + [a for n in names for a in ("-c", n)]
    events = json.loads(run(cmd))
    return [e for e in events if not e.get("all_day") and e.get("self_status") != "declined"]


def ledger(directory):
    path = Path(directory).expanduser() / (now().strftime("%Y-%m-%d") + ".json")
    if not path.exists():
        return []
    blocks = json.loads(path.read_text())
    if not isinstance(blocks, list):
        raise ValueError("ledger is not a list")
    spans = []
    for block in blocks:
        try:
            spans.append((parse_time(block["start"]), parse_time(block["end"]), block.get("title") or "?"))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return spans


def extra(command):
    return [" ".join(line.split()) for line in run(["bash", "-o", "pipefail", "-c", command]).splitlines() if line.strip()]


def gather(jobs):
    results = {}

    def work(name, fn):
        try:
            results[name] = (fn(), None)
        except Exception as exc:  # noqa: BLE001, every failure becomes a digest line
            results[name] = (None, (str(exc) or type(exc).__name__)[:200])

    threads = [threading.Thread(target=work, args=(n, f), daemon=True) for n, f in jobs.items()]
    deadline = now() + timedelta(seconds=SIGNAL_TIMEOUT + 2)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(max(0, (deadline - now()).total_seconds()))
    return {name: results.get(name, (None, "timed out")) for name in jobs}


def meetings(events):
    return [e for e in events
            if not (e.get("notes") or "").startswith("bob") and not e.get("title", "").startswith("AFK")]


def meeting_soon(t, events):
    return [e for e in meetings(events) if t < parse_time(e["start_date"]) <= t + INTERVAL]


def meeting_ended(t, last_run, events):
    return [e for e in meetings(events) if last_run < parse_time(e["end_date"]) <= t]


def event_line(event):
    status = event.get("self_status")
    return "%s-%s %s%s" % (hhmm(parse_time(event["start_date"])), hhmm(parse_time(event["end_date"])),
                           event.get("title"), "" if status == "accepted" else " [%s]" % status)


def block_flags(t, last_run, spans, panes, roots, uncovered_before):
    """The raised block flags and the sessions no block covers now."""
    if panes is None or spans is None:
        return [], uncovered_before
    working = sorted(p["name"] for p in panes.values() if p["state"] == "working"
                     and any(p["cwd"] == r or p["cwd"].startswith(r + "/") for r in roots))
    if not working or any(start <= t and end > t + COVER_SLACK for start, end, _ in spans):
        return [], []
    ended = [s for s in spans if last_run < s[1] <= t + COVER_SLACK]
    if ended:
        _, end, title = max(ended, key=lambda span: span[1])
        return [("block-ended", "%s ended %s while %s still works" % (title, hhmm(end), ", ".join(working)))], working
    if set(working) - set(uncovered_before):
        return [("no-block", "no block covers now while %s works" % ", ".join(working))], working
    return [], working


def checkin(args, payload, state):
    t = now()
    last_run = parse_time(state["last_run"]) if state.get("last_run") else t - INTERVAL
    data = {}
    jobs = {"calendar": lambda: calendar(args.calendar)}
    last_nik = state.get("last_nik")
    if last_nik and t - parse_time(last_nik) < QUIET:
        data = gather(jobs)
        events, error = data["calendar"]
        if error is None and not meeting_soon(t, events) and not meeting_ended(t, last_run, events):
            return DROP
        jobs = {}
    jobs.update({"sessions": rex_panes, "checkouts": checkouts, "ledger": lambda: ledger(args.ledger_dir)})
    extras = [item.partition("=") for item in args.extra]
    jobs.update({name: (lambda command=command: extra(command)) for name, _, command in extras})
    data.update(gather(jobs))

    events, spans, panes = data["calendar"][0], data["ledger"][0], data["sessions"][0]
    views = {"sessions": ["%s (%s): %s" % (p["name"], bid[-6:], p["state"]) for bid, p in panes.items()]
             if panes is not None else None,
             "checkouts": data["checkouts"][0],
             "calendar": [event_line(e) for e in meetings(events)] if events is not None else None}
    views.update({name: data[name][0] for name, _, _ in extras})
    old_views = state.get("views", {})
    news = []
    for name, lines in views.items():
        if lines is not None and name in old_views:
            prev, cur = set(old_views[name]), set(lines)
            news += [(name, "%s: + %s" % (name, line)) for line in lines if line not in prev]
            news += [(name, "%s: - %s" % (name, line)) for line in old_views[name] if line not in cur]
    errors = ["%s: %s" % (name, error) for name, (_, error) in data.items() if error]
    new_errors = [e for e in errors if e not in state.get("errors", [])]

    raised = [("meeting", "%s %s starts before the next run" % (hhmm(parse_time(e["start_date"])), e["title"]))
              for e in meeting_soon(t, events or [])]
    raised += [("meeting-ended", "%s ended %s; tell Nik what waited" % (e["title"], hhmm(parse_time(e["end_date"]))))
               for e in meeting_ended(t, last_run, events or [])]
    running = [e for e in meetings(events or []) if parse_time(e["start_date"]) <= t < parse_time(e["end_date"])]
    work_flags, state["uncovered"] = block_flags(t, last_run, spans, panes, [
        str(Path(r).expanduser().resolve()) for r in args.repos_root], state.get("uncovered", []))
    raised += work_flags

    state["views"] = {name: lines if lines is not None else old_views.get(name)
                      for name, lines in views.items() if lines is not None or name in old_views}
    state["errors"] = errors
    state["last_run"] = t.isoformat()
    state["pending"] = ({"session_id": payload.get("session_id"), "flags": [n for n, _ in work_flags]}
                        if work_flags else None)
    if not news and not raised and not new_errors:
        return DROP

    head = [procedure(), "Check-in digest, %s, next run about %s." % (hhmm(t), hhmm(t + INTERVAL))]
    head += ["%s runs until %s." % (e["title"], hhmm(parse_time(e["end_date"]))) for e in running]
    if raised:
        head += ["Flags:"] + ["- %s: %s" % flag for flag in raised]
    if errors:
        head += ["Signals that failed:"] + ["- " + e for e in errors]
    text = "\n".join(head)
    if news:
        room = MAX_CONTEXT - len(text) - 160
        shown = []
        for _, line in news:
            if len(line) + 1 > room:
                break
            shown.append(line)
            room -= len(line) + 1
        cut = Counter(name for name, _ in news[len(shown):])
        if cut:
            shown.append("…and %d more: %s" % (sum(cut.values()), ", ".join("%s %d" % c for c in cut.most_common())))
        text += "\nNews since the last check-in:\n" + "\n".join(shown)
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text[:MAX_CONTEXT]}}


def prompt_mode(args, payload):
    prompt = (payload.get("prompt") or "").strip()
    state = load_state(args.state)
    if prompt == CHECKIN:
        result = checkin(args, payload, state)
    elif prompt.startswith(NOT_NIK):
        return {}
    else:
        state["last_nik"] = now().isoformat()
        if (state.get("pending") or {}).get("session_id") == payload.get("session_id"):
            state["pending"] = None
        result = {}
    save_state(args.state, state)
    return result


def checkin_turn_commands(transcript_path):
    """Bash commands of the last turn, or None when its prompt was no check-in."""
    commands = []
    with open(transcript_path) as f:
        lines = f.readlines()
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        content = entry.get("message", {}).get("content")
        if entry.get("type") == "assistant":
            for block in content or []:
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Bash":
                    commands.append(block.get("input", {}).get("command", ""))
            continue
        if entry.get("type") != "user":
            continue
        if isinstance(content, list):
            texts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
            if not texts:
                continue
            content = texts[0]
        text = (content or "").strip()
        if text == CHECKIN:
            return commands
        if entry.get("isMeta") or text.startswith(NOT_NIK):
            continue
        return None
    return None


def stop_mode(args, payload):
    if payload.get("stop_hook_active"):
        return {}
    state = load_state(args.state)
    pending = state.get("pending")
    if not pending or pending.get("session_id") != payload.get("session_id"):
        return {}
    state["pending"] = None
    save_state(args.state, state)
    commands = checkin_turn_commands(payload["transcript_path"]) if payload.get("transcript_path") else None
    if commands is None or any(re.search(r"\bical\s+(add|update)\b", c) for c in commands):
        return {}
    return {"decision": "block",
            "reason": "The check-in digest raised %s, and no `ical add` or `ical update` ran. Bring the "
                      "time blocks in line with the digest's sessions and ledger, then finish the check-in."
                      % " and ".join(pending["flags"])}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def main():
    parser = Parser(description=__doc__.split("\n")[0])
    parser.add_argument("mode", choices=("prompt", "stop"))
    parser.add_argument("--state", required=True, help="state file, outside any git repo")
    parser.add_argument("--calendar", action="append", required=True, help="calendar to read events from (repeatable)")
    parser.add_argument("--ledger-dir", required=True, help="folder of the YYYY-MM-DD.json block ledgers")
    parser.add_argument("--extra", action="append", default=[], metavar="NAME=COMMAND",
                        help="shell command whose output lines are diffed (repeatable)")
    parser.add_argument("--repos-root", action="append", default=[], metavar="DIR",
                        help="the circle's repos; only sessions under one count for block flags (repeatable)")
    mode = "stop" if sys.argv[1:2] == ["stop"] else "prompt"
    payload = None
    try:
        args = parser.parse_args()
        payload = json.load(sys.stdin)
        result = prompt_mode(args, payload) if mode == "prompt" else stop_mode(args, payload)
    except Exception as exc:  # noqa: BLE001, a crash must still let the check-in through
        result = {}
        if payload is None:
            try:
                payload = json.load(sys.stdin)
            except ValueError:
                payload = {}
        if mode == "prompt" and isinstance(payload, dict) and (payload.get("prompt") or "").strip() == CHECKIN:
            context = procedure() + "\nhook failed: " + (str(exc) or type(exc).__name__)[:200]
            result = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}
    if result or mode == "prompt":
        print(json.dumps(result))


if __name__ == "__main__":
    main()
    sys.exit(0)
