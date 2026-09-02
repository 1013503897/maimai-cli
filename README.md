# maimai-cli

**English** | [中文](#中文)

A small command-line / MCP client for the **脉脉 (com.taou.maimai)** API. Give it a logged-in
session (or mint one with `mm login`) and search jobs, read your profile / feed, and call any 脉脉
endpoint — from your terminal or an AI agent.

> Research / study project. It uses **your own logged-in account's token**; please comply with
> 脉脉's Terms of Service and don't hammer the API.

## Features

- **职位查找 / job search** — `mm jobs "<keyword>"` returns real 脉脉 job listings.
- **Any endpoint** — `mm get <path>` (and `--post`) reaches any path under `/maimai` with your session.
- **Login** — `mm login` does SMS-code (and password) login and writes a fresh `access_token` into your session.
- **Convenience commands** — `mm settings`, `mm suggest`, `mm feed`, `mm gossip`, `mm get user/v4/get` (your profile).
- **Output formats** — text / json / csv / md (`--json`, `--format`, `-o <file>`).
- **MCP server** — expose `maimai_get` / `maimai_settings` / `maimai_suggest` to Claude or any MCP client.

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
| `access_token` | the `access_token` query param on any `open.taou.com/maimai/…` request |
| `u` / `uid` | the `u` query param (your uid) |
| device profile | `version` / `ver_code` / `channel` / `vc` / `device` / `udid` / `android_id` / `oaid` / `density` / `screen_*` / `launch_uuid` / `session_uuid` — copied from that same request's query |

Capture one request from the app with any HTTPS interceptor (Reqable / Charles / mitmproxy), then
fill in `session.local.json`:

```bash
cp session.example.json session.local.json    # paste your access_token / u / device params
```

`session.local.json` is gitignored. When calls start returning "not logged in", grab a fresh
`access_token` the same way — or run `mm login`.

## Usage

```bash
# 职位查找 / job search
mm jobs "安卓逆向工程师"                    # name | salary | company | [city exp degree]
mm jobs "Python" --count 20 --format md    # text | json | csv | md
mm jobs "算法" --page 1                     # paginate

# any endpoint by its bare path under /maimai (GET by default)
mm get user/v4/get                          # your own profile
mm get user/v4/settings
mm get gossip/v3/stext --post -p gid=123 -p share_channel=1   # POST: business params in body

# convenience wrappers
mm settings                       # user/v4/settings
mm suggest 张伟                    # sug/get — search-word suggestions
mm feed home                      # feed/v5/home
mm gossip <name> -p k=v           # gossip/v3/<name>

# output
mm get user/v4/settings --json          # raw JSON
mm get user/v4/settings -o out.json     # write to a file

# run without installing
python -m maimaicli.cli jobs "Python"
```

Options: `-p/--param KEY=VAL` (business params, repeatable) · `--post` (POST, params in body) ·
`--json` · `--format text|json|csv|md` · `-o <file>` · `--token <access_token>` · `--session <path>`.

### Login

```bash
mm login --phone 13900000000                        # send SMS code, then prompt for it -> access_token
mm login --phone 13900000000 --send                 # only send the code (two-step)
mm login --phone 13900000000 --code 1234 --login-token <token-from-send>   # exchange code -> token
mm login --phone 13900000000 --password '***'       # password login
```

`login` reuses the device profile in your session file and writes the new `access_token` + `u`
back into it. The man/machine step is 网易易盾; if it isn't auto-passed, solve it out-of-band and
pass `--yidun-validate <v> --yidun-captcha-id <id>`.

### MCP server

```bash
MAIMAI_SESSION=./session.local.json python -m maimaicli.mcp_server
```

Register it in your MCP client (e.g. `~/.claude.json`); tools are `maimai_get(path, params?, post?)`,
`maimai_settings()`, `maimai_suggest(chars, type?)`.

## Layout

```
maimaicli/api.py       endpoint URL builder
maimaicli/common.py    common device/auth query params
maimaicli/crypto.py    login crypto (RSA password encrypt)
maimaicli/client.py    request assembly + send + endpoints (incl. job_search)
maimaicli/login.py     SMS-code / password login
maimaicli/output.py    text / json / csv / md rendering
maimaicli/cli.py       the `mm {jobs,get,settings,suggest,feed,gossip,login}` CLI
maimaicli/mcp_server.py MCP wrapper
docs/endpoints.md      endpoint map
tests/                 regression tests
session.example.json   template for your session
```

Reverse-engineered from `com.taou.maimai` v6.6.84.

## Disclaimer

For security research and study only. Do not use in any way that violates 脉脉's Terms of Service
or applicable law; you bear all consequences of use.

---

# 中文

[English](#maimai-cli) | **中文**

一个调 **脉脉（com.taou.maimai）** 接口的命令行 / MCP 小工具。给它一个已登录的 session（或用 `mm login` 自己签一个），
就能在终端或 AI agent 里查职位、读资料 / 动态、调用任意脉脉接口。

> 研究 / 学习用途。用的是**你自己登录账号的 token**；请自行遵守脉脉服务条款，别高频打接口。

## 功能

- **职位查找** —— `mm jobs "<关键词>"` 返回真实脉脉职位。
- **任意接口** —— `mm get <path>`（可 `--post`）用你的 session 打 `/maimai` 下任意路径。
- **登录** —— `mm login` 支持短信验证码（及密码）登录，把新 `access_token` 写回 session。
- **便捷命令** —— `mm settings`、`mm suggest`、`mm feed`、`mm gossip`、`mm get user/v4/get`（自己的资料）。
- **多种输出** —— text / json / csv / md（`--json`、`--format`、`-o <文件>`）。
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
| `access_token` | 任意 `open.taou.com/maimai/…` 请求的 `access_token` query 参数 |
| `u` / `uid` | query 参数 `u`（你的 uid） |
| 设备档 | `version` / `ver_code` / `channel` / `vc` / `device` / `udid` / `android_id` / `oaid` / `density` / `screen_*` / `launch_uuid` / `session_uuid` —— 从同一条请求 query 里抄 |

用任意 HTTPS 抓包工具抓一条 App 请求，把这些值填进 `session.local.json`：

```bash
cp session.example.json session.local.json    # 粘你的 access_token / u / 设备参数
```

`session.local.json` 已 gitignore。开始返回「未登录」时，照上面再抓个新 `access_token`，或 `mm login`。

## 用法

```bash
# 职位查找
mm jobs "安卓逆向工程师"                    # 岗位 | 薪资 | 公司 | [城市 经验 学历]
mm jobs "Python" --count 20 --format md    # text | json | csv | md
mm jobs "算法" --page 1                     # 翻页

# 按 /maimai 下的裸路径打任意端点（默认 GET）
mm get user/v4/get                          # 自己的资料
mm get user/v4/settings
mm get gossip/v3/stext --post -p gid=123 -p share_channel=1   # POST：业务参数进 body

# 便捷封装
mm settings                       # user/v4/settings
mm suggest 张伟                    # sug/get —— 搜索联想
mm feed home                      # feed/v5/home
mm gossip <name> -p k=v           # gossip/v3/<name>

# 输出
mm get user/v4/settings --json          # 原始 JSON
mm get user/v4/settings -o out.json     # 写文件

# 不安装直接跑
python -m maimaicli.cli jobs "Python"
```

参数：`-p/--param KEY=VAL`（业务参数，可重复）· `--post`（POST，参数进 body）· `--json` ·
`--format text|json|csv|md` · `-o <文件>` · `--token <access_token>` · `--session <路径>`。

### 登录

```bash
mm login --phone 13900000000                        # 发验证码，再提示输入 -> access_token
mm login --phone 13900000000 --send                 # 只发验证码（两步）
mm login --phone 13900000000 --code 1234 --login-token <发码返回的token>   # 用验证码换 token
mm login --phone 13900000000 --password '***'       # 密码登录
```

`login` 复用 session 里的设备档，把新 `access_token` + `u` 写回。man/machine 是网易易盾；若没有无感通过，
自己解掉后传 `--yidun-validate <v> --yidun-captcha-id <id>`。

### MCP 服务

```bash
MAIMAI_SESSION=./session.local.json python -m maimaicli.mcp_server
```

在 MCP 客户端里注册（如 `~/.claude.json`）；工具名 `maimai_get(path, params?, post?)`、`maimai_settings()`、
`maimai_suggest(chars, type?)`。

## 目录

```
maimaicli/api.py       端点 URL 构建器
maimaicli/common.py    通用设备/鉴权 query 参数
maimaicli/crypto.py    登录加密（RSA 加密密码）
maimaicli/client.py    请求装配 + 发送 + 端点（含 job_search）
maimaicli/login.py     短信 / 密码登录
maimaicli/output.py    text / json / csv / md 渲染
maimaicli/cli.py       `mm {jobs,get,settings,suggest,feed,gossip,login}` CLI
maimaicli/mcp_server.py MCP 封装
docs/endpoints.md      端点图
tests/                 回归测试
session.example.json   session 模板
```

逆向自 `com.taou.maimai` v6.6.84。

## 免责声明

仅供安全研究与学习交流。请勿用于任何违反脉脉服务条款或相关法律法规的用途；因使用本项目产生的一切后果由使用者自负。
