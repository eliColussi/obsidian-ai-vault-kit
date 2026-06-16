#!/usr/bin/env bash
#
# Obsidian AI Vault Kit — installer
# Drops the vault scaffold + auto-capture hooks into any folder, non-destructively.
#
# Usage:
#   ./install.sh /path/to/your/vault     # install into a target folder
#   ./install.sh                         # install into the current directory
#
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$PWD}"

if [ "$KIT" = "$TARGET" ]; then
  echo "Refusing to install the kit into itself. Pass a target folder."
  exit 1
fi

echo "Installing Obsidian AI Vault Kit"
echo "  from: $KIT"
echo "  into: $TARGET"
mkdir -p "$TARGET"

# --- 1. Obsidian config + scaffolding (config always refreshed; content never clobbered) ---
mkdir -p "$TARGET/.obsidian" "$TARGET/Templates" "$TARGET/MOCs" "$TARGET/Daily" \
         "$TARGET/.claude/hooks" "$TARGET/.claude/commands"

cp "$KIT/.obsidian/"*.json "$TARGET/.obsidian/"
cp "$KIT/Templates/"*.md   "$TARGET/Templates/"
cp "$KIT/.claude/hooks/obsidian-log.py"              "$TARGET/.claude/hooks/"
cp "$KIT/.claude/hooks/obsidian-recall.py"           "$TARGET/.claude/hooks/"
cp "$KIT/.claude/commands/what-did-i-do-today.md"    "$TARGET/.claude/commands/"
[ -f "$TARGET/Daily/.gitkeep" ] || touch "$TARGET/Daily/.gitkeep"
[ -f "$TARGET/MOCs/.gitkeep" ]  || touch "$TARGET/MOCs/.gitkeep"

# Home.md: only seed it if the vault doesn't already have one.
if [ ! -f "$TARGET/Home.md" ]; then
  cp "$KIT/Home.md" "$TARGET/Home.md"
  echo "  + Home.md (seeded)"
else
  echo "  = Home.md already exists, left untouched"
fi

# OBSIDIAN-SETUP.md: ship the playbook if absent.
if [ ! -f "$TARGET/OBSIDIAN-SETUP.md" ] && [ -f "$KIT/OBSIDIAN-SETUP.md" ]; then
  cp "$KIT/OBSIDIAN-SETUP.md" "$TARGET/OBSIDIAN-SETUP.md"
fi

# --- 2. Merge hook config into .claude/settings.json (additive, never destructive) ---
python3 - "$TARGET" "$KIT" <<'PY'
import json, os, sys
target, kit = sys.argv[1], sys.argv[2]
sp = os.path.join(target, ".claude", "settings.json")
snippet = json.load(open(os.path.join(kit, ".claude", "settings.hooks.json")))["hooks"]

settings = {}
if os.path.exists(sp):
    try:
        settings = json.load(open(sp))
    except Exception:
        settings = {}

hooks = settings.setdefault("hooks", {})
def has_cmd(entries, cmd):
    for e in entries:
        for h in e.get("hooks", []):
            if h.get("command") == cmd:
                return True
    return False

for event, entries in snippet.items():
    bucket = hooks.setdefault(event, [])
    for entry in entries:
        cmd = entry["hooks"][0]["command"]
        if not has_cmd(bucket, cmd):
            bucket.append(entry)

json.dump(settings, open(sp, "w"), indent=2)
open(sp, "a").write("\n")
print("  ~ merged hooks into .claude/settings.json")
PY

# --- 3. Gitignore the per-machine Obsidian cache ---
GI="$TARGET/.gitignore"
if ! grep -q ".obsidian/workspace.json" "$GI" 2>/dev/null; then
  {
    echo ""
    echo "# Obsidian per-machine cache"
    echo ".obsidian/workspace.json"
    echo ".obsidian/workspace-mobile.json"
    echo ".obsidian/cache"
  } >> "$GI"
  echo "  ~ updated .gitignore"
fi

echo ""
echo "Done. Next:"
echo "  1. Open Obsidian → 'Open folder as vault' → select: $TARGET"
echo "  2. Start a Claude Code session in that folder."
echo "  3. At day's end, run: /what-did-i-do-today"
