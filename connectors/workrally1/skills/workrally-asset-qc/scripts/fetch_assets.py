#!/usr/bin/env python
"""串行下载资产（Pitfall 2：并行 curl 会静默截断），下载后校验 PNG 完整性并实测尺寸。"""
import json
import os
import struct
import subprocess
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")


def png_ok(path):
    d = open(path, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        return False, "not png"
    pos = 8
    idat = b""
    try:
        while pos < len(d):
            (ln,) = struct.unpack(">I", d[pos:pos + 4])
            t = d[pos + 4:pos + 8]
            if t == b"IDAT":
                idat += d[pos + 8:pos + 8 + ln]
            pos += 12 + ln
        zlib.decompress(idat)
        return True, "ok"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def sips_size(path):
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                       capture_output=True, text=True)
    w = h = "?"
    for line in r.stdout.splitlines():
        if "pixelWidth" in line:
            w = line.split(":")[-1].strip()
        if "pixelHeight" in line:
            h = line.split(":")[-1].strip()
    return w, h


def main():
    reg = json.load(open(os.path.join(ROOT, "assets_registry.json")))
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for a in reg["assets"]:
        dest = os.path.join(OUT, a["file"])
        if not os.path.exists(dest) or os.path.getsize(dest) < 10000:
            r = subprocess.run(["curl", "-sL", "--max-time", "300", "-o", dest, a["download_url"]])
            if r.returncode != 0:
                print(f"FAIL download {a['code']}")
                continue
        ok, why = png_ok(dest)
        w, h = sips_size(dest)
        size = os.path.getsize(dest)
        flag = "OK " if ok else "BAD"
        rows.append((a["code"], a["file"], w, h, size, flag, why))
        print(f"{flag} {a['code']:<10} {w}x{h}  {size/1e6:.2f}MB  {a['file']}  {why}")
    print("\n合计:", len(rows), "张")
    bad = [r for r in rows if r[5] != "OK "]
    print("异常:", len(bad))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
