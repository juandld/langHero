<!-- Generated from orchestratorHero/AGENTS.md by scripts/ops/harness_sync.py; edit the section there. -->
## Files per task

A task should leave behind the change it was for, not a trail of helper files (David, 2026-11-22: "i need a beter
reusable code culture to mitigate the amount of files made for a single task"; `development/wip/reusable_code_20261122/`).

- **Search for an existing tool first.** Grep the disk by behaviour (what it does, not what you would name it) across
  `scripts/`, `development/` and the sibling hero repos before writing a script.
- **Scratch only through `scripts/ops/scratch.py`** (`dir <label>`, `checkout <repo> <rev>`, `compare-invariants`,
  `done`), never loose in `/tmp` or in a repo. No full repo copies for comparisons: use `checkout`.
- **Fix a file in place.** Never `fixN` / `stepN` / `tryN` / `vN` copies of a script; git keeps the old version.
  Invariant 212 fails on new throwaway-named scripts (`fix<N>`, `step<N>`, `try<N>`, `scratch*`, `_explore*`, `tmp_*`).
- **One wip doc per topic** (`development/wip/<topic>_<YYYYMMDD>.md` or a folder for a multi-brief plan); update it,
  don't start a second one.
- **Remove what you made when the task ends**: `scratch.py done`, and delete helpers nothing will run again.
- **A helper two tasks need becomes a shared tool** (`scripts/ops/`, `scripts/lib/`, heroCommon) with a usage line,
  instead of a second copy.
