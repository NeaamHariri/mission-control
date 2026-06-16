#!/usr/bin/env python3
"""Mission Control data generator.

Project-centric: the spine is ~/Startups/* (the real project folders). Onto each
project it joins three signals:
  1. Status note  — ~/Startups/<project>/mission-control.md (source of truth for
     status / next / milestones / todos / summary). Optional, degrades gracefully.
  2. Claude Code  — sessions, last-active, memory files, matched by the encoded
     session-folder path under ~/.claude/projects/.
  3. Git          — branch, last commit, dirty count, ahead/behind, remote,
     commits in the last 30 days (only when the folder is a repo).

Shared skills/agents come from the global ~/.claude folder.

Zero dependencies — Python 3 stdlib + the local `git` binary.

Status note format (all fields optional):

    ---
    name: Raqib
    status: active        # active | in-progress | blocked | idle | archived
    stack: Multi-agent / Fintech
    next: Finish the MVP and pitch deck
    tags: fintech, P0
    milestones:
      - [x] Project scaffold
      - [ ] MVP core flow
    todos:
      - Lock the demo happy-path
    ---
    One-paragraph human summary.
"""

import json
import os
import re
import calendar
import subprocess
import datetime as dt
from pathlib import Path

HOME = Path.home()
HERE = Path(__file__).resolve().parent

CLAUDE_PROJECTS = HOME / ".claude" / "projects"
CLAUDE_HOME = HOME / ".claude"
BOB_HOME = HOME / ".bob"
# IBM Bob (ibm.bob-code extension, Cline/Roo-Code engine) keeps one folder per
# task under its VS-Code-style app data dir, each with ui_messages.json (usage)
# and api_conversation_history.json (the workspace it ran in).
BOB_TASKS = (HOME / "Library" / "Application Support" / "IBM Bob" / "User"
             / "globalStorage" / "ibm.bob-code" / "tasks")

# --- Engine selection -------------------------------------------------------
# Mission Control ships as one of two "engines", chosen with MC_ENGINE:
#   claude (default) — the original dashboard: spine ~/Startups/*, Claude Code
#                      sessions/usage from ~/.claude, MCPs from `claude mcp list`,
#                      estimated cost (Claude logs tokens, not dollars). → data.js
#   bob ("Bob MC")   — spine ~/bob projects/*, IBM Bob task history + *real* cost
#                      from the ibm.bob-code storage, MCPs from
#                      ~/.bob/settings/mcp_settings.json. → data-bob.js
# Everything else (git, notes, knowledge, tree, rendering) is shared; only the
# project root, the usage/session source, and the MCP source differ by engine.
ENGINE = os.environ.get("MC_ENGINE", "claude").strip().lower()
if ENGINE not in ("claude", "bob"):
    ENGINE = "claude"

if ENGINE == "bob":
    BRAND = "Bob MC"
    USAGE_PROVIDER = "IBM Bob"
    USAGE_ESTIMATED = False          # Bob records real per-request dollar cost
    DEFAULT_ROOT = HOME / "bob projects"
    OUT = HERE / "data-bob.js"
    EXCLUDE = set()
else:
    BRAND = "Mission Control"
    USAGE_PROVIDER = "Claude Code"
    USAGE_ESTIMATED = True           # cost = token counts × public pricing (est.)
    DEFAULT_ROOT = HERE.parent       # the folder that *contains* this checkout
    OUT = HERE / "data.js"
    # Folders in ~/Startups that are support/scratch, not portfolio projects.
    EXCLUDE = {"_Shared", "00_Portfolio_HQ", "fin folio"}

# Projects root. Defaults per engine (above); override with the MC_ROOT env var.
STARTUPS = Path(os.environ.get("MC_ROOT", str(DEFAULT_ROOT))).expanduser().resolve()

STATUS_ORDER = {"active": 0, "in-progress": 1, "blocked": 2, "idle": 3, "archived": 4}


def next_renewal(anchor_day: int, today: dt.date = None) -> str:
    """Next monthly renewal date (>= today) for a subscription anchored on
    `anchor_day` (the day-of-month it was created on). Clamps to month length
    (e.g. a 31st anchor renews on Feb 28). Returns 'YYYY-MM-DD'."""
    today = today or dt.date.today()

    def clamp(y, m, d):
        return dt.date(y, m, min(d, calendar.monthrange(y, m)[1]))

    cand = clamp(today.year, today.month, anchor_day)
    if cand < today:
        y, m = (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1)
        cand = clamp(y, m, anchor_day)
    return cand.strftime("%Y-%m-%d")


def claude_renewal():
    """Derive the Claude Max renewal date from the Stripe subscription anchor in
    ~/.claude.json (oauthAccount.subscriptionCreatedAt). Monthly subs renew on
    the creation day-of-month. Returns 'YYYY-MM-DD' or None."""
    cfg = HOME / ".claude.json"
    if not cfg.exists():
        return None
    try:
        acct = json.loads(cfg.read_text(encoding="utf-8")).get("oauthAccount") or {}
    except (ValueError, OSError):
        return None
    created = acct.get("subscriptionCreatedAt")
    if not created:
        return None
    try:
        anchor = dt.datetime.fromisoformat(created.replace("Z", "+00:00")).day
    except ValueError:
        return None
    return next_renewal(anchor)


def encode_claude_path(abs_path: Path) -> str:
    """Mirror Claude Code's session-folder encoding: every non-alphanumeric
    char in the absolute path becomes '-'. e.g.
    /Users/x/Startups/01_Raqib_Fintech -> -Users-x-Startups-01-Raqib-Fintech
    """
    return re.sub(r"[^A-Za-z0-9]", "-", str(abs_path))


def pretty_name(folder: str) -> str:
    name = re.sub(r"^\d+[_\-]", "", folder)        # strip leading "01_" / "02-"
    name = name.replace("_", " ").strip()
    return name or folder


def parse_note(text: str) -> dict:
    meta, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if m:
        body = m.group(2).strip()
        milestones, todos, current = [], [], None
        for raw in m.group(1).splitlines():
            line = raw.rstrip()
            if not line.strip():
                continue
            if re.match(r"^\s*-\s", line):
                item = re.sub(r"^\s*-\s*", "", line)
                if current == "milestones":
                    done = item[:3].lower() == "[x]"
                    milestones.append({"label": re.sub(r"^\[.\]\s*", "", item), "done": done})
                elif current == "todos":
                    todos.append(item)
                continue
            km = re.match(r"^([A-Za-z_]+)\s*:\s*(.*)$", line)
            if km:
                key, val = km.group(1).lower(), km.group(2).strip()
                if key in ("milestones", "todos") and val == "":
                    current = key
                else:
                    current, meta[key] = None, val
        if milestones:
            meta["milestones"] = milestones
        if todos:
            meta["todos"] = todos
    meta["summary"] = body
    return meta


def find_note(project_dir: Path, claude_dir: Path) -> dict:
    for candidate in (project_dir / "mission-control.md",
                      claude_dir / "mission-control.md"):
        if candidate.exists():
            return parse_note(candidate.read_text(encoding="utf-8", errors="ignore"))
    return {}


def skill_description(skill_dir: Path) -> str:
    skill_md = next(skill_dir.rglob("SKILL.md"), None)
    if skill_md and skill_md.exists():
        mm = re.search(r"description:\s*\"?(.*)", skill_md.read_text(errors="ignore"))
        if mm:
            return mm.group(1).strip().strip('"')[:160]
    return ""


def list_local_skills(project_dir: Path) -> list:
    sdir = project_dir / ".claude" / "skills"
    if not sdir.is_dir():
        return []
    out = []
    for s in sorted(sdir.iterdir()):
        if s.is_dir():
            out.append({"name": s.name, "description": skill_description(s)})
    return out


def list_local_agents(project_dir: Path) -> list:
    adir = project_dir / ".claude" / "agents"
    if not adir.is_dir():
        return []
    return [{"name": a.stem} for a in sorted(adir.glob("*.md"))]


def list_memory(claude_dir: Path) -> list:
    mem = claude_dir / "memory"
    if not mem.is_dir():
        return []
    return sorted(p.name for p in mem.glob("*.md") if p.name != "MEMORY.md")


def _strip_frontmatter(text: str) -> str:
    """Drop a leading YAML frontmatter block (--- ... ---) if present."""
    m = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)$", text, re.DOTALL)
    return m.group(1) if m else text


def _first_heading(text: str) -> str:
    for line in _strip_frontmatter(text).splitlines():
        m = re.match(r"^#{1,3}\s+(.*)", line.strip())
        if m:
            return m.group(1).strip()
    return ""


def _excerpt(text: str, max_chars: int = 240) -> str:
    """First meaningful prose from a markdown doc: skip frontmatter, headings,
    and blank lines, collapse whitespace, truncate to max_chars."""
    body = []
    for line in _strip_frontmatter(text).splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        body.append(s)
    flat = re.sub(r"\s+", " ", " ".join(body)).strip()
    return flat[:max_chars] + ("…" if len(flat) > max_chars else "")


def read_memory_docs(claude_dir: Path, max_chars: int = 240) -> list:
    """Surface the *contents* of Claude Code memory files (not just names):
    for each memory/*.md (except the system MEMORY.md index), return a short
    excerpt so the dashboard can show what each memory actually holds."""
    mem = claude_dir / "memory"
    if not mem.is_dir():
        return []
    out = []
    for p in sorted(mem.glob("*.md")):
        if p.name == "MEMORY.md":
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        out.append({"name": p.name, "title": _first_heading(txt),
                    "excerpt": _excerpt(txt, max_chars)})
    return out


def read_knowledge(project_dir: Path, max_entries: int = 8, max_notes: int = 12):
    """Scan a project's knowledge/ folder (plain markdown that travels with the
    repo). Parses knowledge/journal.md into dated session entries (newest first)
    and lists any other knowledge/*.md as titled notes with excerpts. Returns
    {"journal": [...], "notes": [...]} or None when the folder is absent/empty."""
    kdir = project_dir / "knowledge"
    if not kdir.is_dir():
        return None
    journal, notes, spec = [], [], None
    jpath = kdir / "journal.md"
    if jpath.exists():
        try:
            txt = jpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            txt = ""
        # Split into "## <heading>" sections; everything up to the first
        # heading is intro/ignored.
        parts = re.split(r"^##\s+", txt, flags=re.MULTILINE)
        for chunk in parts[1:]:
            lines = chunk.splitlines()
            heading = lines[0].strip() if lines else ""
            body = "\n".join(lines[1:]).strip()
            dm = re.match(r"(\d{4}-\d{2}-\d{2})", heading)
            journal.append({"title": heading,
                            "date": dm.group(1) if dm else "",
                            "body": body})
        journal = journal[:max_entries]
    for p in sorted(kdir.glob("*.md")):
        # journal.md is rendered separately; context.md is generated (the
        # auto-loaded session digest), not a hand-written note.
        if p.name in ("journal.md", "context.md"):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # architecture.md is the featured deep tech spec: keep its full body so
        # the dashboard can render the whole thing (the on-demand tech tier),
        # not just an excerpt like ordinary notes.
        if p.name == "architecture.md":
            spec = {"name": p.name, "title": _first_heading(txt) or "Architecture",
                    "body": txt.strip(), "words": len(txt.split())}
            continue
        notes.append({"name": p.name, "title": _first_heading(txt) or p.stem,
                      "excerpt": _excerpt(txt), "words": len(txt.split())})
    notes = notes[:max_notes]
    if not journal and not notes and not spec:
        return None
    return {"journal": journal, "notes": notes, "spec": spec}


def build_digest(name: str, note: dict, knowledge, max_entries: int = 3,
                 body_lines: int = 6, body_chars: int = 400) -> str:
    """Distill the source-of-truth note + recent journal into a compact,
    deterministic markdown digest that each project's CLAUDE.md auto-imports
    via `@knowledge/context.md`. Deterministic (no timestamps, stable ordering)
    and bounded (recent journal only) so its bytes stay cache-stable across
    generate.py runs. Returns "" when there's nothing worth loading."""
    note = note or {}
    status = (note.get("status") or "").strip()
    nxt = (note.get("next") or "").strip()
    summary = (note.get("summary") or "").strip()
    milestones = note.get("milestones") or []
    todos = note.get("todos") or []
    journal = (knowledge or {}).get("journal") or []
    if not (status or nxt or summary or milestones or todos or journal):
        return ""

    out = ["<!-- Auto-generated by generate.py from mission-control.md + "
           "knowledge/journal.md. Do not edit; run /update. -->",
           f"# {name} — Working Context", ""]
    line = []
    if status:
        line.append(f"**Status:** {status}")
    if nxt:
        line.append(f"**Next:** {nxt}")
    if line:
        out += [" · ".join(line), ""]
    if summary:
        out += [summary, ""]

    open_ms = [m.get("label", "") for m in milestones if not m.get("done")]
    if milestones:
        done = sum(1 for m in milestones if m.get("done"))
        out.append(f"**Milestones:** {done}/{len(milestones)} done")
        for lbl in open_ms[:6]:
            out.append(f"- [ ] {lbl}")
        out.append("")
    if todos:
        out.append("**Open todos:**")
        for t in todos[:8]:
            out.append(f"- {t}")
        out.append("")

    if journal:
        out.append("**Recent sessions (from journal):**")
        out.append("")
        for e in journal[:max_entries]:
            out.append(f"## {e.get('title') or e.get('date') or 'Entry'}")
            blines = [l for l in (e.get("body") or "").splitlines() if l.strip()]
            body = "\n".join(blines[:body_lines]).strip()
            if len(body) > body_chars:
                body = body[:body_chars].rstrip() + " …"
            if body:
                out.append(body)
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def write_digest(project_dir: Path, name: str, note: dict, knowledge) -> bool:
    """Write the auto-loaded session digest to <project>/knowledge/context.md.
    Only writes when there's content; idempotent (skips the write when bytes are
    unchanged so the file — and the prompt cache — stays stable). Returns True if
    a digest exists for this project."""
    digest = build_digest(name, note, knowledge)
    target = project_dir / "knowledge" / "context.md"
    if not digest:
        return False
    try:
        if not (target.exists() and target.read_text(encoding="utf-8") == digest):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(digest, encoding="utf-8")
    except OSError:
        return False
    return True


def read_news():
    """Read the hand-curated Claude/Anthropic news feed (claude-news.json next to
    this script): releases, events, tutorials, source links. Refreshed manually
    (or via a web search), so generate.py just inlines it into data.js for
    news.html to render. Returns the parsed dict, or None when absent/invalid."""
    src = HERE / "claude-news.json"
    if not src.exists():
        return None
    try:
        return json.loads(src.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


# Directories/files that are noise in a project structure view.
TREE_IGNORE = {
    ".git", ".gstack", "node_modules", ".venv", "venv", "__pycache__", ".next",
    "dist", "build", "target", ".cache", "coverage", ".pytest_cache", ".mypy_cache",
    ".idea", ".vscode", ".DS_Store", "tsconfig.tsbuildinfo",
}


def _tree_children(d: Path) -> list:
    try:
        items = sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except Exception:
        return []
    return [p for p in items if p.name not in TREE_IGNORE]


def read_arch(folder: Path):
    """Load a project's tech-architecture.json (a Cytoscape graph: tiers / nodes /
    edges) and return it inline so project.html can render it live. Returns the
    parsed dict, or None when absent or invalid."""
    src = folder / "tech-architecture.json"
    if not src.exists():
        return None
    try:
        return json.loads(src.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def derive_tech(arch) -> list:
    """Fallback tech stack when a note has no explicit `tech:` line: use the
    architecture's node labels (the real system components the user drew)."""
    if not arch:
        return []
    seen, out = set(), []
    for n in arch.get("nodes", []):
        label = (n.get("label") or "").strip()
        if label and label not in seen:
            seen.add(label)
            out.append(label)
    return out


# Estimated Claude API price per 1M tokens (USD), by model family. Cache-write
# uses the 5-minute rate. These drive a *rough* spend estimate — Claude Code
# logs token counts but not dollar cost, so the dashboard labels it "est.".
PRICING = {
    "opus":   {"in": 15.0, "out": 75.0, "cw": 18.75, "cr": 1.50},
    "sonnet": {"in":  3.0, "out": 15.0, "cw":  3.75, "cr": 0.30},
    "haiku":  {"in":  0.80, "out": 4.0, "cw":  1.00, "cr": 0.08},
}


def _price_for(model: str) -> dict:
    m = (model or "").lower()
    if "haiku" in m:
        return PRICING["haiku"]
    if "sonnet" in m:
        return PRICING["sonnet"]
    return PRICING["opus"]


def claude_usage(claude_dir: Path):
    """Aggregate token usage + an estimated dollar cost from a project's Claude
    Code session logs (~/.claude/projects/<encoded>/*.jsonl). Returns per-project
    totals plus a per-day cost/token map, or None when there are no sessions."""
    if not claude_dir.is_dir():
        return None
    tot = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0,
           "cost": 0.0, "messages": 0}
    by_day = {}
    for f in claude_dir.glob("*.jsonl"):
        try:
            with f.open(encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if '"usage"' not in line:
                        continue
                    try:
                        o = json.loads(line)
                    except ValueError:
                        continue
                    msg = o.get("message") or {}
                    u = msg.get("usage")
                    if not isinstance(u, dict):
                        continue
                    inp = u.get("input_tokens") or 0
                    out = u.get("output_tokens") or 0
                    cw = u.get("cache_creation_input_tokens") or 0
                    cr = u.get("cache_read_input_tokens") or 0
                    if not (inp or out or cw or cr):
                        continue
                    pr = _price_for(msg.get("model"))
                    cost = (inp / 1e6 * pr["in"] + out / 1e6 * pr["out"]
                            + cw / 1e6 * pr["cw"] + cr / 1e6 * pr["cr"])
                    tot["input"] += inp
                    tot["output"] += out
                    tot["cacheWrite"] += cw
                    tot["cacheRead"] += cr
                    tot["cost"] += cost
                    tot["messages"] += 1
                    day = (o.get("timestamp") or "")[:10]
                    if day:
                        d = by_day.setdefault(day, {"cost": 0.0, "tokens": 0})
                        d["cost"] += cost
                        d["tokens"] += inp + out + cw + cr
        except OSError:
            continue
    if not tot["messages"]:
        return None
    tot["tokens"] = tot["input"] + tot["output"] + tot["cacheRead"] + tot["cacheWrite"]
    tot["cost"] = round(tot["cost"], 2)
    return {"total": tot, "byDay": by_day}


def bob_task_index():
    """Index every IBM Bob task by the absolute workspace directory it ran in.
    Bob keeps one folder per task under BOB_TASKS with:
      ui_messages.json              — per-request usage: messages with
                                      say=='api_req_started' carry a JSON `text`
                                      of {tokensIn, tokensOut, cacheWrites,
                                      cacheReads, cost}; every message has a `ts`.
      api_conversation_history.json — contains '# Current Workspace Directory (…)'.
    Each task is one session; per-request timestamps drive the daily series.
    Unlike Claude, Bob logs a real dollar `cost` per request — no estimation.
    Returns { workspace_path: {sessions, lastTs, total{…}, byDay{…}, sessByDay{…}} }.
    """
    index = {}
    if not BOB_TASKS.is_dir():
        return index
    ws_re = re.compile(r"# Current Workspace Directory \(([^)]+)\)")
    for task in BOB_TASKS.iterdir():
        ui = task / "ui_messages.json"
        if not ui.exists():
            continue
        api = task / "api_conversation_history.json"
        ws = None
        if api.exists():
            m = ws_re.search(api.read_text(encoding="utf-8", errors="ignore"))
            if m:
                ws = m.group(1).strip()
        if not ws:
            continue
        try:
            msgs = json.loads(ui.read_text(encoding="utf-8", errors="ignore"))
        except (ValueError, OSError):
            continue
        e = index.setdefault(ws, {
            "sessions": 0, "lastTs": 0,
            "total": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0,
                      "cost": 0.0, "messages": 0},
            "byDay": {}, "sessByDay": {},
        })
        e["sessions"] += 1
        task_last = 0
        for msg in msgs:
            ts = msg.get("ts") or 0
            if ts > task_last:
                task_last = ts
            if msg.get("say") != "api_req_started":
                continue
            try:
                j = json.loads(msg.get("text") or "{}")
            except ValueError:
                continue
            inp = j.get("tokensIn") or 0
            out = j.get("tokensOut") or 0
            cw = j.get("cacheWrites") or 0
            cr = j.get("cacheReads") or 0
            cost = j.get("cost") or 0
            t = e["total"]
            t["input"] += inp
            t["output"] += out
            t["cacheWrite"] += cw
            t["cacheRead"] += cr
            t["cost"] += cost
            t["messages"] += 1
            if ts:
                day = dt.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
                d = e["byDay"].setdefault(day, {"cost": 0.0, "tokens": 0})
                d["cost"] += cost
                d["tokens"] += inp + out + cw + cr
        if task_last:
            e["lastTs"] = max(e["lastTs"], task_last)
            day = dt.datetime.fromtimestamp(task_last / 1000).strftime("%Y-%m-%d")
            e["sessByDay"][day] = e["sessByDay"].get(day, 0) + 1
    for ws, e in index.items():
        t = e["total"]
        t["tokens"] = t["input"] + t["output"] + t["cacheRead"] + t["cacheWrite"]
        t["cost"] = round(t["cost"], 2)
    return index


def bob_usage_for(index: dict, project_dir: Path):
    """Merge every Bob workspace that *is* the project folder or lives inside it
    into one usage record shaped like claude_usage() (so the rest of the pipeline
    and the dashboard treat both engines identically). Returns None when the
    project has no Bob tasks."""
    base = str(project_dir)
    matches = [e for ws, e in index.items()
               if ws == base or ws.startswith(base + os.sep)]
    if not matches:
        return None
    tot = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0,
           "cost": 0.0, "messages": 0, "tokens": 0}
    by_day, sess_by_day, sessions, last_ts = {}, {}, 0, 0
    for e in matches:
        for k in ("input", "output", "cacheRead", "cacheWrite", "messages", "tokens"):
            tot[k] += e["total"].get(k, 0)
        tot["cost"] += e["total"]["cost"]
        sessions += e["sessions"]
        last_ts = max(last_ts, e["lastTs"])
        for day, v in e["byDay"].items():
            d = by_day.setdefault(day, {"cost": 0.0, "tokens": 0})
            d["cost"] += v["cost"]
            d["tokens"] += v["tokens"]
        for day, n in e["sessByDay"].items():
            sess_by_day[day] = sess_by_day.get(day, 0) + n
    tot["cost"] = round(tot["cost"], 2)
    last_active = (dt.datetime.fromtimestamp(last_ts / 1000).strftime("%Y-%m-%d")
                   if last_ts else None)
    return {"total": tot, "byDay": by_day, "sessByDay": sess_by_day,
            "sessions": sessions, "lastActive": last_active}


def scan_bob_commands() -> list:
    """Bob's analog of shared skills: custom slash commands in ~/.bob/commands/
    (markdown + optional `description:` frontmatter — same convention as Claude)."""
    cdir = BOB_HOME / "commands"
    if not cdir.is_dir():
        return []
    out = []
    for f in sorted(cdir.glob("*.md")):
        desc = ""
        m = re.search(r"description:\s*\"?(.*)", f.read_text(errors="ignore"))
        if m:
            desc = m.group(1).strip().strip('"')[:160]
        out.append({"name": "/" + f.stem, "scope": "global", "description": desc})
    return out


def scan_bob_mcps() -> list:
    """Connected MCP servers for Bob, read straight from
    ~/.bob/settings/mcp_settings.json (Bob has no `claude mcp list` equivalent).
    stdio servers have no URL, so `host` shows the launch command instead."""
    src = BOB_HOME / "settings" / "mcp_settings.json"
    if not src.exists():
        return []
    try:
        cfg = json.loads(src.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    out = []
    for name, spec in (cfg.get("mcpServers") or {}).items():
        spec = spec or {}
        url = (spec.get("url") or "").strip()
        if url:
            host = re.sub(r"^https?://", "", url).split("/")[0]
        else:
            cmd = spec.get("command") or ""
            args = [str(a) for a in (spec.get("args") or [])][:2]
            host = " ".join([cmd, *args]).strip() or "stdio"
        disabled = bool(spec.get("disabled"))
        out.append({"name": name, "scope": "local", "url": url, "host": host,
                    "status": "Disabled" if disabled else "Configured",
                    "connected": not disabled, "account": None})
    return out


def read_higgsfield():
    """Read the persisted Higgsfield credit snapshot (higgsfield-usage.json next
    to this script) and enrich it with daily/monthly used + remaining credits
    derived from higgsfield-transactions.json. Both files are refreshed
    out-of-band via the Higgsfield MCP `balance` / `transactions` tools; this
    degrades gracefully (snapshot-only, then None) when files are absent."""
    src = HERE / "higgsfield-usage.json"
    snap = None
    if src.exists():
        try:
            snap = json.loads(src.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            snap = None
    tx = read_higgsfield_tx()
    if tx is None:
        return snap
    if snap is None:
        snap = {"credits": tx["balance"], "plan": tx.get("plan", ""),
                "asOf": tx.get("fetchedAt", "")}
    snap.update(tx["derived"])
    return snap


def read_higgsfield_tx(days: int = 30):
    """Aggregate the raw Higgsfield transaction history
    (higgsfield-transactions.json) into spend rollups + a daily series of used /
    remaining credits. `credits` is signed: negative = spend/deduct, positive =
    grant/refund. Remaining at end of a day = current balance minus the sum of
    every signed delta that happened *after* that day. Returns None when absent."""
    src = HERE / "higgsfield-transactions.json"
    if not src.exists():
        return None
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    balance = raw.get("balance", 0)
    txs = raw.get("transactions", [])
    # Per-day signed delta, used (spend), and granted (positive grants/refunds).
    by_day = {}            # date -> {"delta","used","granted"}
    by_month = {}          # YYYY-MM -> {"used","granted"}
    for t in txs:
        day = (t.get("created_at") or "")[:10]
        if not day:
            continue
        c = t.get("credits") or 0
        d = by_day.setdefault(day, {"delta": 0, "used": 0, "granted": 0})
        d["delta"] += c
        mon = day[:7]
        m = by_month.setdefault(mon, {"used": 0, "granted": 0})
        if c < 0:
            d["used"] += -c
            m["used"] += -c
        elif c > 0:
            d["granted"] += c
            m["granted"] += c
    today = dt.date.today()
    # Build the 30-day daily series with reconstructed end-of-day remaining.
    daily = []
    for i in range(days - 1, -1, -1):
        key = (today - dt.timedelta(days=i)).strftime("%Y-%m-%d")
        d = by_day.get(key, {"delta": 0, "used": 0, "granted": 0})
        after = sum(v["delta"] for k, v in by_day.items() if k > key)
        daily.append({"date": key, "used": d["used"], "granted": d["granted"],
                      "remaining": balance - after})
    today_key = today.strftime("%Y-%m-%d")
    spent_today = by_day.get(today_key, {}).get("used", 0)
    spent_7d = sum(d["used"] for d in daily[-7:])
    spent_30d = sum(d["used"] for d in daily)
    spent_month = by_month.get(today.strftime("%Y-%m"), {}).get("used", 0)
    months = [{"month": k, "used": v["used"], "granted": v["granted"]}
              for k, v in sorted(by_month.items())]
    # Renewal: anchor on the most recent positive "Subscription" grant.
    renews_on = None
    for t in txs:  # newest-first
        if (t.get("credits") or 0) > 0 and "subscription" in (t.get("display_name") or "").lower():
            day = (t.get("created_at") or "")[:10]
            if day:
                renews_on = next_renewal(int(day[8:10]))
            break
    return {
        "balance": balance,
        "plan": raw.get("plan", ""),
        "fetchedAt": raw.get("fetchedAt", ""),
        "derived": {
            "spentToday": spent_today,
            "spent7d": spent_7d,
            "spent30d": spent_30d,
            "spentMonth": spent_month,
            "renewsOn": renews_on,
            "daily": daily,
            "byMonth": months,
        },
    }


def project_tree(project_dir: Path, max_entries: int = 60) -> list:
    """Shallow structure of a project. Top-level entries always; directories
    annotated with a child count. When there are <=10 top-level directories,
    expand each one level (up to 6 children) so code projects read as a tree;
    folder-heavy projects stay compact with just counts.
    """
    tops = _tree_children(project_dir)
    expand = len([p for p in tops if p.is_dir()]) <= 10
    out = []
    for p in tops:
        if len(out) >= max_entries:
            out.append({"name": "…", "depth": 0, "dir": False, "more": True})
            break
        is_dir = p.is_dir()
        count = len(_tree_children(p)) if is_dir else 0
        out.append({"name": p.name, "depth": 0, "dir": is_dir, "count": count})
        if expand and is_dir:
            kids = _tree_children(p)
            for k in kids[:6]:
                out.append({"name": k.name, "depth": 1, "dir": k.is_dir()})
            if len(kids) > 6:
                out.append({"name": f"+{len(kids) - 6} more", "depth": 1,
                            "dir": False, "more": True})
    return out


def claude_account():
    """The Claude account (email) that claude.ai MCP connectors are authorized
    under, from ~/.claude.json. Returns the email or None."""
    cfg = HOME / ".claude.json"
    if not cfg.exists():
        return None
    try:
        acct = json.loads(cfg.read_text(encoding="utf-8")).get("oauthAccount") or {}
    except (ValueError, OSError):
        return None
    return acct.get("emailAddress")


def scan_mcps() -> list:
    """Authoritative list of connected MCP servers via `claude mcp list`.
    Output lines look like: 'claude.ai Notion: https://mcp.notion.com/mcp - ✓ Connected'.
    claude.ai-scoped connectors are tagged with the Claude account that owns them.
    """
    if ENGINE == "bob":
        return scan_bob_mcps()
    account = claude_account()
    try:
        res = subprocess.run(["claude", "mcp", "list"],
                             capture_output=True, text=True, timeout=20)
        txt = res.stdout
    except Exception:
        return []
    mcps = []
    for line in txt.splitlines():
        line = line.strip()
        if ":" not in line or "://" not in line:
            continue
        name_part, rest = line.split(":", 1)
        rest = rest.strip()
        url, status = rest, ""
        if " - " in rest:
            url, status = rest.split(" - ", 1)
        url, status, name = url.strip(), status.strip(), name_part.strip()
        scope = "local"
        if name.lower().startswith("claude.ai "):
            scope, name = "claude.ai", name[len("claude.ai "):].strip()
        connected = ("connected" in status.lower()) or status.startswith("✓")
        status_clean = status.lstrip("✓✗! ").strip() or (
            "Connected" if connected else "Unknown")
        host = re.sub(r"^https?://", "", url).split("/")[0]
        mcps.append({"name": name, "scope": scope, "url": url, "host": host,
                     "status": status_clean, "connected": connected,
                     "account": account if scope == "claude.ai" else None})
    return mcps


def session_stats(claude_dir: Path):
    files = list(claude_dir.glob("*.jsonl")) if claude_dir.is_dir() else []
    if not files:
        return 0, None, {}
    by_day, last = {}, None
    for f in files:
        ts = dt.datetime.fromtimestamp(f.stat().st_mtime)
        day = ts.strftime("%Y-%m-%d")
        by_day[day] = by_day.get(day, 0) + 1
        last = ts if last is None or ts > last else last
    return len(files), last.strftime("%Y-%m-%d"), by_day


def _git(project_dir: Path, *args, timeout=4):
    try:
        out = subprocess.run(["git", "-C", str(project_dir), *args],
                             capture_output=True, text=True, timeout=timeout)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def git_info(project_dir: Path):
    if not (project_dir / ".git").exists():
        return None, {}
    info = {
        "branch": _git(project_dir, "branch", "--show-current") or "",
        "remote": _git(project_dir, "remote", "get-url", "origin") or "",
    }
    last = _git(project_dir, "log", "-1", "--format=%cd|%s", "--date=short")
    if last and "|" in last:
        info["lastCommitDate"], info["lastCommitMsg"] = last.split("|", 1)
        info["lastCommitMsg"] = info["lastCommitMsg"][:80]
    dirty = _git(project_dir, "status", "--porcelain")
    dirty_lines = [l for l in dirty.splitlines() if l.strip()] if dirty else []
    info["dirty"] = len(dirty_lines)
    # uncommitted files: porcelain "XY path" → {code, path}; cap to keep data.js bounded.
    # Split on whitespace (not fixed offsets): _git strips the output, so the first
    # line loses its leading status space and fixed slicing would shift by one.
    files = []
    for l in dirty_lines[:50]:
        parts = l.split(None, 1)
        if len(parts) == 2:
            files.append({"code": parts[0], "path": parts[1]})
        elif parts:
            files.append({"code": "?", "path": parts[0]})
    info["dirtyFiles"] = files
    ab = _git(project_dir, "rev-list", "--left-right", "--count", "HEAD...@{u}")
    if ab and "\t" in ab:
        a, b = ab.split("\t")
        info["ahead"], info["behind"] = int(a), int(b)
        # unpushed commits (local, ahead of upstream): newest first, capped
        if int(a) > 0:
            up = _git(project_dir, "log", "@{u}..HEAD", "--format=%h\x1f%s", "--date=short")
            commits = []
            for line in (up.splitlines() if up else [])[:30]:
                if "\x1f" in line:
                    h, s = line.split("\x1f", 1)
                    commits.append({"hash": h, "subject": s[:90]})
            info["unpushedCommits"] = commits
    # commits per day, last 30 days
    since = (dt.date.today() - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    log = _git(project_dir, "log", "--since=" + since, "--format=%cd", "--date=short")
    by_day = {}
    if log:
        for d in log.splitlines():
            d = d.strip()
            if d:
                by_day[d] = by_day.get(d, 0) + 1
    info["commits30d"] = sum(by_day.values())
    return info, by_day


def scan_projects():
    projects, session_usage, commit_usage, claude_by_day = [], {}, {}, {}
    if not STARTUPS.is_dir():
        return projects, session_usage, commit_usage, claude_by_day
    bob_index = bob_task_index() if ENGINE == "bob" else {}
    for folder in sorted(STARTUPS.iterdir()):
        if not folder.is_dir() or folder.name.startswith(".") or folder.name in EXCLUDE:
            continue
        claude_dir = CLAUDE_PROJECTS / encode_claude_path(folder)
        if ENGINE == "bob":
            bu = bob_usage_for(bob_index, folder)
            sessions = bu["sessions"] if bu else 0
            last_session = bu["lastActive"] if bu else None
            sess_by_day = bu["sessByDay"] if bu else {}
            cu = {"total": bu["total"], "byDay": bu["byDay"]} if bu else None
        else:
            sessions, last_session, sess_by_day = session_stats(claude_dir)
            cu = claude_usage(claude_dir)
        for d, n in sess_by_day.items():
            session_usage[d] = session_usage.get(d, 0) + n
        git, commit_by_day = git_info(folder)
        for d, n in commit_by_day.items():
            commit_usage[d] = commit_usage.get(d, 0) + n
        if cu:
            for d, v in cu["byDay"].items():
                acc = claude_by_day.setdefault(d, {"cost": 0.0, "tokens": 0})
                acc["cost"] += v["cost"]
                acc["tokens"] += v["tokens"]

        note = find_note(folder, claude_dir)
        name = note.get("name") or pretty_name(folder.name)
        status = (note.get("status") or "idle").lower()
        if status not in STATUS_ORDER:
            status = "idle"

        arch = read_arch(folder)
        tech = [t.strip() for t in note.get("tech", "").split(",") if t.strip()]
        if not tech:
            tech = derive_tech(arch)

        knowledge = read_knowledge(folder)
        write_digest(folder, name, note, knowledge)

        # "last active" = most recent of session or git commit
        last_active = last_session
        gcd = git.get("lastCommitDate") if git else None
        if gcd and (not last_active or gcd > last_active):
            last_active = gcd

        projects.append({
            "id": folder.name,
            "name": name,
            "path": str(folder),
            "status": status,
            "sessions": sessions,
            "lastActive": last_active,
            "stack": note.get("stack", ""),
            "techStack": tech,
            "claude": cu["total"] if cu else None,
            "next": note.get("next", ""),
            "tags": [t.strip() for t in note.get("tags", "").split(",") if t.strip()],
            "milestones": note.get("milestones", []),
            "todos": note.get("todos", []),
            "summary": note.get("summary", ""),
            "memory": list_memory(claude_dir),
            "memoryDocs": read_memory_docs(claude_dir),
            "knowledge": knowledge,
            "hasNote": bool(note),
            "git": git,
            "skills": list_local_skills(folder),
            "agents": list_local_agents(folder),
            "tree": project_tree(folder),
            "arch": arch,
        })

    today = dt.date.today()
    projects.sort(key=lambda p: (
        STATUS_ORDER.get(p["status"], 9),
        (today - dt.date(*map(int, p["lastActive"].split("-")))).days
        if p["lastActive"] else 99999,
    ))
    return projects, session_usage, commit_usage, claude_by_day


def scan_skills():
    if ENGINE == "bob":
        return scan_bob_commands()
    skills = []
    sdir = CLAUDE_HOME / "skills"
    if sdir.is_dir():
        for s in sorted(sdir.iterdir()):
            if not s.is_dir():
                continue
            desc = ""
            skill_md = next(s.rglob("SKILL.md"), None)
            if skill_md and skill_md.exists():
                mm = re.search(r"description:\s*\"?(.*)", skill_md.read_text(errors="ignore"))
                if mm:
                    desc = mm.group(1).strip().strip('"')[:160]
            skills.append({"name": s.name, "scope": "global", "description": desc})
    return skills


def scan_agents():
    if ENGINE == "bob":
        return []          # Bob "modes" live in custom_modes.yaml; not surfaced yet
    adir = CLAUDE_HOME / "agents"
    if not adir.is_dir():
        return []
    return [{"name": a.stem, "scope": "global", "description": ""}
            for a in sorted(adir.glob("*.md"))]


def usage_series(sessions: dict, commits: dict, days: int = 30):
    today = dt.date.today()
    out = []
    for i in range(days - 1, -1, -1):
        key = (today - dt.timedelta(days=i)).strftime("%Y-%m-%d")
        out.append({"date": key, "sessions": sessions.get(key, 0),
                    "commits": commits.get(key, 0)})
    return out


def claude_summary(projects: list, claude_by_day: dict, days: int = 30):
    """Portfolio Claude Code usage: summed token/cost totals across projects plus
    a per-day cost+token series for the last 30 days."""
    keys = ("input", "output", "cacheRead", "cacheWrite", "tokens", "messages")
    tot = {k: 0 for k in keys}
    tot["cost"] = 0.0
    for p in projects:
        c = p.get("claude")
        if not c:
            continue
        for k in keys:
            tot[k] += c.get(k, 0)
        tot["cost"] += c.get("cost", 0.0)
    tot["cost"] = round(tot["cost"], 2)
    today = dt.date.today()
    daily = []
    for i in range(days - 1, -1, -1):
        key = (today - dt.timedelta(days=i)).strftime("%Y-%m-%d")
        d = claude_by_day.get(key, {})
        daily.append({"date": key, "cost": round(d.get("cost", 0.0), 2),
                      "tokens": d.get("tokens", 0)})
    return {"total": tot, "daily": daily}


def main():
    projects, sess_usage, commit_usage, claude_by_day = scan_projects()
    skills, agents = scan_skills(), scan_agents()
    mcps = scan_mcps()
    repos = sum(1 for p in projects if p["git"])
    claude = claude_summary(projects, claude_by_day)
    claude["renewsOn"] = claude_renewal() if ENGINE != "bob" else None
    # Only surface the Higgsfield card when a Higgsfield MCP is actually
    # connected (Claude: `claude mcp list`; Bob: ~/.bob/settings/mcp_settings.json).
    # Without a connection there's no way to refresh it, so the card is hidden.
    higgsfield_connected = any(
        "higgsfield" in (m.get("name") or "").lower() and m.get("connected")
        for m in mcps)
    higgsfield = read_higgsfield() if higgsfield_connected else None
    news = read_news()
    data = {
        "generatedAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "engine": ENGINE,
        "brand": BRAND,
        "usageProvider": USAGE_PROVIDER,
        "usageEstimated": USAGE_ESTIMATED,
        "higgsfieldConnected": higgsfield_connected,
        "root": str(STARTUPS),
        "totals": {
            "projects": len(projects),
            "active": sum(1 for p in projects if p["status"] in ("active", "in-progress")),
            "blocked": sum(1 for p in projects if p["status"] == "blocked"),
            "sessions": sum(p["sessions"] for p in projects),
            "openTodos": sum(len(p["todos"]) for p in projects),
            "repos": repos,
            "skills": len(skills),
            "agents": len(agents),
            "mcps": len(mcps),
            "claudeCost": claude["total"]["cost"],
            "claudeTokens": claude["total"]["tokens"],
        },
        "usage": usage_series(sess_usage, commit_usage),
        "claude": claude,
        "higgsfield": higgsfield,
        "news": news,
        "projects": projects,
        "skills": skills,
        "agents": agents,
        "mcps": mcps,
    }
    OUT.write_text("window.MISSION_CONTROL = " + json.dumps(data, indent=2) + ";\n",
                   encoding="utf-8")
    est = "est. " if USAGE_ESTIMATED else ""
    print(f"Wrote {OUT}  [{BRAND}]\n  {len(projects)} projects ({repos} git repos), "
          f"{data['totals']['sessions']} sessions, {len(skills)} skills, "
          f"{len(agents)} agents, {len(mcps)} MCPs. "
          f"{USAGE_PROVIDER} {est}${claude['total']['cost']:.2f} "
          f"({claude['total']['tokens']:,} tok)"
          + (f", Higgsfield {higgsfield['credits']} cr" if higgsfield else "") + ".")

    # Cascade: a default (Claude) run also refreshes the Bob MC dashboard when a
    # ~/bob projects folder exists — so one `python3 generate.py` (and therefore
    # `/update`, which calls it) keeps both dashboards current. MC_NO_CASCADE
    # guards the child against re-cascading; MC_ROOT is dropped so Bob uses its
    # own default root rather than inheriting the Claude one.
    if (ENGINE == "claude" and not os.environ.get("MC_NO_CASCADE")
            and (HOME / "bob projects").is_dir()):
        env = {k: v for k, v in os.environ.items() if k != "MC_ROOT"}
        env["MC_ENGINE"], env["MC_NO_CASCADE"] = "bob", "1"
        try:
            subprocess.run(["python3", str(Path(__file__).resolve())],
                           env=env, timeout=120)
        except Exception as e:
            print(f"  (Bob MC refresh skipped: {e})")


if __name__ == "__main__":
    main()
