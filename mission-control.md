---
name: Mission Control
status: active
stack: HTML / Chart.js / Python (stdlib)
tech: Python (stdlib), Cytoscape.js, Chart.js, Static HTML
next: Publish the "ideas explosion / focus" launch story on LinkedIn + X (brand asset, today), then dogfood for ~1 week before the Show HN
tags: internal-tool, dashboard, open-source
milestones:
  - [x] Design system (ui-ux-pro-max, dark IDE)
  - [x] Data layer (generate.py + data.js)
  - [x] Overview dashboard
  - [x] Per-project view
  - [x] Per-project skills & agents visibility
  - [x] Usage & spend tracking (Claude est. cost + Higgsfield daily/remaining credits)
  - [x] Per-project tech-stack chips + Connected-MCP account details
  - [x] End-of-session command suite (/update, /update-arch, /update-usage, /update-news)
  - [x] Subscription renewal dates on the Claude + Higgsfield cards
  - [x] Knowledge base (knowledge/journal.md + notes) + journal-aware /update
  - [x] Auto-loaded context digest (knowledge/context.md via CLAUDE.md @import)
  - [x] Tiered tech knowledge (CLAUDE.md brief + knowledge/architecture.md spec), piloted here
  - [x] News + Best Practices pages (data-driven news feed, skills cheat-sheet)
  - [x] Open-sourced on GitHub (MIT, README, CONTRIBUTING, setup.sh, demo GIF)
  - [x] Repositioned around AI project sprawl & focus (memory as supporting pillar)
  - [ ] Launch: personal story post → Show HN + r/ClaudeAI (sprawl angle + GIF)
  - [ ] Listed in awesome-claude-code (Tooling › General) — after ~1 week age + some traction
  - [ ] Packaged as a Claude Code plugin + marketplace submission
  - [ ] Roll out /update-arch tech docs to the real code projects (Crclen, Flywheel Creative OS)
  - [ ] gh-based GitHub status (PRs, CI checks)
todos:
  - Marketing — publish the 'ideas explosion / focus' story post on LinkedIn + X today (brand asset; stands alone, no stars needed)
  - Marketing — dogfood Mission Control on real projects for ~1 week (also satisfies the awesome-list 1-week age rule)
  - Marketing — ~1 week out, Show HN + r/ClaudeAI launch led with the project-sprawl angle + the demo GIF
  - Marketing — after some traction, submit the prepared awesome-claude-code entry via the web form (Tooling / General; web-UI only, no gh)
  - Marketing — after traction, package as a Claude Code plugin + open a marketplace submission
  - Marketing — ongoing, post a short 'what I learned building with Claude' every 1–2 weeks (build in public)
  - Marketing — long shot, apply to Claude for Open Source via the exception before June 30 (low odds for a new repo)
  - Run /update-arch inside Crclen + Flywheel Creative OS sessions to author their architecture brief + spec
  - Run /update-usage with the live Higgsfield MCP to prove the refresh end-to-end
  - Add gh-based GitHub status (PRs, CI checks)
---
A local, no-install command center for all Claude Code projects, skills, agents, memory, usage, milestones and todos. Project-centric: the spine is ~/Startups/*, joined with Claude session data and local git status, plus shared skills/agents from ~/.claude. Carries a full usage & spend layer (estimated Claude cost from session logs; Higgsfield daily-used / remaining credits with auto-derived renewal dates on both cards), labelled tech-stack chips, and Connected MCPs showing their claude.ai account. This session added a per-project knowledge base: knowledge/journal.md (append-only history, journal-aware /update), an auto-loaded knowledge/context.md digest wired into every project's CLAUDE.md via @import (so sessions start informed and cache-warm), and a two-tier tech-knowledge system — an always-on CLAUDE.md architecture brief plus an on-demand knowledge/architecture.md deep spec featured in full on the project page — piloted on Mission Control itself and driven by an expanded /update-arch. Now open-sourced at github.com/NeaamHariri/mission-control (MIT, README + CONTRIBUTING + setup.sh + demo GIF) and added News + Best Practices pages with a /update-news command. Repositioned the marketing around the real differentiator — **AI-induced project sprawl and focus** ("Claude gave you an ideas explosion; Mission Control helps you finish them"), with memory as a supporting pillar. Next phase is launch (plan c — organic, brand-first): publish the personal story post, dogfood for a week, then Show HN + r/ClaudeAI, then awesome-list + plugin marketplace once it has a little traction. (A SessionEnd auto-regenerate hook was considered and dropped — the /update* commands and the session-start routine already keep data.js fresh.)
