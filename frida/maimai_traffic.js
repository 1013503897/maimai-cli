/*
 * Full traffic capture: native (m11054) + React-Native (RNRequest ctor) request URLs/bodies +
 * response JSON (telemetry filtered out). Use after login to reverse the job / feed / search APIs.
 *
 * Build: frida-compile maimai_traffic.js -o maimai_traffic.c.js
 * Run:   python maimai_run.py <PID> maimai_traffic.c.js 600
 */
import Java from 'frida-java-bridge';

function clip(s, n) { s = '' + s; return s.length > n ? s.substring(0, n) + '…(' + s.length + ')' : s; }

Java.perform(function () {
  // native request URLs (getNewApi -> m11054)
  try {
    Java.use('df.ൡ')['അ'].overload('java.lang.StringBuilder', 'android.content.Context')
      .implementation = function (sb, ctx) {
        this['അ'](sb, ctx);
        try { send({ tag: 'NATIVE', url: clip('' + sb.toString(), 900) }); } catch (e) {}
      };
    send({ tag: 'INFO', msg: 'm11054 hooked' });
  } catch (e) { send({ tag: 'ERR', where: 'm11054', err: '' + e }); }

  // React-Native requests: RNRequest(String url, JsonParams params, RequestType type)
  try {
    var RN = Java.use('com.taou.common.network.http.RNRequest');
    RN.$init.overload('java.lang.String',
                      'com.taou.common.network.http.RNRequest$JsonParams',
                      'com.taou.common.network.http.RequestType')
      .implementation = function (url, jp, rt) {
        try {
          send({ tag: 'RN', url: clip('' + url, 900), method: '' + jp.method.value,
                 add_common: jp.add_common_params.value, body: clip(jp.body.value, 900) });
        } catch (e) { send({ tag: 'ERR', where: 'rn-read', err: '' + e }); }
        return this.$init(url, jp, rt);
      };
    send({ tag: 'INFO', msg: 'RNRequest ctor hooked' });
  } catch (e) { send({ tag: 'ERR', where: 'rn', err: '' + e }); }

  // response bodies (skip telemetry BaseEvent)
  try {
    var BP = Java.use('com.taou.common.network.http.base.BaseParcelable');
    function tap(json, type) {
      var t = '' + type;
      if (t.indexOf('BaseEvent') >= 0) return;            // drop analytics noise
      send({ tag: 'RESP', type: t, json: clip(json, 1600) });
    }
    BP.defaultFromJson.overload('java.lang.String', 'java.lang.reflect.Type')
      .implementation = function (j, t) { tap(j, t); return this.defaultFromJson(j, t); };
    BP.defaultFromJson.overload('java.lang.String', 'java.lang.Class')
      .implementation = function (j, c) { tap(j, c); return this.defaultFromJson(j, c); };
    send({ tag: 'INFO', msg: 'response hook installed' });
  } catch (e) { send({ tag: 'ERR', where: 'resp', err: '' + e }); }
});
