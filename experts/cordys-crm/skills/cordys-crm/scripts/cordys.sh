#!/usr/bin/env bash
# CORDYS CRM CLI 工具
# 使用 X-Access-Key / X-Secret-Key 进行鉴权
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${SKILL_DIR}/.env"

# ── 加载环境变量 ──────────────────────────────────────────────────────
if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

CORDYS_CRM_DOMAIN="${CORDYS_CRM_DOMAIN:-https://www.cordys.cn}"

# ── 辅助函数 ───────────────────────────────────────────────────────────
die()  { echo "错误: $*" >&2; exit 1; }
info() { echo ":: $*" >&2; }
warn() { echo "⚠️  警告: $*" >&2; }

check_keys() {
  [[ -n "${CORDYS_ACCESS_KEY:-}" ]] || die "未设置 CORDYS_ACCESS_KEY"
  [[ -n "${CORDYS_SECRET_KEY:-}" ]] || die "未设置 CORDYS_SECRET_KEY"
}

# 验证URL是否指向可信的Cordys CRM域名
validate_url() {
  local url="$1"

  local domain
  if [[ "$url" =~ ^https?://([^/]+) ]]; then
    domain="${BASH_REMATCH[1]}"
  else
    return 0
  fi

  local trusted_domain
  if [[ "$CORDYS_CRM_DOMAIN" =~ ^https?://([^/]+) ]]; then
    trusted_domain="${BASH_REMATCH[1]}"
  else
    trusted_domain="$CORDYS_CRM_DOMAIN"
  fi

  if [[ "$domain" != "$trusted_domain" ]] && [[ "$domain" != *".$trusted_domain" ]]; then
    warn "目标域名 '$domain' 与配置的Cordys CRM域名 '$trusted_domain' 不匹配"
    warn "这可能会泄露您的API凭证！"
    return 1
  fi
  return 0
}

page_payload() {
  local keyword="${1:-}"
  python3 - "$keyword" <<'PY'
import json, sys
keyword = sys.argv[1] if len(sys.argv) > 1 else ""
payload = {
  "current": 1,
  "pageSize": 30,
  "sort": {},
  "combineSearch": {"searchMode": "AND", "conditions": []},
  "keyword": keyword,
  "viewId": "ALL",
  "filters": []
}
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps(payload, ensure_ascii=False))
PY
}

# 合并用户 JSON 到默认 payload，确保 current 和 pageSize 始终存在
merge_payload() {
  local user_json="${1:-}"
  python3 - "$user_json" <<'PY'
import json, sys

raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
  user = json.loads(raw) if raw and raw.strip() else {}
except json.JSONDecodeError:
  # 不是合法 JSON，当作 keyword 处理
  user = {"keyword": raw}

default = {
  "current": 1,
  "pageSize": 30,
  "sort": {},
  "combineSearch": {"searchMode": "AND", "conditions": []},
  "keyword": "",
  "viewId": "ALL",
  "filters": []
}

merged = {**default, **user}
# 确保 current 和 pageSize 有值（即使用户传了无效值）
if not isinstance(merged.get("current"), int) or merged["current"] < 1:
  merged["current"] = 1
if not isinstance(merged.get("pageSize"), int) or merged["pageSize"] < 1:
  merged["pageSize"] = 30

sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps(merged, ensure_ascii=False))
PY
}

# ── API 封装（Header Key 鉴权）────────────────────────────────────────
api_request() {
  local method="$1" url="$2" content_type="$3"
  shift 3
  check_keys
  curl -s -X "$method" "$url" \
    -H "X-Access-Key: ${CORDYS_ACCESS_KEY}" \
    -H "X-Secret-Key: ${CORDYS_SECRET_KEY}" \
    -H "X-Request-Source: SKILL" \
    -H "Content-Type: $content_type; charset=utf-8" \
    "$@"
}

api() {
  api_request "$1" "$2" "application/json" "${@:3}"
}

api_form() {
  api_request "$1" "$2" "application/x-www-form-urlencoded" "${@:3}"
}

# ── CRM 辅助函数 ──────────────────────────────────────────────────────
crm_base="${CORDYS_CRM_DOMAIN}"

crm_view() {
  local module="$1" opts="${2:-}"
  api GET "${crm_base}/${module}/view/list" $opts
}

crm_get() {
  local module="$1" id="$2"
  api GET "${crm_base}/${module}/${id}"
}

crm_contact() {
  local module="$1" id="$2"
  api GET "${crm_base}/${module}/contact/list/${id}"
}

crm_page() {
  local module="$1"
  shift
  local first="${1:-}"
  local body
  if [[ "$first" == \{* ]]; then
    body=$(merge_payload "$first")
  else
    body=$(page_payload "${first:-}")
  fi
  local path="${module}/page"
  api POST "${CORDYS_CRM_DOMAIN}/${path}" --data-binary "$body"
}

crm_search() {
  local module="$1" json="${2:-}"
  local body
  if [[ "$json" == \{* ]]; then
    body=$(merge_payload "$json")
  else
    body=$(page_payload "${json}")
  fi
  local path="global/search/${module}"
  api POST "${CORDYS_CRM_DOMAIN}/${path}" --data-binary "$body"
}

crm_follow_page() {
  local kind="$1" module="$2" payload="${3:-}"
  [[ "${kind}" == "plan" || "${kind}" == "record" ]] || die "follow 子命令只支持 plan/record"
  [[ -n "${module}" ]] || die "follow ${kind} 需要指定模块（lead/account 等）"
  local body
  if [[ "${payload}" == \{* ]]; then
    body="${payload}"
  else
    body=$(page_payload "${payload}")
  fi
  api POST "${crm_base}/${module}/follow/${kind}/page" --data-binary "$body"
}

# ── 审批相关 ──────────────────────────────────────────────────────────

crm_approval_todo() {
  local kind="$1" payload="${2:-}"
  local body
  if [[ "${payload}" == \{* ]]; then
    body=$(merge_payload "${payload}")
  else
    body=$(page_payload "${payload}")
  fi
  case "${kind}" in
    pending)   api POST "${crm_base}/approval-todo/pending/page" --data-binary "$body" ;;
    processed) api POST "${crm_base}/approval-todo/processed/page" --data-binary "$body" ;;
    initiated) api POST "${crm_base}/approval-todo/initiated/page" --data-binary "$body" ;;
    cc)        api POST "${crm_base}/approval-todo/cc/page" --data-binary "$body" ;;
    count)     api GET "${crm_base}/approval-todo/pending/count" ;;
    *) die "未知的审批代办类型: ${kind}。支持: pending, processed, initiated, cc, count" ;;
  esac
}

crm_approval_action() {
  local action="$1" payload="${2:-}"
  [[ -n "${payload}" && "${payload}" == \{* ]] || die "${action} 需要 JSON body"
  case "${action}" in
    approve)       api POST "${crm_base}/approval-action/approve" --data-binary "$payload" ;;
    reject)        api POST "${crm_base}/approval-action/reject" --data-binary "$payload" ;;
    back)          api POST "${crm_base}/approval-action/back" --data-binary "$payload" ;;
    sign)          api POST "${crm_base}/approval-action/sign" --data-binary "$payload" ;;
    revoke)        api POST "${crm_base}/approval-action/revoke" --data-binary "$payload" ;;
    batch-approve) api POST "${crm_base}/approval-action/batch-approve" --data-binary "$payload" ;;
    batch-reject)  api POST "${crm_base}/approval-action/batch-reject" --data-binary "$payload" ;;
    *) die "未知的审批操作: ${action}。支持: approve, reject, back, sign, revoke, batch-approve, batch-reject" ;;
  esac
}

crm_approval_resource() {
  local action="$1"
  shift
  case "${action}" in
    push)          api POST "${crm_base}/approval-resource/push" --data-binary "$1" ;;
    revoke)        api POST "${crm_base}/approval-resource/revoke" --data-binary "$1" ;;
    simple-detail) api GET "${crm_base}/approval-resource/simple-detail/$1" ;;
    detail)        api GET "${crm_base}/approval-resource/detail/$1" ;;
    *) die "未知的审批资源操作: ${action}。支持: push, revoke, simple-detail, detail" ;;
  esac
}

crm_approval_flow() {
  local action="$1"
  shift
  case "${action}" in
    list)         api POST "${crm_base}/approval-flow/page" --data-binary "$1" ;;
    get)          api GET "${crm_base}/approval-flow/get/$1" ;;
    add)          api POST "${crm_base}/approval-flow/add" --data-binary "$1" ;;
    update)       api POST "${crm_base}/approval-flow/update" --data-binary "$1" ;;
    delete)       api GET "${crm_base}/approval-flow/delete/$1" ;;
    enable)       api GET "${crm_base}/approval-flow/enable/$1?enable=true" ;;
    disable)      api GET "${crm_base}/approval-flow/enable/$1?enable=false" ;;
    by-form)      api GET "${crm_base}/approval-flow/get-by-form-type/$1" ;;
    setting)      api GET "${crm_base}/approval-flow/status-permission/setting/$1" ;;
    webhook-test) api POST "${crm_base}/approval-flow/webhook/test" --data-binary "$1" ;;
    *) die "未知的审批流操作: ${action}" ;;
  esac
}

# ── 产品 ──────────────────────────────────────────────────────────────
crm_product() {
  local keyword="${1:-}"
  local body
  if [[ "$keyword" == \{* ]]; then
    body="$keyword"
  else
    body=$(page_payload "${keyword}")
  fi
  api POST "${CORDYS_CRM_DOMAIN}/field/source/product" --data-binary "$body"
}

# ── 用户与组织 ─────────────────────────────────────────────────────────
crm_whoami() {
  api GET "${crm_base}/personal/center/info"
}

crm_verify() {
  local result
  result=$(crm_whoami 2>&1) || {
    echo "{\"status\":\"error\",\"message\":\"API密钥验证失败\",\"detail\":\"$result\"}"
    return 1
  }
  echo "$result"
}

crm_org() {
  api GET "${crm_base}/department/tree"
}

crm_members() {
  api POST "${crm_base}/user/list" --data-binary "$1"
}

# ── 统计 API ──────────────────────────────────────────────────────────
crm_stat() {
  local module="$1" payload="${2:-}"
  local body
  if [[ "${payload}" == \{* ]]; then
    body=$(merge_payload "$payload")
  else
    body=$(page_payload "${payload}")
  fi
  case "${module}" in
    contract)                  api POST "${crm_base}/contract/statistic" --data-binary "$body" ;;
    contract/payment-record)   api POST "${crm_base}/contract/payment-record/statistic" --data-binary "$body" ;;
    opportunity)               api POST "${crm_base}/opportunity/statistic" --data-binary "$body" ;;
    order)                     api POST "${crm_base}/order/statistic" --data-binary "$body" ;;
    *) die "不支持的统计模块: ${module}。支持: contract, contract/payment-record, opportunity, order" ;;
  esac
}

crm_stat_home() {
  local kind="$1" payload="${2:-}"
  local body
  if [[ "${payload}" == \{* ]]; then
    body="${payload}"
  else
    body='{"searchType":"SELF","timeField":"CREATE_TIME","userField":"OWNER","priorPeriodEnable":true}'
  fi
  case "${kind}" in
    lead)                   api POST "${crm_base}/home/statistic/lead" --data-binary "$body" ;;
    opportunity)            api POST "${crm_base}/home/statistic/opportunity" --data-binary "$body" ;;
    opportunity/success)    api POST "${crm_base}/home/statistic/opportunity/success" --data-binary "$body" ;;
    opportunity/underway)   api POST "${crm_base}/home/statistic/opportunity/underway" --data-binary "$body" ;;
    dept-tree)              api GET "${crm_base}/home/statistic/department/tree" ;;
    *) die "不支持的首頁统计类型: ${kind}。支持: lead, opportunity, opportunity/success, opportunity/underway, dept-tree" ;;
  esac
}

# ── 全局搜索计数 ─────────────────────────────────────────────────────
crm_glocount() {
  local keyword="$1"
  [[ -n "${keyword}" ]] || die "glocount 需要关键词"
  api GET "${crm_base}/global/search/module/count?keyword=${keyword}"
}

# ── 客户子资源 ──────────────────────────────────────────────────────
crm_acct_sub() {
  local sub="$1" acct_id="$2" payload="${3:-}"
  [[ -n "${sub}" && -n "${acct_id}" ]] || die "acct-sub 需要子资源和客户ID"
  local body
  if [[ "${payload}" == \{* ]]; then
    body=$(merge_payload "$payload")
  else
    body=$(page_payload "${payload}")
  fi
  case "${sub}" in
    contract)           api POST "${crm_base}/account/contract/page" --data-binary "$body" ;;
    contract-stat)      api GET "${crm_base}/account/contract/statistic/${acct_id}" ;;
    opportunity)        api POST "${crm_base}/account/opportunity/page" --data-binary "$body" ;;
    order)              api POST "${crm_base}/account/order/page" --data-binary "$body" ;;
    payment-plan)       api POST "${crm_base}/account/contract/payment-plan/page" --data-binary "$body" ;;
    payment-plan-stat)  api GET "${crm_base}/account/contract/payment-plan/statistic/${acct_id}" ;;
    payment-record)     api POST "${crm_base}/account/contract/payment-record/page" --data-binary "$body" ;;
    payment-record-stat) api GET "${crm_base}/account/contract/payment-record/statistic/${acct_id}" ;;
    invoice)            api POST "${crm_base}/account/invoice/page" --data-binary "$body" ;;
    invoice-stat)       api GET "${crm_base}/account/invoice/statistic/${acct_id}" ;;
    *) die "不支持的客户子资源: ${sub}。支持: contract/opportunity/order/payment-plan/payment-record/invoice 及对应的 -stat" ;;
  esac
}

# ── 合同子资源统计 ──────────────────────────────────────────────────
crm_contract_sub() {
  local sub="$1" contract_id="$2"
  [[ -n "${sub}" && -n "${contract_id}" ]] || die "contract-sub 需要子资源和合同ID"
  case "${sub}" in
    invoice-stat) api GET "${crm_base}/contract/invoice/statistic/${contract_id}" ;;
    *) die "不支持的合同子资源: ${sub}。支持: invoice-stat" ;;
  esac
}

# ── 原始 API 调用 ─────────────────────────────────────────────────────
raw_api() {
  local method="$1" path="$2"
  shift 2

  if [[ "$path" == http* ]]; then
    if ! validate_url "$path"; then
      echo "❌ 拒绝请求：目标域名与配置的Cordys CRM域名不匹配" >&2
      echo "   配置的域名: $CORDYS_CRM_DOMAIN" >&2
      if [[ "${CORDYS_ALLOW_UNTRUSTED:-0}" != "1" ]]; then
        exit 1
      else
        warn "已启用不受信任域名模式，继续发送请求..."
      fi
    fi
    api "$method" "$path" "$@"
  else
    api "$method" "${CORDYS_CRM_DOMAIN}${path}" "$@"
  fi
}

# ── CLI 分发 ──────────────────────────────────────────────────────────
usage() {
  cat <<'EOF'
cordys — CORDYS CRM CLI 工具（X-Access-Key 模式）

使用方法:
  cordys <命令> [参数...]

CRM 数据操作:
  crm view <模块> [参数]                   列出视图记录
  crm get <模块> <ID>                     获取单条记录详情
  crm search <模块> [关键词|JSON]          全局搜索记录
  crm page <模块> [关键词|JSON]            列表分页记录
  crm follow <plan|record> <模块> [JSON]   查询跟进计划/记录
  crm product [关键词|JSON]               查询产品列表
  crm contact <模块> <ID>                 获取联系人列表

统计与管道:
  crm stat <模块> [JSON]                  模块金额统计（contract/opportunity/order/payment-record）
  crm stat-home <类型> [JSON]             首页统计（lead/opportunity/success/underway/dept-tree）
  crm glocount <关键词>                   全局搜索各模块命中计数
  crm acct-sub <子资源> <客户ID> [JSON]    客户子资源（contract/opportunity/order/payment-plan等）
  crm contract-sub <子资源> <合同ID>       合同子资源统计（invoice-stat）

用户与组织:
  crm whoami                              获取当前用户信息
  crm verify                              验证 API 密钥
  crm org                                 获取组织架构树
  crm members <JSON>                      获取部门成员列表

审批操作:
  crm approval todo <类型> [JSON]          审批代办列表
  crm approval action <操作> <JSON>        审批操作（同意/驳回/退回/加签/撤回）
  crm approval resource <操作> [参数]       审批资源（提审/撤销/详情）
  crm approval flow <操作> [参数]          审批流管理

模块列表:
  lead（线索）, opportunity（商机）, account（客户）,
  contact（联系人）, contract（合同）,
  contract/payment-plan（回款计划）, invoice（发票）,
  contract/business-title（工商抬头）, contract/payment-record（回款记录）,
  opportunity/quotation（报价单）, order（订单）

审批 todo 类型: pending（待审）, processed（已处理）, initiated（我发起的）, cc（抄送我）, count（统计）
审批 action 操作: approve（同意）, reject（驳回）, back（退回）, sign（加签）, revoke（撤回）, batch-approve（批量同意）, batch-reject（批量驳回）
审批 resource 操作: push（提审）, revoke（撤销）, simple-detail（列表详情）, detail（记录详情）
审批 flow 操作: list（列表）, get（详情）, add（新建）, update（更新）, delete（删除）, enable（启用）, disable（禁用）, by-form（按表单类型）, setting（状态权限）, webhook-test（测试webhook）

示例:
  cordys crm approval todo pending '{"current":1,"pageSize":30}'
  cordys crm approval todo pending '{"resourceType":"CONTRACT"}'
  cordys crm approval todo pending '{"combineSearch":{"conditions":[{"value":"2026-05-01","operator":"GT","name":"createTime","type":"DATE_TIME"}]}}'
  cordys crm approval todo count
  cordys crm approval action approve '{"resourceId":"xxx","remark":"同意"}'
  cordys crm approval action reject '{"resourceId":"xxx","remark":"驳回原因"}'
  cordys crm approval resource push '{"resourceId":"xxx"}'
  cordys crm approval flow list '{"current":1,"pageSize":30}'

原始 API:
  raw <方法> <路径> [curl参数...]
  cordys raw GET /approval-todo/pending/count

环境变量:
  CORDYS_ACCESS_KEY  CORDYS_SECRET_KEY  CORDYS_CRM_DOMAIN
EOF
}

cmd="${1:-}"
shift || true

case "$cmd" in
  crm)
    sub="${1:-}"; shift || die "crm 需要子命令"
    case "$sub" in
      view)    crm_view "$@" ;;
      get)     crm_get "$@" ;;
      search)  crm_search "$@" ;;
      page)    crm_page "$@" ;;
      whoami)  crm_whoami ;;
      verify)  crm_verify ;;
      org)     crm_org ;;
      product) crm_product "$@" ;;
      members) crm_members "$@" ;;
      contact) crm_contact "$@" ;;
      stat) crm_stat "$@" ;;
      stat-home) crm_stat_home "$@" ;;
      glocount) crm_glocount "$@" ;;
      acct-sub) crm_acct_sub "$@" ;;
      contract-sub) crm_contract_sub "$@" ;;
      follow)
        kind="${1:-}"; shift || die "follow 需要 plan 或 record"
        case "${kind}" in
          plan|record) crm_follow_page "${kind}" "$@" ;;
          *) die "follow 只支持 plan 或 record" ;;
        esac
        ;;
      approval)
        sub2="${1:-}"; shift || die "approval 需要子命令"
        case "${sub2}" in
          todo)     crm_approval_todo "$@" ;;
          action)   crm_approval_action "$@" ;;
          resource) crm_approval_resource "$@" ;;
          flow)     crm_approval_flow "$@" ;;
          *) die "未知的 approval 子命令: ${sub2}。支持: todo, action, resource, flow" ;;
        esac
        ;;
      *) die "未知的 crm 子命令: $sub" ;;
    esac
    ;;
  raw)
    method="${1:-}"; shift || die "raw 需要 HTTP 方法"
    path="${1:-}"; shift || die "raw 需要路径"
    raw_api "$method" "$path" "$@"
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    die "未知命令: $cmd（尝试 cordys help）"
    ;;
esac
