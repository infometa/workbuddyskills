#!/usr/bin/env python3
"""
肺炎AI辅助诊断 - 自动轮询等待结果脚本
提交后自动轮询 /openapi/pneumoniaQuery 直到任务完成或失败
"""

import argparse
import hmac
import hashlib
import time
import json
import sys

try:
    import requests
except ImportError:
    print("错误：缺少 requests 库，请先安装：pip3 install requests", file=sys.stderr)
    sys.exit(1)


def generate_signature(app_id: str, token: str, timestamp: str) -> str:
    """生成 HMAC-SHA256 签名"""
    message = (app_id + timestamp).encode("utf-8")
    return hmac.new(token.encode("utf-8"), message, hashlib.sha256).hexdigest()


def query_once(app_id: str, token: str, host: str, task_id: str, need_report: str) -> dict:
    """执行一次查询"""
    timestamp = str(int(time.time()))
    signature = generate_signature(app_id, token, timestamp)

    headers = {
        "Content-Type": "application/json",
        "appId": app_id,
        "timestamp": timestamp,
        "signature": signature,
    }
    body = {
        "taskId": task_id,
        "needReport": need_report,
    }

    url = f"{host.rstrip('/')}/openapi/pneumoniaQuery"
    resp = requests.post(url, headers=headers, json=body, timeout=30)
    return resp.json()


def poll_task(app_id: str, token: str, host: str, task_id: str,
              need_report: str = "0", initial_wait: int = 30,
              interval: int = 10, max_attempts: int = 300):
    """自动轮询直到任务完成或失败"""

    print(f"⏳ 初始等待 {initial_wait} 秒后开始查询...", file=sys.stderr, flush=True)
    time.sleep(initial_wait)

    for i in range(max_attempts):
        try:
            result = query_once(app_id, token, host, task_id, need_report)
        except requests.exceptions.Timeout:
            print(f"轮询 {i+1}: 请求超时，重试中...", file=sys.stderr, flush=True)
            time.sleep(interval)
            continue
        except requests.exceptions.ConnectionError as e:
            print(f"轮询 {i+1}: 连接失败 ({e})，重试中...", file=sys.stderr, flush=True)
            time.sleep(interval)
            continue
        except Exception as e:
            print(f"轮询 {i+1}: 异常 ({e})，重试中...", file=sys.stderr, flush=True)
            time.sleep(interval)
            continue

        head = result.get("head", {})
        code = head.get("code", -1)
        status = result.get("status", "")

        if code != 0:
            # 鉴权等非业务错误，直接退出
            print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            print(f"\n❌ 请求失败（code={code}）: {head.get('message', '')}", file=sys.stderr, flush=True)
            sys.exit(1)

        if status == "处理完成":
            print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            sign = result.get("pneumoniaSign", "")
            analysis = result.get("pneumoniaAnalysis", "")
            report_url = result.get("reportUrl", "")
            print(f"\n✅ 分析完成！{sign}", file=sys.stderr, flush=True)
            if analysis:
                print(f"\n📋 病灶详情:\n{analysis}", file=sys.stderr, flush=True)
            if report_url:
                print(f"\n📄 报告链接: {report_url}", file=sys.stderr, flush=True)
            return

        elif status == "处理失败":
            print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            print(f"\n❌ 处理失败: {head.get('message', '')}", file=sys.stderr, flush=True)
            sys.exit(1)

        else:
            # 待处理 或 处理中
            elapsed = initial_wait + (i + 1) * interval
            print(f"轮询 {i+1}/{max_attempts}: status={status}，已等待约 {elapsed}s，{interval}s 后重试...", file=sys.stderr, flush=True)
            time.sleep(interval)

    # 超过最大轮询次数
    total_wait = initial_wait + max_attempts * interval
    print(json.dumps({
        "head": {"code": -1, "message": f"已轮询 {max_attempts} 次（约{total_wait // 60}分钟），任务仍在处理中"},
        "status": "处理中",
        "taskId": task_id,
        "reminder": f"AI 分析仍在进行中，可凭 taskId 继续查询最新结果。"
    }, ensure_ascii=False, indent=2), flush=True)
    print(f"\n⏰ 已轮询 {max_attempts} 次（约{total_wait // 60}分钟），任务仍在处理中。", file=sys.stderr, flush=True)
    print(f"💡 您的 taskId: {task_id}，可继续使用查询脚本获取最终结果。", file=sys.stderr, flush=True)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="肺炎AI辅助诊断 - 自动轮询等待结果")
    parser.add_argument("--app_id", required=True, help="合作方ID（appId）")
    parser.add_argument("--token", required=True, help="密钥（token）")
    parser.add_argument("--host", default="https://pacs.qq.com", help="接口服务地址（默认 https://pacs.qq.com 正式环境）")
    parser.add_argument("--task_id", required=True, help="提交时返回的taskId")
    parser.add_argument("--need_report", default="0", choices=["0", "1"], help="是否需要报告：0不需要，1需要")
    parser.add_argument("--initial_wait", type=int, default=30, help="首次查询前等待秒数（默认30）")
    parser.add_argument("--interval", type=int, default=10, help="轮询间隔秒数（默认10）")
    parser.add_argument("--max_attempts", type=int, default=300, help="最大轮询次数（默认300）")

    args = parser.parse_args()

    poll_task(
        app_id=args.app_id,
        token=args.token,
        host=args.host,
        task_id=args.task_id,
        need_report=args.need_report,
        initial_wait=args.initial_wait,
        interval=args.interval,
        max_attempts=args.max_attempts,
    )


if __name__ == "__main__":
    main()
