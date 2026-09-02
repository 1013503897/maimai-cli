"""Endpoint URL building — vb.C7497 reproduction."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from maimaicli import api


def test_new_api_module_version():
    assert api.new_api("send_reg_login_code_v3", "account", "v5") == \
        "https://open.taou.com/maimai/account/v5/send_reg_login_code_v3"


def test_new_api_bare_name():
    assert api.new_api("sug/get") == "https://open.taou.com/maimai/sug/get"


def test_new_api_passthrough_absolute():
    assert api.new_api("https://maimai.cn/x") == "https://maimai.cn/x"


def test_module_shortcuts():
    assert api.feed_api("home") == "https://open.taou.com/maimai/feed/v5/home"
    assert api.feed_api("video_detail", v6=True) == "https://open.taou.com/maimai/feed/v6/video_detail"
    assert api.gossip_api("stext") == "https://open.taou.com/maimai/gossip/v3/stext"
    assert api.user_api("settings", "v4") == "https://open.taou.com/maimai/user/v4/settings"
    assert api.contact_api("addrbook_open_guide", "v5") == \
        "https://open.taou.com/maimai/contact/v5/addrbook_open_guide"


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print(f"  ok  {name}"); n += 1
    print(f"all {n} tests passed")
