# /// script
# dependencies = []
# ///
"""
本机公网 IP 探测脚本（tencent-es-control-panel MCP 版唯一本地脚本）

⚠️ 本脚本【零云 API 调用】，不读取任何腾讯云凭证，不做任何签名。
   它只做一件事：按目标集群所在地域，选择正确的公网 IP 探测服务，拿到本机出口 IP。

为什么必须保留这个脚本：
  MCP 服务端运行在云侧，无法感知用户【本机】的公网出口 IP，
  而 Kibana 报「很抱歉，你没有权限访问」的修复恰恰需要这个 IP。

为什么要按地域选路（核心设计）：
  用户访问 Kibana 的浏览器出口 IP 取决于路由策略：
    - 国内集群（ap-guangzhou 等）：用户通常浏览器直连 → 出口是国内 ISP IP
    - 海外集群（ap-hongkong / ap-singapore 等）：用户通常走代理 → 出口是代理 IP
  若对国内集群误用境外探测服务，本机走代理时会拿到【代理出口 IP】
  （典型如腾讯云海外段 43.x.x.x），与用户浏览器直连 Kibana 的真实出口不匹配，
  加进白名单后 API 返回"成功"但 Kibana 依旧 403，且极难排查。

用法：
  python3 detect_my_ip.py --region ap-guangzhou
  python3 detect_my_ip.py --region ap-singapore --output text
"""

import argparse
import ipaddress
import json
import re
import sys
import urllib.error
import urllib.request

# ============================================================
# 安全约束：禁止「全部放开」类地址（与 SKILL.md 硬性约束一致）
# ============================================================

FORBIDDEN_WIDE_OPEN_LITERALS = {
    "0.0.0.0",
    "0.0.0.0/0",
    "::",
    "::/0",
    "*",
    "any",
    "all",
}


def error_exit(msg: str):
    """统一错误输出到 stderr 并以非零退出码终止"""
    sys.stderr.write(json.dumps({"error": msg}, ensure_ascii=False) + "\n")
    sys.exit(1)


def validate_ip_safety(ip: str) -> str:
    """
    校验探测到的 IP：
      1. 不能是「全部放开」字面值
      2. 不能是 /0 掩码的 CIDR
      3. 必须是合法 IPv4 / IPv6 地址
      4. 不能是私网 / 环回 / 链路本地地址（探测服务异常时可能返回内网 IP）

    返回规范化后的 IP 字符串。校验失败直接 error_exit。
    """
    ip = (ip or "").strip()
    if not ip:
        error_exit("探测到的 IP 为空")

    if ip.lower() in FORBIDDEN_WIDE_OPEN_LITERALS:
        error_exit(
            f"探测结果异常（{ip}）：等同于全部放开，禁止用于白名单。"
            f"请手动确认本机公网 IP 后重试。"
        )

    if "/" in ip:
        try:
            net = ipaddress.ip_network(ip, strict=False)
        except ValueError as e:
            error_exit(f"非法的 IP/CIDR 格式：{ip}（{e}）")
        if net.prefixlen == 0:
            error_exit(f"探测结果异常（{ip}）：掩码 /0 等同于全部放开，禁止使用。")
        return str(net)

    try:
        addr = ipaddress.ip_address(ip)
    except ValueError as e:
        error_exit(f"非法的 IP 格式：{ip}（{e}）")

    # 公网 IP 校验：探测服务异常或被网关劫持时可能返回内网地址
    if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_unspecified:
        error_exit(
            f"探测到的是非公网地址（{ip}）：可能探测服务被劫持或本机无公网出口。"
            f"请在浏览器访问 https://myip.ipip.net 自查公网 IP 后手动指定。"
        )

    return str(addr)


# ============================================================
# 地域识别
# ============================================================

# 腾讯云国内地域（含金融云专区）
CN_REGIONS = {
    "ap-guangzhou", "ap-guangzhou-open",
    "ap-shanghai", "ap-shanghai-fsi",
    "ap-beijing", "ap-beijing-fsi",
    "ap-chengdu",
    "ap-chongqing",
    "ap-nanjing",
    "ap-shenzhen-fsi",
}

# 明确的海外地域前缀（用于地域列表未列全时兜底识别）
OVERSEAS_REGION_PREFIXES = (
    "ap-hongkong", "ap-singapore", "ap-tokyo", "ap-seoul",
    "ap-bangkok", "ap-jakarta", "ap-mumbai",
    "na-",   # 北美：na-ashburn, na-siliconvalley, na-toronto
    "eu-",   # 欧洲：eu-frankfurt, eu-moscow
    "sa-",   # 南美：sa-saopaulo
)

# 国内 IP 探测服务（不被防火墙阻断，能拿真实国内出口 IP）
CN_IP_ENDPOINTS = [
    "https://myip.ipip.net",           # 中文文本格式，需正则提取
    "https://4.ipw.cn",                # 纯 IP 文本
    "https://ddns.oray.com/checkip",   # HTML 格式，需正则提取
]

# 境外 IP 探测服务（走代理时返回代理出口 IP）
OVERSEAS_IP_ENDPOINTS = [
    "https://ifconfig.me/ip",
    "https://api.ipify.org",
    "https://ipv4.icanhazip.com",
]


def is_china_region(region: str) -> bool:
    """
    判断地域是否为国内地域。
    策略：
      1. 命中已知国内地域列表 → True
      2. 命中已知海外前缀 → False
      3. 其他未知地域 → True（保守策略，避免误用境外探测服务）
    """
    region = (region or "").lower().strip()
    if region in CN_REGIONS:
        return True
    if any(region.startswith(p) for p in OVERSEAS_REGION_PREFIXES):
        return False
    return True


def detect_public_ip(region: str, timeout: int = 5) -> dict:
    """
    按集群地域选择 IP 探测服务，返回结果 dict。
    全部端点失败则 error_exit。
    """
    is_cn = is_china_region(region)
    endpoints = CN_IP_ENDPOINTS if is_cn else OVERSEAS_IP_ENDPOINTS
    region_kind = "国内" if is_cn else "海外"
    source_hint = "国内直连出口" if is_cn else "境外/代理出口"

    attempts = []
    for url in endpoints:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace").strip()
            # 从响应中提取第一个合法 IPv4
            m = re.search(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", raw)
            if not m:
                attempts.append(f"{url} → 响应无法解析为 IP: {raw[:80]}")
                continue
            ip = validate_ip_safety(m.group(1))
            return {
                "ip": ip,
                "region": region,
                "region_kind": region_kind,
                "endpoint": url,
                "source": (
                    f"集群地域 {region} 识别为{region_kind}地域，"
                    f"使用{source_hint}（via {url}）"
                ),
                "failed_attempts": attempts,
            }
        except (urllib.error.URLError, urllib.error.HTTPError,
                TimeoutError, OSError) as e:
            attempts.append(f"{url} → {e}")
            continue

    error_exit(
        f"自动探测本机公网 IP 失败（{region_kind}探测服务全部不可达）。\n"
        f"尝试记录：\n  " + "\n  ".join(attempts) + "\n"
        f"请在浏览器访问 https://myip.ipip.net 或 https://ip138.com 查看公网 IP 后手动指定。"
    )


def main():
    parser = argparse.ArgumentParser(
        description="按集群地域智能探测本机公网 IP（零云 API 调用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 国内集群（使用国内探测服务，拿真实国内直连出口 IP）
  python3 scripts/detect_my_ip.py --region ap-guangzhou

  # 海外集群（使用境外探测服务，走代理时拿代理出口 IP）
  python3 scripts/detect_my_ip.py --region ap-singapore

  # 仅输出 IP，便于直接取用
  python3 scripts/detect_my_ip.py --region ap-guangzhou --output text

说明：
  - 本脚本不调用任何腾讯云 API，不读取凭证
  - 探测结果需交由 UpdateEsAcl MCP tool 提交（先读现有白/黑名单，增量修改后同时回传）
        """,
    )
    parser.add_argument("--region", required=True,
                        help="目标集群地域，如 ap-guangzhou。决定使用国内还是海外探测服务")
    parser.add_argument("--output", choices=["json", "text"], default="json",
                        help="输出格式：json=完整信息（默认），text=仅 IP")
    parser.add_argument("--timeout", type=int, default=5,
                        help="单个探测服务超时秒数，默认 5")

    args = parser.parse_args()
    result = detect_public_ip(args.region.strip(), args.timeout)

    if args.output == "text":
        print(result["ip"])
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
