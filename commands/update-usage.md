---
description: Refresh Higgsfield credit usage (balance + transactions) and regenerate the Mission Control dashboard.
---

Refresh the **usage & spend** numbers on Mission Control. Claude Code spend is already automatic (the scanner re-reads session logs on every run), so this command exists for **Higgsfield**, which `generate.py` can't fetch on its own (stdlib-only, no MCP). Run `/update-usage` in a session where the **Higgsfield MCP is connected** — e.g. whenever you open Mission Control, or at the end of a Higgsfield-heavy session.

## Steps

1. **Confirm the Higgsfield MCP is available.** If no Higgsfield MCP tools are connected this session, stop and tell the user to connect it (`claude mcp list` should show `higgsfield ✓ Connected`).

2. **Fetch the balance.** Call the Higgsfield MCP **`balance`** tool. Rewrite `~/Startups/mission-control/higgsfield-usage.json`:

   ```json
   { "credits": <current balance>, "plan": "<subscription_plan_type>", "asOf": "<YYYY-MM-DD today>" }
   ```

3. **Fetch the full transaction history.** Call the Higgsfield MCP **`transactions`** tool (size up to 100) and page with the returned `cursor`/`next_cursor` until exhausted. Rewrite `~/Startups/mission-control/higgsfield-transactions.json` with the complete, newest-first list:

   ```json
   {
     "balance": <current balance>,
     "plan": "<plan>",
     "fetchedAt": "<YYYY-MM-DD today>",
     "transactions": [
       { "display_name": "...", "credits": <signed int>, "action": "spend|refund|grant|deduct", "created_at": "<ISO>" }
     ]
   }
   ```

   `credits` is **signed**: negative = spend/deduct, positive = grant/refund. Keep every transaction — `generate.py` derives daily used / remaining and the renewal date from this file.

4. **Regenerate the dashboard:** run `python3 ~/Startups/mission-control/generate.py`.

5. **Confirm** with a one-line summary: balance, plan, # transactions written, used today / 7d / 30d.

## Rules

- Don't hand-edit the numbers — pull them from the MCP. The two JSON files are the only inputs; everything else (daily series, remaining-over-time, renewal date) is derived by `generate.py`.
- Page until `next_cursor` is null — a truncated history makes the spend rollups wrong.
- Claude Code spend needs no action here; it refreshes automatically on any `generate.py` run (cost is an estimate, token counts exact).
- This is portfolio-wide (not per-project), so it's safe to run from any folder; it only writes the two files under `~/Startups/mission-control/`.
