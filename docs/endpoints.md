# 脉脉 endpoint map (v6.6.84, live-captured)

Captured on-device (Pixel 6, real logged-in session) by hooking the request assembly — native
requests via `df.C2665.m11054`, React-Native requests via the `RNRequest` constructor. Every URL
also carries the common device/auth params (see `common.py`); only the **path + business params**
are listed here. All reproduced off-device with `mm get <path> -p k=v …`.

Hosts: `open.taou.com/maimai` (primary API) · `maimai.cn/sdk` · `api.taou.com/sdk`.

## Auth / bootstrap

| path | method | notes |
|---|---|---|
| `account/v5/send_reg_login_code_v3` | GET | login: send SMS code (`mobile` [+ 网易易盾]) → `token` |
| `account/v5/verify_reg_login_code_v3` | POST | login: `mobile`,`token`,`code`(or `epassword`) `&need_script=1` → `access_token`+`uid` |
| `pbs/check_version`, `pbs/global_config`, `pbs/polaris/get_variables`, `pbs/user_config`, `pbs/iploc` | GET | startup config |
| `sdk/global/config` (api.taou.com) | GET | + `new_device/rom_*/vender/install_uuid/language/package_name` |

## User / profile

| path | method | notes |
|---|---|---|
| `user/v4/get` | GET | my profile (`user{…115 fields: id,realname,company,position,city…}`) |
| `user/v4/settings` | GET | cheap session-liveness check |
| `user/v3/push_perfect_msg`, `user/v4/wxtip` | GET | misc |

## 职位查找 / jobs  (RN 职位 tab)

| path | method | business params | notes |
|---|---|---|---|
| **`search_front/app/job_search`** | GET | `query`,`page`,`count`,`fr`,`sid`,`rn=1`,`use_native_net=1` | **job search** → `data[]` real jobs (`position`,`salary_info`,`company`,`city`,`degree`,`worktime`,`id`,`ejid`) |
| `search/job_sugs` (maimai.cn/sdk) | GET | `query`,`ptype=job` | search suggestions |
| `search/job_home`, `search/home`, `search/job_filter` | GET | — | search home + filter options |
| `job/v3/job_sub/job_list` | GET | `first_page=1`,`page_size=15`,`type=1` | subscribed-jobs list |
| `job/v3/job_sub/banner_state`, `job/v3/resume_profile_sync/popup`, `job/v3/student_interview_review/eligibility` | GET | — | job-tab widgets |
| `sdk/jobs/{showGuide,has_user_publish,get_show_subscribe_Tip,recruit_user_base_info,mc/get_mc_entrance_config,application/get_gallery_entrance_data}` | GET | — | job-tab RN bootstrap |

## Feed / gossip / msg / other

| path | method | notes |
|---|---|---|
| `feed/v5/get_config` | GET | feed config |
| `sug/get` | GET | global search-word suggestions |
| `msg/v5/{get_msg,im_config_client,check_emoji}` | GET | IM |
| `member/vip_level_config`, `pay/v5/check_gift`, `go_growth/external/value_card/info` | GET | member / pay |
| `growth/switch/{get_onoff_info_v2,set_onoff_info}`, `growth/dsp_monitor/reg_or_login` | GET | growth switches |
| `const`, `adshow`, `imad/advfeed_get_url` | GET | const / ads |

> RN requests add `rn=1` / `use_native_net=1` / `rn_req_version=…` on top of the common params;
> some also `rnVersion` / `uiV6`. Reproduce any of these with `mm get <path> -p rn=1 -p use_native_net=1 …`.
