#!/usr/bin/env bash
#
# Mission Control — one-command setup.
#
# Run this once after cloning the repo into your projects folder, e.g.:
#   cd ~/Startups            # the folder that holds all your projects
#   git clone <repo-url> mission-control
#   cd mission-control && ./setup.sh
#
# It installs the /update* slash commands, generates the dashboard data, and
# tells you what to do next. Safe to re-run (idempotent) after a `git pull`.

set -euo pipefail

MC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$MC_DIR/.." && pwd)"
CMD_DIR="$HOME/.claude/commands"

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }

bold "Mission Control setup"
echo "  projects root  : $ROOT"
echo "  dashboard dir  : $MC_DIR"
echo

# 1. Dependencies -----------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "✗ python3 is required but not found. Install Python 3 and re-run." >&2
  exit 1
fi
ok "python3 found ($(python3 --version 2>&1))"
command -v git >/dev/null 2>&1 && ok "git found" || echo "  • git not found — git panels will be empty (optional)"
echo

# 2. Install the /update* slash commands ------------------------------------
# Source of truth lives in this repo's commands/ folder; we copy them into
# ~/.claude/commands/ so they work in any session. If your projects root isn't
# ~/Startups, the paths inside each command are rewritten to match.
mkdir -p "$CMD_DIR"
shopt -s nullglob
installed=0
for f in "$MC_DIR"/commands/*.md; do
  name="$(basename "$f")"
  if [ "$ROOT" = "$HOME/Startups" ]; then
    cp "$f" "$CMD_DIR/$name"
  else
    sed "s#~/Startups#$ROOT#g; s#\$HOME/Startups#$ROOT#g" "$f" > "$CMD_DIR/$name"
  fi
  ok "installed /$(basename "$name" .md)"
  installed=$((installed + 1))
done
[ "$installed" -gt 0 ] || echo "  • no command files found in $MC_DIR/commands/"
echo

# 3. Generate the dashboard data --------------------------------------------
bold "Scanning projects and writing data.js…"
python3 "$MC_DIR/generate.py"
echo

# 4. Next steps -------------------------------------------------------------
bold "Done. Open the dashboard:"
echo "  open \"$MC_DIR/index.html\""
echo
bold "To start tracking a project:"
echo "  1. Add a mission-control.md note to any folder under $ROOT (see guide.html → Folders & files)."
echo "  2. Run /update at the end of a working session to refresh status + journal."
echo "  3. Re-run ./setup.sh after a git pull to refresh the commands."
echo
echo "Full guide: open \"$MC_DIR/guide.html\""
