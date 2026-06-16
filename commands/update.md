---
description: End-of-session refresh — update this project's mission-control.md note and regenerate the Mission Control dashboard.
---

Refresh the Mission Control status note for the project we worked on this session, so tomorrow's dashboard is already current. Works from any project folder under `~/Startups`.

## Steps

1. **Determine the target project.** Default: the current working directory's project root under `~/Startups/<project>`. If `$ARGUMENTS` names a project, use `~/Startups/<that>` instead. If we are not inside a `~/Startups` project and no argument is given, ask which project.

2. **Read context first.** Skim `~/Startups/<project>/knowledge/journal.md` (recent entries) and the project's memory files (`~/.claude/projects/<encoded>/memory/*.md`) if present, so the update reflects accumulated history — not just this session. Absent files are fine; just skip.

3. **Open or create** `~/Startups/<project>/mission-control.md`. If creating, use this frontmatter shape:

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

5. **Append a journal entry.** Add a dated entry at the **top** of `~/Startups/<project>/knowledge/journal.md` (create the `knowledge/` folder and the file with a short `# <Project> — Session Journal` header if missing). Format:

   ```
   ## YYYY-MM-DD — <short title>
   - What genuinely happened this session.
   - Key decisions (and why).
   - Blockers / what's next.
   ```

   The snapshot note is overwritten each run; this journal is the durable history the dashboard renders and that step 2 reads back next time. 2–5 bullets, only what genuinely happened.

6. **Regenerate the dashboard:** run `python3 ~/Startups/mission-control/generate.py` so `data.js` reflects the change. This same run also rebuilds `knowledge/context.md` — the bounded digest auto-loaded into future sessions via the project CLAUDE.md's `@knowledge/context.md` import. No separate step; the digest stays in sync for free.

7. **Confirm** with a one-line diff: status, next, +/- milestones, +/- todos, +1 journal entry, digest refreshed.

## Rules

- Only edit the note + journal for the project we actually worked on (respects one-startup-per-session isolation). With an explicit `$ARGUMENTS` project, target that one.
- Never invent progress — only record what genuinely happened or what the user explicitly stated. Same rule applies to the journal entry.
- The note is the source of truth for status / next / milestones / todos. Sessions, git status, last-active and memory files are derived by the scanner — never hand-write them.
- The journal is append-only — add a new entry, don't rewrite or delete old ones.

## Version control

`mission-control.md` and `knowledge/` are **globally git-ignored** (`~/.config/git/ignore`) so this personal status tracking never lands in a shared repo by default. (Your project's `CLAUDE.md` is a normal file — not ignored.)

- **Team / shared project:** leave them ignored (the default — nothing to do). They're your dashboard state, not shared code.
- **Personal project you want versioned:** un-ignore them in that repo's local `.gitignore` (`!mission-control.md`, `!knowledge/`) and commit normally.

When unsure, leave them ignored — it's the safe default and you can opt in later. Only add the un-ignore overrides if the user explicitly asks.
