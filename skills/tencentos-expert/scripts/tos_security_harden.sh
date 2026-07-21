#!/bin/bash
###############################################################################
# TencentOS Server 等保三级安全加固脚本
# 版本: 2.0.0
# 适用系统: TencentOS Server 3 / TencentOS Server 4
# 功能: 支持 check（合规检查）和 harden（安全加固）两种模式
# 风险分级: R1（高风险-必须执行）、R2（中风险-建议执行）、R3（低风险-可选执行）
###############################################################################

set -o pipefail

# ============================================================================
# 全局变量
# ============================================================================
VERSION="2.0.0"
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/var/log/tos_security_harden_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="/var/backup/security_harden_$(date +%Y%m%d_%H%M%S)"

# 模式: check / harden
MODE=""
# 风险等级过滤: R1 R2 R3 ALL
RISK_LEVEL="ALL"
# 指定检查项（逗号分隔）
SPECIFIED_ITEMS=""
# 排除检查项（逗号分隔）
EXCLUDED_ITEMS=""
# 是否静默模式
QUIET=0

# 统计计数器
TOTAL=0
PASS=0
FAIL=0
CHANGED=0
SKIP=0
ERROR=0

# 颜色定义
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
CYAN="\033[36m"
NC="\033[0m"

# ============================================================================
# 工具函数
# ============================================================================

usage() {
    cat <<EOF
用法: $SCRIPT_NAME <MODE> [OPTIONS]

模式:
  check       合规检查模式（仅检查不修改）
  harden      安全加固模式（检查并修复不合规项）

选项:
  -l, --level <R1|R2|R3|ALL>   按风险等级过滤（默认: ALL）
  -i, --items <ID1,ID2,...>    指定执行的检查项编号
  -e, --exclude <ID1,ID2,...>  排除指定的检查项编号
  -q, --quiet                  静默模式（仅输出结果摘要）
  -h, --help                   显示帮助信息
  -v, --version                显示版本信息

风险等级说明:
  R1 - 高风险（必须执行）：如密码策略、SSH安全、审计日志等
  R2 - 中风险（建议执行）：如网络参数加固、服务关闭等
  R3 - 低风险（可选执行）：如Banner配置、文件权限细化等

示例:
  $SCRIPT_NAME check                       # 检查全部项
  $SCRIPT_NAME check -l R1                 # 仅检查R1级别项
  $SCRIPT_NAME harden -l R1               # 仅加固R1级别项
  $SCRIPT_NAME check -i 1.1,1.2,2.1       # 检查指定项
  $SCRIPT_NAME harden -e 2.8,4.5,4.6      # 加固全部但排除高风险项
  $SCRIPT_NAME harden -l R2 -q            # 静默加固R2级别项
EOF
}

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" >> "$LOG_FILE"
    [[ $QUIET -eq 0 ]] && echo -e "$1"
}

log_result() {
    local id="$1"
    local risk="$2"
    local desc="$3"
    local status="$4"
    local detail="$5"

    ((TOTAL++))
    local color=""
    case "$status" in
        PASS)    color="$GREEN"; ((PASS++)) ;;
        FAIL)    color="$RED"; ((FAIL++)) ;;
        CHANGED) color="$CYAN"; ((CHANGED++)) ;;
        SKIP)    color="$YELLOW"; ((SKIP++)) ;;
        ERROR)   color="$RED"; ((ERROR++)) ;;
    esac

    local line
    line=$(printf "  [%-7s] [%s] %-6s %-50s %s" "$status" "$risk" "$id" "$desc" "$detail")
    log "${color}${line}${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$status] [$risk] $id $desc $detail" >> "$LOG_FILE"
}

# 判断是否需要执行该检查项
should_run() {
    local item_id="$1"
    local item_risk="$2"

    # 如果在排除列表中，跳过
    if [[ -n "$EXCLUDED_ITEMS" ]]; then
        echo "$EXCLUDED_ITEMS" | tr ',' '\n' | grep -qw "$item_id" && return 1
    fi

    # 如果指定了具体项目
    if [[ -n "$SPECIFIED_ITEMS" ]]; then
        echo "$SPECIFIED_ITEMS" | tr ',' '\n' | grep -qw "$item_id" && return 0 || return 1
    fi

    # 按风险等级过滤
    if [[ "$RISK_LEVEL" == "ALL" ]]; then
        return 0
    fi

    [[ "$item_risk" == "$RISK_LEVEL" ]] && return 0 || return 1
}

# 备份文件
backup_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        mkdir -p "$BACKUP_DIR"
        cp -a "$file" "$BACKUP_DIR/$(echo "$file" | tr '/' '_')" 2>/dev/null
    fi
}

# 确保以 root 身份运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}错误: 此脚本需要 root 权限执行${NC}"
        echo "请使用: sudo $SCRIPT_NAME $*"
        exit 1
    fi
}

# 高风险项交互确认
# 非交互模式（如管道/脚本调用）自动跳过高风险项
confirm_high_risk() {
    local item_id="$1"
    local desc="$2"
    local checklist="$3"

    # 检查是否为交互终端
    if [[ ! -t 0 ]]; then
        log "${YELLOW}  [跳过] ${item_id} ${desc} — 非交互模式，高风险项需手动执行${NC}"
        return 1
    fi

    log ""
    log "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    log "${RED}║  ⚠️  高风险项确认: ${item_id} ${desc}${NC}"
    log "${RED}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "$checklist"
    log "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    log ""
    read -r -p "  确认执行此高风险项？输入 YES 继续，其他任意键跳过: " answer
    if [[ "$answer" == "YES" ]]; then
        return 0
    else
        log "${YELLOW}  [跳过] 用户取消${NC}"
        return 1
    fi
}

# 检查操作系统
check_os() {
    if [[ ! -f /etc/os-release ]]; then
        echo -e "${RED}错误: 未找到 /etc/os-release，无法确认操作系统${NC}"
        exit 1
    fi
    source /etc/os-release
    if [[ "$ID" != "tencentos" ]]; then
        echo -e "${YELLOW}警告: 当前系统为 $ID，非 TencentOS Server，部分配置项可能不适用${NC}"
    fi
    # 区分 V3 和 V4，用于后续兼容处理
    OS_MAJOR="${VERSION_ID%%.*}"
    if [[ "$OS_MAJOR" -ge 4 ]]; then
        OS_VER="V4"
    else
        OS_VER="V3"
    fi
}

# ============================================================================
# 1. 身份鉴别
# ============================================================================

# 1.1 密码复杂度策略 [R1]
check_1_1() {
    should_run "1.1" "R1" || return
    local desc="密码复杂度策略（pam_pwquality）"
    local detail=""
    local status="PASS"

    # 检查 /etc/security/pwquality.conf
    local minlen dcredit ucredit lcredit ocredit
    minlen=$(grep -E "^minlen\s*=" /etc/security/pwquality.conf 2>/dev/null | awk -F= '{print $2}' | tr -d ' ')
    dcredit=$(grep -E "^dcredit\s*=" /etc/security/pwquality.conf 2>/dev/null | awk -F= '{print $2}' | tr -d ' ')
    ucredit=$(grep -E "^ucredit\s*=" /etc/security/pwquality.conf 2>/dev/null | awk -F= '{print $2}' | tr -d ' ')
    lcredit=$(grep -E "^lcredit\s*=" /etc/security/pwquality.conf 2>/dev/null | awk -F= '{print $2}' | tr -d ' ')
    ocredit=$(grep -E "^ocredit\s*=" /etc/security/pwquality.conf 2>/dev/null | awk -F= '{print $2}' | tr -d ' ')

    local issues=""
    [[ -z "$minlen" || "$minlen" -lt 8 ]] && issues+="minlen<8 " && status="FAIL"
    [[ "$dcredit" != "-1" ]] && issues+="dcredit!=-1 " && status="FAIL"
    [[ "$ucredit" != "-1" ]] && issues+="ucredit!=-1 " && status="FAIL"
    [[ "$lcredit" != "-1" ]] && issues+="lcredit!=-1 " && status="FAIL"
    [[ "$ocredit" != "-1" ]] && issues+="ocredit!=-1 " && status="FAIL"

    # 检查 PAM 中是否引用了 pam_pwquality
    if ! grep -qE "^\s*password\s+requisite\s+pam_pwquality.so" /etc/pam.d/system-auth 2>/dev/null; then
        issues+="pam未配置pwquality "
        status="FAIL"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/security/pwquality.conf
        backup_file /etc/pam.d/system-auth

        # 配置 pwquality.conf
        local conf="/etc/security/pwquality.conf"
        for param in "minlen=8" "dcredit=-1" "ucredit=-1" "lcredit=-1" "ocredit=-1" "retry=3"; do
            local key="${param%%=*}"
            if grep -qE "^${key}\s*=" "$conf"; then
                sed -i "s/^${key}\s*=.*/${param}/" "$conf"
            else
                echo "$param" >> "$conf"
            fi
        done

        # 确保 PAM 中配置了 pam_pwquality
        if ! grep -qE "^\s*password\s+requisite\s+pam_pwquality.so" /etc/pam.d/system-auth; then
            sed -i '/^password.*pam_unix.so/i password    requisite     pam_pwquality.so try_first_pass minlen=8 dcredit=-1 ucredit=-1 lcredit=-1 ocredit=-1 retry=3 enforce_for_root' /etc/pam.d/system-auth
        fi

        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "1.1" "R1" "$desc" "$status" "$detail"
}

# 1.2 密码有效期策略 [R1]
check_1_2() {
    should_run "1.2" "R1" || return
    local desc="密码有效期策略（login.defs）"
    local status="PASS"
    local detail=""

    local max_days min_days min_len warn_age
    max_days=$(grep -E "^PASS_MAX_DAYS" /etc/login.defs 2>/dev/null | awk '{print $2}')
    min_days=$(grep -E "^PASS_MIN_DAYS" /etc/login.defs 2>/dev/null | awk '{print $2}')
    min_len=$(grep -E "^PASS_MIN_LEN" /etc/login.defs 2>/dev/null | awk '{print $2}')
    warn_age=$(grep -E "^PASS_WARN_AGE" /etc/login.defs 2>/dev/null | awk '{print $2}')

    local issues=""
    [[ -z "$max_days" || "$max_days" -gt 90 ]] && issues+="MAX_DAYS>90 " && status="FAIL"
    [[ -z "$min_days" || "$min_days" -lt 3 ]] && issues+="MIN_DAYS<3 " && status="FAIL"
    [[ -z "$min_len" || "$min_len" -lt 8 ]] && issues+="MIN_LEN<8 " && status="FAIL"
    [[ -z "$warn_age" || "$warn_age" -lt 7 ]] && issues+="WARN_AGE<7 " && status="FAIL"

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/login.defs
        local defs="/etc/login.defs"
        for kv in "PASS_MAX_DAYS 90" "PASS_MIN_DAYS 3" "PASS_MIN_LEN 8" "PASS_WARN_AGE 7"; do
            local key="${kv%% *}" val="${kv#* }"
            if grep -qE "^${key}" "$defs"; then
                sed -i "s/^${key}.*/${key}\t${val}/" "$defs"
            else
                echo -e "${key}\t${val}" >> "$defs"
            fi
        done

        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "1.2" "R1" "$desc" "$status" "$detail"
}

# 1.3 密码历史记录 [R1]
check_1_3() {
    should_run "1.3" "R1" || return
    local desc="密码历史记录（pam_pwhistory）"
    local status="PASS"
    local detail=""

    if ! grep -qE "pam_pwhistory.so.*remember=[0-9]+" /etc/pam.d/system-auth 2>/dev/null; then
        status="FAIL"
        detail="(未配置密码历史)"
    else
        local remember
        remember=$(grep -oE "remember=[0-9]+" /etc/pam.d/system-auth | head -1 | cut -d= -f2)
        if [[ -z "$remember" || "$remember" -lt 3 ]]; then
            status="FAIL"
            detail="(remember=$remember,应>=3)"
        fi
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/pam.d/system-auth
        if grep -qE "pam_pwhistory.so" /etc/pam.d/system-auth; then
            sed -i '/pam_pwhistory.so/d' /etc/pam.d/system-auth
        fi
        # 在 pam_unix.so 之前添加（pwhistory 必须在 unix 之前执行才能生效）
        sed -i '/^password.*pam_unix.so/i password    required      pam_pwhistory.so remember=3 enforce_for_root' /etc/pam.d/system-auth
        status="CHANGED"
        detail="(已配置 remember=3)"
    fi

    log_result "1.3" "R1" "$desc" "$status" "$detail"
}

# 1.4 密码加密算法 [R1]
check_1_4() {
    should_run "1.4" "R1" || return
    local desc="密码加密算法（SHA-512）"
    local status="PASS"
    local detail=""

    # 检查 login.defs
    if ! grep -qE "^ENCRYPT_METHOD\s+SHA512" /etc/login.defs 2>/dev/null; then
        status="FAIL"
        detail="(login.defs未配置SHA512)"
    fi

    # 检查 PAM
    if ! grep -qE "pam_unix.so.*sha512" /etc/pam.d/system-auth 2>/dev/null; then
        status="FAIL"
        detail+="(PAM未配置sha512)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/login.defs
        backup_file /etc/pam.d/system-auth

        # login.defs
        if grep -qE "^ENCRYPT_METHOD" /etc/login.defs; then
            sed -i 's/^ENCRYPT_METHOD.*/ENCRYPT_METHOD SHA512/' /etc/login.defs
        else
            echo "ENCRYPT_METHOD SHA512" >> /etc/login.defs
        fi

        # PAM
        if grep -qE "^\s*password\s+sufficient\s+pam_unix.so" /etc/pam.d/system-auth; then
            if ! grep -qE "pam_unix.so.*sha512" /etc/pam.d/system-auth; then
                sed -i '/^\s*password\s+sufficient\s+pam_unix.so/ s/$/ sha512/' /etc/pam.d/system-auth
            fi
        fi

        status="CHANGED"
        detail="(已配置SHA-512)"
    fi

    log_result "1.4" "R1" "$desc" "$status" "$detail"
}

# 1.5 登录失败锁定策略 [R1]
check_1_5() {
    should_run "1.5" "R1" || return
    local desc="登录失败锁定策略（pam_faillock）"
    local status="PASS"
    local detail=""

    # 检查 faillock.conf 或 PAM 配置
    local deny="" unlock_time=""
    if [[ -f /etc/security/faillock.conf ]]; then
        deny=$(grep -E "^deny\s*=" /etc/security/faillock.conf | awk -F= '{print $2}' | tr -d ' ')
        unlock_time=$(grep -E "^unlock_time\s*=" /etc/security/faillock.conf | awk -F= '{print $2}' | tr -d ' ')
    fi

    # 也检查 PAM 中的配置
    if [[ -z "$deny" ]]; then
        deny=$(grep -oE "deny=[0-9]+" /etc/pam.d/system-auth 2>/dev/null | head -1 | cut -d= -f2)
    fi
    if [[ -z "$unlock_time" ]]; then
        unlock_time=$(grep -oE "unlock_time=[0-9]+" /etc/pam.d/system-auth 2>/dev/null | head -1 | cut -d= -f2)
    fi

    local issues=""
    if [[ -z "$deny" || "$deny" -gt 5 || "$deny" -eq 0 ]]; then
        issues+="deny未配置或>5 "
        status="FAIL"
    fi
    if [[ -z "$unlock_time" || "$unlock_time" -lt 300 ]]; then
        issues+="unlock_time<300 "
        status="FAIL"
    fi

    # 检查 PAM 中是否引用了 pam_faillock
    if ! grep -qE "pam_faillock.so" /etc/pam.d/system-auth 2>/dev/null; then
        issues+="pam未配置faillock "
        status="FAIL"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/security/faillock.conf
        backup_file /etc/pam.d/system-auth

        # 配置 faillock.conf
        local fconf="/etc/security/faillock.conf"
        mkdir -p "$(dirname "$fconf")"
        for param in "deny = 3" "fail_interval = 900" "unlock_time = 600" "even_deny_root" "root_unlock_time = 300"; do
            local key="${param%%=*}"
            key=$(echo "$key" | tr -d ' ')
            if [[ "$param" == "even_deny_root" ]]; then
                grep -q "^even_deny_root" "$fconf" 2>/dev/null || echo "even_deny_root" >> "$fconf"
            elif grep -qE "^${key}\s*=" "$fconf" 2>/dev/null; then
                sed -i "s/^${key}\s*=.*/${param}/" "$fconf"
            else
                echo "$param" >> "$fconf"
            fi
        done

        # 确保 PAM 中配置了 pam_faillock（unlock_time 与 faillock.conf 保持一致=600）
        if ! grep -qE "pam_faillock.so.*preauth" /etc/pam.d/system-auth; then
            sed -i '/^auth.*pam_env.so/a auth        required      pam_faillock.so preauth silent audit deny=3 unlock_time=600 even_deny_root' /etc/pam.d/system-auth
        fi
        if ! grep -qE "pam_faillock.so.*authfail" /etc/pam.d/system-auth; then
            sed -i '/^auth.*pam_unix.so/a auth        [default=die] pam_faillock.so authfail audit deny=3 unlock_time=600 even_deny_root' /etc/pam.d/system-auth
        fi

        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "1.5" "R1" "$desc" "$status" "$detail"
}

# 1.6 会话超时锁定 [R1]
check_1_6() {
    should_run "1.6" "R1" || return
    local desc="会话超时锁定（TMOUT）"
    local status="PASS"
    local detail=""

    local tmout
    tmout=$(grep -E "^TMOUT=" /etc/profile 2>/dev/null | tail -1 | cut -d= -f2)

    if [[ -z "$tmout" || "$tmout" -gt 300 || "$tmout" -eq 0 ]]; then
        status="FAIL"
        detail="(TMOUT=${tmout:-未配置},应<=300)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/profile
        if grep -qE "^TMOUT=" /etc/profile; then
            sed -i 's/^TMOUT=.*/TMOUT=300/' /etc/profile
        else
            echo "TMOUT=300" >> /etc/profile
        fi
        # 同时设置只读防止用户修改
        if ! grep -q "readonly TMOUT" /etc/profile; then
            echo "readonly TMOUT" >> /etc/profile
        fi
        if ! grep -q "export TMOUT" /etc/profile; then
            echo "export TMOUT" >> /etc/profile
        fi
        status="CHANGED"
        detail="(已设置TMOUT=300)"
    fi

    log_result "1.6" "R1" "$desc" "$status" "$detail"
}

# ============================================================================
# 2. 访问控制
# ============================================================================

# 2.1 SSH 安全配置 [R1]
check_2_1() {
    should_run "2.1" "R1" || return
    local desc="SSH安全配置"
    local status="PASS"
    local detail=""
    local sshd_conf="/etc/ssh/sshd_config"
    local issues=""

    # 检查关键SSH参数
    declare -A ssh_params
    ssh_params=(
        ["Protocol"]="2"
        ["PermitEmptyPasswords"]="no"
        ["MaxAuthTries"]="4"
        ["ClientAliveInterval"]="300"
        ["ClientAliveCountMax"]="3"
        ["HostbasedAuthentication"]="no"
        ["IgnoreRhosts"]="yes"
        ["PermitUserEnvironment"]="no"
        ["LogLevel"]="INFO"
        ["SyslogFacility"]="AUTHPRIV"
        ["LoginGraceTime"]="60"
    )

    # 单独检查 Ciphers（值中包含逗号，需特殊处理）
    local ciphers_expected="aes256-ctr,aes192-ctr,aes128-ctr"
    local ciphers_actual
    ciphers_actual=$(grep -E "^\s*Ciphers\s+" "$sshd_conf" 2>/dev/null | awk '{print $2}' | tail -1)
    if [[ -z "$ciphers_actual" ]]; then
        issues+="Ciphers=未设置 "
        status="FAIL"
    fi

    for key in "${!ssh_params[@]}"; do
        local expected="${ssh_params[$key]}"
        local actual
        actual=$(grep -E "^\s*${key}\s+" "$sshd_conf" 2>/dev/null | awk '{print $2}' | tail -1)

        if [[ -z "$actual" || "$actual" != "$expected" ]]; then
            # MaxAuthTries 允许 <= 4
            if [[ "$key" == "MaxAuthTries" && -n "$actual" && "$actual" -le 4 ]]; then
                continue
            fi
            # ClientAliveInterval 允许 > 0 且 <= 300
            if [[ "$key" == "ClientAliveInterval" && -n "$actual" && "$actual" -gt 0 && "$actual" -le 300 ]]; then
                continue
            fi
            # LoginGraceTime 允许 > 0 且 <= 60
            if [[ "$key" == "LoginGraceTime" && -n "$actual" && "$actual" -gt 0 && "$actual" -le 60 ]]; then
                continue
            fi
            issues+="${key}=${actual:-未设置} "
            status="FAIL"
        fi
    done

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file "$sshd_conf"
        for key in "${!ssh_params[@]}"; do
            local expected="${ssh_params[$key]}"
            if grep -qE "^\s*${key}\s+" "$sshd_conf"; then
                sed -i "s/^\s*${key}\s.*/${key} ${expected}/" "$sshd_conf"
            elif grep -qE "^\s*#\s*${key}\s+" "$sshd_conf"; then
                sed -i "s/^\s*#\s*${key}\s.*/${key} ${expected}/" "$sshd_conf"
            else
                echo "${key} ${expected}" >> "$sshd_conf"
            fi
        done
        # Ciphers 单独处理
        if [[ -z "$ciphers_actual" ]]; then
            if grep -qE "^\s*Ciphers\s+" "$sshd_conf"; then
                sed -i "s/^\s*Ciphers\s.*/Ciphers ${ciphers_expected}/" "$sshd_conf"
            elif grep -qE "^\s*#\s*Ciphers" "$sshd_conf"; then
                sed -i "s/^\s*#\s*Ciphers.*/Ciphers ${ciphers_expected}/" "$sshd_conf"
            else
                echo "Ciphers ${ciphers_expected}" >> "$sshd_conf"
            fi
        fi
        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "2.1" "R1" "$desc" "$status" "$detail"
}

# 2.2 SSH Banner 配置 [R3]
check_2_2() {
    should_run "2.2" "R3" || return
    local desc="SSH登录Banner配置"
    local status="PASS"
    local detail=""

    local banner
    banner=$(grep -E "^\s*Banner\s+" /etc/ssh/sshd_config 2>/dev/null | awk '{print $2}')

    if [[ -z "$banner" || "$banner" == "none" ]]; then
        status="FAIL"
        detail="(Banner未配置)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/ssh/sshd_config
        backup_file /etc/issue.net

        echo "Authorized uses only. All activity may be monitored and reported." > /etc/issue.net
        echo "Authorized uses only. All activity may be monitored and reported." > /etc/issue

        if grep -qE "^\s*Banner\s+" /etc/ssh/sshd_config; then
            sed -i "s|^\s*Banner\s.*|Banner /etc/issue.net|" /etc/ssh/sshd_config
        elif grep -qE "^\s*#\s*Banner" /etc/ssh/sshd_config; then
            sed -i "s|^\s*#\s*Banner.*|Banner /etc/issue.net|" /etc/ssh/sshd_config
        else
            echo "Banner /etc/issue.net" >> /etc/ssh/sshd_config
        fi
        status="CHANGED"
        detail="(已配置Banner)"
    fi

    log_result "2.2" "R3" "$desc" "$status" "$detail"
}

# 2.3 SSH密钥文件权限 [R2]
check_2_3() {
    should_run "2.3" "R2" || return
    local desc="SSH密钥文件权限"
    local status="PASS"
    local detail=""
    local issues=""

    # sshd_config 权限
    local sshd_perm
    sshd_perm=$(stat -c "%a" /etc/ssh/sshd_config 2>/dev/null)
    if [[ "$sshd_perm" != "600" ]]; then
        issues+="sshd_config=$sshd_perm "
        status="FAIL"
    fi

    # 私钥权限
    for keyfile in /etc/ssh/ssh_host_*_key; do
        [[ ! -f "$keyfile" ]] && continue
        local perm
        perm=$(stat -c "%a" "$keyfile" 2>/dev/null)
        if [[ "$perm" != "600" && "$perm" != "400" ]]; then
            issues+="$(basename "$keyfile")=$perm "
            status="FAIL"
        fi
    done

    # 公钥权限
    for keyfile in /etc/ssh/ssh_host_*_key.pub; do
        [[ ! -f "$keyfile" ]] && continue
        local perm
        perm=$(stat -c "%a" "$keyfile" 2>/dev/null)
        if [[ "$perm" != "644" ]]; then
            issues+="$(basename "$keyfile")=$perm "
            status="FAIL"
        fi
    done

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        chmod 600 /etc/ssh/sshd_config
        chown root:root /etc/ssh/sshd_config
        for keyfile in /etc/ssh/ssh_host_*_key; do
            [[ -f "$keyfile" ]] && chmod 400 "$keyfile" && chown root:root "$keyfile"
        done
        for keyfile in /etc/ssh/ssh_host_*_key.pub; do
            [[ -f "$keyfile" ]] && chmod 644 "$keyfile" && chown root:root "$keyfile"
        done
        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "2.3" "R2" "$desc" "$status" "$detail"
}

# 2.4 限制su命令访问 [R1]
check_2_4() {
    should_run "2.4" "R1" || return
    local desc="限制su命令访问（pam_wheel）"
    local status="PASS"
    local detail=""

    if ! grep -qE "^\s*auth\s+required\s+pam_wheel.so\s+use_uid" /etc/pam.d/su 2>/dev/null; then
        status="FAIL"
        detail="(su未限制wheel组)"
    fi

    # 检查 login.defs 中的 SU_WHEEL_ONLY
    if ! grep -qE "^SU_WHEEL_ONLY\s+yes" /etc/login.defs 2>/dev/null; then
        status="FAIL"
        detail+="(SU_WHEEL_ONLY未启用)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/pam.d/su
        backup_file /etc/login.defs

        # 配置 PAM su
        if grep -qE "^\s*#.*pam_wheel.so\s+use_uid" /etc/pam.d/su; then
            sed -i 's/^\s*#\s*\(auth\s\+required\s\+pam_wheel.so\s\+use_uid\)/\1/' /etc/pam.d/su
        elif ! grep -qE "^\s*auth\s+required\s+pam_wheel.so\s+use_uid" /etc/pam.d/su; then
            sed -i '/pam_rootok.so/a auth\t\trequired\tpam_wheel.so use_uid' /etc/pam.d/su
        fi

        # 配置 SU_WHEEL_ONLY
        if grep -qE "^SU_WHEEL_ONLY" /etc/login.defs; then
            sed -i 's/^SU_WHEEL_ONLY.*/SU_WHEEL_ONLY yes/' /etc/login.defs
        else
            echo "SU_WHEEL_ONLY yes" >> /etc/login.defs
        fi

        status="CHANGED"
        detail="(已限制su命令)"
    fi

    log_result "2.4" "R1" "$desc" "$status" "$detail"
}

# 2.5 umask 设置 [R2]
check_2_5() {
    should_run "2.5" "R2" || return
    local desc="默认umask值配置"
    local status="PASS"
    local detail=""

    local umask_val
    umask_val=$(grep -E "^\s*umask\s+" /etc/profile 2>/dev/null | tail -1 | awk '{print $2}')

    # 允许 0027 或更严格 (如 077)
    if [[ -z "$umask_val" ]]; then
        status="FAIL"
        detail="(umask未配置)"
    elif [[ "$umask_val" != "0027" && "$umask_val" != "027" && "$umask_val" != "077" && "$umask_val" != "0077" ]]; then
        status="FAIL"
        detail="(umask=$umask_val,应为0027或更严格)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/profile
        if grep -qE "^\s*umask\s+" /etc/profile; then
            sed -i 's/^\(\s*\)umask\s.*/\1umask 0027/' /etc/profile
        else
            echo "umask 0027" >> /etc/profile
        fi
        status="CHANGED"
        detail="(已设置umask=0027)"
    fi

    log_result "2.5" "R2" "$desc" "$status" "$detail"
}

# 2.6 用户目录权限 [R2]
check_2_6() {
    should_run "2.6" "R2" || return
    local desc="用户目录权限（<=750）"
    local status="PASS"
    local detail=""
    local issues=""

    for dir in /home/*/; do
        [[ ! -d "$dir" ]] && continue
        local perm
        perm=$(stat -c "%a" "$dir" 2>/dev/null)
        if [[ $((8#$perm)) -gt $((8#750)) ]]; then
            issues+="$(basename "$dir")=$perm "
            status="FAIL"
        fi
    done

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        for dir in /home/*/; do
            [[ ! -d "$dir" ]] && continue
            local perm
            perm=$(stat -c "%a" "$dir" 2>/dev/null)
            if [[ $((8#$perm)) -gt $((8#750)) ]]; then
                chmod 750 "$dir"
            fi
        done
        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "2.6" "R2" "$desc" "$status" "$detail"
}

# 2.7 关键系统文件权限 [R2]
check_2_7() {
    should_run "2.7" "R2" || return
    local desc="关键系统文件权限"
    local status="PASS"
    local detail=""
    local issues=""

    # 检查关键文件权限和所有权
    declare -A file_perms
    file_perms=(
        ["/etc/passwd"]="644"
        ["/etc/shadow"]="000"
        ["/etc/group"]="644"
        ["/etc/gshadow"]="000"
        ["/etc/passwd-"]="644"
        ["/etc/shadow-"]="600"
        ["/etc/group-"]="644"
        ["/etc/gshadow-"]="600"
    )

    for file in "${!file_perms[@]}"; do
        [[ ! -f "$file" ]] && continue
        local expected="${file_perms[$file]}"
        local actual
        actual=$(stat -c "%a" "$file" 2>/dev/null)
        local owner
        owner=$(stat -c "%U:%G" "$file" 2>/dev/null)

        if [[ "$owner" != "root:root" ]]; then
            issues+="$(basename "$file"):owner=$owner "
            status="FAIL"
        fi

        # 将权限统一为数值比较（stat -c %a 返回 "0" 而非 "000"）
        local actual_num=$((10#$actual))

        # shadow/gshadow 文件（含备份）允许 000(0)、600、640
        if [[ "$file" == *"shadow"* ]]; then
            if [[ "$actual_num" -ne 0 && "$actual_num" -ne 600 && "$actual_num" -ne 640 ]]; then
                issues+="$(basename "$file")=$actual "
                status="FAIL"
            fi
        elif [[ "$file" == *"-"* ]]; then
            # passwd- 和 group- 备份文件，允许 ≤644
            if [[ "$actual_num" -gt 644 ]]; then
                issues+="$(basename "$file")=$actual "
                status="FAIL"
            fi
        else
            # passwd 和 group 正文件，期望精确 644
            if [[ "$actual_num" -ne 644 ]]; then
                issues+="$(basename "$file")=$actual "
                status="FAIL"
            fi
        fi
    done

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        for file in "${!file_perms[@]}"; do
            [[ ! -f "$file" ]] && continue
            chown root:root "$file"
        done
        chmod 644 /etc/passwd /etc/group 2>/dev/null
        chmod 600 /etc/shadow /etc/gshadow 2>/dev/null
        chmod 644 /etc/passwd- /etc/group- 2>/dev/null
        chmod 600 /etc/shadow- /etc/gshadow- 2>/dev/null
        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "2.7" "R2" "$desc" "$status" "$detail"
}

# 2.8 禁止 root 远程 SSH 登录 [R1] ⚠️ 高风险项
check_2_8() {
    should_run "2.8" "R1" || return
    local desc="禁止root远程SSH登录（⚠️ 高风险）"
    local status="PASS"
    local detail=""
    local sshd_conf="/etc/ssh/sshd_config"

    local val
    val=$(grep -E "^\s*PermitRootLogin\s+" "$sshd_conf" 2>/dev/null | awk '{print $2}' | tail -1)

    if [[ -z "$val" || "$val" != "no" ]]; then
        status="FAIL"
        detail="(PermitRootLogin=${val:-yes(默认)})"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        local checklist=""
        checklist+="${YELLOW}  请确认以下前置条件:${NC}\n"
        checklist+="  [ ] 已创建非 root 管理账户\n"
        checklist+="  [ ] 该账户已加入 sudoers 或 wheel 组\n"
        checklist+="  [ ] 已测试该账户可正常 SSH 登录\n"
        checklist+="  [ ] 已测试该账户可正常 sudo\n"
        checklist+="${RED}  风险: 如无其他管理账户，将导致无法远程登录服务器！${NC}"

        if confirm_high_risk "2.8" "禁止root远程SSH登录" "$checklist"; then
            backup_file "$sshd_conf"
            if grep -qE "^\s*PermitRootLogin\s+" "$sshd_conf"; then
                sed -i "s/^\s*PermitRootLogin\s.*/PermitRootLogin no/" "$sshd_conf"
            elif grep -qE "^\s*#\s*PermitRootLogin" "$sshd_conf"; then
                sed -i "s/^\s*#\s*PermitRootLogin.*/PermitRootLogin no/" "$sshd_conf"
            else
                echo "PermitRootLogin no" >> "$sshd_conf"
            fi

            # 验证 sshd 配置
            if sshd -t &>/dev/null; then
                status="CHANGED"
                detail="(已设置PermitRootLogin=no)"
            else
                # 回滚
                cp "$BACKUP_DIR/$(echo "$sshd_conf" | tr '/' '_')" "$sshd_conf" 2>/dev/null
                status="ERROR"
                detail="(sshd配置验证失败,已回滚)"
            fi
        else
            status="SKIP"
            detail="(用户跳过/非交互模式)"
        fi
    fi

    log_result "2.8" "R1" "$desc" "$status" "$detail"
}

# ============================================================================
# 3. 安全审计
# ============================================================================

# 3.1 审计服务状态 [R1]
check_3_1() {
    should_run "3.1" "R1" || return
    local desc="审计服务状态（auditd）"
    local status="PASS"
    local detail=""

    if ! rpm -q audit &>/dev/null; then
        status="FAIL"
        detail="(audit未安装)"
    elif ! systemctl is-active --quiet auditd; then
        status="FAIL"
        detail="(auditd未运行)"
    elif ! systemctl is-enabled --quiet auditd; then
        status="FAIL"
        detail="(auditd未设为开机自启)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        rpm -q audit &>/dev/null || dnf install -y audit &>/dev/null
        systemctl enable --now auditd &>/dev/null
        status="CHANGED"
        detail="(已安装并启动auditd)"
    fi

    log_result "3.1" "R1" "$desc" "$status" "$detail"
}

# 3.2 审计规则配置 [R1]
check_3_2() {
    should_run "3.2" "R1" || return
    local desc="审计规则配置"
    local status="PASS"
    local detail=""
    local rules_file="/etc/audit/rules.d/audit.rules"
    local missing=0

    # 必须的审计规则关键字
    local -a required_keys=(
        "sudoers"          # sudoers 修改
        "identity"         # 用户/组变更
        "time-change"      # 时间修改
        "system-locale"    # 网络环境变更
        "session"          # 会话信息
        "logins"           # 登录/登出
        "perm_mod"         # 权限修改
        "delete"           # 文件删除
        "modules"          # 内核模块
    )

    if [[ ! -f "$rules_file" ]]; then
        status="FAIL"
        detail="(审计规则文件不存在)"
        missing=${#required_keys[@]}
    else
        for key in "${required_keys[@]}"; do
            if ! grep -q "$key" "$rules_file" 2>/dev/null; then
                ((missing++))
            fi
        done
        if [[ $missing -gt 0 ]]; then
            status="FAIL"
            detail="(缺少${missing}类审计规则)"
        fi
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        mkdir -p /etc/audit/rules.d
        backup_file "$rules_file"

        # 生成完整的审计规则
        cat > "$rules_file" <<'AUDIT_RULES'
# TencentOS Server 等保三级审计规则
# 由安全加固脚本自动生成

# 删除所有已有规则
-D

# 设置缓冲区大小
-b 8192

# 监控 sudoers 变更
-w /etc/sudoers -p wa -k scope
-w /etc/sudoers.d -p wa -k scope
-w /var/log/sudo.log -p wa -k actions

# 监控用户/组信息变更
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

# 监控用户/组管理命令
-w /usr/sbin/useradd -p x -k user_group_modify
-w /usr/sbin/userdel -p x -k user_group_modify
-w /usr/sbin/usermod -p x -k user_group_modify
-w /usr/sbin/groupadd -p x -k user_group_modify
-w /usr/sbin/groupdel -p x -k user_group_modify
-w /usr/sbin/groupmod -p x -k user_group_modify

# 监控时间修改
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -S clock_settime -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
-a always,exit -F arch=b32 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change
-w /etc/chrony.conf -p wa -k time-change

# 监控网络环境变更
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale
-a always,exit -F arch=b32 -S sethostname -S setdomainname -k system-locale
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /etc/hostname -p wa -k system-locale
-w /etc/sysconfig/network -p wa -k system-locale

# 监控会话信息
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k session
-w /var/log/btmp -p wa -k session

# 监控登录/登出事件
-w /var/run/faillock/ -p wa -k logins
-w /var/log/lastlog -p wa -k logins

# 监控文件权限变更
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b64 -S setxattr -S lsetxattr -S fsetxattr -S removexattr -S lremovexattr -S fremovexattr -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S setxattr -S lsetxattr -S fsetxattr -S removexattr -S lremovexattr -S fremovexattr -F auid>=1000 -F auid!=4294967295 -k perm_mod

# 监控未授权文件访问
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access
-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access
-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access

# 监控文件系统挂载
-a always,exit -F arch=b64 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts
-a always,exit -F arch=b32 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts

# 监控文件删除事件
-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete
-a always,exit -F arch=b32 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete

# 监控 SELinux/MAC 策略变更
-w /etc/selinux/ -p wa -k MAC-policy

# 监控内核模块加载/卸载
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -S delete_module -k modules

# 锁定审计配置（应在最后一行）
-e 2
AUDIT_RULES

        # 重启 auditd
        service auditd restart &>/dev/null
        status="CHANGED"
        detail="(已部署完整审计规则)"
    fi

    log_result "3.2" "R1" "$desc" "$status" "$detail"
}

# 3.3 审计日志配置 [R2]
check_3_3() {
    should_run "3.3" "R2" || return
    local desc="审计日志存储配置"
    local status="PASS"
    local detail=""
    local auditd_conf="/etc/audit/auditd.conf"
    local issues=""

    if [[ ! -f "$auditd_conf" ]]; then
        status="FAIL"
        detail="(auditd.conf不存在)"
    else
        local max_log_file max_log_file_action
        max_log_file=$(grep -E "^max_log_file\s*=" "$auditd_conf" | awk -F= '{print $2}' | tr -d ' ')
        max_log_file_action=$(grep -E "^max_log_file_action\s*=" "$auditd_conf" | awk -F= '{print $2}' | tr -d ' ')

        [[ -z "$max_log_file" || "$max_log_file" -lt 6 ]] && issues+="max_log_file<6 " && status="FAIL"
        [[ "$max_log_file_action" != "ROTATE" && "$max_log_file_action" != "keep_logs" ]] && issues+="max_log_file_action=$max_log_file_action " && status="FAIL"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file "$auditd_conf"
        if grep -qE "^max_log_file\s*=" "$auditd_conf"; then
            sed -i 's/^max_log_file\s*=.*/max_log_file = 6/' "$auditd_conf"
        else
            echo "max_log_file = 6" >> "$auditd_conf"
        fi
        if grep -qE "^max_log_file_action\s*=" "$auditd_conf"; then
            sed -i 's/^max_log_file_action\s*=.*/max_log_file_action = ROTATE/' "$auditd_conf"
        else
            echo "max_log_file_action = ROTATE" >> "$auditd_conf"
        fi
        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "3.3" "R2" "$desc" "$status" "$detail"
}

# 3.4 rsyslog 服务配置 [R1]
check_3_4() {
    should_run "3.4" "R1" || return
    local desc="rsyslog服务及日志权限"
    local status="PASS"
    local detail=""
    local issues=""

    # 检查 rsyslog 服务
    if ! systemctl is-active --quiet rsyslog; then
        issues+="rsyslog未运行 "
        status="FAIL"
    fi

    # 检查日志文件默认权限
    if ! grep -qE "^\\\$FileCreateMode\s+0640" /etc/rsyslog.conf 2>/dev/null; then
        issues+="FileCreateMode未配置 "
        status="FAIL"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/rsyslog.conf
        rpm -q rsyslog &>/dev/null || dnf install -y rsyslog &>/dev/null
        systemctl enable --now rsyslog &>/dev/null

        if grep -qE "^\\\$FileCreateMode" /etc/rsyslog.conf; then
            sed -i 's/^\$FileCreateMode.*/\$FileCreateMode 0640/' /etc/rsyslog.conf
        else
            echo '$FileCreateMode 0640' >> /etc/rsyslog.conf
        fi
        systemctl restart rsyslog &>/dev/null
        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "3.4" "R1" "$desc" "$status" "$detail"
}

# ============================================================================
# 4. 入侵防范
# ============================================================================

# 4.1 禁用不必要的文件系统 [R2]
check_4_1() {
    should_run "4.1" "R2" || return
    local desc="禁用不必要的文件系统"
    local status="PASS"
    local detail=""
    local -a fs_list=("cramfs" "squashfs" "udf" "dccp" "sctp")
    local issues=""

    for fs in "${fs_list[@]}"; do
        if ! modprobe -n -v "$fs" 2>/dev/null | grep -q "install /bin/true"; then
            if lsmod | grep -qE "^${fs}\s"; then
                issues+="${fs} "
                status="FAIL"
            fi
        fi
    done

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        for fs in "${fs_list[@]}"; do
            if ! modprobe -n -v "$fs" 2>/dev/null | grep -q "install /bin/true"; then
                echo "install $fs /bin/true" >> /etc/modprobe.d/CIS.conf
            fi
            lsmod | grep -qE "^${fs}\s" && rmmod "$fs" 2>/dev/null
        done
        status="CHANGED"
        detail="(已禁用: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(未禁用: $issues)"
    fi

    log_result "4.1" "R2" "$desc" "$status" "$detail"
}

# 4.2 网络参数加固 [R1]
check_4_2() {
    should_run "4.2" "R1" || return
    local desc="网络参数加固（sysctl）"
    local status="PASS"
    local detail=""
    local issues=""

    declare -A sysctl_params
    sysctl_params=(
        ["net.ipv4.ip_forward"]="0"
        ["net.ipv4.conf.all.send_redirects"]="0"
        ["net.ipv4.conf.default.send_redirects"]="0"
        ["net.ipv4.conf.all.accept_source_route"]="0"
        ["net.ipv4.conf.default.accept_source_route"]="0"
        ["net.ipv4.conf.all.accept_redirects"]="0"
        ["net.ipv4.conf.default.accept_redirects"]="0"
        ["net.ipv4.conf.all.secure_redirects"]="0"
        ["net.ipv4.conf.default.secure_redirects"]="0"
        ["net.ipv4.conf.all.log_martians"]="1"
        ["net.ipv4.conf.default.log_martians"]="1"
        ["net.ipv4.icmp_echo_ignore_broadcasts"]="1"
        ["net.ipv4.icmp_ignore_bogus_error_responses"]="1"
        ["net.ipv4.conf.all.rp_filter"]="1"
        ["net.ipv4.conf.default.rp_filter"]="1"
        ["net.ipv4.tcp_syncookies"]="1"
    )

    for key in "${!sysctl_params[@]}"; do
        local expected="${sysctl_params[$key]}"
        local actual
        actual=$(sysctl -n "$key" 2>/dev/null)
        if [[ "$actual" != "$expected" ]]; then
            issues+="$(echo "$key" | sed 's/net.ipv4.//')=$actual "
            status="FAIL"
        fi
    done

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/sysctl.conf
        for key in "${!sysctl_params[@]}"; do
            local expected="${sysctl_params[$key]}"
            if grep -qE "^${key}\s*=" /etc/sysctl.conf; then
                sed -i "s|^${key}\s*=.*|${key} = ${expected}|" /etc/sysctl.conf
            else
                echo "${key} = ${expected}" >> /etc/sysctl.conf
            fi
            sysctl -w "${key}=${expected}" &>/dev/null
        done
        sysctl -w net.ipv4.route.flush=1 &>/dev/null
        status="CHANGED"
        detail="(已修复${#sysctl_params[@]}项网络参数)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "4.2" "R1" "$desc" "$status" "$detail"
}

# 4.3 关闭不必要的服务 [R2]
check_4_3() {
    should_run "4.3" "R2" || return
    local desc="关闭不必要的服务"
    local status="PASS"
    local detail=""
    local issues=""
    local -a services=(
        "xinetd" "avahi-daemon" "cups" "dhcpd" "named"
        "vsftpd" "dovecot" "smb" "squid" "snmpd"
        "ypserv" "rsyncd" "nfs" "rpcbind" "telnet.socket"
        "tftp.socket"
    )

    for svc in "${services[@]}"; do
        if systemctl is-active --quiet "$svc" 2>/dev/null || systemctl is-enabled --quiet "$svc" 2>/dev/null; then
            issues+="${svc} "
            status="FAIL"
        fi
    done

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        for svc in "${services[@]}"; do
            systemctl stop "$svc" &>/dev/null
            systemctl disable "$svc" &>/dev/null
        done
        status="CHANGED"
        detail="(已关闭: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(仍在运行: $issues)"
    fi

    log_result "4.3" "R2" "$desc" "$status" "$detail"
}

# 4.4 关闭高危端口 [R2]
check_4_4() {
    should_run "4.4" "R2" || return
    local desc="关闭高危端口"
    local status="PASS"
    local detail=""
    local issues=""
    local -a danger_ports=("21" "23" "25" "111" "427" "631")

    for port in "${danger_ports[@]}"; do
        if ss -tuln | grep -q ":${port} "; then
            issues+="${port} "
            status="FAIL"
        fi
    done

    if [[ "$status" == "FAIL" ]]; then
        detail="(监听中: $issues)"
        # harden 模式中关闭端口的服务在 4.3 中处理
        if [[ "$MODE" == "harden" ]]; then
            detail="(请执行4.3关闭对应服务)"
        fi
    fi

    log_result "4.4" "R2" "$desc" "$status" "$detail"
}

# 4.5 防火墙状态 [R1] ⚠️ 高风险项
check_4_5() {
    should_run "4.5" "R1" || return
    local desc="防火墙状态（⚠️ 高风险）"
    local status="PASS"
    local detail=""

    if systemctl is-active --quiet firewalld 2>/dev/null; then
        detail="(firewalld运行中)"
    elif systemctl is-active --quiet iptables 2>/dev/null; then
        detail="(iptables运行中)"
    elif iptables -L -n 2>/dev/null | grep -qv "^Chain.*policy ACCEPT" 2>/dev/null; then
        detail="(iptables规则已配置)"
    else
        status="FAIL"
        detail="(防火墙未启用)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        # 列出当前监听端口
        local listen_ports
        listen_ports=$(ss -tuln 2>/dev/null | grep LISTEN | awk '{print $5}' | sed 's/.*://' | sort -nu | tr '\n' ',' | sed 's/,$//')

        local checklist=""
        checklist+="${YELLOW}  当前监听端口: ${listen_ports:-无}${NC}\n"
        checklist+="  请确认以下前置条件:\n"
        checklist+="  [ ] SSH 端口(22)将自动加入白名单\n"
        checklist+="  [ ] 已梳理业务端口清单\n"
        checklist+="  [ ] 业务端口将在启用后手动添加\n"
        checklist+="  [ ] 有备用登录方式(VNC/控制台)\n"
        checklist+="${RED}  风险: 启用防火墙可能拦截业务端口，导致服务不可用！${NC}"

        if confirm_high_risk "4.5" "启用防火墙" "$checklist"; then
            rpm -q firewalld &>/dev/null || dnf install -y firewalld &>/dev/null
            systemctl enable --now firewalld &>/dev/null
            # 默认放行 SSH
            firewall-cmd --permanent --add-service=ssh &>/dev/null
            firewall-cmd --reload &>/dev/null
            status="CHANGED"
            detail="(已启用firewalld,SSH已加入白名单)"
        else
            status="SKIP"
            detail="(用户跳过/非交互模式)"
        fi
    fi

    log_result "4.5" "R1" "$desc" "$status" "$detail"
}

# 4.6 SELinux 状态 [R1] ⚠️ 高风险项
check_4_6() {
    should_run "4.6" "R1" || return
    local desc="SELinux状态（⚠️ 高风险）"
    local status="PASS"
    local detail=""

    local selinux_status
    selinux_status=$(getenforce 2>/dev/null || echo "Unknown")

    case "$selinux_status" in
        Enforcing)
            detail="(Enforcing)"
            ;;
        Permissive)
            status="PASS"
            detail="(Permissive - 观察模式)"
            ;;
        Disabled|*)
            status="FAIL"
            detail="(SELinux=${selinux_status})"
            ;;
    esac

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        local checklist=""
        checklist+="${YELLOW}  SELinux 当前状态: ${selinux_status}${NC}\n"
        checklist+="  请确认以下前置条件:\n"
        checklist+="  [ ] 了解 SELinux 对当前业务的影响\n"
        checklist+="  [ ] 已评估是否有自定义策略需求\n"
        checklist+="  [ ] 本次将设为 permissive 模式(观察,不阻断)\n"
        checklist+="  [ ] 观察确认无影响后再手动改为 enforcing\n"
        checklist+="${RED}  风险: SELinux 可能导致应用无法正常运行、服务启动失败！${NC}"

        if confirm_high_risk "4.6" "启用SELinux" "$checklist"; then
            backup_file /etc/selinux/config
            if [[ -f /etc/selinux/config ]]; then
                sed -i 's/^SELINUX=.*/SELINUX=permissive/' /etc/selinux/config
                setenforce 0 2>/dev/null  # 立即切换到 permissive（不需重启）
                status="CHANGED"
                detail="(已设为permissive,需观察确认后手动改enforcing)"
            else
                status="ERROR"
                detail="(/etc/selinux/config不存在)"
            fi
        else
            status="SKIP"
            detail="(用户跳过/非交互模式)"
        fi
    fi

    log_result "4.6" "R1" "$desc" "$status" "$detail"
}

# ============================================================================
# 5. 恶意代码防范
# ============================================================================

# 5.1 卸载不安全软件包 [R2]
check_5_1() {
    should_run "5.1" "R2" || return
    local desc="卸载不安全/不必要软件包"
    local status="PASS"
    local detail=""
    local issues=""
    local -a packages=(
        "telnet-server" "telnet" "ypbind" "ypserv" "rsh"
        "talk" "openldap-clients" "openslp" "openslp-server" "prelink"
    )

    for pkg in "${packages[@]}"; do
        if rpm -q "$pkg" &>/dev/null; then
            issues+="${pkg} "
            status="FAIL"
        fi
    done

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        for pkg in "${packages[@]}"; do
            rpm -q "$pkg" &>/dev/null && dnf remove -y "$pkg" &>/dev/null
        done
        status="CHANGED"
        detail="(已卸载: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(已安装: $issues)"
    fi

    log_result "5.1" "R2" "$desc" "$status" "$detail"
}

# 5.2 GPG 签名验证 [R2]
check_5_2() {
    should_run "5.2" "R2" || return
    local desc="软件包GPG签名验证"
    local status="PASS"
    local detail=""

    # 兼容 V3(/etc/yum.conf) 和 V4(/etc/dnf/dnf.conf)
    local pkg_conf=""
    if [[ -f /etc/dnf/dnf.conf ]]; then
        pkg_conf="/etc/dnf/dnf.conf"
    elif [[ -f /etc/yum.conf ]]; then
        pkg_conf="/etc/yum.conf"
    fi

    if [[ -z "$pkg_conf" ]]; then
        log_result "5.2" "R2" "$desc" "SKIP" "(未找到yum.conf或dnf.conf)"
        return
    fi

    if ! grep -qE "^gpgcheck\s*=\s*1" "$pkg_conf" 2>/dev/null; then
        status="FAIL"
        detail="($(basename "$pkg_conf") gpgcheck未启用)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file "$pkg_conf"
        if grep -qE "^gpgcheck\s*=" "$pkg_conf"; then
            sed -i 's/^gpgcheck\s*=.*/gpgcheck=1/' "$pkg_conf"
        else
            echo "gpgcheck=1" >> "$pkg_conf"
        fi
        status="CHANGED"
        detail="(已启用gpgcheck)"
    fi

    log_result "5.2" "R2" "$desc" "$status" "$detail"
}

# ============================================================================
# 6. 资源控制
# ============================================================================

# 6.1 时间同步配置 [R1]
check_6_1() {
    should_run "6.1" "R1" || return
    local desc="时间同步服务（chrony）"
    local status="PASS"
    local detail=""

    if ! rpm -q chrony &>/dev/null; then
        status="FAIL"
        detail="(chrony未安装)"
    elif ! systemctl is-active --quiet chronyd; then
        status="FAIL"
        detail="(chronyd未运行)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        rpm -q chrony &>/dev/null || dnf install -y chrony &>/dev/null
        systemctl enable --now chronyd &>/dev/null
        status="CHANGED"
        detail="(已安装并启动chrony)"
    fi

    log_result "6.1" "R1" "$desc" "$status" "$detail"
}

# 6.2 cron 权限配置 [R2]
check_6_2() {
    should_run "6.2" "R2" || return
    local desc="cron权限配置"
    local status="PASS"
    local detail=""
    local issues=""

    # 检查 crontab 相关目录/文件权限
    local -a cron_paths=(
        "/etc/crontab"
        "/etc/cron.hourly"
        "/etc/cron.daily"
        "/etc/cron.weekly"
        "/etc/cron.monthly"
        "/etc/cron.d"
    )

    for path in "${cron_paths[@]}"; do
        [[ ! -e "$path" ]] && continue
        local owner
        owner=$(stat -c "%U:%G" "$path" 2>/dev/null)
        if [[ "$owner" != "root:root" ]]; then
            issues+="$(basename "$path"):owner=$owner "
            status="FAIL"
        fi
    done

    # 检查 cron.allow / at.allow 访问控制
    if [[ -f /etc/cron.deny ]]; then
        issues+="cron.deny存在 "
        status="FAIL"
    fi
    if [[ -f /etc/at.deny ]]; then
        issues+="at.deny存在 "
        status="FAIL"
    fi
    if [[ ! -f /etc/cron.allow ]]; then
        issues+="cron.allow不存在 "
        status="FAIL"
    fi
    if [[ ! -f /etc/at.allow ]]; then
        issues+="at.allow不存在 "
        status="FAIL"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        for path in "${cron_paths[@]}"; do
            [[ ! -e "$path" ]] && continue
            chown root:root "$path"
            chmod go-rwx "$path"
        done
        # 配置 cron/at 访问控制白名单
        rm -f /etc/cron.deny /etc/at.deny
        touch /etc/cron.allow /etc/at.allow
        chown root:root /etc/cron.allow /etc/at.allow
        chmod 600 /etc/cron.allow /etc/at.allow
        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "6.2" "R2" "$desc" "$status" "$detail"
}

# 6.3 GRUB 引导配置权限 [R2]
check_6_3() {
    should_run "6.3" "R2" || return
    local desc="GRUB引导配置文件权限"
    local status="PASS"
    local detail=""

    local grub_cfg=""
    if [[ -d /sys/firmware/efi ]]; then
        # 动态查找 EFI 下的 grub.cfg，兼容 V3/V4 不同路径
        grub_cfg=$(find /boot/efi/EFI -name "grub.cfg" -type f 2>/dev/null | head -1)
    fi
    [[ -z "$grub_cfg" ]] && grub_cfg="/boot/grub2/grub.cfg"

    if [[ ! -f "$grub_cfg" ]]; then
        log_result "6.3" "R2" "$desc" "SKIP" "(grub.cfg不存在)"
        return
    fi

    local perm owner
    perm=$(stat -c "%a" "$grub_cfg" 2>/dev/null)
    owner=$(stat -c "%U:%G" "$grub_cfg" 2>/dev/null)

    if [[ "$owner" != "root:root" ]]; then
        status="FAIL"
        detail="(owner=$owner)"
    fi
    if [[ $((8#$perm)) -gt $((8#600)) ]]; then
        status="FAIL"
        detail+="(perm=$perm)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        chown root:root "$grub_cfg"
        chmod 600 "$grub_cfg"
        status="CHANGED"
        detail="(已修复grub.cfg权限)"
    fi

    log_result "6.3" "R2" "$desc" "$status" "$detail"
}

# 6.4 Banner 文件权限 [R3]
check_6_4() {
    should_run "6.4" "R3" || return
    local desc="Banner文件权限"
    local status="PASS"
    local detail=""
    local issues=""

    for file in /etc/motd /etc/issue /etc/issue.net; do
        [[ ! -f "$file" ]] && continue
        local owner perm
        owner=$(stat -c "%U:%G" "$file" 2>/dev/null)
        perm=$(stat -c "%a" "$file" 2>/dev/null)
        if [[ "$owner" != "root:root" ]]; then
            issues+="$(basename "$file"):owner=$owner "
            status="FAIL"
        fi
        if [[ "$perm" != "644" ]]; then
            issues+="$(basename "$file"):perm=$perm "
            status="FAIL"
        fi
    done

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        for file in /etc/motd /etc/issue /etc/issue.net; do
            [[ ! -f "$file" ]] && continue
            chown root:root "$file"
            chmod 644 "$file"
        done
        status="CHANGED"
        detail="(已修复: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
    fi

    log_result "6.4" "R3" "$desc" "$status" "$detail"
}

# 6.5 自动播放禁用 [R3]
check_6_5() {
    should_run "6.5" "R3" || return
    local desc="禁用自动播放（autofs）"
    local status="PASS"
    local detail=""

    if systemctl is-active --quiet autofs 2>/dev/null || systemctl is-enabled --quiet autofs 2>/dev/null; then
        status="FAIL"
        detail="(autofs仍启用)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        systemctl stop autofs &>/dev/null
        systemctl disable autofs &>/dev/null
        status="CHANGED"
        detail="(已禁用autofs)"
    fi

    log_result "6.5" "R3" "$desc" "$status" "$detail"
}

# 6.6 世界可写目录的 sticky bit [R3]
check_6_6() {
    should_run "6.6" "R3" || return
    local desc="世界可写目录sticky bit"
    local status="PASS"
    local detail=""

    local count
    count=$(df --local -P 2>/dev/null | awk '{if (NR!=1) print $6}' | xargs -I '{}' find '{}' -xdev -type d -perm -0002 ! -perm -1000 2>/dev/null | wc -l)

    if [[ "$count" -gt 0 ]]; then
        status="FAIL"
        detail="(${count}个目录缺少sticky bit)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        df --local -P 2>/dev/null | awk '{if (NR!=1) print $6}' | xargs -I '{}' find '{}' -xdev -type d -perm -0002 2>/dev/null | xargs chmod a+t 2>/dev/null
        status="CHANGED"
        detail="(已修复${count}个目录)"
    fi

    log_result "6.6" "R3" "$desc" "$status" "$detail"
}

# 6.7 审计进程早启动 [R2]
check_6_7() {
    should_run "6.7" "R2" || return
    local desc="审计进程早启动（GRUB audit=1）"
    local status="PASS"
    local detail=""

    if ! grep -qE "audit=1" /etc/default/grub 2>/dev/null; then
        status="FAIL"
        detail="(GRUB未配置audit=1)"
    fi

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        backup_file /etc/default/grub
        if grep -qE "^GRUB_CMDLINE_LINUX=" /etc/default/grub; then
            if ! grep -qE "audit=1" /etc/default/grub; then
                sed -i 's/\(^GRUB_CMDLINE_LINUX="[^"]*\)/\1 audit=1/' /etc/default/grub
            fi
        else
            echo 'GRUB_CMDLINE_LINUX="audit=1"' >> /etc/default/grub
        fi

        # 重新生成 GRUB 配置（动态查找路径，兼容 V3/V4）
        local grub_out=""
        if [[ -d /sys/firmware/efi ]]; then
            grub_out=$(find /boot/efi/EFI -name "grub.cfg" -type f 2>/dev/null | head -1)
        fi
        [[ -z "$grub_out" ]] && grub_out="/boot/grub2/grub.cfg"
        grub2-mkconfig -o "$grub_out" &>/dev/null
        status="CHANGED"
        detail="(已配置audit=1,需重启生效)"
    fi

    log_result "6.7" "R2" "$desc" "$status" "$detail"
}

# 6.8 UID/GID 唯一性检查 [R2]
check_6_8() {
    should_run "6.8" "R2" || return
    local desc="UID/GID唯一性检查"
    local status="PASS"
    local detail=""
    local issues=""

    # UID 唯一性
    local dup_uids
    dup_uids=$(awk -F: '{print $3}' /etc/passwd | sort | uniq -d)
    if [[ -n "$dup_uids" ]]; then
        issues+="重复UID:$(echo "$dup_uids" | tr '\n' ',') "
        status="FAIL"
    fi

    # GID 唯一性
    local dup_gids
    dup_gids=$(awk -F: '{print $3}' /etc/group | sort | uniq -d)
    if [[ -n "$dup_gids" ]]; then
        issues+="重复GID:$(echo "$dup_gids" | tr '\n' ',') "
        status="FAIL"
    fi

    # 用户名唯一性
    local dup_users
    dup_users=$(awk -F: '{print $1}' /etc/passwd | sort | uniq -d)
    if [[ -n "$dup_users" ]]; then
        issues+="重复用户名:$(echo "$dup_users" | tr '\n' ',') "
        status="FAIL"
    fi

    if [[ "$status" == "FAIL" ]]; then
        detail="(不合规: $issues)"
        # UID/GID 重复需要人工处理
        if [[ "$MODE" == "harden" ]]; then
            detail="(需人工处理: $issues)"
        fi
    fi

    log_result "6.8" "R2" "$desc" "$status" "$detail"
}

# 6.9 空密码账户检查 [R1]
check_6_9() {
    should_run "6.9" "R1" || return
    local desc="空密码账户检查"
    local status="PASS"
    local detail=""

    local empty_pass_users
    empty_pass_users=$(awk -F: '($2 == "" || $2 == "!!" || $2 == "!") {print $1}' /etc/shadow 2>/dev/null | grep -v "^$" | head -20)

    # 排除系统锁定账户(以!开头)
    local real_empty=""
    while IFS= read -r user; do
        [[ -z "$user" ]] && continue
        local pw
        pw=$(grep "^${user}:" /etc/shadow 2>/dev/null | cut -d: -f2)
        if [[ "$pw" == "" ]]; then
            real_empty+="${user} "
        fi
    done <<< "$empty_pass_users"

    if [[ -n "$real_empty" ]]; then
        status="FAIL"
        detail="(空密码账户: $real_empty)"
        if [[ "$MODE" == "harden" ]]; then
            # 锁定空密码账户
            for user in $real_empty; do
                passwd -l "$user" &>/dev/null
            done
            status="CHANGED"
            detail="(已锁定: $real_empty)"
        fi
    fi

    log_result "6.9" "R1" "$desc" "$status" "$detail"
}

# 6.10 删除无用系统账户 [R2]
check_6_10() {
    should_run "6.10" "R2" || return
    local desc="无用系统账户清理"
    local status="PASS"
    local detail=""
    local issues=""
    local -a unnecessary_users=("shutdown" "halt" "games" "ftp")

    for user in "${unnecessary_users[@]}"; do
        if id "$user" &>/dev/null; then
            issues+="${user} "
            status="FAIL"
        fi
    done

    if [[ "$status" == "FAIL" && "$MODE" == "harden" ]]; then
        for user in "${unnecessary_users[@]}"; do
            id "$user" &>/dev/null && userdel "$user" &>/dev/null
        done
        status="CHANGED"
        detail="(已删除: $issues)"
    elif [[ "$status" == "FAIL" ]]; then
        detail="(存在无用账户: $issues)"
    fi

    log_result "6.10" "R2" "$desc" "$status" "$detail"
}

# 6.11 SUID/SGID 文件审计 [R3]
check_6_11() {
    should_run "6.11" "R3" || return
    local desc="SUID/SGID文件审计"
    local status="PASS"
    local detail=""

    local count
    count=$(find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null | wc -l)

    detail="(发现${count}个SUID/SGID文件,请人工审查)"
    # 这是一个检查项，不自动修复
    if [[ $count -gt 0 ]]; then
        log_result "6.11" "R3" "$desc" "PASS" "$detail"
    else
        log_result "6.11" "R3" "$desc" "PASS" "(无SUID/SGID文件)"
    fi
}

# ============================================================================
# 主执行流程
# ============================================================================

print_header() {
    log ""
    log "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    log "${BLUE}║   TencentOS Server 等保三级安全加固工具 v${VERSION}                ║${NC}"
    log "${BLUE}╠══════════════════════════════════════════════════════════════╣${NC}"
    log "${BLUE}║   模式: $(printf '%-10s' "$MODE")    风险等级: $(printf '%-5s' "$RISK_LEVEL")                       ║${NC}"
    log "${BLUE}║   日志: ${LOG_FILE}${NC}"
    if [[ "$MODE" == "harden" ]]; then
    log "${BLUE}║   备份: ${BACKUP_DIR}${NC}"
    fi
    log "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    log ""
}

print_summary() {
    log ""
    log "${BLUE}══════════════════════ 执行结果摘要 ══════════════════════${NC}"
    log "  总检查项:   ${TOTAL}"
    log "  ${GREEN}通过 (PASS):    ${PASS}${NC}"
    log "  ${RED}失败 (FAIL):    ${FAIL}${NC}"
    log "  ${CYAN}已修复 (CHANGED): ${CHANGED}${NC}"
    log "  ${YELLOW}跳过 (SKIP):    ${SKIP}${NC}"
    if [[ $ERROR -gt 0 ]]; then
    log "  ${RED}错误 (ERROR):   ${ERROR}${NC}"
    fi
    log "${BLUE}════════════════════════════════════════════════════════════${NC}"
    log "  详细日志: ${LOG_FILE}"
    if [[ "$MODE" == "harden" ]]; then
    log "  备份目录: ${BACKUP_DIR}"
    fi
    log ""

    if [[ $FAIL -gt 0 && "$MODE" == "check" ]]; then
        log "${YELLOW}提示: 存在不合规项，可执行以下命令进行加固:${NC}"
        log "  sudo $SCRIPT_NAME harden -l $RISK_LEVEL"
        log ""
    fi

    if [[ "$MODE" == "harden" && $CHANGED -gt 0 ]]; then
        log "${YELLOW}注意: 部分配置变更需要重启服务或系统才能生效${NC}"
        log "  建议执行: systemctl restart sshd  (如修改了SSH配置)"
        log ""
    fi
}

run_all_checks() {
    log "${BLUE}━━━━━━━━━━━━━━━ 1. 身份鉴别 ━━━━━━━━━━━━━━━${NC}"
    check_1_1    # 密码复杂度策略
    check_1_2    # 密码有效期策略
    check_1_3    # 密码历史记录
    check_1_4    # 密码加密算法
    check_1_5    # 登录失败锁定策略
    check_1_6    # 会话超时锁定

    log ""
    log "${BLUE}━━━━━━━━━━━━━━━ 2. 访问控制 ━━━━━━━━━━━━━━━${NC}"
    check_2_1    # SSH 安全配置
    check_2_2    # SSH Banner
    check_2_3    # SSH 密钥文件权限
    check_2_4    # 限制su命令
    check_2_5    # umask
    check_2_6    # 用户目录权限
    check_2_7    # 关键系统文件权限
    check_2_8    # 禁止root远程SSH登录 ⚠️ 高风险

    log ""
    log "${BLUE}━━━━━━━━━━━━━━━ 3. 安全审计 ━━━━━━━━━━━━━━━${NC}"
    check_3_1    # 审计服务状态
    check_3_2    # 审计规则配置
    check_3_3    # 审计日志配置
    check_3_4    # rsyslog

    log ""
    log "${BLUE}━━━━━━━━━━━━━━━ 4. 入侵防范 ━━━━━━━━━━━━━━━${NC}"
    check_4_1    # 禁用不必要文件系统
    check_4_2    # 网络参数加固
    check_4_3    # 关闭不必要的服务
    check_4_4    # 关闭高危端口
    check_4_5    # 防火墙状态 ⚠️ 高风险
    check_4_6    # SELinux状态 ⚠️ 高风险

    log ""
    log "${BLUE}━━━━━━━━━━━━━━━ 5. 恶意代码防范 ━━━━━━━━━━━━━━━${NC}"
    check_5_1    # 卸载不安全软件包
    check_5_2    # GPG签名验证

    log ""
    log "${BLUE}━━━━━━━━━━━━━━━ 6. 资源控制 ━━━━━━━━━━━━━━━${NC}"
    check_6_1    # 时间同步
    check_6_2    # cron权限
    check_6_3    # GRUB权限
    check_6_4    # Banner文件权限
    check_6_5    # 自动播放禁用
    check_6_6    # sticky bit
    check_6_7    # 审计进程早启动
    check_6_8    # UID/GID唯一性
    check_6_9    # 空密码账户
    check_6_10   # 无用系统账户
    check_6_11   # SUID/SGID审计
}

# ============================================================================
# 参数解析
# ============================================================================

parse_args() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    case "$1" in
        check|harden) MODE="$1"; shift ;;
        -h|--help) usage; exit 0 ;;
        -v|--version) echo "$SCRIPT_NAME v$VERSION"; exit 0 ;;
        *) echo -e "${RED}错误: 未知模式 '$1'${NC}"; usage; exit 1 ;;
    esac

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -l|--level)
                RISK_LEVEL="$2"
                if [[ ! "$RISK_LEVEL" =~ ^(R1|R2|R3|ALL)$ ]]; then
                    echo -e "${RED}错误: 无效的风险等级 '$RISK_LEVEL'，有效值: R1, R2, R3, ALL${NC}"
                    exit 1
                fi
                shift 2
                ;;
            -i|--items)
                SPECIFIED_ITEMS="$2"
                shift 2
                ;;
            -e|--exclude)
                EXCLUDED_ITEMS="$2"
                shift 2
                ;;
            -q|--quiet)
                QUIET=1
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo -e "${RED}错误: 未知选项 '$1'${NC}"
                usage
                exit 1
                ;;
        esac
    done
}

# ============================================================================
# 入口
# ============================================================================

main() {
    parse_args "$@"
    check_root "$@"
    check_os

    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"

    print_header
    run_all_checks
    print_summary

    # 退出码: 0=全部通过, 1=有失败项, 2=有错误
    if [[ $ERROR -gt 0 ]]; then
        exit 2
    elif [[ $FAIL -gt 0 ]]; then
        exit 1
    fi
    exit 0
}

main "$@"
