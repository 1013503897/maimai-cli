"""Render 脉脉 API responses (JSON / pretty / compact list) for the CLI."""
from __future__ import annotations
import json


def as_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _first_list(obj):
    """Find the most likely 'list of items' inside a 脉脉 response (data / list / feeds / …)."""
    if isinstance(obj, list):
        return obj
    if not isinstance(obj, dict):
        return None
    for k in ("data", "list", "feeds", "cards", "contacts", "items", "results", "users"):
        v = obj.get(k)
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            inner = _first_list(v)
            if inner is not None:
                return inner
    return None


def summarize(obj: dict) -> str:
    """One-line status + a peek at any list payload, for `mm get` default text output."""
    code = obj.get("code")
    result = obj.get("result")
    status = f"result={result}" if result is not None else f"code={code}"
    if obj.get("error_msg"):
        status += f" error_msg={obj['error_msg']}"
    lst = _first_list(obj)
    lines = [f"# {status}"]
    if lst is not None:
        lines.append(f"# {len(lst)} item(s)")
        for it in lst[:20]:
            lines.append("- " + _peek(it))
    else:
        keys = ", ".join(list(obj.keys())[:12]) if isinstance(obj, dict) else ""
        lines.append(f"# keys: {keys}")
    return "\n".join(lines)


def _peek(it) -> str:
    if not isinstance(it, dict):
        return str(it)[:120]
    for k in ("name", "realname", "title", "text", "content", "main", "cont", "line1"):
        v = it.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().replace("\n", " ")[:120]
    return json.dumps({k: it[k] for k in list(it)[:4]}, ensure_ascii=False)[:120]


def render(obj, fmt: str) -> str:
    if fmt == "json":
        return as_json(obj)
    return summarize(obj) if isinstance(obj, dict) else as_json(obj)


# ---- job-search rendering ------------------------------------------------------------------
_JOB_COLS = ["name", "salary", "company", "city", "exp", "degree", "scale", "stage", "jobId"]


def render_jobs(jobs: list[dict], fmt: str) -> str:
    if fmt == "json":
        return as_json(jobs)
    if fmt == "csv":
        import csv, io
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=_JOB_COLS, extrasaction="ignore")
        w.writeheader()
        for j in jobs:
            w.writerow({k: ("" if j.get(k) is None else j.get(k)) for k in _JOB_COLS})
        return buf.getvalue()
    if fmt == "md":
        head = "| " + " | ".join(_JOB_COLS) + " |"
        sep = "| " + " | ".join("---" for _ in _JOB_COLS) + " |"
        rows = ["| " + " | ".join(str(j.get(c) or "").replace("|", "\\|") for c in _JOB_COLS) + " |"
                for j in jobs]
        return "\n".join([head, sep, *rows])
    # text
    return "\n".join(
        f"- {j.get('name')} | {j.get('salary')} | {j.get('company')}"
        f"  [{j.get('city') or ''} {j.get('exp') or ''} {j.get('degree') or ''}]".rstrip()
        for j in jobs)
