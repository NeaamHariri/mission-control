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
#
# Engine selector (which dashboard(s) to set up):
#   ./setup.sh            auto  — Claude, plus Bob MC if a ~/bob projects folder exists (default)
#   ./setup.sh claude     Claude only — build data.js, never cascade to Bob
#   ./setup.sh bob        Bob MC only — build data-bob.js; skip the Claude /update* commands
#   ./setup.sh both       force both dashboards regardless of folder detection

set -euo pipefail

MODE="${1:-auto}"
case "$MODE" in
  auto|claude|bob|both) ;;
  -h|--help)
    echo "Usage: ./setup.sh [auto|claude|bob|both]"; exit 0 ;;
  *)
    echo "✗ Unknown mode '$MODE'. Use: auto | claude | bob | both" >&2; exit 1 ;;
esac

MC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$MC_DIR/.." && pwd)"
CMD_DIR="$HOME/.claude/commands"          # Claude Code slash commands
BOB_CMD_DIR="$HOME/.bob/commands"         # IBM Bob slash commands

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }

bold "Mission Control setup"
echo "  mode           : $MODE"
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

# 2. Install the slash commands ---------------------------------------------
# Claude Code commands (commands/*.md) → ~/.claude/commands/ — for every mode
# except bob-only. IBM Bob commands (commands-bob/*.md) → ~/.bob/commands/ — for
# bob and both. Same markdown+frontmatter format; each app reads its own folder.
shopt -s nullglob

# Claude Code commands — installed unless bob-only.
if [ "$MODE" = "bob" ]; then
  echo "  • bob-only mode — skipping Claude /update* commands (they live in ~/.claude/commands)"
else
  mkdir -p "$CMD_DIR"
  installed=0
  for f in "$MC_DIR"/commands/*.md; do
    name="$(basename "$f")"
    # Rewrite ~/Startups → your actual projects root if it differs.
    if [ "$ROOT" = "$HOME/Startups" ]; then
      cp "$f" "$CMD_DIR/$name"
    else
      sed "s#~/Startups#$ROOT#g; s#\$HOME/Startups#$ROOT#g" "$f" > "$CMD_DIR/$name"
    fi
    ok "installed /$(basename "$name" .md) → Claude Code"
    installed=$((installed + 1))
  done
  [ "$installed" -gt 0 ] || echo "  • no command files found in $MC_DIR/commands/"
fi

# IBM Bob commands — installed for bob, both, and auto-when-a-bob-folder-exists
# (so the default setup is turnkey for Bob users). __MC_DIR__ is substituted with
# this checkout's path so the commands can call the right generate.py.
if [ "$MODE" = "bob" ] || [ "$MODE" = "both" ] || { [ "$MODE" = "auto" ] && [ -d "$HOME/bob projects" ]; }; then
  mkdir -p "$BOB_CMD_DIR"
  binstalled=0
  for f in "$MC_DIR"/commands-bob/*.md; do
    name="$(basename "$f")"
    sed "s#__MC_DIR__#$MC_DIR#g" "$f" > "$BOB_CMD_DIR/$name"
    ok "installed /$(basename "$name" .md) → IBM Bob"
    binstalled=$((binstalled + 1))
  done
  [ "$binstalled" -gt 0 ] || echo "  • no command files found in $MC_DIR/commands-bob/"
fi
echo

# 3. Generate the dashboard data --------------------------------------------
# claude → data.js only (cascade suppressed); bob → data-bob.js only;
# both → both dashboards forced; auto → data.js, cascading to data-bob.js when
# a ~/bob projects folder exists.
case "$MODE" in
  claude)
    bold "Scanning projects and writing data.js (Claude only)…"
    MC_NO_CASCADE=1 python3 "$MC_DIR/generate.py" ;;
  bob)
    bold "Scanning ~/bob projects and writing data-bob.js (Bob MC only)…"
    MC_ENGINE=bob python3 "$MC_DIR/generate.py" ;;
  both)
    bold "Scanning projects and writing data.js + data-bob.js (both)…"
    MC_NO_CASCADE=1 python3 "$MC_DIR/generate.py"
    MC_ENGINE=bob python3 "$MC_DIR/generate.py" ;;
  *)
    bold "Scanning projects and writing data.js…"
    python3 "$MC_DIR/generate.py" ;;
esac
echo

# 4. Next steps -------------------------------------------------------------
bold "Done. Open the dashboard:"
if [ "$MODE" = "bob" ]; then
  echo "  open \"$MC_DIR/index.html?engine=bob\"   # Bob MC — IBM Bob projects + spend"
  echo
  bold "To start tracking a Bob project:"
  echo "  1. Put your projects under ~/bob projects/ — usage is read from IBM Bob's task history."
  echo "  2. (Optional) add a mission-control.md note to a project folder for status/milestones/todos."
  echo "  3. Inside IBM Bob, run /update (or /update-arch) — now installed in ~/.bob/commands/."
  echo "     Or refresh from a terminal: MC_ENGINE=bob python3 \"$MC_DIR/generate.py\"."
else
  echo "  open \"$MC_DIR/index.html\""
  if [ "$MODE" = "both" ] || { [ "$MODE" = "auto" ] && [ -d "$HOME/bob projects" ]; }; then
    ok "Bob MC dashboard also built"
    echo "  open \"$MC_DIR/index.html?engine=bob\"   # IBM Bob projects + spend"
    echo "  (or use the “Switch to Bob MC” link in the sidebar)"
  fi
  echo
  bold "To start tracking a project:"
  echo "  1. Add a mission-control.md note to any folder under $ROOT (see guide.html → Folders & files)."
  echo "  2. Run /update at the end of a working session to refresh status + journal."
  if [ "$MODE" = "claude" ]; then
    echo "     (Claude-only mode: /update builds data.js and won't touch Bob MC.)"
  else
    echo "     (/update re-runs generate.py, which also refreshes Bob MC if present.)"
  fi
  echo "  3. Re-run ./setup.sh after a git pull to refresh the commands."
fi
echo
echo "Full guide: open \"$MC_DIR/guide.html\""
