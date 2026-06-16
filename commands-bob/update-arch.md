---
description: Update an IBM Bob project's technical knowledge — architecture diagram, AGENTS.md brief, and knowledge/architecture.md spec — and regenerate the Bob MC dashboard.
---

Refresh a Bob MC project's **technical knowledge** when the system's real shape or workings changed this session. This is separate from `/update` (status note) and covers three tiers of architecture knowledge. (IBM Bob counterpart of the Claude Code `/update-arch`: it targets `~/bob projects`, writes the brief to `AGENTS.md` instead of `CLAUDE.md`, and rebuilds `data-bob.js`.)

1. **Diagram** — `~/bob projects/<project>/tech-architecture.json` (Cytoscape graph, rendered on the Bob MC project page).
2. **Always-on brief** — the **Architecture** section inside the project's own `~/bob projects/<project>/AGENTS.md` (auto-loaded by IBM Bob every session; keep it tight).
3. **On-demand spec** — `~/bob projects/<project>/knowledge/architecture.md` (deep reference, featured in the dashboard Knowledge panel).

Update only the tiers that actually changed. **Altitude rule for the prose (brief + spec): document shape, why, and where — never line-level behavior. The code is the source of truth for *exactly how*, and over-detailed docs rot.** Author tech docs only for projects with real code; skip thin/static ones.

## Steps

1. **Determine the target project.** Default: the current working directory's project root under `~/bob projects/<project>`. If `$ARGUMENTS` names a project, use `~/bob projects/<that>`. If we're not inside a `~/bob projects` project and no argument is given, ask which one.

2. **Diagram — open or create** `~/bob projects/<project>/tech-architecture.json`. Schema:

   ```json
   {
     "title": "<Project name>",
     "tiers": [
       { "id": "client", "label": "01 · Client" },
       { "id": "api",    "label": "02 · Edge + API" },
       { "id": "svc",    "label": "03 · Services" },
       { "id": "data",   "label": "04 · Storage + Data" }
     ],
     "nodes": [
       { "id": "app", "label": "Expo Router App", "tier": "client", "kind": "client" },
       { "id": "wk",  "label": "Cloudflare Workers", "tier": "api", "kind": "edge" },
       { "id": "d1",  "label": "D1", "tier": "data", "kind": "store" }
     ],
     "edges": [
       { "source": "app", "target": "wk", "label": "API", "flow": "read" },
       { "source": "wk",  "target": "d1", "label": "query", "flow": "write" },
       { "source": "wk",  "target": "push", "label": "notify", "flow": "async", "dashed": true }
     ]
   }
   ```

3. **Edit the graph** to match what genuinely changed this session:
   - `tiers` — the grouped layers (top→bottom), each an `id` + a numbered `label` like `"01 · Client"`.
   - `nodes` — each has `id`, `label`, a `tier` (must match a tier id), and a `kind` that drives its color:
     `client` · `edge` · `service` · `core` · `store` · `external` (default `service`).
   - `edges` — `source`/`target` (node ids) plus an optional `label` and a `flow` that drives the edge color:
     `read` · `control` · `data` · `write` · `feedback` · `async` (default `read`). Add `"dashed": true` for async/future/feedback links.

4. **Always-on brief — update the project's `AGENTS.md`.** Ensure an **Architecture** (or "Code architecture") section exists with: stack, the key directories that matter, the data flow in a few sentences, conventions, run/test/deploy commands, and the gotchas that bite. Keep it tight (~1–2k tokens) since IBM Bob loads it every session. If the project has no real `AGENTS.md` yet, bootstrap one with Bob's `/init` (it scans the codebase), then trim to the altitude rule.

5. **On-demand spec — write/refresh** `~/bob projects/<project>/knowledge/architecture.md` (create `knowledge/` if missing). The deep tier: a system-shape overview, a module/file map, the data schema or key contracts, main flows, conventions/invariants, gotchas, and a "where to look" table. This is the featured spec the dashboard renders in full.

6. **Optionally sync the tech-stack chips.** If the stack itself changed, also update the `tech:` line in `~/bob projects/<project>/mission-control.md` (comma-separated). With no `tech:` line, the dashboard falls back to the diagram's node labels.

7. **Regenerate the dashboard:** run `MC_ENGINE=bob python3 "__MC_DIR__/generate.py"` so `data-bob.js` picks up the new graph + spec.

8. **Confirm** with a one-line diff: which tiers changed (+/- diagram nodes/edges, brief updated?, spec updated?, `tech:` changed?).

## Rules

- Only edit the docs for the project we actually worked on. With an explicit `$ARGUMENTS` project, target that one.
- Never invent architecture — only document components, flows, and behavior that genuinely exist or that the user described. If unsure whether something exists, read the code or ask before adding it.
- Keep diagram ids stable across edits (rename `label`, not `id`) so the graph stays diffable.
- Keep the prose at the shape/why/where altitude — don't transcribe code into docs; it goes stale and misleads.
- Valid JSON only for the diagram — a malformed file makes `generate.py` silently drop the panel.
- Always regenerate with `MC_ENGINE=bob` — a plain `generate.py` run rebuilds the Claude dashboard, not Bob MC.
