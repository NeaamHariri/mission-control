---
description: End-of-session refresh for a Bob MC project — update its mission-control.md note and regenerate the Bob MC dashboard.
---

Refresh the Bob MC status note for the IBM Bob project we worked on this session, so the dashboard is already current. Works from any project folder under `~/bob projects`. (This is the IBM Bob counterpart of the Claude Code `/update`; it targets `~/bob projects` and rebuilds `data-bob.js`.)

## Steps

1. **Determine the target project.** Default: the current working directory's project root under `~/bob projects/<project>`. If `$ARGUMENTS` names a project, use `~/bob projects/<that>` instead. If we are not inside a `~/bob projects` project and no argument is given, ask which project.

2. **Read context first.** Skim `~/bob projects/<project>/knowledge/journal.md` (recent entries) so the update reflects accumulated history — not just this session. Absent file is fine; just skip. (Usage/sessions/cost are read automatically from IBM Bob's task history by the scanner — there is nothing to hand-record there.)

3. **Open or create** `~/bob projects/<project>/mission-control.md`. If creating, use this frontmatter shape:

   ```
   ---
   name: <Pretty Name>
   status: active            # active | in-progress | blocked | idle | archived
   stack: <one-liner>
   next: <single most important next action>
   tags: <comma,separated>
   milestones:
     - [ ] <milestone>
   todos:
     - <todo>
   ---
   One-paragraph human summary of where things stand.
   ```

4. **Update the frontmatter** from what genuinely happened this session:
   - `status` — bump to `active` / `in-progress` / `blocked` as appropriate.
   - `next` — the single most important next action.
   - `milestones` — check off completed ones (`[x]`); add any newly agreed.
   - `todos` — remove done items; add new ones surfaced this session.
   - Refresh the summary paragraph.

5. **Append a journal entry.** Add a dated entry at the **top** of `~/bob projects/<project>/knowledge/journal.md` (create the `knowledge/` folder and the file with a short `# <Project> — Session Journal` header if missing). Format:

   ```
   ## YYYY-MM-DD — <short title>
   - What genuinely happened this session.
   - Key decisions (and why).
   - Blockers / what's next.
   ```

   The snapshot note is overwritten each run; this journal is the durable history the dashboard renders and that step 2 reads back next time. 2–5 bullets, only what genuinely happened.

6. **Regenerate the dashboard:** run `MC_ENGINE=bob python3 "__MC_DIR__/generate.py"` so `data-bob.js` reflects the change. This same run also rebuilds `knowledge/context.md` — the bounded digest you can reference from the project's `AGENTS.md` or `.bob/rules/` so future IBM Bob sessions start informed (Bob auto-loads `AGENTS.md` the way Claude Code loads `CLAUDE.md`).

7. **Confirm** with a one-line diff: status, next, +/- milestones, +/- todos, +1 journal entry, dashboard regenerated.

## Rules

- Only edit the note + journal for the project we actually worked on. With an explicit `$ARGUMENTS` project, target that one.
- Never invent progress — only record what genuinely happened or what the user explicitly stated. Same rule applies to the journal entry.
- The note is the source of truth for status / next / milestones / todos. Sessions, git status, last-active and the token/cost numbers are derived by the scanner from IBM Bob's logs — never hand-write them.
- The journal is append-only — add a new entry, don't rewrite or delete old ones.
- Always regenerate with `MC_ENGINE=bob` — a plain `generate.py` run rebuilds the Claude dashboard, not Bob MC.
