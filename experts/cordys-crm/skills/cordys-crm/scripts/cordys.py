#!/usr/bin/env python3
"""
CORDYS CRM CLI 工具
使用 X-Access-Key / X-Secret-Key 进行鉴权
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from urllib import parse, request
from urllib.error import HTTPError, URLError

try:
    from dotenv import load_dotenv
except ImportError:
    # 如果没有 python-dotenv，提供简单的 .env 加载实现
    def load_dotenv(dotenv_path=None):
        if dotenv_path and os.path.exists(dotenv_path):
            with open(dotenv_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip(
                            '"').strip("'")


# ── 路径配置 ──────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ENV_FILE = SKILL_DIR / ".env"

# 加载环境变量
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

CORDYS_CRM_DOMAIN = os.environ.get(
    "CORDYS_CRM_DOMAIN", "https://www.cordys.cn")
CORDYS_ACCESS_KEY = os.environ.get("CORDYS_ACCESS_KEY", "")
CORDYS_SECRET_KEY = os.environ.get("CORDYS_SECRET_KEY", "")

# 提示：若未设置 CORDYS_CRM_DOMAIN 环境变量，将使用默认值 https://www.cordys.cn。
# 如果您使用的是私有部署或其他域名，请在 .env 文件中配置 CORDYS_CRM_DOMAIN。
if not os.environ.get("CORDYS_CRM_DOMAIN"):
    print(":: 提示: 未设置 CORDYS_CRM_DOMAIN，使用默认域名 https://www.cordys.cn", file=sys.stderr)
    print(":: 如需使用其他域名，请在 .env 文件中配置 CORDYS_CRM_DOMAIN", file=sys.stderr)


# ── 辅助函数 ───────────────────────────────────────────────────────────
def die(message: str) -> None:
    """打印错误信息并退出"""
    print(f"错误: {message}", file=sys.stderr)
    sys.exit(1)


def info(message: str) -> None:
    """打印信息"""
    print(f":: {message}", file=sys.stderr)


def check_keys() -> None:
    """检查必需的 API 密钥"""
    if not CORDYS_ACCESS_KEY:
        die("未设置 CORDYS_ACCESS_KEY")
    if not CORDYS_SECRET_KEY:
        die("未设置 CORDYS_SECRET_KEY")

def warn(message: str) -> None:
    """打印警告信息"""
    print(f"⚠️  警告: {message}", file=sys.stderr)

def validate_url(url: str) -> bool:
    """验证URL是否指向可信的Cordys CRM域名"""
    from urllib.parse import urlparse
    
    # 解析URL
    parsed = urlparse(url)
    if not parsed.netloc:
        return True  # 不是完整URL，可能是相对路径
    
    # 从配置的CORDYS_CRM_DOMAIN中提取可信域名
    trusted_parsed = urlparse(CORDYS_CRM_DOMAIN)
    trusted_domain = trusted_parsed.netloc or CORDYS_CRM_DOMAIN
    
    # 检查域名是否匹配（支持子域名）
    request_domain = parsed.netloc
    
    if request_domain != trusted_domain and not request_domain.endswith(f".{trusted_domain}"):
        warn(f"目标域名 '{request_domain}' 与配置的Cordys CRM域名 '{trusted_domain}' 不匹配")
        warn("这可能会泄露您的API凭证！")
        return False
    
    return True


def page_payload(keyword: str = "") -> Dict[str, Any]:
    """生成分页请求的标准 payload"""
    return {
        "current": 1,
        "pageSize": 30,
        "sort": {},
        "combineSearch": {
            "searchMode": "AND",
            "conditions": []
        },
        "keyword": keyword,
        "viewId": "ALL",
        "filters": []
    }


def merge_payload(user_json: str = "") -> Dict[str, Any]:
    """合并用户 JSON 到默认 payload，确保 current 和 pageSize 始终存在"""
    default = page_payload()
    if not user_json or not user_json.strip():
        return default
    try:
        user = json.loads(user_json)
    except json.JSONDecodeError:
        # 不是合法 JSON，当作 keyword 处理
        default["keyword"] = user_json
        return default
    merged = {**default, **user}
    # 确保 current 和 pageSize 有值（即使用户传了无效值）
    if not isinstance(merged.get("current"), int) or merged["current"] < 1:
        merged["current"] = 1
    if not isinstance(merged.get("pageSize"), int) or merged["pageSize"] < 1:
        merged["pageSize"] = 30
    return merged


# ── API 封装（Header Key 鉴权）────────────────────────────────────────
def api_request(method: str, url: str, content_type: str, **kwargs) -> str:
    """执行 API 请求"""
    check_keys()

    headers = {
        "X-Access-Key": CORDYS_ACCESS_KEY,
        "X-Secret-Key": CORDYS_SECRET_KEY,
        "X-Request-Source": "SKILL",
        "Content-Type": f"{content_type}; charset=utf-8"
    }

    # 合并用户提供的 headers（如果有）
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))

    params = kwargs.pop("params", None)
    data = kwargs.pop("data", None)

    if params:
        if isinstance(params, dict):
            query = parse.urlencode(params)
        else:
            query = str(params).lstrip("?")
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"

    data_bytes = None
    if data is not None:
        if isinstance(data, bytes):
            data_bytes = data
        elif isinstance(data, dict):
            data_bytes = parse.urlencode(data).encode("utf-8")
        else:
            data_bytes = str(data).encode("utf-8")

    try:
        req = request.Request(
            url=url,
            data=data_bytes,
            headers=headers,
            method=method.upper()
        )
        with request.urlopen(req) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            detail = str(e)
        die(f"请求失败: HTTP {e.code} {detail}")
    except URLError as e:
        die(f"请求失败: {e}")


def api(method: str, url: str, **kwargs) -> str:
    """执行 JSON API 请求"""
    return api_request(method, url, "application/json", **kwargs)


def api_form(method: str, url: str, **kwargs) -> str:
    """执行表单 API 请求"""
    return api_request(
        method, url, "application/x-www-form-urlencoded", **kwargs)


# ── CRM 辅助函数 ──────────────────────────────────────────────────────
def crm_view(module: str, opts: str = "") -> str:
    """列出视图记录"""
    params = opts if opts else None
    return api("GET", f"{CORDYS_CRM_DOMAIN}/{module}/view/list", params=params)


def crm_get(module: str, id: str) -> str:
    """获取单条记录详情"""
    return api("GET", f"{CORDYS_CRM_DOMAIN}/{module}/{id}")


def crm_contact(module: str, id: str) -> str:
    """获取联系人列表"""
    return api("GET", f"{CORDYS_CRM_DOMAIN}/{module}/contact/list/{id}")


def crm_page(module: str, payload_or_keyword: str = "") -> str:
    """列表分页记录"""
    if payload_or_keyword.startswith("{"):
        body = payload_or_keyword
    else:
        body = json.dumps(page_payload(payload_or_keyword), ensure_ascii=False)

    path = f"{module}/page"
    return api("POST", f"{CORDYS_CRM_DOMAIN}/{path}", data=body)


def crm_search(module: str, json_data: str = "") -> str:
    """全局搜索记录"""
    merged = merge_payload(json_data)
    body = json.dumps(merged, ensure_ascii=False)
    path = f"global/search/{module}"
    return api("POST", f"{CORDYS_CRM_DOMAIN}/{path}", data=body)


def crm_follow_page(kind: str, module: str, payload: str = "") -> str:
    """查询跟进计划或跟进记录"""
    if kind not in ["plan", "record"]:
        die("follow 子命令只支持 plan/record")
    if not module:
        die(f"follow {kind} 需要指定模块（lead/account 等）")

    if payload.startswith("{"):
        body = payload
    else:
        body = json.dumps(page_payload(payload), ensure_ascii=False)

    return api("POST", f"{CORDYS_CRM_DOMAIN}/{module}/follow/{kind}/page", data=body)


# ── 审批相关 ──────────────────────────────────────────────────────────
def crm_approval_todo(kind: str, payload: str = "") -> str:
    """审批代办列表"""
    merged = merge_payload(payload)
    body = json.dumps(merged, ensure_ascii=False)
    kind_map = {
        "pending":   f"{CORDYS_CRM_DOMAIN}/approval-todo/pending/page",
        "processed": f"{CORDYS_CRM_DOMAIN}/approval-todo/processed/page",
        "initiated": f"{CORDYS_CRM_DOMAIN}/approval-todo/initiated/page",
        "cc":        f"{CORDYS_CRM_DOMAIN}/approval-todo/cc/page",
    }
    if kind == "count":
        return api("GET", f"{CORDYS_CRM_DOMAIN}/approval-todo/pending/count")
    if kind not in kind_map:
        die(f"未知的审批代办类型: {kind}。支持: pending, processed, initiated, cc, count")
    return api("POST", kind_map[kind], data=body)


def crm_approval_action(action: str, payload: str = "") -> str:
    """审批操作（同意/驳回/退回/加签/撤回/批量）"""
    if not payload or not payload.strip().startswith("{"):
        die(f"{action} 需要 JSON body")
    action_map = {
        "approve":       f"{CORDYS_CRM_DOMAIN}/approval-action/approve",
        "reject":        f"{CORDYS_CRM_DOMAIN}/approval-action/reject",
        "back":          f"{CORDYS_CRM_DOMAIN}/approval-action/back",
        "sign":          f"{CORDYS_CRM_DOMAIN}/approval-action/sign",
        "revoke":        f"{CORDYS_CRM_DOMAIN}/approval-action/revoke",
        "batch-approve": f"{CORDYS_CRM_DOMAIN}/approval-action/batch-approve",
        "batch-reject":  f"{CORDYS_CRM_DOMAIN}/approval-action/batch-reject",
    }
    if action not in action_map:
        die(f"未知的审批操作: {action}。支持: approve, reject, back, sign, revoke, batch-approve, batch-reject")
    return api("POST", action_map[action], data=payload)


def crm_approval_resource(action: str, arg: str = "") -> str:
    """审批资源（提审/撤销/详情）"""
    if action == "push":
        return api("POST", f"{CORDYS_CRM_DOMAIN}/approval-resource/push", data=arg)
    elif action == "revoke":
        return api("POST", f"{CORDYS_CRM_DOMAIN}/approval-resource/revoke", data=arg)
    elif action == "simple-detail":
        return api("GET", f"{CORDYS_CRM_DOMAIN}/approval-resource/simple-detail/{arg}")
    elif action == "detail":
        return api("GET", f"{CORDYS_CRM_DOMAIN}/approval-resource/detail/{arg}")
    else:
        die(f"未知的审批资源操作: {action}。支持: push, revoke, simple-detail, detail")


def crm_approval_flow(action: str, arg: str = "") -> str:
    """审批流管理"""
    base = CORDYS_CRM_DOMAIN
    if action == "list":
        return api("POST", f"{base}/approval-flow/page", data=arg)
    elif action == "get":
        return api("GET", f"{base}/approval-flow/get/{arg}")
    elif action == "add":
        return api("POST", f"{base}/approval-flow/add", data=arg)
    elif action == "update":
        return api("POST", f"{base}/approval-flow/update", data=arg)
    elif action == "delete":
        return api("GET", f"{base}/approval-flow/delete/{arg}")
    elif action == "enable":
        return api("GET", f"{base}/approval-flow/enable/{arg}?enable=true")
    elif action == "disable":
        return api("GET", f"{base}/approval-flow/enable/{arg}?enable=false")
    elif action == "by-form":
        return api("GET", f"{base}/approval-flow/get-by-form-type/{arg}")
    elif action == "setting":
        return api("GET", f"{base}/approval-flow/status-permission/setting/{arg}")
    elif action == "webhook-test":
        return api("POST", f"{base}/approval-flow/webhook/test", data=arg)
    else:
        die(f"未知的审批流操作: {action}")


def crm_product(keyword: str = "") -> str:
    """查询产品"""
    if keyword.startswith("{"):
        body = keyword
    else:
        body = json.dumps(page_payload(keyword), ensure_ascii=False)

    return api("POST", f"{CORDYS_CRM_DOMAIN}/field/source/product", data=body)


def crm_whoami() -> str:
    """获取当前登录用户信息"""
    return api("GET", f"{CORDYS_CRM_DOMAIN}/personal/center/info")


def crm_verify() -> str:
    """验证 API 密钥是否有效，返回用户信息"""
    return crm_whoami()


def crm_org() -> str:
    """获取组织架构"""
    return api("GET", f"{CORDYS_CRM_DOMAIN}/department/tree")


def crm_members(json_data: str) -> str:
    """根据部门ID获取成员"""
    return api("POST", f"{CORDYS_CRM_DOMAIN}/user/list", data=json_data)


# ── 统计 API ──────────────────────────────────────────────────────────
def crm_stat(module: str, payload: str = "") -> str:
    """模块金额统计"""
    if payload.startswith("{"):
        body = payload
    else:
        body = json.dumps(page_payload(payload), ensure_ascii=False)
    stat_map = {
        "contract":                f"{CORDYS_CRM_DOMAIN}/contract/statistic",
        "contract/payment-record": f"{CORDYS_CRM_DOMAIN}/contract/payment-record/statistic",
        "opportunity":             f"{CORDYS_CRM_DOMAIN}/opportunity/statistic",
        "order":                   f"{CORDYS_CRM_DOMAIN}/order/statistic",
    }
    if module not in stat_map:
        die(f"不支持的统计模块: {module}。支持: contract, contract/payment-record, opportunity, order")
    return api("POST", stat_map[module], data=body)


def crm_stat_home(kind: str, payload: str = "") -> str:
    """首页统计"""
    if payload.startswith("{"):
        body = payload
    else:
        body = json.dumps({
            "searchType": "SELF",
            "timeField": "CREATE_TIME",
            "userField": "OWNER",
            "priorPeriodEnable": True
        }, ensure_ascii=False)
    home_map = {
        "lead":                   f"{CORDYS_CRM_DOMAIN}/home/statistic/lead",
        "opportunity":            f"{CORDYS_CRM_DOMAIN}/home/statistic/opportunity",
        "opportunity/success":    f"{CORDYS_CRM_DOMAIN}/home/statistic/opportunity/success",
        "opportunity/underway":   f"{CORDYS_CRM_DOMAIN}/home/statistic/opportunity/underway",
        "dept-tree":              f"{CORDYS_CRM_DOMAIN}/home/statistic/department/tree",
    }
    if kind not in home_map:
        die(f"不支持的首頁统计类型: {kind}。支持: lead, opportunity, opportunity/success, opportunity/underway, dept-tree")
    if kind == "dept-tree":
        return api("GET", home_map[kind])
    return api("POST", home_map[kind], data=body)


def crm_glocount(keyword: str) -> str:
    """全局搜索各模块命中计数"""
    if not keyword:
        die("glocount 需要关键词")
    return api("GET", f"{CORDYS_CRM_DOMAIN}/global/search/module/count?keyword={keyword}")


def crm_acct_sub(sub: str, acct_id: str, payload: str = "") -> str:
    """客户子资源查询"""
    if not sub or not acct_id:
        die("acct-sub 需要子资源和客户ID")
    if payload.startswith("{"):
        body = payload
    else:
        body = json.dumps(page_payload(payload), ensure_ascii=False)
    sub_map = {
        "contract":             f"{CORDYS_CRM_DOMAIN}/account/contract/page",
        "contract-stat":        f"{CORDYS_CRM_DOMAIN}/account/contract/statistic/{acct_id}",
        "opportunity":          f"{CORDYS_CRM_DOMAIN}/account/opportunity/page",
        "order":                f"{CORDYS_CRM_DOMAIN}/account/order/page",
        "payment-plan":         f"{CORDYS_CRM_DOMAIN}/account/contract/payment-plan/page",
        "payment-plan-stat":    f"{CORDYS_CRM_DOMAIN}/account/contract/payment-plan/statistic/{acct_id}",
        "payment-record":       f"{CORDYS_CRM_DOMAIN}/account/contract/payment-record/page",
        "payment-record-stat":  f"{CORDYS_CRM_DOMAIN}/account/contract/payment-record/statistic/{acct_id}",
        "invoice":              f"{CORDYS_CRM_DOMAIN}/account/invoice/page",
        "invoice-stat":         f"{CORDYS_CRM_DOMAIN}/account/invoice/statistic/{acct_id}",
    }
    if sub not in sub_map:
        die(f"不支持的客户子资源: {sub}。支持: contract/opportunity/order/payment-plan/payment-record/invoice 及对应的 -stat")
    if sub.endswith("-stat"):
        return api("GET", sub_map[sub])
    return api("POST", sub_map[sub], data=body)


def crm_contract_sub(sub: str, contract_id: str) -> str:
    """合同子资源统计"""
    if not sub or not contract_id:
        die("contract-sub 需要子资源和合同ID")
    if sub == "invoice-stat":
        return api("GET", f"{CORDYS_CRM_DOMAIN}/contract/invoice/statistic/{contract_id}")
    die(f"不支持的合同子资源: {sub}。支持: invoice-stat")


# ── 原始 API 调用 ─────────────────────────────────────────────────────
def raw_api(method: str, path: str, *args) -> str:
    """执行原始 API 调用"""
    if path.startswith("http"):
        # 验证URL域名
        if not validate_url(path):
            print("❌ 拒绝请求：目标域名与配置的Cordys CRM域名不匹配", file=sys.stderr)
            print(f"   配置的域名: {CORDYS_CRM_DOMAIN}", file=sys.stderr)
            print("   如需强制发送，请设置环境变量 CORDYS_ALLOW_UNTRUSTED=1", file=sys.stderr)
            
            if os.environ.get("CORDYS_ALLOW_UNTRUSTED", "0") != "1":
                sys.exit(1)
            else:
                warn("已启用不受信任域名模式，继续发送请求...")
        
        url = path
    else:
        url = f"{CORDYS_CRM_DOMAIN}{path}"

    # 这里简化处理，如果需要更多参数可以扩展
    return api(method, url)


# ── CLI 处理 ──────────────────────────────────────────────────────────
def print_usage():
    """打印使用帮助"""
    usage_text = """
cordys — CORDYS CRM CLI 工具（X-Access-Key 模式）

使用方法:
  cordys <命令> [参数...]

CRM 操作:
  crm view <模块> [参数]             列出视图记录
  crm get <模块> <ID>               获取单条记录详情
  crm search <模块> [关键词|JSON]    全局搜索记录
  crm page <模块> [关键词|JSON]      列表分页记录
  crm whoami                       获取当前登录用户信息
  crm verify                       验证 API 密钥是否有效
  crm org                          获取组织架构树
  crm members <部门IDs>             获取部门成员列表
  crm follow <plan|record> <模块> [关键词|JSON]  查询跟进计划或跟进记录
  crm product [关键词|JSON]          查询产品列表
  crm contact <模块> <ID>           获取联系人列表

统计与管道:
  crm stat <模块> [JSON]             模块金额统计（contract/opportunity/order/payment-record）
  crm stat-home <类型> [JSON]        首页统计（lead/opportunity/success/underway/dept-tree）
  crm glocount <关键词>              全局搜索各模块命中计数
  crm acct-sub <子资源> <客户ID> [JSON] 客户子资源（contract/opportunity/order/payment-plan等）
  crm contract-sub <子资源> <合同ID>  合同子资源统计（invoice-stat）

支持的 CRM 一级模块:
 [lead（线索）, opportunity（商机）, account（客户）,contact（联系人）,contract（合同）,order（订单）]

列表查询示例:
  cordys crm view lead
  cordys crm page lead
  cordys crm page lead "测试"
  cordys crm page lead '{"current":1,"pageSize":30,"sort":{},"combineSearch":{"searchMode":"AND","conditions":[]},"keyword":"","viewId":"ALL","filters":[]}'
  cordys crm page contract/payment-plan '{"current":1,"pageSize":30,"sort":{},"combineSearch":{"searchMode":"AND","conditions":[]},"keyword":"","viewId":"ALL","filters":[]}'
  cordys crm search account '{"current":1,"pageSize":30,"combineSearch":{"searchMode":"AND","conditions":[]},"keyword":"xyz","viewId":"ALL","filters":[]}'
  cordys crm org
  cordys crm members '{"current":1,"pageSize":30,"combineSearch":{"searchMode":"AND","conditions":[]},"keyword":"","departmentId":["deptId1","deptId2"],"filters":[]}'
  cordys crm follow plan lead '{"sourceId":"927627065163785","current":1,"pageSize":10,"keyword":"","status":"ALL","myPlan":false}'
  cordys crm follow record account '{"sourceId":"1751888184018919","current":1,"pageSize":10,"keyword":"","myPlan":false}'
  cordys crm product "测试"
  cordys crm contact account '927627065163785'

支持的 CRM 二级模块 :
  [contract/payment-plan(回款计划), invoice（发票）,contract/business-title(工商抬头）,contract/payment-record(回款记录), opportunity/quotation(报价单), order（订单）]

列表查询示例：
  cordys crm page contract/payment-plan
  cordys crm page contract/business-title

原始 API:
  raw <方法> <路径> [curl参数...]
  cordys raw GET /settings/fields?module=account

审批操作:
  cordys crm approval todo pending ['{"current":1,"pageSize":30}']
  cordys crm approval todo pending '{"resourceType":"CONTRACT"}'
  cordys crm approval todo count
  cordys crm approval action approve '{"resourceId":"xxx","remark":"同意"}'
  cordys crm approval action reject '{"resourceId":"xxx","remark":"驳回原因"}'
  cordys crm approval resource push '{"resourceId":"xxx"}'
  cordys crm approval resource detail RESOURCE_ID
  cordys crm approval flow list '{"current":1,"pageSize":30}'

审批 todo 类型: pending, processed, initiated, cc, count
审批 action 操作: approve, reject, back, sign, revoke, batch-approve, batch-reject
审批 resource 操作: push, revoke, simple-detail, detail
审批 flow 操作: list, get, add, update, delete, enable, disable, by-form, setting, webhook-test

环境变量要求:
  CORDYS_ACCESS_KEY
  CORDYS_SECRET_KEY
  CORDYS_CRM_DOMAIN

"""
    print(usage_text)


def handle_crm_command(args: list) -> None:
    """处理 CRM 命令"""
    if not args:
        die("crm 需要子命令")

    sub_cmd = args[0]
    rest_args = args[1:]

    if sub_cmd == "view":
        if not rest_args:
            die("view 需要指定模块")
        module = rest_args[0]
        opts = rest_args[1] if len(rest_args) > 1 else ""
        print(crm_view(module, opts))

    elif sub_cmd == "get":
        if len(rest_args) < 2:
            die("get 需要 <模块> <ID>")
        print(crm_get(rest_args[0], rest_args[1]))

    elif sub_cmd == "search":
        if not rest_args:
            die("search 需要指定模块")
        module = rest_args[0]
        json_data = rest_args[1] if len(rest_args) > 1 else ""
        print(crm_search(module, json_data))

    elif sub_cmd == "page":
        if not rest_args:
            die("page 需要指定模块")
        module = rest_args[0]
        payload = rest_args[1] if len(rest_args) > 1 else ""
        print(crm_page(module, payload))

    elif sub_cmd == "org":
        print(crm_org())

    elif sub_cmd == "product":
        keyword = rest_args[0] if rest_args else ""
        print(crm_product(keyword))

    elif sub_cmd == "whoami":
        print(crm_whoami())

    elif sub_cmd == "verify":
        print(crm_verify())

    elif sub_cmd == "members":
        if not rest_args:
            die("members 需要部门ID JSON")
        print(crm_members(rest_args[0]))

    elif sub_cmd == "contact":
        if len(rest_args) < 2:
            die("contact 需要 <模块> <ID>")
        print(crm_contact(rest_args[0], rest_args[1]))

    elif sub_cmd == "stat":
        if not rest_args:
            die("stat 需要指定模块")
        module = rest_args[0]
        payload = rest_args[1] if len(rest_args) > 1 else ""
        print(crm_stat(module, payload))

    elif sub_cmd == "stat-home":
        if not rest_args:
            die("stat-home 需要指定统计类型")
        kind = rest_args[0]
        payload = rest_args[1] if len(rest_args) > 1 else ""
        print(crm_stat_home(kind, payload))

    elif sub_cmd == "glocount":
        if not rest_args:
            die("glocount 需要关键词")
        print(crm_glocount(rest_args[0]))

    elif sub_cmd == "acct-sub":
        if len(rest_args) < 2:
            die("acct-sub 需要 <子资源> <客户ID>")
        sub = rest_args[0]
        acct_id = rest_args[1]
        payload = rest_args[2] if len(rest_args) > 2 else ""
        print(crm_acct_sub(sub, acct_id, payload))

    elif sub_cmd == "contract-sub":
        if len(rest_args) < 2:
            die("contract-sub 需要 <子资源> <合同ID>")
        print(crm_contract_sub(rest_args[0], rest_args[1]))

    elif sub_cmd == "follow":
        if not rest_args:
            die("follow 需要 plan 或 record")
        kind = rest_args[0]
        if kind not in ["plan", "record"]:
            die("follow 只支持 plan 或 record")
        if len(rest_args) < 2:
            die(f"follow {kind} 需要指定模块")
        module = rest_args[1]
        payload = rest_args[2] if len(rest_args) > 2 else ""
        print(crm_follow_page(kind, module, payload))

    elif sub_cmd == "approval":
        if not rest_args:
            die("approval 需要子命令")
        sub2 = rest_args[0]
        rest = rest_args[1:]
        if sub2 == "todo":
            kind = rest[0] if rest else ""
            payload = rest[1] if len(rest) > 1 else ""
            print(crm_approval_todo(kind, payload))
        elif sub2 == "action":
            action = rest[0] if rest else ""
            payload = rest[1] if len(rest) > 1 else ""
            print(crm_approval_action(action, payload))
        elif sub2 == "resource":
            action = rest[0] if rest else ""
            arg = rest[1] if len(rest) > 1 else ""
            print(crm_approval_resource(action, arg))
        elif sub2 == "flow":
            action = rest[0] if rest else ""
            arg = rest[1] if len(rest) > 1 else ""
            print(crm_approval_flow(action, arg))
        else:
            die(f"未知的 approval 子命令: {sub2}。支持: todo, action, resource, flow")

    else:
        die(f"未知的 crm 子命令: {sub_cmd}")


def handle_raw_command(args: list) -> None:
    """处理原始 API 命令"""
    if len(args) < 2:
        die("raw 需要 HTTP 方法和路径")

    method = args[0]
    path = args[1]
    print(raw_api(method, path))


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "crm":
        handle_crm_command(args)
    elif cmd == "raw":
        handle_raw_command(args)
    elif cmd in ["help", "-h", "--help"]:
        print_usage()
    else:
        die(f"未知命令: {cmd}（尝试 cordys.py help）")


if __name__ == "__main__":
    main()
