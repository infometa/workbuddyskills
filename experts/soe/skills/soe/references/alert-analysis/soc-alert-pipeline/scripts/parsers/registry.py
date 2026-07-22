"""L0 解析器注册表 - 按 product 字段自动选择 parser

新增 parser:
  1. 在 parsers/ 下加 xxx_parser.py
  2. 在本文件 import + 加到 _REGISTRY
  3. (可选) 在 references/tencent-product-naming.md 补充命名
"""
from __future__ import annotations
from ._base import BaseParser
from .yujie_parser import YujieParser
from .yujie_flat_parser import YujieFlatParser
from .cwp_parser import CwpParser
from .tianmu_parser import TianmuParser
from .waf_parser import WafParser


# 注册表: product code (小写) -> parser 实例
# 顺序不重要, get_parser() 按字段精确匹配
_REGISTRY: dict[str, BaseParser] = {
    YujieParser.PRODUCT: YujieParser(),
    YujieFlatParser.PRODUCT: YujieFlatParser(),
    CwpParser.PRODUCT: CwpParser(),
    TianmuParser.PRODUCT: TianmuParser(),
    WafParser.PRODUCT: WafParser(),
}


def get_parser(product: str) -> BaseParser | None:
    """根据 product 字段返回对应 parser (大小写不敏感)

    Args:
        product: 产品代号 (大小写不敏感, 例如 "yujie" / "YUJIE" / "Yujie" 都行)

    Returns:
        对应的 parser 实例, 没找到返回 None
    """
    if not product:
        return None
    return _REGISTRY.get(product.lower())


def register_parser(parser: BaseParser) -> None:
    """注册自定义 parser (供 L1 skill 扩展)

    Args:
        parser: BaseParser 子类实例, 必须有非空 PRODUCT 常量
    """
    if not isinstance(parser, BaseParser):
        raise TypeError(f"parser 必须是 BaseParser 子类, 实际: {type(parser)}")
    if not parser.PRODUCT:
        raise ValueError("parser.PRODUCT 不能为空")
    _REGISTRY[parser.PRODUCT.lower()] = parser


def supported_products() -> list[str]:
    """返回当前支持的产品代号列表"""
    return sorted(_REGISTRY.keys())


def detect_product(ocsf_fields: dict) -> str | None:
    """从 OCSF 字段推断产品代号

    优先看 logsource_subtype, 其次看 data_type, 最后兜底看 event_name 关键字.
    天幕直出格式 (无 raw_log, 中文列头) 用列头关键词识别.

    Args:
        ocsf_fields: SOC 透出的字段, 或天幕直出 xlsx 的行 dict

    Returns:
        产品代号 (小写), 没识别到返回 None
    """
    if not ocsf_fields:
        return None

    # 0. 天幕直出格式识别 (中文列头, 无 raw_log)
    #    天幕 xlsx 列头含 "命中规则"/"累计阻断次数"/"告警来源" 等中文
    if any(col in ocsf_fields for col in TianmuParser.IDENTIFIER_COLS):
        return TianmuParser.PRODUCT

    # 0b. WAF 直出格式识别 (中文列头, 无 raw_log)
    #     WAF CSV/XLSX 列头含 "攻击IP"/"被攻击域名"/"攻击类型"/"风险等级"/"攻击时间"
    if any(col in ocsf_fields for col in WafParser.IDENTIFIER_COLS):
        return WafParser.PRODUCT

    # 0c. 御界直出格式识别 (EVE 风格英文列头, 无 raw_log)
    #     御界控制台单独导出, 列头含 alert.signature / fileinfo.filename 等带点号字段
    # TODO: CWP 直出 / CFW 直出 待用户提供样本后补充识别分支
    if any(col in ocsf_fields for col in YujieFlatParser.IDENTIFIER_COLS):
        return YujieFlatParser.PRODUCT

    # 1. 优先 logsource_subtype
    subtype = ocsf_fields.get("logsource_subtype", "").lower().strip()
    if subtype and subtype in _REGISTRY:
        return subtype

    # 2. 关键词兜底 (避免产品代号不匹配时漏掉)
    event_name = ocsf_fields.get("event_name", "")
    data_type = ocsf_fields.get("data_type", "")
    combined = (event_name + " " + data_type).lower()

    if "wireguard" in combined or "inta" in combined or "nta" in combined or "御界" in event_name:
        return "yujie"

    if "ssh" in combined or "登录" in event_name or "主机" in event_name or "cwp" in combined or "云镜" in event_name:
        return "cwp"

    return None
