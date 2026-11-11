# accountability-check — notes for build sessions
- Scheduled runs follow ROUTINE.md and never commit. Only a build session Mark has approved commits here.
- Run `python3 -m pytest -q` before every commit; the two real-week regressions must pass unchanged unless
  Mark has approved the rule change behind a difference.
- Keep account-specific values in configs/*.yaml, never in acc/ or ROUTINE.md.
- After changing a schedule or the task prompt, regenerate INSTALL.md (see README) and tell Mark which
  account's install prompt must be re-run.
