# LangHero systemd timers

Two timers that complete the observability loop. They're authored here (David's
VPS user can read but can't write `/etc/systemd/system/` without password-sudo),
so pasting the install block below is a one-time, three-command step.

## Install (paste on the VPS)

```bash
sudo install -m 644 \
  /home/claude-user/projects/langHero/backend/scripts/systemd/langhero-full-pass.service \
  /home/claude-user/projects/langHero/backend/scripts/systemd/langhero-full-pass.timer \
  /home/claude-user/projects/langHero/backend/scripts/systemd/langhero-capability.service \
  /etc/systemd/system/

sudo tee /etc/systemd/system/langhero-capability.timer > /dev/null <<'UNIT'
[Unit]
Description=Weekly: run Jev capability-drift probe
Requires=langhero-capability.service

[Timer]
# Sunday 04:17 local — weekly, well after the nightly full-pass.
OnCalendar=Sun *-*-* 04:17:00
RandomizedDelaySec=10min
Persistent=true
Unit=langhero-capability.service

[Install]
WantedBy=timers.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now langhero-full-pass.timer langhero-capability.timer
systemctl list-timers --all | grep langhero
```

## Verify (after paste)

```bash
# These two FAILs on the improvements suite should flip PASS:
cd /home/claude-user/projects/langHero && python3 tests/improvements/suite.py | grep langhero
```

Expected: both `obs_full_pass_cron` and `obs_capability_cron` go from FAIL to
PASS, bringing the dashboard to 18/18 (100%).

## What each one does

- **langhero-full-pass.timer** (nightly 03:17): grades all practice + dialogue +
  legacy content through Jev. Picks up: content edits that tanked a scene, LLM
  provider drift, prompt regressions. Each row lands in `backend/storage/grades.sqlite`.
- **langhero-capability.timer** (weekly Sun 04:17): re-runs the capability probe
  to detect Jev model drift (register/timing/transition/set-phrase baselines).
  Fails non-zero if any baseline shifts.

Both are nice'd (`Nice=10`, `IOSchedulingClass=idle`) so they can't steal
from live user traffic.
