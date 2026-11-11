# Weekly Team Accountability Check — prep run

Engine v2.0. Replaces the manual v1.2 routine (claude/accountability-review-routine.md in the Personal
Assistant project). Hours come only from CIQ (CustomerIQ); Harvest is retired.

The scheduled task gives you `ACCOUNT` (mo, hoonigan, grimco or cba). Everything account-specific is in
`configs/$ACCOUNT.yaml`; read it first. The run mode (`report_only` or `live`) comes only from that file.

## Ground rules
- **Unattended until step 11.** Never ask questions and never use AskUserQuestion before step 11.
  Take the most conservative reading, carry on, and list anything uncertain under "Open items for Mark".
- **Read-only everywhere** except the writes listed in step 9. CIQ: `ciq_query` only (`tenant.user.me`,
  `tenant.query.sql`); never `ciq_change` or `ciq_safe_change`. No Jira, Slack, email, calendar or client-channel writes.
- Never select bill or cost rates. Hours only. No other clients' project names in the doc (the SQL already
  sums them as "other").
- Match people strictly by lowercase email. Never guess an email, never match by name.
- Flags are 1:1 conversation starters, never verdicts. Neutral wording. Use "we" for the team.
- Never commit or push to this repo. Never compute dates by hand.
- Shell: work in `RUN=/home/user/acc-run` (create it). Install once:
  `python3 -m pip install -q pyyaml pytest --break-system-packages`.

## 1. Self-test and dates
```bash
cd /home/user/accountability-check
python3 -m pytest -q            # any failure: notify (step 10) "engine self-test failed" and stop
python3 -m acc.cli check-configs
TODAY=$(TZ=America/New_York date +%F)
python3 -m acc.cli dates --config configs/$ACCOUNT.yaml --run-date $TODAY | tee $RUN/dates.json
```
`dates.json` gives WEEK (Sunday), WEEK_END (Saturday), TREND weeks, the doc title, and whether the trend
still reaches back before 2026-11-01 (`uses_harvest_copy`).

## 2. Connection check (one quick call each, in parallel)
| Check | Call | If it fails |
|---|---|---|
| CIQ | `ciq_query` `tenant.user.me` — roles must include time-sheet-approver or admin | Notify and stop |
| Results sheet | `get_values` `Results!A1:T1` — must equal `RESULTS_HEADER` in acc/report.py | Notify and stop |
| Doc folder | Drive `search_files` `parentId = '<output.doc_folder>'` (pageSize 1) | Notify and stop |
| Jira (if `jira` set) | `searchJiraIssuesUsingJql` `project = <KEY>` maxResults 1 | Retry once after ~60 s; still failing → hours-only run (`--no-jira`), say so first in Open items |
| Slack, Fireflies, Calendar | one call each | Note it; carry on (context only) |

Use the Atlassian_MCP tools (`mcp__Atlassian_MCP__*`), never the old `mcp__Atlassian__*` connector.

## 3. CIQ pulls (read-only, `tenant.query.sql`)
Render each query with the engine; never substitute values by hand:
```bash
python3 -m acc.cli sql users --config configs/$ACCOUNT.yaml --run-date $TODAY > $RUN/users.sql
python3 -m acc.cli sql hours --config configs/$ACCOUNT.yaml --run-date $TODAY > $RUN/hours.sql
```
1. **Projects:** `select id, name from projects where id in (<every ciq id in the config>)` must return one
   row per id. A missing primary project: notify and stop. A missing context project: Open item; carry on.
2. **New projects:** `select id, name from projects where (<name ilike '%x%' for each rediscover_names>)`
   minus the config ids → each one is an Open item: "New CIQ project <name> (<id>) — add as context?".
3. **Users:** run `users.sql`; save the result exactly as returned to `$RUN/users.json`.
4. **Hours:** run `hours.sql`; save exactly as returned to `$RUN/ciq.json`. If `hasMore` is true, notify
   "incomplete CIQ pull" and stop.
5. **Harvest-copy freshness** (only when `uses_harvest_copy` is true):
   `select max(last_synced_at)::text from ciq_time_entries_actuals` — note it in the sources list.
   Unmapped users: `select * from ciq_timekeeping_unmapped_sources where source_type = 'harvest_user'` —
   list any whose email is on the roster as Open items.

## 4. Jira pulls (only if the config has `jira`)
Every query: `cloudId: d022b3c8-ca9e-47eb-b722-065424a0dc28`, **`view: "full"`** (the compact view drops
assignee emails and the engine rejects it), `fields: ["assignee","updated","duedate","labels"]`,
`maxResults: 100`. Page with `nextPageToken` until `isLast` is true. Save **each page exactly as returned** to
`$RUN/jira/<query>_<n>.json` (n = 1, 2, …). A result the tool saved to a file instead of returning inline:
copy that file's JSON as the page. W = WEEK, E = WEEK_END, N = WEEK_END + 7 days (compute in bash).

| query | JQL |
|---|---|
| resolved | `project = KEY AND resolved >= "W" AND resolved <= "E 23:59"` |
| moved | `project = KEY AND status CHANGED DURING ("W", "E 23:59")` |
| open | `project = KEY AND statusCategory != Done AND assignee is not EMPTY` |
| stale_in_progress | `project = KEY AND statusCategory = "In Progress" AND assignee is not EMPTY AND updated < "W"` |
| unassigned_in_progress | `project = KEY AND statusCategory = "In Progress" AND assignee is EMPTY` |
| milestone_watch | if `milestone_watch: true`: `project = KEY AND statusCategory != Done AND (labels in (<milestone_labels>) OR duedate <= "N")`; otherwise save `{"data":{"isLast":true,"issues":[]}}` as `milestone_watch_1.json` |

On "requires authorization" or a timeout: retry once after ~60 s. Still failing: use `--no-jira` in step 6.
Bulk touches: if many `moved` tickets share one `updated` minute (e.g. a grooming pass), add an Open item
saying status changes overstate delivery this week.

## 5. Last week's flags
`get_values` `Results!A:T`. Rows whose Week start = WEEK − 7 days and Account = `results_account` →
`$RUN/prev.json` as `{"<email>": "<Flags column>"}`. If rows for **this** WEEK and account already exist,
note it — step 9 must not add a second set.

## 6. Flags
```bash
python3 -m acc.cli prep --config configs/$ACCOUNT.yaml --run-date $TODAY \
  --ciq $RUN/ciq.json --users $RUN/users.json --jira-dir $RUN/jira --prev $RUN/prev.json --out $RUN
# add --no-jira (and drop --jira-dir) when step 2 or 4 said Jira is unreachable
```
It prints the flagged people. `$RUN/res.json` holds every number; never change a number or a flag by hand.

## 7. Context (light touch; flagged people only)
Goal: one-line explanations Mark can use in the walk. Stay neutral.
- **CIQ detail:** `python3 -m acc.cli sql week_detail … --emails <flagged emails>` → task, daily hours, notes,
  sheet status. Hoonigan (`sow_tagging: true`): if notes clearly belong to the SAP/ERP Data Cleansing SOW,
  say so and name the SOW on every item.
- **Fireflies:** one `fireflies_get_transcripts` call for WEEK..WEEK_END; keep meetings whose titles match
  `fireflies_titles`; read only their summaries. Attendee lists are invitees, not speakers.
- **Calendar:** account meetings and OOO events for the week.
- **Slack:** the config channels for WEEK (exact epochs). Look only for OOO, blockers, reassignments.
  Also Nicole's timesheet reminders and #ar-ciq-time-tracking-formerly-harvest.
- Anything where **Jim Johnson or Nicole Kosky** discusses team effort, hours or the account → `warn_items`.
- Anything that looks like expansion, follow-on scope or a change request → `c_signals` (always flag these).

Write `$RUN/context.json`: `{"<email>": {"note": "...", "confidence": "High|Medium|Low", "questions": ["..."]}}`
— `questions` (one or two neutral, open 1:1 questions) only for people recommended "Raise in 1:1". Many legitimate
hours don't move Jira (workshops, client/vendor calls, access chasing, data work, decks, reviews); say so when that
could explain a flag.

Write `$RUN/meta.json`: `run_time`, `hours_source` ("CIQ timesheets" plus "CIQ's synced Harvest copy for <weeks>"
when used), `run_label` ("<TODAY> scheduled (CIQ)"), `connection_failures`, `warn_items`, `c_signals`,
`open_items` (everything from steps 2–5 and 7), `sources` (each source with timeframe and row/page counts).

## 8. Render
```bash
python3 -m acc.cli report --config configs/$ACCOUNT.yaml --res $RUN/res.json --meta $RUN/meta.json \
  --context $RUN/context.json --out $RUN
```
Read `$RUN/doc.md` once top to bottom: no rates, no other clients' names, no judgmental adjectives.

## 9. Write (the only writes this run makes)
1. **Doc** (both modes), in `output.doc_folder`, titled exactly `title` from res.json:
   - Search the folder for that exact title first. If it exists, replace its content in place (same link)
     with `$RUN/doc.md`. Otherwise create it once with Drive `create_file`, `contentMimeType: text/markdown`
     (converts headings, bullets and tables). Never create drafts or a second copy.
   - Read it back once and check the per-person table rendered.
2. **Results rows** — `live` mode only, and only if step 5 found no rows for this WEEK and account:
   - Read `Results!A:A`; the first empty row is R. Write `$RUN/results_rows.json` rows with `update_values` at
     `Results!A<R>:T<R+n-1>` (valueInputOption RAW, as earlier rows). **Never `append_values`** (the table runs to row 1000, so appends
     land at row 1001).
   - Read back the range; the row count and emails must match. A per-minute quota error: wait ~60 s, retry once.
   - `report_only` mode: write no rows; say "TEST run — no Results rows" in the summary.

## 10. Notify
Send one push notification: "<label> accountability check ready — week of WEEK: N flagged (walk M), open items K.
Walk pending." On a stop in an earlier step, send the stop reason instead and end the run.

## 11. Final step — offer the walk
Only after steps 9–10 are done. If AskUserQuestion is available, ask exactly one question:
- question: "Walk the accountability check for <label> (week of WEEK, N flagged) now?"
- options: "Yes — walk it now" / "No — later"

**Yes** → follow `WALK.md` in this session, using `$RUN` (res.json, context.json, the doc link).
**No**, no answer, or AskUserQuestion unavailable → end with: the doc link, the one-line summary, and
"Say 'Walk the accountability check' in this project when you're ready."

Final reply (always): doc link; people flagged (walk / FYI); Results rows written or not and why; every stop,
fallback (hours-only, Harvest copy) and open item.
