---
type: reference
tags:
  - reference
  - playbook
---

# 🧠 How this vault works

Back to [[Home]].

## The one idea

**Folders are storage. Links are the brain.**

Obsidian adds a web of `[[wiki-links]]` and a few entry-point maps on top of plain
markdown files. You never reorganize folders to find things again. You follow links
and the local graph. No database, no vectorization, no import step.

## The AI bridge (what makes this kit different)

Obsidian mirrors a folder. The included Claude Code hooks turn the *conversation*
into files in that folder:

- **Every prompt you send** is logged to today's Daily note.
- **Every answer Claude gives** is logged as an indented `↳` reply under your prompt.
- **Every file Claude writes or edits** is logged (deduped, one entry per file).

So at the end of a session you ask `/what-did-i-do-today` and Claude reconstructs
the day from the vault's own capture plus git history, then writes a rich recap
back into the Daily note. The vault documents itself.

## Structure

| Piece | What it is |
|-------|-----------|
| [[Home]] | The note you open every day. Links to your maps. |
| `MOCs/` | Maps of Content, one per area of your work. Hand-curated. |
| `Templates/` | Daily, Project, Evergreen, MOC. |
| `Daily/` | One note per day. Auto-captured. |
| `.claude/` | The hook (`obsidian-log.py`) + the `/what-did-i-do-today` command. |
| `.obsidian/` | Config: enabled plugins, graph colors, daily-notes + templates. |

## Daily workflow

1. **Capture** → today's Daily note (`⌘P` → "Daily notes: Open today"). The hook
   fills it as you and Claude work.
2. **Connect** → promote real ideas to their own notes and `[[link]]` them.
3. **Curate** → every note earns its place by being linked from a MOC.
4. **Recap** → end the day with `/what-did-i-do-today`.

Three keystrokes: `⌘O` open any note, `⌘E` edit/preview, `⌘P` → "Graph view".

## First open

1. Obsidian → **Open folder as vault**
2. Select this folder
3. Trust it, open [[Home]]
