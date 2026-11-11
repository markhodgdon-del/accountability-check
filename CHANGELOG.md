# Changelog

## 2.0.0 — 2026-11-11
Moved the weekly accountability check from the manual v1.2 routine into this repo (Mark, 11/11).
- Hours from CIQ only. Harvest API fallback, token and credential clean-up removed. Trend weeks before
  2026-11-01 still read CIQ's synced Harvest copy (`ciq_time_entries_actuals`, bucketed by work date); from the
  week of 11/22 the whole trend is native CIQ timesheets.
- Per-account YAML configs (M&O, Hoonigan, Grimco, Coastal Bridge Advisors) with the roster inside each config.
- CBA included from the start; Jira project CBA ("Coastal Bridge Advisors", Mark 11/11).
- Split into an unattended prep run (Wednesday afternoons, one scheduled task per account project) and an
  interactive walk; the prep run's last step asks whether to walk now.
- F5 kept, always showing the all-project total (v1.2 open question 3, Mark 11/11).
- Flags computed in Python (`acc/flags.py`) with tests; regressions on real CIQ and Jira data for the week of
  2026-11-01 (M&O and CBA).
- Jira pulls require `view: "full"`: the compact view omits assignee emails (found 11/11).
- "Status changes" counts every ticket with a status change in the week, resolutions included (matches
  earlier Results rows).
- New: hours-only fallback when Jira is unreachable (`--no-jira`), week-over-week flag changes from the Results
  sheet, new-CIQ-project discovery, re-run guard on Results rows.
