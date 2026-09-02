"""
MaimaiClient — off-device 脉脉 API client.

A session (access_token + u/uid + a captured device profile) is the only account-bound input;
extract it once from a logged-in device, or mint access_token with `mm login`. The request
assembly is a faithful reproduction of the app's native path:

    url = vb.C7497.getNewApi(module, version, name)         # api.py
        + '?' + df.C2665.m11054(common device/auth params)   # common.build_common_query
        + '&' + business params (GET)                        # common.build_param_string
    body = business params (POST form) / json (POST json)

There is no signature step — that's the whole point (see the module docstrings). The server
accepts the request on the strength of access_token + u over TLS.
"""
from __future__ import annotations
import json as _json
import os
import time
import requests

from . import api, common

# NetworkConstants.NEW_BASE_URI
HOST = api.NEW_BASE_URI


class AuthExpired(RuntimeError):
    """The server rejected the session (not logged in / access_token invalid)."""
    def __init__(self, message="登录状态已失效 (access_token 失效)", resp=None):
        super().__init__(message)
        self.resp = resp


class MaimaiClient:
    def __init__(self, session: dict):
        self.s = session
        self.http = requests.Session()

    @classmethod
    def from_file(cls, path: str) -> "MaimaiClient":
        with open(path, encoding="utf-8") as f:
            return cls(_json.load(f))

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(self.s, f, ensure_ascii=False, indent=2)

    # ---- headers ---------------------------------------------------------------------------
    def _headers(self) -> dict:
        h = {"Accept-Encoding": "gzip"}
        ua = self.s.get("user_agent")
        if ua:
            h["User-Agent"] = ua
        return h

    # ---- url / body assembly ---------------------------------------------------------------
    def build_get_url(self, url_path: str, params: dict | None = None) -> str:
        """url_path + '?'|'&' + common params (+ '&' + business params)."""
        sep = "&" if "?" in url_path else "?"
        url = url_path + sep + common.build_common_query(self.s, url_path)
        if params:
            ps = common.build_param_string(params)
            if ps:
                url += "&" + ps
        return url

    def _http(self, method: str, url: str, *, data=None, headers=None, retries: int = 2):
        last = None
        for attempt in range(retries + 1):
            try:
                r = self.http.request(method, url, data=data, headers=headers, timeout=30)
                r.raise_for_status()
                return r
            except (requests.ConnectionError, requests.Timeout) as e:
                last = e
                if attempt < retries:
                    time.sleep(0.6 * (attempt + 1))
                    continue
                raise
        raise last  # pragma: no cover

    @staticmethod
    def _parse(r: requests.Response) -> dict:
        txt = r.content.decode("utf-8", "replace").lstrip("﻿").strip()
        try:
            obj = _json.loads(txt)
        except Exception:
            return {"_nonjson": True, "raw": txt[:2000], "http_status": r.status_code}
        return obj

    @staticmethod
    def raise_for_auth(resp: dict) -> dict:
        """脉脉 signals 'not logged in' via error_code/error_msg on an otherwise-2xx body."""
        if isinstance(resp, dict):
            ec = resp.get("error_code")
            msg = resp.get("error_msg") or ""
            if ec in (2, 101, 102) or ("登录" in msg and ("失效" in msg or "过期" in msg or "未登录" in msg)):
                raise AuthExpired(msg or "登录状态已失效", resp)
        return resp

    # ---- generic signed calls --------------------------------------------------------------
    def get(self, name: str, module: str | None = None, version: str | None = None,
            params: dict | None = None, base: str = HOST) -> dict:
        """Signed GET to <base>/<module>/<version>/<name> with common+business params."""
        url = self.build_get_url(api.new_api(name, module, version, base), params)
        r = self._http("GET", url, headers=self._headers())
        return self.raise_for_auth(self._parse(r))

    def post(self, name: str, module: str | None = None, version: str | None = None,
             params: dict | None = None, base: str = HOST, is_json: bool = False,
             query_extra: dict | None = None) -> dict:
        """Signed POST to <base>/<module>/<version>/<name>; common params in the query, business
        params in the body (form by default, JSON with is_json=True). `query_extra` appends extra
        query params AFTER the common block (the app does this for e.g. login's need_script=1,
        because getNewApi returns the URL already carrying the common params — confirmed by a live
        frida capture of df.C2665.m11054)."""
        url_path = api.new_api(name, module, version, base)
        sep = "&" if "?" in url_path else "?"
        url = url_path + sep + common.build_common_query(self.s, url_path)
        if query_extra:
            qs = common.build_param_string(query_extra)
            if qs:
                url += "&" + qs
        h = self._headers()
        if is_json:
            h["Content-Type"] = "application/json"
            body = _json.dumps(params or {}, ensure_ascii=False, separators=(",", ":"))
        else:
            h["Content-Type"] = "application/x-www-form-urlencoded"
            body = common.build_param_string(params or {})
        r = self._http("POST", url, data=body.encode("utf-8"), headers=h)
        return self.raise_for_auth(self._parse(r))

    def get_path(self, path: str, params: dict | None = None, method: str = "GET") -> dict:
        """Escape hatch: hit any endpoint by its bare path under maimai (e.g. 'user/v4/settings'
        or 'gossip/v3/stext'). Because there is no per-request signature, a captured session can
        replay ANY read endpoint this way."""
        if method.upper() == "POST":
            return self.post(path, params=params)
        return self.get(path, params=params)

    # ---- convenience read endpoints (RE'd from v6.6.84) ------------------------------------
    def settings(self) -> dict:
        """GetUserSettings — GET user/v4/settings. Cheap session-liveness / whoami-ish check."""
        return self.get("settings", "user", "v4", {"has_read_contacts_permission": 0})

    def suggest(self, chars: str, type: int = 0) -> dict:
        """GetSuggestion — GET sug/get?chars=&type= (search-word suggestions)."""
        return self.get("sug/get", params={"chars": chars, "type": type})

    def feed(self, name: str, params: dict | None = None, v6: bool = False) -> dict:
        return self.get(name, "feed", "v6" if v6 else "v5", params)

    def gossip(self, name: str, params: dict | None = None) -> dict:
        return self.get(name, "gossip", "v3", params)

    def contact(self, name: str, params: dict | None = None, version: str = "v3") -> dict:
        return self.get(name, "contact", version, params)

    # ---- job search (RE'd from the RN 职位 tab, verified live) -----------------------------
    def job_search(self, query: str, page: int = 0, count: int = 10,
                   extra: dict | None = None) -> dict:
        """GET search_front/app/job_search — 脉脉 job search (职位查找). The RN 职位 tab hits this
        with query/page/count (+ rn/use_native_net); reproduced off-device with a captured session.
        Response: {data:[job…], count, remain, filters, search_tags, rec_jobs, …}."""
        params = {"query": query, "page": page, "count": count,
                  "fr": "search_job_list_search_job_list",
                  "rn": 1, "use_native_net": 1}
        if extra:
            params.update(extra)
        return self.get("search_front/app/job_search", params=params)

    @staticmethod
    def parse_jobs(resp: dict) -> list[dict]:
        """Flatten a job_search response into [{name, salary, company, city, degree, exp, scale,
        stage, jobId, ejid}] (fields RE'd from the live response)."""
        out = []
        for j in (resp.get("data") or []):
            if not isinstance(j, dict):
                continue
            out.append({
                "name": j.get("position") or j.get("name"),
                "salary": j.get("salary_info") or (f"{j.get('salary_min')}-{j.get('salary_max')}"
                                                   if j.get("salary_min") else None),
                "company": j.get("company"),
                "scale": j.get("company_scale"),
                "stage": j.get("company_stage"),
                "city": j.get("city"),
                "degree": j.get("degree"),
                "exp": j.get("worktime"),
                "jobId": j.get("id"),
                "ejid": j.get("ejid"),          # encrypted job id (for detail/apply)
                "pub_time": j.get("pub_time"),
            })
        return out


DEFAULT_SESSION = os.environ.get("MAIMAI_SESSION") or "session.local.json"
