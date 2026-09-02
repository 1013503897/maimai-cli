"""Request-assembly tests pinned against a LIVE frida capture (Pixel 6, com.taou.maimai v6.6.84).

The oracle is the real URL df.C2665.m11054 produced on-device, captured by hooking that method:
  https://open.taou.com/maimai/pbs/check_version?version=6.6.84&ver_code=android_60684&channel=MyAPP
  &vc=Android%2016%2F36&push_permit=1&net=wifi&open=icon&appid=3&device=Google%20Pixel%206&udid=...
and the login verify URL ended with `...&session_uuid=...&need_script=1` (need_script AFTER common).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from maimaicli import api
from maimaicli.client import MaimaiClient
from maimaicli.login import LoginClient

# device profile mirroring the live capture (Pixel 6, not logged in)
DEV = {
    "version": "6.6.84", "ver_code": "60684", "channel": "MyAPP", "vc": "Android 16/36",
    "push_open": "1", "net": "wifi", "open": "icon", "device": "Google Pixel 6",
    "udid": "fd82870c-4805-4742-8c33-7429bcd5895c", "isEmulator": "0", "launched_by_user": "1",
    "android_id": "", "density": "2.625", "screen_width": "1080", "screen_height": "2209",
    "launch_uuid": "a287df9d-0ec4-4e37-9350-7f9e20f85146",
    "session_uuid": "e60cc1500f0d4a809dcff6404139bf1b",
}


def test_common_prefix_matches_live_capture():
    c = MaimaiClient(dict(DEV))
    url = c.build_get_url(api.new_api("check_version", "pbs", None), None)
    prefix = ("https://open.taou.com/maimai/pbs/check_version?"
              "version=6.6.84&ver_code=android_60684&channel=MyAPP&vc=Android%2016%2F36"
              "&push_permit=1&net=wifi&open=icon&appid=3&device=Google%20Pixel%206"
              "&udid=fd82870c-4805-4742-8c33-7429bcd5895c&is_push_open=1&isEmulator=0"
              "&rn_version=0.69.0&launched_by_user=1&android_id=")
    assert url.startswith(prefix), f"\nGOT: {url}"
    # no signature param, exactly as the live capture (hasSig:false)
    for banned in ("&sign=", "&sig=", "&sp=", "&signature="):
        assert banned not in url


def test_verify_url_need_script_after_common():
    """Live capture: verify_reg_login_code_v3?<common>&need_script=1 (NOT before the '?')."""
    lc = LoginClient(dict(DEV))
    captured = {}

    def fake_http(method, url, data=None, headers=None, retries=2):
        captured["url"] = url; captured["method"] = method; captured["body"] = data
        class R:
            content = b'{"result":"ok","token":"AT_x","uid":"999"}'
            status_code = 200
        return R()

    lc.c._http = fake_http
    lc.verify_code("13000000000", "TOK", code="1234")
    u = captured["url"]
    assert captured["method"] == "POST"
    assert u.startswith("https://open.taou.com/maimai/account/v5/verify_reg_login_code_v3?version=")
    assert u.endswith("&need_script=1"), f"\nGOT tail: {u[-40:]}"
    assert "verify_reg_login_code_v3&need_script=1?" not in u    # the bug the live capture caught
    # business params (code/reg_way/dev_type…) go in the POST body, not the query
    body = captured["body"].decode() if isinstance(captured["body"], bytes) else captured["body"]
    assert "code=1234" in body and "reg_way=1" in body and "dev_type=3" in body
    assert "code=1234" not in u


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print(f"  ok  {name}"); n += 1
    print(f"all {n} tests passed")
