"""
脉脉 endpoint URL builder — pure-Python reproduction of vb.C7497 (BaseRequestUtil).

The app builds every API URL as:

    <base>[/<module>][/<version>]/<name>

where base defaults to NetworkConstants.NEW_BASE_URI = "https://open.taou.com/maimai"
(vb.C7497.getNewApi 5-arg). The module/version shortcuts below mirror the app's helpers
(getFeedApi/getGossipApi/getUserApi/…). After the path is assembled, the app appends the
common device/auth params (see common.py, a reproduction of df.C2665.m11054) — that append is
done by the client, not here, so these functions return just the bare path URL.
"""
from __future__ import annotations

# NetworkConstants.NEW_BASE_URI (com.taou.common.data.NetworkConstants)
NEW_BASE_URI = "https://open.taou.com/maimai"
# NetworkConstants.getMaiMaiSdkBaseUrl() / getAPISDKBaseUrl()
MAIMAI_SDK_BASE = "https://maimai.cn/sdk"
API_SDK_BASE = "https://api.taou.com/sdk"


def new_api(name: str, module: str | None = None, version: str | None = None,
            base: str = NEW_BASE_URI) -> str:
    """Reproduce vb.C7497.getNewApi(context, module, version, name, base).

    If `name` is already an absolute http(s) URL it is returned as-is; otherwise the parts are
    joined with '/' (leading slashes tolerated) exactly like the app's StringBuilder logic."""
    if name.startswith("http://") or name.startswith("https://"):
        return name
    sb = [base]
    if module:
        sb.append(module if module.startswith("/") else "/" + module)
    if version:
        sb.append("/" + version)
    sb.append(name if name.startswith("/") else "/" + name)
    return "".join(sb)


# ---- module shortcuts (mirror vb.C7497.get*Api) -------------------------------------------
def feed_api(name: str, v6: bool = False) -> str:          # getFeedApi / getFeedApiV6
    return new_api(name, "feed", "v6" if v6 else "v5")


def gossip_api(name: str) -> str:                          # getGossipApi -> gossip/v3
    return new_api(name, "gossip", "v3")


def contact_api(name: str, version: str = "v3") -> str:    # getContactApi -> contact/v3 (v5 exists)
    return new_api(name, "contact", version)


def user_api(name: str, version: str = "v3") -> str:       # getUserApi/getUserV4Api/getUserV5Api
    return new_api(name, "user", version)


def account_api(name: str) -> str:                          # account/v5 (login family)
    return new_api(name, "account", "v5")


def job_api(name: str) -> str:                              # getJobApi -> job/v3
    return new_api(name, "job", "v3")


def talent_api(name: str) -> str:                          # getTalentApi -> talent/v3
    return new_api(name, "talent", "v3")


def tools_api(name: str) -> str:                           # getToolsApi -> tools/v3
    return new_api(name, "tools", "v3")
