"""
看板构建器 — 单一入口文件（合并原 kanban_utils.py + kanban_builder.py）

🛑🛑🛑 P0 强制：本文件为只读模板，禁止任何修改 🛑🛑🛑
本文件是 generate_kanban.py 的公共构建器，通过 exec() 加载使用。
所有 UI 呈现由平台侧读取 DSL（HtmlContent）+ Datasets（SqlSlots）渲染，
所有数据/指标变动通过修改 Spec 后重跑 runner 生成 DSL/Datasets 实现。
绝不允许为了实现某个看板的个性化需求而修改本文件。

解决的核心问题：
1. Python f-string 与 HTML/CSS/JS 花括号冲突 → 使用 string.Template（$variable 占位符）
2. 两个文件分散加载易遗漏 → 合并为单文件，一次 exec 即可

三端统一入库权威链路：
    1. write_kanban_outputs      → 完成 lint 并准备基础 save_meta（主链路不写空 params）
    2. kanban_dsl_emitter.emit_dsl → 一次性写入 kanban_save_params.json（HtmlContent = DSL / SqlSlots = Datasets）
    3. update_to_kanban_list     → UpdateAiKanBan/PREVIEW（读最终 params，PC/H5/embed 三端共用）
       save_to_kanban_list       → SaveAiKanBan（发布态；只带 WorkspaceId + AccessKey）

使用方式（在 Step D 脚本中，沙箱兼容）：
    # 由 kanban_runner 内部解析并 exec 加载 kanban_builder.py；spec 侧无需直接引用本文件。
    # 若需手动定位，参考 _resolve_builder_dir 的多级降级策略：
    #   1) KANBAN_REFERENCE_DIR 显式指定
    #   2) 通过 __file__ 相对定位（reference/ 目录自身）
    #   3) CODEBUDDY_PLUGIN_ROOT 下按新→旧及 WorkBuddy 布局探测
    #   4) os.getcwd()/reference/ 兜底
"""

import os
import sys
import time
import json
import re
import glob
import base64
import gzip
import math
from string import Template
from datetime import datetime, date, time as dt_time


# ===== 沙箱兼容：确定本文件所在目录（用于路径解析） =====
# 通过 exec() 加载时 __file__ 未定义，需要多级降级
def _resolve_builder_dir():
    """确定 kanban_builder.py 所在目录的绝对路径（即 reference/ 目录）。

    优先级（first-wins，兼容 WorkBuddy 与多种 DataBuddy 部署布局）：
    1. KANBAN_REFERENCE_DIR 环境变量（显式指定）
    2. __file__ 所在目录（直接 import / runner exec 加载）
    3. CODEBUDDY_PLUGIN_ROOT 下依次探测新版、旧版和 WorkBuddy connector 布局
    4. os.getcwd()/reference/ 兜底（本地开发）
    """
    ref_dir = os.environ.get('KANBAN_REFERENCE_DIR', '').strip()
    if ref_dir and os.path.isdir(ref_dir):
        return ref_dir

    try:
        here = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(here):
            return here
    except NameError:
        pass

    plugin_root = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '').strip()
    if plugin_root:
        for sub in (
            ('scenarios', 'data-analysis', 'skills', 'intelligent-kanban', 'reference'),
            ('l3-skill-scenario', 'intelligent-kanban', 'reference'),
            ('intelligent-kanban', 'reference'),
        ):
            candidate = os.path.join(plugin_root, *sub)
            if os.path.isdir(candidate):
                return candidate

    candidate = os.path.join(os.getcwd(), 'reference')
    if os.path.isdir(candidate):
        return candidate
    return os.getcwd()

_BUILDER_DIR = _resolve_builder_dir()


# ============================================================
# 通用工具函数（原 kanban_utils.py）
# ============================================================

# ===== 安全 JSON 编码器（兼容 Pandas/NumPy 特殊类型） =====

class _SafeJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，自动处理 Pandas/NumPy 等常见不可序列化类型。
    
    覆盖场景：
    - pandas.Timestamp / NaT → ISO 字符串 / null
    - numpy.int64/float64 → Python int/float
    - numpy.ndarray → list
    - numpy.bool_ → Python bool
    - numpy.nan / inf → null
    - datetime.date/datetime → ISO 字符串
    - pandas.NA / NaT → null
    - set → list
    """
    def default(self, obj):
        # 尝试处理 pandas 类型（不强制 import pandas）
        obj_type = type(obj).__name__
        obj_module = type(obj).__module__ or ''
        
        # pandas.NaT / NA 必须在 datetime 之前检测（因为 NaT 是 datetime 子类）
        if obj_type in ('NaTType', 'NAType') or str(obj) in ('NaT', '<NA>'):
            return None
        
        # pandas.Timestamp（也是 datetime 子类，但需要特殊处理）
        if obj_type == 'Timestamp':
            try:
                return obj.isoformat()
            except Exception:
                return str(obj)
        
        # datetime 系列
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dt_time):
            return obj.isoformat()
        
        # numpy 整数类型
        if 'numpy' in obj_module or obj_type in ('int64', 'int32', 'int16', 'int8', 'uint64', 'uint32', 'uint16', 'uint8'):
            try:
                if hasattr(obj, 'item'):
                    val = obj.item()
                    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                        return None
                    return val
            except (ValueError, OverflowError, TypeError):
                pass
        
        # numpy 浮点类型
        if obj_type in ('float64', 'float32', 'float16'):
            try:
                val = obj.item() if hasattr(obj, 'item') else float(obj)
                if math.isnan(val) or math.isinf(val):
                    return None
                return val
            except (ValueError, OverflowError, TypeError):
                return None
        
        # numpy bool
        if obj_type == 'bool_':
            return bool(obj)
        
        # numpy ndarray
        if obj_type == 'ndarray':
            return obj.tolist()
        
        # pandas Series / DataFrame（极端兜底）
        if obj_type in ('Series', 'DataFrame'):
            return obj.to_dict()
        
        # set → list
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        
        # bytes → base64
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('ascii')
        
        # 最终兜底：尝试 str()
        try:
            return str(obj)
        except Exception:
            return None


def _safe_json_dumps(obj, **kwargs):
    """安全的 json.dumps 封装，自动使用 _SafeJSONEncoder 处理特殊类型。
    
    额外处理：
    - float NaN/Inf → null（json.dumps 默认会输出 NaN/Infinity 导致 JS 解析失败）
    """
    kwargs.setdefault('ensure_ascii', False)
    kwargs['cls'] = _SafeJSONEncoder
    result = json.dumps(obj, **kwargs)
    # 后处理：替换 JSON 中的 NaN/Infinity（Python json 模块默认允许这些非标准值）
    result = re.sub(r'\bNaN\b', 'null', result)
    result = re.sub(r'-Infinity\b', 'null', result)
    result = re.sub(r'\bInfinity\b', 'null', result)
    return result


_UPDATE_PAYLOAD_GZIP_THRESHOLD_BYTES = 64 * 1024
_UPDATE_PAYLOAD_GZIP_MIN_SAVING_RATIO = 0.20


def _encode_update_payload(text: str, field_name: str = '') -> str:
    """将 UpdateAiKanBan 大字段编码为 base64；超过阈值时优先使用 gzip+base64。

    服务端仅接受 base64 或 gzip+base64，并在入库前统一还原为明文。
    本地落盘的 dsl/json 文件不受影响，仅请求参数使用压缩后的传输形态。
    """
    raw = text.encode('utf-8')
    raw_b64 = base64.b64encode(raw).decode('ascii')
    if len(raw) < _UPDATE_PAYLOAD_GZIP_THRESHOLD_BYTES:
        return raw_b64

    gz = gzip.compress(raw, compresslevel=6)
    gz_b64 = base64.b64encode(gz).decode('ascii')
    saving_ratio = 1 - (len(gz_b64) / len(raw_b64)) if raw_b64 else 0
    if saving_ratio >= _UPDATE_PAYLOAD_GZIP_MIN_SAVING_RATIO:
        label = field_name or 'UpdateAiKanBan payload'
        print(f'📦 {label} 已启用 gzip+base64: raw={len(raw)}B, base64={len(raw_b64)}B, '
              f'gzipBase64={len(gz_b64)}B, saving={saving_ratio:.1%}')
        return gz_b64
    return raw_b64


# ===== 产物目录 =====

def get_kanban_output_dir():
    """确定看板产物目录，按优先级降级，最终路径必须为 base_dir/.kanban_output。
    
    优先级（选择基础目录）：
    1. 显式环境变量 KANBAN_OUTPUT_DIR（最高优先级，由 plugin-env 注入）
    2. 显式环境变量 WEDATA_WORKSPACE_FOLDER（WorkBuddy session 场景注入）
    3. /workspace（沙箱固定挂载点）
    4. cwd（兜底，本地开发兼容）
    
    无论基础目录是哪个，看板产物都必须放在 base_dir/.kanban_output 下。
    """
    # 1. 显式环境变量（最高优先级，由 plugin-env 注入）
    env_dir = os.environ.get('KANBAN_OUTPUT_DIR')
    if env_dir:
        # 🛡️ 防嵌套：如果环境变量已经以 .kanban_output 结尾，直接使用（不再追加）
        if env_dir.rstrip('/').endswith('.kanban_output'):
            output_dir = env_dir
            os.makedirs(output_dir, exist_ok=True)
            return output_dir
        base_dir = env_dir
    # 2. WEDATA_WORKSPACE_FOLDER（WorkBuddy connector 场景 session 目录）
    elif os.environ.get('WEDATA_WORKSPACE_FOLDER', '').strip() and os.path.isdir(os.environ['WEDATA_WORKSPACE_FOLDER'].strip()):
        base_dir = os.environ['WEDATA_WORKSPACE_FOLDER'].strip()
    # 3. /workspace（沙箱固定挂载点）
    elif os.path.isdir('/workspace'):
        base_dir = '/workspace'
    # 4. 兜底：cwd（本地开发兼容）
    else:
        base_dir = os.getcwd()

    # 🛡️ 防嵌套（cwd / base_dir 已位于 .kanban_output 内）：
    # 当 LLM 按 SKILL.md 新模板执行 `python3 ./.kanban_output/kanban_spec.py` 时，
    # spec 本身位于 `<case_sandbox>/.kanban_output/kanban_spec.py`，进程 cwd 仍是
    # case_sandbox（os.getcwd()），此时拼接 base_dir/.kanban_output 是正确的。
    # 但若用户/脚本 cd 进了 .kanban_output 再执行 spec（base_dir 末尾就是
    # .kanban_output），需要直接返回该目录而不是再嵌一层 .kanban_output/.kanban_output。
    if os.path.basename(os.path.normpath(base_dir)) == '.kanban_output':
        output_dir = base_dir
    else:
        # 所有看板产物必须放在 .kanban_output 子目录下
        output_dir = os.path.join(base_dir, '.kanban_output')
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


# ===== DataFrame → SLOT_DATA 安全转换 =====

def df_to_slot_data(df, columns=None):
    """将 Pandas DataFrame 安全转换为 SLOT_DATA 格式（二维列表：[header_row, data_row1, ...]）。
    
    自动处理：
    - Timestamp → ISO 字符串
    - numpy int64/float64 → Python int/float
    - NaN/NaT → None
    - 其他不可序列化类型 → str()
    
    参数:
        df: Pandas DataFrame
        columns: 可选，指定输出的列名列表（默认使用 df.columns）
    
    返回:
        [[col1, col2, ...], [val1, val2, ...], ...]
    
    示例:
        daily_trend = df.groupby('date').agg({'sales': 'sum'}).reset_index()
        SLOT_DATA['daily_trend'] = df_to_slot_data(daily_trend)
    """
    if columns:
        df = df[columns]
    
    header = df.columns.tolist()
    
    # 🔧 记录原始整数列集合，修复 iterrows() 混合 dtype 提升问题
    # 背景：pandas iterrows() 在 DataFrame 包含 int + float 列时，
    # 会将整行 Series 统一提升为 float64，导致整数列丢失精度（如 1 → 1.0）。
    # 解决方案：遍历后对原始整数列做类型恢复。
    _int_dtypes = ('int8', 'int16', 'int32', 'int64',
                   'uint8', 'uint16', 'uint32', 'uint64')
    int_col_set = set(df.select_dtypes(include=list(_int_dtypes)).columns)
    
    # 逐行转换，确保所有值都是 JSON 可序列化的基本类型
    rows = []
    for _, row in df.iterrows():
        converted_row = []
        for col_name, val in row.items():
            converted = _convert_value(val)
            # 恢复被 iterrows dtype 提升破坏的整数列
            if col_name in int_col_set and isinstance(converted, float):
                # 仅当值确实是整数时恢复（NaN 已在 _convert_value 中处理为 None）
                if converted == int(converted):
                    converted = int(converted)
            converted_row.append(converted)
        rows.append(converted_row)
    
    return [header] + rows


def _convert_value(val):
    """将单个值转换为 JSON 安全的 Python 基本类型。"""
    if val is None:
        return None
    
    # 检查 NaN 和 Inf（float NaN/Inf 和 numpy NaN/Inf）
    try:
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
    except (TypeError, ValueError):
        pass
    
    # 检查 pandas NaT / NA
    val_type = type(val).__name__
    if val_type in ('NaTType', 'NAType') or str(val) in ('NaT', '<NA>'):
        return None
    
    # Timestamp → ISO 字符串
    if val_type == 'Timestamp':
        try:
            return val.isoformat()
        except Exception:
            return str(val)
    
    # datetime/date → ISO 字符串
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    
    # numpy 数值类型 → Python 原生类型
    if hasattr(val, 'item'):
        try:
            native = val.item()
            if isinstance(native, float) and (math.isnan(native) or math.isinf(native)):
                return None
            return native
        except (ValueError, OverflowError, TypeError):
            pass
    
    # 基本类型直接返回
    if isinstance(val, (str, int, float, bool)):
        return val
    
    # 兜底：转字符串
    return str(val)


# ===== CSV 路径获取 =====

def find_latest_csv():
    """降级方案：从 /tmp/ 目录查找最新的 wedata_result CSV 文件。"""
    csv_files = glob.glob('/tmp/wedata_result_*.csv')
    if not csv_files:
        raise FileNotFoundError('未找到 CSV 数据文件（目录: /tmp/），请确认取数步骤已执行且 --save_dir 为 /tmp')
    return max(csv_files, key=os.path.getmtime)


class _TimeParseResult:
    """parse_time_column 的防误用代理返回值。

    设计目的：
        parse_time_column 返回布尔值表示"是否解析成功"，但 Agent 生成代码时
        极易写出 `df = parse_time_column(df, col)` 导致 df 被覆盖为 True/False。

    本类让返回值同时满足：
        1. 布尔上下文正常工作：`if parse_time_column(df, col):` → True/False
        2. 误赋值场景安全降级：`df = parse_time_column(df, col)` → df 仍是原 DataFrame
           （代理对象转发所有 DataFrame 属性/方法访问到原始 df）
        3. 比较运算正常：`result == True` / `result is True` 的替代 `bool(result)`

    兼容性保证：
        - `bool(result)` → True/False（与原行为一致）
        - `result.columns` → df.columns（透传 DataFrame 属性）
        - `result.groupby(...)` → df.groupby(...)（透传 DataFrame 方法）
        - `result[col]` → df[col]（透传索引）
        - `result[col] = val` → df[col] = val（透传赋值）
        - `len(result)` → len(df)
        - `iter(result)` → iter(df)
    """

    __slots__ = ('_df', '_is_datetime')

    def __init__(self, df, is_datetime):
        object.__setattr__(self, '_df', df)
        object.__setattr__(self, '_is_datetime', bool(is_datetime))

    # ===== 布尔语义（核心：保持原有 bool 返回值行为） =====
    def __bool__(self):
        return object.__getattribute__(self, '_is_datetime')

    def __eq__(self, other):
        if isinstance(other, bool):
            return object.__getattribute__(self, '_is_datetime') == other
        # 非 bool 比较时转发给 df（如 df == other_df）
        return object.__getattribute__(self, '_df').__eq__(other)

    def __ne__(self, other):
        if isinstance(other, bool):
            return object.__getattribute__(self, '_is_datetime') != other
        return object.__getattribute__(self, '_df').__ne__(other)

    def __hash__(self):
        return hash(object.__getattribute__(self, '_is_datetime'))

    # ===== DataFrame 透传（误赋值场景的安全降级） =====
    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, '_df'), name)

    def __setattr__(self, name, value):
        if name in ('_df', '_is_datetime'):
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, '_df'), name, value)

    def __getitem__(self, key):
        return object.__getattribute__(self, '_df')[key]

    def __setitem__(self, key, value):
        object.__getattribute__(self, '_df')[key] = value

    def __len__(self):
        return len(object.__getattribute__(self, '_df'))

    def __iter__(self):
        return iter(object.__getattribute__(self, '_df'))

    def __contains__(self, item):
        return item in object.__getattribute__(self, '_df')

    def __repr__(self):
        is_dt = object.__getattribute__(self, '_is_datetime')
        return f'_TimeParseResult(is_datetime={is_dt}, df=<DataFrame {len(self)} rows>)'

    def __str__(self):
        return str(object.__getattribute__(self, '_is_datetime'))

    # ===== 支持 int() 转换（兼容 True→1, False→0） =====
    def __int__(self):
        return int(object.__getattribute__(self, '_is_datetime'))

    def __float__(self):
        return float(object.__getattribute__(self, '_is_datetime'))


def parse_time_column(df, col, keep_str_copy=True, min_success_ratio=0.5):
    """安全解析 DataFrame 中的时间字段（B4 P0 强制完整模板）。

    解析策略（按顺序尝试，命中即返回）：
        1. 已是 datetime 类型 → 直接返回
        2. 数值类型（int/float） → 优先按 Unix 秒/毫秒识别（10/13 位数量级判断），避免被自动推断当年份解析
        3. 字符串类型 → pd.to_datetime 自动推断（覆盖 yyyy-MM-dd / yyyy/M/d / MM/dd/yyyy / ISO 8601 / 含时间部分）
        4. 字符串解析覆盖率不足 → 尝试截断时间部分后重试（针对 '2017/10/2 10:56' 等带时间字符串）
        5. 全部失败 → 保留原始 dtype，返回 is_datetime=False

    判定逻辑（关键）：
        以"非空值中成功解析为 datetime 的比例 ≥ min_success_ratio"为成功标准（默认 50%）。
        避免被仅 1 行有效就返回 True 的情况误导（如 99% NaN 字段、混合格式只成功 1 个）。

    副作用（仅当 keep_str_copy=True）：
        在 df 中写入 `<col>_str` 列，保存原始字符串副本（用于兜底从字符串中提取年月）。

    参数:
        df: Pandas DataFrame（原地修改 df[col]）
        col: 时间字段列名
        keep_str_copy: 是否保留 `<col>_str` 原始字符串副本（默认 True）
        min_success_ratio: 解析成功率阈值（0~1，默认 0.5），低于此值视为解析失败

    返回:
        _TimeParseResult: 解析后 df[col] 是否为 datetime 类型（兼容 bool 和 DataFrame 双重语义）
              - bool(result) == True：可使用 .dt 访问器（如 df[col].dt.strftime('%Y-%m')）
              - bool(result) == False：仍为字符串/数值类型，需走兜底分支
              - 误用 `df = parse_time_column(df, col)` 时：df 仍可正常使用（代理透传所有 DataFrame 操作）

    示例:
        # ✅ 正确用法（推荐）
        is_dt = parse_time_column(df, 'dt')
        if is_dt:
            df['month'] = df['dt'].dt.strftime('%Y-%m')
        else:
            df['month'] = df['dt_str'].str.extract(r'(\\d{4}[/-]\\d{1,2})')[0]

        # ✅ 误用也安全（df 不会被破坏）
        df = parse_time_column(df, 'dt')  # df 仍是 DataFrame（代理对象透传）
        if df:  # 等价于 if is_datetime
    """
    try:
        import pandas as pd
    except ImportError:
        return _TimeParseResult(df, False)

    # 已是 datetime 类型，直接返回
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        if keep_str_copy and f'{col}_str' not in df.columns:
            df[f'{col}_str'] = df[col].astype(str)
        return _TimeParseResult(df, True)

    # 保留原始字符串副本（防止覆盖后丢失，B4 关键约束）
    str_col = f'{col}_str'
    if keep_str_copy:
        df[str_col] = df[col].astype(str)
    src = df[str_col] if keep_str_copy else df[col].astype(str)

    # 计算非空数量（覆盖率分母）
    # ⚠️ pandas 3.0+ 中 astype(str) 后 NaN 仍保留为 NaN（不是字符串 'nan'），需先 dropna
    src_nonnull = src.dropna()
    src_clean = src_nonnull[~src_nonnull.astype(str).isin(['nan', 'None', 'NaT', '<NA>', ''])]
    non_null = len(src_clean)
    if non_null == 0:
        # 全空：直接判失败（保持 object dtype，下游可走兜底分支）
        return _TimeParseResult(df, False)

    def _accept(parsed):
        """判定解析结果是否可接受（覆盖率 ≥ min_success_ratio）。"""
        # 仅在原本非空的位置上计算覆盖率，避免被 NULL 拖低
        valid = parsed.loc[src_clean.index].notna().sum()
        return valid >= max(1, int(non_null * min_success_ratio))

    # 策略 1（数值类型优先）：Unix 时间戳（先于自动推断，避免被当作年份解析）
    # is_numeric_dtype 不识别 object 中的纯数字串，所以仅适用于真正的数值列
    if pd.api.types.is_numeric_dtype(df[col]):
        numeric = df[col].astype('float64')
        # 以数量级粗判：10^9 ≤ 秒级 < 10^12；10^12 ≤ 毫秒级 < 10^15
        sample = numeric.dropna().abs()
        if not sample.empty:
            mag = sample.iloc[0]
            unit = 'ms' if mag >= 1e12 else 's'
            ts = pd.to_datetime(numeric, unit=unit, errors='coerce')
            if _accept(ts):
                df[col] = ts
                return _TimeParseResult(df, True)

    # 策略 2：字符串自动推断（covers yyyy-MM-dd / yyyy/M/d / MM/dd/yyyy / 含时间部分 等）
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        parsed = pd.to_datetime(src, errors='coerce')
    if _accept(parsed):
        df[col] = parsed
        return _TimeParseResult(df, True)

    # 策略 3：字符串覆盖率不足 → 截断时间部分（' '/'T' 之前）后重试（针对 '2017/10/2 10:56'）
    # 强制转换为 string 后再用 .str 访问器（防止 src 为数值/混合类型时报错）
    truncated = src.astype(str).str.split(r'[ T]', n=1, regex=True).str[0]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        parsed2 = pd.to_datetime(truncated, errors='coerce')
    if _accept(parsed2):
        df[col] = parsed2
        return _TimeParseResult(df, True)

    # 策略 4：字符串中可能是纯数字串的 Unix 时间戳
    numeric_str = pd.to_numeric(src, errors='coerce')
    if numeric_str.notna().any():
        sample = numeric_str.dropna().abs()
        if not sample.empty:
            mag = sample.iloc[0]
            unit = 'ms' if mag >= 1e12 else 's'
            ts2 = pd.to_datetime(numeric_str, unit=unit, errors='coerce')
            if _accept(ts2):
                df[col] = ts2
                return _TimeParseResult(df, True)

    # 全部失败：保留原 dtype
    return _TimeParseResult(df, False)


def safe_time_groupby(df, col, granularity='month'):
    """安全的时间字段分组键提取（兼容 datetime / 已是目标粒度的字符串）。

    参数:
        df: Pandas DataFrame
        col: 时间字段列名
        granularity: 'day' | 'month' | 'year'

    返回:
        Series：可直接用作 groupby 键（name 属性已设置为 col，reset_index 后列名正确）
            - 已是目标粒度的字符串（如 'YYYY-MM' 长度 7）→ 原样返回
            - datetime 类型 → strftime 提取
            - object 字符串 → 先 to_datetime 再 strftime

    正确用法:
        # ✅ 作为 groupby 键（推荐）
        df.groupby(safe_time_groupby(df, 'dt', 'month')).agg({'sales': 'sum'})

        # ✅ 赋值给新列后再 groupby
        df['month'] = safe_time_groupby(df, 'dt', 'month')
        monthly = df.groupby('month').agg({'sales': 'sum'}).reset_index()

    常见误用（已防护）:
        # ⚠️ 不要将返回值当作 DataFrame 使用
        # result = safe_time_groupby(df, 'dt', 'month')
        # result.agg(...)  ← 这是 Series，不是 DataFrame，但 .agg() 仍可用于 Series
    """
    try:
        import pandas as pd
    except ImportError:
        return df[col]

    fmt_map = {'day': '%Y-%m-%d', 'month': '%Y-%m', 'year': '%Y'}
    fmt = fmt_map.get(granularity, '%Y-%m-%d')
    expected_len = {'day': 10, 'month': 7, 'year': 4}.get(granularity, 10)

    def _named(series):
        """确保返回的 Series.name = col，使 groupby + reset_index 后列名正确。"""
        series.name = col
        return series

    if pd.api.types.is_datetime64_any_dtype(df[col]):
        return _named(df[col].dt.strftime(fmt))

    if df[col].dtype == 'object':
        # 检查是否已是目标粒度
        sample = df[col].dropna()
        if not sample.empty:
            s = str(sample.iloc[0])
            if len(s) == expected_len:
                return _named(df[col].copy())
        # 转换后提取
        dt = pd.to_datetime(df[col], errors='coerce')
        return _named(dt.dt.strftime(fmt))

    # 数值类型（可能是 Unix 时间戳）
    dt = pd.to_datetime(df[col], unit='s', errors='coerce')
    if dt.notna().any():
        return _named(dt.dt.strftime(fmt))
    return _named(df[col].astype(str))


# ===== SQL 安全日期/时间提取（Spark 3.4+，实测平台 Spark 3.5.3 全部 PASS） =====
#
# 🛑 设计目的：专为 sqlSlots SQL（写入 kanban_save_params.json 的 SqlSlots 字段，
#    看板保存后平台周期性自动刷新执行）设计。Spark 3.0+ 严格 DateTimeParser 对裸 TO_DATE/TO_TIMESTAMP
#    在以下场景抛 INCONSISTENT_BEHAVIOR_CROSS_VERSION.PARSE_DATETIME_BY_NEW_PARSER：
#       - 字段实际值含时间尾巴而 format 只到日期 ❌
#       - format 比字段值更长 ❌
#       - CAST string AS DATE 仅支持 yyyy-MM-dd 标准格式 ❌
#
# ✅ 实现方案（依赖 Spark 3.4+ 的 try_to_timestamp + regexp_replace）：
#       表达式 = try_to_timestamp(regexp_replace(col, '[./]', '-'))
#    一次性覆盖所有主流格式（已在生产平台 Spark 3.5.3 实测 PASS）：
#       yyyy-MM-dd / yyyy/M/d / yyyy.M.d，可补零/不补零，
#       可含 ' ' 或 'T' 分隔的时间部分（HH:mm / HH:mm:ss）
#    'null' / 'NULL' / '' / 'garbage' / 无效月日 → 返回 NULL（不抛异常）
#    与 pandas.to_datetime(errors='coerce') 行为对齐
#
# ⚠️ 平台版本前置：try_to_timestamp 自 Spark 3.4.0 引入。如果目标 Spark 集群 < 3.4，
#    helper 生成的 SQL 会抛 UNRESOLVED_ROUTINE / ROUTINE_NOT_FOUND。
#    建议 Step B0 用 `SELECT version()` 探测确认（腾讯 Wedata 当前为 3.5.3）。
#
# ⚠️ 适用范围：仅当字段类型为 string 时使用。物理类型为 date/timestamp 时不需要这些 helper。
# 🛑 物理类型为 long/bigint/integer（Unix 时间戳数字字段）时**禁止套主入口 helper** ——
#    会静默返回全 NULL 不报错（看板"无数据"）。改用 CAST(FROM_UNIXTIME(col) AS TIMESTAMP)（秒）
#    或 CAST(FROM_UNIXTIME(col/1000) AS TIMESTAMP)（毫秒）。详见 sql_syntax_rules.md 铁律 3。
# ⚠️ B3 取数 SQL（一次性，wedatacli query-sql 跑一次即丢）也不需要 helper —— 失败可立即手工重试。
#    详见 sql_syntax_rules.md 顶部「sqlSlots SQL 生成铁律」。
#
# 🛑 helper 严格单参签名（仅接收列名），不接受 format/time_format 参数 ——
#    try_to_timestamp 默认 format 已自动识别 ISO 系格式，无需 Agent 探测/传参。
#    **唯一例外**：spark_safe_date_format(col, output_format='yyyy-MM') 的第二个参数
#    是输出聚合粒度（'yyyy-MM' 按月 / 'yyyy' 按年 / 'yyyy-MM-dd' 按日），允许且必要。
# =====


def spark_safe_to_timestamp(col):
    """单表达式安全解析 string 时间字段为 timestamp（主入口）。

    核心实现：try_to_timestamp(regexp_replace(col, '[./]', '-')) + 低粒度兜底
        1. regexp_replace([./], -) 把 '/' 和 '.' 一次性规范化为 '-'（→ ISO 8601 形态）
        2. try_to_timestamp 默认 format 兼容 ISO：
              yyyy-MM-dd[ HH:mm[:ss[.SSS]]] / yyyy-MM-ddTHH:mm:ss
              支持补零/不补零（M/d、MM/dd 均可）
           解析失败 → 返回 NULL（不抛异常）
        3. 低粒度兜底（2026-06 增强）：数仓 ADS 层 year_month='2017-01' /
           stat_month='201701' / dt='2017' 等纯年/年月字符串列，Spark
           默认 try_to_timestamp 也会返回 NULL（要求至少 yyyy-MM-dd）。
           用 RLIKE 锁形态后调用 to_timestamp(x, 'yyyy-MM' | 'yyyyMM' | 'yyyy')
           严格解析，月份非法（00 / 13+）/ 完整日期 / unix 数字均不会命中。

    覆盖格式（已实测全部 PASS）：
        '2017/10/10 21:25'      → 2017-10-10 21:25:00
        '2017/10/2'             → 2017-10-02 00:00:00（不补零）
        '2017-10-10'            → 2017-10-10 00:00:00
        '2017-10-10 21:25:30'   → 2017-10-10 21:25:30
        '2017-10-10T21:25:30'   → 2017-10-10 21:25:30（ISO-T）
        '2017/10/2T21:25'       → 2017-10-02 21:25:00（斜杠+T 混合）
        '2017.10.10 21:25'      → 2017-10-10 21:25:00（点分隔）
        '2017-01' / '2017/01' / '2017.01' / '2017-1'  → 2017-01-01 00:00:00（低粒度兜底）
        '201701' (yyyyMM)       → 2017-01-01 00:00:00
        '2017'                  → 2017-01-01 00:00:00

    安全返回 NULL（不报错）：
        'null' / 'NULL' / '' / '   ' / 'garbage' / '2017-13-40' / '2017-2-30' / NULL
        '2017-13' / '2017-00' / '20170145' / 'abcd'（非法月份/8 位非日期数字等）

    不支持（默认返回 NULL，如需启用见 spark_safe_to_timestamp_extended）：
        '20171010' 纯 8 位数字（yyyyMMdd）/ Unix 时间戳

    参数:
        col: SQL 列名（string 类型时间字段，无需 quote）

    返回:
        str: 可直接嵌入 SQL 的 timestamp 表达式

    使用方式（在 generate_kanban.py 的 sql_slots_list 中）:
        ts = spark_safe_to_timestamp('order_purchase_timestamp')
        sql = f\"\"\"SELECT DATE_FORMAT({ts}, 'yyyy-MM') AS month, COUNT(*) AS cnt
                 FROM tbl WHERE {ts} IS NOT NULL
                 GROUP BY DATE_FORMAT({ts}, 'yyyy-MM')\"\"\"
    """
    return (
        f"COALESCE("
        # 主路径：标准 ISO / Hive / 业务系统 yyyy-MM-dd[ ...] / yyyy/MM/dd[ ...] / yyyy.MM.dd[ ...]
        f"try_to_timestamp(regexp_replace({col}, '[./]', '-')),"
        # 低粒度兜底：'yyyy-MM' / 'yyyy/MM' / 'yyyy.MM' / 'yyyy-M'（已规范化为 '-' 后用 yyyy-MM 解析）
        f"CASE WHEN {col} RLIKE '^[0-9]{{4}}[-/.][0-9]{{1,2}}$'"
        f" THEN to_timestamp(regexp_replace({col}, '[./]', '-'), 'yyyy-M')"
        # 'yyyyMM' 6 位纯数字（与 yyyymmdd 8 位、unix 10/13 位严格隔离）
        f" WHEN {col} RLIKE '^[0-9]{{6}}$' THEN to_timestamp({col}, 'yyyyMM')"
        # 'yyyy' 4 位纯年
        f" WHEN {col} RLIKE '^[0-9]{{4}}$' THEN to_timestamp({col}, 'yyyy')"
        f" ELSE NULL END,"
        # —— 月份英文缩写/全称兜底（BI 报表/财务数仓常见，2026-06 增强）——
        # 业务背景：order_month='Jan 2025' / 'January 2025' / '25-Jan-2025' / 'Jan-25'
        #   旧主路径 try_to_timestamp(默认 fmt) 全部返回 NULL → 看板"无数据"。
        # 平台前置：Spark 3.4+ 的 try_to_timestamp 第二参支持 DateTimeFormatter pattern；
        #   pattern 'MMM' = Jan/Feb/...，'MMMM' = January/February/...
        # 严格用 RLIKE 锁形态，避免对完整 ISO 字段做无效解析（性能可忽略，但语义更清晰）。
        # 任一命中即返回 timestamp，全 miss 走整个 COALESCE 的最终 NULL，行为与 Spark 默认一致。
        # 字符类中 '-' 放在末尾即字面短横，无需转义；空格放在前面避免被误识别为范围。
        f"CASE WHEN {col} RLIKE '^[A-Za-z]+[ /-][A-Za-z0-9 ,/-]+$' OR "
        f"{col} RLIKE '^[0-9]{{1,2}}[ /-][A-Za-z]+[ /-][0-9]{{2,4}}$' OR "
        f"{col} RLIKE '^[0-9]{{4}}[ /-][A-Za-z]+$'"
        f" THEN COALESCE("
        f"try_to_timestamp({col}, 'MMM yyyy'),"
        f"try_to_timestamp({col}, 'MMMM yyyy'),"
        f"try_to_timestamp({col}, 'MMM-yyyy'),"
        f"try_to_timestamp({col}, 'MMMM-yyyy'),"
        f"try_to_timestamp({col}, 'yyyy-MMM'),"
        f"try_to_timestamp({col}, 'yyyy MMM'),"
        f"try_to_timestamp({col}, 'dd-MMM-yyyy'),"
        f"try_to_timestamp({col}, 'dd MMM yyyy'),"
        f"try_to_timestamp({col}, 'dd-MMMM-yyyy'),"
        f"try_to_timestamp({col}, 'dd MMMM yyyy'),"
        f"try_to_timestamp({col}, 'MMM dd, yyyy'),"
        f"try_to_timestamp({col}, 'MMMM dd, yyyy')"
        f") ELSE NULL END"
        f")"
    )


def spark_safe_to_timestamp_extended(col):
    """扩展版：在主表达式基础上额外识别 yyyyMMdd（8 位纯数字）和 Unix 时间戳。

    覆盖额外格式：
        '20171010'              → 2017-10-10
        '1697644800'   (10 位)  → Unix 秒 → timestamp
        '1697644800000'(13 位)  → Unix 毫秒 → timestamp

    长度比主入口大 4 倍。仅在确认数据含上述格式时启用，否则用主入口
    spark_safe_to_timestamp() 即可。

    参数:
        col: SQL 列名

    返回:
        str: 可直接嵌入 SQL 的 timestamp 表达式
    """
    return (
        f"COALESCE("
        f"try_to_timestamp(regexp_replace({col}, '[./]', '-')),"
        f"try_to_timestamp(regexp_replace({col}, '^([0-9]{{4}})([0-9]{{2}})([0-9]{{2}})$', '$1-$2-$3')),"
        f"CASE WHEN {col} RLIKE '^[0-9]{{10}}$' THEN CAST(from_unixtime(CAST({col} AS BIGINT)) AS TIMESTAMP)"
        f" WHEN {col} RLIKE '^[0-9]{{13}}$' THEN CAST(from_unixtime(CAST({col} AS BIGINT)/1000) AS TIMESTAMP)"
        f" ELSE NULL END"
        f")"
    )


def spark_safe_to_date(col):
    """安全解析 string 时间字段为 date（截断时间部分）。

    等价于 CAST(spark_safe_to_timestamp(col) AS DATE)。

    参数:
        col: SQL 列名

    返回:
        str: 可直接嵌入 SQL 的 date 表达式
    """
    return f"CAST({spark_safe_to_timestamp(col)} AS DATE)"


def spark_safe_date_format(col, output_format='yyyy-MM'):
    """生成 DATE_FORMAT SQL 表达式（用于 GROUP BY 月/年聚合）。

    等价于 DATE_FORMAT(spark_safe_to_timestamp(col), output_format)。

    参数:
        col: SQL 列名（string 类型时间字段）
        output_format: 输出格式（默认 'yyyy-MM' 按月聚合）

    返回:
        str: 可直接嵌入 SQL 的 DATE_FORMAT 表达式

    使用方式:
        month_expr = spark_safe_date_format('order_purchase_timestamp', 'yyyy-MM')
        sql = f\"SELECT {month_expr} AS month, COUNT(*) AS cnt FROM tbl GROUP BY {month_expr}\"

    🛑 输出格式黑名单（H24 修复，fail-fast）：
        Spark 3.x 的 DateTimeFormatter（基于 java.time.format）对部分 pattern 字母不再支持，
        典型如 'w'（week-of-year）/'W'（week-of-month）/'u'（day-of-week ISO）/'D'（day-of-year）
        等。在 sqlSlots SQL 中传入这些 pattern 时，平台周期重跑会直接抛
        SparkUpgradeException（DATETIME_PATTERN_RECOGNITION），看板"无数据"。
        本 helper 在生成 SQL 字符串前预检查并立即抛错，强制 Agent 使用专门的 helper（如
        `spark_safe_week_format` 替代 'yyyy-ww'），避免 bug 漏到平台。
    """
    # H24：周聚合 pattern 自动降级为 spark_safe_week_format（无需手动改中间文件）
    import re as _re
    _stripped = _re.sub(r"'[^']*'", '', output_format)
    if 'w' in _stripped or 'W' in _stripped:
        return spark_safe_week_format(col)
    # 其他黑名单 pattern 仍 fail-fast
    _validate_output_format(output_format)
    return f"DATE_FORMAT({spark_safe_to_timestamp(col)}, '{output_format}')"


def _validate_output_format(output_format):
    """校验 DATE_FORMAT 输出格式 pattern 是否被 Spark 3.x DateTimeFormatter 支持（H24）。

    Spark 3.0+ 切换到 java.time.format.DateTimeFormatter，以下 pattern 字母在 sqlSlots 中
    极易导致 SparkUpgradeException（DATETIME_PATTERN_RECOGNITION），统一拦截：
        w / W : 周序（week-of-year/week-of-month）→ 用 spark_safe_week_format / WEEKOFYEAR
        D     : 一年中的第几天（day-of-year）  → 用 DAYOFYEAR
        u     : ISO 星期几                    → 用 DAYOFWEEK 或 EXTRACT
        Q / q : 季度（quarter）              → 用 QUARTER 函数
    其他常用字母：y/M/d/H/m/s/S（秒以下）/E（星期名）已通过 Spark 兼容验证，允许。
    """
    if not output_format:
        raise ValueError(
            "spark_safe_date_format(output_format=...) 不能为空。"
            "推荐：'yyyy-MM'（月）、'yyyy-MM-dd'（日）、'yyyy'（年）。"
        )
    # 简化处理：扫描裸字母（不在引号包裹的字面文本中）
    import re as _re
    # 移除单引号包裹的字面值后再扫描 pattern 字母
    stripped = _re.sub(r"'[^']*'", '', output_format)
    bad_letters = {
        'w': "周序（week-of-year）",
        'W': "周序（week-of-month）",
        'D': "day-of-year",
        'u': "ISO 星期几",
        'Q': "季度",
        'q': "季度",
    }
    found = [c for c in bad_letters if c in stripped]
    if found:
        details = "、".join(f"'{c}'（{bad_letters[c]}）" for c in found)
        raise ValueError(
            f"❌ spark_safe_date_format output_format='{output_format}' 含 Spark 3.x 不支持的 pattern: {details}。\n"
            f"📌 H24 已知问题：'yyyy-ww'/'yyyy-W' 等周/年内日序 pattern 在平台周期重跑时\n"
            f"   抛 SparkUpgradeException（DATETIME_PATTERN_RECOGNITION），看板将无数据。\n"
            f"💡 修复方案：\n"
            f"   ① 周聚合 → 改用 `spark_safe_week_format(col)`（输出 'yyyy-WNN' 形式 ISO 周）\n"
            f"   ② 季度聚合 → `CONCAT(CAST(YEAR(<ts>) AS STRING),'-Q',CAST(QUARTER(<ts>) AS STRING))`\n"
            f"   ③ 一年中第几天 → `DAYOFYEAR(<ts>)`\n"
            f"   ④ ISO 星期几 → `DAYOFWEEK(<ts>)`（注意 Spark 1=Sunday）\n"
            f"   仅当 output_format 为 'yyyy' / 'yyyy-MM' / 'yyyy-MM-dd' / 'yyyy-MM-dd HH:mm:ss' 等\n"
            f"   仅含 y/M/d/H/m/s 字母组合时本 helper 才安全。"
        )


def spark_safe_week_format(col):
    """生成 ISO 周聚合 SQL 表达式（输出 'yyyy-WNN' 形式，可直接 GROUP BY/ORDER BY）。

    等价于 DATE_FORMAT(<ts>, 'yyyy-ww')，但避开 Spark 3.x 不支持 'ww' pattern 的问题。
    底层用 YEAR + WEEKOFYEAR + LPAD + CONCAT 拼接，所有函数 Spark 3.x 完全兼容。

    使用方式:
        week_expr = spark_safe_week_format('order_purchase_timestamp')
        sql = f\"\"\"
            SELECT {week_expr} AS week, SUM(sales) AS sales
            FROM tbl WHERE {spark_safe_to_timestamp('order_purchase_timestamp')} IS NOT NULL
            GROUP BY {week_expr} ORDER BY {week_expr}
        \"\"\"

    输出形式: '2023-W01', '2023-W52', '2024-W01', ...

    ⚠️ 注意：WEEKOFYEAR 在跨年周（如 2024-01-01 实际属于 2023-W52）会产生跨年错位，
    若需严格 ISO 8601 周年（YearOfWeek），需用 EXTRACT(YEAROFWEEK FROM <ts>) 替代 YEAR。
    本 helper 默认用 YEAR(<ts>) 与日历年对齐，业务可读性更高，适合大多数运营看板场景。
    """
    ts = spark_safe_to_timestamp(col)
    return (
        f"CONCAT(CAST(YEAR({ts}) AS STRING), '-W', "
        f"LPAD(CAST(WEEKOFYEAR({ts}) AS STRING), 2, '0'))"
    )


def spark_safe_datediff(end_col, start_col):
    """生成 DATEDIFF SQL 表达式（天数差，Spark 两参数语法）。

    等价于 DATEDIFF(spark_safe_to_timestamp(end_col), spark_safe_to_timestamp(start_col))。

    参数:
        end_col: 结束日期列名
        start_col: 开始日期列名

    返回:
        str: 可直接嵌入 SQL 的 DATEDIFF 表达式

    使用方式:
        dd = spark_safe_datediff('order_delivered_customer_date', 'order_purchase_timestamp')
        sql = f\"SELECT AVG({dd}) AS avg_days FROM tbl WHERE {dd} IS NOT NULL\"
    """
    return f"DATEDIFF({spark_safe_to_timestamp(end_col)}, {spark_safe_to_timestamp(start_col)})"


def build_save_meta(workspace_id, resource_id, sql_slots_list,
                    display_name: str = ''):
    """
    构建保存参数字典（三端统一入库形态 —— HtmlContent/SqlSlots 由
    kanban_dsl_emitter 写入最终 DSL/Datasets）。

    参数:
        workspace_id: 工作空间 ID
        resource_id: 执行资源 ID
        sql_slots_list: SQL 插槽定义列表（本函数不再序列化写入 SqlSlots 字段，
                        仅保留形参以便未来扩展；SqlSlots 由 emitter 用 Datasets 写入）
        display_name: 看板显示名（一般直接来自 spec.title；空则回退为 '未命名看板'）

    返回:
        保存参数字典
    """
    display_name = (display_name or '').strip() or '未命名看板'

    # 🛡️ workspace_id 为空时多级降级自动补充（沙箱兼容）
    if not workspace_id:
        # 降级1：环境变量（wedatacli 启动时可能注入）
        workspace_id = os.environ.get('TENCENTCLOUD_WORKSPACE_ID', '')
        if workspace_id:
            print(f'⚠️ workspace_id 参数为空，已从环境变量 TENCENTCLOUD_WORKSPACE_ID 补充: {workspace_id}')
        else:
            # 降级2：从 ~/.wedata/config.json 的 defaultWorkspace 字段读取（沙箱中最稳定方式）
            config_path_ws = os.path.expanduser('~/.wedata/config.json')
            if os.path.isfile(config_path_ws):
                try:
                    with open(config_path_ws, 'r') as cf_ws:
                        config_ws = json.load(cf_ws)
                    workspace_id = str(config_ws.get('defaultWorkspace', ''))
                    if workspace_id:
                        print(f'⚠️ workspace_id 参数为空，已从 ~/.wedata/config.json defaultWorkspace 补充: {workspace_id}')
                except (json.JSONDecodeError, IOError) as e:
                    print(f'WARN: 读取 ~/.wedata/config.json 失败: {e}')
            if not workspace_id:
                print('WARN: workspace_id 为空，环境变量和 config.json 均无法获取，保存时将失败')

    # 三端统一入库 —— HtmlContent / SqlSlots 由 emitter 在最终 params 中写入；
    # 只有 DSL/Datasets 构造成功后才落盘，避免中间态文件污染。
    save_meta = {
        "WorkspaceId": workspace_id,
        "DisplayName": display_name,
        "ExecuteResourceId": resource_id,
        "SourceType": "dsl",
    }

    # SessionTag
    session_tag_obj = {}
    runtime_id = os.environ.get('AGENTOS_RUNTIME_ID', '')
    if runtime_id:
        session_tag_obj['runtimeId'] = runtime_id

    config_path = os.path.expanduser('~/.wedata/config.json')
    if os.path.isfile(config_path):
        try:
            with open(config_path, 'r') as cf:
                config = json.load(cf)
            analysis_space_key = config.get('analysisSpaceKey', '')
            if analysis_space_key:
                session_tag_obj['analysisSpaceKey'] = analysis_space_key
        except (json.JSONDecodeError, IOError):
            pass

    if session_tag_obj:
        save_meta['SessionTag'] = json.dumps(session_tag_obj, ensure_ascii=False)

    return save_meta


# ===== sqlSlots SQL 反模式 lint（P0 #10.5 强制 - 必须先于其他校验）=====
#
# 设计目的：拦截 Agent 在 sqlSlots SQL 中裸用 CAST/TO_DATE/TO_TIMESTAMP/DATEDIFF/DATE_FORMAT
# 处理 string 类型时间字段的行为（违反 P0 #10.5）。
#
# 关键设计：
#   1. 错误信息直接指向 P0 #10.5（不让 Agent 误以为是其他问题）
#   2. 错误信息附带 helper 调用模板（Agent 能直接复制粘贴修复）
#   3. 智能跳过：纯数字常量参数（如 ROUND(x, 2) 第二参）、date 类型字段（无法精确判断时给 WARN 而非 FATAL）
#   4. 仅校验 sqlSlots（不动 B3 取数 SQL，B3 允许裸 SQL）

# 反模式正则：在 sqlSlots SQL 中禁止出现的裸 SQL 构造
# 注意：必须排除 "spark_safe_*" helper 内部已经合法使用 try_to_timestamp / regexp_replace 的情况
_SQLSLOTS_BANNED_PATTERNS = [
    # (pattern, name, fix_template_key)
    (re.compile(r'\bCAST\s*\(\s*[\w.]+\s+AS\s+(DATE|TIMESTAMP)\b', re.IGNORECASE),
     'CAST(col AS DATE/TIMESTAMP)',
     'cast'),
    (re.compile(r'\bTO_DATE\s*\(\s*[\w.]+\s*,', re.IGNORECASE),
     "TO_DATE(col, 'fmt')",
     'to_date'),
    (re.compile(r'\bTO_TIMESTAMP\s*\(\s*[\w.]+\s*,', re.IGNORECASE),
     "TO_TIMESTAMP(col, 'fmt')",
     'to_timestamp'),
    (re.compile(r'\bDATE_FORMAT\s*\(\s*(?!try_to_timestamp\b)[\w.]+\s*,', re.IGNORECASE),
     "DATE_FORMAT(col, 'fmt')（col 为 string 时）",
     'date_format'),
    (re.compile(r'\bDATEDIFF\s*\(\s*(?!try_to_timestamp\b)[\w.]+\s*,\s*(?!try_to_timestamp\b)[\w.]+\s*\)', re.IGNORECASE),
     'DATEDIFF(end, start)（任一为 string 时）',
     'datediff'),
    # YEAR / MONTH / DAY / QUARTER / WEEK / HOUR / MINUTE / SECOND / DAYOFWEEK 等裸时间提取函数：
    # 在 string 类型时间字段（运行期类型为 VARCHAR）上直接调用会报
    # `No function matches year(VARCHAR)` 类错误，本地预览数据全空 + 平台 Spark 端
    # 也会报 InvalidTypeException。必须先 spark_safe_to_timestamp(col) 再提取。
    # 排除 spark_safe_to_timestamp(...) 已包裹的情形 + 形如 YEAR(2018) 的整数常量。
    (re.compile(
        r'\b(YEAR|MONTH|DAY|QUARTER|WEEK|WEEKOFYEAR|HOUR|MINUTE|SECOND|DAYOFWEEK|DAYOFMONTH|DAYOFYEAR)\s*\(\s*'
        r'(?!\s*spark_safe_to_timestamp\b)'   # 已包裹则放行
        r'(?!\s*spark_safe_to_date\b)'         # 已包裹则放行
        r'(?!\s*-?\d)'                         # 数字常量放行
        r'[\w.]+\s*\)',
        re.IGNORECASE),
     'YEAR/MONTH/DAY/QUARTER/HOUR(col)（col 为 string 时）',
     'extract_part'),
    # EXTRACT(YEAR FROM col) / EXTRACT(MONTH FROM col) 同源 —— SQL 标准写法但同样要求 col 是 timestamp/date
    (re.compile(
        r'\bEXTRACT\s*\(\s*(YEAR|MONTH|DAY|QUARTER|WEEK|HOUR|MINUTE|SECOND|DOW|DOY|EPOCH)\s+FROM\s+'
        r'(?!\s*spark_safe_to_timestamp\b)'
        r'(?!\s*spark_safe_to_date\b)'
        r'[\w.]+\s*\)',
        re.IGNORECASE),
     'EXTRACT(part FROM col)（col 为 string 时）',
     'extract_part'),
    # WHERE col != 'null' 的字符串 hack
    (re.compile(r"!=\s*['\"]null['\"]", re.IGNORECASE),
     "WHERE col != 'null'",
     'null_hack'),
    # 嵌套聚合：AGG(AGG(...))，Spark 严格禁止
    (re.compile(
        r'\b(MIN|MAX|SUM|AVG|COUNT|PERCENTILE|PERCENTILE_APPROX|COLLECT_LIST|COLLECT_SET)\s*\('
        r'[^)]*\b(MIN|MAX|SUM|AVG|COUNT|PERCENTILE|PERCENTILE_APPROX)\s*\(',
        re.IGNORECASE),
     '嵌套聚合函数 AGG(AGG(...))',
     'nested_agg'),
    # 非确定性表达式在聚合内：AVG(RAND()*...)
    (re.compile(
        r'\b(MIN|MAX|SUM|AVG|COUNT)\s*\([^)]*\b(RAND|UUID|RANDOM)\s*\(',
        re.IGNORECASE),
     '聚合内使用非确定性函数 AGG(RAND()/UUID())',
     'nondeterministic_in_agg'),
    # CURRENT_TIMESTAMP / NOW() / CURRENT_DATE：raw_sql 中与 timestamp_tz/string 时间列
    # 比较，DuckDB 体检会因「VARCHAR vs TIMESTAMPTZ」类型不匹配阻断（runner 把 timestamp_tz
    # 列降级为 VARCHAR）。即便能跑通，业务上 90% 的看板数据都是历史数据，「与当前时间比较」
    # 多半是误用——应改为字面量上限。本反模式仅作 WARN（不阻断），但给出明确指路。
    (re.compile(r'\bCURRENT_TIMESTAMP\b(?!\s*\(\s*\))', re.IGNORECASE),
     'CURRENT_TIMESTAMP（raw_sql 中与 timestamp_tz/VARCHAR 列比较会失败）',
     'current_timestamp'),
    (re.compile(r'\bNOW\s*\(\s*\)', re.IGNORECASE),
     'NOW()（raw_sql 中与 timestamp_tz/VARCHAR 列比较会失败）',
     'current_timestamp'),
    (re.compile(r'\bCURRENT_DATE\b(?!\s*\(\s*\))', re.IGNORECASE),
     'CURRENT_DATE（raw_sql 中与 string 时间列比较会失败）',
     'current_timestamp'),
]

# 修复模板（直接复用到错误信息，让 Agent 复制粘贴）
_HELPER_FIX_TEMPLATES = {
    'cast': (
        "# ❌ 禁止：CAST(col AS DATE/TIMESTAMP)\n"
        "# ✅ 正确：\n"
        "ts_expr   = spark_safe_to_timestamp('your_col')   # 替代 CAST(col AS TIMESTAMP)\n"
        "date_expr = spark_safe_to_date('your_col')        # 替代 CAST(col AS DATE)"
    ),
    'to_date': (
        "# ❌ 禁止：TO_DATE(col, 'yyyy-MM-dd')\n"
        "# ✅ 正确（helper 自动识别 ISO 系格式，无需传 fmt）：\n"
        "date_expr = spark_safe_to_date('your_col')"
    ),
    'to_timestamp': (
        "# ❌ 禁止：TO_TIMESTAMP(col, 'yyyy-MM-dd HH:mm:ss')\n"
        "# ✅ 正确：\n"
        "ts_expr = spark_safe_to_timestamp('your_col')"
    ),
    'date_format': (
        "# ❌ 禁止：DATE_FORMAT(col, 'yyyy-MM')  ← col 为 string 时\n"
        "# ✅ 正确（output_format 是输出粒度，允许传）：\n"
        "month_expr = spark_safe_date_format('your_col', output_format='yyyy-MM')"
    ),
    'datediff': (
        "# ❌ 禁止：DATEDIFF(end_col, start_col)  ← 任一为 string 时\n"
        "# ✅ 正确：\n"
        "diff_expr = spark_safe_datediff('end_col', 'start_col')"
    ),
    'extract_part': (
        "# ❌ 禁止：YEAR(col) / MONTH(col) / EXTRACT(YEAR FROM col)  ← col 为 string 时\n"
        "#   - 本地 DuckDB 报 `No function matches year(VARCHAR)`，\n"
        "#     图表本地预览数据全空（HTML 仍渲染但只有标题，无数据点）。\n"
        "#   - Spark 端虽兼容但语义依赖 session timezone，跨时区聚合会失真。\n"
        "# ✅ 正确（先 helper 包裹，再提取年/月/日）：\n"
        "ts_expr = spark_safe_to_timestamp('order_purchase_timestamp')\n"
        "sql = f\"WHERE YEAR({ts_expr}) = 2018\"        # YEAR(spark_safe_to_timestamp(col))\n"
        "# ✅ 月度聚合（更推荐用 spark_safe_date_format 直接出 'yyyy-MM' 字符串）：\n"
        "month_expr = spark_safe_date_format('order_purchase_timestamp', output_format='yyyy-MM')"
    ),
    'null_hack': (
        "# ❌ 禁止：WHERE col != 'null'  （漏过 NULL/大小写/空格变体）\n"
        "# ✅ 正确：\n"
        "ts_expr = spark_safe_to_timestamp('your_col')\n"
        "sql = f\"... WHERE {ts_expr} IS NOT NULL\""
    ),
    'nested_agg': (
        "# ❌ 禁止：PERCENTILE(COUNT(*), 0.25) / MIN(COUNT(*)) 等嵌套聚合\n"
        "# ✅ 正确：用 WITH 子查询先算内层聚合，外层再做统计\n"
        "sql = f\"\"\"WITH daily AS (\n"
        "  SELECT date_col, COUNT(*) AS cnt FROM t GROUP BY date_col\n"
        ")\n"
        "SELECT PERCENTILE(cnt, 0.25) AS q1, PERCENTILE(cnt, 0.5) AS median\n"
        "FROM daily\"\"\""
    ),
    'nondeterministic_in_agg': (
        "# ❌ 禁止：AVG(RAND()*30) / SUM(RANDOM()) 等聚合内使用非确定性函数\n"
        "# ✅ 正确：使用真实字段计算，若无真实字段则不应创建该组件\n"
        "# 如需模拟数据，应在 SLOT_DATA 中用 Pandas 生成，sqlSlots 留空或使用真实字段"
    ),
    'current_timestamp': (
        "# ❌ 禁止：raw_sql 中 `WHERE col > CURRENT_TIMESTAMP` / `NOW() - col` / `CURRENT_DATE - col`\n"
        "#   - runner 把 timestamp_tz/timestamp 列在 DuckDB 体检阶段统一降级为 VARCHAR\n"
        "#   - VARCHAR 列与 TIMESTAMPTZ/DATE 比较会引发 'No function matches >' 类错误，本地体检阻断\n"
        "#   - 即便绕过体检，远端 Spark 与本地 DuckDB 对 timestamp_tz 的处理也不一致\n"
        "# ✅ 修法 A（推荐，多数看板数据是历史快照、不需要『当前时间』语义）：\n"
        "#     用业务字面量上限替代：WHERE col >= '2018-01-01' AND col < '2019-01-01'\n"
        "# ✅ 修法 B（确实需要『相对当前』）：列必须先 helper 包裹，再与 NOW() 字面量比较\n"
        "ts_expr = spark_safe_to_timestamp('order_purchase_timestamp')\n"
        "sql = f\"... WHERE {ts_expr} > NOW() - INTERVAL 30 DAY\"   # 列在左，常量在右\n"
        "# ✅ 修法 C（KPI/单值想取『近 N 天』）：用 kpi(from_sql=) 而非 raw_sql，from_sql 由 runner\n"
        "#     编译为标量子查询，时间过滤同样要 spark_safe_to_timestamp 包列"
    ),
}


# ===== 派生指标硬编码常量 lint（P0 #10.6 强制） =====
#
# 防御目标：metrics 声称是同/环/比/率/增长率等派生指标，但 SQL 把它写成 `0.0 AS xxx_rate`
#         / `NULL AS yyy_pct` 等常量占位 → 平台周期刷新永远算出常量、看板"无数据"。
#
# 命名收敛：仅匹配"双词复合"派生命名（mom_xxx / xxx_pct / xxx_rate / sales_yoy 等），
#         避免误伤业务字段（如单词 rate / change / diff 在业务字段中常见）。

_DERIVED_METRIC_NAME_RE = re.compile(
    r'^('
    r'(mom|yoy|wow|qoq|dod|chain|growth)_\w+'      # 前缀：mom_rate / yoy_value / wow_pct
    r'|\w+_(mom|yoy|wow|qoq|dod|chain|growth)'     # 后缀：sales_mom / gmv_yoy / orders_wow
    r'|\w+_(pct|ratio)'                            # 比率后缀：mom_pct / conversion_ratio
    r'|(mom|yoy|wow|qoq|dod)_(rate|pct|ratio)'     # 复合：mom_rate / yoy_pct / wow_ratio
    r')$',
    re.IGNORECASE,
)

# SQL 中"真实计算"的信号：命中任一即视为非常量（豁免本校验）
_DERIVED_CALC_SIGNALS_RE = re.compile(
    r'\b(LAG|LEAD|FIRST_VALUE|LAST_VALUE)\s*\(|'   # 窗口对比函数
    r'\bOVER\s*\(|'                                # 窗口子句
    r'\bWITH\s+\w+\s+AS\s*\(|'                     # CTE
    r'\bJOIN\b|'                                   # 自联（取去年同月等）
    r'\bNULLIF\s*\(|'                              # 比率防除零（说明在做除法）
    r'\bCASE\s+WHEN\b',                            # CASE 计算
    re.IGNORECASE,
)
def _strip_sql_comments_and_strings(sql):
    """剥离 SQL 中的注释和字符串字面值，避免误匹配（如字符串里的 'CAST(x AS DATE)'）。

    剥离顺序：
      1. /* ... */ 块注释
      2. -- ... 行注释
      3. '...' 单引号字符串（含 '' 转义）
      4. "..." 双引号字符串（Spark 中用于标识符，通常无 SQL 关键字但保险起见）
    """
    # 块注释
    sql = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
    # 行注释
    sql = re.sub(r'--[^\n]*', ' ', sql)
    # 单引号字符串
    sql = re.sub(r"'(?:[^']|'')*'", "''", sql)
    # 反引号标识符（保留为占位避免误判，但内容剔除）
    sql = re.sub(r'`[^`]*`', '``', sql)
    return sql


def _extract_select_body(sql):
    """提取最外层 SELECT 与对应 FROM 之间的"列定义主体"，正确处理嵌套子查询。

    算法：用括号深度计数，找出最外层 SELECT（depth==0）后第一个 depth==0 的 FROM。
    返回 SELECT…FROM 之间的字符串。无 FROM 时返回 SELECT 之后所有内容。
    若无 SELECT 关键字，返回原 SQL（保守降级）。
    """
    clean = _strip_sql_comments_and_strings(sql)

    # 1. 找最外层（depth==0）的 SELECT 起点
    select_start = None
    depth = 0
    i = 0
    while i < len(clean):
        ch = clean[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif depth == 0:
            # 在 depth==0 处匹配 SELECT 单词边界
            if i + 6 <= len(clean) and clean[i:i+6].upper() == 'SELECT':
                # 检查单词边界
                prev_ok = (i == 0) or (not clean[i-1].isalnum() and clean[i-1] != '_')
                next_ch = clean[i+6] if i + 6 < len(clean) else ' '
                next_ok = (not next_ch.isalnum() and next_ch != '_')
                if prev_ok and next_ok:
                    select_start = i + 6
                    break
        i += 1

    if select_start is None:
        return clean  # 没找到 SELECT，保守降级

    # 2. 从 select_start 开始，找 depth==0 的 FROM
    depth = 0
    body_end = len(clean)
    j = select_start
    while j < len(clean):
        ch = clean[j]
        if ch == '(':
            depth += 1
        elif ch == ')':
            # 防御性：depth 可能因为外层多了 ) 变负
            if depth > 0:
                depth -= 1
        elif depth == 0:
            if j + 4 <= len(clean) and clean[j:j+4].upper() == 'FROM':
                prev_ok = (not clean[j-1].isalnum() and clean[j-1] != '_')
                next_ch = clean[j+4] if j + 4 < len(clean) else ' '
                next_ok = (not next_ch.isalnum() and next_ch != '_')
                if prev_ok and next_ok:
                    body_end = j
                    break
        j += 1

    return clean[select_start:body_end]


def _count_select_columns_via_as(sql):
    """通过 SELECT 主体中的顶层 AS 别名估算列数。

    精化措施：
      1. 用 _extract_select_body 取出"外层 SELECT…外层 FROM"之间的内容（不会被子查询的 FROM 截断）
      2. 把 SELECT 主体里的 `CAST(... AS TYPE)` 整段抠掉（CAST 的 AS 是类型转换，不代表新列）
      3. 把每列定义中 OVER(...) 部分抠掉（窗口函数内部不会有列定义 AS）
      4. 剩余文本统计 `\\bAS\\b` 次数

    返回 int 或 None（无法估计列数时返回 None，让 KPI 校验跳过）。
    """
    body = _extract_select_body(sql)
    if not body or not body.strip():
        return None

    # 抠掉 CAST(... AS TYPE) 的内部 AS（递归处理嵌套 CAST）
    # 简化方案：把 CAST(...) 整段替换为单个标识符 `_cast_expr_`
    # 用括号匹配抠出 CAST(...) 整体
    def _strip_balanced(text, keyword):
        """把所有 keyword(...) 的整段（含匹配括号）替换为 keyword_"""
        result = []
        i = 0
        klen = len(keyword)
        while i < len(text):
            # 单词边界检查 + 匹配 keyword + 可选空白 + (
            if (i + klen + 1 <= len(text)
                and text[i:i+klen].upper() == keyword.upper()
                and (i == 0 or (not text[i-1].isalnum() and text[i-1] != '_'))):
                # 寻找紧跟 keyword 之后的 '('
                k = i + klen
                while k < len(text) and text[k] in ' \t\n':
                    k += 1
                if k < len(text) and text[k] == '(':
                    # 找匹配的 )
                    depth = 1
                    p = k + 1
                    while p < len(text) and depth > 0:
                        if text[p] == '(':
                            depth += 1
                        elif text[p] == ')':
                            depth -= 1
                        p += 1
                    if depth == 0:
                        result.append(f'{keyword}_')
                        i = p
                        continue
            result.append(text[i])
            i += 1
        return ''.join(result)

    body = _strip_balanced(body, 'CAST')
    body = _strip_balanced(body, 'OVER')

    as_count = len(re.findall(r'\bAS\b', body, re.IGNORECASE))
    return as_count if as_count > 0 else None


# ─────────────────────────────────────────────────────────────────────────────
# 窗口函数双层结构校验（P0 #10.7 / 铁律 7 / H32）
# ─────────────────────────────────────────────────────────────────────────────
# Spark 不支持 OVER 子句或窗口表达式中引用同一 SELECT 层的列别名（LATERAL_COLUMN_ALIAS_IN_WINDOW）。
# 必须使用 WITH agg AS (...) SELECT ..., LAG(<已聚合列>) OVER (...) FROM agg 双层结构。
_WINDOW_FUNC_RE = re.compile(
    r'\b(LAG|LEAD|ROW_NUMBER|RANK|DENSE_RANK|FIRST_VALUE|LAST_VALUE|NTILE|PERCENT_RANK|CUME_DIST)\s*\(',
    re.IGNORECASE,
)
# OVER 单独出现（如 SUM(x) OVER (...) / AVG(x) OVER (...)）也算窗口
_WINDOW_OVER_RE = re.compile(r'\bOVER\s*\(', re.IGNORECASE)
# 子查询信号：WITH ... AS ( 或 FROM (SELECT
_HAS_SUBQUERY_RE = re.compile(
    r'\bWITH\s+\w+\s+AS\s*\(|\bFROM\s*\(\s*SELECT\b',
    re.IGNORECASE,
)
# 豁免标记
_WINDOW_EXEMPT_MARKER_RE = re.compile(r'--\s*@lint-allow:\s*native-window', re.IGNORECASE)
_WINDOW_EXEMPT_INLINE_SQL_RE = re.compile(
    r'--[^\n]*?@lint-allow:[^\n]*?\b(WITH|SELECT|INSERT|UPDATE|DELETE|MERGE|VALUES|FROM)\b',
    re.IGNORECASE,
)


def _validate_window_function_scope(sql_slots_list):
    """校验 sqlSlots 中含窗口函数的 SQL 必须用「WITH 聚合 → SELECT 窗口」双层结构（P0 #10.7 / 铁律 7）。

    背景（H32）：
        Spark 不支持在 `OVER` 子句或窗口表达式里引用同一 SELECT 层的列别名（与 MySQL/PG 不同）。
        Agent 凭直觉写出单层 SELECT + 同层别名的同/环比 SQL（如
        `SELECT m AS month, COUNT(*) AS order_count, LAG(order_count,1) OVER (ORDER BY m) ...`）
        在本地 Pandas 切片完全跑不到，但保存到平台后周期重跑必抛
        `[UNSUPPORTED_FEATURE.LATERAL_COLUMN_ALIAS_IN_WINDOW]` 或 `[UNRESOLVED_COLUMN.WITH_SUGGESTION]`。

    检测条件（同时满足 = 违规）：
        ① SQL 含窗口函数关键字（LAG/LEAD/ROW_NUMBER/RANK/.../OVER）
        ② SQL 中没有外层 `WITH ... AS (` 或 `FROM (SELECT ...)` 子查询结构
        → 几乎 100% 会触发 LCA-IN-WINDOW，必须改写为双层。

    🚪 豁免机制：SQL 中含 `-- @lint-allow: native-window` 注释（适用于 ROW_NUMBER() OVER () 给原始行打号
       且不引用任何聚合的场景）。豁免注释禁止与 SQL 主体同行（与铁律 1/6 一致）。
    """
    if not sql_slots_list:
        return

    violations = []  # [(slot_key, snippet)]
    for slot_def in sql_slots_list:
        key = slot_def.get('key', '')
        raw_sql = slot_def.get('sql', '') or ''
        if not raw_sql.strip():
            continue

        # 🛰️ OLAP 分流（sqlType == 3，MySQL/PG/GaussDB/StarRocks/Doris）：
        #    OLAP 数据源本身支持 LATERAL COLUMN ALIAS IN WINDOW（MySQL 8+/PG/Doris/SR 全部支持），
        #    不需要 Spark 的「WITH 聚合 → SELECT 窗口」双层结构；直接跳过。
        if int(slot_def.get('sqlType') or 0) == 3:
            print(f'  ⏭️ slot "{key}" sqlType=3（OLAP），跳过 Spark 窗口双层结构校验')
            continue

        # 🚪 豁免标记检测（必须在剥离注释前检测）
        if _WINDOW_EXEMPT_MARKER_RE.search(raw_sql):
            if _WINDOW_EXEMPT_INLINE_SQL_RE.search(raw_sql):
                raise ValueError(
                    '\n'
                    f'🚨 sqlSlots 豁免注释格式错误（P0 强制：与 SQL 主体在同一行）\n'
                    f'   slot "{key}" 的 `-- @lint-allow: native-window` 豁免注释未以换行符结束，\n'
                    f'   SQL 主体被 `--` 单行注释吞掉，平台 SQL 溯源面板将显示为非 SQL 内容。\n'
                    '\n'
                    '✅ 正确写法（推荐用三引号多行字符串，物理换行最稳）：\n'
                    '   sql = """-- @lint-allow: native-window（说明：纯 ROW_NUMBER 不引用聚合）\n'
                    '   SELECT order_id, ROW_NUMBER() OVER (ORDER BY order_purchase_timestamp) AS rn\n'
                    '   FROM DataLakeCatalog.default.tiny_orders"""\n'
                    '\n'
                    '📖 完整规则见：sql_syntax_rules.md 铁律 7 豁免章节'
                )
            print(f'  ⏭️ slot "{key}" 含 @lint-allow:native-window 豁免标记，跳过 P0 #10.7 校验')
            continue

        clean_sql = _strip_sql_comments_and_strings(raw_sql)
        # 命中条件 ①：含窗口函数关键字
        has_window = bool(_WINDOW_FUNC_RE.search(clean_sql) or _WINDOW_OVER_RE.search(clean_sql))
        if not has_window:
            continue
        # 命中条件 ②：没有 WITH / FROM (SELECT 子查询
        has_subquery = bool(_HAS_SUBQUERY_RE.search(clean_sql))
        if has_subquery:
            continue
        # 两条件同时命中 → 违规
        snippet = raw_sql.strip().replace('\n', ' ')
        if len(snippet) > 220:
            snippet = snippet[:220] + ' ...'
        violations.append((key, snippet))

    if not violations:
        return

    error_lines = ['']
    error_lines.append('🚨 窗口函数双层结构校验失败（P0 #10.7 / 铁律 7 / H32 违反）：')
    error_lines.append('   sqlSlots SQL 使用了窗口函数（LAG/LEAD/ROW_NUMBER/.../OVER），')
    error_lines.append('   但未采用「WITH 聚合 → SELECT 窗口」双层结构。')
    error_lines.append('   Spark 不支持 OVER 子句引用同 SELECT 层别名（LATERAL_COLUMN_ALIAS_IN_WINDOW），')
    error_lines.append('   平台周期重跑时必抛 [UNSUPPORTED_FEATURE.LATERAL_COLUMN_ALIAS_IN_WINDOW]')
    error_lines.append('   或 [UNRESOLVED_COLUMN.WITH_SUGGESTION]，看板"无数据"。')
    error_lines.append('')
    for slot_key, snippet in violations:
        error_lines.append(f'   ❌ slot "{slot_key}" SQL：{snippet}')
    error_lines.append('')
    error_lines.append('💡 修复模板（直接复制到 generate_kanban.py）：')
    error_lines.append('')
    error_lines.append('   month_expr = spark_safe_date_format("order_purchase_timestamp", "yyyy-MM")')
    error_lines.append('   ts_expr    = spark_safe_to_timestamp("order_purchase_timestamp")')
    error_lines.append('')
    error_lines.append('   # ─── 同/环比月趋势：WITH 聚合 → 外层窗口（OVER 内只引用 WITH 别名）─────')
    error_lines.append('   sql = (')
    error_lines.append('       f"WITH m AS (SELECT {month_expr} AS month, COUNT(*) AS order_count "')
    error_lines.append('       f"FROM {TBL} WHERE {ts_expr} IS NOT NULL GROUP BY {month_expr}) "')
    error_lines.append('       f"SELECT month, order_count, "')
    error_lines.append('       f"  ROUND((order_count - LAG(order_count,1)  OVER (ORDER BY month))"')
    error_lines.append('       f"        / NULLIF(LAG(order_count,1)  OVER (ORDER BY month), 0) * 100, 2) AS mom_rate, "')
    error_lines.append('       f"  ROUND((order_count - LAG(order_count,12) OVER (ORDER BY month))"')
    error_lines.append('       f"        / NULLIF(LAG(order_count,12) OVER (ORDER BY month), 0) * 100, 2) AS yoy_rate "')
    error_lines.append('       f"FROM m ORDER BY month"')
    error_lines.append('   )')
    error_lines.append('')
    error_lines.append('   # ─── K 线（开盘价 = 上期收盘）：子查询 t 内 AS 已就位，外层 OVER 只引用 t 的别名 ─')
    error_lines.append('   sql = (')
    error_lines.append('       f"WITH t AS (SELECT {month_expr} AS month, COUNT(*) AS cnt "')
    error_lines.append('       f"FROM {TBL} WHERE {ts_expr} IS NOT NULL GROUP BY {month_expr}) "')
    error_lines.append('       f"SELECT month, "')
    error_lines.append('       f"  COALESCE(LAG(cnt,1) OVER (ORDER BY month), cnt) AS open_orders, "')
    error_lines.append('       f"  cnt AS close_orders, "')
    error_lines.append('       f"  ROUND(cnt * 0.9, 0) AS low_orders, "')
    error_lines.append('       f"  ROUND(cnt * 1.1, 0) AS high_orders "')
    error_lines.append('       f"FROM t ORDER BY month"')
    error_lines.append('   )')
    error_lines.append('')
    error_lines.append('   # ─── 周环比：week_expr 必须用 spark_safe_week_format（铁律 1.1）─────────')
    error_lines.append('   week_expr = spark_safe_week_format("order_purchase_timestamp")')
    error_lines.append('   sql = (')
    error_lines.append('       f"WITH w AS (SELECT {week_expr} AS week, COUNT(*) AS order_count "')
    error_lines.append('       f"FROM {TBL} WHERE {ts_expr} IS NOT NULL GROUP BY {week_expr}) "')
    error_lines.append('       f"SELECT week, order_count, "')
    error_lines.append('       f"  ROUND((order_count - LAG(order_count,1) OVER (ORDER BY week))"')
    error_lines.append('       f"        / NULLIF(LAG(order_count,1) OVER (ORDER BY week), 0) * 100, 2) AS wow_rate "')
    error_lines.append('       f"FROM w ORDER BY week"')
    error_lines.append('   )')
    error_lines.append('')
    error_lines.append('🚦 三条铁律（违反任一即必炸）：')
    error_lines.append('   ① WITH 子查询负责所有聚合 + 时间字段表达式（一次写好 month/week 别名）')
    error_lines.append('   ② OVER 的 ORDER BY/PARTITION BY 只能用 WITH 输出别名，禁止重写 DATE_FORMAT(原始列,...)')
    error_lines.append('   ③ 窗口函数参数（LAG(x,...)）的 x 必须来自 WITH，不能是同层 SELECT 的别名')
    error_lines.append('')
    error_lines.append('📖 完整规则见：sql_syntax_rules.md 铁律 7 + known_issues.md H32')
    error_lines.append('🚪 极少数纯 ROW_NUMBER() OVER () 不引用聚合的场景可加豁免（推荐三引号多行字符串）：')
    error_lines.append('   sql = """-- @lint-allow: native-window（说明：纯 ROW_NUMBER 给原始行打号）')
    error_lines.append('   SELECT order_id, ROW_NUMBER() OVER (ORDER BY ts) AS rn FROM t"""')
    error_lines.append('   🛑 禁止把豁免注释与 SQL 主体写在同一行（`--` 会吞掉整条 SQL）。')

    raise ValueError('\n'.join(error_lines))


def _validate_sqlslots_helper_compliance(sql_slots_list, column_types=None):
    """校验 sqlSlots 中所有 SQL 是否合规使用 spark_safe_* helper（P0 #10.5）。

    🛑 这是 write_kanban_outputs 的第 0 道校验，先于 KPI 一致性校验执行。
       理由：KPI 校验中 AS 计数依赖 SQL 结构纯净；如果 SQL 里有非法 CAST(... AS DATE)，
       会让 AS 计数虚高，把 Agent 引向错误的"列数不一致"诊断（已知 Bug，对应本次报错根因）。

    校验失败时抛出 ValueError，错误信息直接含 helper 修复模板（Agent 可复制粘贴）。

    🆕 列类型上下文豁免（消除 timestamp_tz 列误报）：
       column_types: { '<col_name>': 'date'|'timestamp'|'string'|... }
       当传入此映射时，对涉及 DATEDIFF / YEAR / MONTH / TO_DATE / TO_TIMESTAMP /
       DATE_FORMAT 等反模式的命中，若所有引用列都在映射中且类型 ∈ {'date','timestamp'}，
       则直接放行（这些列物理上已是日期/时间戳，spark_safe_* 包装是多余的）。
       未传或类型未知时，行为与之前完全一致（保守报错）。

    🚪 豁免机制：若 SQL 中含 `-- @lint-allow: native-datetime` 注释，跳过本 SQL 的校验。
       适用场景：B0 已确认字段类型为 date/timestamp，按铁律 3 允许直接使用裸 DATEDIFF/DATE_FORMAT；
                或 Unix 时间戳字段按铁律 3 用 CAST(FROM_UNIXTIME(col) AS TIMESTAMP)（虽然
                正则已对函数调用形态豁免，留此入口便于扩展未来其他场景）。
       使用方式（推荐用三引号多行字符串，物理换行最稳）：
         sql = \"\"\"-- @lint-allow: native-datetime（end_date/start_date 已确认为 date 类型）
         SELECT DATEDIFF(end_date, start_date) AS d FROM t\"\"\"

       🛑 P0 硬校验：豁免注释行**必须以换行符结束**，不得与 SQL 主体在同一行。
          否则 `--` 单行注释会吞掉整条 SQL，平台 SQL 溯源面板将显示为"非 SQL 内容"。
          本函数会在豁免命中时强制校验换行，未换行直接抛 ValueError。
    """
    violations = []  # [(slot_key, pattern_name, fix_key, snippet)]

    # 特殊 hack 模式：必须在剥离字符串前匹配（因为 'null' 本身就是字符串字面值）
    _null_hack_re = re.compile(r"!=\s*['\"]null['\"]", re.IGNORECASE)
    # 豁免标记（自描述，需写明字段类型说明）
    _exempt_marker_re = re.compile(r'--\s*@lint-allow:\s*native-datetime', re.IGNORECASE)
    # 🛑 豁免注释与 SQL 主体同行检测：`--` 之后到换行前若出现 SQL 关键字 = 整条 SQL 被注释吞掉
    _exempt_inline_sql_re = re.compile(
        r'--[^\n]*?@lint-allow:[^\n]*?\b(WITH|SELECT|INSERT|UPDATE|DELETE|MERGE|VALUES|FROM)\b',
        re.IGNORECASE,
    )

    for slot_def in sql_slots_list:
        key = slot_def.get('key', '')
        raw_sql = slot_def.get('sql', '') or ''
        if not raw_sql.strip():
            continue

        # 🛰️ OLAP 分流（sqlType == 3，MySQL/PG/GaussDB/StarRocks/Doris）：
        #    Spark helper lint 面向 lakehouse DSL 产物，OLAP 必须走原生方言（TO_CHAR/
        #    STR_TO_DATE/DATE_FORMAT 等），本 lint 会误报为「必须包 spark_safe_*」。
        #    OLAP 侧的方言合规交由 runner L2 OLAP 硬拦截负责（禁 spark_safe_* /
        #    percentile_approx / 三段式表名）；此处直接跳过，避免双头误杀。
        if int(slot_def.get('sqlType') or 0) == 3:
            print(f'  ⏭️ slot "{key}" sqlType=3（OLAP），跳过 Spark helper 合规校验')
            continue

        # 🚪 豁免标记检测（必须在字符串剥离前检测，因为标记在注释里）
        if _exempt_marker_re.search(raw_sql):
            # 🛑 P0 换行硬校验：豁免注释必须以换行结束，否则整条 SQL 会被 `--` 吞掉
            if _exempt_inline_sql_re.search(raw_sql):
                raise ValueError(
                    '\n'
                    f'🚨 sqlSlots 豁免注释格式错误（P0 强制：与 SQL 主体在同一行）\n'
                    f'   slot "{key}" 的 `-- @lint-allow:` 豁免注释未以换行符结束，\n'
                    f'   SQL 主体被 `--` 单行注释吞掉，平台 SQL 溯源面板将显示为非 SQL 内容。\n'
                    '\n'
                    '❌ 错误写法（豁免注释 + SQL 主体被字符串拼接到同一行）：\n'
                    '   sql = "-- @lint-allow: native-datetime（说明）" + "WITH m AS ( ... ) SELECT ..."\n'
                    '   sql = "-- @lint-allow: native-datetime（说明）\\n"  # ⚠️ \\n 仅在双引号字符串中生效，\n'
                    '          "WITH m AS ..."                              #    若被外层再次拼接易丢失\n'
                    '\n'
                    '✅ 正确写法（推荐用三引号多行字符串，物理换行最稳）：\n'
                    '   sql = """-- @lint-allow: native-datetime（说明）\n'
                    '   WITH m AS (\n'
                    '     SELECT ...\n'
                    '   )\n'
                    '   SELECT ... FROM m ORDER BY ..."""\n'
                    '\n'
                    '📖 完整规则见：sql_syntax_rules.md 顶部「sqlSlots SQL 生成铁律」豁免章节'
                )
            print(f'  ⏭️ slot "{key}" 含 @lint-allow:native-datetime 豁免标记，跳过 P0 #10.5 校验')
            continue

        # 先检测 WHERE col != 'null' 这类含字符串字面值的 hack（剥离前）
        m_null = _null_hack_re.search(raw_sql)
        if m_null:
            start = max(0, m_null.start() - 20)
            end = min(len(raw_sql), m_null.end() + 20)
            violations.append((key, "WHERE col != 'null'", 'null_hack',
                               raw_sql[start:end].strip(),
                               bool(slot_def.get('_is_raw_sql'))))

        # 剥离字符串/注释后再做其他反模式匹配
        clean_sql = _strip_sql_comments_and_strings(raw_sql)

        for pattern, name, fix_key in _SQLSLOTS_BANNED_PATTERNS:
            if fix_key == 'null_hack':
                continue  # 已在剥离前处理
            # current_timestamp 反模式仅对 raw_sql 路径触发：
            # DSL 编译产物里 runner 永远不会注入 CURRENT_TIMESTAMP/NOW()/CURRENT_DATE，
            # 而 raw_sql 里这些关键字与 timestamp_tz/VARCHAR 列比较时本地 DuckDB 体检
            # 会因「VARCHAR vs TIMESTAMPTZ」类型失败，必须强制改为字面量上限或先 spark_safe 包列。
            if fix_key == 'current_timestamp' and not slot_def.get('_is_raw_sql'):
                continue
            m = pattern.search(clean_sql)
            if m:
                # ─────────────────────────────────────────────────────────
                # 🆕 列类型豁免（消除 timestamp_tz / date 列上的误报）
                # 仅对"列类型已知 date/timestamp"做物理放行；string/未知类型仍报。
                # ─────────────────────────────────────────────────────────
                if column_types and fix_key in ('datediff', 'extract_part',
                                                 'date_format', 'to_date',
                                                 'to_timestamp'):
                    # 🛡️ 物理日期列豁免：DSL 编译产物与 raw_sql 都适用。
                    #    SKILL.md 明确要求：lakehouse raw_sql 若字段在 source.columns 中确认为
                    #    date/timestamp/datetime，可直接用原生 DATE_FORMAT/YEAR/DATEDIFF；
                    #    只有 string/未知时间列才必须 spark_safe_* 手包。
                    matched = m.group(0)
                    # 提取出现的列名（仅大小写字母/下划线/数字、含点）
                    candidates = re.findall(r'[A-Za-z_][A-Za-z0-9_.]*', matched)
                    # 优先按 source.columns 精确识别真实列名，避免列名恰好叫 date/timestamp
                    # 时被 SQL 关键字过滤掉，导致 DATE_FORMAT(date, ...) 误报。
                    known_refs = [c for c in candidates if c.split('.')[-1] in column_types]
                    if known_refs:
                        col_refs = known_refs
                    else:
                        # 过滤掉函数名（DATEDIFF/YEAR/...）和 SQL 关键字；仅未知列走保守路径。
                        _SQL_FN_WORDS = {
                            'DATEDIFF', 'YEAR', 'MONTH', 'DAY', 'QUARTER', 'WEEK',
                            'WEEKOFYEAR', 'HOUR', 'MINUTE', 'SECOND',
                            'DAYOFWEEK', 'DAYOFMONTH', 'DAYOFYEAR',
                            'EXTRACT', 'FROM', 'TO_DATE', 'TO_TIMESTAMP',
                            'DATE_FORMAT', 'CAST', 'AS', 'DATE', 'TIMESTAMP',
                            'TRY_TO_TIMESTAMP', 'TRY_TO_DATE',
                            'SPARK_SAFE_TO_TIMESTAMP', 'SPARK_SAFE_TO_DATE',
                            'DOW', 'DOY', 'EPOCH',
                        }
                        col_refs = [c for c in candidates
                                    if c.upper() not in _SQL_FN_WORDS
                                    and not c.replace('.', '').isdigit()]
                    if col_refs:
                        # 所有引用列都在 column_types 且类型是 date/timestamp → 豁免
                        _SAFE_TYPES = {'date', 'timestamp'}
                        if all(column_types.get(c.split('.')[-1]) in _SAFE_TYPES
                               for c in col_refs):
                            continue  # ✅ 类型物理安全，跳过本反模式
                start = max(0, m.start() - 20)
                end = min(len(clean_sql), m.end() + 20)
                snippet = clean_sql[start:end].strip()
                # 🆕 把 _is_raw_sql 标记带进 violations，供报错文案区分展示策略：
                #   raw_sql 命中 → 只展示 spark_safe_* 手包模板，不展示
                #   `-- @lint-allow: native-datetime` 豁免方案
                #   （raw_sql 故意不享受类型豁免，鼓励豁免会让 LLM 在
                #   "用注释 vs 手包" 之间反复纠结、多写一轮 spec）。
                violations.append((key, name, fix_key, snippet,
                                   bool(slot_def.get('_is_raw_sql'))))

    if not violations:
        if sql_slots_list:
            print(f'✅ sqlSlots SQL helper 合规校验通过：{len(sql_slots_list)} 个 slot 均未发现裸 SQL 反模式')
        return

    # 聚合相同 fix_key 的违规，避免输出冗余
    by_fix = {}
    for slot_key, name, fix_key, snippet, is_raw in violations:
        by_fix.setdefault(fix_key, []).append((slot_key, name, snippet, is_raw))
    # 全部违规是否都来自 raw_sql？是 → 报错文案隐藏 `@lint-allow: native-datetime`
    # 豁免方案（raw_sql 故意不享受类型豁免，避免 LLM 在两条修法间纠结返工）。
    _all_from_raw_sql = all(it[3] for items in by_fix.values() for it in items)

    error_lines = ['']
    error_lines.append('🚨 sqlSlots SQL 反模式检测失败（P0 #10.5 违反）：')
    error_lines.append('   sqlSlots SQL 是平台周期性自动刷新的 SQL，单行解析失败 = 看板永久报错。')
    error_lines.append('   string 类型时间字段处理**只能**通过 spark_safe_* helper，禁止裸 SQL。')
    if _all_from_raw_sql:
        error_lines.append('   ⚠️ 本次违规均来自 raw_sql 字面量 SQL —— raw_sql 故意不享受列类型豁免，')
        error_lines.append('       所有时间提取/差值一律用 spark_safe_to_timestamp(col) 手包，')
        error_lines.append('       不要使用 `-- @lint-allow: native-datetime` 豁免注释绕过。')
    error_lines.append('')

    for fix_key, items in by_fix.items():
        error_lines.append(f'❌ 检测到 {len(items)} 处违规：')
        for slot_key, name, snippet, _is_raw in items[:5]:  # 每类最多展示 5 处
            error_lines.append(f'   - slot "{slot_key}" 使用了 {name}')
            error_lines.append(f'     位置：...{snippet}...')
        if len(items) > 5:
            error_lines.append(f'   - （还有 {len(items) - 5} 处未列出）')
        error_lines.append('')
        error_lines.append('💡 修复模板（直接复制到 generate_kanban.py）：')
        for line in _HELPER_FIX_TEMPLATES[fix_key].split('\n'):
            error_lines.append(f'     {line}')
        error_lines.append('')

    error_lines.append('📖 完整规则见：sql_syntax_rules.md 顶部「sqlSlots SQL 生成铁律」')
    error_lines.append('📖 helper API 见：SKILL.md Step D 构建器 API 表')
    if not _all_from_raw_sql:
        # 仅当存在非 raw_sql 违规时才展示豁免注释方案（DSL 编译产物的列类型豁免兜底）
        error_lines.append('⚠️ 例外豁免：如果字段 B0 schema 类型确认为 date/timestamp（非 string），按铁律 3 允许直接用裸 SQL。')
        error_lines.append('   豁免方式（推荐三引号多行字符串，物理换行最稳）：')
        error_lines.append('     sql = """-- @lint-allow: native-datetime（end_date/start_date B0 已确认为 date 类型）')
        error_lines.append('     SELECT DATEDIFF(end_date, start_date) AS d FROM t"""')
        error_lines.append('   🛑 禁止把豁免注释与 SQL 主体写在同一行（`--` 会吞掉整条 SQL，平台溯源面板显示为非 SQL 内容）。')
        error_lines.append('   ⚠️ 滥用豁免标记 = 看板上线后平台报错的责任由 Agent 承担，请务必先核对 B0 schema。')

    raise ValueError('\n'.join(error_lines))


# ===== sqlglot AST 校验 + spark_safe_* 误写自愈（P0 #10.8） =====
#
# 防御目标：Agent 把 spark_safe_*(col) Python 函数调用文本误写入 SQL 字符串
#   → 平台 Spark 执行时 ROUTINE_NOT_FOUND / UNRESOLVED_ROUTINE
# 方案：用 sqlglot 解析 SQL AST，检测未知函数调用，自动用正则替换为正确表达式。
# 设计要点：
#   - sqlglot 可选依赖：import 失败则跳过（降级为仅正则校验，不阻塞流程）
#   - 自愈是就地修改 sql_slots_list（写盘前最后一道防线）
#   - 仅处理已知的 spark_safe_* 函数名，不做通用 transpile（避免误改合法 SQL）

# spark_safe_* 函数名 → 对应的 SQL 表达式生成器（参数为捕获的列名列表）
#
# ⚠️ 幂等性约束（P0 #10.8.1 修复）：
#   自愈循环 `while match_found` 会从内层向外层逐层展开 spark_safe_*。
#   若 LLM 写了嵌套形式（如 spark_safe_date_format(spark_safe_to_timestamp(time), 'yyyy-MM')），
#   第一轮展开内层 to_timestamp → try_to_timestamp(regexp_replace(time, ...))；
#   第二轮再展开外层 date_format 时，args[0] 已是一个 timestamp 表达式（不再是裸列）！
#   如果展开器无脑地把 args[0] 再包一层 regexp_replace(<timestamp>, ...) → Spark 非法
#   （regexp_replace 期望 string，传入 timestamp 整列返回 NULL），月份/日期字段全为 NULL。
#
# 修复策略：所有"消费时间字段"的展开器（date_format/datediff/week_format/to_date/extended）
#   在参数已是表达式时（_is_expr_arg 检测到括号或函数调用）直接当成 timestamp 使用，
#   不再外包 regexp_replace；仅当参数是裸列名（如 `time` / time / "time"）时才外包。
#   `spark_safe_to_timestamp` 自身保持原行为（裸列 → try_to_timestamp+regexp_replace）。

def _is_expr_arg(arg: str) -> bool:
    """判断 spark_safe_* 的参数是否已是 SQL 表达式（含括号 / 函数调用），
    而不是简单的列引用。表达式参数已经返回正确类型，不应再被 regexp_replace 包裹。"""
    if not arg:
        return False
    s = arg.strip()
    # 含左括号即视为函数调用 / 子表达式（裸列名 `col` 或 col 不会含括号）
    return '(' in s


def _strip_quotes(arg: str) -> str:
    """剥离 LLM 在 SQL 字符串里误用 helper 时多写的最外层引号（P0 健壮性 #2026-06）。

    背景：
      LLM 经常把 spark_safe_datediff 当成 SQL 函数写在表达式里：
          AVG(spark_safe_datediff('order_delivered_customer_date', 'order_purchase_timestamp'))
      _split_sql_args 严格保留引号，参数会变成 "'order_delivered_customer_date'" 这种字符串字面量。
      若 _ts_of 不剥离外层引号，最终展开为 CAST('order_delivered_customer_date' AS STRING)，
      整列被替换成常量字符串，DATEDIFF 永远 NULL → KPI 显示 0、line 图全空。

    策略：
      - 仅当参数是"严格的字符串字面量"（即两端都是同种引号、且内部不再含引号 / 括号 / 空格）
        且 strip 后看起来像 SQL 标识符（合法列名 / a.b.c）时，才剥离；
        其它情况（真正的字符串字面量如 'yyyy-MM'）保持原样。
      - 容忍单/双引号混用，但内部不允许出现引号、括号、逗号、空格（避免误剥离 'mock' 这种字面量）。
    """
    if not arg:
        return arg
    s = arg.strip()
    if len(s) < 2:
        return s
    if (s[0] == s[-1]) and s[0] in ("'", '"'):
        inner = s[1:-1]
        # 仅当 inner 形如合法标识符 / 限定列名（含点号、下划线、字母数字）时才剥离
        if inner and re.match(r'^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$', inner):
            return inner
    return s


def _normalize_fmt_arg(arg: str) -> str:
    """规范化 DATE_FORMAT 第二参数：

    - 兼容 Python 命名参数：output_format='yyyy-MM' / fmt="yyyy-MM" / format=...
    - 不带引号：yyyy-MM → 'yyyy-MM'
    - 已带引号：原样返回
    """
    if not arg:
        return "'yyyy-MM'"
    s = arg.strip()
    # 剥离 Python 风格命名参数（output_format=... / fmt=... / format=...）
    if '=' in s:
        # 仅当等号左侧是合法 Python 标识符且 SQL 中本身不存在该比较语义时剥离
        left, right = s.split('=', 1)
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', left.strip()):
            s = right.strip()
    if not s:
        return "'yyyy-MM'"
    # 已带引号 → 直接用
    if (s[0] == s[-1]) and s[0] in ("'", '"'):
        # 统一成单引号
        return "'" + s[1:-1].replace("'", "''") + "'"
    return "'" + s.replace("'", "''") + "'"


def _ts_of(arg: str) -> str:
    """把 spark_safe_* 的参数转换为可直接消费的 timestamp 表达式：
       - 已是表达式 → 原样返回（避免 regexp_replace(<timestamp>) 这种非法嵌套）
       - 是裸列 → 包裹成 try_to_timestamp(regexp_replace(CAST(<col> AS STRING), '[./]', '-'))

    为何裸列分支必须显式 CAST AS STRING：
      - 远端 Spark 对 string 是隐式 cast，但本地 DuckDB（_spark_to_duckdb_compat 文本展开后）严格类型，
        当 <col> 是 date / timestamp / int / decimal 等非字符串类型时，
        regexp_replace(<DATE>, ...) 会抛 BinderException: No function matches 'regexp_replace(DATE,...)'
        → 直接导致 line/compare/table 等含日期 GROUP BY 的图表本地数据为空。
      - CAST(any AS STRING) 在 Spark 全版本合法、对 string 列幂等、对 date/timestamp 等非 string 列
        统一兜底，远端 Spark 与本地 DuckDB 行为完全对齐。

    P0 健壮性增强（2026-06）：
      自动剥离 LLM 误用 helper 时给参数加的字符串引号，
      避免 CAST('col_name' AS STRING) 这种把列名当成字面量的致命错误。
    """
    arg = _strip_quotes(arg)
    return arg if _is_expr_arg(arg) else f"try_to_timestamp(regexp_replace(CAST({arg} AS STRING), '[./]', '-'))"


_SPARK_SAFE_REPLACEMENTS = {
    'spark_safe_to_timestamp': lambda args: (
        # 已是表达式（如内层已展开）→ 原样返回，不重复包裹
        # 裸列分支显式 CAST AS STRING：与 _ts_of 保持一致，兜住 date/timestamp/数值列
        # P0 健壮性：剥离 LLM 误传的字符串字面量引号
        (lambda a0: (
            a0 if _is_expr_arg(a0)
            else f"try_to_timestamp(regexp_replace(CAST({a0} AS STRING), '[./]', '-'))"
        ))(_strip_quotes(args[0]))
    ),
    'spark_safe_to_date': lambda args: f"CAST({_ts_of(args[0])} AS DATE)",
    'spark_safe_datediff': lambda args: (
        f"DATEDIFF({_ts_of(args[0])}, {_ts_of(args[1])})"
    ),
    'spark_safe_date_format': lambda args: (
        # P0 健壮性：args[1] 走 _normalize_fmt_arg，
        # 兼容 output_format='yyyy-MM' / fmt='yyyy-MM' 等 Python 命名参数误用，
        # 同时为不带引号的格式串自动补单引号，避免 DATE_FORMAT(ts, yyyy-MM) 抛错。
        "DATE_FORMAT({col}, {fmt})".format(
            col=_ts_of(args[0]),
            fmt=_normalize_fmt_arg(args[1]) if len(args) > 1 else "'yyyy-MM'")
    ),
    'spark_safe_week_format': lambda args: (
        f"CONCAT(CAST(YEAR({_ts_of(args[0])}) AS STRING), "
        f"'-W', LPAD(CAST(WEEKOFYEAR({_ts_of(args[0])}) AS STRING), 2, '0'))"
    ),
    'spark_safe_to_timestamp_extended': lambda args: (
        # 已是表达式（已是 timestamp）直接返回，无需扩展兜底
        # 裸列分支：所有进入 regexp_replace / RLIKE 的列引用统一 CAST AS STRING，
        # 避免 DATE / TIMESTAMP / 整数日期等非 string 列触发本地 DuckDB Binder 错。
        # P0 健壮性（2026-06）：
        #   1) 剥离 LLM 误传的字符串字面量引号（'col' → col）
        #   2) 在解析前先 trim 时区后缀（如 ' +0800' / ' +08:00' / 'Z' / ' UTC'），
        #      解决 olist 这类带时区文本本地 DuckDB try_to_timestamp 解析失败导致全空的问题。
        (lambda a0: (
            a0 if _is_expr_arg(a0) else (
                # _ts_str：标准化后的时间字符串 = TRIM 去尾 + 去毫秒小数 + 去时区后缀（仅在 STRING 列上做）
                # 注：先 CAST AS STRING 兜底，再用 regexp_replace 一次性处理多种时区写法
                f"COALESCE("
                # 优先级 1：标准 'YYYY-MM-DD HH:MM:SS' / 含毫秒 / 含时区
                f"try_to_timestamp("
                f"  regexp_replace("
                f"    regexp_replace("
                f"      regexp_replace(CAST({a0} AS STRING), '\\\\s*([+-][0-9]{{2}}:?[0-9]{{2}}|Z|UTC|GMT)\\\\s*$', ''),"
                f"      '\\\\.[0-9]+$', ''),"
                f"    '[./]', '-')),"
                # 优先级 2：紧凑日期 'YYYYMMDD'
                f"try_to_timestamp(regexp_replace(CAST({a0} AS STRING), '^([0-9]{{4}})([0-9]{{2}})([0-9]{{2}})$', '$1-$2-$3')),"
                # 优先级 3：unix 秒 / 毫秒
                f"CASE WHEN CAST({a0} AS STRING) RLIKE '^[0-9]{{10}}$' THEN CAST(from_unixtime(CAST({a0} AS BIGINT)) AS TIMESTAMP)"
                f" WHEN CAST({a0} AS STRING) RLIKE '^[0-9]{{13}}$' THEN CAST(from_unixtime(CAST({a0} AS BIGINT)/1000) AS TIMESTAMP)"
                f" ELSE NULL END)"
            )
        ))(_strip_quotes(args[0]))
    ),
}

# 匹配 spark_safe_xxx(...) 调用的正则（支持嵌套括号一层）
_SPARK_SAFE_CALL_RE = re.compile(
    r'\b(spark_safe_(?:to_timestamp|to_date|datediff|date_format|week_format|to_timestamp_extended))'
    r'\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)',
    re.IGNORECASE,
)


def _validate_and_repair_sql_with_sqlglot(sql_slots_list):
    """用 sqlglot 校验 sqlSlots SQL 语法 + 自动修复 spark_safe_* 误写（P0 #10.8）。

    行为：
      1. 尝试 import sqlglot（可选依赖，失败则降级为纯正则检测）
      2. 对每条 SQL 做正则扫描：检测 spark_safe_* 函数名是否出现在 SQL 文本中
      3. 如果检测到，用正则替换为正确的 SQL 表达式（自愈）
      4. 自愈后再用 sqlglot 做语法校验（可选，失败不阻塞）
      5. 就地修改 sql_slots_list

    返回:
        dict: {'repaired': int, 'parse_errors': list, 'sqlglot_available': bool}
    """
    result = {'repaired': 0, 'parse_errors': [], 'sqlglot_available': False}

    # 尝试加载 sqlglot（可选依赖）
    sqlglot_mod = None
    try:
        import sqlglot as sqlglot_mod
        result['sqlglot_available'] = True
    except ImportError:
        pass

    if not sql_slots_list:
        return result

    repaired_count = 0
    for slot_def in sql_slots_list:
        key = slot_def.get('key', '')
        raw_sql = slot_def.get('sql', '') or ''
        if not raw_sql.strip():
            continue

        # 🛰️ OLAP 分流（sqlType == 3）：目标数据源用其原生方言（MySQL/PG/GaussDB/StarRocks/Doris），
        #    既不需要 spark_safe_* 自愈，也不能用 Spark dialect 做 sqlglot 语法校验（会误报 STR_TO_DATE
        #    /DATE_FORMAT/TO_CHAR 等合法函数）；直接跳过，交由 runner OLAP L2 硬拦截兜底。
        if int(slot_def.get('sqlType') or 0) == 3:
            continue

        # 正则检测 + 替换 spark_safe_* 调用
        new_sql = raw_sql
        match_found = True
        max_iterations = 20  # 防无限循环
        iteration = 0
        while match_found and iteration < max_iterations:
            iteration += 1
            match_found = False
            def _replace_call(m):
                nonlocal match_found
                func_name = m.group(1).lower()
                args_str = m.group(2).strip()
                # 解析参数（简单逗号分割，尊重括号嵌套）
                args = _split_sql_args(args_str)
                replacer = _SPARK_SAFE_REPLACEMENTS.get(func_name)
                if replacer and args:
                    match_found = True
                    return replacer(args)
                return m.group(0)  # 未知函数名，保持原样
            new_sql = _SPARK_SAFE_CALL_RE.sub(_replace_call, new_sql)

        if new_sql != raw_sql:
            slot_def['sql'] = new_sql
            repaired_count += 1
            print(f'  🔧 slot "{key}" 检测到 spark_safe_* 误写，已自动修复为 Spark SQL 表达式')

        # sqlglot 语法校验（可选，仅报告不阻塞）
        if sqlglot_mod and new_sql.strip():
            try:
                sqlglot_mod.parse_one(new_sql, read='spark')
            except Exception as e:
                err_msg = str(e)[:200]
                result['parse_errors'].append({'key': key, 'error': err_msg})
                print(f'  ⚠️ slot "{key}" sqlglot 语法校验警告: {err_msg[:100]}')

    result['repaired'] = repaired_count
    if repaired_count > 0:
        print(f'✅ sqlglot 自愈完成：修复了 {repaired_count} 个 slot 中的 spark_safe_* 误写')
    elif result['sqlglot_available']:
        print(f'✅ sqlglot 语法校验通过：{len(sql_slots_list)} 个 slot 均无 spark_safe_* 误写')
    else:
        # 纯正则模式（sqlglot 不可用）
        has_misuse = any(_SPARK_SAFE_CALL_RE.search(s.get('sql', '') or '') for s in sql_slots_list)
        if not has_misuse:
            print(f'✅ 正则校验通过：{len(sql_slots_list)} 个 slot 均无 spark_safe_* 误写（sqlglot 未安装，降级为正则）')

    # ---- P0 拦截：未知 spark_safe_<x>() 调用一律 FATAL ----
    # 自愈循环只展开 _SPARK_SAFE_REPLACEMENTS 白名单内的函数；展开后 SQL 中若仍残留
    # `spark_safe_<其它>(...)` 前缀，必是 LLM 幻觉（如 spark_safe_now / spark_safe_current_date /
    # spark_safe_year / spark_safe_unix_timestamp 等运行时既无 Spark UDF 也无 DuckDB macro 的名字）。
    # 远端 Spark 必报 UNRESOLVED_FUNCTION，本地 DuckDB 必报 Catalog Error → 卡片显示空。
    # 这里直接 raise，让 LLM 看到 FATAL 后按提示改回 CURRENT_TIMESTAMP / YEAR(...) 等 Spark 原生语法。
    _unknown_re = re.compile(r'\bspark_safe_([A-Za-z_][\w]*)\s*\(', re.IGNORECASE)
    _known = {
        'to_timestamp', 'to_date', 'datediff', 'date_format',
        'week_format', 'to_timestamp_extended',
    }
    _unknown_hits = []  # [(key, func_name)]
    for slot_def in sql_slots_list:
        # OLAP slot 不参与 spark_safe_* 前缀检测（runner OLAP L2 已在其它维度硬拦截）
        if int(slot_def.get('sqlType') or 0) == 3:
            continue
        key = slot_def.get('key', '')
        sql_txt = slot_def.get('sql', '') or ''
        for m in _unknown_re.finditer(sql_txt):
            fn = m.group(1).lower()
            if fn not in _known:
                _unknown_hits.append((key, f'spark_safe_{fn}'))
    if _unknown_hits:
        seen = set()
        lines = []
        for k, fn in _unknown_hits:
            sig = (k, fn)
            if sig in seen:
                continue
            seen.add(sig)
            lines.append(f'   - slot "{k}" 调用了未知函数 {fn}()')
        joined = '\n'.join(lines)
        raise ValueError(
            f'❌ [FATAL][P0] sqlSlots 中检测到未知 spark_safe_<x>() 调用（运行时必报 '
            f'UNRESOLVED_FUNCTION / Catalog Error，卡片必空）：\n{joined}\n'
            f'修法：白名单仅 {sorted(_known)}；其它一律按 Spark 原生写法：\n'
            f'  - 当前时间 → 用 CURRENT_TIMESTAMP（关键字常量，无括号；远端 Spark 与本地 DuckDB 同义）\n'
            f'  - 当前日期 → 用 CURRENT_DATE\n'
            f'  - 年/月/日 → 用 YEAR(col) / MONTH(col) / DAY(col)\n'
            f'  - Unix 时间戳 → 用 UNIX_TIMESTAMP(col) / FROM_UNIXTIME(col)\n'
            f'禁止把 spark_safe_ 当作"万能前缀"包裹任意 Spark 函数。'
        )

    return result


# ===== 基于 sqlglot AST 的全面 SQL 校验（P0 通用校验） =====
#
# 设计目标：利用 sqlglot 的 AST 解析能力，对 LLM 生成的 sqlSlots 做全面校验，
# 确保 SQL 在 Spark 上都能执行；**一次扫描汇总全部问题**，让 LLM 一次改完。
#
# 校验范围（对应 sql_syntax_rules.md 中的 P0 铁律）：
#   1. MySQL 特有函数黑名单（铁律 9）
#   2. 嵌套聚合检测（铁律 8）
#   3. 相关标量子查询无聚合检测（铁律 5）
#   4. 中文别名/裸标识符无反引号检测（铁律 6/10）—— 覆盖 Column / Table / Alias
#   5. Presto 三参数 DATEDIFF 检测（铁律 3）
#   6. MySQL 风格日期格式 %Y-%m-%d 检测（铁律 2.2）
#   7. 除零未用 NULLIF 检测（最佳实践）
#   8. sqlglot 解析期语法错误检测（PARSE_SYNTAX_ERROR 提前拦截）
#   9. 列名白名单校验（铁律 11）—— 防 UNRESOLVED_COLUMN：列名必须 ∈ 真实表 schema
#  10. JOIN 列歧义检测（铁律 12）—— 防 AMBIGUOUS_REFERENCE
#  11. WHERE/ORDER BY/QUALIFY 子句裸聚合检测（铁律新增）
#      —— Spark 必抛 [UNSUPPORTED_EXPR_FOR_OPERATOR]，DuckDB 会自动重写而隐藏问题，
#         必须在落盘前用 AST 静态拦截，避免引擎语义差异导致线上失败。


# CJK 字符正则（中日韩统一表意文字 + 扩展 A）
_CJK_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')


def _is_unquoted_cjk_identifier(node):
    """检测一个 sqlglot Identifier 节点是否为未加反引号的 CJK 标识符。

    Spark SQL Parser 解析裸中文标识符直接抛 PARSE_SYNTAX_ERROR（位置即首个 CJK 字符）。
    必须确保所有 CJK 列名/表名/别名都用反引号包裹。
    """
    try:
        import sqlglot.expressions as expr
    except ImportError:
        return False
    if not isinstance(node, expr.Identifier):
        return False
    name = node.name or ''
    if not _CJK_RE.search(name):
        return False
    # sqlglot Identifier 的 quoted 属性表示是否被反引号/双引号包裹
    return not bool(node.args.get('quoted'))


def _suggest_similar_columns(unknown_col, available_cols, top_n=3):
    """对未知列名做编辑距离 Top-N 建议（Did you mean ...?）。"""
    if not available_cols:
        return []
    try:
        import difflib
        return difflib.get_close_matches(unknown_col, list(available_cols), n=top_n, cutoff=0.4)
    except Exception:
        return []


def _build_column_whitelist(table_schemas, slot_data, sql_slots_list):
    """构建列名白名单（用于 UNRESOLVED_COLUMN 校验）。

    优先级：
    1. 显式传入的 table_schemas（最可靠，从 Step B schema JSON 输出）

      2. SLOT_DATA headers（每个 slot 第一行就是 SELECT 输出列）+ 已有 SQL 的 SELECT alias
      3. 都没有则返回空集合（跳过此项校验，不阻塞）

    返回:
        dict: {
            'all_columns': set,        # 全集（用于"是否存在"快速判断）
            'by_table': dict,          # 'catalog.db.table' -> set(cols)
            'has_explicit': bool,      # 是否有 table_schemas 显式输入（决定提示语强度）
        }
    """
    by_table = {}
    all_columns = set()

    # 1) 显式 table_schemas 最高优先级
    if table_schemas and isinstance(table_schemas, dict):
        for tbl, cols in table_schemas.items():
            if not cols:
                continue
            cols_set = {str(c) for c in cols}
            # 同时记录 full name 与短名
            by_table[tbl] = cols_set
            short = tbl.split('.')[-1] if '.' in tbl else tbl
            by_table.setdefault(short, set()).update(cols_set)
            all_columns.update(cols_set)
        return {'all_columns': all_columns, 'by_table': by_table, 'has_explicit': True}

    # 2) 弱推断：从 SLOT_DATA headers 收集
    if slot_data and isinstance(slot_data, dict):
        for v in slot_data.values():
            if isinstance(v, list) and v and isinstance(v[0], list):
                for h in v[0]:
                    all_columns.add(str(h))

    # 3) 从已有 sqlSlots 的 metrics/dimensions 字段名收集（Agent 自报）
    for slot in (sql_slots_list or []):
        for m in (slot.get('metrics') or []):
            f = m.get('field') or m.get('name')
            if f:
                all_columns.add(str(f))
        for d in (slot.get('dimensions') or []):
            f = d.get('field') or d.get('name')
            if f:
                all_columns.add(str(f))

    return {'all_columns': all_columns, 'by_table': by_table, 'has_explicit': False}


def _validate_sql_with_sqlglot_comprehensive(sql_slots_list, slot_data=None, table_schemas=None):
    """基于 sqlglot AST 的全面 SQL 校验（P0 通用校验）。

    利用 sqlglot 的 AST 解析能力，对 LLM 生成的 sqlSlots 做全面校验，
    确保 SQL 在 Spark 上都能执行；**一次扫描汇总全部问题**，让 LLM 一次改完。

    校验范围（对应 sql_syntax_rules.md 中的 P0 铁律）：
      1. MySQL 特有函数黑名单（铁律 9）：FIELD、IFNULL、NOW、CURDATE 等
      2. 嵌套聚合检测（铁律 8）：PERCENTILE(COUNT(*), ...) 等
      3. 相关标量子查询无聚合检测（铁律 5）：MUST_AGGREGATE_CORRELATED_SCALAR_SUBQUERY
      4. CJK 标识符无反引号检测（铁律 6/10）：Column / Table / Alias 全覆盖
      5. Presto 三参数 DATEDIFF 检测（铁律 3）：DATE_DIFF('day', start, end)
      6. MySQL 风格日期格式检测（铁律 2.2）：%Y-%m-%d 而非 yyyy-MM-dd
      7. 除零未用 NULLIF 检测（最佳实践）
      8. sqlglot 解析期语法错误检测
      9. 列名白名单校验（铁律 11）：UNRESOLVED_COLUMN 提前拦截
      10. JOIN 列歧义检测（铁律 12）：AMBIGUOUS_REFERENCE 提前拦截
      11. WHERE/ORDER BY/QUALIFY 子句裸聚合检测：UNSUPPORTED_EXPR_FOR_OPERATOR 提前拦截

    参数:
        sql_slots_list: SQL 插槽定义列表
        slot_data: 切片数据字典（可选，用于弱白名单推断）
    table_schemas: dict, 可选 — { 'catalog.db.table': ['col1', ...] }
    传入则启用强列名白名单校验（推荐：Step B schema JSON 直接复用）


    异常:
        ValueError: 检测到违规时抛出，附带修复建议（按 slot 聚合，一次报齐）
    """
    try:
        import sqlglot
        import sqlglot.expressions as expr
    except ImportError:
        print('  ⚠️ sqlglot 未安装，跳过全面 AST 校验（仅做正则校验）')
        _validate_sql_with_regex_fallback(sql_slots_list)
        return

    violations = []  # [(slot_key, rule_name, description, suggestion)]

    # MySQL 特有函数黑名单（铁律 9）
    MYSQL_FORBIDDEN_FUNCTIONS = {
        'FIELD': 'Spark 不支持 FIELD() 函数，请用 CASE WHEN 实现自定义排序',
        'FIND_IN_SET': 'Spark 不支持 FIND_IN_SET()，请用 ARRAY_CONTAINS(SPLIT(...), ...)',
        'GROUP_CONCAT': 'Spark 不支持 GROUP_CONCAT()，请用 CONCAT_WS(",", COLLECT_LIST(...))',
        'IFNULL': 'Spark 不支持 IFNULL()，请用 COALESCE(col, default)',
        'IF': 'Spark 不支持 IF()，请用 CASE WHEN cond THEN v1 ELSE v2 END',
        'DATE_SUB': 'Spark 的 DATE_SUB 不支持 INTERVAL 语法，请用 DATE_SUB(date, n)',
        'DATE_ADD': 'Spark 的 DATE_ADD 不支持 INTERVAL 语法，请用 DATE_ADD(date, n)',
        'STR_TO_DATE': 'Spark 不支持 STR_TO_DATE()，请用 TO_DATE(str, format) 或 spark_safe_to_timestamp()',
        'NOW': 'Spark 不支持 NOW()，请用 CURRENT_TIMESTAMP()',
        'CURDATE': 'Spark 不支持 CURDATE()，请用 CURRENT_DATE()',
        'DATE_DIFF': 'Presto 风格 DATE_DIFF()，Spark 请用 DATEDIFF(end, start)（两参数）',
    }

    # 列名白名单（用于 UNRESOLVED_COLUMN 校验）
    whitelist = _build_column_whitelist(table_schemas, slot_data, sql_slots_list)
    enable_column_check = bool(whitelist['has_explicit'])  # 仅显式传入时强校验，避免误报

    for slot_def in sql_slots_list:
        key = slot_def.get('key', '')
        raw_sql = slot_def.get('sql', '') or ''
        if not raw_sql.strip():
            continue

        # 🛰️ OLAP 分流（sqlType == 3）：本函数所有规则均为 Spark-only（MySQL 函数黑名单、
        #    CJK 反引号、Presto DATEDIFF、%Y-%m-%d 日期格式、Spark dialect parse 等），
        #    对 OLAP raw_sql 会大规模误报（如 STR_TO_DATE/DATE_FORMAT/TO_CHAR 都是合法函数）。
        #    OLAP 语义合规交由 runner OLAP L2 硬拦截 + 目标数据源引擎兜底。
        if int(slot_def.get('sqlType') or 0) == 3:
            continue

        # ─── 1. sqlglot 解析（捕获 PARSE 阶段错误） ───
        ast = None
        try:
            ast = sqlglot.parse_one(raw_sql, read='spark')
        except Exception as e:
            err_msg = str(e)[:200]
            # 友好提示：常见 PARSE 失败往往是 CJK 裸标识符
            hint = '请检查 SQL 语法，确保符合 Spark SQL 规范'
            if _CJK_RE.search(raw_sql):
                hint = ('SQL 中含中文标识符，**所有中文列名/表名/别名必须用反引号包裹**：'
                        '`SELECT 零售价` ❌ → ``SELECT `零售价` `` ✅')
            violations.append((key, 'PARSE_ERROR',
                               f'Spark SQL 解析失败: {err_msg}',
                               hint))
            # 注意：不再 continue，下面会回退到正则规则继续扫，做到"一次报齐"

        # ─── 2~7：基于 AST 的规则（仅 ast 可用时） ───
        if ast is not None:
            # 2. MySQL 特有函数黑名单（铁律 9）
            for node in ast.walk():
                if isinstance(node, expr.Func):
                    func_name = node.name.upper() if node.name else ''
                    if func_name in MYSQL_FORBIDDEN_FUNCTIONS:
                        violations.append((key, 'MYSQL_FUNCTION',
                                           f'使用了 MySQL 特有函数 {func_name}()',
                                           MYSQL_FORBIDDEN_FUNCTIONS[func_name]))

            # 3. 嵌套聚合（铁律 8）
            def _check_nested_agg(node, depth=0):
                if isinstance(node, expr.AggFunc):
                    for child in node.args.values():
                        child_nodes = []
                        if isinstance(child, (list, tuple)):
                            child_nodes = [c for c in child if isinstance(c, expr.Expression)]
                        elif isinstance(child, expr.Expression):
                            child_nodes = [child]
                        for child_node in child_nodes:
                            if isinstance(child_node, expr.AggFunc):
                                violations.append((key, 'NESTED_AGGREGATE',
                                                   f'检测到嵌套聚合: {type(node).__name__}({type(child_node).__name__}(...))',
                                                   '请用 WITH 双层结构：先聚合得到中间结果，外层再做二次聚合'))
                            else:
                                _check_nested_agg(child_node, depth + 1)
                else:
                    for child in node.args.values():
                        if isinstance(child, expr.Expression):
                            _check_nested_agg(child, depth + 1)
                        elif isinstance(child, (list, tuple)):
                            for item in child:
                                if isinstance(item, expr.Expression):
                                    _check_nested_agg(item, depth + 1)

            _check_nested_agg(ast)

            # 4. CJK 标识符无反引号（铁律 6/10）—— 覆盖 Column / Table / Alias
            cjk_reported = set()  # 同一 slot 内同名标识符只报一次
            for node in ast.walk():
                if isinstance(node, expr.Identifier) and _is_unquoted_cjk_identifier(node):
                    name = node.name
                    if name in cjk_reported:
                        continue
                    cjk_reported.add(name)
                    # 判断角色（Column / Table / Alias），给出更精准的修复建议
                    parent = node.parent
                    if isinstance(parent, expr.Alias):
                        role = '列别名'
                        fix = f'裸用 {name} ➜ 改为 `{name}`（反引号包裹）'
                    elif isinstance(parent, expr.Table):
                        role = '表名'
                        fix = f'裸用 {name} ➜ 改为 `{name}` 或换英文表名'
                    else:
                        role = '列引用'
                        fix = (f'裸用 {name} ➜ 改为 `{name}`（反引号包裹）；'
                               f'若 {name} 不是表中真实列名，应改为真实英文列名')
                    violations.append((key, 'CJK_IDENTIFIER_UNQUOTED',
                                       f'{role} "{name}" 含中文但未用反引号包裹（Spark Parser 必失败）',
                                       fix))

            # 5. Presto 三参数 DATEDIFF（铁律 3）
            sql_upper = raw_sql.upper()
            if re.search(r'DATE_DIFF\s*\(\s*[\'"]', sql_upper):
                violations.append((key, 'PRESTO_DATEDIFF',
                                   '检测到 Presto 风格三参数 DATE_DIFF(unit, start, end)',
                                   'Spark 请用 DATEDIFF(end, start)（两参数，返回天数差）'))

            # 6. MySQL 风格日期格式（铁律 2.2）
            for node in ast.walk():
                if isinstance(node, expr.Func) and node.name.upper() == 'DATE_FORMAT':
                    for arg_group in node.args.values():
                        items = arg_group if isinstance(arg_group, (list, tuple)) else [arg_group]
                        for arg in items:
                            if isinstance(arg, expr.Literal):
                                fmt_str = arg.sql(dialect='spark')
                                if '%' in fmt_str:
                                    violations.append((key, 'MYSQL_DATE_FORMAT',
                                                       f'DATE_FORMAT 使用了 MySQL 风格格式字符串: {fmt_str}',
                                                       '请用 Java DateTimeFormatter 格式: yyyy-MM-dd（非 %Y-%m-%d）'))

            # 11. WHERE / ORDER BY / QUALIFY 子句裸聚合检测
            #
            # 背景：Spark 严格遵守 SQL 标准，**外层 SELECT 的 WHERE / ORDER BY / QUALIFY**
            #       中不允许直接出现聚合函数（COUNT/SUM/AVG/...）；HAVING 例外。
            #       而 DuckDB 会自动重写「ORDER BY COUNT(*)」 → 引用聚合输出列，导致本地
            #       DuckDB 体检通过、Spark 端失败（[UNSUPPORTED_EXPR_FOR_OPERATOR]）。
            #
            # 排除场景（合法用法，必须放行）：
            #   - HAVING 子句内的聚合（标准用法）
            #   - 聚合函数位于 Window 内（OVER(...) 内的 PARTITION/ORDER BY）
            #   - 聚合函数自身参数中的 ORDER BY（如 PERCENTILE(...) WITHIN GROUP 等）
            #
            # 实现：自顶向下找每个 Select 节点，独立判断其 args['where'] / args['order'] /
            #       args['qualify'] 子树中是否含 AggFunc，且该 AggFunc 的祖先链不在
            #       Window 内（避免误报 LEAD(...) OVER (ORDER BY COUNT(*)) 这种内层窗口）。
            #
            # 注意：本规则只校验「裸聚合」，对「引用某个已物化为别名的聚合列」（如
            #       `ORDER BY cnt DESC`，cnt = COUNT(*) AS cnt）放行，因为 AST 看到的是
            #       Column 而非 AggFunc，自然不会命中。这正是修复方案推荐的写法。
            def _has_window_ancestor(node, stop_at):
                """node 的祖先链中是否存在 Window（不越过 stop_at）。"""
                cur = node.parent
                while cur is not None and cur is not stop_at:
                    if isinstance(cur, expr.Window):
                        return True
                    cur = cur.parent
                return False

            CLAUSE_LABELS = {
                'where': 'WHERE',
                'order': 'ORDER BY',
                'qualify': 'QUALIFY',
            }
            agg_clause_reported = set()  # (slot_key, clause_key, agg_name) 去重
            for sel in ast.find_all(expr.Select):
                for clause_key, clause_label in CLAUSE_LABELS.items():
                    clause = sel.args.get(clause_key)
                    if clause is None:
                        continue
                    for sub in clause.walk():
                        if not isinstance(sub, expr.AggFunc):
                            continue
                        # 跳过位于 Window 内的聚合（合法的窗口排序键）
                        if _has_window_ancestor(sub, stop_at=clause):
                            continue
                        agg_name = (sub.name or type(sub).__name__).upper()
                        sig = (clause_key, agg_name)
                        if sig in agg_clause_reported:
                            continue
                        agg_clause_reported.add(sig)
                        if clause_key == 'order':
                            fix = (f'请把 {agg_name}(...) 在子查询中物化为别名（如 `cnt`），'
                                   f'外层改为 `ORDER BY `cnt` DESC`；'
                                   f'或下沉到子查询内部的 ORDER BY。')
                        elif clause_key == 'where':
                            fix = (f'WHERE 不能含聚合，请改用 HAVING（GROUP BY 后），'
                                   f'或把聚合先物化为子查询列再在外层 WHERE 引用别名。')
                        else:  # qualify
                            fix = (f'请把 {agg_name}(...) 物化为子查询列后再在外层 QUALIFY 引用别名。')
                        violations.append((key, 'AGG_IN_CLAUSE',
                                           f'{clause_label} 子句中直接使用了聚合函数 {agg_name}(...)，'
                                           f'Spark 必抛 [UNSUPPORTED_EXPR_FOR_OPERATOR]',
                                           fix))
                        break  # 同一 clause 同一聚合名只报一次，继续看下一 clause

            # 9. 列名白名单校验（铁律 11）—— UNRESOLVED_COLUMN 拦截
            # 收集本 SQL 中定义的别名（CTE / 子查询输出列），避免被误判为未知列
            local_aliases = set()
            if enable_column_check:
                for node in ast.walk():
                    if isinstance(node, expr.Alias):
                        try:
                            local_aliases.add(node.alias)
                        except Exception:
                            pass
                # 收集本 SQL 引用的所有列名
                col_reported = set()
                for node in ast.walk():
                    if isinstance(node, expr.Column):
                        col_name = node.name or ''
                        if not col_name or col_name == '*':
                            continue
                        if col_name in col_reported:
                            continue
                        # 跳过 CJK 列（已被规则 4 覆盖，避免重复噪音）
                        if _CJK_RE.search(col_name):
                            continue
                        # 跳过本 SQL 内定义的 alias
                        if col_name in local_aliases:
                            continue
                        # 在白名单中查找（不区分大小写匹配，Spark 默认大小写不敏感）
                        all_cols_lower = {c.lower() for c in whitelist['all_columns']}
                        if col_name.lower() not in all_cols_lower:
                            col_reported.add(col_name)
                            suggestions = _suggest_similar_columns(col_name, whitelist['all_columns'])
                            sugg_text = (f'相似列名: {suggestions}' if suggestions
                       else '请核对 Step B schema JSON 输出，使用真实存在的列名')

                            violations.append((key, 'UNRESOLVED_COLUMN',
                                               f'列 "{col_name}" 不在表 schema 中（Spark 必抛 UNRESOLVED_COLUMN）',
                                               sugg_text))

            # 10. JOIN 场景中未限定表别名的列引用（铁律 12：AMBIGUOUS_REFERENCE）
            joins = list(ast.find_all(expr.Join))
            if joins:
                # 收集所有 FROM/JOIN 表的别名 → 表真实名映射
                alias_to_table = {}
                for table_node in ast.find_all(expr.Table):
                    tbl_alias = table_node.alias or ''
                    tbl_name = table_node.name or ''
                    if tbl_alias:
                        alias_to_table[tbl_alias] = tbl_name

                # 检测自联（同一张表出现多次，别名不同）
                table_name_counts = {}
                for tbl_name in alias_to_table.values():
                    table_name_counts[tbl_name] = table_name_counts.get(tbl_name, 0) + 1
                is_self_join = any(cnt > 1 for cnt in table_name_counts.values())

                # 如果有 table_schemas，收集多表共有列（交集）
                ambiguous_cols = set()
                if table_schemas and len(alias_to_table) >= 2:
                    # 收集各表的列集合
                    table_col_sets = []
                    for tbl_alias, tbl_name in alias_to_table.items():
                        # 尝试在 table_schemas 中匹配（支持三段式和短名）
                        matched_cols = None
                        for schema_key, schema_cols in table_schemas.items():
                            if schema_key == tbl_name or schema_key.endswith('.' + tbl_name):
                                matched_cols = {c.lower() for c in schema_cols}
                                break
                        if matched_cols:
                            table_col_sets.append(matched_cols)
                    # 计算多表共有列（出现在 2+ 个表中的列）
                    if len(table_col_sets) >= 2:
                        from collections import Counter
                        col_counter = Counter()
                        for col_set in table_col_sets:
                            for c in col_set:
                                col_counter[c] += 1
                        ambiguous_cols = {c for c, cnt in col_counter.items() if cnt >= 2}

                # 遍历所有列引用，检查是否未限定表别名
                ambig_reported = set()
                for col_node in ast.find_all(expr.Column):
                    if col_node.table:  # 已限定表别名，安全
                        continue
                    col_name = col_node.name or ''
                    if not col_name or col_name == '*':
                        continue
                    if col_name in ambig_reported:
                        continue
                    # 跳过聚合函数内的 * （COUNT(*)）
                    if col_name in local_aliases:
                        continue

                    should_report = False
                    if is_self_join:
                        # 自联场景：所有未限定的列都歧义（同表所有列完全相同）
                        should_report = True
                    elif ambiguous_cols and col_name.lower() in ambiguous_cols:
                        # 非自联但有 table_schemas：仅报多表共有列
                        should_report = True

                    if should_report:
                        ambig_reported.add(col_name)
                        aliases_list = list(alias_to_table.keys())[:4]
                        aliases_hint = '/'.join(f'{a}.{col_name}' for a in aliases_list)
                        violations.append((key, 'AMBIGUOUS_REFERENCE',
                                           f'JOIN 中列 "{col_name}" 未限定表别名（Spark 必抛 AMBIGUOUS_REFERENCE）',
                                           f'请改为 {aliases_hint}（根据业务语义选择正确的表别名）'))

        # ─── 8. PARSE 失败时的正则降级规则（保证一次报齐） ───
        if ast is None:
            # CJK 裸标识符正则识别：FROM/SELECT/WHERE/ORDER BY 后未加反引号的中文 token
            cjk_tokens = set()
            for m in re.finditer(r'(?<!`)([\u4e00-\u9fff\u3400-\u4dbf][\u4e00-\u9fff\u3400-\u4dbf\w]*)(?!`)', raw_sql):
                cjk_tokens.add(m.group(1))
            for tok in list(cjk_tokens)[:5]:  # 限量，避免噪音
                violations.append((key, 'CJK_IDENTIFIER_UNQUOTED',
                                   f'裸中文标识符 "{tok}" 未用反引号包裹',
                                   f'裸用 {tok} ➜ 改为 `{tok}`（反引号包裹）；若引用列名，应改为真实英文列名'))
            # MySQL 函数 / Presto DATEDIFF / MySQL date format（与 _validate_sql_with_regex_fallback 同口径）
            if re.search(r'\b(FIELD|IFNULL|NOW|CURDATE|GROUP_CONCAT|FIND_IN_SET|STR_TO_DATE)\s*\(',
                         raw_sql, re.IGNORECASE):
                violations.append((key, 'MYSQL_FUNCTION',
                                   '使用了 MySQL 特有函数（PARSE 失败时正则兜底）',
                                   '请改用 Spark 等价函数（COALESCE / CASE WHEN 等）'))
            if re.search(r'DATE_DIFF\s*\(\s*[\'"]', raw_sql, re.IGNORECASE):
                violations.append((key, 'PRESTO_DATEDIFF',
                                   '检测到 Presto 风格三参数 DATE_DIFF',
                                   'Spark 请用 DATEDIFF(end, start)（两参数）'))
            if re.search(r'DATE_FORMAT\s*\([^,]+,\s*[\'"]%', raw_sql, re.IGNORECASE):
                violations.append((key, 'MYSQL_DATE_FORMAT',
                                   'MySQL 风格日期格式字符串（%Y/%m/%d）',
                                   '请用 Java DateTimeFormatter 格式: yyyy-MM-dd'))

    # ─── 汇总违规并抛出错误（按 slot 分组，一次报齐） ───
    if not violations:
        msg_extra = '（含列名白名单校验）' if enable_column_check else '（未传 table_schemas，列名白名单校验已跳过）'
        print(f'✅ sqlglot 全面校验通过：{len(sql_slots_list)} 个 slot 均未发现 Spark 兼容性问题{msg_extra}')
        return

    # 去重（同一 slot + 规则 + 描述 只报一次）
    seen = set()
    unique_violations = []
    for v in violations:
        sig = (v[0], v[1], v[2])
        if sig not in seen:
            seen.add(sig)
            unique_violations.append(v)

    # 按 slot 分组，方便 LLM 一次定位一次改完
    by_slot = {}
    for slot_key, rule_name, description, suggestion in unique_violations:
        by_slot.setdefault(slot_key, []).append((rule_name, description, suggestion))

    error_lines = ['']
    error_lines.append('🚨 sqlglot 全面校验失败（P0 强制，本次不会落盘）：')
    error_lines.append(f'   共 {len(by_slot)} 个 slot 累计 {len(unique_violations)} 处问题，请**一次性全部修复**后再调用。')
    if not enable_column_check:
        error_lines.append('   💡 建议给 write_kanban_outputs() 传入 table_schemas={...}（B0 输出可直接复用），')
        error_lines.append('      启用列名白名单校验，提前拦截 UNRESOLVED_COLUMN。')
    error_lines.append('')

    for slot_key in by_slot:
        error_lines.append(f'─── slot: "{slot_key}" ───')
        for idx, (rule_name, description, suggestion) in enumerate(by_slot[slot_key], 1):
            error_lines.append(f'   [{idx}] [{rule_name}] {description}')
            error_lines.append(f'       💡 {suggestion}')
        error_lines.append('')

    error_lines.append('📖 完整规则见：sql_syntax_rules.md')
    error_lines.append('🛑 修复完上述全部问题后再调用 write_kanban_outputs()，本次未写盘')

    raise ValueError('\n'.join(error_lines))


def _validate_sql_with_regex_fallback(sql_slots_list):
    """sqlglot 不可用时的正则降级校验。

    检测最关键的 Spark 兼容性问题：
      1. MySQL 特有函数
      2. Presto 三参数 DATEDIFF
      3. MySQL 风格日期格式
    """
    violations = []

    MYSQL_FUNCTIONS_RE = re.compile(
        r'\b(FIELD|IFNULL|NOW|CURDATE|GROUP_CONCAT|FIND_IN_SET|STR_TO_DATE)\s*\(',
        re.IGNORECASE
    )
    PRESTO_DATEDIFF_RE = re.compile(r'DATE_DIFF\s*\(\s*[\'"]', re.IGNORECASE)
    MYSQL_DATE_FMT_RE = re.compile(r'DATE_FORMAT\s*\([^,]+,\s*[\'"]%', re.IGNORECASE)

    for slot_def in sql_slots_list:
        key = slot_def.get('key', '')
        raw_sql = slot_def.get('sql', '') or ''
        if not raw_sql.strip():
            continue

        if MYSQL_FUNCTIONS_RE.search(raw_sql):
            violations.append((key, 'MYSQL_FUNCTION',
                               '使用了 MySQL 特有函数'))
        if PRESTO_DATEDIFF_RE.search(raw_sql):
            violations.append((key, 'PRESTO_DATEDIFF',
                               'Presto 风格三参数 DATE_DIFF'))
        if MYSQL_DATE_FMT_RE.search(raw_sql):
            violations.append((key, 'MYSQL_DATE_FORMAT',
                               'MySQL 风格日期格式字符串'))

    if violations:
        print(f'  ⚠️ 正则降级校验检测到 {len(violations)} 处潜在 Spark 兼容性问题')
        for slot_key, rule_name, desc in violations:
            print(f'     - slot "{slot_key}" [{rule_name}]: {desc}')


# ===== sqlSlots 缺失自动补全（P0 #10.1 自愈） =====
def _extract_table_name_from_slots(sql_slots_list):
    """从已有 sql_slots_list 中提取表名（取第一个有效的 FROM 子句）。"""
    for slot_def in sql_slots_list:
        sql = slot_def.get('sql', '') or ''
        # 匹配 FROM table_name（支持三段式 catalog.db.table）
        match = re.search(r'\bFROM\s+([a-zA-Z0-9_.]+)', sql, re.IGNORECASE)
        if match:
            table = match.group(1)
            # 排除子查询别名（通常是单个短词如 t, monthly, sub 等）
            if '.' in table or len(table) > 10:
                return table
    return 'UNKNOWN_TABLE'


def _build_slot_definition(slot_key, data_type, table_name, slot_data_entry):
    """根据 slot_data 推断字段结构，生成骨架 SQL slot 定义。

    参数:
        slot_key: slot 的 key
        data_type: HTML 中的 data-type（kpi/echarts/table）
        table_name: 从已有 SQL 中提取的表名
        slot_data_entry: SLOT_DATA 中对应的数据（list of lists，第一行为 headers）

    返回:
        dict: slot 定义，或 None（无法推断时）
    """
    if not slot_data_entry or not isinstance(slot_data_entry, list) or len(slot_data_entry) < 2:
        # 无数据或数据不足，生成最小骨架
        return {
            'key': slot_key,
            'sql': f'SELECT 1 AS placeholder FROM {table_name} LIMIT 1',
            'metrics': [],
            'dimensions': [],
            'refreshInterval': 600,
        }

    headers = slot_data_entry[0]
    if not isinstance(headers, list) or not headers:
        return {
            'key': slot_key,
            'sql': f'SELECT 1 AS placeholder FROM {table_name} LIMIT 1',
            'metrics': [],
            'dimensions': [],
            'refreshInterval': 600,
        }

    # 从第二行数据推断字段类型
    first_data_row = slot_data_entry[1] if len(slot_data_entry) > 1 else []
    metrics = []
    dimensions = []
    select_parts = []

    # 判断是否为明细型图表（不需要聚合）
    # 通过 slot_key 中的关键词推断：scatter/parallel/boxplot/candlestick/table 等需要明细数据
    _DETAIL_CHART_KEYWORDS = ('scatter', 'parallel', 'boxplot', 'candlestick', 'kline', 'detail', 'table')
    is_detail_chart = data_type == 'table' or any(kw in slot_key.lower() for kw in _DETAIL_CHART_KEYWORDS)

    # 判断是否为静态数据型图表（通常手动构建 UNION ALL，不从表中聚合）
    _STATIC_CHART_KEYWORDS = ('funnel', 'gauge', 'sankey', 'graph', 'sunburst')
    is_static_data = any(kw in slot_key.lower() for kw in _STATIC_CHART_KEYWORDS)

    for i, header in enumerate(headers):
        header_str = str(header)
        # 判断是否为数值字段
        is_numeric = False
        if i < len(first_data_row):
            val = first_data_row[i]
            is_numeric = isinstance(val, (int, float)) and not isinstance(val, bool)

        if is_numeric:
            metrics.append({
                'name': header_str,
                'field': header_str,
                'formula': header_str if is_detail_chart else f'SUM({header_str})',
                'description': header_str,
            })
            if is_detail_chart or is_static_data:
                select_parts.append(header_str)
            else:
                select_parts.append(f'ROUND(SUM({header_str}), 2) AS {header_str}')
        else:
            dimensions.append({
                'name': header_str,
                'field': header_str,
                'description': header_str,
            })
            select_parts.append(header_str)

    # 构建 SQL
    select_clause = ', '.join(select_parts) if select_parts else '*'
    dim_fields = [d['field'] for d in dimensions]

    if data_type == 'kpi':
        # KPI 不需要 GROUP BY
        sql = f'SELECT {select_clause}\nFROM {table_name}'
        refresh = 60
    elif data_type == 'table' or is_detail_chart:
        # 表格/散点图/平行坐标等直接 SELECT 明细
        sql = f'SELECT {select_clause}\nFROM {table_name}\nORDER BY 1 DESC\nLIMIT 50'
        refresh = 300
    elif is_static_data:
        # 静态数据（funnel/gauge/sankey/graph/sunburst）：直接用 UNION ALL 重建
        # 但如果数据行数合理且有维度，仍用 GROUP BY
        if dim_fields:
            group_clause = ', '.join(dim_fields)
            sql = f'SELECT {select_clause}\nFROM {table_name}\nGROUP BY {group_clause}\nORDER BY {dim_fields[0]}'
        else:
            sql = f'SELECT {select_clause}\nFROM {table_name}'
        refresh = 600
    elif dim_fields:
        # 有维度字段，需要 GROUP BY
        group_clause = ', '.join(dim_fields)
        sql = f'SELECT {select_clause}\nFROM {table_name}\nGROUP BY {group_clause}\nORDER BY {dim_fields[0]}'
        refresh = 300
    else:
        # 纯数值，无维度
        sql = f'SELECT {select_clause}\nFROM {table_name}'
        refresh = 300

    return {
        'key': slot_key,
        'sql': sql,
        'metrics': metrics,
        'dimensions': dimensions,
        'refreshInterval': refresh,
    }


def _split_sql_args(args_str):
    """简单的 SQL 函数参数分割（尊重括号嵌套，不进入字符串内部）。"""
    args = []
    depth = 0
    current = []
    in_single_quote = False
    in_double_quote = False

    for ch in args_str:
        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(ch)
        elif ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(ch)
        elif in_single_quote or in_double_quote:
            current.append(ch)
        elif ch == '(':
            depth += 1
            current.append(ch)
        elif ch == ')':
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            args.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)

    if current:
        args.append(''.join(current).strip())

    return [a for a in args if a]  # 过滤空参数


# ===== Mock SQL 检测模式 =====

# Mock SQL 检测模式（匹配占位符 SQL）
_MOCK_SQL_PATTERNS = [
    re.compile(r"^\s*SELECT\s+'mock'", re.IGNORECASE),
    re.compile(r"^\s*SELECT\s+0\s+as\s+\w+\s*,\s*0\s+as\s+\w+\s*$", re.IGNORECASE),
    re.compile(r"^\s*SELECT\s+\d+(\.\d+)?\s+as\s+\w+\s*,\s*\d+(\.\d+)?\s+as\s+\w+\s*$", re.IGNORECASE),
]


def _validate_data_sanity(sql_slots_list, slot_data):
    """
    P0 语义校验门（H29/H30/H31 拦截器，2026-06 新增）。

    在结构层校验全部通过后，仍可能存在"产物有数据但视觉上看似空白"的语义偏差，
    本函数集中拦截 3 类隐蔽问题：

      1) KPI 口径与饼/状态分布合计不一致（如 KPI total=131 但 status_pie 合计=124）
         —— 用户感知为"KPI 与图表对不上"。
      2) 数据严重偏态导致视觉退化（heatmap/treemap/sankey 单格 >90%）
         —— 用户感知为"图表只见一格亮"。
      3) sqlSlots 已声明但 SLOT_DATA 仅含表头（空数据集）
         —— 用户感知为"组件无数据 / loading 转圈"。

    设计原则：
      - 仅 warning，不 fatal：避免在结构正确时阻断生产；
      - 但所有警告**必须**显式打印，迫使 Agent 看到并主动决定是否回到 SQL 层修正。
      - 命中规则只输出 1 行修复建议，绝不写大段散文（防止 Agent 注意力稀释）。
    """
    warnings = []

    # ── 规则 1：KPI 总数 vs 状态/分类分布合计的口径校验 ─────────────────
    # 触发条件：存在 key 含 "kpi" 的 slot，且存在 key 同时含 ("status" 或 "category" 或 "type")
    # 与 ("pie" 或 "dist") 的分布 slot；KPI 第一列若是"总数/订单数/客户数"等命名 → 与分布合计比对
    try:
        kpi_keys = [k for k in slot_data if 'kpi' in k.lower()]
        dist_keys = [k for k in slot_data
                     if any(t in k.lower() for t in ('status', 'category', 'type', 'class'))
                     and any(t in k.lower() for t in ('pie', 'dist', 'distribution', 'breakdown'))]
        for kk in kpi_keys:
            kdata = slot_data.get(kk) or []
            if len(kdata) < 2:
                continue
            headers, values = kdata[0], kdata[1]
            # KPI 横向格式：第一列若像"总数"则取其值
            for ci, h in enumerate(headers):
                if not isinstance(h, str):
                    continue
                if any(t in h for t in ('总订单', '总数', '订单数', '总客户', '总记录', 'total')):
                    try:
                        kpi_total = float(values[ci])
                    except (TypeError, ValueError, IndexError):
                        continue
                    if kpi_total <= 0:
                        continue
                    for dk in dist_keys:
                        ddata = slot_data.get(dk) or []
                        if len(ddata) < 2:
                            continue
                        # 取最后一个数值列做合计
                        try:
                            dist_total = sum(
                                float(r[-1]) for r in ddata[1:]
                                if isinstance(r, (list, tuple)) and r
                                and isinstance(r[-1], (int, float))
                            )
                        except (TypeError, ValueError):
                            continue
                        if dist_total <= 0:
                            continue
                        diff_ratio = abs(kpi_total - dist_total) / kpi_total
                        if diff_ratio > 0.05:
                            warnings.append(
                                f'WARN: KPI 口径不一致 — {kk}.{h}={kpi_total:.0f}, '
                                f'{dk} 合计={dist_total:.0f}, 差异 {diff_ratio*100:.1f}%。'
                                f'修复：两条 SQL 统一过滤条件（如 WHERE <字段> IS NOT NULL）'
                            )
                    break  # 一个 KPI slot 只比一次
    except Exception as _e:
        # 任何检测异常都不该阻断写入
        warnings.append(f'WARN: KPI 口径校验跳过（{type(_e).__name__}: {_e}）')

    # ── 规则 2：偏态检测（top1 占比 > 90% 视觉退化） ─────────────────
    # 适用图表：heatmap / treemap / sankey / funnel —— 这类图视觉上严重依赖比例
    SKEW_SENSITIVE = ('heatmap', 'treemap', 'sankey', 'funnel')
    try:
        for key, data in slot_data.items():
            if not any(t in key.lower() for t in SKEW_SENSITIVE):
                continue
            if not isinstance(data, list) or len(data) < 4:
                continue  # 数据点 <3 不构成偏态问题
            # 找出最后一个数值列（兼容 sankey 的 [source,target,value] 格式）
            numeric_col = None
            for ci in range(len(data[0]) - 1, -1, -1):
                col_vals = [r[ci] for r in data[1:] if isinstance(r, (list, tuple)) and len(r) > ci]
                if col_vals and all(isinstance(v, (int, float)) for v in col_vals):
                    numeric_col = ci
                    break
            if numeric_col is None:
                continue
            vals = [float(r[numeric_col]) for r in data[1:]
                    if isinstance(r, (list, tuple)) and len(r) > numeric_col
                    and isinstance(r[numeric_col], (int, float))]
            total = sum(v for v in vals if v > 0)
            if total <= 0 or len(vals) < 4:
                continue
            top1 = max(vals) / total
            if top1 > 0.90:
                warnings.append(
                    f'WARN: {key} 数据严重偏态 — top1 占比 {top1*100:.1f}%，'
                    f'视觉上其他类目将不可见。修复：① 改用 Top-N + 其他聚合 '
                    f'② SQL 加 WHERE <类目字段> NOT IN (\'已支付\',\'已发货\') 剔除离群项 '
                    f'③ 改用 visualMap 对数色阶（heatmap/treemap）'
                )
    except Exception as _e:
        warnings.append(f'WARN: 偏态校验跳过（{type(_e).__name__}: {_e}）')

    # ── 规则 3：仅含表头的空数据集 ─────────────────────────────────
    # P0 健壮性升级（2026-06）：
    #   原本所有空 slot 都是 WARN，导致 LLM 误用 helper 时全表头空数据看板照常进入 PREVIEW。
    #   现新增"核心图表多个为空"的硬升级：line/heatmap/funnel/compare/kpi_overview 这些
    #   是看板叙事主轴，若其中 ≥2 个仅含表头，则升级为 ❌ ERROR 显式提示，要求 Agent 必修。
    _CORE_PREFIXES = ('line_', 'heatmap_', 'funnel_', 'compare_', 'kpi_overview',
                      'kpi_', 'bar_', 'pie_')
    try:
        empty_slots = []
        empty_core_slots = []
        for key, data in slot_data.items():
            if not isinstance(data, list):
                continue
            if len(data) <= 1:
                empty_slots.append(key)
                if any(str(key).startswith(p) for p in _CORE_PREFIXES):
                    empty_core_slots.append(key)
                warnings.append(
                    f'WARN: {key} 仅含表头无数据行（SQL 可能返回空集 / 过滤过严）。'
                f'修复：本地重跑 build_kanban 该 spec 确认该 slot 的 SQL 返回非空再产出'
                )
        # 升级为 ERROR：多个核心图表为空，看板呈"空壳"状态
        if len(empty_core_slots) >= 2:
            warnings.append(
                f'❌ ERROR: 共 {len(empty_core_slots)} 个核心图表数据为空 '
                f'({", ".join(empty_core_slots[:5])}{"..." if len(empty_core_slots) > 5 else ""})，'
                f'看板将以"空壳"状态进入 PREVIEW。常见根因：'
                f'① helper 误用（如 spark_safe_datediff(\'col1\',\'col2\') 把列名传成字符串字面量）'
                f'② 时间字段含时区文本本地解析失败（请改用 spark_safe_to_timestamp_extended）'
                f'③ 表数据时间范围与 timeRange 过滤不匹配。'
                f'必修：本地重跑 build_kanban 该 spec 检查空 slot 的 SQL → 修复 spec → 重新保存 PREVIEW'
            )
        elif len(empty_slots) >= max(3, int(len(slot_data) * 0.5)):
            warnings.append(
                f'❌ ERROR: 空 slot 占比过半 ({len(empty_slots)}/{len(slot_data)})，'
                f'看板可读性已严重受损，请先排查公共 SQL 模式（时间字段 / helper 用法 / 过滤条件）'
            )
    except Exception as _e:
        warnings.append(f'WARN: 空数据集校验跳过（{type(_e).__name__}: {_e}）')

    if warnings:
        print('⚠️ 数据语义校验告警（不阻塞写入，但需 Agent 关注）：')
        for w in warnings:
            print(f'  {w}')
    return warnings


def write_kanban_outputs(sql_slots_list, slot_data, workspace_id, resource_id,
                         table_schemas=None, column_types=None,
                         display_name: str = ''):
    """
    三端统一入库产物准备 —— 跑完 builder lint 后返回基础 save_meta，主链路不写空 params。

    参数:
        sql_slots_list: SQL 插槽定义列表
        slot_data: 切片数据字典（供 lint 使用；不再写入本地文件）
        workspace_id: 工作空间 ID
        resource_id: 执行资源 ID
        table_schemas: dict, 可选 — { 'catalog.db.table': ['col1', 'col2', ...] }
                       传入则启用列名白名单校验（彻底拦截 UNRESOLVED_COLUMN）；
                       推荐复用 Step B schema JSON 输出，零成本接入。
        column_types: dict, 可选 — { 'col_name': 'date'|'timestamp'|'string'|... }
                       由 DSL 层从 Spec.source.columns 自动推断（_column_type_map）。
                       传入后，sqlSlots 反模式校验会对"列类型已知 date/timestamp"
                       的 DATEDIFF / YEAR / MONTH 等命中做物理豁免，避免误报。
        display_name: 看板显示名（由 runner 传 spec.title）；空则回退 '未命名看板'。

    返回:
        dict: {
            'output_dir': 产物目录路径,
            'params_path': 保存参数文件路径,
            'save_meta': 基础保存参数（供 emitter 合成最终 params 后一次性落盘）, 
        }

    🛡️ 设计要点：
        - 调用前只读取已有 kanban_save_params.json 的 AccessKey，二次执行时 UpdateAiKanBan 继续覆盖同一 PREVIEW
        - 仅保留当前 API 白名单字段，避免本地历史元信息误传到后端
        - HtmlContent/SqlSlots 由 emitter 在 DSL/Datasets 构造成功后一次性写入，避免无效 params 中间态落盘

    🛡️ 三端统一入库权威链路（本函数只完成第 1 步）：
        1. write_kanban_outputs（本函数）→ lint + 准备基础 save_meta
        2. kanban_dsl_emitter.emit_dsl → 写入最终 kanban_save_params.json（HtmlContent = DSL / SqlSlots = Datasets）
        3. update_to_kanban_list → 读最终 params 调 UpdateAiKanBan 写 PREVIEW
    """
    output_dir = get_kanban_output_dir()
    params_path_pre = os.path.join(output_dir, 'kanban_save_params.json')

    # 只保留预览锚点 AccessKey；其他本地历史元信息不再进入当前 API 协议。
    existing_access_key = ''
    if os.path.isfile(params_path_pre):
        try:
            with open(params_path_pre, 'r', encoding='utf-8') as f:
                _prev = json.load(f)
            existing_access_key = str(_prev.get('AccessKey', '') or '')
        except (IOError, json.JSONDecodeError, ValueError) as _e:
            print(f'⚠️ 读取已有 kanban_save_params.json 失败（将以新预览处理）: {_e}')

    # 0. sqlSlots SQL helper 合规校验（强制：必须最先执行）
    #    理由：裸 CAST/AS 会污染下面 KPI 一致性校验的 AS 计数，必须先拦截
    _validate_sqlslots_helper_compliance(sql_slots_list, column_types=column_types)

    # 0.07 窗口函数双层结构校验（铁律 7 / H32 强制）
    #     理由：单层 SELECT + 同层别名的窗口 SQL 在 Spark 必抛 LATERAL_COLUMN_ALIAS_IN_WINDOW；
    #          本地 Pandas 切片不暴露此问题，必须在写盘前拦截。
    _validate_window_function_scope(sql_slots_list)

    # 0.08 sqlglot AST 校验 + spark_safe_* 误写自愈
    #      理由：spec 编写者可能把 Python helper 函数名误写入 raw_sql 字符串 → 平台 ROUTINE_NOT_FOUND；
    #           本步骤在写盘前自动检测并修复，就地更新 sql_slots_list。
    _validate_and_repair_sql_with_sqlglot(sql_slots_list)

    # 0.085 基于 sqlglot AST 的全面 SQL 校验（平台兼容兜底）
    #       MySQL 函数黑名单 / 嵌套聚合 / CJK 反引号 / 三参数 DATEDIFF /
    #       MySQL 风格日期格式 / sqlglot 解析期错误 / 列名白名单
    _validate_sql_with_sqlglot_comprehensive(sql_slots_list, slot_data=slot_data, table_schemas=table_schemas)

    # 0.3 数据语义校验门（H29/H30/H31 软告警，非阻塞但显式打印）
    _validate_data_sanity(sql_slots_list, slot_data)

    # 入库前剥离内部字段：_is_raw_sql 仅供 lint 区分豁免边界，不属于平台契约
    _public_sql_slots = [
        {k: v for k, v in s.items() if not str(k).startswith('_')}
        for s in sql_slots_list
    ]

    # 1. 构建基础保存参数；最终 HtmlContent/SqlSlots 由 emitter 成功后一次性写入文件。
    save_meta = build_save_meta(
        workspace_id, resource_id, _public_sql_slots,
        display_name=display_name,
    )
    if existing_access_key:
        save_meta['AccessKey'] = existing_access_key
        print(f'🔑 保留已有 AccessKey: {existing_access_key}')

    params_path = os.path.join(output_dir, 'kanban_save_params.json')
    print(f'✅ 保存参数已准备: {params_path}')

    return {
        'output_dir': output_dir,
        'params_path': params_path,
        'save_meta': save_meta,
    }


# ============================================================
# 三端统一入库权威链路：
#   write_kanban_outputs → emit_dsl → update_to_kanban_list(UpdateAiKanBan/PREVIEW)
# 发布态：save_to_kanban_list(SaveAiKanBan)
# ============================================================
# ============================================================
# 发布 / 预览同步到「仪表盘 → AI 看板列表」（封装 wedatacli 调用）
# ============================================================
#
# 设计目标：
#   1. save_to_kanban_list() 是发布入口，只调用 SaveAiKanBan。
#      AccessKey 必须来自 PREVIEW；发布请求只携带 WorkspaceId + AccessKey。
#   2. update_to_kanban_list() 是预览入口，只调用 UpdateAiKanBan。
#      AccessKey 非空时覆盖 PREVIEW；AccessKey 为空时由后端创建 PREVIEW 并返回 AccessKey。
#   3. 入参仅 1 个（可选）：write_kanban_outputs() 的返回值；不传则自动从默认目录推断。
#   4. 内部细节全部封装：
#        - 自动从 kanban_save_params.json 加载已 Base64 编码好的 DSL/Dataset / DisplayName / WorkspaceId / ExecuteResourceId
#        - 预览路径只透传 UpdateAiKanBanReq 白名单字段；SourceType 仅承载新协议标识（默认 'dsl'），
#          不再复用为其他状态编码
#        - 发布路径只走 SaveAiKanBan；预览保存/更新路径只走 UpdateAiKanBan
#        - 接口成功后，AccessKey 持久化写回 kanban_save_params.json
#   5. 输出协议明确：status / action / access_key / view_status / error，便于上层 Agent 判定后续输出。
#
# Agent 使用模式：
#   ① build_kanban() 成功 → runner 自动 update_to_kanban_list() 写 PREVIEW
#   ② 用户明说"发布/上线/确认发布" → 调 save_to_kanban_list() 写发布态
#   ③ 用户明说"保存预览/更新预览/同步预览" → 调 update_to_kanban_list() 写 PREVIEW
# ============================================================

# 包级常量：subprocess 默认超时
_KANBAN_API_TIMEOUT = 60


def _resolve_wedatacli_path():
    """解析 wedatacli 可执行文件路径。

    解析逻辑（与 prefetch_table.py / kanban_runner.py 的三档定位对齐）：
      1. 环境变量 WEDATACLI_PATH（优先级最高，便于测试覆盖）
      2. <CODEBUDDY_PLUGIN_ROOT>/l0-cli/wedatacli.sh（DataBuddy 沙箱）
      3. <_BUILDER_DIR>/../../../l0-cli/wedatacli.sh （从 reference/ 上溯到 plugin/）
      4. shutil.which('wedatacli')：PATH 兜底（WorkBuddy 市场安装场景走这条）
    任意一项命中即返回；均未命中返回空串。
    """
    cli_path = os.environ.get('WEDATACLI_PATH', '')
    if cli_path and os.path.isfile(cli_path):
        return cli_path
    plugin_root = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '')
    if plugin_root:
        candidate = os.path.join(plugin_root, 'l0-cli', 'wedatacli.sh')
        if os.path.isfile(candidate):
            return candidate
    fallback = os.path.normpath(os.path.join(_BUILDER_DIR, '..', '..', '..', 'l0-cli', 'wedatacli.sh'))
    if os.path.isfile(fallback):
        return fallback
    # PATH 兜底：WorkBuddy market zip 场景由 databuddycli init 装到系统 PATH 上
    try:
        import shutil as _shutil
        which_path = _shutil.which('wedatacli')
        if which_path and os.path.isfile(which_path):
            return which_path
    except Exception:
        pass
    return ''


def _builder_workspace_folder_extra_args():
    """从 env WEDATA_WORKSPACE_FOLDER 读取工作空间目录，非空则返回 ['--workspace_folder', <path>]。

    - DataBuddy 沙箱场景：env 未设置 → 返回 [] → CLI argv 不变。
    - WorkBuddy 连接器场景：intelligent-kanban SKILL.md 已在 Step B/D 前置 export，
      追加到 argv 后满足 WorkBuddy 严格模式（runtimeMode=workbuddy）对 --workspace_folder 的强制要求。
    """
    wf = os.environ.get('WEDATA_WORKSPACE_FOLDER', '').strip()
    if wf:
        return ['--workspace_folder', wf]
    return []


def _resolve_record_resource_script():
    """解析 <plugin-v2>/shared-scripts/record_resource.sh 绝对路径，未命中返回空串。
    优先级：env WEDATA_RECORD_SCRIPT > CODEBUDDY_PLUGIN_ROOT > reference 上溯 5 层 > CLI 同级兜底。
    """
    override = os.environ.get('WEDATA_RECORD_SCRIPT', '').strip()
    if override and os.path.isfile(override):
        return override
    plugin_root = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '')
    if plugin_root:
        candidate = os.path.join(plugin_root, 'shared-scripts', 'record_resource.sh')
        if os.path.isfile(candidate):
            return candidate
    # reference→intelligent-kanban→skills→data-analysis→scenarios→plugin-v2 = 5 层
    fallback = os.path.normpath(
        os.path.join(_BUILDER_DIR, '..', '..', '..', '..', '..',
                     'shared-scripts', 'record_resource.sh')
    )
    if os.path.isfile(fallback):
        return fallback
    # CLI 同级兜底：l0-cli 与 shared-scripts 在 plugin-v2 下互为同级目录
    cli_path = _resolve_wedatacli_path()
    if cli_path:
        cli_relative = os.path.normpath(
            os.path.join(os.path.dirname(cli_path), '..',
                         'shared-scripts', 'record_resource.sh')
        )
        if os.path.isfile(cli_relative):
            return cli_relative
    return ''


def _load_save_params(params_path):
    """读取 kanban_save_params.json；不存在或损坏则返回 None。"""
    if not os.path.isfile(params_path):
        return None
    try:
        with open(params_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f'⚠️ 读取 {params_path} 失败: {e}')
        return None


def _get_wedatacli_env(key):
    """通过 wedatacli GetEnv 读取指定字段，失败返回空串。

    仅在需要外部环境信息（consoleDomain / regionId / workspaceId）时使用；
    subprocess 失败/超时均静默降级为空串，由上层决定是否给出链接。
    """
    cli_path = _resolve_wedatacli_path()
    if not cli_path:
        return ''
    try:
        import subprocess
        proc = subprocess.run(
            [cli_path, 'GetEnv', str(key)] + _builder_workspace_folder_extra_args(),
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10,
        )
        if proc.returncode != 0:
            return ''
        return (proc.stdout or '').strip()
    except Exception:
        return ''


def build_ai_kanban_url(access_key, workspace_id='', region_id='', console_domain=''):
    """拼接 DataBuddy 控制台 AI 看板详情页链接。

    与前端 ROUTES.DASHBOARD.AI_BOARD 保持一致：
        https://{console_domain}/dashboard/aiBoard/{access_key}?o={workspace_id}&r={region_id}

    参数解析顺序（每个参数独立）：
        access_key    ：必填；空则返回空串（表示无法生成链接）
        workspace_id  ：入参 > env WEDATA_WORKSPACE_ID > env TENCENTCLOUD_WORKSPACE_ID > wedatacli GetEnv workspaceId
        region_id     ：入参 > env WEDATA_REGION_ID > wedatacli GetEnv regionId
        console_domain：入参 > env WEDATA_CONSOLE_DOMAIN > wedatacli GetEnv consoleDomain > 缺省 databuddy.cloud.tencent.com

    返回：完整 URL 字符串；access_key 为空时返回空串。
    """
    ak = str(access_key or '').strip()
    if not ak:
        return ''

    ws = str(workspace_id or '').strip()
    if not ws:
        ws = (os.environ.get('WEDATA_WORKSPACE_ID', '')
              or os.environ.get('TENCENTCLOUD_WORKSPACE_ID', '')).strip()
    if not ws:
        ws = _get_wedatacli_env('workspaceId')

    rid = str(region_id or '').strip()
    if not rid:
        rid = os.environ.get('WEDATA_REGION_ID', '').strip()
    if not rid:
        rid = _get_wedatacli_env('regionId')

    domain = str(console_domain or '').strip()
    if not domain:
        domain = os.environ.get('WEDATA_CONSOLE_DOMAIN', '').strip()
    if not domain:
        domain = _get_wedatacli_env('consoleDomain')
    if not domain:
        domain = 'databuddy.cloud.tencent.com'

    url = f'https://{domain}/dashboard/aiBoard/{ak}'
    query = []
    if ws:
        query.append(f'o={ws}')
    if rid:
        query.append(f'r={rid}')
    if query:
        url = f'{url}?{"&".join(query)}'
    return url


_PREVIEW_API_PAYLOAD_FIELDS = (
    'WorkspaceId',
    'AccessKey',
    'DisplayName',
    'HtmlContent',
    'SqlSlots',
    'ExecuteResourceId',
    'SourceType',
    'RefreshSchedule',
    'SessionTag',
)


def _build_api_payload(params, api_kind):
    """从 kanban_save_params.json 派生 API stdin JSON。

    api_kind: 'save' | 'preview'
    协议：
      - save 是发布入口：只携带 WorkspaceId + AccessKey，发布内容由后端从 PREVIEW 同步
      - preview 是预览入口：只按 UpdateAiKanBanReq 白名单携带字段；无 AccessKey 时由后端创建 PREVIEW 并返回 AccessKey
      - 不再全量透传本地 params，避免未来本地元信息误传到后端
      - preview 携带 SourceType=dsl 与 SessionTag 写入 PREVIEW，发布时由后端同步到发布态
    """
    if api_kind == 'save':
        return _build_publish_payload(params)

    source = params or {}
    payload = {
        field: source.get(field)
        for field in _PREVIEW_API_PAYLOAD_FIELDS
        if field in source
    }
    payload['WorkspaceId'] = payload.get('WorkspaceId') or os.environ.get('TENCENTCLOUD_WORKSPACE_ID', '')
    payload['AccessKey'] = str(payload.get('AccessKey') or '').strip()
    payload['SourceType'] = payload.get('SourceType') or 'dsl'

    return payload


def _build_publish_payload(params):
    """构造 SaveAiKanBan 发布请求：只携带 WorkspaceId + AccessKey。

    DSL / Dataset / DisplayName / ExecuteResourceId / RefreshSchedule 均由后端从同 AccessKey 的 PREVIEW 同步。
    """
    return {
        'WorkspaceId': (params or {}).get('WorkspaceId') or os.environ.get('TENCENTCLOUD_WORKSPACE_ID', ''),
        'AccessKey': ((params or {}).get('AccessKey') or '').strip(),
    }


def _run_wedatacli_api(api_name, payload_dict):
    """统一封装 wedatacli stdin 调用。

    返回:
        dict {
            'status': 'success' | 'failed',
            'response': {...},          # 解析后的服务端 Response 对象（成功时）
            'error': '...',             # 失败原因（失败时）
            'raw_stdout': '...',
            'raw_stderr': '...',
        }
    """
    import subprocess
    cli_path = _resolve_wedatacli_path()
    if not cli_path:
        return {'status': 'failed', 'error': 'wedatacli 未找到（已尝试 WEDATACLI_PATH / CODEBUDDY_PLUGIN_ROOT/l0-cli / reference 上溯 ../../../l0-cli / 系统 PATH）'}

    payload_json = json.dumps(payload_dict, ensure_ascii=False)
    try:
        proc = subprocess.run(
            [cli_path, api_name, '-'] + _builder_workspace_folder_extra_args(),
            input=payload_json,
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=_KANBAN_API_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return {'status': 'failed', 'error': f'{api_name} 调用超时（>{_KANBAN_API_TIMEOUT}s）'}
    except Exception as e:
        return {'status': 'failed', 'error': f'{api_name} 调用异常: {e}'}

    stdout = (proc.stdout or '').strip()
    stderr = (proc.stderr or '').strip()
    parsed = None
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None

    # 判定成功条件：returncode==0 且响应里有 Response.Data 字段（无 Response.Error）
    if proc.returncode == 0 and parsed:
        response = parsed.get('Response') or {}
        if response.get('Error'):
            return {
                'status': 'failed', 'response': response,
                'error': f"{response['Error'].get('Code', '')}: {response['Error'].get('Message', '')}",
                'raw_stdout': stdout, 'raw_stderr': stderr,
            }
        return {'status': 'success', 'response': response, 'raw_stdout': stdout, 'raw_stderr': stderr}

    # 失败：尝试从 parsed 提取错误，否则用 stderr
    if parsed and isinstance(parsed, dict):
        err = parsed.get('Response', {}).get('Error', {}) or parsed.get('errors', [])
        msg = json.dumps(err, ensure_ascii=False)[:500] if err else (stderr or stdout)[:500]
    else:
        msg = (stderr or stdout)[:500] or f'returncode={proc.returncode}'
    return {'status': 'failed', 'error': msg, 'raw_stdout': stdout, 'raw_stderr': stderr}


def _persist_access_key(params_path, access_key):
    """把 AccessKey 写回 kanban_save_params.json；未变化时不重复落盘。"""
    access_key = str(access_key or '').strip()
    if not access_key:
        return
    try:
        with open(params_path, 'r', encoding='utf-8') as f:
            params = json.load(f)
        if str(params.get('AccessKey') or '').strip() == access_key:
            return
        params['AccessKey'] = access_key
        tmp_path = f'{params_path}.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(params, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, params_path)
    except (IOError, json.JSONDecodeError, OSError) as e:
        print(f'⚠️ AccessKey 回填到 {params_path} 失败: {e}')


def _record_ai_kanban_to_product_json(access_key, display_name, params=None, action='update'):
    """登记 AI 看板到 /workspace/file/file.json，供 ReadProductJson 读取。
    通道降级：P0 直调 shared-scripts/record_resource.sh > P1 wedatacli RecordResource wrapper > P2 silent skip。

    ⚠️ 静默契约（用户明确要求，2026-09-08）：
      - WorkBuddy 本地连接器与 DataBuddy 沙箱下，此登记环节的**所有失败/异常/未找到**分支
        均**只落日志文件**（{tmpdir}/intelligent-kanban-registration.log），**不打印到 stdout/stderr**，
        避免对话面板出现 ⚠️ 警告误导用户以为看板保存出错。
      - 成功分支保留 stdout ✅ 提示（正向反馈，用户可感知）。
      - 若确需排查 rc=2 等问题，请查看上述日志文件。
    """
    access_key = str(access_key or '').strip()
    if not access_key:
        return ''

    def _kanban_log(msg):
        """静默追加登记日志到临时文件；任何异常吞掉，绝不影响主流程或污染对话输出。"""
        try:
            import tempfile
            import datetime
            log_path = os.path.join(tempfile.gettempdir(), 'intelligent-kanban-registration.log')
            ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(log_path, 'a', encoding='utf-8') as _lf:
                _lf.write(f'[{ts}] [record_ai_kanban] {msg}\n')
        except Exception:
            pass

    name = str(display_name or '').strip() or 'AI 看板'
    action = 'create' if action == 'create' else 'update'

    # 两条通道 argv 集一致（wrapper 只是原样透传给 record_resource.sh），因此复用同一份 record_args。
    record_args = [
        '--id', access_key,
        '--name', name,
        '--path', f'/dashboard/aiBoard/{access_key}',
        '--type', 'dashboard',
        '--subtype', 'ai_kanban',
        '--action', action,
        '--source', 'manual',
        '--command', 'UpdateAiKanBan',
    ]

    record_env = os.environ.copy()
    workspace_id = str((params or {}).get('WorkspaceId') or '').strip()
    if workspace_id:
        record_env.setdefault('TENCENTCLOUD_WORKSPACE_ID', workspace_id)
        record_env.setdefault('WEDATA_WORKSPACE_ID', workspace_id)

    import subprocess

    # P0：直调 shared-scripts/record_resource.sh。
    # 注意：该脚本不识别 --workspace_folder，workspace 上下文完全通过 record_env 继承。
    record_sh = _resolve_record_resource_script()
    if record_sh:
        try:
            proc = subprocess.run(
                ['bash', record_sh] + record_args,
                capture_output=True, text=True, timeout=15, env=record_env,
            )
            if proc.returncode == 0:
                print(f'✅ 已通过 shared-scripts/record_resource.sh 登记 AI 看板到 file.json (AccessKey={access_key})')
                return ''
            # 脚本存在但执行失败不回退 wrapper：wrapper 也转发到同一脚本，避免复现错误 + 双份 warning。
            # 静默契约：失败仅落日志，不打印到对话（不影响远端预览入库）。
            _kanban_log(f"P0 record_resource.sh 登记失败 rc={proc.returncode} stderr={(proc.stderr or '')[:300]}")
            return ''
        except Exception as e:
            # 直调异常（timeout / OSError 等）同样不回退 wrapper，避免连锁副作用。
            _kanban_log(f'P0 record_resource.sh 直调异常（已跳过）: {e}')
            return ''

    # P1：脚本未解析到 → 回退 wedatacli RecordResource 伪命令；P2：CLI 也不可用则 silent skip。
    cli_path = _resolve_wedatacli_path()
    if not cli_path:
        _kanban_log('P2 record_resource.sh 与 wedatacli 均未找到，已跳过登记（不影响远端预览入库）')
        return ''

    cmd = [cli_path, 'RecordResource'] + record_args
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15, env=record_env)
        if proc.returncode == 0:
            print(f'✅ 已复用 wedatacli RecordResource 登记 AI 看板到 file.json (AccessKey={access_key})')
        else:
            _kanban_log(f"P1 wedatacli RecordResource 登记失败 rc={proc.returncode} stderr={(proc.stderr or '')[:300]}")
    except Exception as e:
        _kanban_log(f'P1 wedatacli RecordResource 登记异常（已跳过）: {e}')
    return ''


def _resolve_params_path(write_result):
    """从 write_result（可空）派生 kanban_save_params.json 路径。"""
    if write_result and isinstance(write_result, dict):
        params_path = write_result.get('params_path') or ''
        if params_path and os.path.isfile(params_path):
            return params_path
    output_dir = get_kanban_output_dir()
    return os.path.join(output_dir, 'kanban_save_params.json')


def save_to_kanban_list(write_result=None):
    """保存/覆盖发布看板到「仪表盘 → AI 看板列表」。

    流程：
      1. 加载 kanban_save_params.json（其中 AccessKey 由 PREVIEW 保存/更新后回填）
      2. 复用本地 AccessKey 调 SaveAiKanBan；请求只携带 WorkspaceId + AccessKey
      3. 后端按同 AccessKey 从 PREVIEW 同步 DSL/Dataset/元信息到发布态
      4. 成功后回填 AccessKey 到 kanban_save_params.json

    入参:
        write_result: 可选；write_kanban_outputs() 的返回值。不传时从默认 .kanban_output 目录推断。

    返回:
        dict {
            'status': 'success' | 'failed',
            'action': 'publish' | 'preview' | 'none',
            'access_key': '...',
            'display_name': '...',
            'view_status': 'PUBLISHED' | 'PREVIEW',
            'dashboard_url': 'https://.../dashboard/aiBoard/<access_key>?o=&r='（成功时；缺 workspace/region 时不带对应参数）,
            'error': '...'（仅 failed），
        }
    """
    params_path = _resolve_params_path(write_result)
    params = _load_save_params(params_path)
    if not params:
        return {
            'status': 'failed', 'action': 'none', 'access_key': '',
            'error': f'kanban_save_params.json 不存在或损坏: {params_path}'
        }

    workspace_id = params.get('WorkspaceId') or os.environ.get('TENCENTCLOUD_WORKSPACE_ID', '')
    if not workspace_id:
        return {'status': 'failed', 'action': 'none', 'access_key': '',
                'error': 'WorkspaceId 缺失，无法保存'}

    display_name = params.get('DisplayName') or ''

    existing_access = (params.get('AccessKey') or '').strip()
    if not existing_access:
        return {
            'status': 'failed', 'action': 'none', 'access_key': '',
            'display_name': display_name,
            'error': 'AccessKey 缺失，无法发布；请先调用 update_to_kanban_list() 保存/更新 PREVIEW'
        }

    print(f'🔁 使用已有预览态（AccessKey={existing_access}），走 SaveAiKanBan 同步发布态')
    params['AccessKey'] = existing_access
    save_payload = _build_api_payload(params, 'save')
    res = _run_wedatacli_api('SaveAiKanBan', save_payload)
    action = 'publish'

    if res.get('status') != 'success':
        return {
            'status': 'failed', 'action': action, 'access_key': existing_access,
            'display_name': display_name, 'error': res.get('error', '未知错误')
        }

    data = (res.get('response') or {}).get('Data') or {}
    final_access = str(data.get('AccessKey') or existing_access or '')
    _persist_access_key(params_path, final_access)

    view_status = str(data.get('ViewStatus') or 'PUBLISHED')
    dashboard_url = build_ai_kanban_url(final_access, workspace_id=workspace_id)
    if dashboard_url:
        print(f'✅ 已发布到 AI 看板列表（AccessKey={final_access}） → {dashboard_url}')
    else:
        print(f'✅ 已发布到 AI 看板列表（AccessKey={final_access}）')
    return {
        'status': 'success', 'action': action,
        'access_key': final_access, 'display_name': display_name,
        'view_status': view_status,
        'dashboard_url': dashboard_url,
    }


def update_to_kanban_list(write_result=None):
    """保存/更新「仪表盘 → AI 看板」后端预览态（UpdateAiKanBan）。

    契约：update 只代表 PREVIEW 保存/更新，只调用 UpdateAiKanBan；
    AccessKey 非空时覆盖已有 PREVIEW；AccessKey 为空时仍调用 UpdateAiKanBan，
    由后端创建预览锚点并返回 AccessKey。SaveAiKanBan 只用于发布态，
    必须由用户明确“发布/上线/确认发布”后调用 save_to_kanban_list()。
    """
    params_path = _resolve_params_path(write_result)
    params = _load_save_params(params_path)
    if not params:
        return {'status': 'failed', 'action': 'preview', 'access_key': '',
                'error': f'kanban_save_params.json 不存在或损坏: {params_path}'}

    access_key = (params.get('AccessKey') or '').strip()
    display_name = params.get('DisplayName') or ''
    workspace_id = params.get('WorkspaceId') or os.environ.get('TENCENTCLOUD_WORKSPACE_ID', '')
    if not workspace_id:
        return {'status': 'failed', 'action': 'preview', 'access_key': access_key,
                'display_name': display_name, 'error': 'WorkspaceId 缺失，无法同步预览态'}

    if access_key:
        print(f'📤 调用接口: UpdateAiKanBan 更新预览态（AccessKey={access_key}）')
    else:
        print('📤 调用接口: UpdateAiKanBan 保存首次预览态（等待后端返回 AccessKey）')
    preview_payload = _build_api_payload(params, 'preview')
    res = _run_wedatacli_api('UpdateAiKanBan', preview_payload)
    if res.get('status') != 'success':
        return {'status': 'failed', 'action': 'preview', 'access_key': access_key,
                'display_name': display_name, 'error': res.get('error', '未知错误')}

    data = (res.get('response') or {}).get('Data') or {}
    final_access = str(data.get('AccessKey') or access_key or '')
    if not final_access:
        return {'status': 'failed', 'action': 'preview', 'access_key': '',
                'display_name': display_name, 'error': 'UpdateAiKanBan 未返回 AccessKey，无法建立预览锚点'}
    view_status = str(data.get('ViewStatus') or 'PREVIEW')
    _persist_access_key(params_path, final_access)
    params['AccessKey'] = final_access
    _record_ai_kanban_to_product_json(
        final_access,
        display_name,
        params,
        action='update' if access_key else 'create',
    )
    dashboard_url = build_ai_kanban_url(final_access, workspace_id=workspace_id)
    if dashboard_url:
        print(f'✅ 已保存到 AI 看板预览态（AccessKey={final_access}） → {dashboard_url}')
    else:
        print(f'✅ 已保存到 AI 看板预览态（AccessKey={final_access}）')
    return {'status': 'success', 'action': 'preview',
            'access_key': final_access, 'display_name': display_name,
            'view_status': view_status,
            'dashboard_url': dashboard_url}
