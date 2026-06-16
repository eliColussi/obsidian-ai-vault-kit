#!/usr/bin/env python3
"""
Obsidian session-start recall hook.

The counterpart to obsidian-log.py. Where that hook WRITES the day into the
vault, this one READS the vault back at the start of every session so Claude
opens already knowing where you left off — no need to ask "what did I do?".

Wired to SessionStart in .claude/settings.json. Its stdout is injected into
Claude's context, so it prints a compact "Recent vault activity" briefing built
from the most recent Daily notes:
  - the latest End-of-day recap TL;DR (if /what-did-i-do-today was run)
  - still-open checkboxes ("- [ ]") across recent days
  - a one-line pulse per recent day (how many prompts, how many files touched)

Design rules (mirror obsidian-log.py):
  - Lean and bounded: only the last few days, todos capped, recap clipped.
  - Never block Claude. Any error -> print nothing, exit 0.
  - Plain file I/O only. Read-only; never writes to the vault.
  - Silent when there's nothing to say (fresh vault -> no noise).
"""
import sys, os, re, json, glob, datetime

RECENT_DAYS = 3          # how many of the most recent Daily notes to summarize
MAX_TODOS = 12           # cap open checkboxes surfaced across those days
RECAP_CLIP = 400         # chars of the latest recap TL;DR to include
DATED_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\.md$")


def recent_daily_files(daily_dir):
    """Most-recent-first list of (date, path) for date-named Daily notes."""
    out = []
    for p in glob.glob(os.path.join(daily_dir, "*.md")):
        m = DATED_RE.search(os.path.basename(p))
        if m:
            out.append((m.group(1), p))
    out.sort(key=lambda t: t[0], reverse=True)
    return out


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def section_body(text, header):
    """Return the lines of a '## header' section, up to the next '## ' or '---'."""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip() == header), None)
    if start is None:
        return []
    body = []
    for l in lines[start + 1:]:
        s = l.strip()
        if s.startswith("## ") or s == "---":
            break
        body.append(l)
    return body


def open_todos(text):
    """Unchecked checkboxes anywhere in the note, trimmed, non-empty only."""
    todos = []
    for l in text.splitlines():
        m = re.match(r"\s*-\s*\[ \]\s*(.+\S)\s*$", l)
        if m:
            todos.append(m.group(1).strip())
    return todos


def latest_recap_tldr(files):
    """First TL;DR found scanning recent notes newest-first."""
    for _, path in files:
        try:
            text = read(path)
        except Exception:
            continue
        lines = text.splitlines()
        idx = next((i for i, l in enumerate(lines)
                    if l.strip().lower().startswith("### tl;dr")), None)
        if idx is None:
            continue
        chunk = []
        for l in lines[idx + 1:]:
            s = l.strip()
            if s.startswith("#") or s == "---":
                break
            if s:
                chunk.append(s)
        if chunk:
            joined = " ".join(chunk)
            return joined[:RECAP_CLIP] + ("…" if len(joined) > RECAP_CLIP else "")
    return None


def pulse(text):
    """One-line activity count for a note: prompts asked, files touched."""
    prompts = sum(1 for l in section_body(text, "## 💬 Prompts")
                  if l.lstrip().startswith("- ") and "↳" not in l)
    files = sum(1 for l in section_body(text, "## 🤖 Files touched")
                if l.lstrip().startswith("- "))
    bits = []
    if prompts:
        bits.append(f"{prompts} prompt{'s' if prompts != 1 else ''}")
    if files:
        bits.append(f"{files} file{'s' if files != 1 else ''} touched")
    return ", ".join(bits)


def main():
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    daily_dir = os.path.join(cwd, "Daily")
    if not os.path.isdir(daily_dir):
        return

    files = recent_daily_files(daily_dir)
    if not files:
        return
    recent = files[:RECENT_DAYS]

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    lines = []

    tldr = latest_recap_tldr(files)
    if tldr:
        lines.append(f"**Last recap:** {tldr}")
        lines.append("")

    todos, seen = [], set()
    for _, path in recent:
        try:
            text = read(path)
        except Exception:
            continue
        for t in open_todos(text):
            if t not in seen:
                seen.add(t)
                todos.append(t)
    if todos:
        lines.append("**Open items (from recent days):**")
        for t in todos[:MAX_TODOS]:
            lines.append(f"- [ ] {t}")
        if len(todos) > MAX_TODOS:
            lines.append(f"- …and {len(todos) - MAX_TODOS} more")
        lines.append("")

    pulses = []
    for date, path in recent:
        try:
            p = pulse(read(path))
        except Exception:
            p = ""
        label = f"{date} (today)" if date == today else date
        pulses.append(f"- {label}: {p or 'logged'}")
    if pulses:
        lines.append("**Recent days:**")
        lines.extend(pulses)
        lines.append("")

    if not lines:
        return

    print("📓 Recent vault activity (auto-recalled from Daily/ notes — "
          "the user can ask \"what did I do on <date>?\" for any day's full note):")
    print()
    print("\n".join(lines).rstrip())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # never block Claude
    sys.exit(0)
