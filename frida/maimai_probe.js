/*
 * 脉脉 (com.taou.maimai v6.6.84) dynamic probe — validates the static findings on live traffic.
 *   1. NativeLib.getKey()      -> the value getKey returns (claim: an RSA public key)
 *   2. df.ൡ.അ (= df.C2665.m11054, the common-param appender) -> read the StringBuilder after it
 *      runs -> the fully-assembled request query. Confirms: no sign/sig/sp, only device+auth params.
 *
 * Build: frida-compile maimai_probe.js -o maimai_probe.c.js
 * Run:   python maimai_run.py <PID> maimai_probe.c.js
 */
import Java from 'frida-java-bridge';

function jstr(x) { return (x == null) ? null : ('' + x); }

Java.perform(function () {
  // ---- confirm which df.* / vb.* classes are actually loaded (verifies obfuscated names) ----
  try {
    var names = Java.enumerateLoadedClassesSync();
    var picks = [];
    for (var i = 0; i < names.length; i++) {
      var n = names[i];
      if ((n.indexOf('com.taou.maimai.nativelib') === 0) ||
          (/^df\.[^.]{1,3}$/.test(n)) || (/^vb\.[^.]{1,3}$/.test(n))) picks.push(n);
    }
    send({ tag: 'CLASSES', df_vb: picks.slice(0, 60) });
  } catch (e) { send({ tag: 'ERR', where: 'enum', err: '' + e }); }

  // ---- 1. NativeLib.getKey() : dump the returned key (RSA pubkey?) ----
  try {
    var NL = Java.use('com.taou.maimai.nativelib.NativeLib');
    NL.getKey.implementation = function () {
      var r = this.getKey();
      send({ tag: 'GETKEY', value: jstr(r), len: (r == null ? 0 : ('' + r).length) });
      return r;
    };
    send({ tag: 'INFO', msg: 'NativeLib.getKey hooked' });
  } catch (e) { send({ tag: 'ERR', where: 'getKey', err: '' + e }); }

  // ---- 2. df.C2665.m11054(StringBuilder, Context) : the common-param appender ----
  // runtime name (from jadx): class df.ൡ, method അ. Try that; fall back to scanning if it moved.
  function hookAppender(clsName, methName) {
    var C = Java.use(clsName);
    C[methName].overload('java.lang.StringBuilder', 'android.content.Context')
      .implementation = function (sb, ctx) {
        this[methName](sb, ctx);                 // let the app append its params
        try {
          var url = '' + sb.toString();
          // flag whether any signature-ish param appears (expected: none)
          var hasSig = /[?&](sign|sig|sp|_sig|signature)=/.test(url);
          send({ tag: 'URL', url: url, hasSig: hasSig });
        } catch (e) { send({ tag: 'ERR', where: 'sb', err: '' + e }); }
      };
    send({ tag: 'INFO', msg: 'appender hooked: ' + clsName + '.' + methName });
  }
  try {
    hookAppender('df.ൡ', 'അ');         // df.ൡ . അ  (escaped so the bytes are exact)
  } catch (e) {
    send({ tag: 'WARN', where: 'appender-primary', err: '' + e });
    // fallback: find a df.* class with a static void (StringBuilder, Context) method
    try {
      var loaded = Java.enumerateLoadedClassesSync().filter(function (n) { return /^df\.[^.]{1,3}$/.test(n); });
      send({ tag: 'FALLBACK', candidates: loaded.slice(0, 40) });
    } catch (e2) { send({ tag: 'ERR', where: 'fallback', err: '' + e2 }); }
  }
});
