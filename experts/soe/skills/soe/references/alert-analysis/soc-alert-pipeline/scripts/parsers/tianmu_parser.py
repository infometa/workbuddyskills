"""天幕 (安全治理) 阻断日志解析器 - L0 适配层

天幕 xlsx 直出格式 (非 SOC 导出, 无 raw_log):
    列头 (中文):
      命中规则 / 首次告警时间 / 最新告警时间 / 告警来源 / 状态 /
      累计阻断次数 / 协议类型 / IP格式 / 源IP / 源端口 / HOST / CGI /
      目标IP / 目标端口

数据性质:
    - 每行是一个 (规则 + 源IP + 目标IP) 的聚合阻断统计, 不是单次请求
    - "累计阻断次数" 表示该组合被阻断了多少次
    - "首次告警时间" / "最新告警时间" 是时间范围
    - HOST / CGI 在纯 TCP 阻断时为空 (非 HTTP 协议)

设计原则:
  - 天幕无 raw_log, 数据直接在 row dict (作为 ocsf_fields 传入)
  - 中文列头映射成英文内部字段, 保留原值
  - 网络字段对齐 event-schema.md 的 network 结构
  - 阻断动作标记 action="block", action_result="blocked"
  - 聚合标记 is_aggregated=True, block_count 保留
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path

if __name__ == "__main__ and __package__ is None":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ._base import BaseParser, ParseResult, ParseError


class TianmuParser(BaseParser):
    """天幕安全治理阻断日志解析器

    与 yujie/cwp 不同: 天幕 xlsx 是直出格式, 无 raw_log 列.
    数据已经是结构化的 (中文列头), parser 直接做字段映射 + 归一化.
    """
    PRODUCT = "tianmu"
    VERSION = "0.1.0"

    # 天幕中文列头 → L0 内部字段名
    COLUMN_MAP = {
        "命中规则":     "rule_id",
        "首次告警时间":  "first_alert_time",
        "最新告警时间":  "last_alert_time",
        "告警来源":     "alert_source",
        "状态":         "status",
        "累计阻断次数":  "block_count",
        "协议类型":     "protocol",
        "IP格式":       "ip_format",
        "源IP":         "src_ip",
        "源端口":       "src_port",
        "HOST":         "http_host",
        "CGI":          "http_uri",
        "目标IP":       "dst_ip",
        "目标端口":     "dst_port",
    }

    # 天幕识别关键词 (出现在列头中)
    IDENTIFIER_COLS = ("命中规则", "累计阻断次数", "告警来源")

    def _do_parse(self, raw_log: str, ocsf_fields: dict) -> ParseResult:
        """解析天幕行.

        Args:
            raw_log: 天幕模式下始终为空字符串
            ocsf_fields: 实际是 xlsx 行 dict (中文列头 → 值)
        """
        result = ParseResult(parser_version=self.VERSION)
        row = ocsf_fields or {}

        if not row:
            raise ParseError("天幕行数据为空 (row dict is None/empty)")

        # 1. 中文列头 → 内部字段
        mapped: dict = {}
        for cn, internal in self.COLUMN_MAP.items():
            val = row.get(cn)
            if val is not None and val != "":
                mapped[internal] = val

        # 2. 类型归一
        mapped["src_port"] = self.safe_int(mapped.get("src_port"))
        mapped["dst_port"] = self.safe_int(mapped.get("dst_port"))
        mapped["block_count"] = self.safe_int(mapped.get("block_count"), 0) or 0

        # 3. 时间归一
        first_iso = self._try_iso(mapped.get("first_alert_time"))
        last_iso = self._try_iso(mapped.get("last_alert_time"))
        # event_time 取最新告警时间 (更接近事件发生时刻)
        mapped["event_time"] = last_iso or first_iso
        mapped["event_time_raw"] = mapped.get("last_alert_time") or mapped.get("first_alert_time")

        # 4. 网络字段 (对齐 event-schema.md network 结构)
        protocol = self.safe_str(mapped.get("protocol")).lower() or "tcp"
        src_ip = self.safe_str(mapped.get("src_ip")) or None
        dst_ip = self.safe_str(mapped.get("dst_ip")) or None

        mapped["protocol"] = protocol
        mapped["real_attacker_ip"] = src_ip
        mapped["real_victim_ip"] = dst_ip
        mapped["ip_discrepancy"] = False
        mapped["encapsulation"] = {"gre": None}
        mapped["src_mac"] = None
        mapped["dst_mac"] = None
        mapped["app_proto"] = "http" if mapped.get("http_host") else None

        # 5. 阻断动作 (天幕核心特征: 已阻断)
        mapped["action"] = "block"
        mapped["action_result"] = "blocked"

        # 6. 聚合标记
        mapped["is_aggregated"] = True
        mapped["event_type"] = "block_log"

        # 7. 检测字段
        mapped["rule_name"] = mapped.get("rule_id")  # 天幕规则 ID 即规则名
        mapped["category"] = "network_security"
        mapped["subcategory"] = "block_action"

        # 8. 校验
        if not src_ip and not dst_ip:
            result.parse_status = "partial"
            result.parse_errors.append("源IP 和 目标IP 都为空")
        if not mapped.get("rule_id"):
            result.parse_status = "partial"
            result.parse_errors.append("命中规则为空")

        result.parsed = mapped
        return result

    # ========== 工具 ==========

    @staticmethod
    def _try_iso(ts_str: str | None) -> str | None:
        """尝试把天幕时间字符串归一成 ISO8601

        天幕时间样例: 2026-07-07T23:40:01-03:00 (带时区偏移)
        """
        if not ts_str:
            return None
        ts = str(ts_str).strip()
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
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
        # 示例: 模拟一行天幕数据
        sample_row = {
            "命中规则": "GB00002",
            "首次告警时间": "2026-06-24T05:47:52-03:00",
            "最新告警时间": "2026-07-07T23:40:01-03:00",
            "告警来源": "黑名单",
            "状态": "已拦截（已发送阻断报文）",
            "累计阻断次数": "141",
            "协议类型": "TCP",
            "IP格式": "IPv4",
            "源IP": "223.71.46.114",
            "源端口": "44066",
            "HOST": "",
            "CGI": "",
            "目标IP": "109.244.106.31",
            "目标端口": "80",
        }
        print(f"用法: {sys.argv[0]} <json_row_str>")
        print(f"\n示例输入 (天幕行 dict):\n{sample_row}\n")
        parser = TianmuParser()
        result = parser.parse("", sample_row)
    else:
        import json as _json
        row = _json.loads(sys.argv[1])
        parser = TianmuParser()
        result = parser.parse("", row)

    import json as _json
    print(_json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
