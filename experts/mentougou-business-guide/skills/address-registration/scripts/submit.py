#!/usr/bin/env python3
"""
门头沟注册地址申请脚本

功能：
1. 提交地址申请 → POST /opc-admin/api/open/address-applications
2. 查询申请状态 → GET /opc-admin/api/open/address-applications/{application_code}
3. 本地存档到 address_requests/

使用方式：
  # 提交申请
  python scripts/submit.py submit \
    --name "张三" \
    --phone "13800138000" \
    --email "a@example.com" \
    --id-number "110101199001011234" \
    --industry "餐饮" \
    --entity-type "个体工商户" \
    --tax-agency "朝阳区税务局" \
    --address "北京市朝阳区xxx"

  # 查询申请状态
  python scripts/submit.py status --code "20260727A3K9"

  # 交互式提交
  python scripts/submit.py submit --interactive

配置：
  BASE_URL 在此文件配置区修改。
"""

import json
import os
import re
import sys
import argparse
import urllib.request
import urllib.error
from datetime import datetime

# ============ 配置区 ============
BASE_URL = "https://open-api.6fenyi.com"
API_PATH = "/opc-admin/api/open/address-applications"
REVIEW_EMAIL = "opc@6fenyi.cn"
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ADDRESS_REQUESTS_DIR = os.path.join(WORKSPACE_DIR, "address_requests")
# ================================


def api_request(method, path, data=None):
    """通用 API 请求"""
    url = f"{BASE_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    body = None
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8")
            try:
                resp_data = json.loads(raw)
            except json.JSONDecodeError:
                resp_data = raw
            return {"status": status, "body": resp_data}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        try:
            resp_data = json.loads(raw)
        except json.JSONDecodeError:
            resp_data = raw
        return {"status": e.code, "body": resp_data}
    except urllib.error.URLError as e:
        return {"status": 0, "body": f"网络错误: {e.reason}"}


def mask_sensitive(value, keep_end=4):
    """脱敏：仅保留后N位，其余用*替代"""
    if not value or len(value) <= keep_end:
        return value
    return "*" * (len(value) - keep_end) + value[-keep_end:]


def mask_email(email):
    """脱敏邮箱：仅保留首字符和@后部分"""
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}***@{domain}"


def submit_application(name, phone, email, id_number, industry,
                       company_name="", entity_type="", tax_agency="", address="", remarks=""):
    """提交地址申请"""
    payload = {
        "applicant_name": name,
        "phone": phone,
        "email": email,
        "id_card_no": id_number,
        "industry": industry,
    }
    # detail_address 选填
    if address:
        payload["detail_address"] = address
    if company_name:
        payload["company_name"] = company_name
    if entity_type:
        payload["entity_type"] = entity_type
    if tax_agency:
        payload["tax_agency"] = tax_agency
    if remarks:
        payload["remarks"] = remarks

    result = api_request("POST", API_PATH, payload)

    # 本地存档
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    safe_name = name.replace("/", "_")
    filename = f"{date_str}_{safe_name}.json"
    os.makedirs(ADDRESS_REQUESTS_DIR, exist_ok=True)
    filepath = os.path.join(ADDRESS_REQUESTS_DIR, filename)

    record = {
        "提交时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "企业名称": company_name,
        "姓名": name,
        "手机号": mask_sensitive(phone, 4),
        "邮箱": mask_email(email),
        "身份证号": mask_sensitive(id_number, 4),
        "主体类型": entity_type,
        "从事行业": industry,
        "现居住地址": address,
        "是否需要代办税务": tax_agency,
        "备注": remarks,
        "api_response": result,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return result, filepath


def query_status(application_code):
    """查询申请状态"""
    path = f"{API_PATH}/{application_code}"
    return api_request("GET", path)


def collect_info_interactive():
    """交互式收集用户信息"""
    print("=" * 56)
    print("              门头沟注册地址申请")
    print("=" * 56)
    print()
    print("我们为你提供门头沟区注册地址（免费使用）。")
    print("请填写以下信息，提交后等待审核。")
    print()
    print("⚠️ 隐私告知：")
    print("  · 你填写的信息仅用于注册地址申请审核，不会泄露给第三方。")
    print("  · 身份证号用于必要的背景调查，确保地址使用的合规性。")
    print("  · 审核通过后，通过你留下的手机号或邮箱联系你。")
    print()

    info = {}

    info["company_name"] = input("① 企业名称（必填，如未核名可填'核名中'）：").strip()
    info["name"] = input("② 姓名（必填）：").strip()
    info["phone"] = input("③ 手机号（必填）：").strip()
    info["email"] = input("④ 邮箱（必填，用于审核结果通知）：").strip()
    info["id_number"] = input("⑤ 身份证号（必填，用于背景调查）：").strip()

    print("\n主体类型选项（选填）：")
    print("  1. 个体工商户")
    print("  2. 个人独资企业")
    print("  3. 一人有限公司")
    print("  4. 有限责任公司")
    type_choice = input("⑥ 选择主体类型（1/2/3/4，回车跳过）：").strip()
    type_map = {"1": "个体工商户", "2": "个人独资企业", "3": "一人有限公司", "4": "有限责任公司"}
    info["entity_type"] = type_map.get(type_choice, "")

    info["industry"] = input("⑦ 从事行业（必填，如：软件开发、餐饮、电商零售）：").strip()
    info["address"] = input("⑧ 现居住地址（选填，回车跳过）：").strip()

    tax_choice = input("⑨ 是否需要代办税务？(是/否，回车跳过)：").strip()
    info["tax_agency"] = "是" if tax_choice in ["是", "Y", "y", "yes"] else tax_choice

    return info


def validate_fields(info):
    """验证必填字段"""
    errors = []
    if not info.get("company_name"):
        errors.append("企业名称")
    if not info.get("name"):
        errors.append("姓名")
    if not info.get("phone"):
        errors.append("手机号")
    elif not re.match(r"^1\d{10}$", info["phone"]):
        errors.append("手机号格式不正确（11位，1开头）")
    if not info.get("email"):
        errors.append("邮箱")
    if not info.get("id_number"):
        errors.append("身份证号")
    elif not re.match(r"^(\d{15}|\d{17}[\dXx])$", info["id_number"]):
        errors.append("身份证号格式不正确（15位或18位）")
    if not info.get("industry"):
        errors.append("从事行业")
    return errors


def cmd_submit(args):
    """处理 submit 子命令"""
    if args.interactive:
        info = collect_info_interactive()
    else:
        info = {
            "company_name": args.company_name or "",
            "name": args.name,
            "phone": args.phone,
            "email": args.email,
            "id_number": args.id_number,
            "industry": args.industry,
            "entity_type": args.entity_type or "",
            "tax_agency": args.tax_agency or "",
            "address": args.address or "",
            "remarks": args.remarks or "",
        }

    # 验证
    errors = validate_fields(info)
    if errors:
        print(f"⚠️ 以下必填信息缺失或格式错误：{', '.join(errors)}")
        sys.exit(1)

    # 确认
    print("\n── 信息确认 ──")
    for k, v in info.items():
        if v:
            print(f"  {k}：{v}")
    print()

    if args.interactive:
        confirm = input("信息无误？确认提交 (y/n)：").strip().lower()
        if confirm not in ["y", "yes", "是"]:
            print("已取消提交。")
            sys.exit(0)

    # 提交
    print("\n正在提交申请...")
    result, filepath = submit_application(
        name=info["name"],
        phone=info["phone"],
        email=info["email"],
        id_number=info["id_number"],
        industry=info["industry"],
        company_name=info.get("company_name", ""),
        entity_type=info.get("entity_type", ""),
        tax_agency=info.get("tax_agency", ""),
        address=info.get("address", ""),
        remarks=info.get("remarks", ""),
    )

    if isinstance(result["body"], dict):
        body = result["body"]
        code = body.get("code")
        if code in (0, 200):
            data = body.get("data", {})
            app_code = data.get("application_code", "")
            if app_code:
                print(f"\n✅ 申请已成功提交！")
                print(f"   申请编号：{app_code}")
                print(f"   审核完成后通过手机号或邮箱通知你，也可随时用申请编号查询进度。")
                return
        else:
            # 业务错误（如参数校验失败）
            print(f"\n⚠️ 提交失败")
            print(f"   原因：{body.get('msg', '未知错误')}")
            return

    if result["status"] == 200:
        print(f"\n✅ 申请已成功提交！")
    else:
        print(f"\n⚠️ 提交失败（HTTP {result['status']}）")
        if isinstance(result["body"], dict):
            print(f"   原因：{result['body'].get('msg', '未知错误')}")
        print(f"   可稍后重试或联系 {REVIEW_EMAIL}")

    print(f"  本地存档：{filepath}")


def cmd_status(args):
    """处理 status 子命令"""
    code = args.code
    if not code:
        code = input("请输入申请编号：").strip()

    print(f"\n正在查询申请状态（编号：{code}）...")
    result = query_status(code)

    if result["status"] != 200 or not isinstance(result["body"], dict) or result["body"].get("code") not in (0, 200):
        status = result["status"]
        if status == 404:
            print("\n⚠️ 未找到该申请编号，请确认编号是否正确。")
        else:
            msg = result["body"].get("msg", "") if isinstance(result["body"], dict) else ""
            print(f"\n⚠️ 查询失败（HTTP {status}）{msg}")
        return

    data = result["body"]["data"]
    status_map = {1: "待处理", 2: "审批中", 3: "已通过", 4: "已驳回"}
    approval_status = data.get("approval_status", "")
    status_text = status_map.get(approval_status, f"未知({approval_status})")

    print(f"\n  申请编号：{data.get('application_code','')}")
    print(f"  申请人：{data.get('applicant_name','')}")
    id_card = data.get('id_card_no','')
    if len(id_card) >= 8:
        id_card = id_card[:3] + "****" + id_card[-4:]
    print(f"  身份证号：{id_card}")
    print(f"  从事行业：{data.get('industry','')}")
    if data.get('entity_type'):
        print(f"  主体类型：{data['entity_type']}")
    if data.get('detail_address'):
        print(f"  现居住地址：{data['detail_address']}")
    if data.get('remarks'):
        print(f"  备注：{data['remarks']}")
    print(f"  审核状态：{status_text}")
    print(f"  创建时间：{data.get('create_time','')}")

    logs = data.get("approval_logs", [])
    if logs:
        print(f"\n  审批记录：")
        for log in logs:
            fm = status_map.get(log.get("from_status"), "")
            to = status_map.get(log.get("to_status"), "")
            comment = log.get("comment", "")
            ts = log.get("create_time", "")
            line = f"    {fm} → {to}  {ts}"
            if comment:
                line += f" | {comment}"
            print(line)


def main():
    parser = argparse.ArgumentParser(description="门头沟注册地址申请")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # submit 子命令
    submit_parser = subparsers.add_parser("submit", help="提交地址申请")
    submit_parser.add_argument("--name", help="姓名（必填）")
    submit_parser.add_argument("--phone", help="手机号（必填）")
    submit_parser.add_argument("--email", help="邮箱（必填）")
    submit_parser.add_argument("--id-number", help="身份证号（必填，用于背景调查）")
    submit_parser.add_argument("--industry", help="从事行业（必填）")
    submit_parser.add_argument("--company-name", default="", help="企业名称（必填）")
    submit_parser.add_argument("--entity-type", default="", help="主体类型（选填）")
    submit_parser.add_argument("--tax-agency", default="", help="代办税务（选填）")
    submit_parser.add_argument("--address", default="", help="现居住地址（选填）")
    submit_parser.add_argument("--remarks", default="", help="备注（选填，≤500字）")
    submit_parser.add_argument("--interactive", action="store_true", help="交互式收集信息")

    # status 子命令
    status_parser = subparsers.add_parser("status", help="查询申请状态")
    status_parser.add_argument("--code", help="申请编号")

    args = parser.parse_args()

    if args.command == "submit":
        cmd_submit(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
