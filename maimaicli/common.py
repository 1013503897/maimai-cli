"""
Common request parameters — pure-Python reproduction of df.C2665.m11054(StringBuilder, Context),
the routine 脉脉 calls at the end of every vb.C7497.getNewApi() to append the device / session /
auth params to the request URL. There is NO signature here: the params are the account
`access_token` + `u`(uid) plus a plaintext device fingerprint, and that (over TLS) is the whole
of the app's request authentication.

`build_common_query(session, url)` returns the "k=v&k=v…" string (no leading separator); the
client appends it after '?' or '&' exactly as m11054 does. Values are session-driven; a captured
device profile fills them (see session.example.json). The append order and the per-key
Uri.encode / raw-append distinction mirror the decompiled method byte-for-byte.
"""
from __future__ import annotations

# --- Android Uri.encode(String) reproduction ------------------------------------------------
# Uri.encode(s) with no allowed set keeps only [A-Za-z0-9] and "_-!.~'()*"; everything else is
# percent-encoded as UTF-8 with UPPERCASE hex (space -> %20, NOT '+').
_URI_SAFE = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-!.~'()*")


def uri_encode(s) -> str:
    if s is None:
        return ""
    out = []
    for ch in str(s):
        if ch in _URI_SAFE:
            out.append(ch)
        else:
            for b in ch.encode("utf-8"):
                out.append("%%%02X" % b)
    return "".join(out)


# endpoints that get the extra vender/install_uuid/language/package_name block (m11054)
_VENDER_PATHS = (
    "growth/first_open", "user/v3/register", "user/v3/login",
    "account/v5/verify_reg_login_code_v2", "contact/v4/upload",
    "sdk/global/config", "growth/pttc", "growth/ptts",
    "account/v5/register_complete",
)

# constants baked into the app
RN_VERSION = "0.69.0"
APPID = "3"


def _b(v) -> str:
    """boolean -> "1"/"0" like the app's ternaries."""
    return "1" if v in (1, "1", True, "true") else "0"


def build_common_query(session: dict, url: str) -> str:
    """Return the common-param query string (no leading '?'/'&'). Mirrors df.C2665.m11054.

    Only `session` (device profile) + login (`u`/`access_token`) drive the values; anything
    missing is emitted as an empty value or skipped, matching the app's m11055 helper (which
    appends `key=val` only when val is non-empty)."""
    dev = session
    parts: list[str] = []

    def add(k: str, v, encode: bool = False, raw_missing: bool = True):
        """append k=v.  encode=True mirrors Uri.encode(v); the plain sb.append path is encode=False.
        For m11055-style keys (u/access_token/oaid…) we skip entirely when empty."""
        if v is None or v == "":
            if not raw_missing:
                return
        parts.append(k + "=" + (uri_encode(v) if encode else str(v)))

    def add_opt(k: str, v):
        """m11055(sb, "&k=", v): only when v is non-empty; value appended raw (no encode)."""
        if v not in (None, ""):
            parts.append(k + "=" + str(v))

    push = _b(dev.get("push_open", "0"))

    add("version", dev.get("version", ""))
    add("ver_code", "android_" + str(dev.get("ver_code", "")))
    add("channel", dev.get("channel", "develop"))
    add("vc", dev.get("vc", ""), encode=True)                 # MM_SYSTEM_INFO "Android 13/33"
    add("push_permit", push)
    add("net", dev.get("net", "wifi"))
    add("open", dev.get("open", "icon"))
    add("appid", APPID)
    add("device", dev.get("device", ""), encode=True)         # MM_DEVICE_INFO "Xiaomi 22011211C"
    add("udid", dev.get("udid", ""), encode=True)
    add("is_push_open", push)
    add("isEmulator", _b(dev.get("isEmulator", "0")))
    add("rn_version", RN_VERSION)
    add("launched_by_user", _b(dev.get("launched_by_user", "1")))
    add("android_id", dev.get("android_id", ""), encode=True)
    add_opt("oaid", dev.get("oaid"))
    add_opt("hms_oaid", dev.get("hms_oaid"))
    add_opt("sm_dl", dev.get("sm_dl"))
    add_opt("sm_did", dev.get("sm_did"))

    # identity(uid) + access_token — the actual auth. Appended raw via m11055.
    add_opt("u", session.get("u") or session.get("uid"))
    add_opt("access_token", session.get("access_token"))

    if "sdk/global/config" in url:
        add("new_device", dev.get("new_device", "1"))
        add_opt("rom_version", dev.get("rom_version"))
        add_opt("rom_name", dev.get("rom_name"))

    if dev.get("webview_user_agent"):
        add("webviewUserAgent", dev["webview_user_agent"], encode=True)

    if any(p in url for p in _VENDER_PATHS):
        add("vender", dev.get("vender", dev.get("brand", "")), encode=True)
        add("install_uuid", dev.get("install_uuid", ""), encode=True)
        add("language", dev.get("language", "zh_CN"))
        add("package_name", dev.get("package_name", "com.taou.maimai"))

    add("density", dev.get("density", "3.0"))
    add("screen_width", dev.get("screen_width", "1080"))
    add("screen_height", dev.get("screen_height", "2340"))
    add("launch_uuid", dev.get("launch_uuid", ""), encode=True)
    add("session_uuid", dev.get("session_uuid", ""), encode=True)
    llt = dev.get("last_launch_time")
    if llt:
        add("last_launch_time", llt)

    return "&".join(parts)


def build_param_string(params: dict) -> str:
    """Reproduce vb.AbstractC7495.parameterString(): key=Uri.encode(value), joined '&', for the
    business params of a request. Keys are NOT encoded; empty keys skipped."""
    out = []
    for k, v in params.items():
        if k is None or k == "":
            continue
        out.append(str(k) + "=" + uri_encode(v))
    return "&".join(out)
