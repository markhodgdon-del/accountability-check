# accountability-check

Weekly team accountability check for Mark Hodgdon's AnswerRocket accounts: **CIQ hours vs Jira activity**,
per person, as 1:1 conversation starters. Replaces the manual v1.2 routine (Harvest retired; CIQ only).

| Account | Config | Jira | Runs (ET) | Installed from project |
|---|---|---|---|---|
| M&O | `configs/mo.yaml` | MEADOWSOH | Wed 1:47pm | Meadows & Ohly - Engagement Lead |
| Hoonigan (Call Queue/CRM) | `configs/hoonigan.yaml` | HOON | Wed 2:07pm | Hoonigan - Engagement Lead |
| Grimco | `configs/grimco.yaml` | GRIM + milestone watch | Wed 2:23pm | Grimco - Engagement Lead |
| Coastal Bridge Advisors | `configs/cba.yaml` | CBA | Wed 2:41pm | Coastal Bridge Advisors - Engagement Lead |

## How it fits together
- **Engine** (same for every account): `ROUTINE.md` (prep run), `WALK.md` (interactive walk), `acc/` (flag rules,
  doc and Results rows; pure Python, no network), `sql/` (read-only CIQ queries).
- **Config** (one per account): CIQ projects, Jira, Slack, Fireflies, roster, thresholds, schedule, mode.
- **Scheduled task** (one per account, ~10 lines): clones this repo and follows `ROUTINE.md` for its account.
  It must be created from a chat in that account's project, so it runs with that project's context.
- **Walk**: the prep run's last step asks "walk now? yes/no". Yes walks the flags in that session; no leaves
  it for later — say "Walk the accountability check" in the account's project.

## Outputs
- Private Google Doc per account per week in "06 - Accountability Checks" (00 Personal Assistant).
- Rows in "INTERNAL – Accountability Check Results" (tab Results) — `live` mode only; the walk fills in
  Mark's decision and reason.

## Modes
`mode: report_only` writes a "(TEST)" doc and no Results rows. `mode: live` writes both. Mark switches it
per account by editing the config and committing.

## Flags (unchanged from v1.2)
F0 no time entered · F1 hours, little Jira movement · F2 Jira movement, few hours · F3 hours swing vs 3-week
average · F4 stale work / milestone watch · F5 presence gap (always shows the all-project total) · F6 data
hygiene (blank-note rows, unassigned in-progress tickets). Mark's own row is never flagged.
Thresholds: `acc/config.py` `DEFAULT_THRESHOLDS`, overridable per account.

## Change something
- A setting (roster, channel, threshold, mode): edit the account's YAML, run `python3 -m pytest -q`, commit.
- The schedule: edit `schedule:`, commit, then re-run that account's install prompt in its project.
- A flag rule: change `acc/flags.py` and its tests; both real-week regressions
  (`tests/fixtures/*_2026-11-01*`) must still pass.

## Install
`python3 -m acc.cli install-prompt --config configs/<account>.yaml` prints the prompt to paste into a chat in
that account's project. `INSTALL.md` has all four.
