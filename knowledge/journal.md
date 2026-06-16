# Mission Control — Session Journal

Append-only log of what happened each session. Newest entry on top. The dashboard
reads this (recent entries first) and `/update` both consults it for context and
appends a new entry at the end of a session.

## 2026-06-09 — Pending-changes panel + porcelain parse fix

- Added a **Pending changes** panel to `project.html` (right column, under Repository): lists uncommitted files (status-colored badge + path) and unpushed commits (hash + subject), with an `in sync` / no-remote empty state. A per-project "what's staged for the next push/version" view.
- Extended `git_info()` in `generate.py` to collect `dirtyFiles[]` (capped 50) and `unpushedCommits[]` (`@{u}..HEAD`, capped 30) on top of the existing dirty/ahead counts; documented the `git` sub-object schema.
- Fixed a latent bug: `_git()` does `stdout.strip()`, which trims the leading space off the **first** `git status --porcelain` line — fixed-offset slicing dropped the first char of the first filename ("README.md"→"EADME.md"). Switched to whitespace-splitting. Captured as a spec/brief gotcha.
- Verified live in the browser preview (added `.claude/launch.json` for a static server); confirmed both subsections render. Ran `/update-arch` to refresh the brief + spec (diagram unchanged — work sits inside the existing git→scanner→data.js→project flow).

## 2026-06-09 — /archive command + compact archived cards

- Added a new **`/archive`** slash command (`commands/archive.md`, also installed to `~/.claude/commands/`) — mirrors the `/update*` family: confirms, sets `status: archived`, preserves all milestones/todos/summary, appends a dated journal entry, regenerates `data.js`. Never deletes; resume via `/update` → `active`. README command table updated (now lists 5 commands).
- First real run: **archived Raqib** (`01_Raqib_Fintech`) — status → archived, +1 journal entry noting the resume path (AMAD 2026 registration verify + the saved revision plan).
- UI: archived projects now render as a **compact card** on the overview (`index.html`) — accent bar + name + status pill only, dimmed to ~72% (full on hover), `align-self:start` so it doesn't stretch to match taller neighbors. Presentation-only; renderer branches on `status==='archived'` and returns early.
- Next: still the launch story post; the archive work was a side feature surfaced this session.

## 2026-06-05 — Open-sourced + launch plan (positioning around project sprawl)

- Open-sourced on GitHub: github.com/NeaamHariri/mission-control (MIT). Added README (feature-led pitch), CONTRIBUTING, `setup.sh` (one-command install, auto-detects projects root via `HERE.parent`/`MC_ROOT`), `.gitignore` (keeps personal data out), `commands/` (the 4 `/update*` files travel with the clone), hero PNG + a sanitized demo tour GIF.
- Added **News** + **Best Practices** pages and a **/update-news** command (data-driven via `claude-news.json`).
- Competitor scan: the "Claude Code usage tracker" space is saturated (ccusage, 8k-star monitor); the **project-management + memory** space is empty. Repositioned the whole pitch around the real wedge — **AI ideas-explosion → project sprawl → focus** ("Claude gave you an ideas explosion; Mission Control helps you finish them"), memory demoted to a supporting pillar.
- Goal clarified: solve a real problem + build personal brand (not revenue, not the star-gated free-Max program — 5k stars by Jun 30 isn't realistic for a day-old repo). Chose plan **c**: organic, brand-first growth.
- Captured the launch plan as todos: publish the story post (today), dogfood ~1 week, Show HN + r/ClaudeAI, then awesome-claude-code (Tooling › General, web-UI only — no gh, ≥1 week age) + plugin marketplace, plus an ongoing build-in-public cadence.
- Next: publish the launch story post; let the repo age a week before the Show HN.

## 2026-06-04 — Auto-loaded digest + tiered tech knowledge

- Shipped the auto-loaded context digest: `generate.py` builds a bounded, deterministic `knowledge/context.md` (status/next/todos + last 2–3 journal entries); wired `@knowledge/context.md` into all 8 projects' CLAUDE.md so sessions start informed and cache-warm. Created a minimal CLAUDE.md for Flywheel Creative OS (it had none).
- Built two-tier **tech knowledge**: an always-on architecture brief in CLAUDE.md + an on-demand `knowledge/architecture.md` deep spec. `read_knowledge()` features the spec (full body) and `project.html` renders it in a collapsible block; the spec stays out of the digest so it costs nothing per session.
- Piloted the tech spec on Mission Control itself (module map, data.js schema, render pipeline, gotchas). Expanded `/update-arch` to maintain all three tiers (diagram + brief + spec) with an altitude rule (shape/why/where, never line-level).
- Verified renewal dates were already live on both spend cards (Claude Jun 11, Higgsfield Jun 28) — checked that milestone off.
- Next: run `/update-arch` inside Crclen + Flywheel Creative OS to give the real codebases their tech docs; then a SessionEnd hook to auto-run generate.py.

## 2026-06-04 — Knowledge base + journal-aware /update

- Added a per-project `knowledge/` convention (plain markdown, travels with the repo): `journal.md` (this file) plus free-form notes.
- `generate.py` now reads the knowledge folder (`read_knowledge`) and the *contents* of Claude Code memory files (`read_memory_docs`), not just filenames.
- `project.html` gains a Knowledge panel (recent journal + notes, markdown-rendered) and the Memory panel now shows excerpts.
- Decision: no Obsidian dependency — the format is Obsidian-friendly, but the dashboard is the viewer.
- `/update` extended to read recent journal + memory first, then append a dated entry.
- Next: wire subscription renewal dates onto the Claude + Higgsfield spend cards.

## 2026-06-03 — Usage & spend layer + end-of-session command suite

- Added estimated Claude Code cost (from session logs) and Higgsfield daily-used / remaining credits (derived from a saved transaction history).
- Each project now shows labelled tech-stack chips; Connected MCPs show the claude.ai account they're authorized under.
- Built three commands: `/update` (status note), `/update-arch` (tech-architecture.json), `/update-usage` (Higgsfield refresh), each documented in a "Keep it current" card.
- Decision: derive renewal dates automatically (Claude from the Stripe anchor, Higgsfield from the latest subscription grant) rather than hand-entering them.
- Confirmed hooks can auto-run `generate.py` (mechanical) but cannot perform the judgment half of `/update`.
