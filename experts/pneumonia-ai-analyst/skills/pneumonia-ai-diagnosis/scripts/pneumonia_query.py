#!/usr/bin/env python3
"""
肺炎AI辅助诊断 - 查询任务结果脚本
调用 /openapi/pneumoniaQuery 接口查询分析结果
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


def query_task(app_id: str, token: str, host: str, task_id: str,
               need_report: str = "0", study_id: str = None):
    """查询肺炎AI分析结果"""

    # 1. 生成签名
    timestamp = str(int(time.time()))
    signature = generate_signature(app_id, token, timestamp)

    # 2. 构造请求头
    headers = {
        "Content-Type": "application/json",
        "appId": app_id,
        "timestamp": timestamp,
        "signature": signature,
    }

    # 3. 构造请求体
    body = {
        "taskId": task_id,
        "needReport": need_report,
    }
    if study_id:
        body["studyId"] = study_id

    # 4. 发送请求
    url = f"{host.rstrip('/')}/openapi/pneumoniaQuery"

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        result = resp.json()
    except requests.exceptions.Timeout:
        print(json.dumps({
            "error": "查询请求超时",
            "head": {"code": -1, "message": "查询请求超时"}
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print(json.dumps({
            "error": f"连接失败: {str(e)}",
            "head": {"code": -1, "message": f"连接失败: {str(e)}"}
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "error": f"请求异常: {str(e)}",
            "head": {"code": -1, "message": f"请求异常: {str(e)}"}
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 5. 输出原始JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 6. 友好提示
    head = result.get("head", {})
    code = head.get("code", -1)
    if code == 0:
        status = result.get("status", "")
        if status == "处理完成":
            sign = result.get("pneumoniaSign", "")
            analysis = result.get("pneumoniaAnalysis", "")
            report_url = result.get("reportUrl", "")
            print(f"\n✅ 分析完成！{sign}", file=sys.stderr)
            if analysis:
                print(f"\n📋 病灶详情:\n{analysis}", file=sys.stderr)
            if report_url:
                print(f"\n📄 报告链接: {report_url}", file=sys.stderr)
        elif status in ("待处理", "处理中"):
            print(f"\n⏳ 任务状态: {status}，请稍后查询", file=sys.stderr)
        elif status == "处理失败":
            print(f"\n❌ 处理失败: {head.get('message', '')}", file=sys.stderr)
    else:
        message = head.get("message", "未知错误")
        print(f"\n❌ 查询失败（code={code}）: {message}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="肺炎AI辅助诊断 - 查询分析结果")
    parser.add_argument("--app_id", required=True, help="合作方ID（appId）")
    parser.add_argument("--token", required=True, help="密钥（token）")
    parser.add_argument("--host", default="https://pacs.qq.com", help="接口服务地址（默认 https://pacs.qq.com 正式环境）")
    parser.add_argument("--task_id", required=True, help="提交时返回的taskId（多个以英文分号分隔）")
    parser.add_argument("--need_report", default="0", choices=["0", "1"], help="是否需要报告：0不需要，1需要")
    parser.add_argument("--study_id", default=None, help="检查唯一标识（可选）")

    args = parser.parse_args()

    query_task(
        app_id=args.app_id,
        token=args.token,
        host=args.host,
        task_id=args.task_id,
        need_report=args.need_report,
        study_id=args.study_id,
    )


if __name__ == "__main__":
    main()
