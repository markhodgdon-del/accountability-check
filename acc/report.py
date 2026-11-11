"""Render the private report doc (markdown) and the Results sheet rows."""
from __future__ import annotations

RESULTS_HEADER = ["Week start", "Account", "Person", "Email", "Hours wk-3", "Hours wk-2", "Hours wk-1",
                  "Hours this week", "3-wk avg hours", "Change vs avg", "Context project hours", "Jira resolved",
                  "Jira status changes", "Open assigned tickets", "Flags", "Claude recommendation",
                  "Mark's decision", "Mark's reason", "Run", "Notes"]


def _h(x) -> str:
    return f"{x:.1f}"


def _pct(x) -> str:
    if x is None:
        return "n/a"
    return f"({abs(x):.1f}%)" if x < 0 else f"{x:.1f}%"


def doc_title(cfg: dict, week: str) -> str:
    t = f"{cfg['label']} Team Accountability Check — week of {week} (private)"
    return ("(TEST) " + t) if cfg["mode"] == "report_only" else t


def results_rows(res: dict, cfg: dict, run_label: str, context: dict | None = None) -> list[list[str]]:
    context = context or {}
    rows = []
    for p in res["people"]:
        if not p["on_roster"] and not p["week_hours"] and not p["flags"]:
            continue
        t = (p["trend_hours"] + [0, 0, 0])[:3]
        j = p["jira"]
        rows.append([
            res["week"], cfg["results_account"], p["name"], p["email"],
            _h(t[0]), _h(t[1]), _h(t[2]), _h(p["week_hours"]), _h(p["avg_hours"]), _pct(p["change_pct"]),
            _h(p["context_hours"]),
            "n/a" if j is None else str(j["resolved"]), "n/a" if j is None else str(j["moved"]),
            "n/a" if j is None else str(j["open"]),
            ", ".join(f["code"] for f in p["flags"]) or ("Mark — not flagged" if p["is_owner"] else "none"),
            p["recommendation"], "", "", run_label,
            context.get(p["email"], {}).get("note", ""),
        ])
    return rows


def render_doc(res: dict, cfg: dict, meta: dict, context: dict | None = None) -> str:
    """meta: run_time, hours_source, connection_failures[list], c_signals[list], warn_items[list],
    changes[list], sources[list]. context: email -> {"note": str, "confidence": str, "questions": [str]}."""
    context = context or {}
    by_email = {p["email"]: p for p in res["people"]}
    L = []
    L.append(f"# {doc_title(cfg, res['week'])}")
    L.append("")
    L.append(f"- **Week:** {res['week']} to {meta.get('week_end', '')} (Sun–Sat); trend weeks {', '.join(res['trend_weeks'])}")
    ids = [f"{cfg['ciq']['primary']['name']} ({cfg['ciq']['primary']['id']})"] + \
          [f"{c['name']} ({c['id']}, context)" for c in cfg["ciq"]["context"]]
    L.append(f"- **CIQ projects:** {'; '.join(ids)}")
    if res.get("jira_skipped"):
        L.append(f"- **Jira:** {cfg['jira']['project']} unreachable this run — hours-only flags (F0, F3, F6); F1, F2, F4, F5 not checked")
    else:
        L.append(f"- **Jira:** {cfg['jira']['project'] if cfg.get('jira') else 'none — hours-only flags (F0, F3, F6)'}")
    L.append(f"- **Run:** {meta.get('run_time', '')} · mode {cfg['mode']} · engine {meta.get('version', '')} ({meta.get('commit', '')})")
    L.append(f"- **Hours source:** {meta.get('hours_source', 'CIQ timesheets')}")
    L.append("- **Walk status:** pending — say \"Walk the accountability check\" in this account's project to review the flags.")
    L.append("")
    if meta.get("warn_items"):
        L.append("## ⚠ Jim / Nicole items")
        L += [f"- {x}" for x in meta["warn_items"]]
        L.append("")
    if meta.get("c_signals"):
        L.append("## Revenue (C) signals")
        L += [f"- {x}" for x in meta["c_signals"]]
        L.append("")
    tt = res["totals"]
    L.append("## Summary")
    L.append(f"- Project hours this week: {_h(tt['week_hours'])} h vs 3-week average {_h(tt['avg_hours'])} h "
             f"(trend {', '.join(_h(x) for x in tt['trend_hours'])})")
    if res["jira_enabled"]:
        L.append(f"- Jira: {tt['resolved']} resolved, {tt['moved']} with a status change")
    nflag = len(res["walk"]) + len(res["fyi"])
    L.append(f"- People flagged: {nflag} ({len(res['walk'])} to walk, {len(res['fyi'])} FYI)")
    for a in res["account_items"]:
        L.append(f"- {a['code']}: {a['text']}")
    if meta.get("connection_failures"):
        L.append(f"- Connection problems: {'; '.join(meta['connection_failures'])}")
    L.append("")
    L.append("## Per-person table")
    L.append("")
    head = ["Person", "wk-3", "wk-2", "wk-1", "This wk", "3-wk avg", "Change", "Context", "All projects"]
    if res["jira_enabled"]:
        head += ["Resolved", "Moved", "Open", "Stale"]
    head += ["Sheet status", "Flags"]
    L.append("| " + " | ".join(head) + " |")
    L.append("|" + "---|" * len(head))
    for p in res["people"]:
        t = (p["trend_hours"] + [0, 0, 0])[:3]
        row = [p["name"] + (" (not on roster)" if not p["on_roster"] else ""), *(_h(x) for x in t),
               _h(p["week_hours"]), _h(p["avg_hours"]), _pct(p["change_pct"]), _h(p["context_hours"]), _h(p["all_hours"])]
        if res["jira_enabled"]:
            j = p["jira"]
            row += [str(j["resolved"]), str(j["moved"]), str(j["open"]), str(j["stale"])]
        row += [", ".join(p["statuses"]) or "—",
                ", ".join(f["code"] for f in p["flags"]) or ("not flagged (Mark)" if p["is_owner"] else "—")]
        L.append("| " + " | ".join(row) + " |")
    L.append("")
    L.append("## Flags to walk")
    if not res["walk"]:
        L.append("- None this week.")
    for e in res["walk"]:
        p = by_email[e]
        L.append(f"### {p['name']} — recommendation: {p['recommendation']}")
        for f in p["flags"]:
            rep = " (repeat from last week)" if f["code"] in p["repeat"] else ""
            L.append(f"- {f['code']}{rep}: {f['text']}")
        c = context.get(e)
        if c and c.get("note"):
            L.append(f"- Context: {c['note']}")
        for q in (c or {}).get("questions", []):
            L.append(f"- 1:1 question: {q}")
        L.append(f"- Mark's decision ({p['name']}): pending walk")
        if c and c.get("confidence"):
            L.append(f"- Confidence: {c['confidence']}")
        L.append("")
    L.append("## FYI — not walked")
    if not res["fyi"]:
        L.append("- None.")
    for e in res["fyi"]:
        p = by_email[e]
        L.append(f"- {p['name']}: " + "; ".join(f"{f['code']} {f['text']}" for f in p["flags"]))
    L.append("")
    L.append("## Changes since last week")
    L += [f"- {x}" for x in (meta.get("changes") or res.get("changes")
                             or ["No earlier Results rows for this account to compare."])]
    L.append("")
    L.append("## Open items for Mark")
    items = res["open_items"] + (meta.get("open_items") or [])
    L += [f"- {x}" for x in items] if items else ["- None."]
    L.append("")
    L.append("## Sources and access log")
    L += [f"- {x}" for x in (meta.get("sources") or [])]
    L.append("- Confidence: High on CIQ hours and Jira counts (direct pulls, email-matched); "
             "Medium on context explanations (notes, meetings, Slack); flags are conversation starters, not verdicts.")
    return "\n".join(L) + "\n"
