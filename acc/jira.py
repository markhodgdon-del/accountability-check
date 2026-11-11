"""Normalize saved Jira search results (Atlassian_MCP searchJiraIssuesUsingJql, view: full).

The session saves every page of each query, exactly as returned, to
RUN/jira/<query>_<n>.json, where <query> is one of QUERIES. This module turns them into
{query: [{"key", "assignee", "updated", "duedate", "labels"}]} with assignee = lowercase
email or None. Compact-view results carry no emailAddress, so they are rejected.
"""
from __future__ import annotations

import glob
import json
import os
import re

QUERIES = ("resolved", "moved", "open", "stale_in_progress", "unassigned_in_progress", "milestone_watch")


class JiraDataError(ValueError):
    pass


def _issues(doc):
    if isinstance(doc, dict) and "data" in doc:
        doc = doc["data"]
    if isinstance(doc, dict):
        return doc.get("issues", []), doc.get("isLast", True)
    raise JiraDataError("unexpected Jira result shape")


def normalize(jira_dir: str) -> dict:
    out = {q: [] for q in QUERIES}
    pages_read = {q: 0 for q in QUERIES}
    for path in sorted(glob.glob(os.path.join(jira_dir, "*.json"))):
        m = re.match(r"(.+?)_(\d+)\.json$", os.path.basename(path))
        if not m or m.group(1) not in QUERIES:
            raise JiraDataError(f"unexpected file {os.path.basename(path)}; name pages <query>_<n>.json")
        q = m.group(1)
        issues, is_last = _issues(json.load(open(path)))
        pages_read[q] += 1
        for it in issues:
            f = it.get("fields", {})
            a = f.get("assignee")
            if a is not None and "emailAddress" not in a:
                raise JiraDataError(f"{it.get('key')}: assignee has no emailAddress; rerun with view: full")
            out[q].append({
                "key": it["key"],
                "assignee": (a or {}).get("emailAddress", "").lower() or None,
                "updated": f.get("updated"),
                "duedate": f.get("duedate"),
                "labels": f.get("labels") or [],
            })
    for q in QUERIES:   # de-duplicate keys across pages
        seen, keep = set(), []
        for r in out[q]:
            if r["key"] not in seen:
                seen.add(r["key"])
                keep.append(r)
        out[q] = keep
    out["_pages"] = pages_read
    return out


def by_assignee(rows: list[dict]) -> dict:
    d: dict = {}
    for r in rows:
        if r["assignee"]:
            d.setdefault(r["assignee"], []).append(r["key"])
    return d
