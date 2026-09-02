# frida — dynamic validation of the static findings

These scripts confirm, on a live device, the claims the off-device client is built on
(com.taou.maimai **v6.6.84**, Pixel 6 / Android 16, art-runtime-srv 17.16.4).

frida-17 no longer exposes `Java` as a global, so the hook sources `import Java from
'frida-java-bridge'` and are bundled with `frida-compile` before loading (same as the boss-cli
frida flow).

## Build & run

```bash
npm install                                   # frida-java-bridge
frida-compile maimai_probe.js  -o maimai_probe.c.js
frida-compile maimai_getkey.js -o maimai_getkey.c.js

adb forward tcp:27042 tcp:27042               # art-runtime-srv listening on the device

# capture the anonymous startup requests (no login, no SMS):
python maimai_spawn.py maimai_probe.c.js 30
# or attach to a running app by PID:
python maimai_run.py <PID> maimai_probe.c.js 40
```

## What each script proves

- **`maimai_probe.js`** hooks `df.ൡ.അ` (= `df.C2665.m11054`, the common-param appender) and reads
  the `StringBuilder` after it runs — i.e. the fully-assembled request query. Every captured URL
  reports `hasSig:false`. Sample (startup, not logged in):

  ```
  https://open.taou.com/maimai/pbs/check_version?version=6.6.84&ver_code=android_60684
  &channel=MyAPP&vc=Android%2016%2F36&push_permit=1&net=wifi&open=icon&appid=3
  &device=Google%20Pixel%206&udid=fd82870c-…&is_push_open=1&isEmulator=0&rn_version=0.69.0
  &launched_by_user=1&android_id=&webviewUserAgent=…&density=2.625&screen_width=1080
  &screen_height=2209&launch_uuid=…&session_uuid=…
  ```

  This param set / order matches `maimaicli/common.py` byte-for-byte (`tests/test_client.py` pins
  it). The `sdk/global/config` request additionally carried `new_device / rom_version / rom_name /
  vender / install_uuid / language / package_name`, exactly the conditional block common.py adds.

  It also hooks `NativeLib.getKey()`; on password login the capture was:

  ```
  GETKEY  MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKB…IDAQAB   (len 216)
  URL     …/account/v5/verify_reg_login_code_v3?<common>&need_script=1   hasSig:false
  ```

  i.e. `getKey()` is a **1024-bit RSA public key** (used only to encrypt the login password), and
  `need_script=1` is appended to the query **after** the common params — a placement bug this
  capture caught and fixed in `login.py`.

- **`maimai_getkey.js`** force-loads `NativeLib` and calls `getKey()` directly (reflection on the
  Kotlin singleton). Direct out-of-context calls can block; the reliable trigger is a password
  login, which the probe captures naturally.
