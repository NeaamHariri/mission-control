---
description: Archive a project — set its Mission Control status to archived, log it in the journal, and regenerate the dashboard.
---

Archive a project so it drops out of the active standup but keeps all its history. Works from any project folder under `~/Startups`.

## Steps

1. **Determine the target project.** Default: the current working directory's project root under `~/Startups/<project>`. If `$ARGUMENTS` names a project, use `~/Startups/<that>` instead. If we are not inside a `~/Startups` project and no argument is given, ask which project to archive.

2. **Confirm before archiving.** State which project will be archived and ask the user to confirm — archiving is a deliberate status change, not a routine refresh. If `$ARGUMENTS` includes an explicit confirmation (e.g. the user already said "archive Foo"), skip the extra prompt.

3. **Open or create** `~/Startups/<project>/mission-control.md`. If it doesn't exist yet, create it with the standard frontmatter shape (see `/update`) before archiving.

4. **Set the status to archived.** In the frontmatter:
   - `status: archived`
   - `next` — set to a short closing note (e.g. `Archived — no active work`) unless the user gives a specific reason to resume later.
   - Leave `milestones`, `todos`, `tags`, `stack`, and the summary paragraph intact — they are the record of where the project ended. Do **not** delete history.

5. **Append a journal entry.** Add a dated entry at the **top** of `~/Startups/<project>/knowledge/journal.md` (create the `knowledge/` folder and the file with a short `# <Project> — Session Journal` header if missing). Format:

   ```
   ## YYYY-MM-DD — Archived
   - Archived the project (status → archived).
   - Reason / state at archival (only what the user stated or genuinely happened).
   - How to resume, if relevant.
   ```

6. **Regenerate the dashboard:** run `python3 ~/Startups/mission-control/generate.py` so `data.js` reflects the new status. Archived projects are excluded from the active standup but remain visible on the dashboard.

7. **Confirm** with a one-line diff: status → archived, +1 journal entry, dashboard regenerated.

## Rules

- Archiving never deletes a project, its note, journal, knowledge, or code — it only changes `status`. To bring a project back, run `/update` and set the status to `active`/`in-progress`.
- Only edit the note + journal for the project being archived.
- Never invent a reason — record only what the user stated or what genuinely happened.
- The journal is append-only — add a new entry, don't rewrite or delete old ones.
