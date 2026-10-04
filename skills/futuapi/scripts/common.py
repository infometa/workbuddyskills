#!/usr/bin/env python3
"""
公共工具模块 - 提供 Futu OpenAPI 脚本的通用功能

包含：
- 环境变量配置
- 依赖检查与自动安装
- OpenD 连接配置
- 交易环境/市场枚举转换
- 上下文管理辅助
"""
import os
import subprocess
import sys
import json
import tempfile
import time
from dataclasses import dataclass
from typing import Optional


# ============================================================
# 环境变量配置
# ============================================================

@dataclass
class FutuConfig:
    """Futu OpenAPI 配置类"""
    # 登录凭证
    login_account: Optional[str] = None
    login_pwd: Optional[str] = None

    # OpenD 连接配置
    opend_host: str = "127.0.0.1"
    opend_port: int = 11111

    # 交易配置
    trd_env: str = "SIMULATE"
    default_market: str = "NONE"
    security_firm: Optional[str] = None


def get_config() -> FutuConfig:
    """
    获取 Futu OpenAPI 配置

    从环境变量中读取配置，未设置的使用默认值。

    环境变量:
        - FUTU_LOGIN_ACCOUNT: Futu 登录账号
        - FUTU_LOGIN_PWD: Futu 登录密码
        - FUTU_OPEND_HOST: OpenD 主机地址 (默认: 127.0.0.1)
        - FUTU_OPEND_PORT: OpenD 端口 (默认: 11111)
        - FUTU_TRD_ENV: 交易环境 (默认: SIMULATE)
        - FUTU_DEFAULT_MARKET: 默认市场 (默认: US)

    Returns:
        FutuConfig: 配置对象
    """
    return FutuConfig(
        login_account=os.getenv("FUTU_LOGIN_ACCOUNT", ""),
        login_pwd=os.getenv("FUTU_LOGIN_PWD", ""),
        opend_host=os.getenv("FUTU_OPEND_HOST", "127.0.0.1"),
        opend_port=int(os.getenv("FUTU_OPEND_PORT", "11111")),
        trd_env=os.getenv("FUTU_TRD_ENV", "SIMULATE"),
        default_market=os.getenv("FUTU_DEFAULT_MARKET", "NONE"),
        security_firm=os.getenv("FUTU_SECURITY_FIRM", "") or None,
    )


def _ensure_utf8_io():
    """Windows 下切换 stdout/stderr 为 UTF-8，避免 GBK 编码错误"""
    if sys.platform != "win32":
        return
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


_ensure_utf8_io()


# ============================================================
# 依赖检查
# ============================================================

SDK_MODULE_NAME = "futu"  # 固定品牌模块名

# 与 install-futu-opend SKILL.md 的 metadata.version 保持一致
# 使用 /install-futu-opend 技能安装完 OpenD 后会自动生成版本戳文件
SKILL_VERSION = "0.1.1"
STAMP_FILE = os.path.join(os.path.expanduser("~"), ".futu_skill_version")

MIN_SDK_VERSION = "10.4.6408"

# ai_type 参数需要 SDK >= MIN_SDK_VERSION，低版本不传此参数
_sdk_supports_ai_type = True

# 环境检查缓存：首次完整检查后写入临时文件，TTL 内跳过
_ENV_CHECK_CACHE_FILE = os.path.join(tempfile.gettempdir(), ".futu_env_ok")
_ENV_CHECK_TTL = 3600  # 1 小时


def _parse_version(ver_str):
    """将版本字符串解析为可比较的元组，如 '10.4.6408' -> (10, 4, 6408)"""
    try:
        return tuple(int(x) for x in ver_str.strip().split("."))
    except (ValueError, AttributeError):
        return (0,)


def _env_check_is_cached():
    """检查是否有近期的成功环境检查缓存"""
    try:
        mtime = os.path.getmtime(_ENV_CHECK_CACHE_FILE)
        return (time.time() - mtime) < _ENV_CHECK_TTL
    except OSError:
        return False


def _env_check_mark_ok():
    """标记环境检查通过"""
    try:
        with open(_ENV_CHECK_CACHE_FILE, "w") as f:
            f.write(str(time.time()))
    except OSError:
        pass


def _check_version_stamp():
    """检查版本戳文件，确保 OpenD 和 SDK 已通过 install skill 正确安装（仅警告，不阻断）"""
    try:
        with open(STAMP_FILE, "r", encoding="utf-8") as f:
            installed = f.read().strip()
    except FileNotFoundError:
        print(f"[WARN] 未检测到版本戳文件 {STAMP_FILE}，建议运行 /install-futu-opend 安装", file=sys.stderr)
        return
    if installed != SKILL_VERSION:
        print(f"[WARN] 版本戳不匹配: 已安装 {installed}, 当前要求 {SKILL_VERSION}，建议运行 /install-futu-opend 更新", file=sys.stderr)


def _check_opend_reachable():
    """检查 OpenD 是否可连接"""
    import socket
    config = get_config()
    host, port = config.opend_host, config.opend_port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect((host, port))
    except (ConnectionRefusedError, OSError) as e:
        print(f"[ERROR] 无法连接 OpenD ({host}:{port}): {e}")
        print("请先启动 OpenD 客户端")
        sys.exit(1)
    finally:
        sock.close()


def _detect_ai_type_support():
    """检测当前 SDK 是否支持 ai_type 参数（仅检查版本，不打印警告）"""
    global _sdk_supports_ai_type
    try:
        import futu
        current = getattr(futu, "__version__", "0")
        if _parse_version(current) < _parse_version(MIN_SDK_VERSION):
            _sdk_supports_ai_type = False
    except ImportError:
        pass


def ensure_futu_api():
    """环境检查（带缓存）：SDK 版本 + 版本戳 + OpenD 连通性。首次完整检查，TTL 内跳过。"""
    # 1. 缓存命中时仅做轻量 ai_type 支持检测
    if _env_check_is_cached():
        _detect_ai_type_support()
        return True

    # 2. 版本戳检查
    _check_version_stamp()

    # 3. SDK 导入 + 版本检查
    global _sdk_supports_ai_type
    try:
        import futu
        current = getattr(futu, "__version__", "0")
        if _parse_version(current) < _parse_version(MIN_SDK_VERSION):
            _sdk_supports_ai_type = False
            print(f"[WARN] futu-api 版本过低: {current} < {MIN_SDK_VERSION}，ai_type 参数将被跳过，建议运行 /install-futu-opend 升级 SDK", file=sys.stderr)
    except ImportError:
        print("[ERROR] futu-api 未安装，请运行 /install-futu-opend 安装")
        sys.exit(1)

    # 4. OpenD 连通性检查
    _check_opend_reachable()

    # 5. 标记检查通过
    _env_check_mark_ok()
    return True

ensure_futu_api()

from futu import (
        OpenQuoteContext,
        OpenSecTradeContext,
        RET_OK,
        TrdEnv,
        TrdMarket,
        TrdSide,
        OrderType,
        ModifyOrderOp,
        SubType,
        Session,
        KLType,
        AuType,
        Market,
        SecurityType,
        SecurityReferenceType,
        SimpleFilter,
        AccumulateFilter,
        FinancialFilter,
        FinancialQuarter,
        StockField,
        SortDir,
        Plate,
)

try:
    from futu import TradeDateMarket
except ImportError:
    TradeDateMarket = None

from futu import SecurityFirm


# ============================================================
# 连接配置
# ============================================================

def get_opend_config():
    """获取 OpenD 连接配置 -> (host, port)"""
    config = get_config()
    return config.opend_host, config.opend_port


def _check_opend_alive(host, port):
    """快速检测 OpenD 端口是否可连接，不可连接时直接报错退出"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        print(f"错误: 无法连接 OpenD ({host}:{port})，连接被拒绝。请先启动 OpenD 客户端。")
        sys.exit(1)
    except OSError as e:
        print(f"错误: 无法连接 OpenD ({host}:{port}): {e}。请检查 OpenD 是否已启动。")
        sys.exit(1)
    finally:
        sock.close()


def create_quote_context():
    """创建行情上下文"""
    host, port = get_opend_config()
    _check_opend_alive(host, port)
    kwargs = dict(host=host, port=port)
    if _sdk_supports_ai_type:
        kwargs["ai_type"] = 1
    return OpenQuoteContext(**kwargs)


def parse_security_firm(firm_str):
    """解析券商标识字符串 -> SecurityFirm 枚举，无效时返回 None"""
    if not firm_str:
        return None
    key = str(firm_str).strip().upper()
    if hasattr(SecurityFirm, key):
        return getattr(SecurityFirm, key)
    return None


def get_default_security_firm():
    """获取默认券商标识（从环境变量）"""
    config = get_config()
    return parse_security_firm(config.security_firm)


def create_trade_context(market=None, security_firm=None):
    """创建交易上下文"""
    host, port = get_opend_config()
    _check_opend_alive(host, port)
    trd_market = parse_market(market) if market else get_default_market()
    kwargs = dict(host=host, port=port, filter_trdmarket=trd_market)
    if _sdk_supports_ai_type:
        kwargs["ai_type"] = 1
    if security_firm is not None:
        kwargs["security_firm"] = security_firm
    else:
        default_firm = get_default_security_firm()
        kwargs["security_firm"] = default_firm if default_firm is not None else SecurityFirm.NONE
    return OpenSecTradeContext(**kwargs)


# ============================================================
# 枚举转换
# ============================================================

def parse_trd_env(env_str):
    """解析交易环境字符串 -> TrdEnv"""
    if env_str and str(env_str).upper() == "REAL":
        return TrdEnv.REAL
    return TrdEnv.SIMULATE


def parse_market(market_str):
    """解析交易市场字符串 -> TrdMarket"""
    if not market_str:
        return TrdMarket.US
    mapping = {
        "NONE": TrdMarket.NONE,
        "N/A": TrdMarket.NONE,
        "US": TrdMarket.US,
        "HK": TrdMarket.HK,
        "CN": TrdMarket.CN,
        "HKCC": TrdMarket.HKCC,
        "SG": TrdMarket.SG,
    }
    return mapping.get(str(market_str).upper(), TrdMarket.US)


# 股票代码前缀 -> 交易市场映射
_CODE_PREFIX_TO_MARKET = {
    "US": "US",
    "HK": "HK",
    "SH": "CN",
    "SZ": "CN",
    "SG": "SG",
}


def infer_market_from_code(code):
    """从股票代码前缀推导交易市场字符串，如 US.AAPL -> 'US'，HK.00700 -> 'HK'。
    无法识别时返回 None。"""
    if not code or "." not in code:
        return None
    prefix = code.split(".")[0].upper()
    return _CODE_PREFIX_TO_MARKET.get(prefix)


def parse_trd_side(side_str):
    """解析交易方向字符串 -> TrdSide"""
    if not side_str or str(side_str).strip().upper() not in ("BUY", "SELL"):
        raise ValueError(f"无效的交易方向: {side_str}，必须为 BUY 或 SELL")
    if str(side_str).strip().upper() == "BUY":
        return TrdSide.BUY
    return TrdSide.SELL


def parse_subtypes(subtype_names):
    """将字符串列表转换为 SubType 枚举列表"""
    subtypes = []
    for name in subtype_names:
        key = str(name).strip().upper()
        if key == "BASIC":
            key = "QUOTE"
        if not hasattr(SubType, key):
            raise ValueError(f"不支持的订阅类型: {name}")
        subtypes.append(getattr(SubType, key))
    return subtypes


# ============================================================
# 配置获取
# ============================================================

def get_default_acc_id():
    """获取默认账户 ID"""
    return int(os.getenv("FUTU_ACC_ID", "0"))


def get_default_trd_env():
    """获取默认交易环境"""
    config = get_config()
    return parse_trd_env(config.trd_env)


def get_default_market():
    """获取默认交易市场"""
    config = get_config()
    return parse_market(config.default_market)



# ============================================================
# 数据处理辅助
# ============================================================

def safe_get(row, *keys, default=""):
    """安全获取 DataFrame 行或字典中的值，支持多个备选 key"""
    for key in keys:
        val = row.get(key) if hasattr(row, 'get') else getattr(row, key, None)
        if val is not None:
            return val
    return default


def safe_float(val, default=0.0):
    """安全转换为 float，遇到 N/A、空串、None 等非数值时返回默认值"""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    """安全转换为 int，遇到 N/A、空串、None 等非数值时返回默认值。
    处理 numpy 标量类型，避免大整数（如 18 位 acc_id）经 float64 转换后精度丢失。"""
    if val is None:
        return default
    # numpy 标量: 提取原生 Python 类型，避免 float64 精度丢失
    if hasattr(val, 'item'):
        val = val.item()
    try:
        return int(val)
    except (ValueError, TypeError):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default


def format_enum(val):
    """格式化枚举值为字符串"""
    if hasattr(val, "name"):
        return val.name
    return str(val)


# ============================================================
# 上下文管理辅助
# ============================================================

def safe_close(ctx):
    """安全关闭上下文"""
    try:
        if ctx:
            ctx.close()
    except Exception:
        pass


def _is_permission_error(error_msg):
    """检测错误信息是否为行情权限不足"""
    keywords = [
        "权限", "没有权限", "权限不足", "无权限",
        "no permission", "permission denied", "not permission",
        "authority", "no authority",
        "quota", "no quota",
        "bmp", "lv1", "lv2",
        "未开通", "未购买", "need subscribe",
        "not subscribed", "unsubscribed",
    ]
    msg = str(error_msg).lower()
    return any(kw in msg for kw in keywords)


_MARKET_NAMES = {
    "HK": "港股", "US": "美股",
    "SH": "A股", "SZ": "A股",
    "SG": "新加坡",
}

_AUTHORITY_URLS = {"futu": "https://openapi.futunn.com/futu-api-doc/intro/authority.html"}


def _detect_market_from_argv():
    """从命令行参数中的股票代码检测市场（如 HK.00700 -> 港股）"""
    import re
    for arg in sys.argv[1:]:
        m = re.match(r'^(HK|US|SH|SZ|SG)\.', arg, re.IGNORECASE)
        if m:
            return _MARKET_NAMES.get(m.group(1).upper(), "")
    return ""


def _get_authority_url():
    """返回行情权限页面链接"""
    return _AUTHORITY_URLS["futu"]



def _build_permission_hint():
    """构建行情权限不足的提示信息"""
    market = _detect_market_from_argv()
    market_prefix = f"{market}" if market else ""
    url = _get_authority_url()
    return (
        f"\n\n{market_prefix}行情权限不足，请购买对应行情卡以获取数据。"
        f"详情参考：{url}"
    )



def _build_permission_hint_json():
    """构建 JSON 格式的行情权限提示字段"""
    market = _detect_market_from_argv()
    market_prefix = f"{market}" if market else ""
    hint = f"{market_prefix}行情权限不足，请购买对应行情卡以获取数据"
    url = _get_authority_url()
    return {"hint": hint, "authority_url": url}



def check_ret(ret, data, ctx=None, action="操作", output_json=None):
    """检查 API 返回值，失败则打印错误并退出"""
    if ret != RET_OK:
        if output_json is None:
            try:
                output_json = "--json" in sys.argv
            except Exception:
                output_json = False

        perm_error = _is_permission_error(data)

        if output_json:
            err_obj = {"ret": ret, "action": action, "error": str(data)}
            if perm_error:
                err_obj.update(_build_permission_hint_json())
            print(json.dumps(err_obj, ensure_ascii=False))
        else:
            print(f"{action}失败: {data}")
            if perm_error:
                print(_build_permission_hint())
        safe_close(ctx)
        sys.exit(1)


def is_empty(data):
    """检查数据是否为空"""
    if data is None:
        return True
    if hasattr(data, "shape"):
        return data.shape[0] == 0
    if hasattr(data, "__len__"):
        return len(data) == 0
    return False


def to_jsonable(val, default=None):
    """将值转为 JSON 可序列化类型"""
    import math
    if val is None:
        return default
    if hasattr(val, "item"):
        val = val.item()
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return default
    if hasattr(val, "name"):
        return val.name
    if isinstance(val, (str, int, float, bool, list, dict)):
        return val
    return str(val)


def df_to_records(df, limit=None):
    """将 DataFrame 转为 JSON 可序列化的记录列表"""
    if is_empty(df):
        return []
    total = len(df)
    n = total if (limit is None or limit <= 0) else min(total, limit)
    records = []
    for i in range(n):
        row = df.iloc[i] if hasattr(df, "iloc") else df[i]
        if hasattr(row, "index"):
            keys = row.index
        elif isinstance(row, dict):
            keys = row.keys()
        else:
            keys = [k for k in dir(row) if not k.startswith("_")]
        records.append({
            k: to_jsonable(row.get(k) if hasattr(row, "get") else getattr(row, k, None))
            for k in keys
        })
    return records
