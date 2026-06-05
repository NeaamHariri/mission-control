# Mission Control — Architecture & Code Spec

Deep technical reference for *how the code works*. On-demand tier: not auto-loaded
into every session (that's `context.md`); read this when working on the scanner or
the dashboards. Altitude rule: this documents **shape, why, and where** — the code
itself is the source of truth for exact behavior.

## System shape

A local, no-install tool with two halves and no server, no build step:

```
~/Startups/*  ──►  generate.py  ──►  data.js  ──►  index.html / project.html
(real folders)     (scanner,       (window.        (static dark dashboards,
 + ~/.claude        stdlib+git)      MISSION_        opened via file://, CDN libs)
 sessions/memory)                    CONTROL)
```

- **generate.py** scans the filesystem + git + Claude session logs and writes a single `data.js`.
- **data.js** is a snapshot: `window.MISSION_CONTROL = {...}`. Never hand-edited.
- **index.html** (overview) and **project.html** (drilldown, `?id=<folder>`) read that global and render with vanilla JS + CDN libs (Chart.js, Cytoscape.js + dagre, marked.js). No bundler, no framework.

## generate.py — module map

Pure stdlib + the local `git` binary. Grouped by concern (function names are stable; read them for detail):

- **Path / identity:** `encode_claude_path()` (abs path → `~/.claude/projects/<encoded>` session dir, every non-alnum → `-`), `pretty_name()`.
- **Status note:** `parse_note()` (frontmatter + milestones/todos/summary), `find_note()` (project folder, then claude dir).
- **Claude usage:** `claude_usage()` walks `<encoded>/*.jsonl`, sums `message.usage` tokens, estimates cost via `PRICING`/`_price_for()` (cost is an *estimate* — logs have tokens, not dollars). `claude_summary()` rolls up portfolio totals + a 30-day daily series.
- **Higgsfield:** `read_higgsfield()` merges the balance snapshot (`higgsfield-usage.json`) with derived series from `read_higgsfield_tx()` (reads `higgsfield-transactions.json`; signed credits; reconstructs daily used + remaining + renewal date).
- **Knowledge:** `read_knowledge()` (journal entries + featured `architecture.md` spec + other notes; excludes generated `context.md`), `read_memory_docs()` (excerpts of `~/.claude/.../memory/*.md`), `build_digest()` + `write_digest()` (the auto-loaded `knowledge/context.md`, bounded + deterministic for cache stability).
- **Architecture:** `read_arch()` loads `<project>/tech-architecture.json` inline; `derive_tech()` is the tech-chip fallback.
- **Git:** `git_info()` (branch, dirty, ahead/behind, last commit, 30-day commit series).
- **MCPs:** `scan_mcps()` parses `claude mcp list`; `claude_account()` tags claude.ai connectors with the owning account email.
- **Structure:** `project_tree()` (shallow, expands one level for code projects), `TREE_IGNORE`.
- **Assembly:** `scan_projects()` joins all of the above per folder (spine = `~/Startups/*`, minus `EXCLUDE`), sorts by status then recency; `main()` builds the `data` dict and writes `data.js`.

## data.js schema (the contract between halves)

`window.MISSION_CONTROL`:
- `generatedAt`, `root`
- `totals` — projects/active/blocked/sessions/openTodos/repos/skills/agents/mcps + `claudeCost`/`claudeTokens`
- `usage[]` — 30-day `{date, sessions, commits}`
- `claude` — `{total, daily[]}`
- `higgsfield` — `{credits, plan, asOf, spentToday/7d/30d/Month, daily[], byMonth[], renews...}`
- `projects[]` — see below
- `skills[]`, `agents[]`, `mcps[]`

Each **project** object: `id, name, path, status, sessions, lastActive, stack, techStack[], claude, next, tags[], milestones[{label,done}], todos[], summary, memory[], memoryDocs[], knowledge{journal[],notes[],spec}, hasNote, git, skills[], agents[], tree[], arch`.

The renderers read these field names directly, so **renaming a field is a breaking change** across `generate.py` + both HTML files.

## Rendering

- **index.html:** KPI row, spend cards (Claude est. + Higgsfield), Activity chart (Chart.js), project cards (status, next, tech chips, milestones, git, claude cost), then Shared skills / Shared agents / Connected MCPs / "Keep it current" cards.
- **project.html:** header + tech chips, Knowledge base panel (journal newest-first + featured architecture spec + notes, markdown via marked.js), two-column panels (Milestones/Memory/Skills · Todos/Repository/Claude usage), Tech architecture (Cytoscape + dagre, interactive), Project structure tree. Builds its own DOM from `MISSION_CONTROL.projects.find(id)`.
- CDN libs load over the network even under `file://`; QA waits on `--networkidle`.

## Conventions & invariants

- **Stdlib only** in `generate.py` (+ `git`). No pip installs — that's the "no-install" promise.
- **Generated files are never hand-edited:** `data.js`, every `knowledge/context.md`. The source of truth is `mission-control.md` + `knowledge/journal.md` + the `*.json` inputs.
- **Determinism / cache stability:** `context.md` carries no timestamps and stable ordering so its bytes don't churn → the CLAUDE.md `@import` stays cache-warm.
- **Graceful degradation:** every optional input (note, arch JSON, knowledge folder, git, higgsfield files) is absent-safe; a missing input just drops its panel.
- **The command loop:** `/update` (note + journal → digest), `/update-arch` (architecture: diagram + this spec + CLAUDE.md brief), `/update-usage` (Higgsfield). All end by running `generate.py`.

## Gotchas

- Session-dir encoding must match Claude Code exactly, or usage/memory silently read empty.
- Claude cost is **estimated** (cache-heavy; Opus 5-min cache rate assumed) — token counts are exact, dollars are not.
- Higgsfield can't be fetched by `generate.py` (stdlib, no MCP); it needs `/update-usage` to refresh the two JSON files.
- A malformed `tech-architecture.json` silently drops the diagram panel — valid JSON only.
- `project.html` is opened with `?id=<folder>`; folders with spaces (e.g. `Flywheel Creative OS`) must be URL-encoded.

## Where to look

| Want to change… | File / function |
|---|---|
| A new per-project data field | `scan_projects()` in `generate.py` + both HTML renderers |
| Cost math | `PRICING`, `_price_for()`, `claude_usage()` |
| The auto-loaded digest | `build_digest()` / `write_digest()` |
| Knowledge panel | `read_knowledge()` + the Knowledge `<section>` in `project.html` |
| Architecture diagram | `tech-architecture.json` + the Cytoscape block in `project.html` |
| Overview cards | the markup + render blocks in `index.html` |
