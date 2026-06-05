# Contributing to Mission Control

Thanks for being here. Mission Control is small on purpose, so contributing is meant to be easy — clone it, make a change, open it in a browser, send a PR. No build tools, no dependency hell, no CI gauntlet.

This guide gets you productive in a few minutes.

## The one rule that shapes everything

**No dependencies, no build step.** The scanner (`generate.py`) is Python **standard library only** — never add a `pip install`. The dashboards are static HTML that load a couple of libraries from a CDN. If a change would require `npm install`, a bundler, or a server, it's probably the wrong approach for this project. Keeping it zero-install is the whole point.

A few rules that follow from that:

- **Don't hand-edit generated files.** `data.js` and every `knowledge/context.md` are written by `generate.py`. Change the generator, not its output.
- **Don't commit personal data.** `data.js`, the Higgsfield JSON, and generated digests are git-ignored for a reason — they contain real project info. Keep them out of PRs.
- **Degrade gracefully.** Every input (a note, a diagram, a knowledge folder, git, Higgsfield) is optional. A missing input should just drop its panel, never crash a page.
- **Match the look.** The UI is vanilla JS with a shared set of dark-theme CSS variables. No frameworks. Reuse the existing tokens and components (`.panel`, `.card`, `.callout`, tables) so new UI feels native.

## Local development

```bash
git clone https://github.com/NeaamHariri/mission-control.git
cd mission-control
python3 generate.py        # builds data.js from the folder this repo lives in
open index.html            # or just double-click it
```

`generate.py` scans the **parent folder** of the checkout for projects. Two ways to get data to work against:

- **Use your own projects** — clone into your existing projects folder (e.g. `~/Startups/mission-control`) and it scans them.
- **Use a throwaway test root** — make a folder with one or two dummy project subfolders, each containing a `mission-control.md`, then point the scanner at it:
  ```bash
  MC_ROOT=/tmp/mc-test python3 generate.py
  ```

Then open `index.html` / `project.html?id=<folder>` and check the **browser console for errors** — that's the test bar for a UI change.

## Where things live

| Area | File |
|---|---|
| The scanner (data layer) | `generate.py` |
| Overview dashboard | `index.html` |
| Per-project drilldown | `project.html` |
| Docs / news / tips pages | `guide.html`, `news.html`, `best-practices.html` |
| Slash commands (source of truth) | `commands/*.md` |

For a deeper map — the `data.js` schema, the module layout of `generate.py`, and the render pipeline — read **`knowledge/architecture.md`**, or open **`guide.html`** in a browser for the visual walkthrough.

> Editing a `/update*` command? Change it in `commands/` (the source of truth), then run `./setup.sh` to reinstall it into `~/.claude/commands/`.

## Good first contributions

- A new optional per-project panel (it must degrade gracefully when its input is absent).
- `gh`-based GitHub status (open PRs, CI checks) in the repository panel.
- Better empty states, accessibility, or responsive behavior on the HTML pages.
- New `mission-control.md` fields, or polish to the architecture-diagram styling.
- Docs fixes and clearer guide copy.

Not sure if an idea fits? **Open an issue first** and ask — happy to talk it through before you write code.

## Opening a pull request

1. **Branch** off `main` (`git checkout -b your-feature`).
2. Keep PRs **small and focused** — one change per PR is easier to review and merge.
3. **Test it**: run `python3 generate.py` (no errors) and open the affected page(s) with a clean console.
4. For any UI change, **include a before/after screenshot** in the PR description. Use sanitized/demo data — never post real project data.
5. Write a clear title and a short description of *what* and *why*. Conventional-style prefixes (`feat:`, `fix:`, `docs:`) are appreciated but not required.

## Reporting bugs

Open an issue with: what you did, what you expected, what happened, and your OS + Python version (`python3 --version`). A console error or screenshot helps a lot.

## License

By contributing, you agree your contributions are licensed under the project's [MIT License](LICENSE).
