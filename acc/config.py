"""Load and validate an account config (configs/<account>.yaml)."""
from __future__ import annotations

import re

import yaml

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
EMAIL = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")
MODES = {"report_only", "live"}

DEFAULT_THRESHOLDS = {
    "f1_min_hours": 15,        # F1: at least this many project hours ...
    "f1_max_moved": 1,         # ... with 0 resolved and at most this many status changes
    "f2_min_tickets": 3,       # F2: at least this many tickets resolved or moved ...
    "f2_max_hours": 5,         # ... with fewer project hours than this
    "f3_pct": 50,              # F3: differs from the 3-week average by more than this % ...
    "f3_min_hours": 8,         # ... and by more than this many hours
    "f4_min_stale": 2,         # F4: at least this many in-progress tickets not updated since before WEEK
    "f6_blank_note_hours": 4,  # F6: CIQ weekly rows of at least this many hours with blank notes
}


class ConfigError(ValueError):
    pass


def load(path: str) -> dict:
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    validate(cfg)
    th = dict(DEFAULT_THRESHOLDS)
    th.update(cfg.get("thresholds") or {})
    cfg["thresholds"] = th
    cfg.setdefault("max_walk_flags", 10)
    cfg["ciq"].setdefault("context", [])
    for p in cfg["roster"]:
        p["email"] = p["email"].strip().lower()
    cfg["owner_email"] = cfg["owner_email"].strip().lower()
    return cfg


def validate(cfg: dict) -> None:
    def need(cond, msg):
        if not cond:
            raise ConfigError(f"{cfg.get('account', '?')}: {msg}")

    for k in ("account", "label", "project", "schedule", "mode", "owner_email", "ciq", "roster", "output"):
        need(k in cfg, f"missing '{k}'")
    need(cfg["mode"] in MODES, f"mode must be one of {sorted(MODES)}")
    need(UUID.match(str(cfg["ciq"].get("primary", {}).get("id", ""))), "ciq.primary.id must be a CIQ project UUID")
    for c in cfg["ciq"].get("context") or []:
        need(UUID.match(str(c.get("id", ""))), f"bad ciq.context id {c!r}")
    jira = cfg.get("jira")
    need(jira is None or (isinstance(jira, dict) and jira.get("project")), "jira must be null or have 'project'")
    need(isinstance(cfg["roster"], list) and cfg["roster"], "roster must be a non-empty list")
    seen = set()
    for p in cfg["roster"]:
        e = str(p.get("email", "")).strip().lower()
        need(EMAIL.match(e), f"bad roster email {p!r}")
        need(e not in seen, f"duplicate roster email {e}")
        seen.add(e)
        need(p.get("name"), f"roster entry without name {p!r}")
    need(str(cfg["owner_email"]).lower() in seen, "owner_email must be on the roster")
    out = cfg["output"]
    for k in ("doc_folder", "results_sheet", "results_tab"):
        need(out.get(k), f"output.{k} missing")


def project_ids(cfg: dict) -> list[str]:
    return [cfg["ciq"]["primary"]["id"]] + [c["id"] for c in cfg["ciq"]["context"]]
