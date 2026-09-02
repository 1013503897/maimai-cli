/*
 * Full login-flow capture. Hooks:
 *   - df.ൡ.അ (C2665.m11054)  -> every request URL (post-login ones carry &u=&access_token=)
 *   - BaseParcelable.defaultFromJson(String, *) -> every response JSON body (login token, feed, jobs)
 *   - NativeLib.getKey() -> RSA pubkey (password path only)
 *
 * Build: frida-compile maimai_login_capture.js -o maimai_login_capture.c.js
 * Run:   python maimai_spawn.py maimai_login_capture.c.js 600   (spawn so hooks precede login)
 */
import Java from 'frida-java-bridge';

function clip(s, n) { s = '' + s; return s.length > n ? s.substring(0, n) + '…(' + s.length + ')' : s; }

Java.perform(function () {
  // ---- request URLs ----
  try {
    Java.use('df.ൡ')['അ'].overload('java.lang.StringBuilder', 'android.content.Context')
      .implementation = function (sb, ctx) {
        this['അ'](sb, ctx);
        try {
          var url = '' + sb.toString();
          var hasSig = /[?&](sign|sig|sp|signature)=/.test(url);
          var tok = /[?&]access_token=([^&]+)/.exec(url);
          var uid = /[?&]u=([^&]+)/.exec(url);
          send({ tag: 'URL', url: clip(url, 700), hasSig: hasSig,
                 access_token: tok ? tok[1] : null, u: uid ? uid[1] : null });
        } catch (e) {}
      };
    send({ tag: 'INFO', msg: 'm11054 hooked' });
  } catch (e) { send({ tag: 'ERR', where: 'm11054', err: '' + e }); }

  // ---- response bodies (BaseParcelable.defaultFromJson) ----
  try {
    var BP = Java.use('com.taou.common.network.http.base.BaseParcelable');
    function tap(json, type) {
      try {
        var s = '' + json;
        // flag the ones we care about; dump all (clipped) so the log is greppable
        var interesting = /access_token|"token"|"uid"|retry_token|yidun|captcha/.test(s);
        send({ tag: interesting ? 'RESP*' : 'RESP', type: '' + type, json: clip(s, 1400) });
      } catch (e) {}
    }
    BP.defaultFromJson.overload('java.lang.String', 'java.lang.reflect.Type')
      .implementation = function (j, t) { tap(j, t); return this.defaultFromJson(j, t); };
    BP.defaultFromJson.overload('java.lang.String', 'java.lang.Class')
      .implementation = function (j, c) { tap(j, c); return this.defaultFromJson(j, c); };
    send({ tag: 'INFO', msg: 'BaseParcelable.defaultFromJson hooked' });
  } catch (e) { send({ tag: 'ERR', where: 'resp', err: '' + e }); }

  // ---- getKey (password path) ----
  try {
    Java.use('com.taou.maimai.nativelib.NativeLib').getKey.implementation = function () {
      var r = this.getKey();
      send({ tag: 'GETKEY', value: clip(r, 40) });
      return r;
    };
  } catch (e) {}
});
