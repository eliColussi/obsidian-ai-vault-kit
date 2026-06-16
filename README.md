# Obsidian AI Vault Kit

The simplest Obsidian + Claude Code setup that actually captures your work.

Point this kit at any folder on your computer and it instantly becomes an
Obsidian vault that documents itself. Work with Claude Code like you normally
would, and the vault fills in behind you: every prompt you send, every answer
Claude gives, and every file it touches lands in today's Daily note,
automatically. At the end of a long session you ask one question and get the
whole day back:

```
/what-did-i-do-today
```

Claude reconstructs the day from the vault's capture plus your git history,
writes a rich recap into the Daily note, and tells you what's still open. That's
the whole pitch. No plugins to buy, no sync service, no manual logging.

---

## What it does

Four hooks bridge your Claude Code conversation into the vault:

| When | What gets captured |
|------|--------------------|
| A session starts | Recent Daily notes are read back **into context** — last recap, open TODOs, a per-day pulse — so a blank session opens already knowing where you left off |
| You send a prompt | The prompt is timestamped into today's Daily note (editor noise like IDE tags is stripped first) |
| Claude finishes answering | Its final answer is logged as an indented `↳` reply under your prompt, so every prompt/answer pair is preserved |
| Claude writes or edits a file | The file is logged as a clickable `[[wiki-link]]`, deduped to one entry per file per day |

Pure-conversation turns (questions, strategy talk, decisions) get captured too,
not just file work. That's the part most setups miss. And because the first hook
reads the vault back at session start, recall is automatic — you don't even have
to ask.

## What's inside

| Piece | Does what |
|-------|-----------|
| `install.sh` | One command to drop it all into any folder, non-destructively |
| `.obsidian/` | Obsidian config: core plugins on, graph colored, daily notes + templates wired |
| `Templates/` | Daily, Project, Evergreen, MOC note templates |
| `Home.md` | A starter dashboard with Maps of Content |
| `.claude/hooks/obsidian-log.py` | The auto-capture hook (prompts, replies, file edits) |
| `.claude/hooks/obsidian-recall.py` | The session-start recall hook (reads recent Daily notes back into context) |
| `.claude/commands/what-did-i-do-today.md` | The end-of-day recap command |
| `.claude/settings.hooks.json` | The hook wiring (the installer merges it for you) |

---

## Install (60 seconds)

```bash
git clone https://github.com/eliColussi/obsidian-ai-vault-kit.git
cd obsidian-ai-vault-kit
```

Into a brand-new vault folder:

```bash
./install.sh ~/Desktop/my-vault
```

Into an existing project folder (merges, never overwrites your `Home.md` or
existing hooks):

```bash
./install.sh /path/to/existing/project
```

The installer is additive and idempotent: it refreshes config, seeds anything
missing, merges the hooks into `.claude/settings.json` without touching hooks
you already have, and never clobbers your content. Run it twice, nothing breaks.

Then:

1. Open Obsidian → **Open folder as vault** → select that folder.
2. Start a Claude Code session in the same folder.
3. Work. The Daily note fills itself.
4. End the day with `/what-did-i-do-today`.

---

## What to expect after setup

The first time you prompt Claude in the folder, `Daily/<today>.md` appears on
its own and starts growing as you work:

```markdown
## 💬 Prompts
- 09:14 "refactor the email parser to handle attachments"
    - ↳ 09:17 "Done. Split parse_email into parse_headers and extract_attachments…"
- 10:02 "why is the webhook failing on retries?"
    - ↳ 10:04 "The retry handler re-sends the original idempotency key, so the…"

## 🤖 Files touched
- [[src/parser|parser]]
- [[src/webhooks|webhooks]]
```

Open the graph view after a few days and you'll watch your work connect itself.
Run `/what-did-i-do-today` at the end of a session and Claude writes a recap
(TL;DR, what shipped, what's still open, suggested next steps) straight into the
Daily note.

---

## How it works (the honest version)

- **Obsidian mirrors a folder.** Anything that writes a file there shows up live —
  Claude, a script, git, Finder. No import, no sync button.
- **Claude in chat ≠ in the vault.** By default a conversation leaves no files
  behind, so it's invisible to Obsidian. The hooks fix that: `UserPromptSubmit`
  records what you asked, `Stop` records what Claude answered, and `PostToolUse`
  records what changed on disk.
- **Recall runs in reverse.** `SessionStart` reads the most recent Daily notes
  back into context when a session opens, so Claude starts already knowing where
  you left off — automatic recall, no DB, just the markdown it already wrote.
- **You do NOT need a PreToolUse hook.** It fires before a file exists, so it has
  nothing to save. This kit uses exactly the four events above.

The capture is deliberately lean: prompts and replies are clipped to one line,
files are deduped (one line per file per day, not one per keystroke), and the
hook exits silently on any error so it can never block Claude. The Daily note
stays readable instead of becoming noise.

Privacy note: everything is captured to plain markdown **on your own machine**,
inside the vault folder. Nothing is sent anywhere.

---

## Requirements

- [Obsidian](https://obsidian.md) (free)
- [Claude Code](https://claude.com/claude-code)
- `python3` (preinstalled on macOS; any 3.x works)

---

## License

MIT. Use it, ship it, set it up for your clients.
