#!/usr/bin/env python3
"""
肺炎AI辅助诊断 - 提交任务脚本
调用 /openapi/pneumoniaSubmit 接口上传DICOM压缩包
"""

import argparse
import hmac
import hashlib
import time
import json
import sys
import os

try:
    import requests
except ImportError:
    print("错误：缺少 requests 库，请先安装：pip3 install requests", file=sys.stderr)
    sys.exit(1)


def generate_signature(app_id: str, token: str, timestamp: str) -> str:
    """生成 HMAC-SHA256 签名"""
    message = (app_id + timestamp).encode("utf-8")
    return hmac.new(token.encode("utf-8"), message, hashlib.sha256).hexdigest()


def submit_task(app_id: str, token: str, host: str, study_id: str,
                dicom_file: str, study_date: str = None, need_report: str = "0",
                patient_id: str = None, patient_name: str = None,
                patient_gender: str = None, patient_age: str = None,
                study_name: str = None):
    """提交肺炎AI分析任务"""

    # 1. 生成签名
    timestamp = str(int(time.time()))
    signature = generate_signature(app_id, token, timestamp)

    # 2. 构造请求头
    headers = {
        "appId": app_id,
        "timestamp": timestamp,
        "signature": signature,
    }

    # 3. 构造表单数据
    data = {
        "studyId": study_id,
        "needReport": need_report,
    }
    if study_date:
        data["studyDate"] = study_date
    if patient_id:
        data["patientId"] = patient_id
    if patient_name:
        data["patientName"] = patient_name
    if patient_gender:
        data["patientGender"] = patient_gender
    if patient_age:
        data["patientAge"] = patient_age
    if study_name:
        data["studyName"] = study_name

    # 4. 上传文件
    if not os.path.isfile(dicom_file):
        print(json.dumps({
            "error": f"文件不存在: {dicom_file}",
            "head": {"code": -1, "message": f"文件不存在: {dicom_file}"}
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    file_size_mb = os.path.getsize(dicom_file) / (1024 * 1024)
    if file_size_mb > 300:
        print(json.dumps({
            "error": f"文件大小 {file_size_mb:.1f}MB 超过300MB限制",
            "head": {"code": -1, "message": f"文件大小 {file_size_mb:.1f}MB 超过300MB限制"}
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    with open(dicom_file, "rb") as f:
        files = {"dicomFile": (os.path.basename(dicom_file), f, "application/zip")}

        url = f"{host.rstrip('/')}/openapi/pneumoniaSubmit"
        print(f"正在提交任务到: {url}", file=sys.stderr)
        print(f"文件: {dicom_file} ({file_size_mb:.1f}MB)", file=sys.stderr)

        try:
            resp = requests.post(url, headers=headers, data=data, files=files, timeout=600)
            result = resp.json()
        except requests.exceptions.Timeout:
            print(json.dumps({
                "error": "请求超时（600秒）",
                "head": {"code": -1, "message": "请求超时"}
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

    # 5. 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 6. 友好提示
    head = result.get("head", {})
    code = head.get("code", -1)
    if code == 0:
        task_id = head.get("taskId", "")
        remaining = head.get("resourceRemaining", "N/A")
        print(f"\n✅ 提交成功！taskId: {task_id}，剩余配额: {remaining}", file=sys.stderr)
        print(f"💡 可使用查询脚本获取结果，建议30秒后开始轮询", file=sys.stderr)
    else:
        message = head.get("message", "未知错误")
        print(f"\n❌ 提交失败（code={code}）: {message}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="肺炎AI辅助诊断 - 提交分析任务")
    parser.add_argument("--app_id", required=True, help="合作方ID（appId）")
    parser.add_argument("--token", required=True, help="密钥（token）")
    parser.add_argument("--host", default="https://pacs.qq.com", help="接口服务地址（默认 https://pacs.qq.com 正式环境）")
    parser.add_argument("--study_id", required=True, help="检查ID，唯一标识一次检查")
    parser.add_argument("--dicom_file", required=True, help="DICOM文件压缩包路径（ZIP格式，最大300MB）")
    parser.add_argument("--study_date", default=None, help="检查时间的秒级时间戳（可选）")
    parser.add_argument("--need_report", default="0", choices=["0", "1"], help="是否需要报告：0不需要（默认），1需要")
    parser.add_argument("--patient_id", default=None, help="患者ID（可选）")
    parser.add_argument("--patient_name", default=None, help="患者姓名（可选）")
    parser.add_argument("--patient_gender", default=None, choices=["0", "1", "2"], help="患者性别：0未知，1男，2女")
    parser.add_argument("--patient_age", default=None, help="患者年龄（整数）")
    parser.add_argument("--study_name", default=None, help="检查项目（如 胸部CT）")

    args = parser.parse_args()

    submit_task(
        app_id=args.app_id,
        token=args.token,
        host=args.host,
        study_id=args.study_id,
        dicom_file=args.dicom_file,
        study_date=args.study_date,
        need_report=args.need_report,
        patient_id=args.patient_id,
        patient_name=args.patient_name,
        patient_gender=args.patient_gender,
        patient_age=args.patient_age,
        study_name=args.study_name,
    )


if __name__ == "__main__":
    main()
