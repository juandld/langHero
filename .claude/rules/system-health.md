<!-- Generated from orchestratorHero/AGENTS.md by scripts/ops/harness_sync.py; edit the section there. -->
## System health

Before sizing the disk, memory or services by hand (`du`, `df`, `free`, `systemctl --failed`), run the probe
(David, 2026-11-23; `development/wip/system_health_20261123/`):

- `python3 /home/claude-user/projects/osHero/health_probe.py` (same as `all`): disk by area with the unexplained
  remainder, memory and swap, failed units, containers, red cron jobs, pending root steps. Add `--json` to parse it.
- `python3 /home/claude-user/projects/osHero/health_probe.py disk --since 1h|24h|7d`: what grew, from the 10-minute
  samples (30 days kept). Measure by hand only what the probe cannot see (`/var/lib/docker`, `/root`, Nellie's
  volume): file a root step for those.
- The same data is on the dashboard: click a tile of the activity monitor, or `GET /api/health/system` and
  `GET /api/health/disk?since=24h` on localhost:8000.
