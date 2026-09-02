#!/usr/bin/env python3
"""Spawn 脉脉 suspended, install hooks, resume, capture the anonymous startup requests
(sdk/global/config, growth/first_open, imad/*, feed visitor …) that all flow through
getNewApi -> df.C2665.m11054. No login / no SMS to anyone.

Usage: python maimai_spawn.py maimai_probe.c.js [seconds]
"""
import sys
import json
import time
import frida

HOST = "127.0.0.1:27042"
PKG = "com.taou.maimai"
SCRIPT = sys.argv[1] if len(sys.argv) > 1 else "maimai_probe.c.js"
SECS = int(sys.argv[2]) if len(sys.argv) > 2 else 25


def on_message(message, data):
    if message["type"] == "send":
        print("[CAP] " + json.dumps(message["payload"], ensure_ascii=False), flush=True)
    elif message["type"] == "error":
        print("[ERR] " + (message.get("stack") or str(message)), flush=True)
    else:
        print("[MSG] " + str(message), flush=True)


def main():
    dev = frida.get_device_manager().add_remote_device(HOST)
    pid = dev.spawn([PKG])
    print(f"[*] spawned {PKG} pid={pid}", flush=True)
    session = dev.attach(pid)
    with open(SCRIPT, "r", encoding="utf-8") as f:
        src = f.read()
    script = session.create_script(src)
    script.on("message", on_message)
    script.load()
    dev.resume(pid)
    print("[*] resumed, capturing startup...", flush=True)
    time.sleep(SECS)
    try:
        script.unload(); session.detach()
    except Exception:
        pass


if __name__ == "__main__":
    main()
