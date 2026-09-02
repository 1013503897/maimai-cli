"""maimai-cli entry point.  Usage: mm {whoami|suggest|get|post|feed|gossip|login} ... [opts]
(or `python -m maimaicli.cli ...` without installing)."""
from __future__ import annotations
import argparse
import json
import os
import sys

from .client import MaimaiClient, AuthExpired
from . import output

DEFAULT_SESSION = os.environ.get("MAIMAI_SESSION") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session.local.json")


def _client(args) -> MaimaiClient:
    if not os.path.exists(args.session):
        sys.exit(f"session file not found: {args.session}\n"
                 f"Copy session.example.json -> session.local.json and fill in your access_token, "
                 f"u(uid) and device profile (see README), or run "
                 f"`mm login --phone <手机号> --code <验证码>`.")
    client = MaimaiClient.from_file(args.session)
    if getattr(args, "token", None):
        client.s["access_token"] = args.token
    return client


def _auth_hint():
    print("[!] 登录状态已失效 (access_token 失效)。用以下命令刷新后重试：", file=sys.stderr)
    print("    mm login --phone <你的手机号> --send   然后  mm login --phone <...> --code <验证码>",
          file=sys.stderr)


def _run(fn):
    try:
        return fn()
    except AuthExpired:
        _auth_hint(); sys.exit(2)


def _kv(items) -> dict:
    fp: dict = {}
    for it in (items or []):
        if "=" not in it:
            sys.exit(f"-p/--param 需形如 KEY=VALUE，收到: {it!r}")
        k, v = it.split("=", 1)
        fp[k.strip()] = v.strip()
    return fp


def _emit(obj, args):
    fmt = "json" if getattr(args, "json", False) else "text"
    body = output.render(obj, fmt)
    if getattr(args, "output", None):
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(body + ("\n" if not body.endswith("\n") else ""))
        print(f"[✓] -> {args.output}")
    else:
        print(body)


def cmd_get(args):
    client = _client(args)
    params = _kv(args.param)
    method = "POST" if args.post else "GET"
    obj = _run(lambda: client.get_path(args.path, params or None, method=method))
    _emit(obj, args)


def cmd_settings(args):
    client = _client(args)
    _emit(_run(lambda: client.settings()), args)


def cmd_suggest(args):
    client = _client(args)
    _emit(_run(lambda: client.suggest(args.chars, type=args.type)), args)


def cmd_feed(args):
    client = _client(args)
    _emit(_run(lambda: client.feed(args.name, _kv(args.param) or None, v6=args.v6)), args)


def cmd_gossip(args):
    client = _client(args)
    _emit(_run(lambda: client.gossip(args.name, _kv(args.param) or None)), args)


def cmd_login(args):
    if not os.path.exists(args.session):
        sys.exit(f"session file not found: {args.session}\n"
                 f"login reuses the device profile from your session file; copy "
                 f"session.example.json -> session.local.json and fill the device profile first.")
    from .login import LoginClient, LoginError, CaptchaRequired, update_session_token
    lc = LoginClient.from_file(args.session)
    try:
        if not args.code and not args.password:
            token = lc.send_code(args.phone, voice=args.voice,
                                 yidun_validate=args.yidun_validate,
                                 yidun_captcha_id=args.yidun_captcha_id)
            print(f"[+] 验证码已发送到 {args.phone} (token={token[:12]}…)")
            if args.send:
                print(f"    收到后用: mm login --phone {args.phone} --code <验证码> --login-token {token}")
                return
            code = input("请输入收到的短信验证码: ").strip()
            tokens = lc.verify_code(args.phone, token, code=code)
        else:
            token = args.login_token
            if not token:
                token = lc.send_code(args.phone, yidun_validate=args.yidun_validate,
                                     yidun_captcha_id=args.yidun_captcha_id)
                print(f"[+] 已发送验证码 (token={token[:12]}…)")
            tokens = lc.verify_code(args.phone, token, code=args.code,
                                    password=args.password, pubkey=args.pubkey)
    except CaptchaRequired as e:
        print(f"[风控拦截] {e}")
        print("    脉脉登录 man/machine = 网易易盾。离设备需先解出，再传 "
              "--yidun-validate <v> --yidun-captcha-id <id>。")
        sys.exit(2)
    except LoginError as e:
        sys.exit(f"[登录失败] {e}")

    update_session_token(args.session, tokens)
    who = "新用户(注册)" if tokens.get("new_user") else "老用户"
    print(f"[✓] 登录成功 · uid={tokens.get('uid')} · {who} · access_token 已写入 {args.session}")
    if not tokens.get("access_token"):
        print("[!] 响应里没解出 access_token，原始响应：")
        print(json.dumps(tokens.get("raw"), ensure_ascii=False, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mm", description="Off-device 脉脉 (com.taou.maimai) API client")
    ap.add_argument("--session", default=DEFAULT_SESSION,
                    help="session json (default: session.local.json / $MAIMAI_SESSION)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_common(p, with_param=True):
        if with_param:
            p.add_argument("-p", "--param", action="append", metavar="KEY=VAL",
                           help="business param (repeatable)")
        p.add_argument("--json", action="store_true", help="raw JSON output")
        p.add_argument("-o", "--output", help="write to this file instead of stdout")
        p.add_argument("--token", help="override access_token")

    g = sub.add_parser("get", help="signed GET/POST to any maimai path (e.g. user/v4/settings)")
    g.add_argument("path", help="bare path under /maimai, e.g. 'user/v4/settings' or 'gossip/v3/stext'")
    g.add_argument("--post", action="store_true", help="use POST (business params in body)")
    add_common(g)
    g.set_defaults(func=cmd_get)

    s = sub.add_parser("settings", help="GET user/v4/settings (session-liveness / whoami-ish)")
    add_common(s, with_param=False)
    s.set_defaults(func=cmd_settings)

    su = sub.add_parser("suggest", help="GET sug/get — search-word suggestions")
    su.add_argument("chars")
    su.add_argument("--type", type=int, default=0)
    add_common(su, with_param=False)
    su.set_defaults(func=cmd_suggest)

    fe = sub.add_parser("feed", help="GET feed/v5|v6/<name>")
    fe.add_argument("name")
    fe.add_argument("--v6", action="store_true", help="use feed/v6 instead of v5")
    add_common(fe)
    fe.set_defaults(func=cmd_feed)

    go = sub.add_parser("gossip", help="GET gossip/v3/<name> (职言)")
    go.add_argument("name")
    add_common(go)
    go.set_defaults(func=cmd_gossip)

    lp = sub.add_parser("login", help="SMS-code login -> obtain access_token into the session file")
    lp.add_argument("--phone", required=True, help="mobile number")
    lp.add_argument("--code", help="the SMS code (skip the interactive prompt)")
    lp.add_argument("--login-token", help="the token from a prior --send step")
    lp.add_argument("--send", action="store_true", help="only send the SMS code, then exit")
    lp.add_argument("--voice", action="store_true", help="request a voice-call code")
    lp.add_argument("--password", help="password login (needs --pubkey)")
    lp.add_argument("--pubkey", help="NativeLib.getKey() RSA public key (base64) for --password")
    lp.add_argument("--yidun-validate", help="solved 网易易盾 validate")
    lp.add_argument("--yidun-captcha-id", help="网易易盾 captcha id")
    lp.set_defaults(func=cmd_login)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
