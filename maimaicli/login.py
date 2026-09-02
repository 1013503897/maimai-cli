"""
Off-device 脉脉 login — mint your own access_token, no device at runtime.

Two calls, both reproduced byte-for-byte from the app's request POJOs (v6.6.84):

  1. GET  account/v5/send_reg_login_code_v3   (com.taou.maimai.growth.pojo.MMSendRegLoginCode.Req
        — note: no usePost() override -> it's a GET) with `mobile` [+ 网易易盾 captcha fields] ->
        response carries a `token` (retry_token) to feed into step 2.
  2. POST account/v5/verify_reg_login_code_v3 (MMVerifyRegLoginCode.Req, usePost()=true) with
        `mobile`, `token`, `code` (SMS) OR `epassword` (RSA-encrypted password), plus the fixed
        `reg_way=1`, `dev_type=3`, `info_type=2`, `new_fr=1` and the app's `&need_script=1` /
        optional `&from=` path suffix. Response yields access_token + uid.

The man/machine step is 网易易盾 (Yidun): off-device it must be solved out-of-band and the
`validate` passed in (`--yidun-validate` / `--yidun-captcha-id`). SMS-code login needs no native
crypto; only the password path calls crypto.encrypt_password (NativeLib.getKey RSA pubkey).
"""
from __future__ import annotations
import json as _json

from .client import MaimaiClient
from . import api, crypto


class LoginError(RuntimeError):
    pass


class CaptchaRequired(RuntimeError):
    """send_reg_login_code demanded a 网易易盾 (Yidun) captcha we didn't supply."""
    def __init__(self, message, resp=None):
        super().__init__(message)
        self.resp = resp


def _ok(resp: dict) -> bool:
    return isinstance(resp, dict) and (resp.get("code") == 0 or str(resp.get("result", "")).lower() == "ok")


def _err(resp: dict) -> str:
    return (resp.get("error_msg") or resp.get("msg") or resp.get("result")
            or f"code={resp.get('code')} error_code={resp.get('error_code')}")


class LoginClient:
    def __init__(self, session: dict):
        self.c = MaimaiClient(session)
        self.s = session

    @classmethod
    def from_file(cls, path: str) -> "LoginClient":
        with open(path, encoding="utf-8") as f:
            return cls(_json.load(f))

    def send_code(self, mobile: str, *, voice: bool = False, yidun_validate: str | None = None,
                  yidun_captcha_id: str | None = None, yidun_error_code: int = 0,
                  refresh_captcha: int = 0, cptoken: str | None = None,
                  cpval: str | None = None) -> str:
        """GET account/v5/send_reg_login_code_v3 -> the token for verify. Raises CaptchaRequired
        if the server insists on a 网易易盾 captcha we didn't pass."""
        params: dict = {"mobile": mobile, "refresh_captcha": refresh_captcha,
                        "yidun_error_code": yidun_error_code}
        if voice:
            params["voice"] = "1"
        if yidun_validate:
            params["yidun_validate"] = yidun_validate
        if yidun_captcha_id:
            params["yidun_captcha_id"] = yidun_captcha_id
        if cptoken:
            params["cptoken"] = cptoken
        if cpval:
            params["cpval"] = cpval
        resp = self.c.get("send_reg_login_code_v3", "account", "v5", params)
        if not _ok(resp):
            msg = _err(resp)
            if resp.get("yidun_captcha_id") or "验证" in str(msg) or resp.get("captcha"):
                raise CaptchaRequired(f"需要 网易易盾 验证: {msg}", resp)
            raise LoginError(f"send_reg_login_code 失败: {msg}")
        token = resp.get("retry_token") or resp.get("token")
        if not token:
            raise LoginError(f"响应未含 token: {resp}")
        return token

    def verify_code(self, mobile: str, token: str, *, code: str | None = None,
                    password: str | None = None, pubkey: str | None = None,
                    from_: str | None = None) -> dict:
        """POST account/v5/verify_reg_login_code_v3 -> {access_token, uid, raw}. Provide `code`
        (SMS) or `password` (+ `pubkey` = NativeLib.getKey())."""
        # need_script=1 (+ optional from) go into the URL query AFTER the common params — the app
        # appends them to getNewApi()'s already-common-param'd result. Verified live via a frida
        # capture: wire URL = verify_reg_login_code_v3?<common>&need_script=1 (NOT before the '?').
        query_extra = {"need_script": 1}
        if from_:
            query_extra["from"] = from_
        params: dict = {
            "mobile": mobile, "token": token,
            "reg_way": "1", "dev_type": 3, "info_type": 2, "new_fr": 1,
        }
        if code:
            params["code"] = code
        elif password:
            pk = pubkey or self.s.get("pubkey") or crypto.MAIMAI_LOGIN_PUBKEY
            params["epassword"] = crypto.encrypt_password(password, pk)
        else:
            raise LoginError("需要 code 或 password")
        resp = self.c.post("verify_reg_login_code_v3", "account", "v5", params,
                           query_extra=query_extra)
        if not _ok(resp):
            raise LoginError(f"verify_reg_login_code 失败: {_err(resp)}")
        return _extract_tokens(resp)


def _extract_tokens(resp: dict) -> dict:
    """Pull access_token + uid out of the verify response (fields the app feeds into LoginInfo)."""
    info = resp.get("info") or {}
    access = (resp.get("access_token") or resp.get("token") or info.get("token")
              or (resp.get("user") or {}).get("access_token"))
    uid = (resp.get("uid") or resp.get("u") or (resp.get("user") or {}).get("id")
           or (resp.get("user") or {}).get("mmid"))
    return {"access_token": access, "uid": uid, "new_user": bool(resp.get("register_token"))
            or bool(info.get("new_user")), "raw": resp}


def update_session_token(session_path: str, tokens: dict) -> None:
    """Write access_token + u(uid) back into the session file (parallels the app storing them in
    LoginInfo, which df.C2665.m11054 then reads for every request)."""
    with open(session_path, encoding="utf-8") as f:
        sess = _json.load(f)
    if tokens.get("access_token"):
        sess["access_token"] = tokens["access_token"]
    if tokens.get("uid"):
        sess["u"] = str(tokens["uid"])
        sess["uid"] = str(tokens["uid"])
    with open(session_path, "w", encoding="utf-8") as f:
        _json.dump(sess, f, ensure_ascii=False, indent=2)
