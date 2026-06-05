---
description: Refresh the Claude News feed (releases, events, tutorials) and regenerate the Mission Control dashboard.
---

Refresh the **Claude News** page on Mission Control. `generate.py` is stdlib-only and can't fetch the web, so the news feed lives in a hand-curated `claude-news.json` that this command updates in one step: search the web for the latest Anthropic/Claude news, rewrite the JSON, and regenerate.

## Steps

1. **Gather the latest** via web search (a few `WebSearch` queries; `WebFetch` a specific page only if you need detail). Cover three buckets:
   - **Releases & updates** — new Claude models, Claude Code features, and Anthropic product launches (with dates).
   - **Events** — Anthropic conferences and developer events (e.g. Code with Claude), with dates, location, and whether they're free / livestreamed.
   - **Tutorials** — free Anthropic learning (Anthropic Academy courses, the tutorials hub, notable new guides).

2. **Rewrite** `~/Startups/mission-control/claude-news.json`, preserving this shape:

   ```json
   {
     "updatedAt": "<YYYY-MM-DD today>",
     "releases":  [{ "date": "<YYYY-MM-DD>", "title": "...", "tag": "Model|Product|Feature", "url": "...", "summary": "..." }],
     "events":    [{ "date": "<YYYY-MM-DD>", "name": "...", "location": "...", "url": "...", "note": "..." }],
     "tutorials": [{ "title": "...", "tag": "...", "url": "...", "summary": "..." }],
     "sources":   [{ "label": "...", "url": "..." }]
   }
   ```

   - Keep ~5 most-relevant releases (newest first by date), a handful of events (the page auto-sorts upcoming-first and marks past ones — include both recent past and any upcoming), the key free tutorials, and the stable `sources` links (Newsroom, Events, Academy, Code with Claude, docs, cookbook, status).
   - `tag` on a release should be `Model`, `Product`, or `Feature` (drives the chip colour). Set `updatedAt` to today.

3. **Only record what's real.** Use dates and titles from the sources — never invent a release or event. If unsure of an exact date, use the announcement's date or omit the item.

4. **Regenerate the dashboard:** run `python3 ~/Startups/mission-control/generate.py` so `data.js` picks up the new `news`.

5. **Confirm** with a one-line summary: `updatedAt`, and counts of releases / events / tutorials, plus the next upcoming event if any.

## Rules

- Don't hand-write the rendered page — `news.html` reads from `data.js`; the only input you edit is `claude-news.json`.
- Pull facts from the web (Anthropic's own pages are authoritative); cite them via the `url` fields. Never fabricate news.
- Portfolio-wide (not per-project) — safe to run from anywhere; it only writes `claude-news.json` under `~/Startups/mission-control/`.
- Respect the browsing rule: use `WebSearch` / `WebFetch` (or the `/browse` skill) for research; do not use Chrome-automation MCP tools.
