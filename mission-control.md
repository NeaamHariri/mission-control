---
name: Mission Control
status: active
stack: HTML / Chart.js / Python (stdlib)
tech: Python (stdlib), Cytoscape.js, Chart.js, Static HTML
next: Roll out /update-arch tech docs (CLAUDE.md brief + knowledge/architecture.md) to Crclen + Flywheel Creative OS in their own sessions
tags: internal-tool, dashboard
milestones:
  - [x] Design system (ui-ux-pro-max, dark IDE)
  - [x] Data layer (generate.py + data.js)
  - [x] Overview dashboard
  - [x] Per-project view
  - [x] Per-project skills & agents visibility
  - [x] Usage & spend tracking (Claude est. cost + Higgsfield daily/remaining credits)
  - [x] Per-project tech-stack chips + Connected-MCP account details
  - [x] End-of-session command suite (/update, /update-arch, /update-usage)
  - [x] Subscription renewal dates on the Claude + Higgsfield cards
  - [x] Knowledge base (knowledge/journal.md + notes) + journal-aware /update
  - [x] Auto-loaded context digest (knowledge/context.md via CLAUDE.md @import)
  - [x] Tiered tech knowledge (CLAUDE.md brief + knowledge/architecture.md spec), piloted here
  - [ ] Roll out /update-arch tech docs to the real code projects (Crclen, Flywheel Creative OS)
  - [ ] gh-based GitHub status (PRs, CI checks) once gh is installed
todos:
  - Run /update-arch inside Crclen + Flywheel Creative OS sessions to author their architecture brief + spec
  - Run /update-usage with the live Higgsfield MCP to prove the refresh end-to-end
  - Add gh-based GitHub status (PRs, CI checks) once gh is installed
---
A local, no-install command center for all Claude Code projects, skills, agents, memory, usage, milestones and todos. Project-centric: the spine is ~/Startups/*, joined with Claude session data and local git status, plus shared skills/agents from ~/.claude. Carries a full usage & spend layer (estimated Claude cost from session logs; Higgsfield daily-used / remaining credits with auto-derived renewal dates on both cards), labelled tech-stack chips, and Connected MCPs showing their claude.ai account. This session added a per-project knowledge base: knowledge/journal.md (append-only history, journal-aware /update), an auto-loaded knowledge/context.md digest wired into every project's CLAUDE.md via @import (so sessions start informed and cache-warm), and a two-tier tech-knowledge system — an always-on CLAUDE.md architecture brief plus an on-demand knowledge/architecture.md deep spec featured in full on the project page — piloted on Mission Control itself and driven by an expanded /update-arch. Open next: roll the tech-knowledge tiers out to the real code projects (Crclen, Flywheel Creative OS). (A SessionEnd auto-regenerate hook was considered and dropped — the /update* commands and the session-start routine already keep data.js fresh.)
