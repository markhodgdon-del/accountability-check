"""F0-F6 flag rules. Pure functions over saved CIQ and Jira results; no network.

Flags are 1:1 conversation starters, never verdicts. Each is phrased as a question.
"""
from __future__ import annotations

from .config import project_ids
from .jira import by_assignee

ORDER = ["F4", "REPEAT", "F1", "F2", "F3", "F5", "F0", "F6"]   # walk priority (v1.2 Step 5.2)


def _f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _n(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def hours_table(rows: list[dict], cfg: dict, wk: dict) -> dict:
    """email -> {name, by_week{week: {primary, context, other, blank_rows, statuses}}}"""
    primary = cfg["ciq"]["primary"]["id"]
    context = {c["id"] for c in cfg["ciq"]["context"]}
    acct = set(project_ids(cfg))
    weeks = {str(w) for w in wk["trend"] + [wk["week"]]}
    people: dict = {}
    for r in rows:
        e = (r.get("email") or "").lower()
        if not e or r["week"] not in weeks:
            continue
        p = people.setdefault(e, {"name": r.get("name") or e, "by_week": {}})
        b = p["by_week"].setdefault(r["week"], {"primary": 0.0, "context": 0.0, "other": 0.0,
                                                "blank_rows": 0, "statuses": set()})
        h = _f(r["hours"])
        if r["project"] == primary:
            b["primary"] += h
        elif r["project"] in context:
            b["context"] += h
        else:
            b["other"] += h
        if r["project"] in acct:
            b["blank_rows"] += int(r.get("blank_note_rows_ge4h") or 0)
            for s in (r.get("statuses") or "").split(","):
                if s:
                    b["statuses"].add(s)
    return people


def evaluate(cfg: dict, wk: dict, ciq_rows: list[dict], ciq_users: list[dict],
             jira: dict | None, prev_flags: dict | None = None) -> dict:
    th = cfg["thresholds"]
    roster = {p["email"]: p for p in cfg["roster"]}
    has_user = {(u.get("email") or "").lower() for u in ciq_users}
    hours = hours_table(ciq_rows, cfg, wk)
    W = str(wk["week"])
    trend = [str(t) for t in wk["trend"]]
    prev_flags = prev_flags or {}

    if jira is not None:
        resolved = by_assignee(jira["resolved"])
        moved = by_assignee(jira["moved"])
        open_ = by_assignee(jira["open"])
        stale = by_assignee(jira["stale_in_progress"])
        mw_stale = {r["assignee"] for r in jira["milestone_watch"]
                    if r["assignee"] and (r.get("updated") or "")[:10] < str(wk["week"])}
    else:
        resolved = moved = open_ = stale = {}
        mw_stale = set()

    people_emails = list(roster)
    jira_people = set(resolved) | set(moved) | set(open_) | set(stale)
    for e in list(hours) + sorted(jira_people):
        if e not in people_emails:
            people_emails.append(e)

    people, open_items = [], []
    for e in people_emails:
        h = hours.get(e, {"name": roster.get(e, {}).get("name", e), "by_week": {}})
        name = roster[e]["name"] if e in roster else h["name"]
        bw = h["by_week"]
        wkb = bw.get(W, {"primary": 0.0, "context": 0.0, "other": 0.0, "blank_rows": 0, "statuses": set()})
        t = [round(bw.get(x, {}).get("primary", 0.0), 2) for x in trend]
        week_h = round(wkb["primary"], 2)
        all_h = round(wkb["primary"] + wkb["context"] + wkb["other"], 2)
        avg = round(sum(t) / len(t), 2) if t else 0.0
        change = None if avg == 0 else round((week_h - avg) / avg * 100, 1)
        n_res = len(resolved.get(e, []))
        n_mov = len(set(moved.get(e, [])) | set(resolved.get(e, [])))   # any status change in WEEK, resolutions included
        n_open, n_stale = len(open_.get(e, [])), len(stale.get(e, []))
        touched = len(set(resolved.get(e, [])) | set(moved.get(e, [])))
        statuses = sorted(wkb["statuses"])
        on_roster = e in roster
        is_owner = e == cfg["owner_email"]

        flags = []
        f0 = all_h == 0
        if f0:
            flags.append(("F0", "No time entered yet for the week on any project — check the timesheet?"
                          if e in has_user or e in hours else
                          "No CIQ user found for this email — is the roster email right, or is time not set up?"))
        if jira is not None and not f0:
            if week_h >= th["f1_min_hours"] and n_res == 0 and n_mov <= th["f1_max_moved"]:
                flags.append(("F1", f"{week_h:g} h on the project, 0 tickets resolved and {_n(n_mov, 'status change')} — "
                                    "what did the time go to? (Workshops, calls, data work and reviews often don't move Jira.)"))
            if touched >= th["f2_min_tickets"] and week_h < th["f2_max_hours"]:
                flags.append(("F2", f"{_n(touched, 'ticket')} resolved or moved with {week_h:g} h on the project — "
                                    f"is the time logged elsewhere ({all_h:g} h across all projects)?"))
        if not f0 and week_h > 0:
            diff = week_h - avg
            if abs(diff) > th["f3_min_hours"] and (avg == 0 or abs(diff) / avg * 100 > th["f3_pct"]):
                flags.append(("F3", f"{week_h:g} h vs a 3-week average of {avg:.1f} h — what changed?"))
        if jira is not None and (n_stale >= th["f4_min_stale"] or e in mw_stale):
            what = f"{_n(n_stale, 'in-progress ticket')} not updated since before the week" if n_stale >= th["f4_min_stale"] else ""
            if e in mw_stale:
                what = (what + "; " if what else "") + "a milestone-watch ticket has gone stale"
            flags.append(("F4", f"{what} — are these still active, blocked, or ready to move?"))
        if jira is not None and not f0:
            if week_h > 0 and touched == 0 and n_open == 0:
                flags.append(("F5", f"{week_h:g} h on the project with no Jira presence — which tickets does the work map to? "
                                    f"({all_h:g} h across all projects)"))
            elif n_open > 0 and week_h == 0:
                flags.append(("F5", f"{_n(n_open, 'open ticket')} assigned but no project time this week — "
                                    f"is the work paused or allocated elsewhere? ({all_h:g} h across all projects)"))
        if wkb["blank_rows"] > 0:
            flags.append(("F6", f"{_n(wkb['blank_rows'], 'CIQ weekly row')} of {th['f6_blank_note_hours']}+ h with blank notes — "
                                "can notes say what the time covered?"))

        prev = {x.strip() for x in str(prev_flags.get(e, "")).replace(";", ",").split(",") if x.strip().startswith("F")}
        codes = [c for c, _ in flags]
        repeat = sorted(set(codes) & {p.split()[0] for p in prev})

        if is_owner:
            flags = []   # Mark's own row: shown for completeness, never flagged
            codes, repeat = [], []

        if not on_roster and (week_h > 0 or any(bw.get(x, {}).get("primary", 0) for x in trend)):
            open_items.append(f"Add to roster in configs/{cfg['account']}.yaml: {name}, {e} (has project hours in CIQ)")
        if not on_roster and jira_people and e in jira_people and week_h == 0:
            open_items.append(f"Jira assignee not on the roster: {name}, {e}")
        if on_roster and e not in has_user and e not in hours:
            open_items.append(f"No CIQ user for roster email {e} ({name})")

        people.append({
            "email": e, "name": name, "on_roster": on_roster, "is_owner": is_owner,
            "trend_hours": t, "week_hours": week_h, "avg_hours": avg, "change_pct": change,
            "context_hours": round(wkb["context"], 2), "all_hours": all_h, "statuses": statuses,
            "jira": None if jira is None else {"resolved": n_res, "moved": n_mov, "open": n_open, "stale": n_stale},
            "flags": [{"code": c, "text": tx} for c, tx in flags],
            "repeat": repeat,
            "recommendation": recommend(codes, repeat),
        })

    people.sort(key=lambda p: (not p["flags"], _rank(p), p["name"].lower()))
    flagged = [p for p in people if p["flags"]]
    walk, fyi = flagged[:cfg["max_walk_flags"]], flagged[cfg["max_walk_flags"]:]

    account_items = []
    if jira is not None:
        un = [r["key"] for r in jira["unassigned_in_progress"]]
        if un:
            account_items.append(("F6", f"In-progress tickets with no assignee: {', '.join(un)}"))
        mw = [r for r in jira["milestone_watch"] if not r["assignee"]]
        if mw:
            account_items.append(("F4", "Unassigned milestone-watch tickets: " + ", ".join(r["key"] for r in mw)))

    tot_week = round(sum(p["week_hours"] for p in people), 2)
    tot_trend = [round(sum(p["trend_hours"][i] for p in people), 2) for i in range(len(trend))]
    return {
        "account": cfg["account"], "label": cfg["label"], "week": W, "trend_weeks": trend,
        "jira_enabled": jira is not None,
        "totals": {"week_hours": tot_week, "trend_hours": tot_trend,
                   "avg_hours": round(sum(tot_trend) / len(tot_trend), 2) if tot_trend else 0.0,
                   "resolved": len(jira["resolved"]) if jira else None,
                   "moved": len({r["key"] for r in jira["moved"]}) if jira else None},
        "people": people, "walk": [p["email"] for p in walk], "fyi": [p["email"] for p in fyi],
        "account_items": [{"code": c, "text": t} for c, t in account_items],
        "open_items": sorted(set(open_items)),
        "jira_pages": jira.get("_pages") if jira else None,
    }


def _rank(p: dict) -> int:
    codes = {f["code"] for f in p["flags"]}
    if p["repeat"]:
        codes.add("REPEAT")
    return min((ORDER.index(c) for c in codes if c in ORDER), default=len(ORDER))


def recommend(codes: list[str], repeat: list[str]) -> str:
    if not codes:
        return ""
    if repeat and set(repeat) & {"F1", "F2", "F4", "F5"}:
        return "Raise in 1:1"
    if {"F1", "F2", "F4"} & set(codes):
        return "Raise in 1:1"
    return "Note only"
