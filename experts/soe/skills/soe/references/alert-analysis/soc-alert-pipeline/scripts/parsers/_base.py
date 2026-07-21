"""L0 Parser 基类 - 所有产品解析器继承此类"""
from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field
from typing import Any


class ParseError(Exception):
    """L0 解析失败基类 (子类抛出后由 BaseParser 统一捕获)"""
    pass


@dataclass
class ParseResult:
    """L0 统一返回结构

    Attributes:
        parsed: 结构化字段 (各产品自定义, 需遵循 references/event-schema.md)
        parse_status: "ok" (完整) | "partial" (部分) | "failed" (失败)
        parse_errors: 字段级错误列表, 不阻断, 仅供 L1 / 调试参考
        parser_version: 解析器版本, 用于追溯
    """
    parsed: dict[str, Any] = field(default_factory=dict)
    parse_status: str = "ok"
    parse_errors: list[str] = field(default_factory=list)
    parser_version: str = "0.1.0"

    def to_dict(self) -> dict:
        return {
            "parsed": self.parsed,
            "parse_status": self.parse_status,
            "parse_errors": self.parse_errors,
            "parser_version": self.parser_version,
        }


class BaseParser(ABC):
    """L0 Parser 抽象基类

    子类必须实现:
      - PRODUCT: str  (产品代号, 与统一事件 schema 的 vendor_product 对应)
      - _do_parse(raw_log, ocsf_fields) -> ParseResult

    子类不应重写 parse() 方法, 它已经统一处理异常捕获.
    """
    PRODUCT: str = ""
    VERSION: str = "0.1.0"

    def parse(self, raw_log: str, ocsf_fields: dict | None = None) -> ParseResult:
        """主入口: 解析 raw_log 字符串, 返回 ParseResult

        Args:
            raw_log: SOC 导出的原始日志字符串
            ocsf_fields: SOC 透出的 OCSF 字段 (可选, 用于交叉验证)

        Returns:
            ParseResult - 永不抛异常, 失败时 parse_status="failed"
        """
        if not self.PRODUCT:
            raise NotImplementedError(f"{type(self).__name__} 必须设置 PRODUCT 常量")

        ocsf = ocsf_fields or {}
        try:
            return self._do_parse(raw_log, ocsf)
        except ParseError as e:
            return ParseResult(
                parsed={},
                parse_status="failed",
                parse_errors=[f"ParseError: {e}"],
                parser_version=self.VERSION,
            )
        except Exception as e:
            # 兜底: 任何未预期的异常都不外抛
            return ParseResult(
                parsed={},
                parse_status="failed",
                parse_errors=[f"unexpected: {type(e).__name__}: {e}"],
                parser_version=self.VERSION,
            )

    def _do_parse(self, raw_log: str, ocsf_fields: dict) -> ParseResult:
        """子类实现: 实际解析逻辑

        可以抛 ParseError 表示不可恢复错误, 外层会捕获并返回 failed
        """
        raise NotImplementedError

    # ========== 工具方法 (供子类使用) ==========

    @staticmethod
    def safe_int(value, default=None):
        """安全的 int 转换"""
        if value is None or value == "":
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_float(value, default=None):
        """安全的 float 转换"""
        if value is None or value == "":
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_str(value, default=""):
        """安全的字符串转换, 处理 None 和非字符串类型"""
        if value is None:
            return default
        if isinstance(value, str):
            return value
        return str(value)
