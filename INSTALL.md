# Install prompts

Paste each one into a **new chat inside that account's Engagement Lead project** (a scheduled task runs in the project of the chat that creates it). Regenerate with `python3 -m acc.cli install-prompt --config configs/<account>.yaml` after any schedule change.

## M&O — Meadows & Ohly - Engagement Lead

````text
Install the weekly accountability check for M&O in this project.

1. Create one scheduled task with create_trigger:
   - name: "M&O - Weekly Accountability Check (CIQ)"
   - cron_expression: "CRON_TZ=America/New_York 47 13 * * 3"
   - initiation: human_request
   - notifications: {"push": true}
   - prompt (exactly the text between the lines):
-----
Weekly team accountability check — M&O (ACCOUNT=mo). Repo markhodgdon-del/accountability-check, config configs/mo.yaml.
1. Get the code: add_repo {owner: "markhodgdon-del", repo: "accountability-check", access: "read"}, then
   git clone --depth 1 --branch main https://github.com/markhodgdon-del/accountability-check /home/user/accountability-check
   If either fails, retry once. Still failing: send ONE push notification "M&O accountability check: repo unreachable — no run this week" and stop. Never run from memory or an old copy.
2. Read /home/user/accountability-check/ROUTINE.md and follow it exactly with ACCOUNT=mo. The run mode comes only from configs/mo.yaml.
3. You are unattended until ROUTINE step 11: never ask questions or use AskUserQuestion before it.
4. Read-only on CIQ (ciq_query only; never ciq_change or ciq_safe_change), Jira, Slack, Fireflies, Calendar and Gmail. The only writes are the ones in ROUTINE step 9 (and, if Mark says yes to the walk, WALK.md step 4). Never commit to the repo.
5. Last step (ROUTINE step 11): ask Mark whether to walk the accountability check now, yes or no.
-----
2. Save this project doc with the Projects tool (project_write, path "claude/accountability-walk.md"), exactly the text between the lines:
-----
# Accountability walk — M&O

When Mark says "Walk the accountability check" in this project: add_repo {owner: "markhodgdon-del", repo: "accountability-check", access: "read"}, clone it, read WALK.md and configs/mo.yaml, and follow WALK.md. The weekly prep runs as the scheduled task "M&O - Weekly Accountability Check (CIQ)".
-----
3. Run the new task once now as the install test (fire_trigger with its trigger id). The repo config is in report_only mode, so it writes only a "(TEST)" doc and no Results rows.
4. Tell me: the trigger id, its schedule in ET, its approval setting, and that the test run started.
````

## Hoonigan — Hoonigan - Engagement Lead

````text
Install the weekly accountability check for Hoonigan in this project.

1. Create one scheduled task with create_trigger:
   - name: "Hoonigan - Weekly Accountability Check (CIQ)"
   - cron_expression: "CRON_TZ=America/New_York 7 14 * * 3"
   - initiation: human_request
   - notifications: {"push": true}
   - prompt (exactly the text between the lines):
-----
Weekly team accountability check — Hoonigan (ACCOUNT=hoonigan). Repo markhodgdon-del/accountability-check, config configs/hoonigan.yaml.
1. Get the code: add_repo {owner: "markhodgdon-del", repo: "accountability-check", access: "read"}, then
   git clone --depth 1 --branch main https://github.com/markhodgdon-del/accountability-check /home/user/accountability-check
   If either fails, retry once. Still failing: send ONE push notification "Hoonigan accountability check: repo unreachable — no run this week" and stop. Never run from memory or an old copy.
2. Read /home/user/accountability-check/ROUTINE.md and follow it exactly with ACCOUNT=hoonigan. The run mode comes only from configs/hoonigan.yaml.
3. You are unattended until ROUTINE step 11: never ask questions or use AskUserQuestion before it.
4. Read-only on CIQ (ciq_query only; never ciq_change or ciq_safe_change), Jira, Slack, Fireflies, Calendar and Gmail. The only writes are the ones in ROUTINE step 9 (and, if Mark says yes to the walk, WALK.md step 4). Never commit to the repo.
5. Last step (ROUTINE step 11): ask Mark whether to walk the accountability check now, yes or no.
-----
2. Save this project doc with the Projects tool (project_write, path "claude/accountability-walk.md"), exactly the text between the lines:
-----
# Accountability walk — Hoonigan

When Mark says "Walk the accountability check" in this project: add_repo {owner: "markhodgdon-del", repo: "accountability-check", access: "read"}, clone it, read WALK.md and configs/hoonigan.yaml, and follow WALK.md. The weekly prep runs as the scheduled task "Hoonigan - Weekly Accountability Check (CIQ)".
-----
3. Run the new task once now as the install test (fire_trigger with its trigger id). The repo config is in report_only mode, so it writes only a "(TEST)" doc and no Results rows.
4. Tell me: the trigger id, its schedule in ET, its approval setting, and that the test run started.
````

## Grimco — Grimco - Engagement Lead

````text
Install the weekly accountability check for Grimco in this project.

1. Create one scheduled task with create_trigger:
   - name: "Grimco - Weekly Accountability Check (CIQ)"
   - cron_expression: "CRON_TZ=America/New_York 23 14 * * 3"
   - initiation: human_request
   - notifications: {"push": true}
   - prompt (exactly the text between the lines):
-----
Weekly team accountability check — Grimco (ACCOUNT=grimco). Repo markhodgdon-del/accountability-check, config configs/grimco.yaml.
1. Get the code: add_repo {owner: "markhodgdon-del", repo: "accountability-check", access: "read"}, then
   git clone --depth 1 --branch main https://github.com/markhodgdon-del/accountability-check /home/user/accountability-check
   If either fails, retry once. Still failing: send ONE push notification "Grimco accountability check: repo unreachable — no run this week" and stop. Never run from memory or an old copy.
2. Read /home/user/accountability-check/ROUTINE.md and follow it exactly with ACCOUNT=grimco. The run mode comes only from configs/grimco.yaml.
3. You are unattended until ROUTINE step 11: never ask questions or use AskUserQuestion before it.
4. Read-only on CIQ (ciq_query only; never ciq_change or ciq_safe_change), Jira, Slack, Fireflies, Calendar and Gmail. The only writes are the ones in ROUTINE step 9 (and, if Mark says yes to the walk, WALK.md step 4). Never commit to the repo.
5. Last step (ROUTINE step 11): ask Mark whether to walk the accountability check now, yes or no.
-----
2. Save this project doc with the Projects tool (project_write, path "claude/accountability-walk.md"), exactly the text between the lines:
-----
# Accountability walk — Grimco

When Mark says "Walk the accountability check" in this project: add_repo {owner: "markhodgdon-del", repo: "accountability-check", access: "read"}, clone it, read WALK.md and configs/grimco.yaml, and follow WALK.md. The weekly prep runs as the scheduled task "Grimco - Weekly Accountability Check (CIQ)".
-----
3. Run the new task once now as the install test (fire_trigger with its trigger id). The repo config is in report_only mode, so it writes only a "(TEST)" doc and no Results rows.
4. Tell me: the trigger id, its schedule in ET, its approval setting, and that the test run started.
````

## Coastal Bridge Advisors — Coastal Bridge Advisors - Engagement Lead

````text
Install the weekly accountability check for Coastal Bridge Advisors in this project.

1. Create one scheduled task with create_trigger:
   - name: "Coastal Bridge Advisors - Weekly Accountability Check (CIQ)"
   - cron_expression: "CRON_TZ=America/New_York 41 14 * * 3"
   - initiation: human_request
   - notifications: {"push": true}
   - prompt (exactly the text between the lines):
-----
Weekly team accountability check — Coastal Bridge Advisors (ACCOUNT=cba). Repo markhodgdon-del/accountability-check, config configs/cba.yaml.
1. Get the code: add_repo {owner: "markhodgdon-del", repo: "accountability-check", access: "read"}, then
   git clone --depth 1 --branch main https://github.com/markhodgdon-del/accountability-check /home/user/accountability-check
   If either fails, retry once. Still failing: send ONE push notification "Coastal Bridge Advisors accountability check: repo unreachable — no run this week" and stop. Never run from memory or an old copy.
2. Read /home/user/accountability-check/ROUTINE.md and follow it exactly with ACCOUNT=cba. The run mode comes only from configs/cba.yaml.
3. You are unattended until ROUTINE step 11: never ask questions or use AskUserQuestion before it.
4. Read-only on CIQ (ciq_query only; never ciq_change or ciq_safe_change), Jira, Slack, Fireflies, Calendar and Gmail. The only writes are the ones in ROUTINE step 9 (and, if Mark says yes to the walk, WALK.md step 4). Never commit to the repo.
5. Last step (ROUTINE step 11): ask Mark whether to walk the accountability check now, yes or no.
-----
2. Save this project doc with the Projects tool (project_write, path "claude/accountability-walk.md"), exactly the text between the lines:
-----
# Accountability walk — Coastal Bridge Advisors

When Mark says "Walk the accountability check" in this project: add_repo {owner: "markhodgdon-del", repo: "accountability-check", access: "read"}, clone it, read WALK.md and configs/cba.yaml, and follow WALK.md. The weekly prep runs as the scheduled task "Coastal Bridge Advisors - Weekly Accountability Check (CIQ)".
-----
3. Run the new task once now as the install test (fire_trigger with its trigger id). The repo config is in report_only mode, so it writes only a "(TEST)" doc and no Results rows.
4. Tell me: the trigger id, its schedule in ET, its approval setting, and that the test run started.
````
