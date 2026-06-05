# Mission Control

A **local, no-install command center** for all your Claude Code projects — status, milestones, todos, recent activity, usage & spend, architecture diagrams, and a per-project knowledge base, in one dark dashboard you open as a local file.

![Mission Control dashboard](docs/dashboard.png)

> The screenshot uses demo data; your dashboard shows your real projects.

No server. No build step. No database. Just a Python script that scans your project folders and a few static HTML pages that render the result.

```
your-projects/*  ──►  generate.py  ──►  data.js  ──►  index.html · project.html
(real folders +       (stdlib + git)    (snapshot)    (open via file://)
 ~/.claude sessions)
```

## Quick start

Mission Control assumes all your projects live under one parent folder. **Clone it into that folder**, alongside your projects:

```bash
cd ~/Startups                       # the folder that holds all your projects
git clone <repo-url> mission-control
cd mission-control
./setup.sh                          # installs commands, generates data.js
open index.html                     # open the dashboard
```

`setup.sh` is idempotent — re-run it after a `git pull`. That's the whole install.

> No `~/Startups`? Clone wherever your projects live. `generate.py` auto-detects the projects root as the folder containing this checkout (override with `MC_ROOT=/path ./setup.sh`).

## What you get

- **Overview** (`index.html`) — KPIs, an activity chart, a card per project, usage & spend (estimated Claude cost + optional Higgsfield credits with renewal dates), shared skills/agents, and connected MCPs.
- **Per-project drilldown** (`project.html?id=<folder>`) — status, milestones, todos, an interactive architecture diagram, Claude usage, the file tree, and the knowledge base.
- **A knowledge base per project** — plain markdown (`knowledge/journal.md`, notes, an optional `architecture.md`) that travels with the repo, plus an auto-loaded `context.md` digest so new sessions start informed.

## The `/update` commands

`setup.sh` installs four slash commands (run them in any Claude Code session):

| Command | Refreshes |
|---|---|
| `/update` | the project's status note + appends a journal entry |
| `/update-arch` | architecture: diagram + CLAUDE.md brief + `knowledge/architecture.md` |
| `/update-usage` | Higgsfield credit usage |
| `/update-news` | the Claude News feed |

Each ends by running `generate.py`, so the dashboard stays current. The only one you run regularly is **`/update`** at the end of a session.

## How a project is tracked

Add an optional `mission-control.md` note to any project folder:

```yaml
---
name: My Project
status: active          # active | in-progress | blocked | idle | archived
stack: Next.js / Postgres
next: Ship the checkout flow
milestones:
  - [x] Auth
  - [ ] Billing
todos:
  - Wire the webhook
---
One paragraph on where things stand.
```

Everything is optional and degrades gracefully — a project with no note still shows derived data (sessions, git, last active).

## Requirements

- **Python 3** (standard library only — nothing to `pip install`).
- **git** (optional — powers the repository panels).
- A modern browser to open the HTML files.

## Learn more

Open **`guide.html`** for the full walkthrough: architecture, folder/file structure, the daily workflow, the knowledge base, and Obsidian integration. Also see **`best-practices.html`** and **`news.html`** from the dashboard sidebar.

## License

MIT — see `LICENSE`.
