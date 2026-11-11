# Walk the accountability check (interactive)

Start: "Yes — walk it now" at the end of a prep run, or Mark saying "Walk the accountability check" in an
account's Engagement Lead project. Recommend only: Mark decides every flag.

## 0. Find the week
- **Same session as the prep run:** use `$RUN/res.json`, `$RUN/context.json` and the doc link.
- **New chat:** clone the repo (read-only), read `configs/<account>.yaml` (the project doc
  `claude/accountability-walk.md` names the account). Find the newest doc in `output.doc_folder` whose title
  contains "<label> Team Accountability Check — week of" and is not already walked (its "Walk status" line says
  pending). Read it, and read this WEEK's Results rows for `results_account`. Work from those; do not re-pull
  CIQ or Jira. If Mark names a week, use that week.

## 1. Summary first (≤5 lines)
Total hours vs 3-week average; Jira resolved / changed; milestone watch (Grimco); people flagged; any ⚠ item
(Jim Johnson / Nicole Kosky) and any revenue (C) signal.

## 2. One question per flagged person
Walk list order (repeat flags and milestone items first; at most `max_walk_flags`; the rest are FYI).
Up to four people per AskUserQuestion call. Each question shows the facts in 2–3 lines and the context note,
with Claude's recommendation first and marked "(Recommended)":
"Raise in 1:1" / "Note only" / "Dismiss — explained", plus "Skip". Escapes: "list" (show the rest at once),
"stop" (keep what's decided; the rest stay pending).

- **Dismiss — explained → ask why, right away.** Before the next person: "Why is <name>'s flag explained?"
  with 2–3 likely reasons from the evidence (e.g. "Out of office", "Time logged to another project by agreement")
  plus Other. Record the answer as the reason; skipped → "not given". If the chosen option itself stated the
  reason, record it and say so.
- **Raise in 1:1:** record one or two neutral, open questions Mark can use (from context.json or new).

## 3. During the walk
- A reminder or to-do Mark asks for goes to the Delivery Action Plan (sheet 1rmAKzISbWznNVj18aOhgZz1bEvJ8lJnU_Ms8KbwRDII)
  by its Rules tab: update the existing row on the same subject rather than adding one; log it on its Updates tab.
- A Jira change Mark directs (e.g. unassigning tickets): confirm ticket by ticket, make it with Atlassian_MCP
  `editJiraIssue`, check the response, and log it in the doc.
- Nothing else is written. Never post to Slack or email.

## 4. Record decisions
- **Doc** (Google Docs `update_doc`, `replaceAllText`, matchCase):
  - each `- Mark's decision (<name>): pending walk` → `- Mark's decision (<name>): <decision> — <reason or 1:1 questions>`
  - the "Walk status" line → `- **Walk status:** walked <date> — <n> raised, <n> noted, <n> dismissed, <n> skipped`
  - add every write made during the walk to "Sources and access log".
- **Results sheet** (`live` mode only): for each walked person, find the row with this Week start, Account and
  Email; write "Mark's decision" (column Q) and "Mark's reason" (column R) with `update_values` at that exact
  row. Every "Dismiss — explained" carries its reason. Never add or move rows. In `report_only` mode the doc
  is the only record.

## 5. Close
One line: doc link, raised / noted / dismissed / skipped counts, and any Delivery Action Plan or Jira change made.
