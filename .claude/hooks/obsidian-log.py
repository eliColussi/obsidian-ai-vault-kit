#!/usr/bin/env python3
"""
Obsidian auto-capture hook.

Bridges the gap between the Claude conversation and the Obsidian vault:
every prompt you send and every file Claude writes/edits gets recorded in
today's Daily note, so at the end of a session you can ask
"What did I do today?" and get a rich answer from the vault itself.

Wired to three events in .claude/settings.json:
  - UserPromptSubmit  -> logs the prompt under "## 💬 Prompts"
  - Stop              -> logs Claude's final answer as an indented "↳" reply
                         under the same section, pairing prompt + output
  - PostToolUse       -> logs file mutations under "## 🤖 Files touched"

Design rules (keep it lean, never noisy):
  - Files are DEDUPED: each file appears once per day, not once per edit.
  - IDE-injected tags (<ide_opened_file>, <ide_selection>) are stripped from
    prompts before snippetting, so editor noise never eats the real question.
  - Never block Claude. Any error -> exit 0 silently.
  - Print nothing to stdout (UserPromptSubmit stdout is injected into context).
  - Only logs file-mutating tools; ignores Read/Grep/Glob/Bash/etc.
  - Writes with plain file I/O, so it never re-triggers PostToolUse.
"""
import sys, os, re, json, datetime

MUTATING_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
PROMPTS_HEADER = "## 💬 Prompts"
ACTIVITY_HEADER = "## 🤖 Files touched"
SNIPPET_LEN = 200

# Editor/harness metadata injected ahead of the user's real words.
INJECTED_TAG_RE = re.compile(
    r"<(ide_opened_file|ide_selection|system-reminder)>.*?</\1>",
    re.DOTALL,
)


def snippet(text):
    text = " ".join(text.split())
    return text[:SNIPPET_LEN] + ("…" if len(text) > SNIPPET_LEN else "")


def daily_path(cwd, today):
    return os.path.join(cwd, "Daily", f"{today}.md")


def ensure_daily(path, today):
    """Create today's Daily note from a minimal skeleton if it doesn't exist."""
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    skeleton = (
        "---\n"
        "type: daily\n"
        f"date: {today}\n"
        "tags:\n"
        "  - daily\n"
        "---\n\n"
        f"# {today}\n\n"
        "## 🎯 Today\n- [ ] \n\n"
        f"{PROMPTS_HEADER}\n\n"
        f"{ACTIVITY_HEADER}\n\n"
        "---\n"
        "[[Home]]\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(skeleton)


def read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def section_bounds(lines, header):
    """Return (start, end) line indices of a section body (exclusive of header),
    or (None, None) if the header is absent."""
    start = next((i for i, l in enumerate(lines) if l.rstrip() == header), None)
    if start is None:
        return None, None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].lstrip().startswith("## ") or lines[j].rstrip() == "---":
            end = j
            break
    return start, end


def append_to_section(path, header, line, dedupe_substr=None):
    """Append `line` to a section. If dedupe_substr is given and already present
    anywhere in that section, do nothing. Creates the section before the footer
    '---' if missing."""
    lines = read_lines(path)
    start, end = section_bounds(lines, header)

    if start is None:
        footer = next((i for i, l in enumerate(lines) if l.rstrip() == "---" and i > 5), None)
        block = [f"{header}\n", f"{line}\n", "\n"]
        if footer is not None:
            lines[footer:footer] = block
        else:
            lines.extend(["\n"] + block)
        write_lines(path, lines)
        return

    if dedupe_substr is not None:
        body = "".join(lines[start + 1:end])
        if dedupe_substr in body:
            return  # already recorded today

    # Insert at end of the section body (chronological order).
    insert_at = end
    while insert_at - 1 > start and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    lines.insert(insert_at, f"{line}\n")
    write_lines(path, lines)


def last_assistant_text(transcript_path):
    """Pull the final assistant text message from a Claude Code transcript (.jsonl)."""
    last = None
    with open(transcript_path, "r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "assistant":
                continue
            content = (entry.get("message") or {}).get("content") or []
            texts = [
                b.get("text", "") for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            ]
            joined = " ".join(t.strip() for t in texts if t.strip())
            if joined:
                last = joined
    return last


def vault_link(cwd, file_path):
    """Make a wiki-link (no extension) relative to the vault root."""
    try:
        rel = os.path.relpath(file_path, cwd)
    except ValueError:
        rel = file_path
    name = os.path.splitext(os.path.basename(rel))[0]
    rel_noext = os.path.splitext(rel)[0]
    return rel_noext, f"[[{rel_noext}|{name}]]"


def main():
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}

    # Vault root: prefer the project dir Claude Code exports, so the Daily note
    # always lands at the vault root no matter the shell's current directory.
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    event = data.get("hook_event_name", "")
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    hhmm = now.strftime("%H:%M")
    path = daily_path(cwd, today)

    if event == "UserPromptSubmit":
        prompt = INJECTED_TAG_RE.sub("", data.get("prompt") or "").strip()
        if not prompt:
            return
        ensure_daily(path, today)
        append_to_section(path, PROMPTS_HEADER, f'- {hhmm} "{snippet(prompt)}"')

    elif event == "Stop":
        tp = data.get("transcript_path")
        if not tp or not os.path.exists(tp):
            return
        reply = last_assistant_text(tp)
        if not reply:
            return
        ensure_daily(path, today)
        append_to_section(path, PROMPTS_HEADER, f'    - ↳ {hhmm} "{snippet(reply)}"')

    elif event == "PostToolUse":
        tool = data.get("tool_name", "")
        if tool not in MUTATING_TOOLS:
            return
        fp = (data.get("tool_input") or {}).get("file_path") \
            or (data.get("tool_input") or {}).get("notebook_path")
        if not fp:
            return
        norm = os.path.normpath(fp)
        if os.sep + "Daily" + os.sep in norm or os.sep + ".obsidian" + os.sep in norm:
            return
        rel_noext, link = vault_link(cwd, fp)
        ensure_daily(path, today)
        # Dedupe by the file's relative path so each file appears once per day.
        append_to_section(path, ACTIVITY_HEADER, f"- {link}", dedupe_substr=f"[[{rel_noext}|")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # never block Claude
    sys.exit(0)
