#!/usr/bin/env python3
"""Headless frida driver: attach 脉脉 via remote art-runtime-srv, load a compiled hook, print captures.

Usage: python maimai_run.py <PID> maimai_probe.c.js [seconds]
(Morphida anti-detect masks process names -> attach by PID.)
"""
import sys
import json
import time
import frida

HOST = "127.0.0.1:27042"
TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else "com.taou.maimai"
SCRIPT = sys.argv[2] if len(sys.argv) > 2 else "maimai_probe.c.js"
SECS = int(sys.argv[3]) if len(sys.argv) > 3 else 0  # 0 = run until Ctrl-C


def on_message(message, data):
    if message["type"] == "send":
        print("[CAP] " + json.dumps(message["payload"], ensure_ascii=False), flush=True)
    elif message["type"] == "error":
        print("[ERR] " + (message.get("stack") or str(message)), flush=True)
    else:
        print("[MSG] " + str(message), flush=True)


def main():
    dev = frida.get_device_manager().add_remote_device(HOST)
    session = dev.attach(TARGET)
    print(f"[*] attached to {TARGET} @ {HOST}", flush=True)
    with open(SCRIPT, "r", encoding="utf-8") as f:
        src = f.read()
    script = session.create_script(src)
    script.on("message", on_message)
    script.load()
    print("[*] script loaded, capturing...", flush=True)
    if SECS:
        time.sleep(SECS)
        script.unload(); session.detach()
    else:
        while True:
            time.sleep(1)


if __name__ == "__main__":
    main()
