#!/bin/bash
# install-deps.sh
# 文件系统延迟分析 - 依赖工具自动安装脚本
# 用法: ./install-deps.sh [--all] [--bcc] [--cflow] [--fix-tops]
#
# --all       安装所有依赖（bcc-tools + cflow + 修复 t-ops）
# --bcc       仅安装 bcc-tools
# --cflow     仅源码编译安装 cflow
# --fix-tops  修复 t-ops 兼容性（include 符号链接 + vmx.h + reverse_cpuid.h TSA + 5.4.241 ARM 误判）

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warning() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ============ 权限检查 ============
if [ "$EUID" -ne 0 ]; then
    error "此脚本需要 root 权限运行"
    exit 1
fi

# ============ 参数解析 ============
INSTALL_BCC=false
INSTALL_CFLOW=false
FIX_TOPS=false
INSTALL_TOPS=false

if [ $# -eq 0 ]; then
    # 无参数时自动检测并安装所有缺失依赖
    INSTALL_BCC=true
    INSTALL_CFLOW=true
    FIX_TOPS=true
    INSTALL_TOPS=true
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)      INSTALL_BCC=true; INSTALL_CFLOW=true; FIX_TOPS=true; INSTALL_TOPS=true; shift ;;
        --tops)     INSTALL_TOPS=true; shift ;;
        --bcc)      INSTALL_BCC=true; shift ;;
        --cflow)    INSTALL_CFLOW=true; shift ;;
        --fix-tops) FIX_TOPS=true; shift ;;
        --help|-h)
            echo "用法: $0 [--all] [--bcc] [--cflow] [--fix-tops]"
            echo ""
            echo "  --all       安装所有依赖（tencentos-tools + bcc-tools + cflow + 修复 t-ops）"
            echo "  --tops      安装 tencentos-tools 并修复已知 bug"
            echo "  --bcc       仅安装 bcc-tools（提供 biolatency/ext4slower/fileslower 等 eBPF 工具）"
            echo "  --cflow     仅源码编译安装 cflow（t-ops os_stat 热路径分析依赖）"
            echo "  --fix-tops  修复 t-ops 兼容性问题（include 符号链接 + vmx.h + reverse_cpuid.h TSA + 5.4.241 ARM 误判）"
            echo ""
            echo "  不带参数时自动检测并安装所有缺失依赖。"
            exit 0
            ;;
        *) error "未知参数: $1"; exit 1 ;;
    esac
done

# ============ 安装 tencentos-tools 并修复已知 bug ============
install_tops() {
    if rpm -q tencentos-tools &>/dev/null; then
        success "tencentos-tools 已安装: $(rpm -q tencentos-tools)"
    else
        info "安装 tencentos-tools..."
        if yum install -y tencentos-tools 2>&1; then
            success "tencentos-tools 安装成功: $(rpm -q tencentos-tools)"
        else
            error "tencentos-tools 安装失败，请检查 yum 源配置"
            return 1
        fi
    fi

    # 修复 4.2.17+ ops-run 路径 bug：
    # 4.2.17 将 os_stat_user/os_stat 内容移到了 common/tools-manager 和 common/kernel，
    # 但 latency/ops-run 脚本里仍然 cd $file_dir/os_stat_user 和 cd $file_dir/os_stat/，
    # 导致 t-ops latency os_stat 无法运行。
    # 修复方式：sed 替换 ops-run 里的路径。
    local LATENCY_OPS_RUN="/usr/lib/tencentos-tools/ops/latency/ops-run"
    if [ -f "$LATENCY_OPS_RUN" ]; then
        # 检查是否还在用旧路径
        if grep -q 'cd \$file_dir/os_stat_user' "$LATENCY_OPS_RUN"; then
            local COMMON="/usr/lib/tencentos-tools/ops/common"
            if [ -d "$COMMON/tools-manager" ] && [ -d "$COMMON/kernel" ] && \
               [ ! -d "/usr/lib/tencentos-tools/ops/latency/os_stat_user" ]; then
                info "检测到 4.2.17+ ops-run 路径 bug，正在修复..."

                # 备份
                if [ ! -f "${LATENCY_OPS_RUN}.bak.install-deps" ]; then
                    cp "$LATENCY_OPS_RUN" "${LATENCY_OPS_RUN}.bak.install-deps"
                    info "已备份: ${LATENCY_OPS_RUN}.bak.install-deps"
                fi

                # os_stat_user -> ../common/tools-manager
                sed -i 's|cd \$file_dir/os_stat_user|cd $file_dir/../common/tools-manager|g' "$LATENCY_OPS_RUN"
                # os_stat/ -> ../common/kernel
                sed -i 's|cd \$file_dir/os_stat/|cd $file_dir/../common/kernel/|g' "$LATENCY_OPS_RUN"
                # os_stat_show_parameter -> ../common/user/os_stat_show_parameter
                sed -i 's|cd \$file_dir/os_stat_show_parameter|cd $file_dir/../common/user/os_stat_show_parameter|g' "$LATENCY_OPS_RUN"
                # os_stat_uprobe -> ../common/user/uprobe
                sed -i 's|cd \$file_dir/os_stat_uprobe|cd $file_dir/../common/user/uprobe|g' "$LATENCY_OPS_RUN"
                # os_stat_paremter (typo in ops-run) -> ../common/user (若存在)
                sed -i 's|cd \$file_dir/os_stat_paremter|cd $file_dir/../common/user|g' "$LATENCY_OPS_RUN"
                # mv os_aware.ko ../os_stat_user/ -> ../tools-manager/
                sed -i 's|mv os_aware.ko ../os_stat_user/|mv os_aware.ko ../tools-manager/|g' "$LATENCY_OPS_RUN"
                # mv os_aware.ko ../os_stat_show_parameter/ -> ../user/os_stat_show_parameter/
                sed -i 's|mv os_aware.ko ../os_stat_show_parameter/|mv os_aware.ko ../user/os_stat_show_parameter/|g' "$LATENCY_OPS_RUN"
                # $file_dir/os_stat_user/$module -> ../common/tools-manager/$module
                sed -i 's|\$file_dir/os_stat_user/\$module|$file_dir/../common/tools-manager/$module|g' "$LATENCY_OPS_RUN"

                success "ops-run 路径已修复（os_stat_user -> common/tools-manager, os_stat -> common/kernel 等）"
            else
                success "ops-run 路径无需修复（os_stat_user 目录存在或 common 结构不匹配）"
            fi
        else
            success "ops-run 路径已是正确的（无旧路径引用）"
        fi
    fi
}

# ============ 安装 bcc-tools ============
install_bcc() {
    if ! rpm -q bcc-tools &>/dev/null; then
        info "安装 bcc-tools（提供 biolatency/ext4slower/fileslower/filetop 等 eBPF 工具）..."
        if yum install -y bcc-tools 2>&1; then
            success "bcc-tools 安装成功"
        else
            error "bcc-tools 安装失败，请检查 yum 源配置"
            return 1
        fi
    else
        success "bcc-tools 已安装: $(rpm -q bcc-tools)"
    fi

    # bcc-tools 工具安装在 /usr/share/bcc/tools/ 下，不在 PATH 中
    # 创建软链接到 /usr/local/bin/ 使其可直接调用
    local BCC_DIR="/usr/share/bcc/tools"
    local LINK_DIR="/usr/local/bin"
    local LINKED=0
    for tool in biolatency ext4slower fileslower filetop readahead; do
        if [ -f "$BCC_DIR/$tool" ]; then
            if [ ! -e "$LINK_DIR/$tool" ]; then
                ln -sf "$BCC_DIR/$tool" "$LINK_DIR/$tool"
                LINKED=$((LINKED + 1))
            fi
        else
            warning "  $tool 未找到"
        fi
    done
    if [ "$LINKED" -gt 0 ]; then
        success "已创建 $LINKED 个 bcc 工具软链接到 $LINK_DIR（biolatency 等可直接调用）"
    else
        success "bcc 工具软链接已就绪"
    fi
}

# ============ 源码编译安装 cflow ============
install_cflow() {
    if command -v cflow &>/dev/null; then
        success "cflow 已安装: $(cflow --version | head -1)"
        return 0
    fi

    info "源码编译安装 cflow（t-ops os_stat 热路径分析依赖）..."

    # 检查编译依赖
    if ! command -v gcc &>/dev/null; then
        info "安装 gcc..."
        yum install -y gcc 2>&1
    fi
    if ! command -v make &>/dev/null; then
        info "安装 make..."
        yum install -y make 2>&1
    fi

    local CFLOW_VERSION="1.7"
    local CFLOW_URL="https://ftp.gnu.org/gnu/cflow/cflow-${CFLOW_VERSION}.tar.gz"
    local BUILD_DIR="/tmp/cflow-build-$$"

    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"

    info "下载 cflow-${CFLOW_VERSION}..."
    if ! wget -q "$CFLOW_URL" -O "cflow-${CFLOW_VERSION}.tar.gz"; then
        # 备用镜像
        local MIRROR_URL="https://mirrors.ustc.edu.cn/gnu/cflow/cflow-${CFLOW_VERSION}.tar.gz"
        info "GNU 官方源下载失败，尝试 USTC 镜像..."
        if ! wget -q "$MIRROR_URL" -O "cflow-${CFLOW_VERSION}.tar.gz"; then
            error "cflow 下载失败，请手动下载: $CFLOW_URL"
            rm -rf "$BUILD_DIR"
            return 1
        fi
    fi

    tar xzf "cflow-${CFLOW_VERSION}.tar.gz"
    cd "cflow-${CFLOW_VERSION}"

    info "编译 cflow..."
    ./configure --quiet 2>&1
    make -j 2>&1
    make install 2>&1

    # 验证
    if command -v cflow &>/dev/null; then
        success "cflow 安装成功: $(cflow --version | head -1)"
    else
        error "cflow 安装失败"
        rm -rf "$BUILD_DIR"
        return 1
    fi

    # 清理
    rm -rf "$BUILD_DIR"
    success "编译临时文件已清理"
}

# ============ 修复 t-ops 兼容性问题 ============
fix_tops_compat() {
    local KVER
    KVER=$(uname -r)
    local ARCH
    ARCH=$(uname -m)

    # 自动识别 tencentos-tools 版本的目录布局
    # 4.2.17+: common/ops-run, common/kernel/, latency/ops-run
    # 4.2.12:  os_stat/ops-run, os_stat/os_stat/ (编译目录), common/kernel/ (可能不完整)
    local TOPS_BASE="/usr/lib/tencentos-tools/ops"
    local TOPS_COMMON="$TOPS_BASE/common"

    if [ ! -d "$TOPS_BASE" ]; then
        warning "tencentos-tools 未安装（$TOPS_BASE 不存在），跳过修复"
        return 0
    fi

    # 确定 ops-run 位置和编译目录
    local OPS_RUN=""
    local KERNEL_DIR=""
    local TOPS_VER=""

    if [ -f "$TOPS_COMMON/ops-run" ]; then
        # 4.2.17+ 布局
        OPS_RUN="$TOPS_COMMON/ops-run"
        KERNEL_DIR="$TOPS_COMMON/kernel"
        TOPS_VER="4.2.17+"
    elif [ -f "$TOPS_BASE/os_stat/ops-run" ]; then
        # 4.2.12 布局
        OPS_RUN="$TOPS_BASE/os_stat/ops-run"
        KERNEL_DIR="$TOPS_BASE/os_stat/os_stat"
        TOPS_VER="4.2.12"
    else
        warning "未找到 ops-run（路径不匹配已知版本），跳过修复"
        return 0
    fi

    info "检测到 tencentos-tools $TOPS_VER 布局（ops-run: $OPS_RUN）"

    # ---- 1. 修复 5.4.241-24 x86_64 被误判为 ARM 的 bug ----
    if [[ "$ARCH" == "x86_64" ]] && echo "$KVER" | grep -q "5.4.241-24"; then
        info "检测到 t-ops include 软链接 bug（x86_64 内核 $KVER 被误判为 ARM）"

        if [ ! -f "${OPS_RUN}.bak.install-deps" ]; then
            cp "$OPS_RUN" "${OPS_RUN}.bak.install-deps"
            info "已备份: ${OPS_RUN}.bak.install-deps"
        fi

        if grep -q '"5.4.241-1"' "$OPS_RUN"; then
            sed -i 's/strstr $(uname -r) "5.4.241-1"/strstr $(uname -r) "5.4.241"/' "$OPS_RUN"
            success "已修复: res_5_4_new 匹配范围扩展为 5.4.241"
        fi

        if grep -q 'res_5_4_arm.*\]; then' "$OPS_RUN" && ! grep -q 'uname -m.*aarch64' "$OPS_RUN"; then
            sed -i 's/\[ ! -z "$res_5_4_arm" \]; then/[ ! -z "$res_5_4_arm" ] \&\& [ "$(uname -m)" = "aarch64" ]; then/' "$OPS_RUN"
            success "已修复: ARM 分支增加 aarch64 架构检查"
        fi
    fi

    # ---- 2. 通用 include 符号链接修复 ----
    # 4.2.17 的 latency/ops-run include_link() 有 bug（rm include 少了一层路径），
    # 导致 include/include 符号链接永远修不对。这里主动根据内核版本设置正确的链接。
    # 4.2.12 的 include 是一层结构（os_stat/os_stat/include），ops-run 自身能正常处理，
    # 但这里也做检查作为防御。
    _fix_include_link "$KERNEL_DIR" "$KVER" "$ARCH"

    # ---- 2.1 修复 ops-run 脚本中 include_link() 的路径 bug ----
    # latency/ops-run 和 test/ops-run 的 include_link() 使用 "rm include" + "ln -sf xxx include"
    # 但在两层嵌套结构（include/include -> include_xxx）下应该是 "rm include/include" +
    # "ln -sf xxx include/include"。common/ops-run 已修正，这里把其他副本也修正。
    _fix_ops_run_include_link "$TOPS_BASE"

    # ---- 3. vmx.h host_debugctl 兼容修复（6.6.0~6.6.103 内核） ----
    # tencentos-tools 自带的 vmx.h 中 3 个 inline 函数引用了 host_debugctl 字段，
    # 该字段在 6.6.104+ 内核的 kvm_vcpu_arch 中才存在。
    # 用 LINUX_VERSION_CODE >= KERNEL_VERSION(6,6,104) 做条件编译保护。
    # 在两种版本布局下搜索所有可能的 vmx.h 位置
    local VMX_FOUND=false
    local vmx_path
    for vmx_path in \
        "$KERNEL_DIR/include/include_6_6/arch/x86/kvm/vmx/vmx.h" \
        "$TOPS_COMMON/kernel/include/include_6_6/arch/x86/kvm/vmx/vmx.h"; do
        if [ -f "$vmx_path" ]; then
            _fix_vmx_h "$vmx_path"
            VMX_FOUND=true
            break
        fi
    done
    if [ "$VMX_FOUND" = false ]; then
        success "vmx.h 不存在，无需修复（当前版本可能未包含）"
    fi

    # ---- 4. net_tracker_refcnt.c kabi_reserved 冲突修复 ----
    # 4.2.17 的 net_tracker_refcnt.c 使用 sk->kabi_reserved1 存 netns_tracker 指针，
    # 但开启 CONFIG_SECURITY_BIBA 的内核中 kabi_reserved1 已被 BIBA 占用，
    # 需改用 kabi_reserved2。
    _fix_net_tracker_kabi "$TOPS_BASE"

    # ---- 5. reverse_cpuid.h TSA_SQ_NO/TSA_L1_NO 兼容修复（<6.6.98 内核） ----
    _fix_reverse_cpuid_tsa "$TOPS_BASE"
}

# include 符号链接修复子函数
# 参数: $1=KERNEL_DIR $2=KVER $3=ARCH
_fix_include_link() {
    local KERNEL_DIR="$1" KVER="$2" ARCH="$3"

    # 4.2.17: include/include -> include_xxx (两层嵌套)
    if [ -d "$KERNEL_DIR/include" ] && [ -d "$KERNEL_DIR/include/include_pub" ]; then
        local CURRENT_LINK
        CURRENT_LINK=$(readlink "$KERNEL_DIR/include/include" 2>/dev/null)
        local EXPECTED_LINK=""
        EXPECTED_LINK=$(_get_expected_include "$KVER" "$ARCH")

        if [ -n "$EXPECTED_LINK" ]; then
            if [ -d "$KERNEL_DIR/include/$EXPECTED_LINK" ]; then
                if [[ "$CURRENT_LINK" != "$EXPECTED_LINK" ]]; then
                    rm -f "$KERNEL_DIR/include/include" 2>/dev/null
                    ln -sf "$EXPECTED_LINK" "$KERNEL_DIR/include/include"
                    success "include 符号链接已修复: include/include -> $EXPECTED_LINK（原: ${CURRENT_LINK:-无}）"
                else
                    success "include 符号链接已正确: include/include -> $EXPECTED_LINK"
                fi
            else
                warning "期望的 include 目录不存在: $KERNEL_DIR/include/$EXPECTED_LINK"
            fi
        else
            info "未匹配到已知内核版本（$KVER），跳过 include 链接修复"
        fi
    # 4.2.12: include -> include_xxx (一层，直接是符号链接)
    elif [ -L "$KERNEL_DIR/include" ]; then
        local CURRENT_LINK
        CURRENT_LINK=$(readlink "$KERNEL_DIR/include" 2>/dev/null)
        local EXPECTED_LINK=""
        EXPECTED_LINK=$(_get_expected_include "$KVER" "$ARCH")

        if [ -n "$EXPECTED_LINK" ]; then
            if [[ "$CURRENT_LINK" != "$EXPECTED_LINK" ]]; then
                rm -f "$KERNEL_DIR/include" 2>/dev/null
                ln -sf "$EXPECTED_LINK" "$KERNEL_DIR/include"
                success "include 符号链接已修复: include -> $EXPECTED_LINK（原: ${CURRENT_LINK:-无}）"
            else
                success "include 符号链接已正确: include -> $EXPECTED_LINK"
            fi
        else
            info "未匹配到已知内核版本（$KVER），跳过 include 链接修复"
        fi
    else
        info "未找到 include 链接结构（$KERNEL_DIR），跳过"
    fi
}

# 根据内核版本返回期望的 include 目录名
_get_expected_include() {
    local KVER="$1" ARCH="$2"

    if echo "$KVER" | grep -q "6\.6"; then
        echo "include_6_6"
    elif echo "$KVER" | grep -qE "5\.4\.203|5\.4\.119|5\.4\.241-1"; then
        echo "include_private"
    elif echo "$KVER" | grep -q "5\.4\.241-24"; then
        if [[ "$ARCH" == "aarch64" ]]; then
            echo "include_tk4_arm"
        else
            echo "include_private"
        fi
    elif echo "$KVER" | grep -q "4\.14"; then
        echo "include_tk3"
    elif echo "$KVER" | grep -q "3\.10"; then
        echo "include_tk2"
    elif echo "$KVER" | grep -q "0009"; then
        echo "include_pub"
    fi
}

# 修复 ops-run 脚本中 include_link() 的路径 bug
# 将 "rm include" / "ln -sf xxx include" 修正为 "rm -f include/include" / "ln -sf xxx include/include"
# 只在两层嵌套结构（include/ 是目录）的布局下执行
_fix_ops_run_include_link() {
    local TOPS_BASE="$1"
    local KERNEL_DIR="$TOPS_BASE/common/kernel"

    # 只有两层嵌套结构才需要修
    if [ ! -d "$KERNEL_DIR/include" ] || [ ! -d "$KERNEL_DIR/include/include_pub" ]; then
        return 0
    fi

    local ops_run_file patched=0
    for ops_run_file in "$TOPS_BASE"/latency/ops-run "$TOPS_BASE"/test/ops-run; do
        if [ ! -f "$ops_run_file" ]; then
            continue
        fi
        # 检查是否包含有 bug 的 "rm include"（行尾是 include，不是 include/include）
        if grep -q '^\s*rm include$' "$ops_run_file"; then
            if [ ! -f "${ops_run_file}.bak.install-deps" ]; then
                cp "$ops_run_file" "${ops_run_file}.bak.install-deps"
            fi
            # rm include  →  rm -f include/include
            sed -i '/^\s*rm include$/s|rm include|rm -f include/include|' "$ops_run_file"
            # rm ./include/include 的情况不用改（已经对了）
            # ln -sf xxx include$  →  ln -sf xxx include/include
            sed -i '/^\s*ln -sf include_[a-z0-9_]* include$/s|include$|include/include|' "$ops_run_file"
            patched=$((patched + 1))
            success "已修复 ops-run include_link() 路径 bug: $ops_run_file"
        else
            success "ops-run include_link() 路径已正确: $ops_run_file"
        fi
    done

    if [ "$patched" -eq 0 ]; then
        success "所有 ops-run 的 include_link() 路径均已正确"
    fi
}

# net_tracker_refcnt.c kabi_reserved 修复子函数
# 4.2.17 的 net_tracker_refcnt.c 使用 sk->kabi_reserved1 存 netns_tracker 指针，
# 但开启 CONFIG_SECURITY_BIBA 的内核中 kabi_reserved1 已被 BIBA 模块占用（sk_biba_security），
# 此时应改用 kabi_reserved2。
_fix_net_tracker_kabi() {
    local TOPS_BASE="$1"
    local NET_TRACKER=""
    local f
    for f in \
        "$TOPS_BASE/common/kernel/net_scene/net_tracker_refcnt.c" \
        "$TOPS_BASE/os_stat/os_stat/net_scene/net_tracker_refcnt.c"; do
        if [ -f "$f" ]; then
            NET_TRACKER="$f"
            break
        fi
    done

    if [ -z "$NET_TRACKER" ]; then
        success "net_tracker_refcnt.c 不存在，无需修复"
        return 0
    fi

    # 检查是否使用了 kabi_reserved1
    if ! grep -q 'kabi_reserved1' "$NET_TRACKER"; then
        success "net_tracker_refcnt.c 未使用 kabi_reserved1，无需修复"
        return 0
    fi

    # 检查内核是否开启 CONFIG_SECURITY_BIBA
    local KCONFIG=""
    if [ -f "/boot/config-$(uname -r)" ]; then
        KCONFIG="/boot/config-$(uname -r)"
    elif [ -f "/lib/modules/$(uname -r)/build/.config" ]; then
        KCONFIG="/lib/modules/$(uname -r)/build/.config"
    fi

    if [ -z "$KCONFIG" ]; then
        warning "未找到内核 config，跳过 net_tracker_refcnt.c kabi 修复"
        return 0
    fi

    if grep -q '^CONFIG_SECURITY_BIBA=y' "$KCONFIG"; then
        info "检测到 CONFIG_SECURITY_BIBA=y，kabi_reserved1 已被占用，替换为 kabi_reserved2..."
        cp "$NET_TRACKER" "${NET_TRACKER}.bak"
        sed -i 's/kabi_reserved1/kabi_reserved2/g' "$NET_TRACKER"
        local count
        count=$(grep -c 'kabi_reserved2' "$NET_TRACKER")
        success "net_tracker_refcnt.c: kabi_reserved1 -> kabi_reserved2 (${count} 处已替换)"
    else
        success "CONFIG_SECURITY_BIBA 未开启，kabi_reserved1 无冲突，无需修复"
    fi
}

# vmx.h 修复子函数
_fix_vmx_h() {
    local VMX_H="$1"
    if grep -q "host_debugctl" "$VMX_H" && ! grep -q "KERNEL_VERSION(6,6,104)" "$VMX_H"; then
        info "检测到 vmx.h 缺少版本保护（host_debugctl 兼容问题），正在修复..."
        sed -i '/^static inline void vmx_guest_debugctl_write/i #if LINUX_VERSION_CODE >= KERNEL_VERSION(6,6,104)' "$VMX_H"
        sed -i '/vmx_guest_debugctl_write(vcpu, val & ~DEBUGCTLMSR_FREEZE_IN_SMM);/{n;s/^}$/}\n#endif/}' "$VMX_H"
        if grep -q "KERNEL_VERSION(6,6,104)" "$VMX_H"; then
            success "vmx.h host_debugctl 兼容修复完成"
        else
            warning "vmx.h 修复可能未生效，请手动检查"
        fi
    else
        success "vmx.h 无需修复（已有版本保护或无 host_debugctl）"
    fi
}

# reverse_cpuid.h TSA 兼容修复：X86_FEATURE_TSA_SQ_NO/TSA_L1_NO 仅 6.6.98+ 内核才有，加 #ifdef 保护
_fix_reverse_cpuid_tsa() {
    local TOPS_BASE="$1"
    local REVERSE_CPUID="" f
    for f in \
        "$TOPS_BASE/common/kernel/include/include/arch/x86/kvm/reverse_cpuid.h" \
        "$TOPS_BASE/common/kernel/include/include_6_6/arch/x86/kvm/reverse_cpuid.h" \
        "$TOPS_BASE/os_stat/os_stat/include/include/arch/x86/kvm/reverse_cpuid.h" \
        "$TOPS_BASE/os_stat/os_stat/include/include_6_6/arch/x86/kvm/reverse_cpuid.h"; do
        [ -f "$f" ] && { REVERSE_CPUID="$f"; break; }
    done

    if [ -z "$REVERSE_CPUID" ]; then
        success "reverse_cpuid.h 不存在，无需修复"; return 0
    fi
    if ! grep -q 'KVM_X86_TRANSLATE_FEATURE(TSA_SQ_NO)' "$REVERSE_CPUID"; then
        success "reverse_cpuid.h 无 TSA 引用，无需修复"; return 0
    fi
    if grep -B1 'KVM_X86_TRANSLATE_FEATURE(TSA_SQ_NO)' "$REVERSE_CPUID" | grep -q '#ifdef X86_FEATURE_TSA_SQ_NO'; then
        success "reverse_cpuid.h TSA 兼容保护已存在，无需修复"; return 0
    fi

    info "检测到 reverse_cpuid.h 缺少 TSA_SQ_NO/TSA_L1_NO 条件编译保护，正在修复..."
    [ ! -f "${REVERSE_CPUID}.bak.install-deps" ] && cp "$REVERSE_CPUID" "${REVERSE_CPUID}.bak.install-deps"

    sed -i '/KVM_X86_TRANSLATE_FEATURE(TSA_SQ_NO)/i #ifdef X86_FEATURE_TSA_SQ_NO' "$REVERSE_CPUID"
    sed -i '/KVM_X86_TRANSLATE_FEATURE(TSA_SQ_NO)/a #endif' "$REVERSE_CPUID"
    sed -i '/KVM_X86_TRANSLATE_FEATURE(TSA_L1_NO)/i #ifdef X86_FEATURE_TSA_L1_NO' "$REVERSE_CPUID"
    sed -i '/KVM_X86_TRANSLATE_FEATURE(TSA_L1_NO)/a #endif' "$REVERSE_CPUID"

    if grep -B1 'KVM_X86_TRANSLATE_FEATURE(TSA_SQ_NO)' "$REVERSE_CPUID" | grep -q '#ifdef'; then
        success "reverse_cpuid.h TSA 兼容修复完成"
    else
        warning "reverse_cpuid.h TSA 修复可能未生效，请手动检查"
    fi
}

# ============ 主流程 ============
echo "========================================"
echo "  fs-latency skill 依赖安装"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  内核: $(uname -r)"
echo "  架构: $(uname -m)"
echo "========================================"
echo ""

if [ "$INSTALL_TOPS" = true ]; then
    install_tops
    echo ""
fi

if [ "$INSTALL_BCC" = true ]; then
    install_bcc
    echo ""
fi

if [ "$INSTALL_CFLOW" = true ]; then
    install_cflow
    echo ""
fi

if [ "$FIX_TOPS" = true ]; then
    fix_tops_compat
    echo ""
fi

echo "========================================"
echo "  依赖安装完成"
echo "========================================"
echo ""

# 汇总状态
echo "工具状态汇总:"
printf "  %-20s %s\n" "tencentos-tools:" "$(rpm -q tencentos-tools 2>/dev/null || echo '未安装')"
printf "  %-20s %s\n" "bcc-tools:" "$(rpm -q bcc-tools 2>/dev/null || echo '未安装')"
printf "  %-20s %s\n" "cflow:" "$(cflow --version 2>/dev/null | head -1 || echo '未安装')"
printf "  %-20s %s\n" "t-ops:" "$(t-ops -v 2>/dev/null || echo '未安装')"
printf "  %-20s %s\n" "biolatency:" "$(command -v biolatency &>/dev/null && echo '可用' || echo '不可用')"
printf "  %-20s %s\n" "ext4slower:" "$(command -v ext4slower &>/dev/null && echo '可用' || echo '不可用')"
printf "  %-20s %s\n" "fileslower:" "$(command -v fileslower &>/dev/null && echo '可用' || echo '不可用')"
