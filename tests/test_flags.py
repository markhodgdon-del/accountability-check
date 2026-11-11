import copy
import glob
import json
import os
from datetime import date

import pytest

from acc.cli import ROOT, render_sql
from acc.config import ConfigError, load, validate
from acc.dates import last_full_week, weeks
from acc.flags import evaluate
from acc.jira import JiraDataError, normalize
from acc.report import RESULTS_HEADER, render_doc, results_rows

FX = os.path.join(ROOT, "tests", "fixtures")
MO = os.path.join(ROOT, "configs", "mo.yaml")
CBA = os.path.join(ROOT, "configs", "cba.yaml")


def mo_real():
    cfg = load(MO)
    wk = weeks(date(2026, 11, 11))
    rows = json.load(open(os.path.join(FX, "ciq_mo_2026-11-01.json")))["rows"]
    users = json.load(open(os.path.join(FX, "users_mo.json")))["rows"]
    jira = normalize(os.path.join(FX, "jira_mo_2026-11-01"))
    return cfg, wk, rows, users, jira


def codes(res, email):
    return [f["code"] for f in next(p for p in res["people"] if p["email"] == email)["flags"]]


# ---- dates -------------------------------------------------------------------------------
@pytest.mark.parametrize("run,expect", [
    ("2026-11-11", "2026-11-01"),   # Wednesday
    ("2026-11-15", "2026-11-08"),   # Sunday: the week that just ended
    ("2026-11-14", "2026-11-01"),   # Saturday: current week not finished
    ("2026-11-18", "2026-11-08"),
])
def test_last_full_week(run, expect):
    assert str(last_full_week(date.fromisoformat(run))) == expect


def test_trend_weeks_and_harvest_copy_cutover():
    w = weeks(date(2026, 11, 11))
    assert [str(x) for x in w["trend"]] == ["2026-10-11", "2026-10-18", "2026-10-25"]
    assert w["uses_harvest_copy"] is True
    assert weeks(date(2026, 12, 2))["uses_harvest_copy"] is False   # week of 11/22: trend 11/1-11/15


# ---- configs ------------------------------------------------------------------------------
def test_all_configs_load():
    paths = sorted(glob.glob(os.path.join(ROOT, "configs", "*.yaml")))
    assert {os.path.basename(p) for p in paths} == {"mo.yaml", "hoonigan.yaml", "grimco.yaml", "cba.yaml"}
    for p in paths:
        c = load(p)
        assert c["schedule"].startswith("CRON_TZ=America/New_York ")
        assert c["schedule"].split()[-1] == "3"          # Wednesdays
        assert 12 <= int(c["schedule"].split()[2]) <= 17   # afternoon
        assert c["owner_email"] == "mark.hodgdon@answerrocket.com"


def test_config_rejects_bad_values():
    good = load(MO)
    for mutate in (lambda c: c.update(mode="write"),
                   lambda c: c["ciq"]["primary"].update(id="not-a-uuid"),
                   lambda c: c["roster"].append({"name": "X", "email": "alex.holloway@answerrocket.com"}),
                   lambda c: c.update(owner_email="someone@else.com")):
        c = copy.deepcopy(good)
        mutate(c)
        with pytest.raises(ConfigError):
            validate(c)


# ---- SQL ----------------------------------------------------------------------------------
def test_sql_is_read_only_and_filled():
    cfg = load(MO)
    wk = weeks(date(2026, 11, 11))
    for name in ("hours", "users", "week_detail"):
        sql = render_sql(name, cfg, wk, ["a@b.com"]).lower()
        assert ":projects" not in sql and ":roster" not in sql and ":from" not in sql
        for bad in ("insert ", "update ", "delete ", "drop ", "rate"):
            assert bad not in sql, (name, bad)
    sql = render_sql("hours", cfg, wk)
    assert "date '2026-10-11'" in sql and "date '2026-11-01'" in sql
    assert "'f6039cfd-f3d2-4158-81f4-4c252230d625', 'e112f025-db2a-447a-b026-e18429c698d6'" in sql


# ---- Jira normalize -----------------------------------------------------------------------
def test_jira_compact_view_rejected(tmp_path):
    (tmp_path / "resolved_1.json").write_text(json.dumps(
        {"data": {"issues": [{"key": "X-1", "fields": {"assignee": {"displayName": "A"}}}]}}))
    with pytest.raises(JiraDataError):
        normalize(str(tmp_path))


def test_jira_pages_dedupe(tmp_path):
    page = {"data": {"issues": [{"key": "X-1", "fields": {"assignee": {"emailAddress": "A@B.com"}}}]}}
    (tmp_path / "open_1.json").write_text(json.dumps(page))
    (tmp_path / "open_2.json").write_text(json.dumps(page))
    j = normalize(str(tmp_path))
    assert j["open"] == [{"key": "X-1", "assignee": "a@b.com", "updated": None, "duedate": None, "labels": []}]
    assert j["_pages"]["open"] == 2


# ---- real M&O regression (week of 2026-11-01, pulled 2026-11-11) -----------------------------
def test_mo_real_week_regression():
    cfg, wk, rows, users, jira = mo_real()
    res = evaluate(cfg, wk, rows, users, jira)
    flagged = {p["email"]: [f["code"] for f in p["flags"]] for p in res["people"] if p["flags"]}
    assert flagged == {
        "clayton.summitt@answerrocket.com": ["F3", "F6"],     # 37 h vs avg 11.3
        "erik.blas@answerrocket.com": ["F5"],                 # open MEADOWSOH-999, 0 M&O h, 40 h elsewhere
        "alex.holloway@answerrocket.com": ["F6"],             # one blank-note row
    }
    assert res["totals"]["week_hours"] == 86.0
    assert res["totals"]["resolved"] == 20 and res["totals"]["moved"] == 38
    erik = next(p for p in res["people"] if p["email"] == "erik.blas@answerrocket.com")
    assert erik["all_hours"] == 40.0 and "40 h across all projects" in erik["flags"][0]["text"]
    assert res["account_items"] == [{"code": "F6", "text": "In-progress tickets with no assignee: MEADOWSOH-55"}]
    assert codes(res, "mark.hodgdon@answerrocket.com") == []
    assert res["open_items"] == []


def test_mo_results_rows_match_sheet_header():
    cfg, wk, rows, users, jira = mo_real()
    res = evaluate(cfg, wk, rows, users, jira)
    out = results_rows(res, cfg, "run")
    assert all(len(r) == len(RESULTS_HEADER) == 20 for r in out)
    alex = next(r for r in out if r[3] == "alex.holloway@answerrocket.com")
    assert alex[:14] == ["2026-11-01", "M&O", "Alexander Holloway", "alex.holloway@answerrocket.com",
                         "24.0", "39.0", "40.0", "40.0", "34.3", "16.5%", "0.0", "6", "11", "19"]
    assert alex[16] == "" and alex[17] == ""   # Mark's decision and reason are left for the walk
    mark = next(r for r in out if r[3] == "mark.hodgdon@answerrocket.com")
    assert mark[14] == "Mark — not flagged"


def test_doc_renders_and_title_marks_test_mode():
    cfg, wk, rows, users, jira = mo_real()
    res = evaluate(cfg, wk, rows, users, jira)
    res["title"] = "t"
    doc = render_doc(res, cfg, {"week_end": "2026-11-07"})
    assert doc.startswith("# (TEST) M&O Team Accountability Check — week of 2026-11-01 (private)")
    assert "Walk the accountability check" in doc
    for word in ("rate", "$"):
        assert word not in doc


# ---- synthetic rules -----------------------------------------------------------------------
P = "f6039cfd-f3d2-4158-81f4-4c252230d625"
CTX = "e112f025-db2a-447a-b026-e18429c698d6"


def row(email, week, hours, project=P, blank=0, status="submitted"):
    return {"email": email, "name": email.split("@")[0], "week": week, "project": project,
            "hours": str(hours), "blank_note_rows_ge4h": blank, "statuses": status}


def jira_of(**kw):
    j = {q: [] for q in ("resolved", "moved", "open", "stale_in_progress", "unassigned_in_progress", "milestone_watch")}
    for q, items in kw.items():
        j[q] = [{"key": k, "assignee": a, "updated": u, "duedate": None, "labels": []} for k, a, u in items]
    return j


A = "alex.holloway@answerrocket.com"
TREND = ["2026-10-11", "2026-10-18", "2026-10-25"]
W = "2026-11-01"


def run(rows, jira=None, cfg=None, prev=None):
    cfg = cfg or load(MO)
    users = [{"email": p["email"]} for p in cfg["roster"]]
    return evaluate(cfg, weeks(date(2026, 11, 11)), rows, users, jira if jira is not None else jira_of(), prev)


def steady(email=A, h=20):
    return [row(email, t, h, status="harvest") for t in TREND]


def test_f0_no_time_anywhere_blocks_other_hour_flags():
    res = run(steady(), jira_of(open=[("M-1", A, None)]))
    assert codes(res, A) == ["F0"]


def test_f0_wording_when_no_ciq_user():
    cfg = load(MO)
    res = evaluate(cfg, weeks(date(2026, 11, 11)), [], [], jira_of())
    alex = next(p for p in res["people"] if p["email"] == A)
    assert "No CIQ user" in alex["flags"][0]["text"]
    assert any(A in x for x in res["open_items"])


def test_f1_hours_little_jira():
    res = run(steady() + [row(A, W, 20)], jira_of(moved=[("M-1", A, None)], open=[("M-2", A, None)]))
    assert codes(res, A) == ["F1"]
    res = run(steady() + [row(A, W, 20)], jira_of(resolved=[("M-1", A, None)], open=[("M-2", A, None)]))
    assert codes(res, A) == []


def test_f2_jira_movement_few_hours():
    j = jira_of(resolved=[("M-1", A, None), ("M-2", A, None)], moved=[("M-3", A, None)])
    res = run([row(A, t, 3, status="harvest") for t in TREND] + [row(A, W, 3), row(A, W, 37, project="other")], j)
    assert codes(res, A) == ["F2"]


def test_f3_swing_thresholds():
    assert "F3" in codes(run(steady(h=20) + [row(A, W, 31)], jira_of(resolved=[("M", A, None)])), A)   # +11 h, 55%
    assert "F3" not in codes(run(steady(h=20) + [row(A, W, 28)], jira_of(resolved=[("M", A, None)])), A)  # +8 h
    assert "F3" not in codes(run(steady(h=40) + [row(A, W, 30)], jira_of(resolved=[("M", A, None)])), A)  # -25%
    assert "F3" in codes(run([row(A, W, 12)], jira_of(resolved=[("M", A, None)])), A)                      # new: avg 0


def test_f4_stale_and_milestone_watch():
    j = jira_of(resolved=[("M-0", A, None)], stale_in_progress=[("M-1", A, "2026-10-20"), ("M-2", A, "2026-10-21")])
    assert "F4" in codes(run(steady() + [row(A, W, 20)], j), A)
    j = jira_of(resolved=[("M-0", A, None)], milestone_watch=[("G-1", A, "2026-10-28T10:00:00")])
    assert "F4" in codes(run(steady() + [row(A, W, 20)], j), A)
    j = jira_of(resolved=[("M-0", A, None)], milestone_watch=[("G-1", A, "2026-11-03T10:00:00")])
    assert "F4" not in codes(run(steady() + [row(A, W, 20)], j), A)
    j = jira_of(milestone_watch=[("G-2", None, "2026-11-03")])
    assert any(i["code"] == "F4" and "G-2" in i["text"] for i in run(steady() + [row(A, W, 20)], j)["account_items"])


def test_f5_both_directions_and_total_shown():
    res = run(steady(h=4) + [row(A, W, 4)], jira_of())
    assert codes(res, A) == ["F5"]
    res = run(steady(h=0) + [row(A, W, 40, project="other")], jira_of(open=[("M-1", A, None)]))
    p = next(x for x in res["people"] if x["email"] == A)
    assert [f["code"] for f in p["flags"]] == ["F5"] and "40 h across all projects" in p["flags"][0]["text"]


def test_f6_blank_notes_only_on_account_projects():
    res = run(steady() + [row(A, W, 20, blank=2), row(A, W, 20, project="other", blank=3)],
              jira_of(resolved=[("M", A, None)]))
    p = next(x for x in res["people"] if x["email"] == A)
    assert [f["code"] for f in p["flags"]] == ["F6"] and p["flags"][0]["text"].startswith("2 CIQ weekly rows")


def test_context_project_hours_kept_separate():
    res = run(steady() + [row(A, W, 20), row(A, W, 6, project=CTX)], jira_of(resolved=[("M", A, None)]))
    p = next(x for x in res["people"] if x["email"] == A)
    assert p["week_hours"] == 20 and p["context_hours"] == 6 and p["all_hours"] == 26


def test_owner_never_flagged():
    M = "mark.hodgdon@answerrocket.com"
    res = run([row(M, W, 30, blank=3)], jira_of())
    assert codes(res, M) == []


def test_not_on_roster_goes_to_open_items():
    res = run([row("new.person@answerrocket.com", W, 12)], jira_of(resolved=[("M", "new.person@answerrocket.com", None)]))
    assert any("new.person@answerrocket.com" in x and "Add to roster" in x for x in res["open_items"])


def test_repeat_flag_raises_recommendation_and_walk_rank():
    rows = steady(h=4) + [row(A, W, 4)]
    assert next(p for p in run(rows)["people"] if p["email"] == A)["recommendation"] == "Note only"
    res = run(rows, prev={A: "F5"})
    p = next(x for x in res["people"] if x["email"] == A)
    assert p["repeat"] == ["F5"] and p["recommendation"] == "Raise in 1:1" and res["walk"][0] == A


def test_walk_cap_moves_rest_to_fyi():
    cfg = load(MO)
    cfg["max_walk_flags"] = 2
    res = run([row(p["email"], W, 4) for p in cfg["roster"]], jira_of(), cfg=cfg)
    assert len(res["walk"]) == 2 and len(res["fyi"]) == 4   # 6 non-owner roster people, all F3/F5


def test_hours_only_when_jira_is_none():
    cfg = load(CBA)
    J = "jack.haidet@answerrocket.com"
    pid = cfg["ciq"]["primary"]["id"]
    users = [{"email": p["email"]} for p in cfg["roster"]]
    res = evaluate(cfg, weeks(date(2026, 11, 25)),
                   [row(J, "2026-11-15", 30, project=pid, blank=1)], users, None)
    assert res["jira_enabled"] is False
    assert codes(res, J) == ["F3", "F6"]
    kin = next(p for p in res["people"] if p["email"] == "kin-yip.chien@answerrocket.com")
    assert [f["code"] for f in kin["flags"]] == ["F0"] and kin["jira"] is None
    rows = results_rows(res, cfg, "r")
    assert next(r for r in rows if r[3] == J)[11:14] == ["n/a", "n/a", "n/a"]


def test_changes_and_no_jira(tmp_path):
    import subprocess, sys
    prev = tmp_path / "prev.json"
    prev.write_text(json.dumps({A: "F6", "kevin.mclanahan@answerrocket.com": "F5"}))
    out = tmp_path / "o"
    base = [sys.executable, "-m", "acc.cli", "prep", "--config", MO, "--run-date", "2026-11-11",
            "--ciq", os.path.join(FX, "ciq_mo_2026-11-01.json"), "--users", os.path.join(FX, "users_mo.json")]
    r = subprocess.run(base + ["--jira-dir", os.path.join(FX, "jira_mo_2026-11-01"), "--prev", str(prev),
                               "--out", str(out)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    res = json.load(open(out / "res.json"))
    assert "Alexander Holloway: repeat F6" in res["changes"]
    assert "Kevin McLanahan: cleared F5" in res["changes"]
    assert "Erik Blas: new F5" in res["changes"]
    r = subprocess.run(base + ["--no-jira", "--out", str(out)], cwd=ROOT, capture_output=True, text=True)
    res = json.load(open(out / "res.json"))
    assert res["jira_skipped"] and not res["jira_enabled"]
    assert {f["code"] for p in res["people"] for f in p["flags"]} <= {"F0", "F3", "F6"}
    r = subprocess.run(base + ["--out", str(out)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 2   # Jira configured but no --jira-dir and no --no-jira


def test_doc_decision_lines_are_unique():
    cfg, wk, rows, users, jira = mo_real()
    doc = render_doc(evaluate(cfg, wk, rows, users, jira), cfg, {})
    lines = [l for l in doc.splitlines() if "Mark's decision (" in l]
    assert len(lines) == 3 and len(set(lines)) == 3


def test_cba_real_week_regression():
    cfg = load(CBA)
    rows = json.load(open(os.path.join(FX, "ciq_cba_2026-11-01.json")))["rows"]
    users = json.load(open(os.path.join(FX, "users_cba.json")))["rows"]
    res = evaluate(cfg, weeks(date(2026, 11, 11)), rows, users, None)
    flagged = {p["email"]: [f["code"] for f in p["flags"]] for p in res["people"] if p["flags"]}
    assert flagged == {
        "jack.haidet@answerrocket.com": ["F3", "F6"],     # first CBA week: 12 h vs avg 0
        "raymond.velez@answerrocket.com": ["F0"],         # no time entered anywhere for 11/1-11/7
    }
    assert res["totals"]["week_hours"] == 12.0
