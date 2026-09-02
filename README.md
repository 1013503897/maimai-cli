# maimai-cli

**English** | [中文](#中文)

Talk to the **脉脉 (com.taou.maimai)** API from your terminal or from an AI agent — off-device,
pure Python, no phone/emulator needed to run. Unlike BOSS直聘 (which signs every request in
native `libyzwg.so`), 脉脉 adds **no per-request signature**: a request is authenticated purely by
your account's `access_token` + `u`(uid) and a set of **plaintext device-fingerprint query params**,
all over TLS. So once a session is captured (or minted with `mm login`), a plain HTTP request is
accepted by the server — this project just assembles that request exactly as the app does.

> Research / educational project (companion to [boss-cli](https://github.com/1013503897/boss-cli)).
> It uses **your own logged-in account's token**; you are responsible for complying with 脉脉's
> Terms of Service. Don't hammer the API.

## The finding (why this is simple)

Reverse-engineered from `com.taou.maimai` **v6.6.84**:

- Every API URL is built by `vb.C7497.getNewApi(module, version, name)` →
  `https://open.taou.com/maimai/<module>/<ver>/<name>` (e.g. `account/v5/send_reg_login_code_v3`,
  `user/v4/settings`, `feed/v6/…`, `gossip/v3/…`).
- Just before sending, `df.C2665.m11054(StringBuilder, Context)` appends the **common params** to
  the URL query: `version` · `ver_code` · `channel` · `vc` · `device` · `udid` · `android_id` ·
  `oaid` · **`u`** · **`access_token`** · `density` · `screen_*` · `launch_uuid` · `session_uuid` …
  — **all plaintext, and there is no `sign`/`sig`/`sp` anywhere.**
- The only native crypto on the request path is at **login**: the *password* field is
  RSA-encrypted (`epassword = base64(RSA/PKCS1(NativeLib.getKey(), password))`), where
  `NativeLib.getKey()` returns an RSA **public** key (not a secret). **SMS-code login needs no
  crypto at all.**

Net result: reproducing 脉脉 off-device is mostly bookkeeping — assemble the exact param set and
send it. This repo is that bookkeeping, pinned by byte-exact tests (`tests/`).

## Features

- **Off-device calls** — no phone/emulator/unidbg at runtime; just Python + your session.
- **Generic signed request** — `mm get <path>` hits *any* endpoint under `/maimai` with your
  session (because there's no signature, a captured session can replay anything).
- **Off-device SMS-code login** — `mm login` reproduces `send_reg_login_code_v3` +
  `verify_reg_login_code_v3` end-to-end, so you can mint a fresh `access_token` yourself.
- **Convenience endpoints** — `mm settings` (user/v4/settings), `mm suggest <chars>` (search-word
  suggestions), `mm feed <name>` (feed/v5|v6), `mm gossip <name>` (职言/gossip v3).
- **JSON / text output** — `--json` for raw, `-o` to write a file.
- **MCP server** — expose `maimai_get` / `maimai_settings` / `maimai_suggest` to Claude / any MCP client.

## Install

```bash
pip install -e .                 # installs the `mm` command (dep: requests)
pip install -e ".[mcp]"          # + MCP server        (python -m maimaicli.mcp_server)
pip install -e ".[login]"        # + password-login RSA (pycryptodome); SMS-code login needs none
```

Or run without installing: `python -m maimaicli.cli <cmd> ...`.

## Get your session (one-time)

The client needs, from a **logged-in** 脉脉 app on a device you control:

| field | where it comes from |
|---|---|
| `access_token` | the `access_token` **query param** on any `open.taou.com/maimai/…` request — your login token |
| `u` / `uid` | the `u` query param (your uid) |
| device profile | `version` / `ver_code` / `channel` / `vc` / `device` / `udid` / `android_id` / `oaid` / `density` / `screen_*` / `launch_uuid` / `session_uuid` — all read straight off one captured request's query string |

Capture one request from the app with any HTTPS interceptor (Reqable / Charles / mitmproxy; use a
frida SSL-unpin script if it pins), then copy those values into `session.local.json`:

```bash
cp session.example.json session.local.json    # paste your access_token / u / device params
```

`session.local.json` is gitignored (it holds your token). When calls start returning "not logged
in", grab a fresh `access_token` the same way — or `mm login`.

## Usage

```bash
# any endpoint by its bare path under /maimai (GET by default)
mm get user/v4/settings
mm get sug/get -p chars=张伟 -p type=0
mm get gossip/v3/stext --post -p gid=123 -p share_channel=1     # POST: business params in body
mm get feed/v6/video_detail --post -p page=1 -p count=10

# 职位查找 / job search (search_front/app/job_search) — real 脉脉 job listings
mm jobs "安卓逆向工程师"                    # name | salary | company | [city exp degree]
mm jobs "Python" --count 20 --format md    # text | json | csv | md
mm jobs "算法" --page 1                     # paginate

# convenience wrappers
mm settings                       # GET user/v4/settings (session liveness)
mm suggest 张伟                    # GET sug/get — search-word suggestions
mm feed home                      # GET feed/v5/home
mm gossip <name> -p k=v           # GET gossip/v3/<name>
mm get user/v4/get                # your own profile (name/company/position/…)

# output
mm get user/v4/settings --json          # raw JSON
mm get user/v4/settings -o out.json     # write to a file

# run without installing
python -m maimaicli.cli get user/v4/settings
```

Options: `-p/--param KEY=VAL` (business params, repeatable) · `--post` (POST, params in body) ·
`--json` · `-o <file>` · `--token <access_token>` (override) · `--session <path>`.

### Login (obtain a fresh `access_token` off-device)

```bash
mm login --phone 13900000000                        # send SMS code, then prompt for it -> access_token
mm login --phone 13900000000 --send                 # only send the code (two-step)
mm login --phone 13900000000 --code 1234 --login-token <token-from-send>   # exchange code -> token
mm login --phone 13900000000 --password '***' --pubkey <getKey-RSA-pubkey> # password login (RSA)
```

`login` reuses the device profile in your session file and writes the new `access_token` + `u`
back into it. The man/machine step is **网易易盾 (Yidun)**; off-device you solve it out-of-band and
pass `--yidun-validate <v> --yidun-captcha-id <id>`. SMS-code login needs no native key; only
`--password` uses `NativeLib.getKey()`'s RSA public key (public, extractable once from
`libnativelib_maimai.so`).

### MCP server

```bash
MAIMAI_SESSION=./session.local.json python -m maimaicli.mcp_server
```

Register it in your MCP client (e.g. `~/.claude.json`); tools are `maimai_get(path, params?, post?)`,
`maimai_settings()`, `maimai_suggest(chars, type?)`.

## How it works (short version)

脉脉's request URL = `getNewApi(module, ver, name)` + `?` + the common device/auth params
(`df.C2665.m11054`) + (`&` business params). There is no signature. This project reproduces the
endpoint builder (`maimaicli/api.py`), the common-param appender (`maimaicli/common.py`, including
Android's `Uri.encode`), and the request assembly + send (`maimaicli/client.py`); login is in
`maimaicli/login.py`. Correctness of the deterministic pieces is pinned by tests:

```bash
python tests/test_api.py         # endpoint URLs
python tests/test_common.py      # common-param assembly + Uri.encode (asserts: no signature param)
python tests/test_crypto.py      # md5/sha256 + login RSA round-trip
```

## Verified on-device (frida)

The static findings were confirmed against live traffic on a Pixel 6 (v6.6.84, art-runtime-srv
17.16.4) — see [`frida/`](frida/):

- Hooking `df.C2665.m11054` (the common-param appender) shows every real request URL carrying
  exactly the param set/order `common.py` produces, and **`hasSig:false`** on all of them — no
  signature on the wire. `tests/test_client.py` pins the assembly against a captured URL.
- `NativeLib.getKey()` returned a **1024-bit RSA public key** (`MIGf…IDAQAB`) — confirming it's a
  public key used only to encrypt the login password, not a request secret. That key ships as the
  default in `session.example.json` / `crypto.MAIMAI_LOGIN_PUBKEY`.
- The capture also caught (and fixed) a placement detail: the login `need_script=1` is appended
  **after** the common params (`verify_reg_login_code_v3?<common>&need_script=1`).
- **Full end-to-end loop verified live**: a real SMS-code login (网易易盾 auto-passed, `200`) minted
  an `access_token`; with it, off-device `mm get user/v4/get` returned the real profile and
  `mm jobs "安卓逆向工程师"` returned real job listings — the server accepts the reproduced request
  (`result:"ok"`). The RN 职位 tab's endpoints and the whole endpoint map are in
  [`docs/endpoints.md`](docs/endpoints.md).

## Layout

```
maimaicli/api.py       endpoint URL builder (vb.C7497 reproduction)
maimaicli/common.py    common device/auth params (df.C2665.m11054) + Android Uri.encode
maimaicli/crypto.py    login crypto (re.C6584 DigestUtils: md5/sha/RSA-pubkey password encrypt)
maimaicli/client.py    request assembly (GET/POST) + send + endpoints
maimaicli/login.py     off-device SMS-code / password login (send + verify -> access_token)
maimaicli/output.py    text / json rendering
maimaicli/cli.py       the `mm {get,settings,suggest,feed,gossip,login}` CLI
maimaicli/mcp_server.py MCP wrapper (maimai_get / maimai_settings / maimai_suggest)
tests/                 deterministic regression tests
session.example.json   template for your session
```

> Note: endpoints here are reverse-engineered statically from v6.6.84. The request assembly is
> byte-faithful to the app; live responses depend on your account's own `access_token`.

## Disclaimer

For security research and study only. Do not use in any way that violates 脉脉's Terms of Service
or applicable law; you bear all consequences of use.

---

# 中文

[English](#maimai-cli) | **中文**

在终端或 AI agent 里调 **脉脉（com.taou.maimai）** 的接口 —— 纯 Python、离设备，运行时不需要手机/模拟器。
与 BOSS直聘（每个请求都由 native `libyzwg.so` 加签）不同，脉脉 **没有 per-request 签名**：一条请求的鉴权
完全靠账号的 `access_token` + `u`(uid)，外加一组**明文设备指纹 query 参数**，全程走 TLS。所以只要抓到一次
session（或用 `mm login` 自己签一个），一条普通 HTTP 请求就能被服务器接受 —— 本项目只是把这条请求按 App 的方式装配出来。

> 研究 / 学习用途（[boss-cli](https://github.com/1013503897/boss-cli) 的姊妹项目）。用的是**你自己登录账号的
> token**；请自行遵守脉脉服务条款，别高频打接口。

## 逆向结论（为什么简单）

从 `com.taou.maimai` **v6.6.84** 逆出：

- 每个 API URL 由 `vb.C7497.getNewApi(module, version, name)` 拼成
  `https://open.taou.com/maimai/<module>/<ver>/<name>`（如 `account/v5/send_reg_login_code_v3`、
  `user/v4/settings`、`feed/v6/…`、`gossip/v3/…`）。
- 发送前 `df.C2665.m11054(StringBuilder, Context)` 把**通用参数**追加到 URL query：`version` · `ver_code` ·
  `channel` · `vc` · `device` · `udid` · `android_id` · `oaid` · **`u`** · **`access_token`** · `density` ·
  `screen_*` · `launch_uuid` · `session_uuid` … —— **全部明文，全程没有 `sign`/`sig`/`sp`。**
- 请求链路上唯一的 native 加密在**登录**：*密码*字段做 RSA 加密
  （`epassword = base64(RSA/PKCS1(NativeLib.getKey(), password))`），其中 `NativeLib.getKey()` 返回的是
  RSA **公钥**（非机密）。**短信验证码登录完全不用任何加密。**

结论：脉脉的离设备复现基本是「把参数拼对再发出去」的体力活。本仓库就是这份体力活，用字节级测试兜底（`tests/`）。

## 功能

- **离设备调用** —— 运行时不要手机/模拟器/unidbg，只要 Python + 你的 session。
- **通用签名请求** —— `mm get <path>` 用你的 session 打*任意* `/maimai` 下的端点（因为没有签名，抓到的
  session 可以重放任何读接口）。
- **离设备短信验证码登录** —— `mm login` 端到端复现 `send_reg_login_code_v3` + `verify_reg_login_code_v3`，
  可自己拿新 `access_token`。
- **便捷端点** —— `mm settings`（user/v4/settings）、`mm suggest <chars>`（搜索联想）、`mm feed <name>`
  （feed/v5|v6）、`mm gossip <name>`（职言 gossip v3）。
- **JSON / 文本输出** —— `--json` 原始，`-o` 落盘。
- **MCP 服务** —— 把 `maimai_get` / `maimai_settings` / `maimai_suggest` 暴露给 Claude / 任意 MCP 客户端。

## 安装

```bash
pip install -e .                 # 装上 `mm` 命令（依赖：requests）
pip install -e ".[mcp]"          # + MCP 服务       （python -m maimaicli.mcp_server）
pip install -e ".[login]"        # + 密码登录 RSA（pycryptodome）；短信验证码登录不需要
```

也可不安装直接跑：`python -m maimaicli.cli <命令> ...`。

## 获取 session

需要从一台**已登录**脉脉的设备上拿：

| 字段 | 来源 |
|---|---|
| `access_token` | 任意 `open.taou.com/maimai/…` 请求的 `access_token` query 参数 —— 你的登录 token |
| `u` / `uid` | query 参数 `u`（你的 uid） |
| 设备档 | `version` / `ver_code` / `channel` / `vc` / `device` / `udid` / `android_id` / `oaid` / `density` / `screen_*` / `launch_uuid` / `session_uuid` —— 都直接从抓到的那条请求 query 里抄 |

用任意 HTTPS 抓包工具抓一条 App 请求（脉脉有 pin 就上 frida SSL-unpin），把这些值粘进 `session.local.json`：

```bash
cp session.example.json session.local.json    # 粘你的 access_token / u / 设备参数
```

`session.local.json` 已 gitignore（存着你的 token）。开始返回「未登录」时，照上面再抓个新 `access_token`，或 `mm login`。

## 用法

```bash
# 按 /maimai 下的裸路径打任意端点（默认 GET）
mm get user/v4/settings
mm get sug/get -p chars=张伟 -p type=0
mm get gossip/v3/stext --post -p gid=123 -p share_channel=1     # POST：业务参数进 body
mm get feed/v6/video_detail --post -p page=1 -p count=10

# 职位查找 / job search（search_front/app/job_search）—— 真实脉脉职位
mm jobs "安卓逆向工程师"                    # 岗位 | 薪资 | 公司 | [城市 经验 学历]
mm jobs "Python" --count 20 --format md    # text | json | csv | md
mm jobs "算法" --page 1                     # 翻页

# 便捷封装
mm settings                       # GET user/v4/settings（验活）
mm suggest 张伟                    # GET sug/get —— 搜索联想
mm feed home                      # GET feed/v5/home
mm gossip <name> -p k=v           # GET gossip/v3/<name>
mm get user/v4/get                # 自己的资料（姓名/公司/职位…）

# 输出
mm get user/v4/settings --json          # 原始 JSON
mm get user/v4/settings -o out.json     # 写文件

# 不安装直接跑
python -m maimaicli.cli get user/v4/settings
```

参数：`-p/--param KEY=VAL`（业务参数，可重复）· `--post`（POST，参数进 body）· `--json` · `-o <文件>` ·
`--token <access_token>`（覆盖）· `--session <路径>`。

### 登录（离设备拿新 `access_token`）

```bash
mm login --phone 13900000000                        # 发验证码，再提示输入 -> access_token
mm login --phone 13900000000 --send                 # 只发验证码（两步）
mm login --phone 13900000000 --code 1234 --login-token <发码返回的token>   # 用验证码换 token
mm login --phone 13900000000 --password '***' --pubkey <getKey的RSA公钥>   # 密码登录（RSA）
```

`login` 复用 session 里的设备档，把新 `access_token` + `u` 写回。man/machine 是**网易易盾**；离设备时你自己解掉，
再传 `--yidun-validate <v> --yidun-captcha-id <id>`。短信验证码登录不用 native key；只有 `--password` 会用到
`NativeLib.getKey()` 的 RSA 公钥（公钥、可从 `libnativelib_maimai.so` 一次性抽出）。

### MCP 服务

```bash
MAIMAI_SESSION=./session.local.json python -m maimaicli.mcp_server
```

在 MCP 客户端里注册（如 `~/.claude.json`）；工具名 `maimai_get(path, params?, post?)`、`maimai_settings()`、
`maimai_suggest(chars, type?)`。

## 原理

脉脉请求 URL = `getNewApi(module, ver, name)` + `?` + 通用设备/鉴权参数（`df.C2665.m11054`）+（`&` 业务参数），
没有签名。本项目复现了端点构建器（`maimaicli/api.py`）、通用参数装配器（`maimaicli/common.py`，含 Android 的
`Uri.encode`）、请求装配与发送（`maimaicli/client.py`）；登录在 `maimaicli/login.py`。确定性部分用测试兜底：

```bash
python tests/test_api.py         # 端点 URL
python tests/test_common.py      # 通用参数装配 + Uri.encode（断言：无签名参数）
python tests/test_crypto.py      # md5/sha256 + 登录 RSA 往返
```

## 设备实测验证（frida）

静态结论已在 Pixel 6（v6.6.84，art-runtime-srv 17.16.4）真机流量上验证 —— 见 [`frida/`](frida/)：

- hook `df.C2665.m11054`（通用参数装配器）打印出每条真实请求 URL，参数集/顺序与 `common.py` 逐字段一致，
  且全部 **`hasSig:false`** —— wire 上没有签名。`tests/test_client.py` 用抓到的真实 URL 钉住装配。
- `NativeLib.getKey()` 返回一个 **1024-bit RSA 公钥**（`MIGf…IDAQAB`）—— 印证它是只用于加密登录密码的公钥、
  不是请求密钥。该公钥作为默认值写进 `session.example.json` / `crypto.MAIMAI_LOGIN_PUBKEY`。
- 抓包还发现并修正了一个位置细节：登录 `need_script=1` 追加在通用参数**之后**
  （`verify_reg_login_code_v3?<common>&need_script=1`）。
- **全链路实测打通**：一次真实短信验证码登录（网易易盾无感通过、`200`）签发出 `access_token`；用它离设备
  `mm get user/v4/get` 拉到真实资料、`mm jobs "安卓逆向工程师"` 拉到真实职位列表，服务器接受复现请求
  （`result:"ok"`）。RN 职位 tab 的端点与完整端点图见 [`docs/endpoints.md`](docs/endpoints.md)。

## 目录

```
maimaicli/api.py       端点 URL 构建器（复现 vb.C7497）
maimaicli/common.py    通用设备/鉴权参数（df.C2665.m11054）+ Android Uri.encode
maimaicli/crypto.py    登录加密（re.C6584 DigestUtils：md5/sha/RSA 公钥加密密码）
maimaicli/client.py    请求装配（GET/POST）+ 发送 + 端点
maimaicli/login.py     离设备短信/密码登录（send + verify -> access_token）
maimaicli/output.py    文本 / json 渲染
maimaicli/cli.py       `mm {get,settings,suggest,feed,gossip,login}` CLI
maimaicli/mcp_server.py MCP 封装（maimai_get / maimai_settings / maimai_suggest）
tests/                 确定性回归测试
session.example.json   session 模板
```

> 说明：这里的端点是从 v6.6.84 静态逆向得到的。请求装配对 App 是字节级忠实的；线上响应取决于你自己账号的 `access_token`。

## 免责声明

仅供安全研究与学习交流。请勿用于任何违反脉脉服务条款或相关法律法规的用途；因使用本项目产生的一切后果由使用者自负。
