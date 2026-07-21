"""御界 (高级威胁检测 / NDR) raw_log 解析器 - L0 适配层

raw_log 实际样例 (来自 esSearch_20260706145614.xlsx):
    raw_log 是双层 JSON: 外层 {"raw": "<内层 JSON>", "ext": {...}}
    内层 raw 才是真正的告警载荷, 包含 attacker_ip / victim_ip / packet hex 等

设计原则:
  - L0 只还原事实, 不判断威胁
  - NAT 还原: 优先内层 JSON 的 attacker_ip / victim_ip, 缺失时回退到 OCSF src_ip/dst_ip
  - packet hex 解析: 仅做网络层头部解析 (IPv4/UDP/TCP/GRE/WireGuard 识别)
  - 异常处理: 任何字段解析失败不影响其他字段, 通过 parse_errors 记录

TODO (等用户确认产品代号):
  - 当前 PRODUCT="yujie" (基于御界拼音推断)
  - 如果官方用 NDR / NTA / InTA 缩写, 直接改下面 PRODUCT 常量即可
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# 允许独立运行 (python3 yujie_parser.py raw.json)
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ._base import BaseParser, ParseResult, ParseError

# packet 解码在同级 packet_decode.py 里, 这里直接 import
try:
    from ..packet_decode import decode_packet_hex, parse_flow_stats
except ImportError:
    # 相对 import 失败时的兜底 (单独运行)
    decode_packet_hex = None
    parse_flow_stats = None


class YujieParser(BaseParser):
    PRODUCT = "yujie"      # TODO: 御界官方英文代号确认后改这里
    VERSION = "0.1.0"

    def _do_parse(self, raw_log: str, ocsf_fields: dict) -> ParseResult:
        result = ParseResult(parser_version=self.VERSION)

        if not raw_log or not raw_log.strip():
            # raw_log 为空, 从 OCSF 兜底
            result.parse_status = "partial"
            result.parse_errors.append("raw_log 为空, 仅用 OCSF 字段")
            result.parsed = self._from_ocsf_only(ocsf_fields)
            return result

        # 1. 解析外层 JSON
        # 兼容两种结构:
        #   A) 顶层 dict (实际数据): {"attacker_ip": "...", "victim_ip": "...", "packet": "..."}
        #   B) 嵌套: {"raw": "<内层 JSON 字符串>", "ext": {...}}
        try:
            outer = json.loads(raw_log)
        except json.JSONDecodeError as e:
            raise ParseError(f"raw_log 不是合法 JSON: {e}")

        if not isinstance(outer, dict):
            raise ParseError(f"raw_log 顶层不是 dict, 实际类型: {type(outer).__name__}")

        # 2. 判断结构: 有 outer.raw 走 B 路径, 否则走 A 路径
        if "raw" in outer and isinstance(outer.get("raw"), str):
            # B 路径: 嵌套结构 (历史数据)
            try:
                payload = json.loads(outer["raw"])
            except json.JSONDecodeError as e:
                raise ParseError(f"内层 raw JSON 解析失败: {e}")
            ext = outer.get("ext", {}) or {}
            if not isinstance(ext, dict):
                ext = {}
        else:
            # A 路径: 字段全在顶层 (实际 14:56 重导数据)
            payload = outer
            ext = outer  # 字段全在顶层, 复用 ext 命名

        # 3. 主字段提取 (含 NAT 还原)
        result.parsed = self._extract_fields(payload, ext, ocsf_fields)

        # 4. packet hex 解析 (可选, 实际字段名是 packet, 也有可能是 raw_packet_hex)
        pkt_hex = self.safe_str(ext.get("packet", "")) or self.safe_str(ext.get("raw_packet_hex", ""))
        if pkt_hex and decode_packet_hex:
            try:
                pkt_info = decode_packet_hex(pkt_hex)
                result.parsed["packet_header"] = pkt_info
            except Exception as e:
                result.parse_errors.append(f"packet hex 解析失败: {type(e).__name__}: {e}")
                result.parse_status = "partial"

        # 5. flow 字段解析
        flow = ext.get("flow")
        if flow and isinstance(flow, dict):
            if parse_flow_stats:
                result.parsed["flow_stats"] = parse_flow_stats(flow)
            else:
                result.parsed["flow_stats"] = self._extract_flow(flow)

        return result

    def _extract_fields(self, payload: dict, ext: dict, ocsf: dict) -> dict:
        """提取结构化字段 - 关键: NAT 还原

        兼容两种数据形态:
          A) ext == payload (字段全在顶层, 实际数据)
          B) ext 独立 (历史嵌套结构)
        字段都从 ext 读, ext 缺时回退到 payload, 再缺时回退到 OCSF
        """
        # OCSF 透出字段 (NAT 前, 用于交叉验证)
        ocsf_src = self.safe_str(ocsf.get("src_ip")) or self.safe_str(payload.get("src_ip"))
        ocsf_dst = self.safe_str(ocsf.get("dst_ip")) or self.safe_str(payload.get("dst_ip"))

        # NAT 还原: 优先 ext.attacker_ip / ext.victim_ip
        real_attacker = self.safe_str(ext.get("attacker_ip")) or ocsf_src
        real_victim = self.safe_str(ext.get("victim_ip")) or ocsf_dst

        # GRE 封装信息 (御界 raw_log.gre 含 src_ip/dst_ip/vmip/vpcid)
        gre = ext.get("gre")
        gre_norm = None
        gre_vpcid = None
        gre_vmip = None
        if isinstance(gre, dict):
            gre_norm = {
                "src": self.safe_str(gre.get("src")) or self.safe_str(gre.get("src_ip")),
                "dst": self.safe_str(gre.get("dst")) or self.safe_str(gre.get("dst_ip")),
                "vpcid": self.safe_int(gre.get("vpcid")),
            }
            gre_vpcid = gre_norm["vpcid"]
            gre_vmip = self.safe_str(gre.get("vmip"))
        elif gre is not None:
            gre_norm = {"raw": str(gre)}

        # score (御界内部打分, 0-100)
        score = self.safe_float(ext.get("score"))

        # 时间戳 (实际数据用 timestamp 字段)
        ts_raw = self.safe_str(ext.get("timestamp")) or self.safe_str(payload.get("create_time"))

        # 规则名: 优先 OCSF event_name, 再 payload.rule_name, 再 ext.rule
        rule_name = (
            self.safe_str(ocsf.get("event_name"))
            or self.safe_str(payload.get("rule_name"))
            or self.safe_str(ext.get("rule_name"))
        )
        rule_id = (
            self.safe_str(ext.get("alert_id"))
            or self.safe_str(ext.get("original_id"))
            or self.safe_str(payload.get("rule_id"))
            or self.safe_str(payload.get("rule"))
        )

        return {
            # === OCSF 透出字段 (NAT 前, 用于追溯) ===
            "src_ip": ocsf_src or None,
            "src_port": self.safe_int(payload.get("src_port")),
            "dst_ip": ocsf_dst or None,
            "dst_port": self.safe_int(payload.get("dst_port")),

            # === NAT 还原 (L0 核心产出) ===
            "real_attacker_ip": real_attacker or None,
            "real_victim_ip": real_victim or None,
            "ip_discrepancy": bool(
                real_attacker and ocsf_src and real_attacker != ocsf_src
            ),

            # === 协议元数据 ===
            "protocol": self.safe_str(payload.get("proto")).lower() or None,
            "app_proto": self.safe_str(ext.get("app_proto")) or None,

            # === 规则 (多源聚合) ===
            "rule_id": rule_id or None,
            "rule_name": rule_name or None,
            "category": self.safe_str(ocsf.get("category")) or self.safe_str(payload.get("category")) or None,
            "subcategory": self.safe_str(ocsf.get("subcategory")) or None,

            # === 威胁评估 (透出值, L1 增强) ===
            "score": score,
            "attack_result": self.safe_str(ext.get("attack_result")) or None,
            "attack_state": self.safe_str(ext.get("attack_state")) or None,
            "confidence": self.safe_int(ext.get("confidence")),

            # === 封装链 ===
            "encapsulation": {
                "gre": gre_norm,
            },

            # === 资产关联键 (顶层, 供 asset_resolver 用) ===
            "vpcid": gre_vpcid,            # 云平台全局 VPC ID, 关联 tenant CSV 网络字段
            "gre_vmip": gre_vmip,          # GRE 内层虚拟机 IP (可选关联键)
            "asset_ip": self._normalize_asset_ip(ext.get("asset_ip")),

            # === MAC ===
            "src_mac": self.safe_str(ext.get("src_mac")) or None,
            "dst_mac": self.safe_str(ext.get("dst_mac")) or None,

            # === 时间 (L0 不归一, 保留原值 + ISO 尝试) ===
            "event_timestamp_raw": ts_raw or None,
            "event_timestamp": self._try_iso(ts_raw) if ts_raw else None,

            # === Suricata 规则详情 (如有) ===
            "alert": self._extract_alert(ext.get("alert")),
        }

    @staticmethod
    def _normalize_asset_ip(raw):
        """规范化 asset_ip 字段 (御界 raw_log 里是 list "['1.2.3.4']")"""
        if not raw:
            return None
        if isinstance(raw, list):
            return raw[0] if raw else None
        s = str(raw).strip()
        import re as _re
        m = _re.match(r"^\['?([^'\]]+)'?\]$", s)
        if m:
            return m.group(1)
        return s if s else None

    @staticmethod
    def _extract_alert(alert):
        """提取 Suricata 规则详情 (可选)"""
        if not alert or not isinstance(alert, dict):
            return None
        return {
            "signature_id": alert.get("signature_id"),
            "gid": alert.get("gid"),
            "rule_type": alert.get("rule_type"),
            "signature": alert.get("signature"),
        }

    @staticmethod
    def _extract_flow(flow: dict) -> dict:
        """从 flow 字段提取 (decode_packet_hex 不可用时兜底)"""
        return {
            "bytes_toserver": BaseParser.safe_int(flow.get("bytes_toserver"), 0),
            "bytes_toclient": BaseParser.safe_int(flow.get("bytes_toclient"), 0),
            "pkts_toserver": BaseParser.safe_int(flow.get("pkts_toserver"), 0),
            "pkts_toclient": BaseParser.safe_int(flow.get("pkts_toclient"), 0),
            "start": flow.get("start"),
            "end": flow.get("end"),
        }

    @staticmethod
    def _try_iso(ts_str):
        """尝试把字符串时间转成 ISO 8601, 失败返回 None"""
        if not ts_str:
            return None
        from datetime import datetime
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
        ):
            try:
                return datetime.strptime(ts_str, fmt).isoformat()
            except (ValueError, TypeError):
                continue
        return None

    @staticmethod
    def _from_ocsf_only(ocsf: dict) -> dict:
        """raw_log 为空时, 仅从 OCSF 提取的最小字段集"""
        return {
            "src_ip": YujieParser.safe_str(ocsf.get("src_ip")) or None,
            "src_port": YujieParser.safe_int(ocsf.get("src_port")),
            "dst_ip": YujieParser.safe_str(ocsf.get("dst_ip")) or None,
            "dst_port": YujieParser.safe_int(ocsf.get("dst_port")),
            "real_attacker_ip": YujieParser.safe_str(ocsf.get("src_ip")) or None,
            "real_victim_ip": YujieParser.safe_str(ocsf.get("dst_ip")) or None,
            "ip_discrepancy": False,
            "protocol": None,
            "app_proto": None,
            "rule_id": YujieParser.safe_str(ocsf.get("rule_id", "")) or None,
            "rule_name": YujieParser.safe_str(ocsf.get("event_name")) or None,
            "category": YujieParser.safe_str(ocsf.get("category")) or None,
            "encapsulation": {"gre": None},
            "src_mac": None,
            "dst_mac": None,
            "event_timestamp_raw": YujieParser.safe_str(ocsf.get("event_timestamp")) or None,
            "event_timestamp": YujieParser._try_iso(YujieParser.safe_str(ocsf.get("event_timestamp"))),
        }


# ==================== 独立测试入口 ====================

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: yujie_parser.py <raw_log_str_or_json_file>")
        sys.exit(1)

    arg = sys.argv[1]
    if arg.endswith(".json") and Path(arg).exists():
        raw_log = Path(arg).read_text(encoding="utf-8")
    else:
        raw_log = arg

    parser = YujieParser()
    result = parser.parse(raw_log, {"src_ip": "10.0.0.4", "dst_ip": "172.16.114.118"})
    import json as _json
    print(_json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
