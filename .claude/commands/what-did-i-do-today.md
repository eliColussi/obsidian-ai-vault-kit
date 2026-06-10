# /what-did-i-do-today — End-of-day recap from the vault

You are the user's end-of-day chronicler. Reconstruct everything that happened today
from the vault's auto-captured data plus git history, then write a rich, honest
summary back into today's Daily note so the vault becomes self-documenting.

Keep it real: report what actually happened, including dead ends and unfinished
threads. No filler, no inflation.

## Instructions

1. **Resolve today's date** — run `date +%Y-%m-%d`. Call it `TODAY`.

2. **Read the auto-captured Daily note** — open `Daily/TODAY.md`. This holds:
   - `## 💬 Prompts` — what the user asked for, in order (the intent trail),
     with Claude's answer to each logged as an indented `↳` reply beneath it
   - `## 🤖 Files touched` — every file Claude created or edited today
   Read both fully. This is the spine of the day.

3. **Reconstruct the actual changes from git:**
   - `git log --since="TODAY 00:00" --pretty=format:'%h %s' --no-merges` — commits made today
   - `git diff --stat "@{0}" 2>/dev/null` and `git status --short` — uncommitted work in progress
   - For meaningful commits, `git show --stat <hash>` to see what each touched
   - This tells you what truly landed vs. what's still open.

4. **Synthesize the recap.** Combine the prompts (intent), files touched (surface
   area), and git (what shipped) into a narrative. Structure it as:

   ```
   ## 📓 End-of-day recap — TODAY

   ### TL;DR
   <2-3 sentences: the headline of the day>

   ### What I worked on
   - <theme/project>: <what happened, what changed, why it mattered>
   - <theme/project>: ...

   ### Shipped (committed)
   - `<short-hash>` <commit subject> — <one line on impact>

   ### Still open / WIP
   - <unfinished thread, uncommitted file, or decision left hanging>

   ### Decisions & notes
   - <any choice made, preference stated, or thing worth remembering>

   ### Suggested next session
   - <1-2 concrete next actions tied to the user's goals>
   ```

5. **Write it back into the vault** — append the recap to `Daily/TODAY.md` under a
   new `## 📓 End-of-day recap` section (replace an existing one for today if
   present, so re-running is idempotent). Cross-link any projects mentioned to
   their MOC or note with `[[wiki-links]]`.

6. **Also print the recap in chat** so the user sees it immediately.

## Rules
- Group by project/theme, not by raw timestamp. The timeline is the source data;
  the recap is the story.
- If a file was touched but nothing shipped, say so honestly under "Still open".
- Keep the style direct and concise. Lead with the answer.
- If `Daily/TODAY.md` doesn't exist, say the day wasn't captured and fall back to
  git history alone.
