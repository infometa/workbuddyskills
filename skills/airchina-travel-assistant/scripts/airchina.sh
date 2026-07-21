#!/usr/bin/env bash
# =============================================================================
# 中国国航 B2C 移动应用对外服务接口 - 纯 Bash 客户端
# 基于《中国国航B2C移动应用对外服务接口规范 v1.0.0》实现
#
# 依赖：curl、openssl、jq、base64、awk（全部是类 Unix 系统标准命令）
# 零语言运行时，无 Python/Node 依赖
#
# 协议底座：accessToken 鉴权 + MD5 签名 + AES-128-ECB/PKCS5 加密 + adapter/procedure 分发
# 业务接口：send_sms_code、claim_coupon、invoke（通用）
# =============================================================================
# set -u 与 macOS 自带 bash 3.2 的 substring 扩展不兼容，用 -eo 即可
set -eo pipefail

# -----------------------------------------------------------------------------
# 硬编码配置（全部内置，无需任何外部环境变量；切换生产只需改 ENV_MODE）
# -----------------------------------------------------------------------------
# 国航签发给腾讯 WorkBuddy 的【生产】凭证
APP_ID="2NhdoyHXf41wWutaM5kULzAD"
SECRET_KEY="gXcWi1qzGUuo4KFOIASdCrE7"
# 渠道：国航分配给腾讯 WorkBuddy 的固定值
CHANNEL="TENCENT"
SUB_CHANNEL="OTA"
# 接口版本：文档 v1.0.0 的当前版本
SERVICE_VERSION="10100"
# 运行环境：生产。需要回测试时改 test（或临时用 AIRCHINA_ENV=test 覆盖）
ENV_MODE="${AIRCHINA_ENV:-prod}"
# 调试开关：1=打印中间值（也支持 AIRCHINA_DEBUG 临时覆盖）
DEBUG_MODE="${AIRCHINA_DEBUG:-0}"
# 网关地址
TEST_GATEWAY="https://m.airchina.com.cn:9066"
PROD_GATEWAY="https://m.airchina.com.cn"
AUTH_PATH="/airchina/gateway/ota/v2.0/auth/getAccessToken"
SERVICE_PATH="/airchina/gateway/ota/v2.0/api/services/"

case "$ENV_MODE" in
  test) GATEWAY="$TEST_GATEWAY" ;;
  prod) GATEWAY="$PROD_GATEWAY" ;;
  *)    echo "未知环境 ENV_MODE=$ENV_MODE（可选 test | prod）" >&2; exit 2 ;;
esac
AUTH_URL="${GATEWAY}${AUTH_PATH}"
SERVICE_URL="${GATEWAY}${SERVICE_PATH}"

# -----------------------------------------------------------------------------
# 本地文件路径
# -----------------------------------------------------------------------------
# accessToken 本地缓存（2 小时有效期，留 10 分钟缓冲）
TOKEN_CACHE_FILE="${TMPDIR:-/tmp}/airchina_token_${ENV_MODE}.json"
TOKEN_TTL=6600  # 110 分钟

# 已领券账本（跨进程持久化，供 check_claimed 使用）
CLAIMED_LEDGER_FILE="${TMPDIR:-/tmp}/airchina_claimed_ledger.json"

# -----------------------------------------------------------------------------
# 工具函数
# -----------------------------------------------------------------------------
die() { echo "[国航接口错误] $*" >&2; exit 1; }

require_cmd() {
  for c in "$@"; do
    command -v "$c" >/dev/null 2>&1 || die "缺少命令 $c，请先安装"
  done
}

# MD5：兼容 macOS(md5) 和 Linux(md5sum)；国航网关要求 **大写 hex**
md5_of() {
  local lower
  if command -v md5sum >/dev/null 2>&1; then
    lower=$(printf '%s' "$1" | md5sum | awk '{print $1}')
  else
    lower=$(printf '%s' "$1" | md5 -q)
  fi
  # 转大写（国航 MD5Util.Md5 返回大写）
  printf '%s' "$lower" | tr 'a-f' 'A-F'
}

# AES-128-ECB/PKCS5 加密，Base64 输出
# $1 = accessToken，$2 = 明文
aes_encrypt() {
  local token="$1" plain="$2"
  local key="${token:8:16}"
  [[ ${#key} -eq 16 ]] || die "accessToken 长度不足，无法截取 8~24 位生成 AES 密钥"
  local hex_key
  hex_key=$(printf '%s' "$key" | od -An -tx1 | tr -d ' \n')
  printf '%s' "$plain" | openssl enc -aes-128-ecb -nosalt -K "$hex_key" | base64 | tr -d '\n'
}

# AES-128-ECB/PKCS5 解密
# $1 = accessToken，$2 = Base64 密文
aes_decrypt() {
  local token="$1" cipher_b64="$2"
  local key="${token:8:16}"
  [[ ${#key} -eq 16 ]] || die "accessToken 长度不足，无法截取 8~24 位生成 AES 密钥"
  local hex_key
  hex_key=$(printf '%s' "$key" | od -An -tx1 | tr -d ' \n')
  printf '%s' "$cipher_b64" | base64 -d | openssl enc -d -aes-128-ecb -nosalt -K "$hex_key"
}

now_epoch() { date +%s; }

# 毫秒级时间戳：Linux 用 date +%s%3N，macOS 退回秒 * 1000
now_millis() {
  local t
  t=$(date +%s%3N 2>/dev/null || true)
  if [[ "$t" == *N* || -z "$t" ]]; then
    echo "$(($(date +%s) * 1000))"
  else
    echo "$t"
  fi
}

# -----------------------------------------------------------------------------
# 鉴权：获取 accessToken（带文件缓存）
# -----------------------------------------------------------------------------
get_access_token() {
  local force="${1:-}"
  if [[ "$force" != "--force" && -f "$TOKEN_CACHE_FILE" ]]; then
    local cached_token cached_at now
    cached_token=$(jq -r '.accessToken // empty' "$TOKEN_CACHE_FILE" 2>/dev/null || true)
    cached_at=$(jq -r '.cachedAt // 0' "$TOKEN_CACHE_FILE" 2>/dev/null || echo 0)
    now=$(now_epoch)
    if [[ -n "$cached_token" ]] && (( now - cached_at < TOKEN_TTL )); then
      echo "$cached_token"
      return 0
    fi
  fi

  local body resp security_code token
  body=$(curl -sS -X POST \
    --data-urlencode "appId=${APP_ID}" \
    --data-urlencode "secretKey=${SECRET_KEY}" \
    --data-urlencode "channel=${CHANNEL}" \
    --data-urlencode "subChannel=${SUB_CHANNEL}" \
    -G "$AUTH_URL" \
    -H "Content-Type: application/json")

  security_code=$(echo "$body" | jq -r '.securityCode // empty')
  token=$(echo "$body" | jq -r '.accessToken // empty')
  [[ "$security_code" == "0000" && -n "$token" ]] || die "获取 accessToken 失败：$body"

  jq -n --arg t "$token" --argjson at "$(now_epoch)" \
    '{accessToken:$t, cachedAt:$at}' > "$TOKEN_CACHE_FILE"
  chmod 600 "$TOKEN_CACHE_FILE" 2>/dev/null || true

  echo "$token"
}

# -----------------------------------------------------------------------------
# 签名：文档 3.3.2
# 输入：已经按需要拼好的 body kv pairs（name1=val1 name2=val2 ...，空格分隔）
# 输出：升序排序后 k=v&k=v 的 MD5
# -----------------------------------------------------------------------------
sign_body_params() {
  # 入参：多行 "k=v"
  # 输出：signString + stdout 输出 sorted_plain（给加密用）
  local sorted_plain
  sorted_plain=$(printf '%s\n' "$@" | LC_ALL=C sort | paste -sd '&' -)
  local sig
  sig=$(md5_of "$sorted_plain")
  # 用分隔符回传两个值
  printf '%s\t%s' "$sig" "$sorted_plain"
}

# -----------------------------------------------------------------------------
# 通用业务调用：invoke adapter procedure req_json [lang]
# 环境变量 AIRCHINA_DEBUG=1 时会把每一步中间值打到 stderr（不污染 stdout 的 JSON）
# -----------------------------------------------------------------------------
invoke_service() {
  local adapter="$1" procedure="$2" req_json="$3" lang="${4:-zh_CN}"
  local token
  token=$(get_access_token)

  local timestamp
  timestamp=$(now_millis)

  # 压缩 req_json（去空白，防止签名/加密前后空白差异）
  local req_compact
  req_compact=$(echo "$req_json" | jq -c .)

  # 组 body 三件套
  local pair_lang="lang=${lang}"
  local pair_req="req=${req_compact}"
  local pair_ts="timestamp=${timestamp}"

  # 签名：按 key 升序
  local sig_out sig_string sorted_plain
  sig_out=$(sign_body_params "$pair_lang" "$pair_req" "$pair_ts")
  sig_string=$(printf '%s' "$sig_out" | cut -f1)
  sorted_plain=$(printf '%s' "$sig_out" | cut -f2-)

  # AES 加密
  local encrypted_body aes_key hex_key
  encrypted_body=$(aes_encrypt "$token" "$sorted_plain")
  aes_key="${token:8:16}"
  hex_key=$(printf '%s' "$aes_key" | od -An -tx1 | tr -d ' \n')

  # 调试模式：打出全部中间值（走 stderr，不干扰正常 stdout）
  if [[ "${DEBUG_MODE}" == "1" ]]; then
    {
      echo "================ AIRCHINA DEBUG ================"
      echo "adapter          = $adapter"
      echo "procedure        = $procedure"
      echo "serviceVersion   = $SERVICE_VERSION"
      echo "accessToken      = $token"
      echo "AES key (plain)  = $aes_key   (accessToken[8:24], 16 bytes)"
      echo "AES key (hex)    = $hex_key"
      echo "AES mode         = AES/ECB/PKCS5Padding, no salt"
      echo "body plain       = $sorted_plain"
      echo "signString (MD5) = $sig_string"
      echo "body cipher (b64)= $encrypted_body"
      echo "URL              = $SERVICE_URL"
      echo "================================================"
    } >&2
  fi

  # 发请求
  local http_resp
  http_resp=$(curl -sS -X POST "$SERVICE_URL" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "channel: ${CHANNEL}" \
    -H "subChannel: ${SUB_CHANNEL}" \
    -H "appId: ${APP_ID}" \
    -H "accessToken: ${token}" \
    -H "signString: ${sig_string}" \
    -H "adapter: ${adapter}" \
    -H "procedure: ${procedure}" \
    -H "serviceVersion: ${SERVICE_VERSION}" \
    --data-raw "$encrypted_body")

  if [[ "${DEBUG_MODE}" == "1" ]]; then
    echo "gateway response = $http_resp" >&2
    echo "================================================" >&2
  fi

  # 校验网关层
  local gw_code
  gw_code=$(echo "$http_resp" | jq -r '.securityCode // empty')
  if [[ "$gw_code" != "0000" ]]; then
    die "网关返回错误：$http_resp"
  fi

  # 解密 resp
  local enc_resp decrypted
  enc_resp=$(echo "$http_resp" | jq -r '.resp // empty')
  if [[ -z "$enc_resp" ]]; then
    echo "$http_resp"
    return 0
  fi

  decrypted=$(aes_decrypt "$token" "$enc_resp")
  # 国航响应的 resp 解密后是 URL-encoded JSON，需要 URL-decode 还原
  # 用 awk 纯文本 URL-decode，避免引入 python/perl 依赖
  decrypted=$(printf '%s' "$decrypted" | awk '
    BEGIN {
      for (i=0;i<256;i++) chr[sprintf("%02X",i)] = sprintf("%c",i)
      for (i=0;i<256;i++) chr[sprintf("%02x",i)] = sprintf("%c",i)
    }
    {
      out = ""; n = length($0); i = 1
      while (i <= n) {
        c = substr($0, i, 1)
        if (c == "%" && i+2 <= n) { out = out chr[substr($0, i+1, 2)]; i += 3 }
        else if (c == "+") { out = out " "; i++ }
        else { out = out c; i++ }
      }
      print out
    }
  ')
  # 拼回外层 envelope
  echo "$http_resp" | jq --argjson r "$decrypted" '.resp = $r'
}

# -----------------------------------------------------------------------------
# 业务方法
# -----------------------------------------------------------------------------
cmd_send_sms_code() {
  local phone="" area_code="86"
  while (( $# > 0 )); do
    case "$1" in
      --phone) phone="$2"; shift 2 ;;
      --area-code) area_code="$2"; shift 2 ;;
      *) die "未知参数：$1" ;;
    esac
  done
  [[ -n "$phone" ]] || die "缺少 --phone"

  local req_json
  req_json=$(jq -n --arg p "$phone" --arg a "$area_code" '{phone:$p, areaCode:$a}')
  local envelope resp_obj code
  envelope=$(invoke_service "ACOTADigitalProducts" "sendSMSVeriCodeActivity" "$req_json")
  resp_obj=$(echo "$envelope" | jq '.resp')
  code=$(echo "$resp_obj" | jq -r '.code // empty')
  [[ "$code" == "0" ]] || die "发送短信失败：$resp_obj"
  echo "$resp_obj"
}

cmd_claim_coupon() {
  local phone="" area_code="86" veri_code=""
  while (( $# > 0 )); do
    case "$1" in
      --phone) phone="$2"; shift 2 ;;
      --area-code) area_code="$2"; shift 2 ;;
      --veri-code) veri_code="$2"; shift 2 ;;
      *) die "未知参数：$1" ;;
    esac
  done
  [[ -n "$phone" && -n "$veri_code" ]] || die "缺少 --phone 或 --veri-code"

  local req_json
  req_json=$(jq -n --arg m "$phone" --arg a "$area_code" --arg v "$veri_code" \
    '{mobileNo:$m, areaCode:$a, veriCode:$v}')
  local envelope resp_obj code
  envelope=$(invoke_service "ACOTADigitalProducts" "tencentClaimCoupon" "$req_json")
  resp_obj=$(echo "$envelope" | jq '.resp')
  code=$(echo "$resp_obj" | jq -r '.code // empty')
  [[ "$code" == "00000000" ]] || die "领券失败：$resp_obj"

  # 领券成功后写入本地账本，供下次 check_claimed 使用
  ledger_record_claim "$phone" "$area_code" "tencentClaimCoupon" "$resp_obj"

  echo "$resp_obj"
}

# -----------------------------------------------------------------------------
# 本地已领券账本
# 目的：用户再次来领时，在问验证码之前就能查出"已领过"，不骚扰用户
# 文件位置：$CLAIMED_LEDGER_FILE
# 键：      {areaCode}-{phone}（如 86-13761808559）
# 值：      { activity, claimed_at, coupons[] }
# -----------------------------------------------------------------------------

# 初始化账本文件（不存在则建空 JSON 对象）
ledger_init() {
  if [[ ! -f "$CLAIMED_LEDGER_FILE" ]]; then
    echo '{}' > "$CLAIMED_LEDGER_FILE"
    chmod 600 "$CLAIMED_LEDGER_FILE" 2>/dev/null || true
  fi
}

# 记录一次成功领券
# $1 = phone, $2 = areaCode, $3 = activity (procedure 名), $4 = resp_obj (包含 couponList)
ledger_record_claim() {
  local phone="$1" area_code="$2" activity="$3" resp_obj="$4"
  ledger_init
  local key="${area_code}-${phone}"
  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%S+00:00")

  # 用 jq 原子更新：读入 + 修改 + 写回
  local coupons_json
  coupons_json=$(echo "$resp_obj" | jq '.couponList // []')
  local new_entry
  new_entry=$(jq -n --arg a "$activity" --arg t "$now" --argjson c "$coupons_json" \
    '{activity:$a, claimed_at:$t, coupons:$c}')

  local tmp="${CLAIMED_LEDGER_FILE}.tmp.$$"
  jq --arg k "$key" --argjson e "$new_entry" '.[$k] = $e' \
    "$CLAIMED_LEDGER_FILE" > "$tmp" && mv "$tmp" "$CLAIMED_LEDGER_FILE"
}

# 查询某手机号是否已领过某活动
# $1 = phone, $2 = areaCode, $3 = activity（默认 tencentClaimCoupon）
# 输出：未领过时输出 null；已领过时输出 JSON { activity, claimed_at, coupons }
cmd_check_claimed() {
  local phone="" area_code="86" activity="tencentClaimCoupon"
  while (( $# > 0 )); do
    case "$1" in
      --phone) phone="$2"; shift 2 ;;
      --area-code) area_code="$2"; shift 2 ;;
      --activity) activity="$2"; shift 2 ;;
      *) die "未知参数：$1" ;;
    esac
  done
  [[ -n "$phone" ]] || die "缺少 --phone"
  ledger_init
  local key="${area_code}-${phone}"
  jq --arg k "$key" --arg a "$activity" \
    'if .[$k] and .[$k].activity == $a then .[$k] else null end' \
    "$CLAIMED_LEDGER_FILE"
}

# 查看整个账本（调试用）
cmd_ledger_show() {
  ledger_init
  jq . "$CLAIMED_LEDGER_FILE"
}

# 清空账本（测试用）
cmd_ledger_clear() {
  echo '{}' > "$CLAIMED_LEDGER_FILE"
  chmod 600 "$CLAIMED_LEDGER_FILE" 2>/dev/null || true
  echo "账本已清空：$CLAIMED_LEDGER_FILE"
}

cmd_invoke() {
  local adapter="" procedure="" req="" lang="zh_CN"
  while (( $# > 0 )); do
    case "$1" in
      --adapter) adapter="$2"; shift 2 ;;
      --procedure) procedure="$2"; shift 2 ;;
      --req) req="$2"; shift 2 ;;
      --lang) lang="$2"; shift 2 ;;
      *) die "未知参数：$1" ;;
    esac
  done
  [[ -n "$adapter" && -n "$procedure" && -n "$req" ]] || die "缺少 --adapter / --procedure / --req"
  invoke_service "$adapter" "$procedure" "$req" "$lang"
}

cmd_check_env() {
  echo "—— 硬编码配置（全部内置，无需任何环境变量）——"
  echo "  appId           = $APP_ID"
  echo "  secretKey       = ${SECRET_KEY:0:8}... (长度 ${#SECRET_KEY})"
  echo "  channel         = $CHANNEL"
  echo "  subChannel      = $SUB_CHANNEL"
  echo "  serviceVersion  = $SERVICE_VERSION"
  echo "  运行环境        = $ENV_MODE → $GATEWAY"
  echo "  调试模式        = $DEBUG_MODE"
  echo ""
  echo "—— 可临时覆盖的环境变量（可选）——"
  echo "  AIRCHINA_ENV=prod     切换到生产环境"
  echo "  AIRCHINA_DEBUG=1      打印中间值便于对账"
}

# -----------------------------------------------------------------------------
# 主入口
# -----------------------------------------------------------------------------
usage() {
  cat <<EOF
用法（所有配置已硬编码，无需任何环境变量即可运行）：
  $(basename "$0") check-env
  $(basename "$0") get-token [--force]
  $(basename "$0") send_sms_code --phone <手机号> [--area-code 86]
  $(basename "$0") claim_coupon --phone <手机号> --veri-code <验证码> [--area-code 86]
  $(basename "$0") invoke --adapter <adapter> --procedure <procedure> --req <JSON> [--lang zh_CN]

已领券账本（本地缓存，避免用户重复领同一活动）：
  $(basename "$0") check_claimed --phone <手机号> [--area-code 86] [--activity tencentClaimCoupon]
      未领过 → 输出 null；已领过 → 输出 JSON（含 claimed_at + coupons 列表）
  $(basename "$0") ledger_show
  $(basename "$0") ledger_clear

可选环境变量（仅用于临时覆盖）：
  AIRCHINA_ENV=prod      切换到生产环境（默认 test）
  AIRCHINA_DEBUG=1       打印中间值便于对账

依赖命令：curl openssl jq base64 awk od
EOF
}

main() {
  require_cmd curl openssl jq base64 awk od
  local cmd="${1:-}"
  [[ -n "$cmd" ]] || { usage; exit 1; }
  shift

  case "$cmd" in
    check-env)      cmd_check_env ;;
    get-token)      get_access_token "${1:-}" ;;
    send_sms_code)  cmd_send_sms_code "$@" ;;
    claim_coupon)   cmd_claim_coupon "$@" ;;
    invoke)         cmd_invoke "$@" ;;
    check_claimed)  cmd_check_claimed "$@" ;;
    ledger_show)    cmd_ledger_show ;;
    ledger_clear)   cmd_ledger_clear ;;
    -h|--help|help) usage ;;
    *)              echo "未知子命令：$cmd" >&2; usage; exit 1 ;;
  esac
}

main "$@"
