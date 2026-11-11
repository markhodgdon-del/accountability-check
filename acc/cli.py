"""Command line for the scheduled session. Pure Python, no network.

  python3 -m acc.cli dates  --config configs/mo.yaml --run-date 2026-11-18
  python3 -m acc.cli sql hours|users|week_detail --config ... --run-date ... [--emails a@x,b@y]
  python3 -m acc.cli prep   --config ... --run-date ... --ciq RUN/ciq.json --users RUN/users.json
                            [--jira-dir RUN/jira] [--prev RUN/prev.json] --out RUN
  python3 -m acc.cli report --config ... --res RUN/res.json --meta RUN/meta.json
                            [--context RUN/context.json] --out RUN
  python3 -m acc.cli check-configs
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import date

from . import __version__
from .config import ConfigError, load, project_ids
from .dates import weeks
from .flags import evaluate
from .jira import normalize
from .report import doc_title, render_doc, results_rows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _commit() -> str:
    try:
        return subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "uncommitted"


def _q(items) -> str:
    return ", ".join("'" + str(x).replace("'", "''") + "'" for x in items)


def render_sql(name: str, cfg: dict, wk: dict, emails: list[str] | None = None) -> str:
    sql = open(os.path.join(ROOT, "sql", f"{name}.sql")).read()
    sql = "\n".join(l for l in sql.splitlines() if not l.lstrip().startswith("--"))
    roster = [p["email"] for p in cfg["roster"]]
    return (sql.replace(":projects", _q(project_ids(cfg)))
               .replace(":roster", _q(roster))
               .replace(":emails", _q(emails or ["none@none"]))
               .replace(":from", str(wk["from"]))
               .replace(":to", str(wk["week"]))
               .replace(":wk", str(wk["week"])))


REPO = "markhodgdon-del/accountability-check"


def task_prompt(cfg: dict) -> str:
    acc, label = cfg["account"], cfg["label"]
    return f"""Weekly team accountability check — {label} (ACCOUNT={acc}). Repo {REPO}, config configs/{acc}.yaml.
1. Get the code: add_repo {{owner: "markhodgdon-del", repo: "accountability-check", access: "read"}}, then
   git clone --depth 1 --branch main https://github.com/{REPO} /home/user/accountability-check
   If either fails, retry once. Still failing: send ONE push notification "{label} accountability check: repo unreachable — no run this week" and stop. Never run from memory or an old copy.
2. Read /home/user/accountability-check/ROUTINE.md and follow it exactly with ACCOUNT={acc}. The run mode comes only from configs/{acc}.yaml.
3. You are unattended until ROUTINE step 11: never ask questions or use AskUserQuestion before it.
4. Read-only on CIQ (ciq_query only; never ciq_change or ciq_safe_change), Jira, Slack, Fireflies, Calendar and Gmail. The only writes are the ones in ROUTINE step 9 (and, if Mark says yes to the walk, WALK.md step 4). Never commit to the repo.
5. Last step (ROUTINE step 11): ask Mark whether to walk the accountability check now, yes or no."""


def install_prompt(cfg: dict) -> str:
    acc, label = cfg["account"], cfg["label"]
    cron = cfg["schedule"]
    walk_doc = f"""# Accountability walk — {label}

When Mark says "Walk the accountability check" in this project: add_repo {{owner: "markhodgdon-del", repo: "accountability-check", access: "read"}}, clone it, read WALK.md and configs/{acc}.yaml, and follow WALK.md. The weekly prep runs as the scheduled task "{label} - Weekly Accountability Check (CIQ)"."""
    return f"""Install the weekly accountability check for {label} in this project.

1. Create one scheduled task with create_trigger:
   - name: "{label} - Weekly Accountability Check (CIQ)"
   - cron_expression: "{cron}"
   - initiation: human_request
   - notifications: {{"push": true}}
   - prompt (exactly the text between the lines):
-----
{task_prompt(cfg)}
-----
2. Save this project doc with the Projects tool (project_write, path "claude/accountability-walk.md"), exactly the text between the lines:
-----
{walk_doc}
-----
3. Run the new task once now as the install test (fire_trigger with its trigger id). The repo config is in report_only mode, so it writes only a "(TEST)" doc and no Results rows.
4. Tell me: the trigger id, its schedule in ET, its approval setting, and that the test run started."""


def changes(res: dict, prev: dict) -> list[str]:
    """Cleared / new / repeat flags vs last week's Results rows ({email: "F1, F3"})."""
    if not prev:
        return []
    now = {p["email"]: {f["code"] for f in p["flags"]} for p in res["people"]}
    names = {p["email"]: p["name"] for p in res["people"]}
    out = []
    for e in sorted(set(now) | set(prev)):
        before = {x.strip().split()[0] for x in str(prev.get(e, "")).replace(";", ",").split(",")
                  if x.strip().startswith("F")}
        after = now.get(e, set())
        n = names.get(e, e)
        if before - after:
            out.append(f"{n}: cleared {', '.join(sorted(before - after))}")
        if after - before:
            out.append(f"{n}: new {', '.join(sorted(after - before))}")
        if before & after:
            out.append(f"{n}: repeat {', '.join(sorted(before & after))}")
    return out or ["No flag changes from last week."]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="acc")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("dates", "sql", "prep", "report"):
        s = sub.add_parser(n)
        s.add_argument("--config", required=True)
        if n != "report":
            s.add_argument("--run-date", required=True, type=date.fromisoformat)
            s.add_argument("--week", type=date.fromisoformat, help="override WEEK (a Sunday)")
        if n == "sql":
            s.add_argument("name", choices=["hours", "users", "week_detail"])
            s.add_argument("--emails", default="")
        if n == "prep":
            s.add_argument("--ciq", required=True)
            s.add_argument("--users", required=True)
            s.add_argument("--jira-dir")
            s.add_argument("--prev")
            s.add_argument("--no-jira", action="store_true", help="Jira unreachable: run hours-only flags")
            s.add_argument("--out", required=True)
        if n == "report":
            s.add_argument("--res", required=True)
            s.add_argument("--meta", required=True)
            s.add_argument("--context")
            s.add_argument("--out", required=True)
    sub.add_parser("check-configs")
    ip = sub.add_parser("install-prompt")
    ip.add_argument("--config", required=True)
    a = ap.parse_args(argv)

    if a.cmd == "check-configs":
        bad = 0
        for path in sorted(glob.glob(os.path.join(ROOT, "configs", "*.yaml"))):
            try:
                c = load(path)
                print(f"ok   {os.path.basename(path)}  {c['label']}  mode={c['mode']}  "
                      f"jira={(c.get('jira') or {}).get('project', 'none')}  roster={len(c['roster'])}")
            except (ConfigError, KeyError, TypeError) as e:
                bad += 1
                print(f"FAIL {os.path.basename(path)}: {e}")
        return 1 if bad else 0

    cfg = load(a.config)

    if a.cmd == "install-prompt":
        print(install_prompt(cfg))
        return 0

    if a.cmd in ("dates", "sql", "prep"):
        wk = weeks(a.run_date, cfg.get("trend_weeks", 3), a.week)

    if a.cmd == "dates":
        print(json.dumps({k: (str(v) if not isinstance(v, list) else [str(x) for x in v]) for k, v in wk.items()}
                         | {"title": doc_title(cfg, str(wk["week"]))}, indent=1))
        return 0

    if a.cmd == "sql":
        print(render_sql(a.name, cfg, wk, [e.strip().lower() for e in a.emails.split(",") if e.strip()]))
        return 0

    if a.cmd == "prep":
        ciq = json.load(open(a.ciq))
        if ciq.get("hasMore"):
            print("CIQ result has hasMore=true: incomplete pull", file=sys.stderr)
            return 2
        users = json.load(open(a.users)).get("rows", [])
        jira = None
        if cfg.get("jira") and not a.no_jira:
            if not a.jira_dir or not os.path.isdir(a.jira_dir):
                print("config has jira but no --jira-dir given", file=sys.stderr)
                return 2
            jira = normalize(a.jira_dir)
        prev = json.load(open(a.prev)) if a.prev and os.path.exists(a.prev) else {}
        res = evaluate(cfg, wk, ciq["rows"], users, jira, prev)
        res["week_end"] = str(wk["week_end"])
        res["jira_skipped"] = bool(cfg.get("jira") and a.no_jira)
        res["changes"] = changes(res, prev)
        res["uses_harvest_copy"] = wk["uses_harvest_copy"]
        res["title"] = doc_title(cfg, res["week"])
        res["engine"] = {"version": __version__, "commit": _commit()}
        os.makedirs(a.out, exist_ok=True)
        json.dump(res, open(os.path.join(a.out, "res.json"), "w"), indent=1, default=list)
        flagged = [p for p in res["people"] if p["flags"]]
        print(f"{cfg['label']} week {res['week']}: {len(res['people'])} people, {len(flagged)} flagged "
              f"({len(res['walk'])} walk, {len(res['fyi'])} FYI); open items {len(res['open_items'])}")
        for p in flagged:
            print(f"  {p['name']}: {', '.join(f['code'] for f in p['flags'])} -> {p['recommendation']}")
        return 0

    if a.cmd == "report":
        res = json.load(open(a.res))
        meta = json.load(open(a.meta))
        meta.setdefault("week_end", res.get("week_end", ""))
        meta.setdefault("version", res["engine"]["version"])
        meta.setdefault("commit", res["engine"]["commit"])
        ctx = json.load(open(a.context)) if a.context and os.path.exists(a.context) else {}
        doc = render_doc(res, cfg, meta, ctx)
        rows = results_rows(res, cfg, meta.get("run_label", ""), ctx)
        open(os.path.join(a.out, "doc.md"), "w").write(doc)
        json.dump({"title": res["title"], "rows": rows}, open(os.path.join(a.out, "results_rows.json"), "w"), indent=1)
        print(f"doc.md ({len(doc)} chars), {len(rows)} Results rows")
        return 0


if __name__ == "__main__":
    sys.exit(main())
