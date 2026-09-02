"""Common-param + Uri.encode reproduction (df.C2665.m11054 / vb.AbstractC7495.parameterString)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from maimaicli import common

SESSION = {
    "access_token": "AT_demo", "u": "12345678",
    "version": "6.6.84", "ver_code": "60684", "channel": "appstore",
    "vc": "Android 13/33", "device": "Xiaomi 22011211C", "udid": "udid-abc",
    "android_id": "aid-xyz", "oaid": "oaid-1",
    "density": "3.0", "screen_width": "1080", "screen_height": "2340",
    "launch_uuid": "L-1", "session_uuid": "S-1",
}


def test_uri_encode_android():
    # space -> %20, '/' -> %2F, unreserved kept
    assert common.uri_encode("Android 13/33") == "Android%2013%2F33"
    assert common.uri_encode("a-b_c.d~e") == "a-b_c.d~e"
    assert common.uri_encode("中") == "%E4%B8%AD"


def test_common_query_core_keys():
    q = common.build_common_query(SESSION, "https://open.taou.com/maimai/user/v4/settings")
    assert q.startswith("version=6.6.84&ver_code=android_60684&channel=appstore&")
    assert "vc=Android%2013%2F33" in q
    assert "device=Xiaomi%2022011211C" in q
    assert "appid=3" in q
    assert "rn_version=0.69.0" in q
    assert "&u=12345678" in q
    assert "&access_token=AT_demo" in q
    # no signature param anywhere — the whole point
    for banned in ("&sign=", "&sig=", "&sp=", "&_sig="):
        assert banned not in q


def test_common_query_conditional_vender_block():
    # verify_reg_login_code_v2 substring triggers the vender/install_uuid/language block
    q = common.build_common_query(
        {**SESSION, "install_uuid": "iu-1", "brand": "Xiaomi"},
        "https://open.taou.com/maimai/account/v5/verify_reg_login_code_v2&need_script=1")
    assert "&vender=Xiaomi" in q
    assert "&install_uuid=iu-1" in q
    assert "&language=zh_CN" in q
    assert "&package_name=com.taou.maimai" in q


def test_common_query_skips_missing_optional():
    q = common.build_common_query({"version": "6.6.84"}, "x")
    assert "&oaid=" not in q          # m11055 skips empty
    assert "&access_token=" not in q  # no token -> skipped


def test_param_string():
    ps = common.build_param_string({"mobile": "13900000000", "chars": "张 三", "type": 0})
    assert ps == "mobile=13900000000&chars=%E5%BC%A0%20%E4%B8%89&type=0"


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print(f"  ok  {name}"); n += 1
    print(f"all {n} tests passed")
