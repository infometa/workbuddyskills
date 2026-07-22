"""御界 (高级威胁检测/NDR) 直出格式解析器 - L0 适配层

御界直出格式 (御界控制台单独导出, 非 SOC 中转, 无 raw_log):
    列头 (EVE/Suricata 风格, 17 字段, 英文带点号嵌套):
      timestamp / event_type / attack_result / alert.signature /
      src_ip / src_port / dst_ip / dst_port / app_proto /
      http.url / http.status / http.hostname /
      alert.signature_id / score /
      fileinfo.filetype / fileinfo.filename / sub_type

数据性质:
    - 每行是一条告警事件 (非聚合)
    - 字段是 EVE (Extensible Event Format) 扁平化导出, 御界底层基于 Suricata
    - 与 SOC 导出 (含 raw_log 双层 JSON) 不同: 已拆解成扁平列, 丢失结构化字段
    - 丢失的关键字段: attacker_ip / victim_ip (NAT 还原) / packet (包解码) /
                      gre (封装) / flow (流统计)

设计原则 (对齐 waf_parser / tianmu_parser 直出范式):
  - 无 raw_log, 数据直接在 row dict (作为 ocsf_fields 传入)
  - EVE 字段名 (带点号) 映射成 L0 内部扁平字段
  - NAT 还原字段降级: real_attacker=src_ip, real_victim=dst_ip (无 attacker_ip/victim_ip)
  - 包解码/封装链/流统计字段为 None (直出格式无这些结构化字段)
  - 时间归一: timestamp → ISO8601

L0 与 L1 的分工:
  - L0 (本 parser): 字段映射 + 类型归一 + 时间归一, 不做威胁判断
  - L1 (yujie-analyzer): 由于直出格式丢失 NAT/包/流字段, L1 的 NAT 还原/
    C2 Beacon/隧道检测能力受限, 但仍可基于 rule_name/score/attack_result/
    五元组做威胁判定

注意:
  - 御界 SOC 导出 (含 raw_log) 走 yujie_parser.py, 能力完整 (NAT 还原+包解码+流统计)
  - 御界直出 (本 parser) 是降级模式, 仅做字段映射, L1 部分能力不可用
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ._base import BaseParser, ParseResult, ParseError


# 御界直出 EVE 风格列头 → L0 内部字段名
COLUMN_MAP = {
    "timestamp":           "event_time_raw",
    "event_type":          "event_type",
    "attack_result":       "attack_result",
    "alert.signature":     "rule_name",
    "alert.signature_id":  "rule_id",
    "src_ip":              "src_ip",
    "src_port":            "src_port",
    "dst_ip":              "dst_ip",
    "dst_port":            "dst_port",
    "app_proto":           "app_proto",
    "http.url":            "http_uri",
    "http.status":         "http_status",
    "http.hostname":       "http_hostname",
    "score":               "score",
    "fileinfo.filetype":   "file_type",
    "fileinfo.filename":   "file_name",
    "sub_type":            "sub_type",
}

# 御界直出识别关键词 (EVE 风格带点号字段名, 与中文列头产品不冲突)
# alert.signature + fileinfo.filename 组合最独特 (其他产品不会有这种字段名)
IDENTIFIER_COLS = (
    "alert.signature",
    "alert.signature_id",
    "fileinfo.filename",
    "fileinfo.filetype",
)


class YujieFlatParser(BaseParser):
    """御界直出格式解析器 (EVE 扁平字段, 无 raw_log)

    与 yujie_parser (SOC 导出 raw_log) 的差异:
      - 数据已是扁平结构 (EVE 字段), 无需 JSON 解析
      - 丢失 attacker_ip/victim_ip → 无法 NAT 还原, real_attacker=src_ip
      - 丢失 packet hex → 无法包头解码
      - 丢失 gre/flow → 无法封装链识别/流统计
      - L1 (yujie-analyzer) 的 C2 Beacon/隧道/横向移动检测能力受限

    L0 输出对齐 yujie_parser 的字段集, 缺失字段置 None, 供 L1 降级处理.
    """
    PRODUCT = "yujie_flat"
    VERSION = "0.1.0"

    # 供 registry.detect_product 识别用
    IDENTIFIER_COLS = IDENTIFIER_COLS

    def _do_parse(self, raw_log: str, ocsf_fields: dict) -> ParseResult:
        """解析御界直出行.

        Args:
            raw_log: 御界直出模式下始终为空字符串 (数据在 ocsf_fields)
            ocsf_fields: 御界直出 xlsx 行 dict (EVE 字段名 → 值)
        """
        result = ParseResult(parser_version=self.VERSION)
        row = ocsf_fields or {}

        if not row:
            raise ParseError("御界直出行数据为空 (row dict is None/empty)")

        # 1. EVE 字段 → 内部字段
        mapped: dict = {}
        for eve_name, internal in COLUMN_MAP.items():
            val = row.get(eve_name)
            if val is not None and val != "":
                if isinstance(val, str):
                    val = val.strip()
                mapped[internal] = val

        # 2. 类型归一
        mapped["src_port"] = self.safe_int(mapped.get("src_port"))
        mapped["dst_port"] = self.safe_int(mapped.get("dst_port"))
        mapped["http_status"] = self.safe_int(mapped.get("http_status"))
        mapped["score"] = self.safe_float(mapped.get("score"))

        # 3. 时间归一 (timestamp → ISO8601)
        ts_raw = self.safe_str(mapped.get("event_time_raw"))
        mapped["event_time"] = self._try_iso(ts_raw) if ts_raw else None
        # 对齐 yujie_parser 输出字段名
        mapped["event_timestamp"] = mapped.get("event_time")
        mapped["event_timestamp_raw"] = ts_raw

        # 4. 网络字段 (对齐 event-schema.md network 结构)
        src_ip = self.safe_str(mapped.get("src_ip")) or None
        dst_ip = self.safe_str(mapped.get("dst_ip")) or None
        app_proto = self.safe_str(mapped.get("app_proto")).lower() or None

        # 协议推断: app_proto=http → tcp, 其他保留原值
        mapped["protocol"] = "tcp" if app_proto == "http" else app_proto

        # 5. NAT 还原 (直出格式无 attacker_ip/victim_ip, 降级: real=ocsf)
        #    标记 ip_discrepancy=False, 并在 parse_errors 注明降级原因
        mapped["real_attacker_ip"] = src_ip
        mapped["real_victim_ip"] = dst_ip
        mapped["ip_discrepancy"] = False
        mapped["encapsulation"] = {"gre": None}
        mapped["src_mac"] = None
        mapped["dst_mac"] = None

        # 6. 御界 raw_log 专属字段 (直出格式丢失, 置 None 供 L1 降级判断)
        mapped["packet_header"] = None
        mapped["flow_stats"] = None
        mapped["vpcid"] = None
        mapped["gre_vmip"] = None
        mapped["asset_ip"] = None

        # 7. Suricata alert 详情 (直出格式已拆成 alert.signature/alert.signature_id)
        if mapped.get("rule_name") or mapped.get("rule_id"):
            mapped["alert"] = {
                "signature_id": mapped.get("rule_id"),
                "signature": mapped.get("rule_name"),
                "gid": None,
                "rule_type": None,
            }
        else:
            mapped["alert"] = None

        # 8. 聚合标记 (御界直出是逐条记录, 非聚合)
        mapped["is_aggregated"] = False

        # 9. 检测字段 (对齐 event-schema.md detection)
        mapped["category"] = "network_security"
        mapped["subcategory"] = mapped.get("sub_type") or None
        mapped["confidence"] = None
        mapped["attack_state"] = None

        # 10. 降级提示 (L1 据此知道 NAT/包/流能力不可用)
        #     标记 partial, 因为缺失 NAT/包/流等结构化字段
        result.parse_status = "partial"
        result.parse_errors.append(
            "御界直出格式: 缺失 attacker_ip/victim_ip/packet/gre/flow, "
            "NAT 还原/包解码/流统计能力不可用 (L1 降级模式)"
        )

        # 11. 校验
        if not src_ip and not dst_ip:
            result.parse_errors.append("src_ip 和 dst_ip 都为空")
        if not mapped.get("rule_name"):
            result.parse_errors.append("alert.signature (规则名) 为空")

        result.parsed = mapped
        return result

    # ========== 工具 ==========

    @staticmethod
    def _try_iso(ts_str):
        """尝试把 timestamp 字符串归一成 ISO8601

        御界直出 timestamp 样例: 2026-06-16 11:04:42 (空格分隔)
        """
        if not ts_str:
            return None
        ts = str(ts_str).strip()
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y/%m/%d %H:%M:%S",
        ):
            try:
                return datetime.strptime(ts, fmt).isoformat()
            except (ValueError, TypeError):
                continue
        return ts  # 无法解析时返回原值


# ==================== 独立测试入口 ====================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 示例: 模拟一行御界直出数据
        sample_row = {
            "timestamp": "2026-06-16 14:20:10",
            "event_type": "alert",
            "attack_result": "成功",
            "alert.signature": "webshell antSword 通信行为",
            "src_ip": "0031:0000:0000:0000:0000:0012:0054:0086",
            "src_port": "54321",
            "dst_ip": "0031:0000:0000:0000:0000:0012:0054:0037",
            "dst_port": "80",
            "app_proto": "http",
            "http.url": "/handle_post.php",
            "http.status": "200",
            "http.hostname": "123.207.136.252",
            "alert.signature_id": "2100001",
            "score": "96",
            "fileinfo.filetype": "",
            "fileinfo.filename": "",
            "sub_type": "",
        }
        print(f"用法: {sys.argv[0]} <json_row_str>")
        print(f"\n示例输入 (御界直出行 dict):\n{sample_row}\n")
        parser = YujieFlatParser()
        result = parser.parse("", sample_row)
    else:
        import json as _json
        row = _json.loads(sys.argv[1])
        parser = YujieFlatParser()
        result = parser.parse("", row)

    import json as _json
    print(_json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
