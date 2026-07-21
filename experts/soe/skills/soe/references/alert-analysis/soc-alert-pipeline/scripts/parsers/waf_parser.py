"""腾讯云 WAF 攻击日志解析器 - L0 适配层

WAF 攻击日志格式 (腾讯云控制台导出, 中文 CSV/XLSX):
    列头 (中文, 12 字段):
      攻击IP / 被攻击域名 / URI / 方法 / 攻击类型 / 攻击内容 /
      UserAgent / APPID / uuid / 动作 / 风险等级 / 攻击时间

数据性质:
    - 每行是一次 HTTP 请求级的攻击检测记录 (非聚合)
    - "攻击时间" 是毫秒级 epoch (13 位数字)
    - "动作" 取值: 拦截 / 观察 / 放行 (中文)
    - "风险等级" 取值: 高危 / 中危 / 低危 (中文)

设计原则 (对齐 tianmu_parser, 因为 WAF 也是无 raw_log 的直出格式):
  - WAF 无 raw_log, 数据直接在 row dict (作为 ocsf_fields 传入)
  - 中文列头映射成英文内部字段, 保留原值
  - 网络字段对齐 event-schema.md 的 network 结构
  - 保留 WAF 独有字段 (域名/URI/UA/攻击内容/风险等级), 供 L1 深度分析
  - 安全约束: 不在 L0 输出 payload 原文 (攻击内容只标记 has_obfuscation, 不透出)

L0 与 L1 的分工:
  - L0 (本 parser): 字段映射 + 类型归一 + 时间归一, 不做威胁判断
  - L1 (waf-log-analyzer/l1_waf_analyze.py): 真实性研判 / 配置异常 / 扫描器指纹 / 处置建议
"""
from __future__ import annotations
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ._base import BaseParser, ParseResult, ParseError


# WAF 中文列头 (严格匹配, 与 analyzer.py EXPECTED_HEADER 一致)
WAF_HEADER = [
    "攻击IP", "被攻击域名", "URI", "方法", "攻击类型",
    "攻击内容", "UserAgent", "APPID", "uuid", "动作",
    "风险等级", "攻击时间",
]

# 中文列头 → L0 内部字段名
COLUMN_MAP = {
    "攻击IP":       "src_ip",
    "被攻击域名":    "victim_domain",
    "URI":          "http_uri",
    "方法":         "http_method",
    "攻击类型":      "rule_name",
    "攻击内容":      "attack_payload",      # L0 保留, L1 决定是否透出 (安全约束)
    "UserAgent":    "user_agent",
    "APPID":        "appid",
    "uuid":         "event_uuid",
    "动作":         "action_raw",
    "风险等级":      "risk_level_raw",
    "攻击时间":      "event_time_raw",
}

# WAF 识别关键词 (出现在列头中)
IDENTIFIER_COLS = ("攻击IP", "被攻击域名", "攻击类型", "风险等级", "攻击时间")

# 动作中文 → 内部枚举 (对齐 cfw 的 action 枚举)
ACTION_MAP = {
    "拦截": "block",
    "观察": "observe",
    "放行": "allow",
    "人机验证": "challenge",
    "重定向": "redirect",
}

# 风险等级中文 → severity 枚举 (对齐 event-schema.md detection.severity)
SEVERITY_MAP = {
    "高危": "high",
    "中危": "medium",
    "低危": "low",
    "严重": "critical",
    "信息": "informational",
}

# 混淆特征 (与 analyzer.py OBFUSCATION_HINTS 对齐, L0 只标记不展开)
OBFUSCATION_RE = re.compile(
    r"(%[0-9a-fA-F]{2}.*%[0-9a-fA-F]{2}|/\*!|"
    r"&#x?\d+;|\\u00[0-9a-f]{2}|"
    r"char\s*\(|0x[0-9a-fA-F]{4,}|base64,|"
    r"concat\s*\(|substring\s*\(|"
    r"%[uU][0-9a-fA-F]{4})",
)


class WafParser(BaseParser):
    """腾讯云 WAF 攻击日志解析器

    与 tianmu 类似: WAF 导出是直出格式 (CSV/XLSX, 无 raw_log).
    数据已经是结构化的 (中文列头), parser 做字段映射 + 归一化.

    L0 输出的 parsed 字段 (扁平 dict, 对齐其他 parser):
      - src_ip / victim_domain / http_uri / http_method / rule_name
      - user_agent / appid / event_uuid
      - action (归一) / action_raw (原值)
      - severity (归一) / risk_level_raw (原值)
      - event_time (ISO8601) / event_time_raw (原值)
      - real_attacker_ip / real_victim_ip (WAF 无 IP 层受害, 用域名占位)
      - has_obfuscation (bool, L0 只标记不展开 payload)
      - protocol / app_proto (WAF 固定 http)
    """
    PRODUCT = "waf"
    VERSION = "0.1.0"

    # 供 registry.detect_product 识别用
    IDENTIFIER_COLS = IDENTIFIER_COLS

    def _do_parse(self, raw_log: str, ocsf_fields: dict) -> ParseResult:
        """解析 WAF 行.

        Args:
            raw_log: WAF 模式下始终为空字符串 (数据在 ocsf_fields)
            ocsf_fields: WAF CSV/XLSX 行 dict (中文列头 → 值)
        """
        result = ParseResult(parser_version=self.VERSION)
        row = ocsf_fields or {}

        if not row:
            raise ParseError("WAF 行数据为空 (row dict is None/empty)")

        # 1. 中文列头 → 内部字段
        mapped: dict = {}
        for cn, internal in COLUMN_MAP.items():
            val = row.get(cn)
            if val is not None and val != "":
                # 清理 WAF 导出常见的尾部 tab 残留
                if isinstance(val, str):
                    val = val.rstrip("\t").strip()
                mapped[internal] = val

        # 2. 动作归一
        action_raw = self.safe_str(mapped.get("action_raw"))
        mapped["action"] = ACTION_MAP.get(action_raw, "unknown")

        # 3. 风险等级归一 (severity)
        risk_raw = self.safe_str(mapped.get("risk_level_raw"))
        mapped["severity"] = SEVERITY_MAP.get(risk_raw, "informational")

        # 4. 时间归一 (WAF 攻击时间是毫秒 epoch)
        ts_raw = self.safe_str(mapped.get("event_time_raw"))
        mapped["event_time"] = self._parse_waf_ts(ts_raw)

        # 5. 网络字段 (对齐 event-schema.md network 结构)
        #    WAF 是应用层, 协议固定 http, 端口固定 80/443 (无法从日志区分, 留 null)
        src_ip = self.safe_str(mapped.get("src_ip")) or None
        victim_domain = self.safe_str(mapped.get("victim_domain")) or None

        mapped["protocol"] = "tcp"  # HTTP 底层传输
        mapped["app_proto"] = "http"
        mapped["src_port"] = None   # WAF 日志不含源端口
        mapped["dst_port"] = None   # WAF 日志不含目标端口
        mapped["dst_ip"] = None     # WAF 日志只有域名, 无目标 IP

        # NAT 还原: WAF 无 NAT 概念, real_attacker = src_ip, real_victim 用域名
        mapped["real_attacker_ip"] = src_ip
        mapped["real_victim_ip"] = None  # 域名不是 IP, 放 victim_domain
        mapped["ip_discrepancy"] = False
        mapped["encapsulation"] = {"gre": None}
        mapped["src_mac"] = None
        mapped["dst_mac"] = None

        # 6. WAF 独有字段 (供 L1 深度分析)
        mapped["victim_domain"] = victim_domain
        mapped["http_host"] = victim_domain  # 对齐 tianmu 的 http_host 命名

        # 7. 安全约束: L0 只标记 payload 特征, 不透出原文
        #    L1 (l1_waf_analyze.py) 可以访问 mapped["attack_payload"] 做深度分析,
        #    但 case/report 输出时不复制原文.
        payload = self.safe_str(mapped.get("attack_payload"))
        mapped["has_obfuscation"] = bool(OBFUSCATION_RE.search(payload)) if payload else False
        mapped["payload_length"] = len(payload) if payload else 0
        # payload 是否为最简形态 (教科书载荷), 供 L1 研判用
        mapped["is_simple_payload"] = self._is_simple_payload(payload)

        # 8. 聚合标记 (WAF 是逐条记录, 非聚合)
        mapped["is_aggregated"] = False
        mapped["event_type"] = "attack_log"

        # 9. 检测字段 (对齐 event-schema.md detection)
        mapped["rule_id"] = mapped.get("event_uuid")  # WAF uuid 作为 rule_id
        mapped["category"] = "web_security"
        mapped["subcategory"] = mapped.get("rule_name") or "unknown"

        # 10. 校验
        if not src_ip:
            result.parse_status = "partial"
            result.parse_errors.append("攻击IP 为空")
        if not victim_domain:
            result.parse_status = "partial"
            result.parse_errors.append("被攻击域名为空")
        if not mapped.get("rule_name"):
            result.parse_status = "partial"
            result.parse_errors.append("攻击类型为空")

        result.parsed = mapped
        return result

    # ========== 工具方法 ==========

    @staticmethod
    def _parse_waf_ts(ts_str: str | None) -> str | None:
        """把 WAF 攻击时间 (毫秒 epoch) 归一成 ISO8601

        WAF 时间样例:
          - 1780556626000 (13 位毫秒 epoch)
          - 1780556626    (10 位秒 epoch, 兼容)
        """
        if not ts_str:
            return None
        s = str(ts_str).strip()
        if not s.isdigit():
            return None
        try:
            v = int(s)
            if v > 10**12:  # 毫秒
                v //= 1000
            return datetime.fromtimestamp(v, tz=timezone.utc).isoformat()
        except (ValueError, OSError, OverflowError):
            return None

    @staticmethod
    def _is_simple_payload(content: str) -> bool:
        """判断 payload 是否为最简/教科书形态 (供 L1 研判用)

        与 analyzer.py is_simple_payload 逻辑对齐, 但 L0 只返回 bool 标记,
        不影响 L1 的完整研判逻辑.
        """
        if not content:
            return True
        c = content.strip().lower()
        if not c:
            return True
        simple_set = {
            "alert(1)", "alert(1", "1 union select", "id=1 and 1=1",
            "id=1 AND 1=1", "1=1", "or 1=1", "<script>", "../../",
        }
        for s in simple_set:
            if s.lower() in c:
                return True
        if re.fullmatch(r"[\d./:]+", c):
            return True
        if re.fullmatch(r"/[a-z0-9_/.-]*", c):
            return True
        if "ip penalty" in c or "ip-match-" in c or "ip-127" in c \
                or "session-" in c or c.startswith("ip-"):
            return True
        return False


# ==================== 独立测试入口 ====================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 示例: 模拟一行 WAF 数据
        sample_row = {
            "攻击IP": "1.2.3.4",
            "被攻击域名": "api.example.com",
            "URI": "/login",
            "方法": "POST",
            "攻击类型": "SQL注入攻击",
            "攻击内容": "1 union select * from users",
            "UserAgent": "sqlmap/1.6",
            "APPID": "1250000000",
            "uuid": "waf-uuid-abc123",
            "动作": "拦截",
            "风险等级": "高危",
            "攻击时间": "1780556626000",
        }
        print(f"用法: {sys.argv[0]} <json_row_str>")
        print(f"\n示例输入 (WAF 行 dict):\n{sample_row}\n")
        parser = WafParser()
        result = parser.parse("", sample_row)
    else:
        import json as _json
        row = _json.loads(sys.argv[1])
        parser = WafParser()
        result = parser.parse("", row)

    import json as _json
    print(_json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
