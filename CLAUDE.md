# Mission Control

Current working context (auto-generated digest — status, next action, recent journal):

@knowledge/context.md

This is the command center for all my Claude Code projects, skills, agents, memory, usage, milestones and todos. It is **local and no-install**: a Python scan script + a static dark dashboard, plus the session behavior below.

## What lives here

| File | Purpose |
|------|---------|
| `setup.sh` | One-command installer — installs the `/update*` commands into `~/.claude/commands/`, runs `generate.py`, prints next steps. Idempotent; re-run after `git pull`. |
| `README.md` | Open-source front door — quick start (clone into your projects folder → `./setup.sh`), what it does, the commands. |
| `commands/` | Source-of-truth copies of the slash commands (`/update`, `/update-arch`, `/update-usage`, `/update-news`, `/archive`), so they ship with a clone. `setup.sh` installs every `commands/*.md` (rewriting paths if the projects root isn't `~/Startups`). |
| `generate.py` | Scans the projects root → writes `data.js`. Stdlib + local `git`. Root auto-detected as the checkout's parent folder (override with `MC_ROOT`). |
| `data.js` | Generated snapshot (`window.MISSION_CONTROL`). Never hand-edit; git-ignored (personal data). |
| `index.html` | Overview dashboard — KPIs, activity chart, project grid, shared skills/agents. |
| `project.html` | Per-project drilldown (`project.html?id=<folder>`). |
| `guide.html` | Static docs page — how Mission Control works, folder/file structure, daily workflow, and a setup guide for replicating it elsewhere. Linked from the dashboard sidebar ("How it works"); no `data.js` dependency. |
| `news.html` | Claude News page — latest Anthropic/Claude releases, events calendar (upcoming highlighted), and free tutorials. Data-driven: reads `data.js` → `news` (from `claude-news.json`). |
| `best-practices.html` | Tips &amp; tricks page — skills/commands and use cases, plus session, cost, and knowledge habits. Static, evergreen; no `data.js` dependency. |
| `claude-news.json` | Hand-curated news feed (`releases`, `events`, `tutorials`, `sources`, `updatedAt`). `generate.py` inlines it into `data.js` as `news`. Refresh with **`/update-news`** (web-searches the latest, rewrites the JSON, regenerates) or by hand-editing + re-running `generate.py`. |

## How the data is assembled

The spine is **`~/Startups/*`** (the real project folders). Support folders are excluded: `_Shared`, `00_Portfolio_HQ`, `fin folio` (see `EXCLUDE` in `generate.py`). Onto each project the scanner joins three signals:

1. **Status note** — `~/Startups/<project>/mission-control.md` (source of truth for status / next / milestones / todos / summary). Optional, degrades gracefully.
2. **Claude Code sessions** — matched by encoding the folder's absolute path (every non-alphanumeric char → `-`) to find its folder under `~/.claude/projects/`. Yields session count, last-active, and memory files.
3. **Git** — when the folder is a repo: branch, last commit, uncommitted count, ahead/behind, remote, and commits in the last 30 days. The activity chart overlays sessions + commits. It also captures the **lists** of uncommitted files (`dirtyFiles`, capped 50) and unpushed commits (`unpushedCommits`, ahead of upstream, capped 30); `project.html` renders these in a **Pending changes** panel — the per-project view of what's staged for the next push/version. (Parse `git status --porcelain` by whitespace-splitting, not fixed columns: `_git()` strips the output, shifting the first line's status column by one.)

Each project also carries its **file structure** (a shallow tree: top-level entries with child counts, expanded one level for code projects) and any **project-local skills/agents** under `<project>/.claude/`.

Each project can also carry a **tech architecture diagram** at `<project>/tech-architecture.json` — a small, hand-editable graph (`tiers` → grouped boxes, `nodes` with `kind`, `edges` with `flow`). The scanner reads it inline into `data.js` and `project.html` renders it live with **Cytoscape.js** (loaded from CDN) as an interactive graph: draggable nodes, zoom/pan, dark theme matching the dashboard. To change a flow, edit the JSON and re-run `generate.py` — no image to regenerate. A project with no `tech-architecture.json` simply omits the panel.

Each project can also carry a **knowledge base** at `<project>/knowledge/` — plain markdown that travels with the repo (no Obsidian required, though the format is Obsidian-friendly so `~/Startups` can be opened as a vault). `knowledge/journal.md` is an append-only session log (entries are `## YYYY-MM-DD — title` sections, newest on top); any other `knowledge/*.md` are free-form notes (decisions, references). The scanner reads it via `read_knowledge()` — parsing recent journal entries and titled note excerpts — and `project.html` renders a **Knowledge base** panel (journal + notes, markdown rendered via marked.js from CDN). The drilldown's **Memory files** panel also shows the *contents* (excerpts) of Claude Code memory under `~/.claude/projects/<encoded>/memory/*.md`, not just filenames, via `read_memory_docs()`. A project with no `knowledge/` folder omits the panel.

### Auto-loaded context digest (`knowledge/context.md`)

`generate.py` also distills each project's note + recent journal into a small **`knowledge/context.md`** via `build_digest()` / `write_digest()`: status, next action, open milestones/todos, and the last 2–3 journal entries. It's **generated — never hand-edit it** (run `/update`). It's deliberately **deterministic** (no timestamps, stable ordering) and **bounded** (recent journal only) so its bytes don't churn between runs, keeping it cache-stable. Each project's `CLAUDE.md` auto-loads it with a single line — `@knowledge/context.md` — so every session in that project starts with current status/history instead of amnesia, without re-exploring. This is the shared-logic loop: `/update` writes the note + journal → `generate.py` rebuilds the digest → CLAUDE.md imports it next session. (First import per project triggers a one-time approval dialog.) `read_knowledge()` skips `context.md` so the dashboard doesn't list the generated digest as a note.

### Tech knowledge: two tiers (architecture brief + deep spec)

Status/narrative memory (the digest above) is separate from **durable technical knowledge** — how the system is shaped and how the code works. The latter lives in two tiers so it's both informed-by-default and cheap:

- **Tier 1 — always-on brief:** a concise **Architecture** section inside the project's own `CLAUDE.md` (stack, key directories, data flow in a few lines, conventions, run/test commands, the gotchas that bite). Auto-loaded every session, so keep it tight. Altitude rule: document **shape, why, and where** — never line-level behavior; the code is the source of truth for *exactly how*, and over-detailed docs rot. Bootstrap from the codebase with `/init`.
- **Tier 2 — on-demand spec:** `knowledge/architecture.md`, a deeper reference (module map, the `data.js`-style schema/contract, key flows). `read_knowledge()` **features** it — returns its full body (not just an excerpt) in a `spec` field — and `project.html` renders the whole spec in the Knowledge panel. Claude reads it on demand when working in that area, so it costs nothing until needed.

The visual third leg is the `tech-architecture.json` diagram. **`/update-arch` refreshes all three** (diagram + CLAUDE.md brief + `knowledge/architecture.md`) when the system's shape changed. Author tech docs only for projects with real code; skip thin/static ones (a brochure site doesn't earn an architecture spec). The reference implementation is this project: see `mission-control/knowledge/architecture.md`.

Shared **skills** and **agents** come from the global `~/.claude/skills` and `~/.claude/agents`. **Connected MCP servers** come from `claude mcp list` (name, url, host, connection status) and render in the overview's "Connected MCPs" section. For `claude.ai`-scoped connectors the card also shows the **Claude account** they're authorized under (the email from `~/.claude.json` → `oauthAccount.emailAddress`); per-connector service accounts aren't exposed by the CLI, so only the owning Claude account is shown.

### Usage & spend

- **Claude Code usage** — the scanner reads every session log under each project's `~/.claude/projects/<encoded>/*.jsonl`, sums input/output/cache tokens, and computes an **estimated** dollar cost (logged token counts × public per-model pricing in `PRICING`; Claude Code logs tokens but not cost). It shows as a portfolio "Usage & spend" card on the overview, a per-project cost chip on each project card, and a full breakdown panel on the drilldown. Always labelled **est.**
- **Higgsfield usage** — two files in this folder feed the card:
  - `higgsfield-usage.json` (`{ "credits", "plan", "asOf" }`) — the current balance snapshot.
  - `higgsfield-transactions.json` (`{ "balance", "plan", "fetchedAt", "transactions": [{ "display_name", "credits", "action", "created_at" }] }`) — the raw, newest-first transaction history. `credits` is **signed**: negative = spend/deduct, positive = grant/refund.
  - `generate.py` reads the transactions and derives **daily used credits** (30-day series), **daily remaining** (reconstructed: `remaining(day) = balance − Σ deltas after that day`), and rollups (`spentToday`, `spent7d`, `spent30d`, `spentMonth`, `byMonth`). The overview shows the remaining balance, the used today/7d/30d/this-month row, and a **Higgsfield credits** chart (used-per-day bars + remaining line). Missing transactions file → balance-only card; missing both → placeholder.
- **Renewal dates** — both spend cards show when the subscription renews, derived automatically (no manual entry): **Claude** from the Stripe anchor in `~/.claude.json` (`oauthAccount.subscriptionCreatedAt` → renews on that day-of-month each month); **Higgsfield** from the most recent positive "Subscription" grant in `higgsfield-transactions.json` (+1 month).
- **Tech stack** — each project shows a chip list of technologies. Source: the `tech:` field in `mission-control.md` (comma-separated); if absent, the scanner falls back to the architecture diagram's node labels.

### Keeping usage tracking up to date

- **Claude Code** — fully **automatic**. Every `python3 generate.py` re-reads the session logs, so the spend/token numbers are current as of the last run (cost is always an estimate; token counts are exact). No manual step.
- **Higgsfield** — needs a refresh because `generate.py` is stdlib-only and can't call MCP. Run **`/update-usage`** in a session where the Higgsfield MCP is connected. It:
  1. Calls the Higgsfield MCP **`balance`** tool → rewrites `higgsfield-usage.json` (`credits`, `plan`, today's date as `asOf`).
  2. Calls the Higgsfield MCP **`transactions`** tool (pages with `cursor`/`next_cursor` until exhausted) → rewrites `higgsfield-transactions.json` with the full list and the current `balance`/`fetchedAt`.
  3. Re-runs `python3 generate.py` and confirms balance / # transactions / used today·7d·30d.
  A natural cadence is to run `/update-usage` whenever you open Mission Control, or at the end of a Higgsfield-heavy session.

### `mission-control.md` note format

```
---
name: Raqib
status: active            # active | in-progress | blocked | idle | archived
stack: Multi-agent / Fintech
tech: Multi-agent orchestration, Postgres, Vector memory   # comma list → tech-stack chips
next: Finish MVP and pitch deck to win the hackathon
tags: fintech, P0
milestones:
  - [x] Project scaffold
  - [ ] MVP core flow
todos:
  - Lock the demo happy-path
---
One-paragraph human summary of where things stand.
```

The note lives **inside the project folder** (`~/Startups/<project>/mission-control.md`), so it travels with the code and can be committed to the repo. Everything is optional and defaults gracefully (a project with no note shows derived data: sessions, git, last active, memory files).

## On session start (dashboard mode)

When I open a session in this folder, do the following automatically:

1. Run `python3 generate.py` to refresh `data.js`.
2. Read `data.js` and present a concise **text dashboard** in chat:
   - One-line portfolio header: `N projects · X active · Y blocked · Z open todos · S sessions`.
   - **Active / in-progress projects** first, each as: `name — status — next action — (M/N milestones, T todos)`.
   - A short **"Top of mind"** list: the `next` action of every active project.
3. End with: **"What do you want to work on today?"** and list the active project names as options.
4. Remind me I can open `index.html` for the visual dashboard.

Keep it tight — this is a standup, not a report. Do not dump idle/archived projects unless I ask.

## `/update` — end-of-session refresh

When I run `/update` (optionally `/update <project>`), update the status note so tomorrow's dashboard is already current:

1. Determine the target project. Default: the one we worked on this session. If ambiguous, ask.
2. Read context first: skim `~/Startups/<project>/knowledge/journal.md` (recent entries) and the project's memory files, so the update reflects accumulated history, not just this session.
3. Open (or create) `~/Startups/<project>/mission-control.md`.
4. From what we did this session, update the frontmatter:
   - `status` — bump to `active`/`in-progress`/`blocked` as appropriate.
   - `next` — the single most important next action.
   - `milestones` — check off any completed; add new ones we agreed on.
   - `todos` — remove done items, add new ones surfaced this session.
   - Refresh the summary paragraph.
5. Append a dated entry at the top of `~/Startups/<project>/knowledge/journal.md` (create `knowledge/` + the file if missing): `## YYYY-MM-DD — title` + 2–5 bullets (what happened, decisions, next). This is the durable history the snapshot note discards.
6. Run `python3 generate.py` so `data.js` reflects the change. This also rebuilds `knowledge/context.md` (the digest auto-loaded into future sessions via the project CLAUDE.md's `@knowledge/context.md` import) — no separate step.
7. Confirm with a one-line diff of what changed (status, next, +/- milestones, +/- todos, +1 journal entry, digest refreshed).

**Rules:**
- Only edit the note for the project we actually worked on (respects one-startup-per-session isolation).
- Never invent progress — only record what genuinely happened or what I explicitly stated.
- The note is the source of truth for status/next/milestones/todos; sessions, git status, last-active and memory files are derived by the scanner and must not be hand-written.
- The journal (`knowledge/journal.md`) is append-only — add a new dated entry, never rewrite or delete old ones.

## `/update-arch` — refresh the tech architecture diagram

`/update` deliberately does **not** touch the architecture diagram. When the system's real shape changed this session, run `/update-arch` (optionally `/update-arch <project>`):

1. Determine the target project (default: the one we worked on; respects one-startup-per-session isolation).
2. Open (or create) `~/Startups/<project>/tech-architecture.json` — the Cytoscape graph: `tiers` (grouped boxes), `nodes` (each with a `kind`: `client` · `edge` · `service` · `core` · `store` · `external`), `edges` (each with a `flow`: `read` · `control` · `data` · `write` · `feedback` · `async`, plus `"dashed": true` for async/feedback).
3. Edit nodes/edges to match what genuinely exists now; optionally sync the `tech:` chips in the note.
4. Run `python3 generate.py` so `data.js` picks up the new graph.
5. Confirm with a one-line diff (+/- tiers, nodes, edges).

**Rules:** keep node `id`s stable (rename `label`, not `id`) so the graph stays diffable; never invent components; valid JSON only (a malformed file silently drops the panel).

## `/archive` — archive a project

When a project is done or shelved, run `/archive` (optionally `/archive <project>`): it confirms, sets `status: archived` in that project's `mission-control.md`, appends a dated journal entry, and regenerates the dashboard. It **never deletes** — note, journal, knowledge, milestones, and code all stay; resume by running `/update` and setting the status back to `active`. Archived projects drop out of the session-start standup and render as a **compact** name-only card on the overview.

## Refresh manually

```bash
python3 generate.py        # rescan everything
open index.html            # open the visual dashboard
```
