#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""push_wecom.py — 企微推送（可选出口，拔掉主流程不受影响）

把已生成的头图推送到企业微信群机器人 Webhook。**外发边界**：本脚本会把
素材内容发往腾讯服务器，因此必须显式传 --confirm-outbound，否则拒绝执行
（exit 2）。这是可审计的外发确认，不是障碍。

用法：
  python push_wecom.py --covers cover_a.png cover_b.png \
      --text "今日三方案，回复 A/B/C 或回会话说修改" \
      --webhook "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx" \
      --confirm-outbound

退出码：
  0 = 全部推送成功
  1 = 部分图片推送失败（其余成功）
  2 = 前置条件不满足 / 全部失败（webhook 未配置、外发未确认、图片无法处理等）

Webhook 两种替代方式（脚本绝不自动绕过）：
  ① 在群里添加「群机器人」拿到 Webhook 地址，用 --webhook 传入；
  ② 或在 WorkBuddy 会话内用 wecomcli-message 技能手动推送（无 webhook 时）。
"""

import argparse
import base64
import hashlib
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

WECOM_IMAGE_LIMIT = 2 * 1024 * 1024  # 企微图片消息 2MB 上限


def _post_json(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _load_image_bytes(path):
    """读取图片字节；超过 2MB 时用 Pillow 压缩（JPEG 质量递减），返回 (bytes, note)。"""
    data = Path(path).read_bytes()
    if len(data) <= WECOM_IMAGE_LIMIT:
        return data, "original"
    try:
        from PIL import Image
    except ImportError:
        return None, "over-2MB and Pillow unavailable, skipped"
    img = Image.open(io.BytesIO(data))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    for quality in (85, 75, 65, 55):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        candidate = buf.getvalue()
        if len(candidate) <= WECOM_IMAGE_LIMIT:
            return candidate, "recompressed JPEG q=%d (%dKB)" % (quality, len(candidate) // 1024)
    return None, "over-2MB even after recompress, skipped"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Push covers to WeCom group robot")
    parser.add_argument("--covers", nargs="+", required=True, help="头图文件路径（可多张）")
    parser.add_argument("--text", default=None, help="随图附言（先发一条文本）")
    parser.add_argument("--webhook", default=os.environ.get("WECOM_WEBHOOK", ""),
                        help="群机器人 Webhook URL；缺省读环境变量 WECOM_WEBHOOK")
    parser.add_argument("--confirm-outbound", action="store_true",
                        help="显式确认把素材外发到腾讯服务器（必须）")
    args = parser.parse_args(argv)

    if not args.confirm_outbound:
        print("[PUSH][REFUSED] 缺少 --confirm-outbound。素材内容将离开本机，"
              "必须显式确认外发（exit 2）。", file=sys.stderr)
        return 2
    if not args.webhook:
        print("[PUSH][UNAVAILABLE] 企微 Webhook 未配置。两种替代：", file=sys.stderr)
        print("  ① 群机器人 Webhook：--webhook https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
              file=sys.stderr)
        print("  ② 会话内用 wecomcli-message 技能手动推送。", file=sys.stderr)
        print("主流程不受影响：产物已落盘，进门三句话照常汇报。", file=sys.stderr)
        return 2

    rc = 0
    if args.text:
        resp = _post_json(args.webhook, {"msgtype": "text", "text": {"content": args.text}})
        if resp.get("errcode") != 0:
            print("[PUSH][ERROR] 文本推送失败：%s" % resp, file=sys.stderr)
            rc = 2
        else:
            print("[PUSH] 文本已发送。")

    for path in args.covers:
        p = Path(path)
        if not p.exists():
            print("[PUSH][ERROR] 图片不存在：%s" % p, file=sys.stderr)
            rc = max(rc, 1)
            continue
        data, note = _load_image_bytes(p)
        if data is None:
            print("[PUSH][SKIP] %s：%s" % (p.name, note), file=sys.stderr)
            rc = max(rc, 1)
            continue
        payload = {"msgtype": "image",
                   "image": {"base64": base64.b64encode(data).decode("ascii"),
                             "md5": hashlib.md5(data).hexdigest()}}
        resp = _post_json(args.webhook, payload)
        if resp.get("errcode") != 0:
            print("[PUSH][ERROR] %s 推送失败：%s" % (p.name, resp), file=sys.stderr)
            rc = max(rc, 1)
        else:
            print("[PUSH] %s 已发送（%s）" % (p.name, note))
    return rc


if __name__ == "__main__":
    sys.exit(main())
