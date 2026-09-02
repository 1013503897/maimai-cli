/*
 * Force-load NativeLib (Kotlin object, lazy singleton), reach its static instance by reflection,
 * and call getKey() — confirms the claim that getKey() returns an RSA public key, no login/network.
 *
 * Build: frida-compile maimai_getkey.js -o maimai_getkey.c.js
 * Run:   python maimai_run.py <PID> maimai_getkey.c.js 8
 */
import Java from 'frida-java-bridge';

Java.perform(function () {
  try {
    var NL = Java.use('com.taou.maimai.nativelib.NativeLib');   // triggers <clinit> -> loads .so + singleton
    var cls = NL.class;
    var fields = cls.getDeclaredFields();
    var inst = null;
    for (var i = 0; i < fields.length; i++) {
      var f = fields[i];
      if (('' + f.getType().getName()) === 'com.taou.maimai.nativelib.NativeLib') {
        f.setAccessible(true);
        inst = f.get(null);
        break;
      }
    }
    if (inst === null) { send({ tag: 'WARN', msg: 'no static NativeLib field' }); return; }
    var wrapped = Java.cast(inst, NL);
    var k = '' + wrapped.getKey();
    send({ tag: 'GETKEY', len: k.length, head: k.substring(0, 24), value: k });
  } catch (e) { send({ tag: 'ERR', where: 'getkey', err: '' + e }); }
});
