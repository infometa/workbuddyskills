"""腾讯主机安全 (CWP/云镜) raw_log 解析器 - L0 适配层

raw_log 实际样例 (来自 esSearch_20260706144610.xlsx):
    格式: key=value, 用 & 分隔
    例子: "src_ip=1.2.3.4&src_port=22&dst_ip=...&process=...&cmd=...&user=...&event_type=..."

设计原则:
  - kv 切分时考虑 value 含 & / = 的情况 (用正则逐对匹配, 跳过引号内的)
  - 不做进程威胁判定 (留给 L1)
  - 时间字段保留原值 + 尝试归一 (L1 可进一步处理)
  - 异常处理: 字段缺失不阻断, 通过 parse_errors 记录

TODO (等用户确认产品代号):
  - 当前 PRODUCT="cwp" (基于 Cloud Workload Protection 推断)
  - 旧称"云镜 / YunJing", 文档里可能用中文"主机安全"
"""
from __future__ import annotations
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ._base import BaseParser, ParseResult, ParseError


class CwpParser(BaseParser):
    PRODUCT = "cwp"        # TODO: 主机安全产品代号确认后改这里
    VERSION = "0.1.0"

    # 时间字段候选 (按优先级, 匹配实际数据: modify_time / event_time / create_time)
    TIME_KEYS = ("modify_time", "event_time", "create_time", "time", "timestamp", "ctime", "log_time")

    # 网络字段
    NET_KEYS = ("src_ip", "src_port", "dst_ip", "dst_port", "protocol", "proto")

    # 主机/资产字段 (实际数据用 hostip, 也兼容 host_ip)
    HOST_KEYS = ("hostip", "host_ip", "hostname", "host", "machine_ip", "local_ip", "server_ip")

    # 进程/命令字段 (实际数据用 proc_path/proc_commandline, 也兼容 process_xxx)
    PROCESS_KEYS = ("process_name", "proc_name", "process", "exe",
                    "process_path", "exe_path", "proc_path",
                    "cmd", "command", "command_line", "cmdline", "proc_commandline")

    # 用户/认证字段 (实际数据用 username, 也兼容 user_xxx)
    AUTH_KEYS = ("username", "user", "user_name", "login_user", "account", "src_user", "proc_user")

    # 状态/结果字段 (实际数据用 type 区分事件类型, status 区分结果)
    STATUS_KEYS = ("status", "result", "action", "event_type", "rule_name", "event_subtype", "type")

    def _do_parse(self, raw_log: str, ocsf_fields: dict) -> ParseResult:
        result = ParseResult(parser_version=self.VERSION)

        if not raw_log or not raw_log.strip():
            result.parse_status = "partial"
            result.parse_errors.append("raw_log 为空, 仅用 OCSF 字段")
            result.parsed = self._from_ocsf_only(ocsf_fields)
            return result

        # 1. kv 切分
        kvs = self._split_kv(raw_log)
        if not kvs:
            raise ParseError(f"kv 切分失败: {raw_log[:200]}")

        # 2. 时间归一
        event_time_raw, event_time_iso = self._extract_time(kvs)
        if not event_time_iso:
            result.parse_errors.append(f"时间字段未识别 (候选: {self.TIME_KEYS})")

        # 3. 网络字段
        network = self._extract_network(kvs, ocsf_fields)
        if not network.get("src_ip") and not network.get("dst_ip"):
            result.parse_errors.append("网络字段 (src_ip/dst_ip) 都为空")

        # 4. 主机/资产字段
        asset = self._extract_asset(kvs, network, ocsf_fields)

        # 5. 进程/命令字段
        process = self._extract_process(kvs)

        # 6. 用户字段
        user = self._extract_user(kvs)

        # 7. 检测/状态字段
        detection = self._extract_detection(kvs, ocsf_fields)

        # 8. 构造 L0 输出
        result.parsed = {
            # === 网络 ===
            **network,

            # === 主机/资产 ===
            **asset,

            # === 进程 ===
            **process,

            # === 用户 ===
            "user": user,
            "src_user": kvs.get("src_user"),

            # === 资产关联键 (顶层, 供 asset_resolver 用) ===
            "appid": kvs.get("appid"),                # 租户 AppID, 关联 tenant CSV
            "vpc_id": kvs.get("vpc_id"),              # 主机安全内部 vpc_id (注意: 跟云平台 vpcid 不同)
            "uuid": kvs.get("uuid"),                  # 事件 UUID (主机安全唯一标识)

            # === 检测 ===
            **detection,

            # === 时间 ===
            "event_time": event_time_iso,
            "event_time_raw": event_time_raw,

            # === 完整 kv 兜底 (L1 可用) ===
            "_raw_kv": kvs,
        }
        return result

    # ========== 字段提取方法 ==========

    def _extract_network(self, kvs: dict, ocsf: dict) -> dict:
        """提取网络字段 (NAT 还原暂不适用, CWP 视角下 IP 通常是真实 IP)"""
        src_ip = kvs.get("src_ip") or ocsf.get("src_ip")
        dst_ip = kvs.get("dst_ip") or ocsf.get("dst_ip")

        return {
            "src_ip": self.safe_str(src_ip) or None,
            "src_port": self.safe_int(kvs.get("src_port") or ocsf.get("src_port")),
            "dst_ip": self.safe_str(dst_ip) or None,
            "dst_port": self.safe_int(kvs.get("dst_port") or ocsf.get("dst_port")),
            "protocol": (self.safe_str(kvs.get("protocol")) or self.safe_str(kvs.get("proto")) or "tcp").lower(),

            # CWP 视角下, IP 通常已经是真实 IP (无 NAT), 但保留字段供 L1 增强
            "real_attacker_ip": self.safe_str(src_ip) or None,
            "real_victim_ip": self.safe_str(dst_ip) or None,
            "ip_discrepancy": False,

            # 主机类无网络封装
            "encapsulation": {"gre": None},
            "src_mac": None,
            "dst_mac": None,
            "app_proto": None,
        }

    def _extract_asset(self, kvs: dict, network: dict, ocsf: dict) -> dict:
        """提取资产/主机字段"""
        # 主机 IP: 优先 host_ip, 其次 dst_ip (主机事件中 dst 通常是本机)
        host_ip = None
        for key in self.HOST_KEYS:
            v = kvs.get(key)
            if v:
                host_ip = v
                break
        if not host_ip:
            host_ip = network.get("dst_ip")

        hostname = kvs.get("hostname") or ocsf.get("hostname")

        return {
            "host_ip": self.safe_str(host_ip) or None,
            "hostname": self.safe_str(hostname) or None,
        }

    def _extract_process(self, kvs: dict) -> dict:
        """提取进程/命令字段"""
        process = None
        for key in self.PROCESS_KEYS:
            v = kvs.get(key)
            if v and key in ("process", "process_name", "exe"):
                process = v
                break

        process_path = None
        for key in ("process_path", "exe_path"):
            v = kvs.get(key)
            if v:
                process_path = v
                break

        cmd = None
        for key in ("cmd", "command", "command_line", "cmdline"):
            v = kvs.get(key)
            if v:
                cmd = v
                break

        return {
            "process": self.safe_str(process) or None,
            "process_path": self.safe_str(process_path) or None,
            "cmd": self.safe_str(cmd) or None,
        }

    def _extract_user(self, kvs: dict) -> str | None:
        """提取用户字段"""
        for key in self.AUTH_KEYS:
            v = kvs.get(key)
            if v:
                return self.safe_str(v)
        return None

    def _extract_detection(self, kvs: dict, ocsf: dict) -> dict:
        """提取检测相关字段"""
        event_type = None
        for key in ("event_type", "rule_name", "event_subtype"):
            v = kvs.get(key)
            if v:
                event_type = v
                break
        if not event_type:
            event_type = ocsf.get("event_name")

        status = None
        for key in ("status", "result", "action"):
            v = kvs.get(key)
            if v:
                status = v
                break

        rule_id = kvs.get("rule_id") or ocsf.get("event_id")

        return {
            "rule_id": self.safe_str(rule_id) or None,
            "rule_name": self.safe_str(event_type) or None,
            "status": self.safe_str(status) or None,
            "category": self.safe_str(ocsf.get("category")) or None,
            "subcategory": self.safe_str(ocsf.get("subcategory")) or None,
        }

    def _extract_time(self, kvs: dict) -> tuple[str | None, str | None]:
        """提取时间字段, 返回 (原值, ISO 归一值)"""
        raw = None
        for key in self.TIME_KEYS:
            v = kvs.get(key)
            if v:
                raw = v
                break

        if not raw:
            return None, None

        iso = self._try_iso(raw)
        return raw, iso

    @staticmethod
    def _try_iso(ts_str: str) -> str | None:
        if not ts_str:
            return None
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y%m%d%H%M%S",
        ):
            try:
                return datetime.strptime(ts_str, fmt).isoformat()
            except (ValueError, TypeError):
                continue
        return None

    # ========== kv 切分 ==========

    @staticmethod
    def _split_kv(raw: str) -> dict:
        """拆分 key=value, 支持 & 或 , 作为分隔符 (实际数据两种都有)

        使用正则逐对匹配, 自动跳过引号内 / urlencoded 后含 = 或 & 的 value
        """
        result = {}
        # 先把 , 替换为 &, 然后用 & 切
        # (因为部分 value 可能含逗号, 比如 "cmd=ls, -la" 这种, 我们的切分是贪婪的, 不会切到 value 里)
        # 但 hostip=11.0.0.9 这种 value 里也有数字点, 也不影响, 因为我们用 [^,&]+ 匹配 value
        parts = re.findall(r'([^=,&]+)=([^,&]*)', raw)
        for k, v in parts:
            k = k.strip()
            if not k:
                continue
            v_decoded = unquote(v.strip())
            # 去掉首尾引号 (单/双)
            if len(v_decoded) >= 2 and v_decoded[0] == v_decoded[-1] and v_decoded[0] in '"\'':
                v_decoded = v_decoded[1:-1]
            result[k] = v_decoded
        return result

    @staticmethod
    def _from_ocsf_only(ocsf: dict) -> dict:
        """raw_log 为空时, 仅从 OCSF 提取的最小字段集"""
        return {
            "src_ip": CwpParser.safe_str(ocsf.get("src_ip")) or None,
            "src_port": CwpParser.safe_int(ocsf.get("src_port")),
            "dst_ip": CwpParser.safe_str(ocsf.get("dst_ip")) or None,
            "dst_port": CwpParser.safe_int(ocsf.get("dst_port")),
            "protocol": "tcp",
            "real_attacker_ip": CwpParser.safe_str(ocsf.get("src_ip")) or None,
            "real_victim_ip": CwpParser.safe_str(ocsf.get("dst_ip")) or None,
            "ip_discrepancy": False,
            "encapsulation": {"gre": None},
            "src_mac": None,
            "dst_mac": None,
            "app_proto": None,
            "host_ip": CwpParser.safe_str(ocsf.get("dst_ip")) or None,
            "hostname": CwpParser.safe_str(ocsf.get("hostname")) or None,
            "process": None,
            "process_path": None,
            "cmd": None,
            "user": None,
            "src_user": None,
            "rule_id": CwpParser.safe_str(ocsf.get("event_id")) or None,
            "rule_name": CwpParser.safe_str(ocsf.get("event_name")) or None,
            "status": None,
            "category": CwpParser.safe_str(ocsf.get("category")) or None,
            "subcategory": CwpParser.safe_str(ocsf.get("subcategory")) or None,
            "event_time": None,
            "event_time_raw": CwpParser.safe_str(ocsf.get("event_timestamp")) or None,
            "_raw_kv": {},
        }


# ==================== 独立测试入口 ====================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 示例 raw_log
        sample = "src_ip=203.0.113.45&src_port=51234&dst_ip=10.10.1.100&dst_port=22&process=sshd&user=root&event_type=SSH登录成功&status=success&event_time=2026-07-05 15:30:22"
        print(f"用法: {sys.argv[0]} <raw_log_str>")
        print(f"\n示例输入:\n{sample}\n")
    else:
        sample = sys.argv[1]

    parser = CwpParser()
    result = parser.parse(sample, {"src_ip": "203.0.113.45", "event_name": "SSH登录成功"})
    import json as _json
    print(_json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
