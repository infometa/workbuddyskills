"""
看板 DSL Emitter —— spec + runner 编译产物 → DSL JSON。

设计原则
========
1. **零重复计算**：emitter 不重新解析 spec / 不重新编译 SQL / 不重新生成数据。
   所有数据都来自 runner build_kanban() 编译循环里**已经计算好**的产物：
       - cfg（ECharts options dict） → Chart.Option（只保留样式与 dataBinding 字段映射，不内联业务数据）
       - kpi_config                  → KPI（DSL 称作 indexCard）的 Option 字段映射
       - slot_data                   → Dataset.data（首行 header 的二维数组 JSON 字符串，仅写入 SqlSlots）
       - 编译期 SQL                  → Dataset.sql

2. **DSL / Dataset 同源**：emitter 在 build_kanban() 末尾、PREVIEW 同步之前调用，
   保证本地 kanban_dsl.json 与写入平台的 lowerCamelCase Dataset 数组同源同步。
   入库时 HtmlContent 只承载页面/组件 DSL（不含 Datasets），SqlSlots 是唯一 Dataset 源。
   任何修改都通过改 spec 重跑 build_kanban，入库参数原子级一起更新。

3. **30 栅格映射**：DSL 约定 Cols=30，与 spec.grid_columns（默认 4）按比例映射：
       step = 30 // grid_columns
       w = span × step
       KPI 行 N 张卡走"等分 30"特殊映射：w = 30 // N（保证 N 张卡占满整行不留空隙）

4. **Dataset 1:1 绑定 widget**：每个 chart/kpi widget 对应一个独立 dataset，
   key/sql/data 一一对应，便于面板编辑回显与按需走 Sql 实时查询。
   纯文本 widget（page_title / page_subtitle）不绑定 dataset。

5. **SqlSlots 是唯一数据源**：Dataset.data 只是预览态初始快照，可能因体积阈值被整体剥离。
   前端必须通过 Widget.DatasetName 匹配 SqlSlots.key，优先使用 data，缺失或刷新时调用批量查询接口拉取最新 rows。

6. **不引入新 LLM API**：spec 形态零变化（LLM 仍只写 kanban_spec.py），
   emitter 完全是 runner 内部细节，遵循 SKILL P0-1 / P0-2。

入口
====
    emit_dsl(spec, widget_records, slot_data, sql_map, output_dir, slot_meta_map=None, save_meta=None) -> Dict
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from kanban_dsl import Spec, Source, Chart, Compare, Metric, Dim


DSL_VERSION = '1.0.0'
GRID_COLS = 30                  # DSL 约定（30 列，5 张 KPI 卡可整除）
ROW_HEIGHT_PX = 20              # widget.h × 20px = 实际高度
UPDATE_PAYLOAD_GZIP_THRESHOLD_BYTES = 64 * 1024
UPDATE_PAYLOAD_GZIP_MIN_SAVING_RATIO = 0.20
MAX_DEFAULT_RENDER_DATA_BYTES = 128 * 1024
MAX_UNCOMPRESSED_CONTENT_BYTES = 16 * 1024 * 1024
LEGACY_DATASET_FIELDS = frozenset({
    'Key', 'Sql', 'Metrics', 'Dimensions', 'Data', 'Columns',
    'RefreshInterval', 'SqlType', 'DataSourceId', 'ConnectionType',
})


def _encode_update_payload(text: str, field_name: str = '') -> str:
    """将 UpdateAiKanBan 大字段编码为 base64；超过阈值时优先使用 gzip+base64。"""
    raw = text.encode('utf-8')
    label = field_name or 'UpdateAiKanBan payload'
    if len(raw) > MAX_UNCOMPRESSED_CONTENT_BYTES:
        raise ValueError(
            f'{label} 解码后内容超过服务端上限: raw={len(raw)}B, '
            f'threshold={MAX_UNCOMPRESSED_CONTENT_BYTES}B'
        )

    raw_b64 = base64.b64encode(raw).decode('ascii')
    if len(raw) < UPDATE_PAYLOAD_GZIP_THRESHOLD_BYTES:
        return raw_b64

    gz = gzip.compress(raw, compresslevel=6)
    gz_b64 = base64.b64encode(gz).decode('ascii')
    saving_ratio = 1 - (len(gz_b64) / len(raw_b64)) if raw_b64 else 0
    if saving_ratio >= UPDATE_PAYLOAD_GZIP_MIN_SAVING_RATIO:
        print(f'📦 {label} 已启用 gzip+base64: raw={len(raw)}B, base64={len(raw_b64)}B, '
              f'gzipBase64={len(gz_b64)}B, saving={saving_ratio:.1%}')
        return gz_b64
    return raw_b64


def _validate_lower_camel_datasets(datasets: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """校验入库 Dataset 数组只使用当前 lowerCamelCase 字段协议。"""
    for index, dataset in enumerate(datasets):
        if not isinstance(dataset, dict):
            return False, f'DSL Dataset 协议错误：Datasets[{index}] 不是对象'
        legacy_fields = sorted(LEGACY_DATASET_FIELDS.intersection(dataset.keys()))
        if legacy_fields:
            key = dataset.get('key') or dataset.get('Key') or f'#{index}'
            return False, (
                'DSL Dataset 协议错误：检测到旧 PascalCase 字段 '
                f'{legacy_fields}，dataset={key}；请重跑当前 emitter 生成 lowerCamelCase 字段'
            )
    return True, ''


def _default_render_data_bytes(datasets: List[Dict[str, Any]]) -> int:
    """统计整组 Datasets 的默认渲染 data 字节数；结构不明确时返回 -1。"""
    total = 0
    for dataset in datasets:
        if not isinstance(dataset, dict):
            return -1
        if 'data' not in dataset or dataset.get('data') is None:
            continue
        data = dataset.get('data')
        data_text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
        total += len(data_text.encode('utf-8'))
        if total > MAX_DEFAULT_RENDER_DATA_BYTES:
            return total
    return total


def _strip_default_render_data_if_needed(datasets: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], bool, int]:
    """生成端与服务端保持同口径：整组默认渲染 data 超过阈值时删除所有 dataset.data。

    Dataset.data 只是可选预览快照；缺失时前端必须按 Widget.DatasetName 动态查询。
    """
    data_bytes = _default_render_data_bytes(datasets)
    if data_bytes < 0 or data_bytes <= MAX_DEFAULT_RENDER_DATA_BYTES:
        return datasets, False, data_bytes

    next_datasets: List[Dict[str, Any]] = []
    stripped = False
    for dataset in datasets:
        if not isinstance(dataset, dict):
            next_datasets.append(dataset)
            continue
        next_dataset = dict(dataset)
        if 'data' in next_dataset:
            next_dataset.pop('data', None)
            stripped = True
        next_datasets.append(next_dataset)
    return next_datasets, stripped, data_bytes


def _dsl_without_internal_fields(dsl: Dict[str, Any]) -> Dict[str, Any]:
    """移除 emitter/runner 内部诊断字段，保证入库 DSL 协议稳定。"""
    return {k: v for k, v in dsl.items() if not str(k).startswith('_')}


def _dsl_without_datasets(dsl: Dict[str, Any]) -> Dict[str, Any]:
    """HtmlContent 只承载页面/组件 DSL；Datasets 仅通过 SqlSlots 入库，避免重复存储。"""
    html_dsl = _dsl_without_internal_fields(dsl)
    html_dsl.pop('Datasets', None)
    return html_dsl


# 各 kind 推荐的 widget 高度（行数；× 20px = 像素高度）
# KPI 卡只有「数值 + 标签」两行内容，6 行 = 120px 留白过多；
# 4 行 = 80px 紧凑且足以容纳 24px 数值 + 标签 + 内边距，视觉上更协调。
HEIGHT_BY_KIND: Dict[str, int] = {
    'kpi':         4,
    'indexCard':   4,
    'text':        2,
    'line':        14,
    'bar':         14,
    'pie':         14,
    'scatter':     14,
    'radar':       14,
    'funnel':      14,
    'gauge':       14,
    'heatmap':     14,
    'candlestick': 14,
    'treemap':     14,
    'sunburst':    14,
    'sankey':      16,
    'graph':       16,
    'boxplot':     14,
    'parallel':    16,
    'table':       18,
    'compare':     14,
}

# 看板 DSL 默认视觉色板 / 圆角 / 阴影常量
ACCENT = '#FF6B35'  # 橙色 —— KPI 数值 / gauge 指针 / trend 强调
PRIMARY = '#0EA5E9'  # 青蓝 —— line/bar/pie 主色
KANBAN_COLORS = [
    '#4C84FF', '#36CBCB', '#F2637B', '#FAD337', '#975FE4',
    '#3AA1FF', '#4ECB73', '#FBD44A', '#F97B7B', '#6DD47E',
]
CARD_BORDER = '#eef2f7'
CARD_RADIUS = 14
TITLE_COLOR = '#0f172a'
KPI_LABEL_COLOR = '#64748b'

# 指标卡数值色板：5 张 KPI 常见于一行，避免整排"清一色橙"造成视觉疲劳。
# 首位保留 ACCENT（#FF6B35 橙）延续既有主视觉，后 4 位与 KANBAN_COLORS 主色系呼应，
# 且饱和度接近、明度接近，确保整排 KPI 在同一视觉权重上（不出现某张"过淡/过亮"）。
# 依赖前端契约：IndexCardWidget 的 valueColor 直接作用于数字字色（css color）。
KPI_VALUE_COLORS = [
    '#FF6B35',  # 橙 —— 主 KPI（承接 ACCENT）
    '#0EA5E9',  # 天蓝
    '#22C55E',  # 翠绿
    '#8B5CF6',  # 紫
    '#F59E0B',  # 琥珀
]


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _now_iso8601() -> str:
    """返回带 +08:00 时区的 ISO 8601 时间字符串。"""
    tz_cn = timezone(timedelta(hours=8))
    return datetime.now(tz_cn).strftime('%Y-%m-%dT%H:%M:%S+08:00')


def _expr_to_field_name(expr: str) -> str:
    """从 SQL 表达式提取主字段名（用于 KPI valueField / 兜底字段名）。

    简单启发式：
      - SUM(sales) → 'sales'
      - COUNT(*) → '*'
      - SUM(a)/SUM(b) → 'a'（取第一个字段）
      - 裸列名 → 原样
    """
    if not expr:
        return ''
    s = expr.strip()
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', s):
        return s
    m = re.match(
        r'^(?:SUM|AVG|COUNT|MIN|MAX|FIRST|LAST|MEDIAN)\s*\(\s*'
        r'(?:DISTINCT\s+)?(?P<c>[^),]+?)\s*[,)]',
        s, flags=re.IGNORECASE,
    )
    if m:
        c = m.group('c').strip().strip('`').strip('"')
        if c == '*':
            return '*'
        return c
    return s


def _normalize_unit(unit: Optional[str]) -> str:
    """统一单位文本，兼容全角百分号和空白。"""
    value = str(unit or '').strip()
    return '%' if value in ('%', '％') else value


def _is_percent_suffix(suffix: Optional[str]) -> bool:
    return _normalize_unit(suffix) == '%'


def _format_decimal_places(fmt: Optional[str], *, default: int = 0,
                           max_decimals: Optional[int] = None) -> int:
    """从 spec format 中提取小数位，并可统一封顶。"""
    fmt_s = (fmt or '').strip()
    decimal_match = re.search(r'\.(\d+)', fmt_s)
    decimals = int(decimal_match.group(1)) if decimal_match else default
    decimals = max(0, decimals)
    if max_decimals is not None:
        decimals = min(max_decimals, decimals)
    return decimals


def _format_to_numeral(fmt: Optional[str], prefix: str = '', suffix: str = '', *,
                       include_affixes: bool = True,
                       max_decimals: Optional[int] = None) -> str:
    """spec 风格 format → numeral.js 风格字符串（纯数字格式，不承担单位）。

    协议约定（前端渲染器统一消费 valuePrefix / valueSuffix 作为单位真源）：
      - valueFormat 只描述**纯数字**格式（千分位、小数位），不含 ¥ / % / 件 / 万 等单位；
      - 单位一律通过 chart 顶层的 valuePrefix / valueSuffix 字段下发，前端在渲染时拼装
        `${valuePrefix}${numeral(v).format(valueFormat)}${valueSuffix}`。

    format → numeral 转换示例：
      ',.0f'  → '0,0'
      ',.2f'  → '0,0.00'
      '.1f' + suffix='%' → '0.0'（% 走 valueSuffix，绝不拼进 numeral 格式串）
      ','     → '0,0'

    关于百分比：SQL 端已把百分比 × 100（例如 25.30 表示 25.30%），因此这里的 numeral
    表达式绝不能用 numeral 的百分比触发符 `%`（会二次 ×100 → 2530%）。本函数**始终不**
    在返回值中包含 `%` / `¥` 等单位字符，避免任何双单位拼接风险。

    参数说明：
      include_affixes: 保留形参用于向后兼容 emitter 内其他调用点，实际语义已收敛为
                       "永远剥离单位"。传 True 也不会把单位塞回 numeral 格式串——
                       调用方必须通过 valuePrefix / valueSuffix 显式下发单位。
    """
    del prefix, suffix, include_affixes  # 单位真源改由 valuePrefix / valueSuffix 承载
    fmt = (fmt or ',').strip()
    has_thousand = ',' in fmt
    decimal_match = re.search(r'\.(\d+)', fmt)
    decimals = int(decimal_match.group(1)) if decimal_match else 0
    decimals = max(0, decimals)
    if max_decimals is not None:
        decimals = min(decimals, max_decimals)

    base = '0,0' if has_thousand else '0'
    if decimals > 0:
        base += '.' + ('0' * decimals)
    return base


def _column_type_lower(col_type: str) -> str:
    """spec source.columns 的 type → Dataset columns[].columnType（小写枚举）。

    DSL 约定：string / int / bigint / double / decimal / date / timestamp / boolean
    """
    if not col_type:
        return 'string'
    t = col_type.strip().lower()
    mapping = {
        'string': 'string', 'varchar': 'string', 'char': 'string', 'text': 'string',
        'date': 'date',
        'timestamp': 'timestamp', 'datetime': 'timestamp',
        'unix': 'bigint',
        'int': 'int', 'integer': 'int', 'tinyint': 'int', 'smallint': 'int',
        'bigint': 'bigint', 'long': 'bigint',
        'double': 'double', 'float': 'double', 'real': 'double',
        'decimal': 'decimal', 'numeric': 'decimal',
        'boolean': 'boolean', 'bool': 'boolean',
    }
    return mapping.get(t, 'string')


def _column_type_upper(col_type_lower: str) -> str:
    """columnType（小写）→ table 列定义用的 DataType（大写，前端 table 渲染用）。"""

    return col_type_lower.upper()


def _is_numeric_lower(col_type_lower: str) -> bool:
    return col_type_lower in ('int', 'bigint', 'double', 'decimal')


def _metric_alias(m: Metric) -> str:
    """与 runner._metric_alias 同语义，用于查找列名。"""
    if m.alias:
        return m.alias
    s = (m.expr or '').strip()
    mm = re.match(
        r'^(?P<f>SUM|AVG|COUNT|MIN|MAX|FIRST|LAST)\s*\(\s*(?:DISTINCT\s+)?(?P<c>[^)]+?)\s*\)$',
        s, flags=re.IGNORECASE,
    )
    if mm:
        f = mm.group('f').lower()
        c = mm.group('c').strip().strip('`').strip('"')
        if c == '*':
            return f'{f}_count'
        if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', c):
            distinct = bool(re.search(r'DISTINCT', s, re.IGNORECASE))
            return f'{f}_distinct_{c}' if distinct else f'{f}_{c}'
    return _expr_to_field_name(s) or 'metric'


def _dim_alias(d: Dim) -> str:
    """与 runner._dim_sql 输出列名对齐。"""
    if d.alias:
        return d.alias
    if d.is_time:
        return f'{d.expr.strip()}_{d.granularity}'
    return _expr_to_field_name(d.expr)


# ---------------------------------------------------------------------------
# UI Settings 主题派生（保留主题色，但圆角/阴影对齐 mock 视觉）
# ---------------------------------------------------------------------------

_THEME_PRESETS: Dict[str, Dict[str, str]] = {
    'retail':    {'PrimaryColor': PRIMARY, 'BackgroundColor': '#F5F7FA', 'Mode': 'light'},
    'business':  {'PrimaryColor': '#1E40AF', 'BackgroundColor': '#F1F5F9', 'Mode': 'light'},
    'finance':   {'PrimaryColor': '#15803D', 'BackgroundColor': '#F0FDF4', 'Mode': 'light'},
    'monitor':   {'PrimaryColor': '#0891B2', 'BackgroundColor': '#0F172A', 'Mode': 'dark'},
    'dark':      {'PrimaryColor': '#3B82F6', 'BackgroundColor': '#0F172A', 'Mode': 'dark'},
}


def _build_ui_settings(theme: str) -> Dict[str, Any]:
    preset = _THEME_PRESETS.get((theme or '').lower(), _THEME_PRESETS['retail'])
    is_dark = preset['Mode'] == 'dark'
    return {
        'Theme': {
            'Mode': preset['Mode'],
            'PrimaryColor': preset['PrimaryColor'],
            'FontColor': '#E5E7EB' if is_dark else TITLE_COLOR,
            'BackgroundColor': preset['BackgroundColor'],
            'Padding': {'X': 24, 'Y': 24},
            'FontFamily': 'PingFang SC, Helvetica, Arial, sans-serif',
            'FontSize': 14,
            'FontWeight': '400',
            'EnableEdit': True,
            'EnableHoverHighlight': True,
            'HoverBorderStyle': 'dashed',
            'HoverBorderColor': preset['PrimaryColor'],
            'SelectedBorderStyle': 'solid',
            'SelectedBorderColor': preset['PrimaryColor'],
            'SelectedBorderWidth': 2,
            'BorderRadius': CARD_RADIUS,
            'BoxShadow': 30,
            'TitleAlign': 'left',
        },
        'Grid': {
            'Cols': GRID_COLS,
            'RowHeight': ROW_HEIGHT_PX,
            'Gutter': [12, 12],
        },
        'Locale': 'zh-CN',
        'Filters': [],
        'Variables': [],
    }


# ---------------------------------------------------------------------------
# Card / Title 默认样式（与 mock 视觉对齐）
# ---------------------------------------------------------------------------

def _default_card(*, transparent: bool = False) -> Dict[str, Any]:
    """DSL Card 默认样式（无 Size/Margin，Padding 用 {X,Y}，Border 含 Radius）。

    transparent=True 时用于纯文本 widget（page-title / note），
    去掉边框 / 阴影 / 背景。
    """
    if transparent:
        return {
            'Padding': {'X': 0, 'Y': 0},
            'Background': {'Color': 'transparent', 'Opacity': 100},
            'Border': {'Color': 'transparent', 'Width': 0, 'Style': 'none', 'Radius': 0},
        }
    return {
        'Padding': {'X': 16, 'Y': 16},
        'Background': {'Color': '#ffffff', 'Opacity': 100},
        'Border': {'Color': CARD_BORDER, 'Width': 1, 'Style': 'solid', 'Radius': CARD_RADIUS},
    }


def _default_title(text: str, *, kind: str = 'card') -> Dict[str, Any]:
    """生成 Title。

    kind:
      'page'       → 页面大标题（22px / 700 / Layout=vertical）
      'card'       → 卡片标题（14px / 600 / Layout=auto / Bottom margin=8）
      'kpi-label'  → KPI 卡 label（12px / 500 / 灰色 / 不加粗）
      'section'    → 分组段落标题（15px / 600）
    """
    # 说明：DSL 已用 Font.StrokeColor / Font.StrokeWidth（CSS `-webkit-text-stroke`
    # 作用在标题文字本身）取代原 Title.BorderBottom（作用在标题底部下划线）。默认不描边，
    # 与历史 BorderBottom={Color:null, Width:0, Style:'none'} 的"无边框"语义一致。
    base = {
        'Show': True,
        'Text': text,
        'Description': {'Show': False, 'Text': ''},
        'Margin': {'X': 0, 'Y': 0},
        'Padding': {'X': 0, 'Y': 0},
        'Font': {'Family': None, 'Size': 14, 'Weight': 600,
                 'Color': TITLE_COLOR, 'LetterSpacing': 0,
                 'StrokeColor': None, 'StrokeWidth': 0},
        'Decoration': {'Align': 'left', 'Bold': True, 'Italic': False,
                       'Underline': False, 'LineThrough': False},
    }
    if kind == 'page':
        base['Font'] = {'Family': None, 'Size': 22, 'Weight': 700,
                        'Color': TITLE_COLOR, 'LetterSpacing': 0,
                        'StrokeColor': None, 'StrokeWidth': 0}
        base['Margin'] = {'X': 0, 'Y': 0}
        base['Padding'] = {'X': 18, 'Y': 0}
    elif kind == 'kpi-label':
        # KPI 标签：符合现代 Dashboard 审美（Linear / Stripe / Vercel 风格）。
        # 12px / 500 / 浅灰（#94A3B8）+ 字距 0.4，与 32px 深黑数字形成"label—value"两级层次。
        # 浅灰 label 主动"退后"，让数字成为正负空间的唯一视觉中心。
        base['Padding'] = {'X': 0, 'Y': 4}
        base['Margin'] = {'X': 0, 'Y': 0}
        base['Font'] = {'Family': None, 'Size': 12, 'Weight': 500,
                        'Color': '#94A3B8', 'LetterSpacing': 0.4,
                        'StrokeColor': None, 'StrokeWidth': 0}
        base['Decoration'] = {'Align': 'left', 'Bold': False, 'Italic': False,
                              'Underline': False, 'LineThrough': False}
    elif kind == 'section':
        base['Font'] = {'Family': None, 'Size': 15, 'Weight': 600,
                        'Color': TITLE_COLOR, 'LetterSpacing': 0,
                        'StrokeColor': None, 'StrokeWidth': 0}
    elif kind == 'card':
        base['Margin'] = {'X': 0, 'Y': 8}
    return base


def _default_chart_block() -> Dict[str, Any]:
    """除 Option 之外的 Chart 通用配置块（前端兜底字段）。

    全部走 null 回退到主题默认，避免硬编码污染主题。
    """
    return {
        'Padding': {'X': 0, 'Y': 0},
        'Background': {'Color': None, 'Opacity': 100},
        'Legend': {'Show': True, 'Position': 'top', 'Orient': 'horizontal', 'Color': None},
        'Tooltip': {'Show': True, 'BackgroundColor': None, 'BorderColor': None, 'FontColor': None},
        'Axis': {
            'X': {'Name': '', 'LabelRotate': 0},
            'Y': {'Name': ''},
        },
    }


# ---------------------------------------------------------------------------
# Chart.Option 派发（按 widget_type）
# ---------------------------------------------------------------------------

def _build_indexcard_option(kpi_metric: Metric,
                            *,
                            value_field: Optional[str] = None,
                            color: str = ACCENT) -> str:
    """KPI Metric → Chart.Option（顶层 key=indexCard）字符串。

    DSL 渲染契约：indexCard 的 valueField 指向 dataset.columns[].columnName，
    valueFormat 仅表达**纯数字**的 numeral 格式串（千分位 / 小数位），
    单位一律通过顶层 valuePrefix / valueSuffix 下发；前端渲染器统一按
    `${valuePrefix}${numeral(v).format(valueFormat)}${valueSuffix}` 拼装。

    历史上曾把单位内联进 valueFormat 做"旧协议兜底"，但 numeral.js 对字面 `%`
    的语义在部分前端实现下会触发 ×100，与 SQL 端已 ×100 的百分比字段叠加导致
    二次放大（例如 25.30 → 2530%）。因此这里 valueFormat 绝不再承载单位。

    数值色由调用方按 KPI_VALUE_COLORS 轮换传入（默认 ACCENT 兼容旧行为）：
    整排 KPI 各取一色，与 KPI 标题（TITLE_COLOR 深灰）拉开对比，
    避免"一片橙色"或"一片黑白灰"的视觉疲劳。

    单位视觉分隔：
      - 非百分号后缀（如 '元' / 'K' / '万'）自动在前面补 U+2009 窄空格，
        改善 `12,345 元` 的可读性；`%` 保持紧贴数字（`50.1%`）符合中文排版习惯。
      - 前缀（如 `¥` / `$`）保持紧贴数字，符合货币符号排版习惯。
    """
    val_field = value_field or _metric_alias(kpi_metric) or _expr_to_field_name(kpi_metric.expr)
    prefix = _normalize_unit(kpi_metric.prefix)
    suffix = _normalize_unit(kpi_metric.suffix)
    is_percent = _is_percent_suffix(suffix)
    # 非 % 的文字后缀（元/万/K/件…）加窄空格分隔；% 保持紧贴。
    if suffix and not is_percent and not suffix.startswith(('\u2009', ' ')):
        suffix = '\u2009' + suffix
    decimals = _format_decimal_places(kpi_metric.format, default=2 if is_percent else 0,
                                      max_decimals=2 if is_percent else None)
    # valueFormat 只表达纯数字格式（千分位/小数位）；单位由 valuePrefix / valueSuffix 承载，
    # 前端渲染器拼装 `${valuePrefix}${numeral(v).format(valueFormat)}${valueSuffix}`。
    val_format = _format_to_numeral(
        kpi_metric.format,
        max_decimals=2 if is_percent else None,
    )
    index_card = {
        'dataBinding': _build_data_binding('indexCard', {'value': val_field}),
        'valueField': val_field,
        'valueFormat': val_format,
        # valueFontSize 走存量兼容：前端契约优先 Chart.Text.Font.Size（emitter 已在
        # KPI 分支写入 24），存量 DSL 走这里的 24 兜底。
        # 字号选型：一行 5~6 张 KPI 时，单卡内宽通常 <180px，长金额数字（10~12 位含千分位）
        # 用 32/36 会溢出被截断（例如 135,702,970 显示为 135,702,97）。降到 24 既保证
        # 长数字完整可读，也与 12px 标题保持 2x 层次比（Linear / Notion / Vercel 通用尺度）。
        'valueFontSize': 24,
        'valueColor': color,
        'showTrend': False,
        # 单位真源：valuePrefix / valueSuffix，前端渲染器统一消费。
        'valuePrefix': prefix,
        'valueSuffix': suffix,
        'decimalPlaces': decimals,
    }
    return json.dumps({'indexCard': index_card}, ensure_ascii=False)


# 依赖笛卡尔坐标系（必须显式声明 xAxis + yAxis 才能 setOption 渲染）的图表族。
# 与 frontend/packages/dashboard-aidash/src/widgets/EChartsWidget.tsx 的 CARTESIAN_TYPES 保持一致。
_CARTESIAN_KINDS = frozenset({'line', 'bar', 'scatter', 'boxplot', 'candlestick', 'heatmap'})


def _ensure_cartesian_axes(kind: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """笛卡尔族 cfg 缺 xAxis / yAxis 时补一个最小可工作声明，不覆盖已声明字段。

    动机：ECharts 在 series 落到笛卡尔坐标系（line/bar/scatter/...）时，
    必须能找到 xAxisIndex/yAxisIndex 指向的轴对象，否则会抛
    `xAxis "0" not found` / `yAxis "0" not found`。DSL 自身就该是
    "取出即可 setOption" 的，前端兜底只是安全网。
    """
    # 也兼容 series[].type 是笛卡尔但顶层 kind 不是的情形
    series = cfg.get('series')
    series_has_cartesian = isinstance(series, list) and any(
        isinstance(s, dict) and s.get('type') in _CARTESIAN_KINDS for s in series
    )
    if kind not in _CARTESIAN_KINDS and not series_has_cartesian:
        return cfg

    next_cfg = dict(cfg)  # 浅拷贝即可，xAxis/yAxis 是顶层字段
    if next_cfg.get('xAxis') is None:
        next_cfg['xAxis'] = {'type': 'category'}
    if next_cfg.get('yAxis') is None:
        next_cfg['yAxis'] = {'type': 'value'}
    return next_cfg


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """历史渲染协议里的 _hexToRgba Python 等价实现。"""
    if not hex_color or not isinstance(hex_color, str):
        return f'rgba(76,132,255,{alpha})'
    if hex_color.startswith('rgb'):
        return hex_color
    h = hex_color.strip().lstrip('#')
    if len(h) == 3:
        h = ''.join(ch * 2 for ch in h)
    if len(h) != 6:
        return f'rgba(76,132,255,{alpha})'
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return f'rgba(76,132,255,{alpha})'
    return f'rgba({r},{g},{b},{alpha})'


def _linear_gradient(x: int, y: int, x2: int, y2: int, stops: List[Tuple[float, str]]) -> Dict[str, Any]:
    """ECharts JSON 形式线性渐变，等价于运行态的 echarts.graphic.LinearGradient。"""
    return {
        'type': 'linear',
        'x': x,
        'y': y,
        'x2': x2,
        'y2': y2,
        'colorStops': [{'offset': offset, 'color': color} for offset, color in stops],
        'global': False,
    }


def _as_dict_list(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _ensure_axis_style(axis: Any) -> None:
    """补齐旧协议 axisLabel/axisLine/axisTick/splitLine/nameTextStyle。"""
    if isinstance(axis, list):
        for item in axis:
            _ensure_axis_style(item)
        return
    if not isinstance(axis, dict):
        return
    axis_label = axis.setdefault('axisLabel', {})
    if isinstance(axis_label, dict):
        axis_label.setdefault('color', KPI_LABEL_COLOR)
        axis_label.setdefault('fontSize', 11)
        axis_label.setdefault('margin', 12)
        if axis.get('type') == 'category':
            axis_label.setdefault('overflow', 'truncate')
            axis_label.setdefault('width', 80)
    axis_line = axis.setdefault('axisLine', {})
    if isinstance(axis_line, dict):
        axis_line.setdefault('lineStyle', {'color': '#e2e8f0'})
        if axis.get('type') == 'value':
            axis_line.setdefault('show', False)
    axis_tick = axis.setdefault('axisTick', {})
    if isinstance(axis_tick, dict):
        axis_tick.setdefault('show', False)
    axis.setdefault('splitLine', {'lineStyle': {'type': 'dashed', 'color': 'rgba(15,23,42,0.06)'}})
    if axis.get('name') and not axis.get('nameTextStyle'):
        axis['nameTextStyle'] = {'color': '#94a3b8', 'fontSize': 11}


def _polish_data_zoom(data_zoom: Any, primary: str) -> None:
    """补齐旧协议缩放滑块样式。"""
    for dz in _as_dict_list(data_zoom):
        if dz.get('type') != 'slider':
            continue
        dz.setdefault('borderColor', 'transparent')
        dz.setdefault('backgroundColor', 'rgba(15,23,42,0.02)')
        dz.setdefault('fillerColor', _hex_to_rgba(primary, 0.18))
        dz.setdefault('handleStyle', {
            'color': primary,
            'borderColor': '#fff',
            'borderWidth': 2,
            'shadowColor': 'rgba(15,23,42,0.15)',
            'shadowBlur': 6,
        })
        dz.setdefault('moveHandleStyle', {'color': primary, 'opacity': 0.6})
        dz.setdefault('height', 18)
        dz.setdefault('dataBackground', {
            'lineStyle': {'color': _hex_to_rgba(primary, 0.4), 'width': 1},
            'areaStyle': {'color': _hex_to_rgba(primary, 0.10)},
        })
        dz.setdefault('selectedDataBackground', {
            'lineStyle': {'color': primary, 'width': 1},
            'areaStyle': {'color': _hex_to_rgba(primary, 0.25)},
        })
        dz.setdefault('textStyle', {'color': '#94a3b8', 'fontSize': 10})


def _polish_echarts_option(kind: str,
                           option: Dict[str, Any],
                           slot_data: Optional[List[List[Any]]] = None) -> Dict[str, Any]:
    """复用历史渲染协议 _polishOption 的样式兜底。

    只注入可 JSON 序列化的视觉/交互字段，不写入 series.data、axis.data、dataset.source 等运行态数据，
    因而不会破坏 HtmlContent data-free 契约。
    """
    if not isinstance(option, dict):
        return option
    next_option = option
    primary = KANBAN_COLORS[0]
    next_option.setdefault('color', KANBAN_COLORS)
    next_option.setdefault('animation', True)
    next_option.setdefault('animationDuration', 800)
    next_option.setdefault('animationEasing', 'cubicOut')
    next_option.setdefault('animationDurationUpdate', 500)
    next_option.setdefault('animationEasingUpdate', 'cubicOut')

    for tooltip in _as_dict_list(next_option.get('tooltip')):
        tooltip.setdefault('backgroundColor', 'rgba(255,255,255,0.96)')
        tooltip.setdefault('borderColor', '#e2e8f0')
        tooltip.setdefault('borderWidth', 1)
        tooltip.setdefault('textStyle', {'color': '#334155', 'fontSize': 12})
        tooltip.setdefault(
            'extraCssText',
            'box-shadow: 0 8px 24px -8px rgba(15,23,42,0.18); border-radius: 10px; padding: 8px 12px;',
        )

    for legend in _as_dict_list(next_option.get('legend')):
        legend.setdefault('textStyle', {'color': KPI_LABEL_COLOR, 'fontSize': 12})
        legend.setdefault('itemGap', 18)
        legend.setdefault('itemWidth', 14)
        legend.setdefault('itemHeight', 8)
        legend.setdefault('icon', 'roundRect')

    for grid in _as_dict_list(next_option.get('grid')):
        grid.setdefault('containLabel', True)

    _ensure_axis_style(next_option.get('xAxis'))
    _ensure_axis_style(next_option.get('yAxis'))

    for radar in _as_dict_list(next_option.get('radar')):
        # setdefault 保护 DSL 内已声明的自定义 splitArea / splitLine / axisLine，避免样式覆盖。
        radar.setdefault('splitArea', {
            'areaStyle': {
                'color': [
                    _hex_to_rgba(primary, 0.02),
                    _hex_to_rgba(primary, 0.05),
                    _hex_to_rgba(primary, 0.08),
                    _hex_to_rgba(primary, 0.11),
                    _hex_to_rgba(primary, 0.14),
                ],
            },
        })
        radar.setdefault('axisName', {'color': '#475569', 'fontSize': 11})
        radar.setdefault('splitLine', {'lineStyle': {'color': 'rgba(15,23,42,0.08)'}})
        radar.setdefault('axisLine', {'lineStyle': {'color': 'rgba(15,23,42,0.08)'}})

    for visual_map in _as_dict_list(next_option.get('visualMap')):
        visual_map.setdefault('textStyle', {'color': KPI_LABEL_COLOR, 'fontSize': 11})
        visual_map.setdefault('inRange', {
            'color': ['#eaf6fb', '#a5e0ed', '#52c0d6', primary, _hex_to_rgba(primary, 0.95)],
        })
        visual_map.setdefault('itemWidth', 14)
        visual_map.setdefault('itemHeight', 100)
        # 底部横向图例默认 bottom=0 时，会与 xAxis label 重叠；提升到 8 并同步扩展 grid.bottom。
        if visual_map.get('orient') == 'horizontal' and (visual_map.get('bottom') in (0, '0', None)):
            visual_map['bottom'] = 8
            for grid in _as_dict_list(next_option.get('grid')):
                grid['bottom'] = max(int(grid.get('bottom') or 0), 76)

    for parallel_axis in _as_dict_list(next_option.get('parallelAxis')):
        parallel_axis.setdefault('nameTextStyle', {'color': '#475569', 'fontSize': 11})
        parallel_axis.setdefault('axisLine', {'lineStyle': {'color': '#cbd5e1'}})
        parallel_axis.setdefault('axisLabel', {'color': KPI_LABEL_COLOR, 'fontSize': 10})

    _polish_data_zoom(next_option.get('dataZoom'), primary)

    series = next_option.get('series')
    series_arr: List[Dict[str, Any]] = []
    if isinstance(series, list):
        series_arr = [s for s in series if isinstance(s, dict)]
    elif isinstance(series, dict):
        series_arr = [series]

    for idx, item in enumerate(series_arr):
        series_type = item.get('type') or kind
        color = KANBAN_COLORS[idx % len(KANBAN_COLORS)]
        if series_type == 'bar':
            item_style = item.setdefault('itemStyle', {})
            item_style['borderRadius'] = [10, 10, 0, 0]
            item_style.setdefault('color', _linear_gradient(0, 0, 0, 1, [
                (0, color),
                (1, _hex_to_rgba(color, 0.32)),
            ]))
            item_style.setdefault('shadowColor', _hex_to_rgba(color, 0.20))
            item_style.setdefault('shadowBlur', 6)
            item_style.setdefault('shadowOffsetY', 2)
            if item.get('barMaxWidth') is None or item.get('barMaxWidth') > 36:
                item['barMaxWidth'] = 36
            # ECharts 支持数值型 animationDelay/animationDelayUpdate，兼容 DSL JSON 序列化。
            item.setdefault('animationDelay', 40)
            item.setdefault('animationDelayUpdate', 20)
            item['emphasis'] = {
                'focus': 'series',
                'itemStyle': {'shadowBlur': 14, 'shadowColor': _hex_to_rgba(color, 0.55)},
            }
        elif series_type == 'line':
            item.setdefault('smooth', True)
            item.setdefault('symbol', 'circle')
            item['symbolSize'] = 7
            item['lineStyle'] = {
                'width': 2.8,
                'color': color,
                'shadowColor': _hex_to_rgba(color, 0.35),
                'shadowBlur': 8,
                'shadowOffsetY': 4,
            }
            item['itemStyle'] = {'color': '#fff', 'borderColor': color, 'borderWidth': 2.5}
            area_style = item.setdefault('areaStyle', {'opacity': 0.85})
            if isinstance(area_style, dict):
                area_style.setdefault('opacity', 0.85)
                area_style.setdefault('color', _linear_gradient(0, 0, 0, 1, [
                    (0, _hex_to_rgba(color, 0.32)),
                    (1, _hex_to_rgba(color, 0.02)),
                ]))
            item.setdefault('animationDelay', 30)
            item.setdefault('animationDelayUpdate', 15)
            item['emphasis'] = {'focus': 'series', 'scale': 1.4}
        elif series_type == 'pie':
            item_style = item.setdefault('itemStyle', {})
            item_style['borderRadius'] = 12
            item_style.setdefault('borderColor', '#fff')
            item_style['borderWidth'] = max(3, int(item_style.get('borderWidth') or 0))
            emphasis = item.setdefault('emphasis', {})
            emphasis['scale'] = True
            emphasis['scaleSize'] = 8
            emphasis.setdefault('itemStyle', {})
            emphasis['itemStyle'].setdefault('shadowBlur', 18)
            emphasis['itemStyle'].setdefault('shadowColor', 'rgba(15,23,42,0.18)')
            item.setdefault('padAngle', 2)
        elif series_type == 'gauge':
            item['progress'] = {
                'show': True,
                'width': 18,
                'roundCap': True,
                'itemStyle': {'color': _linear_gradient(0, 0, 1, 0, [(0, '#22d3ee'), (1, primary)])},
            }
            item['axisLine'] = {'lineStyle': {'width': 18, 'color': [[1, '#eef2f7']]}, 'roundCap': True}
            item['pointer'] = {
                'length': '60%',
                'width': 5,
                'itemStyle': {'color': primary, 'shadowColor': _hex_to_rgba(primary, 0.4), 'shadowBlur': 8},
            }
            item['axisTick'] = {'show': False}
            item['splitLine'] = {'show': False}
            item['axisLabel'] = {'show': False}
            item['anchor'] = {'show': True, 'size': 10, 'itemStyle': {'color': '#fff', 'borderWidth': 3, 'borderColor': primary}}
            detail = item.setdefault('detail', {})
            if isinstance(detail, dict):
                detail.setdefault('color', TITLE_COLOR)
                detail.setdefault('fontWeight', 700)
                detail.setdefault('fontSize', 22)
        elif series_type == 'funnel':
            item['itemStyle'] = {'borderColor': '#fff', 'borderWidth': 2, 'borderRadius': 6}
            label = item.setdefault('label', {'show': True, 'position': 'inside'})
            if isinstance(label, dict):
                label.setdefault('color', '#fff')
                label.setdefault('fontWeight', 600)
                label.setdefault('fontSize', 12)
                label.setdefault('overflow', 'truncate')
            item.setdefault('labelLayout', {'hideOverlap': True})
            item['gap'] = 4
            item['emphasis'] = {
                'label': {'fontSize': 14, 'fontWeight': 700},
                'itemStyle': {'shadowBlur': 14, 'shadowColor': 'rgba(15,23,42,0.2)'},
            }
        elif series_type == 'scatter':
            item_style = item.setdefault('itemStyle', {})
            item_style.setdefault('opacity', 0.82)
            item_style.setdefault('borderColor', '#fff')
            item_style.setdefault('borderWidth', 1.5)
            # 默认 6 太小 hover 时不易察觉；提升到 10 与旧协议视觉一致，DSL 显式声明仍生效。
            if item.get('symbolSize') is None or item.get('symbolSize') == 6:
                item['symbolSize'] = 10
            item['emphasis'] = {'scale': 1.4, 'focus': 'series', 'itemStyle': {'borderColor': primary, 'borderWidth': 2}}
        elif series_type == 'radar':
            item['areaStyle'] = {'opacity': 0.20}
            item['lineStyle'] = {'width': 2.5}
            item['symbol'] = 'circle'
            item['symbolSize'] = 6
            item['emphasis'] = {'lineStyle': {'width': 4}, 'areaStyle': {'opacity': 0.4}}
        elif series_type == 'heatmap':
            item_style = item.setdefault('itemStyle', {})
            item_style.setdefault('borderRadius', 4)
            item_style.setdefault('borderColor', '#fff')
            item_style.setdefault('borderWidth', 2)
            label = item.setdefault('label', {})
            if isinstance(label, dict):
                label.setdefault('color', TITLE_COLOR)
                label.setdefault('fontSize', 10)
            item['emphasis'] = {
                'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(15,23,42,0.3)', 'borderColor': primary, 'borderWidth': 2},
            }
        elif series_type == 'candlestick':
            item['itemStyle'] = {
                'color': '#10B981',
                'color0': '#EF4444',
                'borderColor': '#0d9488',
                'borderColor0': '#dc2626',
                'borderWidth': 1.5,
                'shadowColor': 'rgba(15,23,42,0.10)',
                'shadowBlur': 4,
                'shadowOffsetY': 2,
            }
            item['emphasis'] = {'itemStyle': {'shadowBlur': 12, 'shadowColor': 'rgba(15,23,42,0.25)'}}
        elif series_type == 'boxplot':
            item['itemStyle'] = {
                'color': _hex_to_rgba(primary, 0.18),
                'borderColor': primary,
                'borderWidth': 1.8,
                'shadowBlur': 4,
                'shadowColor': _hex_to_rgba(primary, 0.18),
                'shadowOffsetY': 2,
            }
            item['boxWidth'] = ['25%', '55%']
            item['emphasis'] = {
                'itemStyle': {
                    'color': _hex_to_rgba(primary, 0.35),
                    'borderColor': primary,
                    'borderWidth': 2.5,
                    'shadowBlur': 10,
                    'shadowColor': _hex_to_rgba(primary, 0.4),
                },
            }
        elif series_type == 'treemap':
            item['itemStyle'] = {'borderColor': '#fff', 'borderWidth': 2, 'gapWidth': 2, 'borderRadius': 6}
            label = item.setdefault('label', {})
            if isinstance(label, dict):
                label['show'] = True
                label.setdefault('formatter', '{b}')
                label.setdefault('color', '#fff')
                label.setdefault('fontWeight', 600)
                label.setdefault('fontSize', 12)
            item['upperLabel'] = {
                'show': True,
                'height': 24,
                'color': '#fff',
                'fontWeight': 700,
                'backgroundColor': 'rgba(0,0,0,0.15)',
                'padding': [4, 8],
                'borderRadius': 4,
            }
            item['breadcrumb'] = {
                'show': True,
                'top': 4,
                'left': 'center',
                'itemStyle': {
                    'color': 'rgba(255,255,255,0.85)',
                    'borderColor': '#cbd5e1',
                    'textStyle': {'color': '#475569', 'fontSize': 11},
                },
            }
            item['levels'] = [
                {'itemStyle': {'borderColor': '#fff', 'borderWidth': 2, 'gapWidth': 2}, 'color': KANBAN_COLORS[:8]},
                {'itemStyle': {'borderColor': 'rgba(255,255,255,0.6)', 'borderWidth': 1, 'gapWidth': 1},
                 'color': KANBAN_COLORS[:8], 'colorSaturation': [0.35, 0.7]},
                {'color': KANBAN_COLORS[:8], 'colorSaturation': [0.35, 0.6],
                 'itemStyle': {'borderWidth': 1, 'gapWidth': 1, 'borderColorSaturation': 0.6}},
            ]
        elif series_type == 'sankey':
            item['nodeWidth'] = 16
            item['nodeGap'] = 10
            item['nodeAlign'] = 'justify'
            item['itemStyle'] = {'borderRadius': 4, 'borderColor': '#fff', 'borderWidth': 1}
            item['lineStyle'] = {'color': 'gradient', 'curveness': 0.5, 'opacity': 0.55}
            item['emphasis'] = {'focus': 'adjacency', 'lineStyle': {'opacity': 0.85}}
            item['label'] = {
                'color': '#475569',
                'fontSize': 11,
                'fontWeight': 500,
                'overflow': 'truncate',
            }
            item.setdefault('labelLayout', {'hideOverlap': True})
        elif series_type == 'sunburst':
            item_style = item.setdefault('itemStyle', {})
            item_style.setdefault('borderColor', '#fff')
            item_style.setdefault('borderWidth', 2)
            item_style.setdefault('borderRadius', 4)
            item['label'] = {
                'show': True,
                'rotate': 'tangential',
                'minAngle': 8,
                'color': '#fff',
                'fontSize': 11,
                'fontWeight': 600,
                'overflow': 'truncate',
            }
            item['labelLayout'] = {'hideOverlap': True}
            item['emphasis'] = {'focus': 'ancestor', 'itemStyle': {'shadowBlur': 12, 'shadowColor': 'rgba(15,23,42,0.25)'}}
            item.setdefault('center', ['50%', '50%'])
            item.setdefault('radius', ['10%', '80%'])
            item.setdefault('levels', [
                {},
                {'r0': '10%', 'r': '35%', 'itemStyle': {'borderWidth': 2}, 'label': {'rotate': 'tangential', 'fontSize': 12, 'fontWeight': 700}},
                {'r0': '35%', 'r': '60%', 'itemStyle': {'borderWidth': 2}, 'label': {'rotate': 'tangential', 'fontSize': 11}},
                {'r0': '60%', 'r': '80%', 'itemStyle': {'borderWidth': 1}, 'label': {'rotate': 'tangential', 'fontSize': 10}},
            ])
        elif series_type == 'graph':
            line_style = item.setdefault('lineStyle', {})
            line_style['opacity'] = 0.9
            line_style['width'] = 2
            line_style['color'] = '#94a3b8'
            line_style['curveness'] = 0.3
            item['edgeSymbol'] = ['circle', 'arrow']
            item['edgeSymbolSize'] = [4, 8]
            item['emphasis'] = {'focus': 'adjacency', 'lineStyle': {'width': 4, 'opacity': 1}}
            item_style = item.setdefault('itemStyle', {})
            item_style.setdefault('borderColor', '#fff')
            item_style.setdefault('borderWidth', 2)
            item_style.setdefault('shadowBlur', 6)
            item_style.setdefault('shadowColor', 'rgba(99,102,241,0.25)')
        elif series_type == 'parallel':
            line_style = item.setdefault('lineStyle', {})
            line_style['width'] = 1.5
            line_style['opacity'] = 0.55
            line_style.setdefault('color', _linear_gradient(0, 0, 1, 0, [
                (0, '#22d3ee'),
                (0.5, primary),
                (1, '#7C3AED'),
            ]))
            item['emphasis'] = {'lineStyle': {'width': 3, 'opacity': 1}}
            item['smooth'] = True
    return next_option


def _inject_legacy_data_zoom(option: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> None:
    """旧协议：line/bar 类目数 >24 自动启用 inside + slider 缩放，>50 初始显示最近 50 条。

    - 阈值 24 避免中短序列（半年～两年月度）也强制出现滑块，视觉更清爽；
    - 只在 legend 原本位于底部时下移，防止与 top:0 的图例位置冲突。
    """
    if option.get('dataZoom'):
        return
    headers, rows = _slot_rows_xy(slot_data)
    if not headers or len(rows) <= 24:
        return
    count = len(rows)
    data_zoom_end = (50 / count * 100) if count > 50 else 100
    data_zoom_start = (100 - data_zoom_end) if count > 50 else 0
    option['dataZoom'] = [
        {'type': 'inside', 'start': data_zoom_start, 'end': 100, 'zoomOnMouseWheel': True},
        {
            'type': 'slider',
            'bottom': 8,
            'height': 20,
            'start': data_zoom_start,
            'end': 100,
            'borderColor': '#e2e8f0',
            'fillerColor': _hex_to_rgba(KANBAN_COLORS[0], 0.15),
            'handleStyle': {'color': KANBAN_COLORS[0]},
        },
    ]
    grid = option.get('grid')
    if isinstance(grid, dict):
        grid['bottom'] = max(int(grid.get('bottom') or 0), 64)
    legend = option.get('legend')
    if isinstance(legend, dict) and 'bottom' in legend:
        legend['bottom'] = max(int(legend.get('bottom') or 0), 32)


def _to_float(v: Any, default: float = 0.0) -> float:
    """slot_data 数值兜底转换（None / 字符串 / NaN 均退化为 default）。"""
    if v is None:
        return default
    try:
        f = float(v)
        if f != f:  # NaN
            return default
        return f
    except (TypeError, ValueError):
        return default


def _slot_rows_xy(slot_data: Optional[List[List[Any]]]) -> Tuple[List[str], List[List[Any]]]:
    """slot_data → (headers, data_rows)。slot_data 首行约定为 header。"""
    if not slot_data or not isinstance(slot_data, list) or len(slot_data) == 0:
        return [], []
    headers = [str(h) for h in (slot_data[0] or [])]
    rows = list(slot_data[1:]) if len(slot_data) > 1 else []
    return headers, rows


def _is_ratio_like_field(name: str) -> bool:
    """识别百分比/比率类字段，用于快照数据与默认 formatter 收敛小数位。

    采用"先排除后命中"的双通道策略，避免误伤：
    - 命中：以 `_pct/_percent/_percentage/_rate/_ratio` 结尾、以 `pct_/percent_/percentage_/ratio_/rate_` 开头、
      tokens 中出现 `pct/percent/percentage/rate/ratio`，或包含中文关键词（率/比例/占比）；
    - 排除（优先级最高）：
      * 命名类后缀 `_id/_key/_no/_num/_count/_cnt/_limit/_size/_length/_index` 等（例：`rate_id`、`rate_limit`）；
      * `percentile/quantile` 系列（分位数不是百分比）；
      * `rate_id/rate_limit/rate_key/rate_type` 这类明确表达"rate 的属性"的前缀词；
    - 特意去除历史上"任意子串含 rate/percent"的宽松匹配，防止把 concentration/celebration 等
      普通英文单词错认为比率字段。
    """
    n = str(name or '').strip().lower()
    if not n:
        return False

    # ── 显式排除 ────────────────────────────────────────────────
    if n in {'percentile', 'percentiles', 'quantile', 'quantiles'}:
        return False
    exclude_suffixes = ('_id', '_key', '_no', '_num', '_count', '_cnt',
                        '_limit', '_size', '_length', '_len', '_index', '_idx',
                        '_type', '_code', '_flag', '_status')
    if any(n.endswith(sfx) for sfx in exclude_suffixes):
        return False
    # rate_ 前缀 + 明确非比率语义（rate_id/rate_limit/rate_key 等）已被 exclude_suffixes 覆盖，此处无需重复。

    # ── 命中判定 ────────────────────────────────────────────────
    # 中文强信号
    if '率' in n or '比例' in n or '占比' in n:
        return True

    ratio_suffixes = ('_pct', '_percent', '_percentage', '_rate', '_ratio')
    if any(n.endswith(sfx) for sfx in ratio_suffixes):
        return True

    ratio_prefixes = ('pct_', 'percent_', 'percentage_', 'ratio_', 'rate_')
    if any(n.startswith(pfx) for pfx in ratio_prefixes):
        return True

    tokens = re.split(r'[_\-.\s]+', n)
    ratio_words = {'pct', 'percent', 'percentage', 'rate', 'ratio'}
    return any(t in ratio_words for t in tokens if t)


def _round_if_number(value: Any, decimals: int) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return round(float(value), decimals)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return value
        try:
            return round(float(text), decimals)
        except ValueError:
            return value
    return value


def _coerce_json_native(value: Any) -> Any:
    """把非 JSON 原生类型的单元格值兜底成可序列化形态。

    命中场景（真实 badcase 归因）：
      - pandas.Timestamp / numpy.datetime64：DuckDB 拉出的时间列在部分路径下
        以 Timestamp 直传到 slot_data，下游 json.dumps 会抛
        "Object of type Timestamp is not JSON serializable"，整张图退回 0 分。
      - datetime.datetime / datetime.date：Python 原生 datetime 也不是 JSON 原生。
      - Decimal / bytes / set：偶发场景兜底。
    非上述类型全部原样返回（含 None / int / float / bool / str / list / dict），
    保持 JSON 原生路径零开销、零副作用。
    """
    # 【顺序敏感】pd.NaT 是 datetime.datetime 子类，且 pd.NaT.isoformat()='NaT'；
    # 必须优先判 NaTType，否则会被下方 isinstance(datetime) 分支吞掉，返出字符串 'NaT'。
    cls_name = type(value).__name__
    if cls_name == 'NaTType':
        return None
    # datetime 原生类型（emitter 顶部已 import datetime）
    if isinstance(value, datetime):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    # datetime.date（datetime 之外的 date 对象，例如 df.dt.date）
    try:
        import datetime as _dt_mod
        if isinstance(value, _dt_mod.date):
            return value.isoformat()
    except Exception:
        pass
    # float('nan') / numpy.nan：JSON 序列化时 nan 会输出非法 NaN，图表消费方无法解析
    if isinstance(value, float) and value != value:  # NaN 的判定：与自身不相等
        return None
    # pandas.Timestamp / numpy.datetime64：动态识别，不硬依赖 pandas / numpy
    if cls_name in ('Timestamp', 'datetime64'):
        try:
            iso = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            # 极端情况：某些异常 Timestamp isoformat() 仍返 'NaT'
            if not iso or iso == 'NaT':
                return None
            return iso
        except Exception:
            return None
    if cls_name == 'Decimal':
        try:
            return float(value)
        except Exception:
            return str(value)
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode('utf-8', errors='replace')
        except Exception:
            return str(value)
    if isinstance(value, (set, frozenset)):
        return list(value)
    return value


def _normalize_slot_data_for_display(slot_data: Optional[List[List[Any]]],
                                     *,
                                     max_ratio_decimals: int = 2) -> Optional[List[List[Any]]]:
    """对默认快照数据做展示级归一，避免比例/百分比类字段长尾小数直接暴露。

    附加职责（防 0 分回归）：在返回前对每个 cell 走 `_coerce_json_native` 兜底，
    确保 pandas.Timestamp / datetime / Decimal 等非 JSON 原生类型不会流入下游
    json.dumps。此路径命中 slot_data 的唯一归一化入口，覆盖所有 emitter 层
    json.dumps（含 slim_dsl / datasets / Option / indexCard）。
    """
    if not slot_data or not isinstance(slot_data, list) or not slot_data:
        return slot_data
    headers = [str(x) for x in (slot_data[0] or [])]
    if not headers:
        return slot_data
    ratio_indexes = {idx for idx, name in enumerate(headers) if _is_ratio_like_field(name)}
    normalized: List[List[Any]] = [list(slot_data[0])]
    for row in slot_data[1:]:
        if not isinstance(row, list):
            normalized.append(row)
            continue
        next_row = list(row)
        for idx, cell in enumerate(next_row):
            # 先做类型兜底（Timestamp/date/Decimal/...），再做比例格式化
            coerced = _coerce_json_native(cell)
            if idx in ratio_indexes:
                coerced = _round_if_number(coerced, max_ratio_decimals)
            next_row[idx] = coerced
        normalized.append(next_row)
    return normalized


def _normalize_slot_data_for_widget(record: Dict[str, Any],
                                    slot_data: Optional[List[List[Any]]]) -> Optional[List[List[Any]]]:
    """按 widget 类型归一 slot_data，使默认快照、Chart.Option 与远端 SQL 列契约一致。"""
    if not slot_data or not isinstance(slot_data, list) or not slot_data:
        return slot_data
    normalized = [list(row) if isinstance(row, list) else row for row in slot_data]
    kind = str(record.get('kind') or record.get('type') or '')

    if kind == 'candlestick' and isinstance(normalized[0], list):
        headers = [str(h) for h in normalized[0]]
        if headers[:5] == ['date', 'o', 'c', 'l', 'h']:
            normalized[0] = ['date', 'open', 'close', 'low', 'high'] + list(normalized[0][5:])

    if kind == 'gauge':
        cfg = record.get('cfg') if isinstance(record.get('cfg'), dict) else {}
        spec_obj = record.get('spec_obj')
        metric = spec_obj.metrics[0] if isinstance(spec_obj, Chart) and spec_obj.metrics else None
        unit = _normalize_unit(cfg.get('unit') or (getattr(metric, 'suffix', '') if metric is not None else ''))
        if _is_percent_suffix(unit):
            decimals = _format_decimal_places(
                cfg.get('format') or (getattr(metric, 'format', None) if metric is not None else None),
                default=2,
                max_decimals=2,
            )
            headers = [str(h) for h in (normalized[0] or [])] if isinstance(normalized[0], list) else []
            value_idx = 1 if len(headers) >= 2 else 0
            for row in normalized[1:]:
                if isinstance(row, list) and value_idx < len(row):
                    row[value_idx] = _round_if_number(row[value_idx], decimals)

    return _normalize_slot_data_for_display(normalized)


def _dedupe_keep_order(values: List[Any]) -> List[str]:
    """按出现顺序去重，并统一转为非空字符串。"""
    seen = set()
    out: List[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _pick_existing_field(headers: List[str], candidates: List[Any], fallback: Optional[str] = None) -> Optional[str]:
    """从 headers 中按候选顺序选择真实存在的字段名。"""
    header_set = set(headers)
    for candidate in _dedupe_keep_order(candidates):
        if candidate in header_set:
            return candidate
    if fallback in header_set:
        return fallback
    return fallback if fallback else None


def _dim_field_candidates(d: Dim) -> List[str]:
    return _dedupe_keep_order([
        d.label,
        d.alias,
        _dim_alias(d),
        _expr_to_field_name(d.expr),
    ])


def _metric_field_candidates(m: Metric) -> List[str]:
    return _dedupe_keep_order([
        m.label,
        m.alias,
        _metric_alias(m),
        _expr_to_field_name(m.expr),
    ])


def _column_numeric_range(rows: List[List[Any]], col_index: int) -> Tuple[float, float]:
    vals = [abs(_to_float(r[col_index])) for r in rows if len(r) > col_index and r[col_index] is not None]
    if not vals:
        return 0.0, 0.0
    return min(vals), max(vals)


def _field_at(headers: List[str], index: int, fallback: str = '') -> str:
    """按列序读取字段名，缺失时回退到稳定占位名。"""
    if 0 <= index < len(headers) and headers[index]:
        return headers[index]
    return fallback


def _fields_from(headers: List[str], start: int = 0, end: Optional[int] = None) -> List[str]:
    """从 header 中截取非空字段名列表。"""
    values = headers[start:end] if end is not None else headers[start:]
    return [str(v) for v in values if str(v)]


# 只有 line/bar 依赖 ECharts dataset.source + series.encode 即可稳定运行。
# 其他图表虽然保留 encode 字段便于编辑器识别，但运行态仍需按 dataBinding.transform
# 从 SqlSlots rows 物化 series.data / nodes / links / children / axis.data 等结构。
_DATASET_ENCODE_TRANSFORMS = frozenset({'line', 'bar'})


def _build_data_binding(transform: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """声明前端如何从 Widget.DatasetName 对应的 SqlSlots Dataset 构造运行态图表数据。

    HtmlContent 只保存字段映射和转换意图；实际 rows 来自 SqlSlots.data 或
    BatchQueryAiKanBanData / RefreshAiKanBanSlot 的动态查询结果。
    """
    render_mode = 'datasetEncode' if transform in _DATASET_ENCODE_TRANSFORMS else 'runtimeTransform'
    return {
        'version': 1,
        'source': 'sqlSlots',
        'datasetKeyRef': 'Widget.DatasetName',
        'refreshApi': 'batchQueryAiKanBanData',
        'slotKeyRef': 'Widget.DatasetName',
        'transform': transform,
        'renderMode': render_mode,
        'fields': fields,
    }


def _dataset_placeholder() -> Dict[str, Any]:
    """ECharts dataset 占位配置；不包含 source，避免 HtmlContent 存业务数据。"""
    return {'sourceHeader': True}


def _is_inline_runtime_data_path(path: Tuple[str, ...], key: str) -> bool:
    """判断某个 option key 是否属于运行态数据，必须由 SqlSlots 注入而不能存入 HtmlContent。"""
    if 'dataBinding' in path:
        return False
    if key == 'source' and 'dataset' in path:
        return True
    if key in {'data', 'links', 'nodes', 'edges', 'children'} and 'series' in path:
        return True
    if key == 'data' and any(p in {'xAxis', 'yAxis', 'radiusAxis', 'angleAxis', 'singleAxis', 'parallelAxis'} for p in path):
        return True
    return False


def _inline_runtime_data_paths(value: Any, path: Tuple[str, ...] = ()) -> List[str]:
    """递归收集 Chart.Option 中不允许入库的运行态数据路径。"""
    paths: List[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_s = str(key)
            if _is_inline_runtime_data_path(path, key_s):
                paths.append('.'.join(path + (key_s,)))
                continue
            paths.extend(_inline_runtime_data_paths(child, path + (key_s,)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_inline_runtime_data_paths(child, path + (str(index),)))
    return paths


def _strip_inline_runtime_data(value: Any, path: Tuple[str, ...] = ()) -> Any:
    """移除 extras/cfg 中误带的运行态数据，保证 HtmlContent 严格 data-free。"""
    if isinstance(value, dict):
        next_value: Dict[str, Any] = {}
        for key, child in value.items():
            key_s = str(key)
            if _is_inline_runtime_data_path(path, key_s):
                continue
            next_value[key] = _strip_inline_runtime_data(child, path + (key_s,))
        return next_value
    if isinstance(value, list):
        return [_strip_inline_runtime_data(child, path + (str(index),)) for index, child in enumerate(value)]
    return value


def _collect_binding_fields(value: Any) -> List[str]:
    """从 dataBinding.fields 中提取需要存在于 Dataset.columns 的字段名。"""
    out: List[str] = []
    if isinstance(value, str):
        if value:
            out.append(value)
    elif isinstance(value, list):
        for item in value:
            out.extend(_collect_binding_fields(item))
    elif isinstance(value, dict):
        for key, item in value.items():
            if key == 'aliases':
                continue
            out.extend(_collect_binding_fields(item))
    return out


def _build_cartesian_dataset_option(kind: str,
                                    cfg: Dict[str, Any],
                                    slot_data: Optional[List[List[Any]]],
                                    chart: Optional[Chart] = None) -> Dict[str, Any]:
    """line / bar → dataset-driven ECharts option。

    为减少 payload，line/bar 不内联 series.data，而是显式生成 series.encode，
    由前端按 DatasetName 注入 SqlSlots 中的 dataset.source 后稳定渲染。
    """
    headers, rows = _slot_rows_xy(slot_data)
    x_field = headers[0] if headers else ''
    if isinstance(chart, Chart) and chart.dims:
        x_field = _pick_existing_field(headers, _dim_field_candidates(chart.dims[0]), x_field) or x_field

    y_fields: List[str] = []
    series_names: List[str] = []
    if isinstance(chart, Chart) and chart.metrics:
        for idx, metric in enumerate(chart.metrics):
            fallback = headers[idx + 1] if idx + 1 < len(headers) else None
            y_field = _pick_existing_field(headers, _metric_field_candidates(metric), fallback)
            if y_field:
                y_fields.append(y_field)
                series_names.append(metric.label or y_field)
    if not y_fields:
        y_fields = headers[1:]
        series_names = y_fields[:]

    series_cfg = cfg.get('series') if isinstance(cfg.get('series'), list) else []
    cfg_y_axis = cfg.get('yAxis')
    explicit_axis_index = any(
        isinstance(s, dict) and isinstance(s.get('yAxisIndex'), int) for s in series_cfg
    )
    max_axis_index = 0
    auto_dual_axis = False
    if not cfg_y_axis and not explicit_axis_index and len(y_fields) == 2 and rows:
        idx_a, idx_b = headers.index(y_fields[0]), headers.index(y_fields[1])
        _, max_a = _column_numeric_range(rows, idx_a)
        _, max_b = _column_numeric_range(rows, idx_b)
        small, large = sorted([max_a, max_b])
        auto_dual_axis = small > 0 and large / small >= 20

    series: List[Dict[str, Any]] = []
    for idx, y_field in enumerate(y_fields):
        s_cfg = dict(series_cfg[idx]) if idx < len(series_cfg) and isinstance(series_cfg[idx], dict) else {}
        s_type = s_cfg.get('type') or kind
        item = dict(s_cfg)
        item['type'] = s_type
        item['name'] = item.get('name') or (series_names[idx] if idx < len(series_names) else y_field)
        item['encode'] = {'x': x_field, 'y': y_field}
        if s_type == 'line' and 'smooth' not in item:
            item['smooth'] = bool(cfg.get('smooth', True))
        # 前端 _polishOption 对 bar 会强制 barMaxWidth<=36，这里不再硬编码，
        # 交给前端统一控制，避免协议冗余。
        if isinstance(chart, Chart) and chart.dual_axis and idx in chart.dual_axis:
            item['yAxisIndex'] = 1
        elif auto_dual_axis and idx == 1:
            item['yAxisIndex'] = 1
        if isinstance(item.get('yAxisIndex'), int):
            max_axis_index = max(max_axis_index, int(item['yAxisIndex']))
        series.append(item)

    if cfg_y_axis is not None:
        y_axis = cfg_y_axis if isinstance(cfg_y_axis, list) else [cfg_y_axis]
        y_axis = [dict(axis) if isinstance(axis, dict) else {'type': 'value'} for axis in y_axis]
        for axis in y_axis:
            axis.setdefault('type', 'value')
        while len(y_axis) <= max_axis_index:
            y_axis.append({'type': 'value'})
    elif max_axis_index > 0:
        y_axis = [
            {'type': 'value', 'name': series[0].get('name') if series else '左轴', 'position': 'left'},
            {'type': 'value', 'name': series[1].get('name') if len(series) > 1 else '右轴', 'position': 'right'},
        ]
    else:
        y_axis = [{'type': 'value'}]

    legend_data = [s.get('name') for s in series if s.get('name')]
    option = {
        'dataBinding': _build_data_binding(kind, {'x': x_field, 'y': y_fields}),
        'dataset': _dataset_placeholder(),
        'tooltip': cfg.get('tooltip') or {'trigger': 'axis'},
        'legend': cfg.get('legend') or {'show': len(series) > 1, 'top': 0,
                                        'type': 'scroll', 'data': legend_data},
        'grid': cfg.get('grid') or {'left': 48, 'right': 24 if max_axis_index == 0 else 58,
                                    'top': 42, 'bottom': 36, 'containLabel': True},
        'xAxis': cfg.get('xAxis') or {'type': 'category'},
        'yAxis': y_axis,
        'series': series,
    }
    _inject_legacy_data_zoom(option, slot_data)
    return option


def _build_pie_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, _ = _slot_rows_xy(slot_data)
    name_field = _field_at(headers, 0, 'name')
    value_field = _field_at(headers, 1, 'value')
    return {
        'dataBinding': _build_data_binding('pie', {'name': name_field, 'value': value_field}),
        'dataset': _dataset_placeholder(),
        'tooltip': {'trigger': 'item', 'formatter': '{b}: {c} ({d}%)'},
        'legend': {'bottom': 0, 'type': 'scroll', 'textStyle': {'color': KPI_LABEL_COLOR}},
        'series': [{
            'type': 'pie',
            'radius': cfg.get('radius') or ['38%', '58%'],
            'center': cfg.get('center') or ['50%', '46%'],
            'encode': {'itemName': name_field, 'value': value_field, 'tooltip': [name_field, value_field]},
            'label': {'show': True, 'position': 'outside', 'formatter': '{b} {d}%'},
            'labelLine': {'show': True, 'length': 8, 'length2': 8},
            'itemStyle': {'borderRadius': 4, 'borderColor': '#fff', 'borderWidth': 2},
        }],
    }


def _build_scatter_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, rows = _slot_rows_xy(slot_data)
    x_field = _field_at(headers, 0, 'x')
    y_field = _field_at(headers, 1, 'y')
    category_field = _field_at(headers, 2, '') if len(headers) >= 3 else ''
    size_field = ''
    # 兼容 [x,y,size,category] 与 [x,y,category] 两种形态。
    if len(headers) >= 4:
        size_field = _field_at(headers, 2, '')
        category_field = _field_at(headers, 3, '')
    fields: Dict[str, Any] = {'x': x_field, 'y': y_field}
    if size_field:
        fields['size'] = size_field
    if category_field:
        fields['category'] = category_field
    # x 轴类型推断：若 slot_data 中 x 列存在非空非数值值（如"<50 / 50-100 / 500+"价格区间，
    # 或商品名、业务档校等分类标签），就不能用 xAxis.type='value'，
    # 否则前端 parseFloat 后全部坡缩到 0 / 首个数字字首，散点图会变成"无数据"。
    def _x_axis_type() -> str:
        for row in rows or []:
            if not row:
                continue
            v = row[0]
            if v is None or v == '':
                continue
            try:
                float(v)
            except (TypeError, ValueError):
                return 'category'
        return 'value'

    def _ordered_categories() -> List[str]:
        if not category_field or category_field not in headers:
            return []
        cat_idx = headers.index(category_field)
        cats: List[str] = []
        seen = set()
        for row in rows or []:
            if len(row) <= cat_idx:
                continue
            cat = str(row[cat_idx] if row[cat_idx] not in (None, '') else '默认')
            if cat not in seen:
                seen.add(cat)
                cats.append(cat)
        return cats

    x_axis_type = _x_axis_type()
    x_axis: Dict[str, Any] = {'type': x_axis_type, 'name': x_field}
    if x_axis_type == 'category':
        # 分类 x 轴默认不需要 splitLine（避免多余的竖线干扰散点分布）。
        x_axis['splitLine'] = {'show': False}
    categories = _ordered_categories()
    base_encode: Dict[str, Any] = {'x': x_field, 'y': y_field, 'tooltip': _fields_from(headers)}
    if size_field:
        base_encode['size'] = size_field
    if category_field:
        base_encode['itemName'] = category_field

    def _coerce_num(val: Any) -> Any:
        """把可数字化的字符串转成数字，供 scatter data 数组使用；无法转就原样保留。"""
        if val is None or val == '':
            return val
        if isinstance(val, (int, float)):
            return val
        try:
            fv = float(val)
            iv = int(fv)
            return iv if iv == fv else fv
        except (TypeError, ValueError):
            return val

    def _row_point(row: List[Any]) -> List[Any]:
        """从一行 slot_data 抽取 [x, y] 或 [x, y, size] 二/三元组。"""
        point: List[Any] = [_coerce_num(row[0]) if len(row) > 0 else None,
                            _coerce_num(row[1]) if len(row) > 1 else None]
        if size_field and len(row) > 2:
            point.append(_coerce_num(row[2]))
        return point

    if categories:
        # 按 category 拆成多 series：直接物化 series.data，摆脱对前端 runtimeTransform
        # 「按 categoryValue 过滤 dataset」的隐式依赖，避免"所有类别叠在同色一条直线"
        # 的可视化事故（同一 dataset 被多 series 共用 encode 时，如前端未按类别过滤，
        # 每个 series 会拿到全量数据，图上出现同点多色叠加）。
        cat_idx = headers.index(category_field) if category_field in headers else -1
        series = []
        for idx, cat in enumerate(categories):
            if cat_idx >= 0:
                cat_rows = [row for row in (rows or [])
                            if len(row) > cat_idx and str(row[cat_idx] or '默认') == cat]
            else:
                cat_rows = []
            cat_data = [_row_point(r) for r in cat_rows]
            series.append({
                'type': 'scatter',
                'name': cat,
                # 物化 data 后 encode 用位置索引，兼容前端不再依赖 dataset。
                'encode': {'x': 0, 'y': 1, 'itemName': 0, 'tooltip': [0, 1]},
                'data': cat_data,
                'dataBinding': {'categoryValue': cat},
                'symbolSize': cfg.get('symbolSize', 6),
                'itemStyle': {'opacity': 0.82, 'color': KANBAN_COLORS[idx % len(KANBAN_COLORS)]},
            })
    else:
        series = [{
            'type': 'scatter',
            'name': y_field,
            'encode': base_encode,
            'symbolSize': cfg.get('symbolSize', 6),
            'itemStyle': {'opacity': 0.82},
        }]

    return {
        'dataBinding': _build_data_binding('scatter', fields),
        'dataset': _dataset_placeholder(),
        'tooltip': {'trigger': 'item'},
        'legend': {'show': bool(categories), 'bottom': 0, 'type': 'scroll', 'data': categories},
        'grid': {'left': 56, 'right': 24, 'top': 36, 'bottom': 64 if categories else 52, 'containLabel': True},
        'xAxis': x_axis,
        'yAxis': {'type': 'value', 'name': y_field},
        'series': series,
    }


def _build_heatmap_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, rows = _slot_rows_xy(slot_data)
    x_field = _field_at(headers, 0, 'x')
    y_field = _field_at(headers, 1, 'y')
    value_field = _field_at(headers, 2, 'value')
    # visualMap.min/max：优先使用 cfg 显式值，否则从 slot_data 第 3 列真实数据计算。
    # - min 走真实最小值（而非硬编码 0），让筛选拖动条对小数据段也具备可分辨的色阶。
    # - max 走真实最大值（而非硬编码 1），避免全部落到最大色阶。
    # 说明：前端 heatmap 分支在 config.visualMap 未提供时会自算 heatMax，
    # DSL 一旦提供 visualMap 就会覆盖前端计算，因此这里必须给出真实 min/max。
    cfg_visual_map = cfg.get('visualMap')
    if cfg_visual_map:
        visual_map = cfg_visual_map
    else:
        real_min, real_max = _column_numeric_range(rows, 2)
        vm_min = cfg.get('min')
        if vm_min is None:
            vm_min = real_min if real_max > 0 else 0
        vm_max = cfg.get('max')
        if not vm_max:
            vm_max = real_max if real_max > 0 else 1
        # 兜底：若 min>=max（单值或空数据），强制拉开一个可分辨的区间，避免 ECharts 报错。
        if vm_min >= vm_max:
            vm_min = 0 if vm_max > 0 else vm_min
            if vm_min >= vm_max:
                vm_max = vm_min + 1
        visual_map = {
            'min': vm_min, 'max': vm_max, 'calculable': True,
            'orient': 'horizontal', 'left': 'center', 'bottom': 0,
        }
    return {
        'dataBinding': _build_data_binding('heatmap', {'x': x_field, 'y': y_field, 'value': value_field}),
        'dataset': _dataset_placeholder(),
        'tooltip': {'position': 'top'},
        'grid': {'left': 50, 'right': 24, 'top': 28, 'bottom': 64, 'containLabel': True},
        'xAxis': {'type': 'category', 'splitArea': {'show': True}},
        'yAxis': {'type': 'category', 'splitArea': {'show': True}},
        'visualMap': visual_map,
        'series': [{'type': 'heatmap', 'encode': {'x': x_field, 'y': y_field, 'value': value_field},
                    'label': {'show': True}}],
    }


def _build_radar_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, rows = _slot_rows_xy(slot_data)
    name_field = _field_at(headers, 0, 'name')
    value_fields = _fields_from(headers, 1)
    # indicator.max：优先使用 cfg.indicator（外部显式指定），否则基于 slot_data
    # 逐维度计算真实 max × 1.2（与前端 renderEcharts 自动 max 语义一致）。
    # 硬编码 max=100 会把真实数据压扁到 100 以内，导致所有点几乎重合在圆心。
    if cfg.get('indicator'):
        indicators = cfg['indicator']
    else:
        indicators = []
        for idx, field in enumerate(value_fields):
            _, col_max = _column_numeric_range(rows, idx + 1)
            ind_max = round(col_max * 1.2, 2) if col_max > 0 else 100
            indicators.append({'name': field, 'max': ind_max})
    return {
        'dataBinding': _build_data_binding('radar', {'name': name_field, 'values': value_fields}),
        'dataset': _dataset_placeholder(),
        'tooltip': {'trigger': 'item'},
        'legend': {'bottom': 0, 'type': 'scroll', 'textStyle': {'color': KPI_LABEL_COLOR}},
        'radar': {
            'indicator': indicators,
            'center': cfg.get('center') or ['50%', '52%'],
            'radius': cfg.get('radius') or '58%',
            'shape': cfg.get('shape') or 'polygon',
        },
        'series': [{
            'type': 'radar',
            'encode': {'itemName': name_field, 'value': value_fields, 'tooltip': [name_field] + value_fields},
            'areaStyle': {'opacity': 0.15},
            'lineStyle': {'width': 2},
            'symbolSize': 5,
        }],
    }


def _build_gauge_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, rows = _slot_rows_xy(slot_data)
    name_field = _field_at(headers, 0, 'name') if len(headers) >= 2 else ''
    value_field = _field_at(headers, 1, 'value') if len(headers) >= 2 else _field_at(headers, 0, 'value')
    unit = _normalize_unit(cfg.get('unit') or '')
    is_percent = _is_percent_suffix(unit)
    fmt = cfg.get('format')
    decimals = _format_decimal_places(fmt, default=2 if is_percent else 0,
                                      max_decimals=2 if is_percent else None)
    value_format = _format_to_numeral(fmt, max_decimals=2 if is_percent else None)
    # max 自适应：优先使用 cfg.max；缺省时百分比场景默认 100，其他默认按首值放大 20%。
    # 若实际首值已超出 max（例如「月度销售目标完成率 = 13570.3%」），自动放大到 ceil(v * 1.2)。
    # 说明：_to_float 对 None / 非法值统一兜底为 0.0，因此 first_value 一定是 float，
    #      用 > 0 判定"是否拿到有效正数首值"即可，无需再区分 None。
    value_col = len(headers) - 1 if len(headers) >= 2 else 0
    first_value = _to_float(rows[0][value_col], 0.0) if rows and len(rows[0]) > value_col else 0.0
    cfg_max = cfg.get('max')
    if cfg_max is None:
        gauge_max = 100 if is_percent else (first_value * 1.2 if first_value > 0 else 100)
    else:
        gauge_max = _to_float(cfg_max, 100)
    if first_value > gauge_max:
        gauge_max = math.ceil(first_value * 1.2)
    fields: Dict[str, Any] = {'value': value_field}
    if name_field:
        fields['name'] = name_field
    return {
        'dataBinding': _build_data_binding('gauge', fields),
        'dataset': _dataset_placeholder(),
        # tooltip / detail 均不硬拼单位，单位统一由 valuePrefix / valueSuffix 承载，
        # 前端渲染器负责在展示时拼装 `${valuePrefix}${numeral(v).format(valueFormat)}${valueSuffix}`。
        'tooltip': {'trigger': 'item'},
        'valuePrefix': '',
        'valueSuffix': unit,
        'valueFormat': value_format,
        'decimalPlaces': decimals,
        'series': [{
            'type': 'gauge',
            'center': cfg.get('center') or ['50%', '58%'],
            'radius': cfg.get('radius') or '78%',
            'min': _to_float(cfg.get('min'), 0),
            'max': gauge_max,
            'detail': {
                'fontSize': 20,
                'fontWeight': 'bold',
                'offsetCenter': [0, '40%'],
                'valueFormat': value_format,
                'decimalPlaces': decimals,
                'valuePrefix': '',
                'valueSuffix': unit,
            },
            'title': {'fontSize': 12, 'offsetCenter': [0, '78%']},
            'encode': {'itemName': name_field or value_field, 'value': value_field,
                       'tooltip': [name_field, value_field] if name_field else [value_field]},
            'axisLine': {'lineStyle': {'width': 12}},
            'progress': {'show': True, 'width': 12},
            'pointer': {'length': '60%', 'width': 5},
            'valueFormat': value_format,
            'decimalPlaces': decimals,
            'valuePrefix': '',
            'valueSuffix': unit,
        }],
    }


def _build_boxplot_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, _ = _slot_rows_xy(slot_data)
    category_field = _field_at(headers, 0, 'category')
    value_fields = _fields_from(headers, 1, 6)
    while len(value_fields) < 5:
        value_fields.append('')
    min_f, q1_f, median_f, q3_f, max_f = value_fields[:5]
    return {
        'dataBinding': _build_data_binding('boxplot', {
            'category': category_field,
            'min': min_f,
            'q1': q1_f,
            'median': median_f,
            'q3': q3_f,
            'max': max_f,
        }),
        'dataset': _dataset_placeholder(),
        'tooltip': {'trigger': 'item'},
        'xAxis': {'type': 'category'},
        'yAxis': {'type': 'value'},
        'series': [{'type': 'boxplot', 'encode': {'itemName': category_field,
                                                  'tooltip': [category_field, min_f, q1_f, median_f, q3_f, max_f]}}],
    }


def _build_funnel_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, _ = _slot_rows_xy(slot_data)
    name_field = _field_at(headers, 0, 'stage_name')
    value_field = _field_at(headers, 1, 'value')
    return {
        'dataBinding': _build_data_binding('funnel', {'name': name_field, 'value': value_field}),
        'dataset': _dataset_placeholder(),
        'tooltip': {'trigger': 'item', 'formatter': '{b}: {c}'},
        'legend': {'bottom': 0, 'type': 'scroll'},
        'series': [{
            'type': 'funnel',
            'sort': cfg.get('sort') or 'descending',
            'gap': cfg.get('gap', 2),
            'radius': cfg.get('radius') or ['10%', '60%'],
            'left': '10%', 'right': '10%', 'top': 30, 'bottom': 40,
            'label': {'show': True, 'position': 'inside'},
            'labelLine': {'show': False},
            'itemStyle': {'borderColor': '#fff', 'borderWidth': 1},
            'encode': {'itemName': name_field, 'value': value_field, 'tooltip': [name_field, value_field]},
        }],
    }


def _build_candlestick_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, _ = _slot_rows_xy(slot_data)
    date_field = _field_at(headers, 0, 'date')
    # runner 本地快照历史上使用短列名 o/c/l/h，但远端刷新 SQL 输出 open/close/low/high。
    # dataBinding/encode 采用语义列名，并提供 aliases 兼容本地短列，避免刷新后 K 线字段 miss → 无数据。
    open_field = _pick_existing_field(headers, ['open', 'o'], 'open') or 'open'
    close_field = _pick_existing_field(headers, ['close', 'c'], 'close') or 'close'
    low_field = _pick_existing_field(headers, ['low', 'l'], 'low') or 'low'
    high_field = _pick_existing_field(headers, ['high', 'h'], 'high') or 'high'

    def _dedupe_aliases(*names: str) -> List[str]:
        out: List[str] = []
        seen = set()
        for n in names:
            if n and n not in seen:
                seen.add(n)
                out.append(n)
        return out

    aliases = {
        'date': _dedupe_aliases(date_field, 'date'),
        'open': _dedupe_aliases(open_field, 'open', 'o'),
        'close': _dedupe_aliases(close_field, 'close', 'c'),
        'low': _dedupe_aliases(low_field, 'low', 'l'),
        'high': _dedupe_aliases(high_field, 'high', 'h'),
    }
    return {
        'dataBinding': _build_data_binding('candlestick', {
            'date': date_field,
            'open': open_field,
            'close': close_field,
            'low': low_field,
            'high': high_field,
            'aliases': aliases,
        }),
        'dataset': _dataset_placeholder(),
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'cross'}},
        'grid': {'left': 60, 'right': 30, 'top': 30, 'bottom': 40, 'containLabel': True},
        'xAxis': {'type': 'category', 'axisLine': {'onZero': False}, 'boundaryGap': True},
        'yAxis': {'type': 'value', 'scale': True, 'splitLine': {'show': True}},
        'dataZoom': [
            # 默认展示全期数据（start=0），避免若 slot_data 行数、运行时实际数据量少
            # 时默认后半区间为空、用户看到"无数据"的视觉错觉。
            {'type': 'inside', 'start': 0, 'end': 100},
            {'show': True, 'type': 'slider', 'bottom': 10, 'start': 0, 'end': 100},
        ],
        'series': [{
            'type': 'candlestick',
            'encode': {'x': date_field, 'y': [open_field, close_field, low_field, high_field],
                       'tooltip': [date_field, open_field, close_field, low_field, high_field]},
            'fieldAliases': aliases,
            'itemStyle': {
                'color': '#ec0000', 'color0': '#00da3c',
                'borderColor': '#8A0000', 'borderColor0': '#008F28',
            },
        }],
    }


def _build_hierarchy_binding_option(kind: str,
                                    cfg: Dict[str, Any],
                                    slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, _ = _slot_rows_xy(slot_data)
    name_field = _field_at(headers, 0, 'name')
    value_field = _field_at(headers, 1, 'value')
    parent_field = _field_at(headers, 2, '') if len(headers) >= 3 else ''
    fields: Dict[str, Any] = {'name': name_field, 'value': value_field}
    if parent_field:
        fields['parent'] = parent_field
    if kind == 'treemap':
        # 下钻交互：nodeClick 支持 'zoomToNode'（点击非叶子节点缩放到该节点）/
        # 'link'（跳转链接）/ 'rootToNode'（当前节点作为根节点）/ False（禁用）。
        # 层级看板默认允许"点击下钻"以贯通"品类 → 商品"的层级探索路径；同时打开 roam
        # 让用户可拖拽/缩放画布查看深层节点。cfg 可显式覆盖为 False。
        node_click = cfg.get('nodeClick', 'zoomToNode') if 'nodeClick' in cfg else 'zoomToNode'
        return {
            'dataBinding': _build_data_binding('treemap', fields),
            'dataset': _dataset_placeholder(),
            'tooltip': {'trigger': 'item', 'formatter': '{b}: {c}'},
            'series': [{
                'type': 'treemap',
                'encode': {'itemName': name_field, 'value': value_field, 'tooltip': _fields_from(headers)},
                'roam': cfg.get('roam', True),
                'nodeClick': node_click,
                'breadcrumb': {'show': True},
                'label': {'show': True, 'formatter': '{b}'},
                'itemStyle': {'borderColor': '#fff', 'borderWidth': 1, 'gapWidth': 1},
                'levels': [
                    {'itemStyle': {'borderColor': '#fff', 'borderWidth': 2, 'gapWidth': 2}},
                    {'itemStyle': {'borderColor': '#fff', 'borderWidth': 1, 'gapWidth': 1}},
                ],
            }],
        }
    # sunburst：ECharts 默认 nodeClick='rootToNode' 已支持点击下钻，这里显式声明
    # 以避免下游渲染器合并 DSL 时误用其他默认值（例如 False）导致点击无响应。
    return {
        'dataBinding': _build_data_binding('sunburst', fields),
        'dataset': _dataset_placeholder(),
        'tooltip': {'trigger': 'item', 'formatter': '{b}: {c}'},
        'series': [{
            'type': 'sunburst',
            'encode': {'itemName': name_field, 'value': value_field, 'tooltip': _fields_from(headers)},
            'radius': cfg.get('radius') or ['15%', '80%'],
            'center': cfg.get('center') or ['50%', '52%'],
            'nodeClick': cfg.get('nodeClick', 'rootToNode'),
            'label': {'rotate': 'radial', 'minAngle': 8},
            'itemStyle': {'borderColor': '#fff', 'borderWidth': 1},
            'emphasis': {'focus': 'ancestor'},
        }],
    }


def _build_sankey_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, _ = _slot_rows_xy(slot_data)
    source_field = _field_at(headers, 0, 'source')
    target_field = _field_at(headers, 1, 'target')
    value_field = _field_at(headers, 2, 'value')
    return {
        'dataBinding': _build_data_binding('sankey', {'source': source_field, 'target': target_field, 'value': value_field}),
        'dataset': _dataset_placeholder(),
        'tooltip': {'trigger': 'item', 'triggerOn': 'mousemove'},
        'series': [{
            'type': 'sankey',
            'encode': {'source': source_field, 'target': target_field, 'value': value_field,
                       'tooltip': [source_field, target_field, value_field]},
            'left': 40, 'right': 60, 'top': 20, 'bottom': 20,
            'nodeAlign': cfg.get('nodeAlign') or 'justify',
            'nodeGap': cfg.get('nodeGap', 8),
            'nodeWidth': cfg.get('nodeWidth', 12),
            'label': {'show': True, 'fontSize': 11},
            'emphasis': {'focus': 'adjacency'},
            'lineStyle': {'color': 'gradient', 'curveness': 0.5, 'opacity': 0.5},
        }],
    }


def _build_graph_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, rows = _slot_rows_xy(slot_data)
    source_field = _field_at(headers, 0, 'source')
    target_field = _field_at(headers, 1, 'target') if len(headers) >= 2 else 'target'
    value_field = _field_at(headers, 2, 'value') if len(headers) >= 3 else (
        _field_at(headers, 1, 'value') if len(headers) >= 2 else 'value'
    )

    def _all_edges_are_self_loops() -> bool:
        if len(headers) < 3 or not rows:
            return False
        has_edge = False
        for row in rows:
            if len(row) < 2:
                continue
            src = '' if row[0] is None else str(row[0])
            tgt = '' if row[1] is None else str(row[1])
            if not src or not tgt:
                continue
            has_edge = True
            if src != tgt:
                return False
        return has_edge

    node_mode = len(headers) == 2 or _all_edges_are_self_loops()
    if node_mode:
        # 自环边会被 ECharts graph/旧运行时过滤掉；全自环时退化为节点权重网络，至少展示节点规模。
        fields = {'name': source_field, 'value': value_field}
        transform = 'graphNodes'
    else:
        fields = {'source': source_field, 'target': target_field, 'value': value_field}
        transform = 'graphLinks'
    series_item = {
        'type': 'graph',
        'layout': cfg.get('layout') or 'force',
        'roam': cfg.get('roam', True),
        # graph 属于非笛卡尔族 series：数据消费走 series.data / series.links（由前端
        # runtimeTransform graphLinks/graphNodes 组装），ECharts 不通过 encode 引用节点
        # 数据的列。此处若显式声明 encode.tooltip=['source','target','value']，会触发
        # ECharts 6 SeriesData encodeGlobal 编码路径把 'source'/'target' 视作维度并到
        # 节点数据中查找，节点对象 {name, symbolSize, category} 上不存在该维度 →
        # 编码失败 → 整个 series 静默不渲染（画布空白，不 throw）。
        # 因此对 graph 不再写 encode；tooltip 走默认 params.name / params.value 即可。
        'draggable': True,
        'left': '5%',
        'right': '5%',
        'top': 30,
        'bottom': 30,
        'center': cfg.get('center') or ['50%', '50%'],
        'symbolSize': cfg.get('symbolSize', 24),
        'force': {'repulsion': 180, 'edgeLength': [40, 90], 'gravity': 0.15},
        'label': {'show': True, 'position': 'right', 'fontSize': 11},
        'labelLayout': {'hideOverlap': True},
        'lineStyle': {'opacity': 0.6, 'curveness': 0.15, 'width': 1},
        'emphasis': {'focus': 'adjacency', 'lineStyle': {'width': 2}},
    }
    if node_mode:
        series_item['edgeSymbol'] = ['none', 'none']
    return {
        'dataBinding': _build_data_binding(transform, fields),
        'dataset': _dataset_placeholder(),
        'tooltip': {'trigger': 'item'},
        'legend': [{'show': False}],
        # graph 不需要 xAxis/yAxis，但前端 force 布局在小卡片（例如 ≤ 320px）中容易把节点
        # 布局到容器边界外，造成"无数据"的视觉错觉。这里显式声明图形区域居中
        # 并适当缩小半径，避免节点飘出容器。
        'series': [series_item],
    }


def _build_parallel_binding_option(cfg: Dict[str, Any], slot_data: Optional[List[List[Any]]]) -> Dict[str, Any]:
    headers, _ = _slot_rows_xy(slot_data)
    axis_fields = _fields_from(headers, 0, len(headers) - 1 if len(headers) >= 2 else len(headers))
    group_field = _field_at(headers, len(headers) - 1, '') if len(headers) >= 2 else ''
    parallel_axis = cfg.get('parallelAxis') or [{'dim': i, 'name': name} for i, name in enumerate(axis_fields)]
    fields: Dict[str, Any] = {'axes': axis_fields}
    if group_field:
        fields['group'] = group_field
    return {
        'dataBinding': _build_data_binding('parallel', fields),
        'dataset': _dataset_placeholder(),
        'tooltip': {'trigger': 'item'},
        'legend': {'bottom': 0, 'type': 'scroll'},
        'parallelAxis': parallel_axis,
        'parallel': {'left': 60, 'right': 80, 'top': 40, 'bottom': 60,
                     'parallelAxisDefault': {'nameLocation': 'end', 'nameGap': 20}},
        'series': [{
            'type': 'parallel',
            'encode': {'parallel': axis_fields, 'tooltip': _fields_from(headers)},
            'lineStyle': {'width': 2, 'opacity': 0.55},
            'emphasis': {'lineStyle': {'width': 3, 'opacity': 0.9}},
        }],
    }


# kind → (slot_data 字段映射函数)。所有 Chart.SUPPORTED_KINDS（table 除外）必须显式覆盖。
_NATIVE_TRANSLATORS: Dict[str, Any] = {
    'pie': _build_pie_binding_option,
    'scatter': _build_scatter_binding_option,
    'radar': _build_radar_binding_option,
    'gauge': _build_gauge_binding_option,
    'heatmap': _build_heatmap_binding_option,
    'boxplot': _build_boxplot_binding_option,
    'funnel': _build_funnel_binding_option,
    'candlestick': _build_candlestick_binding_option,
    'treemap': lambda cfg, sd: _build_hierarchy_binding_option('treemap', cfg, sd),
    'sunburst': lambda cfg, sd: _build_hierarchy_binding_option('sunburst', cfg, sd),
    'sankey': _build_sankey_binding_option,
    'graph': _build_graph_binding_option,
    'parallel': _build_parallel_binding_option,
}
_EXPLICIT_NATIVE_KINDS = set(_NATIVE_TRANSLATORS) | {'line', 'bar'}
_MISSING_NATIVE_KINDS = (set(Chart.SUPPORTED_KINDS) - {'table'}) - _EXPLICIT_NATIVE_KINDS
if _MISSING_NATIVE_KINDS:
    raise RuntimeError(f'kanban_dsl_emitter 缺少图表类型支持: {sorted(_MISSING_NATIVE_KINDS)}')


def _build_native_echarts_option(kind: str,
                                 cfg: Optional[Dict[str, Any]],
                                 slot_data: Optional[List[List[Any]]] = None,
                                 chart: Optional[Chart] = None) -> str:
    """ECharts 族 widget → Chart.Option = {kind: <ECharts 原生 option>} 字符串。

    DSL 渲染契约：Chart.Option 反序列化后顶层是 { [WidgetType]: <ECharts native option> }。
    HtmlContent 不内联业务数据；渲染层必须先按 dataBinding + Widget.DatasetName 从 SqlSlots 注入/转换 rows，再 setOption。

    设计要点：
      - runner adapter 产出的 cfg **不是** ECharts 原生 option（pie/radar/gauge/boxplot 等
        只携带 chartType + 业务字段，没有 series）。本函数按 kind 派发到 translator，
        结合 slot_data 生成 data-free 的完整 option 骨架和 dataBinding 字段映射。
      - line/bar 因 runner 已自带 series，走"笛卡尔补轴"通道，与历史行为一致。
      - cfg 里的非翻译字段（如 extras 透传项）原样 merge，保证用户 chart.extras 不丢。
    """
    cfg = _strip_inline_runtime_data(cfg or {})
    if kind in ('line', 'bar'):
        native = _build_cartesian_dataset_option(kind, cfg, slot_data, chart)
    else:
        translator = _NATIVE_TRANSLATORS.get(kind)
        if translator is None:
            raise ValueError(f'DSL ECharts 图表类型未显式支持: {kind}')
        native = translator(cfg, slot_data)

    # 业务级 extras 透传：cfg 里非翻译消费过的顶层字段（chartType / 已被翻译函数消费的字段
    # 除外）merge 进 native；用户在 chart.extras 透传的 ECharts 配置不丢。
    consumed = {'chartType', 'radius', 'center', 'shape', 'indicator',
                'min', 'max', 'format', 'unit', 'visualMap',
                'sort', 'gap', 'layout', 'roam', 'label', 'series',
                'xAxis', 'yAxis', 'legend', 'tooltip', 'grid', 'smooth'}
    for k, v in cfg.items():
        if k in consumed or k in native:
            continue
        native[k] = v
    native = _ensure_cartesian_axes(kind, native)
    native = _polish_echarts_option(kind, native, slot_data)
    return json.dumps({kind: native}, ensure_ascii=False)


def _build_table_option(chart: Chart,
                        slot_data: Optional[List[List[Any]]],
                        source_columns: List[Any]) -> str:
    """table widget → Chart.Option（顶层 key=table）字符串。

    列定义按 SELECT 顺序：先 dims，后 metrics。DataType 从 source.columns 推导，
    缺失时回落到 'string'。
    """
    col_type_lookup: Dict[str, str] = {}
    for col in (source_columns or []):
        if isinstance(col, dict):
            col_type_lookup[col.get('name', '')] = col.get('type', 'string')

    # ⚠️ 字段名对齐契约（必须遵守）：
    #   - runner table adapter（_ad_table）的 slot_data 首行 header 用 d.label/m.label（中文 DisplayName）
    #   - emitter _build_dataset_for_widget 把 slot_data 首行写进 columns[].columnName
    #   - 前端 table widget 按 PhysicalFieldName 从 dataset.data 行取值
    # 所以这里 PhysicalFieldName 必须**与 label 对齐**，而非 _dim_alias / _metric_alias，
    # 否则前端取值全部 miss → 表格显示全 `-`。
    columns: List[Dict[str, Any]] = []
    for d in (chart.dims or []):
        phys_alias = _dim_alias(d)
        col_key = d.label or phys_alias  # 与 dataset.columns[].columnName 对齐
        physical_field = _expr_to_field_name(d.expr) if not d.is_time else phys_alias
        ct_lower = _column_type_lower(col_type_lookup.get(physical_field, 'string'))
        is_time = d.is_time or ct_lower in ('date', 'timestamp')
        is_num = _is_numeric_lower(ct_lower) and not is_time
        display_as = 'datetime' if is_time else ('number' if is_num else 'text')
        col: Dict[str, Any] = {
            'PhysicalFieldName': col_key,
            'DisplayName': d.label or phys_alias,
            'DisplayAs': display_as,
            'DataType': _column_type_upper(ct_lower) if not is_time else (
                'DATE' if ct_lower == 'date' else 'TIMESTAMP'
            ),
            'Visible': True,
            'Description': d.description or '',
            'Align': 'right' if display_as == 'number' else (
                'center' if display_as == 'datetime' else 'left'
            ),
        }
        if display_as == 'datetime':
            col['DatetimeFormat'] = 'yyyy-MM-dd'
        elif display_as == 'number':
            col['NumberFormat'] = '0,0.00'
        columns.append(col)

    for m in (chart.metrics or []):
        alias = _metric_alias(m)
        col_key = m.label or alias  # 与 dataset.columns[].columnName 对齐
        m_prefix = _normalize_unit(m.prefix)
        m_suffix = _normalize_unit(m.suffix)
        m_is_percent = _is_percent_suffix(m_suffix)
        # 表格数值列：NumberFormat 只承载纯数字格式；单位交由 ValuePrefix / ValueSuffix。
        columns.append({
            'PhysicalFieldName': col_key,
            'DisplayName': m.label or alias,
            'DisplayAs': 'number',
            'DataType': 'DOUBLE',
            'Visible': True,
            'Description': m.description or '',
            'Align': 'right',
            'NumberFormat': _format_to_numeral(m.format, max_decimals=2 if m_is_percent else None),
            'ValuePrefix': m_prefix,
            'ValueSuffix': m_suffix,
        })

    # 兜底：dims/metrics 都为空时按 slot_data 首行 header 派生列定义
    if not columns and slot_data and isinstance(slot_data, list) and slot_data:
        for name in (slot_data[0] or []):
            ct_lower = _column_type_lower(col_type_lookup.get(str(name), 'string'))
            is_num = _is_numeric_lower(ct_lower)
            columns.append({
                'PhysicalFieldName': str(name),
                'DisplayName': str(name),
                'DisplayAs': 'number' if is_num else 'text',
                'DataType': _column_type_upper(ct_lower),
                'Visible': True,
                'Description': '',
                'Align': 'right' if is_num else 'left',
                **({'NumberFormat': '0,0.00'} if is_num else {}),
            })

    return json.dumps({
        'table': {
            'dataBinding': _build_data_binding(
                'table', {'columns': [col.get('PhysicalFieldName') for col in columns if isinstance(col, dict)]}
            ),
            'gridSettings': {
                'itemsPerPage': 10,
                'freezeFirstNColumns': 0,
                'resizableColumns': True,
                'stripedRows': True,
                'stickyHeader': True,
                'rowHeight': 36,
                'headerHeight': 40,
                'pagination': {'show': True, 'position': 'bottom'},
            },
            'columns': columns,
            'displayRowNumber': False,
        },
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# WidgetType 映射（spec.kind → DSL WidgetType）
# ---------------------------------------------------------------------------

def _widget_type_of(record: Dict[str, Any]) -> str:
    """从 widget_record 决定 DSL WidgetType。

    record['type'] ∈ {'kpi', 'echarts', 'table', 'text'}（runner 编译产出的 data_type）
    record['kind'] 是原 spec.kind（仅 chart 类有，KPI/text 为 None）

    映射规则：
        type=kpi   → 'indexCard'（DSL 协议层名称，对应 mock 中的 KPI 卡）
        type=table → 'table'
        type=text  → 'text'
        type=echarts + kind=compare → 'line'（同环比按 line 渲染）
        type=echarts + kind=其他 → 原 kind
    """
    rt = record.get('type')
    if rt == 'kpi':
        return 'indexCard'
    if rt == 'table':
        return 'table'
    if rt == 'text':
        return 'text'
    kind = record.get('kind') or 'bar'
    if kind == 'compare':
        return 'line'
    return kind


# ---------------------------------------------------------------------------
# Layout solver（30 栅格 vertical compact）
# ---------------------------------------------------------------------------

def _solve_layout(widget_records: List[Dict[str, Any]],
                  spec: Spec) -> List[Dict[str, Any]]:
    """按 widget_records 顺序在 30 栅格里贪心铺放。

    布局规则：
    1. 文本类（page_title / page_subtitle / note）独占一整行（w=30）
    2. KPI 行内 N 张 indexCard 走"等分 30"特殊映射：每张 w=30//N，连续摆放占满整行
       - 5 张 KPI → 各 w=6（30/5=6）
       - 4 张 KPI → 各 w=7，最后一张 w=9（30 - 7*3 = 9，凑齐）
       - 3 张 KPI → 各 w=10
    3. 普通图表：w = span × step（step = 30 // grid_columns），超出右边界换行

    KPI 等分逻辑保证视觉效果与 mock 一致（5 个 KPI 严格 5 等分 30 列）。

    span/w 映射策略：
        step = GRID_COLS // grid_columns（基础步长）
        w = span × step；当 span == grid_columns 时强制 w = GRID_COLS（整行铺满，
        消除 grid_columns=4 时 step=7 导致的 28 列遗留缺口）
    """
    gc = max(1, spec.grid_columns)
    step = max(1, GRID_COLS // gc)
    layout: List[Dict[str, Any]] = []
    cursor_x, cursor_y, row_max_h = 0, 0, 0

    # 预先识别 KPI 段落起止：连续的 type==kpi 视为一个 KPI 行
    kpi_indices = [i for i, r in enumerate(widget_records) if r.get('type') == 'kpi']
    kpi_count = len(kpi_indices)
    # KPI 等分宽度：均衡分配余数到两端（视觉上避免最后一张突然变宽）
    # 例：4 张 KPI 30/4=7 余 2 → [8,7,7,8]；5 张 30/5=6 余 0 → [6,6,6,6,6]；3 张 30/3=10 余 0 → [10,10,10]
    kpi_widths: Dict[int, int] = {}
    if kpi_count > 0:
        base_w = GRID_COLS // kpi_count
        rem = GRID_COLS - base_w * kpi_count
        # 余数按对称策略分配：左右两端交替吃，向中间收敛
        extras = [0] * kpi_count
        left, right = 0, kpi_count - 1
        toggle = True
        for _step in range(rem):
            if toggle and left <= right:
                extras[left] += 1
                left += 1
            elif right >= left:
                extras[right] += 1
                right -= 1
            toggle = not toggle
        for j, idx in enumerate(kpi_indices):
            kpi_widths[idx] = base_w + extras[j]

    def _flush_row():
        nonlocal cursor_x, cursor_y, row_max_h
        if cursor_x > 0:
            cursor_y += row_max_h
            cursor_x, row_max_h = 0, 0

    for i, r in enumerate(widget_records):
        wtype = _widget_type_of(r)
        kind_for_h = r.get('kind') or wtype
        h = HEIGHT_BY_KIND.get(kind_for_h, HEIGHT_BY_KIND.get(wtype, 14))

        # page-title 有副标题(description)时需要更大高度
        if r.get('role') == 'page_title' and r.get('description') and h < 3:
            h = 3

        # 文本类（含页标题/副标题/note）独占整行
        if wtype == 'text' or r.get('role') in ('page_title', 'page_subtitle', 'note'):
            _flush_row()
            layout.append({
                'i': r['widget_id'], 'x': 0, 'y': cursor_y,
                'w': GRID_COLS, 'h': h, 'type': wtype,
            })
            cursor_y += h
            continue

        # KPI 卡片：按等分宽度连续摆放
        if r.get('type') == 'kpi':
            w = kpi_widths.get(i, step)
            if cursor_x + w > GRID_COLS:
                _flush_row()
            layout.append({
                'i': r['widget_id'], 'x': cursor_x, 'y': cursor_y,
                'w': w, 'h': h, 'type': wtype,
            })
            cursor_x += w
            row_max_h = max(row_max_h, h)
            if cursor_x >= GRID_COLS:
                _flush_row()
            continue

        # 普通图表：span × step 算基础宽，span 占满 grid_columns 时强制 GRID_COLS
        span = r.get('span') or 1
        if span >= gc:
            w = GRID_COLS
        elif span * 2 == gc:
            # 半行场景（span=2/grid_columns=4 或 span=3/grid_columns=6）：直接半分 GRID_COLS
            # 避免 grid_columns=4/step=7 时半行只有 14 列而非 15 列的整除残差
            w = GRID_COLS // 2
        else:
            w = max(step, min(GRID_COLS, span * step))
        if cursor_x + w > GRID_COLS:
            _flush_row()
        layout.append({
            'i': r['widget_id'], 'x': cursor_x, 'y': cursor_y,
            'w': w, 'h': h, 'type': wtype,
        })
        cursor_x += w
        row_max_h = max(row_max_h, h)
        if cursor_x >= GRID_COLS:
            _flush_row()

    return layout


# ---------------------------------------------------------------------------
# Dataset 构造（每个 widget 一个 1:1 dataset）
# ---------------------------------------------------------------------------

def _encode_fields(value: Any) -> List[str]:
    """把 ECharts encode 字段统一展开为非空字符串列表。"""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if isinstance(v, (str, int)) and str(v)]
    if isinstance(value, (str, int)) and str(value):
        return [str(value)]
    return []


def _align_meta_fields_to_headers(meta_list: List[Dict[str, Any]],
                                  header_fields: List[str],
                                  start_index: int = 0,
                                  repeat_last: bool = False) -> None:
    """让 metrics/dimensions[].field 优先对齐 dataset.columns[].columnName。

    前端组件编辑器通常按 field 回查 Dataset columns；field 与真实 header 不一致时，
    图表仍可能可渲染，但编辑面板会出现字段回显为空或修改后取不到列的问题。
    """
    last_field = ''
    for idx, item in enumerate(meta_list):
        header_idx = start_index + idx
        if header_idx < len(header_fields):
            field_name = str(header_fields[header_idx] or '')
            if field_name:
                item['field'] = field_name
                last_field = field_name
        elif repeat_last and last_field:
            item['field'] = last_field


def _align_dataset_meta_to_headers(record: Dict[str, Any],
                                   dims_list: List[Dict[str, Any]],
                                   metrics_list: List[Dict[str, Any]],
                                   header_fields: List[str]) -> None:
    """按 runner slot_data 语义对齐 Dataset 元信息字段，支撑前端组件编辑回显。"""
    if not header_fields:
        return
    rtype = record.get('type')
    kind = record.get('kind') or ''
    spec_obj = record.get('spec_obj')

    if rtype == 'kpi':
        _align_meta_fields_to_headers(metrics_list, header_fields, 0)
        return

    if isinstance(spec_obj, Compare):
        _align_meta_fields_to_headers(dims_list, header_fields, 0)
        _align_meta_fields_to_headers(metrics_list, header_fields, 1)
        return

    if kind == 'scatter':
        if dims_list and len(header_fields) >= 1:
            dims_list[0]['field'] = header_fields[0]
        if metrics_list and len(header_fields) >= 2:
            metrics_list[0]['field'] = header_fields[1]
        if len(dims_list) >= 2 and len(header_fields) >= 3:
            dims_list[1]['field'] = header_fields[2]
        return

    if kind == 'gauge':
        if metrics_list:
            metrics_list[0]['field'] = header_fields[1] if len(header_fields) >= 2 else header_fields[0]
        return

    if kind == 'funnel':
        # funnel 将多个 stage metric 纵向 UNION 成 [stage_name, value]，所有阶段共用 value 列。
        if dims_list and header_fields:
            dims_list[0]['field'] = header_fields[0]
        value_field = header_fields[1] if len(header_fields) >= 2 else header_fields[-1]
        for item in metrics_list:
            item['field'] = value_field
        return

    if kind == 'candlestick':
        _align_meta_fields_to_headers(dims_list, header_fields, 0)
        role_to_field = {'open': 'open', 'close': 'close', 'low': 'low', 'high': 'high'}
        field_candidates = {
            'open': ['open', 'o'],
            'close': ['close', 'c'],
            'low': ['low', 'l'],
            'high': ['high', 'h'],
        }
        role_by_formula: Dict[str, str] = {}
        if isinstance(spec_obj, Chart):
            for metric in (spec_obj.metrics or []):
                if metric.role in role_to_field:
                    role_by_formula[metric.expr] = metric.role
        for idx, item in enumerate(metrics_list):
            role = role_by_formula.get(str(item.get('formula') or ''))
            if role:
                item['field'] = _pick_existing_field(header_fields, field_candidates[role], role_to_field[role]) or role_to_field[role]
            elif idx + 1 < len(header_fields):
                item['field'] = header_fields[idx + 1]
        return

    if kind == 'boxplot':
        _align_meta_fields_to_headers(dims_list, header_fields, 0)
        if metrics_list:
            # boxplot 输出五数概括列；保留原始 metric 公式，field 指向第一个统计列以保证可回查。
            metrics_list[0]['field'] = header_fields[1] if len(header_fields) >= 2 else header_fields[0]
        return

    if kind in ('treemap', 'sunburst'):
        # runner 层级图输出最多 [name, value, parent]；高层路径已折叠到 parent 聚合行。
        if len(dims_list) > 2:
            del dims_list[2:]
        if dims_list:
            dims_list[0]['field'] = header_fields[0]
        if len(dims_list) >= 2:
            dims_list[1]['field'] = header_fields[2] if len(header_fields) >= 3 else header_fields[0]
        if metrics_list:
            metrics_list[0]['field'] = header_fields[1] if len(header_fields) >= 2 else header_fields[0]
        return

    # 通用图：line/bar/pie/radar/heatmap/sankey/graph/parallel/table 均按 header 顺序消费。
    _align_meta_fields_to_headers(dims_list, header_fields, 0)
    metric_start = len(dims_list)
    _align_meta_fields_to_headers(metrics_list, header_fields, metric_start)


def _validation_issue(code: str,
                      message: str,
                      path: str,
                      *,
                      severity: str = 'error',
                      widget_id: str = '',
                      dataset_key: str = '',
                      chart_kind: str = '',
                      actual: Any = None,
                      expected: Any = None,
                      auto_fixable: bool = False,
                      repair_hint: str = '') -> Dict[str, Any]:
    """生成机器可读校验问题，便于 runner/LLM 快速自动返工。"""
    issue: Dict[str, Any] = {
        'code': code,
        'severity': severity,
        'message': message,
        'path': path,
        'widgetId': widget_id,
        'datasetKey': dataset_key,
        'chartKind': chart_kind,
        'autoFixable': auto_fixable,
        'repairHint': repair_hint,
    }
    if actual is not None:
        issue['actual'] = actual
    if expected is not None:
        issue['expected'] = expected
    return issue


def _safe_option_root(option_text: Any) -> Tuple[Optional[Dict[str, Any]], str]:
    try:
        option_root = json.loads(option_text) if isinstance(option_text, str) else option_text
    except json.JSONDecodeError as e:
        return None, str(e)
    if not isinstance(option_root, dict):
        return None, 'Chart.Option 顶层不是对象'
    return option_root, ''


def _dataset_columns(dataset: Dict[str, Any]) -> List[str]:
    return [str(c.get('columnName') or '') for c in (dataset.get('columns') or []) if isinstance(c, dict)]


def _first_existing_field(columns: List[str], *preferred: Any) -> str:
    column_set = set(columns)
    for value in preferred:
        if isinstance(value, list):
            for item in value:
                item_s = str(item or '')
                if item_s in column_set:
                    return item_s
        else:
            value_s = str(value or '')
            if value_s in column_set:
                return value_s
    return columns[0] if columns else ''


def _remap_binding_fields(value: Any, columns: List[str], repairs: List[Dict[str, Any]], path: str) -> Any:
    """把 dataBinding.fields 中不存在的字段稳定映射到 Dataset.columns，保证动态刷新可取数。"""
    if '.aliases' in path:
        return value
    column_set = set(columns)
    fallback = columns[0] if columns else ''
    if isinstance(value, str):
        if not value or value.isdigit() or value in column_set:
            return value
        repairs.append({'code': 'DSL_AUTOFIX_BINDING_FIELD', 'path': path, 'from': value, 'to': fallback})
        return fallback
    if isinstance(value, list):
        return [_remap_binding_fields(item, columns, repairs, f'{path}[{idx}]') for idx, item in enumerate(value)]
    if isinstance(value, dict):
        return {k: _remap_binding_fields(v, columns, repairs, f'{path}.{k}') for k, v in value.items()}
    return value


def _remap_encode_value(value: Any, columns: List[str], repairs: List[Dict[str, Any]], path: str) -> Any:
    column_set = set(columns)
    fallback = columns[0] if columns else ''
    if isinstance(value, str):
        if not value or value.isdigit() or value in column_set:
            return value
        repairs.append({'code': 'DSL_AUTOFIX_ENCODE_FIELD', 'path': path, 'from': value, 'to': fallback})
        return fallback
    if isinstance(value, list):
        return [_remap_encode_value(item, columns, repairs, f'{path}[{idx}]') for idx, item in enumerate(value)]
    return value


def _series_data_binding_fields(series_binding: Any) -> List[str]:
    """series 级 dataBinding 只提取字段名，跳过 categoryValue 等字面筛选值。"""
    out: List[str] = []
    if not isinstance(series_binding, dict):
        return out
    for key, value in series_binding.items():
        if key in {'categoryValue', 'nameValue', 'filterValue', 'value'}:
            continue
        out.extend(_collect_binding_fields(value))
    return out


def _normalize_dataset_contract(datasets: List[Dict[str, Any]], repairs: List[Dict[str, Any]]) -> None:
    """用 data header 反向规范 columns/metrics/dimensions，保障组件编辑和动态刷新字段一致。"""
    seen_keys = set()
    for index, dataset in enumerate(datasets):
        if not isinstance(dataset, dict):
            continue
        key = str(dataset.get('key') or '')
        if not key:
            key = f'dataset_{index}'
            dataset['key'] = key
            repairs.append({'code': 'DSL_AUTOFIX_DATASET_KEY', 'path': f'Datasets[{index}].key', 'to': key})
        if key in seen_keys:
            next_key = f'{key}_{index}'
            dataset['key'] = next_key
            repairs.append({'code': 'DSL_AUTOFIX_DATASET_DUP_KEY', 'path': f'Datasets[{index}].key', 'from': key, 'to': next_key})
            key = next_key
        seen_keys.add(key)

        data_text = dataset.get('data')
        header: List[str] = []
        if data_text is not None:
            try:
                data_obj = json.loads(data_text) if isinstance(data_text, str) else data_text
                if isinstance(data_obj, list) and data_obj:
                    header = [str(h) for h in (data_obj[0] or [])]
            except json.JSONDecodeError:
                header = []

        columns = dataset.get('columns')
        if not isinstance(columns, list):
            dataset['columns'] = []
            columns = dataset['columns']
            repairs.append({'code': 'DSL_AUTOFIX_COLUMNS_TYPE', 'path': f'Datasets[{index}].columns', 'to': []})
        names = _dataset_columns(dataset)
        if header and header != names:
            type_lookup = {
                str(c.get('columnName') or ''): str(c.get('columnType') or 'string')
                for c in columns if isinstance(c, dict)
            }
            semantic_string_fields = {
                'name', 'category', 'cat', 'source', 'target', 'parent',
                'stage', 'stage_name', 'date', 'time', 'period', 'group',
            }
            dataset['columns'] = [
                {
                    'columnName': name,
                    'columnType': type_lookup.get(
                        name,
                        'string' if idx == 0 or name in semantic_string_fields else 'double',
                    ),
                }
                for idx, name in enumerate(header) if name
            ]
            names = _dataset_columns(dataset)
            repairs.append({'code': 'DSL_AUTOFIX_COLUMNS_HEADER', 'path': f'Datasets[{index}].columns', 'to': names})

        column_set = set(names)
        for meta_kind in ('metrics', 'dimensions'):
            meta_items = dataset.get(meta_kind)
            if not isinstance(meta_items, list):
                dataset[meta_kind] = []
                repairs.append({'code': 'DSL_AUTOFIX_META_TYPE', 'path': f'Datasets[{index}].{meta_kind}', 'to': []})
                continue
            for mi, item in enumerate(meta_items):
                if not isinstance(item, dict):
                    continue
                field = str(item.get('field') or '')
                if field and field not in column_set and names:
                    replacement = names[min(mi, len(names) - 1)]
                    item['field'] = replacement
                    repairs.append({
                        'code': 'DSL_AUTOFIX_META_FIELD',
                        'path': f'Datasets[{index}].{meta_kind}[{mi}].field',
                        'from': field,
                        'to': replacement,
                    })


def _autofix_render_contract(dsl: Dict[str, Any], datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """确定性修复 DSL/Dataset 闭环问题，避免 LLM 为可推断字段返工。"""
    repairs: List[Dict[str, Any]] = []
    _normalize_dataset_contract(datasets, repairs)
    dataset_map = {str(ds.get('key') or ''): ds for ds in datasets if isinstance(ds, dict)}

    for page_index, page in enumerate(dsl.get('Pages') or []):
        if not isinstance(page, dict):
            continue
        widgets = page.get('Widgets') or []
        widget_ids = [w.get('WidgetId') for w in widgets if isinstance(w, dict)]
        layout = page.get('PageLayout')
        if not isinstance(layout, list):
            page['PageLayout'] = []
            layout = page['PageLayout']
            repairs.append({'code': 'DSL_AUTOFIX_LAYOUT_TYPE', 'path': f'Pages[{page_index}].PageLayout', 'to': []})
        layout_ids = {item.get('i') for item in layout if isinstance(item, dict)}
        for wid in widget_ids:
            if wid not in layout_ids:
                layout.append({'i': wid, 'x': 0, 'y': 0, 'w': GRID_COLS, 'h': HEIGHT_BY_KIND.get('text', 2), 'type': 'text'})
                repairs.append({'code': 'DSL_AUTOFIX_LAYOUT_MISSING', 'path': f'Pages[{page_index}].PageLayout', 'widgetId': wid})

        for widget in widgets:
            if not isinstance(widget, dict):
                continue
            wid = str(widget.get('WidgetId') or '')
            wtype = str(widget.get('WidgetType') or '')
            if wtype == 'text':
                continue
            ds_name = str(widget.get('DatasetName') or '')
            if not ds_name and wid in dataset_map:
                widget['DatasetName'] = wid
                ds_name = wid
                repairs.append({'code': 'DSL_AUTOFIX_WIDGET_DATASET', 'path': f'Widget {wid}.DatasetName', 'to': wid})
            dataset = dataset_map.get(ds_name)
            if not dataset:
                continue
            columns = _dataset_columns(dataset)
            chart = widget.get('Chart') if isinstance(widget.get('Chart'), dict) else None
            if chart is None:
                continue
            option_root, err = _safe_option_root(chart.get('Option'))
            if err or not option_root or wtype not in option_root:
                continue
            option = option_root.get(wtype)
            if not isinstance(option, dict):
                continue

            stripped = _strip_inline_runtime_data(option)
            if stripped != option:
                option_root[wtype] = stripped
                option = stripped
                repairs.append({'code': 'DSL_AUTOFIX_STRIP_RUNTIME_DATA', 'path': f'Widget {wid}.{wtype}.Chart.Option'})

            binding = option.get('dataBinding')
            if not isinstance(binding, dict):
                transform = wtype if wtype != 'indexCard' else 'indexCard'
                option['dataBinding'] = _build_data_binding(transform, {})
                binding = option['dataBinding']
                repairs.append({'code': 'DSL_AUTOFIX_DATABINDING_MISSING', 'path': f'Widget {wid}.{wtype}.dataBinding'})
            if binding.get('version') != 1:
                repairs.append({'code': 'DSL_AUTOFIX_DATABINDING_VERSION', 'path': f'Widget {wid}.{wtype}.dataBinding.version', 'from': binding.get('version'), 'to': 1})
                binding['version'] = 1
            if binding.get('source') != 'sqlSlots':
                repairs.append({'code': 'DSL_AUTOFIX_DATABINDING_SOURCE', 'path': f'Widget {wid}.{wtype}.dataBinding.source', 'from': binding.get('source'), 'to': 'sqlSlots'})
                binding['source'] = 'sqlSlots'
            if binding.get('datasetKeyRef') != 'Widget.DatasetName':
                repairs.append({'code': 'DSL_AUTOFIX_DATABINDING_DATASET_REF', 'path': f'Widget {wid}.{wtype}.dataBinding.datasetKeyRef', 'from': binding.get('datasetKeyRef'), 'to': 'Widget.DatasetName'})
                binding['datasetKeyRef'] = 'Widget.DatasetName'
            if binding.get('refreshApi') != 'batchQueryAiKanBanData':
                repairs.append({'code': 'DSL_AUTOFIX_DATABINDING_REFRESH_API', 'path': f'Widget {wid}.{wtype}.dataBinding.refreshApi', 'from': binding.get('refreshApi'), 'to': 'batchQueryAiKanBanData'})
                binding['refreshApi'] = 'batchQueryAiKanBanData'
            if binding.get('slotKeyRef') != 'Widget.DatasetName':
                repairs.append({'code': 'DSL_AUTOFIX_DATABINDING_SLOT_REF', 'path': f'Widget {wid}.{wtype}.dataBinding.slotKeyRef', 'from': binding.get('slotKeyRef'), 'to': 'Widget.DatasetName'})
                binding['slotKeyRef'] = 'Widget.DatasetName'
            transform = str(binding.get('transform') or (wtype if wtype != 'indexCard' else 'indexCard'))
            if not binding.get('transform'):
                binding['transform'] = transform
                repairs.append({'code': 'DSL_AUTOFIX_DATABINDING_TRANSFORM', 'path': f'Widget {wid}.{wtype}.dataBinding.transform', 'to': transform})
            expected_render_mode = 'datasetEncode' if transform in _DATASET_ENCODE_TRANSFORMS else 'runtimeTransform'
            if binding.get('renderMode') != expected_render_mode:
                repairs.append({'code': 'DSL_AUTOFIX_DATABINDING_RENDER_MODE', 'path': f'Widget {wid}.{wtype}.dataBinding.renderMode', 'from': binding.get('renderMode'), 'to': expected_render_mode})
                binding['renderMode'] = expected_render_mode
            if not isinstance(binding.get('fields'), dict):
                binding['fields'] = {}
                repairs.append({'code': 'DSL_AUTOFIX_DATABINDING_FIELDS', 'path': f'Widget {wid}.{wtype}.dataBinding.fields', 'to': {}})
            binding['fields'] = _remap_binding_fields(binding.get('fields') or {}, columns, repairs, f'Widget {wid}.{wtype}.dataBinding.fields')

            if wtype == 'indexCard':
                value_field = str(option.get('valueField') or '')
                fixed_value = _first_existing_field(columns, value_field, (binding.get('fields') or {}).get('value'))
                if fixed_value and value_field != fixed_value:
                    option['valueField'] = fixed_value
                    binding['fields']['value'] = fixed_value
                    repairs.append({'code': 'DSL_AUTOFIX_INDEXCARD_VALUE_FIELD', 'path': f'Widget {wid}.indexCard.valueField', 'from': value_field, 'to': fixed_value})
            elif wtype == 'table':
                table_columns = option.get('columns')
                if isinstance(table_columns, list):
                    for ci, col in enumerate(table_columns):
                        if not isinstance(col, dict):
                            continue
                        pf = str(col.get('PhysicalFieldName') or '')
                        fixed_pf = _first_existing_field(columns, pf)
                        if fixed_pf and pf != fixed_pf:
                            col['PhysicalFieldName'] = fixed_pf
                            repairs.append({'code': 'DSL_AUTOFIX_TABLE_FIELD', 'path': f'Widget {wid}.table.columns[{ci}].PhysicalFieldName', 'from': pf, 'to': fixed_pf})
            else:
                series = option.get('series')
                if isinstance(series, list):
                    y_axis = option.get('yAxis')
                    y_axis_count = len(y_axis) if isinstance(y_axis, list) else (1 if isinstance(y_axis, dict) else 0)
                    for si, item in enumerate(series):
                        if not isinstance(item, dict):
                            continue
                        if len(series) > 1 and not item.get('name') and wtype not in ('pie', 'gauge'):
                            preferred_name = columns[si + 1] if si + 1 < len(columns) else (columns[0] if columns else '')
                            item['name'] = preferred_name or f'series_{si + 1}'
                            repairs.append({'code': 'DSL_AUTOFIX_SERIES_NAME', 'path': f'Widget {wid}.{wtype}.series[{si}].name', 'to': item['name']})
                        encode = item.get('encode')
                        if not isinstance(encode, dict) and wtype in _CARTESIAN_KINDS and len(columns) >= 2:
                            encode = {'x': columns[0], 'y': columns[min(si + 1, len(columns) - 1)]}
                            item['encode'] = encode
                            repairs.append({'code': 'DSL_AUTOFIX_SERIES_ENCODE', 'path': f'Widget {wid}.{wtype}.series[{si}].encode', 'to': encode})
                        if isinstance(encode, dict):
                            for role, encoded in list(encode.items()):
                                encode[role] = _remap_encode_value(encoded, columns, repairs, f'Widget {wid}.{wtype}.series[{si}].encode.{role}')
                        if isinstance(item.get('fieldAliases'), dict):
                            # fieldAliases 是运行时候选列名，不要求全部存在于当前默认快照 columns。
                            pass
                        y_idx = item.get('yAxisIndex')
                        if isinstance(y_idx, int) and y_axis_count > 0 and (y_idx < 0 or y_idx >= y_axis_count):
                            item['yAxisIndex'] = min(max(y_idx, 0), y_axis_count - 1)
                            repairs.append({'code': 'DSL_AUTOFIX_Y_AXIS_INDEX', 'path': f'Widget {wid}.{wtype}.series[{si}].yAxisIndex', 'from': y_idx, 'to': item['yAxisIndex']})
            chart['Option'] = json.dumps(option_root, ensure_ascii=False)
    return repairs


def _validate_render_contract_report(dsl: Dict[str, Any], datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """入库前全量校验 Widget → Dataset → Chart.Option 是否形成可渲染/可刷新闭环。"""
    issues: List[Dict[str, Any]] = []
    dataset_map: Dict[str, Dict[str, Any]] = {}
    for index, dataset in enumerate(datasets):
        path = f'Datasets[{index}]'
        if not isinstance(dataset, dict):
            issues.append(_validation_issue('DSL_DATASET_NOT_OBJECT', f'{path} 不是对象', path))
            continue
        key = str(dataset.get('key') or '')
        if not key:
            issues.append(_validation_issue('DSL_DATASET_KEY_EMPTY', f'{path} 缺少 key', f'{path}.key', auto_fixable=True))
        elif key in dataset_map:
            issues.append(_validation_issue('DSL_DATASET_KEY_DUPLICATED', f'Dataset key 重复: {key}', f'{path}.key', dataset_key=key, actual=key, auto_fixable=True))
        columns = dataset.get('columns') or []
        if not isinstance(columns, list):
            issues.append(_validation_issue('DSL_DATASET_COLUMNS_NOT_ARRAY', f'Dataset {key}.columns 不是数组', f'{path}.columns', dataset_key=key, auto_fixable=True))
            continue
        names = [str(c.get('columnName') or '') for c in columns if isinstance(c, dict)]
        if not names:
            issues.append(_validation_issue('DSL_DATASET_COLUMNS_EMPTY', f'Dataset {key}.columns 为空，无法建立组件字段映射', f'{path}.columns', dataset_key=key, repair_hint='请检查 slot_data 首行 header 或 SQL SELECT 别名'))
        if len(names) != len(columns) or any(not n for n in names):
            issues.append(_validation_issue('DSL_DATASET_COLUMN_NAME_EMPTY', f'Dataset {key}.columns 存在空 columnName', f'{path}.columns', dataset_key=key, actual=names))
        if len(set(names)) != len(names):
            issues.append(_validation_issue('DSL_DATASET_COLUMN_DUPLICATED', f'Dataset {key}.columns 存在重复 columnName: {names}', f'{path}.columns', dataset_key=key, actual=names))
        column_set = set(names)
        for meta_kind in ('metrics', 'dimensions'):
            meta_items = dataset.get(meta_kind) or []
            if not isinstance(meta_items, list):
                issues.append(_validation_issue('DSL_DATASET_META_NOT_ARRAY', f'Dataset {key}.{meta_kind} 不是数组', f'{path}.{meta_kind}', dataset_key=key, auto_fixable=True))
                continue
            for mi, item in enumerate(meta_items):
                meta_path = f'{path}.{meta_kind}[{mi}]'
                if not isinstance(item, dict):
                    issues.append(_validation_issue('DSL_DATASET_META_NOT_OBJECT', f'{meta_path} 不是对象', meta_path, dataset_key=key))
                    continue
                field = str(item.get('field') or '')
                if field and field not in column_set:
                    issues.append(_validation_issue('DSL_DATASET_META_FIELD_NOT_FOUND', f'Dataset {key}.{meta_kind}[{mi}].field={field!r} 不在 columns={names}', f'{meta_path}.field', dataset_key=key, actual=field, expected=names, auto_fixable=True))
        data_text = dataset.get('data')
        if data_text is not None:
            try:
                data_obj = json.loads(data_text) if isinstance(data_text, str) else data_text
            except json.JSONDecodeError as e:
                issues.append(_validation_issue('DSL_DATASET_DATA_INVALID_JSON', f'Dataset {key}.data 不是合法 JSON: {e}', f'{path}.data', dataset_key=key, actual=str(e)))
                data_obj = None
            if data_obj is not None:
                if not isinstance(data_obj, list) or not data_obj:
                    issues.append(_validation_issue('DSL_DATASET_DATA_NOT_TABLE', f'Dataset {key}.data 不是带 header 的二维数组', f'{path}.data', dataset_key=key))
                else:
                    header = [str(h) for h in (data_obj[0] or [])]
                    if header != names:
                        issues.append(_validation_issue('DSL_DATASET_HEADER_MISMATCH', f'Dataset {key}.data header 与 columns 不一致: header={header}, columns={names}', f'{path}.data', dataset_key=key, actual=header, expected=names, auto_fixable=True))
        if not str(dataset.get('sql') or '').strip():
            if data_text is None:
                issues.append(_validation_issue('DSL_DATASET_NO_DATA_OR_SQL', f'Dataset {key} 同时缺少 data 和 sql，无法渲染或刷新', path, dataset_key=key, repair_hint='Dataset.data 可剥离，但 sql 必须保留以支持动态刷新'))
            else:
                issues.append(_validation_issue('DSL_DATASET_SQL_EMPTY', f'Dataset {key} 缺少 sql；默认 data 仅为快照且可能被剥离，无法组件级动态刷新', f'{path}.sql', dataset_key=key, repair_hint='请检查 runner 生成的 sql_map/slot_meta_map，确保每个非文本 widget 都有可执行 sql'))
        if key:
            dataset_map[key] = dataset

    pages = dsl.get('Pages') or []
    if not isinstance(pages, list) or not pages:
        issues.append(_validation_issue('DSL_PAGES_EMPTY', 'DSL 缺少 Pages', 'Pages'))
    for page_index, page in enumerate(pages if isinstance(pages, list) else []):
        if not isinstance(page, dict):
            issues.append(_validation_issue('DSL_PAGE_NOT_OBJECT', f'Pages[{page_index}] 不是对象', f'Pages[{page_index}]'))
            continue
        widgets = page.get('Widgets') or []
        widget_ids = {w.get('WidgetId') for w in widgets if isinstance(w, dict)}
        layout_ids = {item.get('i') for item in (page.get('PageLayout') or []) if isinstance(item, dict)}
        missing_layout = widget_ids - layout_ids
        extra_layout = layout_ids - widget_ids
        if missing_layout:
            issues.append(_validation_issue('DSL_LAYOUT_MISSING_WIDGET', f'Pages[{page_index}] Widgets 缺少布局: {sorted(missing_layout)}', f'Pages[{page_index}].PageLayout', actual=sorted(missing_layout), auto_fixable=True))
        if extra_layout:
            issues.append(_validation_issue('DSL_LAYOUT_EXTRA_WIDGET', f'Pages[{page_index}] PageLayout 引用了不存在 widget: {sorted(extra_layout)}', f'Pages[{page_index}].PageLayout', actual=sorted(extra_layout)))

        for widget_index, widget in enumerate(widgets):
            if not isinstance(widget, dict):
                issues.append(_validation_issue('DSL_WIDGET_NOT_OBJECT', f'Pages[{page_index}].Widgets[{widget_index}] 不是对象', f'Pages[{page_index}].Widgets[{widget_index}]'))
                continue
            wid = str(widget.get('WidgetId') or '')
            wtype = str(widget.get('WidgetType') or '')
            if wtype == 'text':
                continue
            ds_name = str(widget.get('DatasetName') or '')
            if not ds_name:
                issues.append(_validation_issue('DSL_WIDGET_DATASET_EMPTY', f'Widget {wid} 缺少 DatasetName', f'Pages[{page_index}].Widgets[{widget_index}].DatasetName', widget_id=wid, chart_kind=wtype, auto_fixable=True))
                continue
            dataset = dataset_map.get(ds_name)
            if dataset is None:
                issues.append(_validation_issue('DSL_WIDGET_DATASET_NOT_FOUND', f'Widget {wid} 引用不存在的 DatasetName={ds_name}', f'Pages[{page_index}].Widgets[{widget_index}].DatasetName', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, expected=sorted(dataset_map.keys())))
                continue
            columns = _dataset_columns(dataset)
            chart = widget.get('Chart') or {}
            option_text = chart.get('Option') if isinstance(chart, dict) else None
            if not option_text:
                issues.append(_validation_issue('DSL_WIDGET_OPTION_EMPTY', f'Widget {wid} 缺少 Chart.Option', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option', widget_id=wid, dataset_key=ds_name, chart_kind=wtype))
                continue
            option_root, option_error = _safe_option_root(option_text)
            if option_error or not option_root:
                issues.append(_validation_issue('DSL_WIDGET_OPTION_INVALID_JSON', f'Widget {wid}.Chart.Option 不是合法 JSON: {option_error}', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=option_error))
                continue
            if wtype not in option_root:
                issues.append(_validation_issue('DSL_WIDGET_OPTION_ROOT_MISSING', f'Widget {wid}.Chart.Option 顶层缺少 {wtype}', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, expected=wtype))
                continue
            option = option_root.get(wtype) or {}
            if not isinstance(option, dict):
                issues.append(_validation_issue('DSL_WIDGET_OPTION_NOT_OBJECT', f'Widget {wid}.{wtype} option 不是对象', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}', widget_id=wid, dataset_key=ds_name, chart_kind=wtype))
                continue

            inline_paths = _inline_runtime_data_paths(option)
            if inline_paths:
                issues.append(_validation_issue('DSL_WIDGET_INLINE_RUNTIME_DATA', f'Widget {wid}.{wtype}.Chart.Option 内联了运行态数据 {inline_paths[:5]}；HtmlContent 只能保存字段映射，数据必须来自 SqlSlots', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=inline_paths[:20], auto_fixable=True))
            binding = option.get('dataBinding')
            if not isinstance(binding, dict):
                issues.append(_validation_issue('DSL_WIDGET_DATABINDING_MISSING', f'Widget {wid}.{wtype} 缺少 dataBinding，无法通过 DatasetName 动态取数', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.dataBinding', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, auto_fixable=True))
                continue
            if binding.get('version') != 1:
                issues.append(_validation_issue('DSL_WIDGET_DATABINDING_VERSION_INVALID', f'Widget {wid}.{wtype}.dataBinding.version 必须为 1', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.dataBinding.version', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=binding.get('version'), expected=1, auto_fixable=True))
            if binding.get('source') != 'sqlSlots':
                issues.append(_validation_issue('DSL_WIDGET_DATABINDING_SOURCE_INVALID', f'Widget {wid}.{wtype}.dataBinding.source 必须为 sqlSlots', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.dataBinding.source', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=binding.get('source'), expected='sqlSlots', auto_fixable=True))
            if binding.get('datasetKeyRef') != 'Widget.DatasetName':
                issues.append(_validation_issue('DSL_WIDGET_DATABINDING_DATASET_REF_INVALID', f'Widget {wid}.{wtype}.dataBinding.datasetKeyRef 必须为 Widget.DatasetName', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.dataBinding.datasetKeyRef', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=binding.get('datasetKeyRef'), expected='Widget.DatasetName', auto_fixable=True))
            if binding.get('refreshApi') != 'batchQueryAiKanBanData':
                issues.append(_validation_issue('DSL_WIDGET_DATABINDING_REFRESH_API_INVALID', f'Widget {wid}.{wtype}.dataBinding.refreshApi 必须为 batchQueryAiKanBanData', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.dataBinding.refreshApi', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=binding.get('refreshApi'), expected='batchQueryAiKanBanData', auto_fixable=True))
            if binding.get('slotKeyRef') != 'Widget.DatasetName':
                issues.append(_validation_issue('DSL_WIDGET_DATABINDING_SLOT_REF_INVALID', f'Widget {wid}.{wtype}.dataBinding.slotKeyRef 必须为 Widget.DatasetName', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.dataBinding.slotKeyRef', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=binding.get('slotKeyRef'), expected='Widget.DatasetName', auto_fixable=True))
            transform = str(binding.get('transform') or '')
            if not transform:
                issues.append(_validation_issue('DSL_WIDGET_DATABINDING_TRANSFORM_EMPTY', f'Widget {wid}.{wtype}.dataBinding.transform 不能为空', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.dataBinding.transform', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, auto_fixable=True))
            render_mode = binding.get('renderMode')
            expected_render_mode = 'datasetEncode' if transform in _DATASET_ENCODE_TRANSFORMS else 'runtimeTransform'
            if transform and render_mode != expected_render_mode:
                issues.append(_validation_issue('DSL_WIDGET_DATABINDING_RENDER_MODE_INVALID', f'Widget {wid}.{wtype}.dataBinding.renderMode={render_mode!r} 与 transform={transform!r} 不匹配，应为 {expected_render_mode!r}', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.dataBinding.renderMode', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=render_mode, expected=expected_render_mode, auto_fixable=True))
            fields = binding.get('fields') or {}
            for field in _collect_binding_fields(fields):
                if not field.isdigit() and field not in columns:
                    issues.append(_validation_issue('DSL_WIDGET_BINDING_FIELD_NOT_FOUND', f'Widget {wid}.{wtype}.dataBinding.fields 包含不存在字段 {field!r}，columns={columns}', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.dataBinding.fields', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=field, expected=columns, auto_fixable=True))

            if wtype == 'indexCard':
                value_field = str(option.get('valueField') or '')
                if value_field not in columns:
                    issues.append(_validation_issue('DSL_INDEXCARD_VALUE_FIELD_NOT_FOUND', f'Widget {wid}.indexCard.valueField={value_field!r} 不在 columns={columns}', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.indexCard.valueField', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=value_field, expected=columns, auto_fixable=True))
                continue

            if wtype == 'table':
                table_columns = option.get('columns') or []
                for ci, col in enumerate(table_columns):
                    if isinstance(col, dict):
                        pf = str(col.get('PhysicalFieldName') or '')
                        if pf and pf not in columns:
                            issues.append(_validation_issue('DSL_TABLE_FIELD_NOT_FOUND', f'Widget {wid}.table.columns[{ci}].PhysicalFieldName={pf!r} 不在 columns={columns}', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.table.columns[{ci}].PhysicalFieldName', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=pf, expected=columns, auto_fixable=True))
                continue

            series = option.get('series')
            if not isinstance(series, list):
                issues.append(_validation_issue('DSL_SERIES_NOT_ARRAY', f'Widget {wid}.{wtype}.series 缺失或不是数组', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.series', widget_id=wid, dataset_key=ds_name, chart_kind=wtype))
                continue
            if not series:
                continue
            y_axis = option.get('yAxis')
            y_axis_count = len(y_axis) if isinstance(y_axis, list) else (1 if isinstance(y_axis, dict) else 0)
            for si, item in enumerate(series):
                if not isinstance(item, dict):
                    issues.append(_validation_issue('DSL_SERIES_ITEM_NOT_OBJECT', f'Widget {wid}.{wtype}.series[{si}] 不是对象', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.series[{si}]', widget_id=wid, dataset_key=ds_name, chart_kind=wtype))
                    continue
                if len(series) > 1 and not item.get('name') and wtype not in ('pie', 'gauge'):
                    issues.append(_validation_issue('DSL_SERIES_NAME_EMPTY', f'Widget {wid}.{wtype}.series[{si}] 缺少 name', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.series[{si}].name', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, auto_fixable=True))
                encode = item.get('encode') if isinstance(item.get('encode'), dict) else None
                has_encode = bool(encode)
                if not has_encode and wtype in _CARTESIAN_KINDS:
                    issues.append(_validation_issue('DSL_SERIES_ENCODE_MISSING', f'Widget {wid}.{wtype}.series[{si}] 缺少 encode', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.series[{si}].encode', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, auto_fixable=True))
                if encode:
                    for role, encoded in encode.items():
                        for field in _encode_fields(encoded):
                            if not field.isdigit() and field not in columns:
                                issues.append(_validation_issue('DSL_SERIES_ENCODE_FIELD_NOT_FOUND', f'Widget {wid}.{wtype}.series[{si}].encode.{role}={field!r} 不在 columns={columns}', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.series[{si}].encode.{role}', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=field, expected=columns, auto_fixable=True))
                for field in _series_data_binding_fields(item.get('dataBinding')):
                    if not field.isdigit() and field not in columns:
                        issues.append(_validation_issue('DSL_SERIES_DATABINDING_FIELD_NOT_FOUND', f'Widget {wid}.{wtype}.series[{si}].dataBinding 包含不存在字段 {field!r}，columns={columns}', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.series[{si}].dataBinding', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=field, expected=columns, auto_fixable=True))
                y_idx = item.get('yAxisIndex')
                if y_idx is not None:
                    if not isinstance(y_idx, int) or y_idx < 0 or y_idx >= y_axis_count:
                        issues.append(_validation_issue('DSL_SERIES_Y_AXIS_INDEX_INVALID', f'Widget {wid}.{wtype}.series[{si}].yAxisIndex={y_idx} 越界 yAxis={y_axis_count}', f'Pages[{page_index}].Widgets[{widget_index}].Chart.Option.{wtype}.series[{si}].yAxisIndex', widget_id=wid, dataset_key=ds_name, chart_kind=wtype, actual=y_idx, expected=f'0..{max(y_axis_count - 1, 0)}', auto_fixable=isinstance(y_idx, int) and y_axis_count > 0))
    return {
        'status': 'success' if not issues else 'failed',
        'recoverable': bool(issues) and all(bool(issue.get('autoFixable')) for issue in issues),
        'errorCount': len([issue for issue in issues if issue.get('severity') == 'error']),
        'issues': issues,
    }


def _validate_render_contract(dsl: Dict[str, Any], datasets: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """入库前校验 Widget → Dataset → Chart.Option 是否形成可渲染闭环。"""
    report = _validate_render_contract_report(dsl, datasets)
    if report.get('status') == 'success':
        return True, ''
    issues = report.get('issues') or []
    first = issues[0] if issues else {}
    msg = str(first.get('message') or 'DSL 渲染契约错误')
    if len(issues) > 1:
        msg += f'（另有 {len(issues) - 1} 个问题，详见 kanban_dsl.validation.json）'
    return False, msg


def _should_write_validation_report(report: Dict[str, Any]) -> bool:
    """失败、自修复或显式开启调试时才写 validation report。"""
    flag = str(os.environ.get('KANBAN_DSL_WRITE_VALIDATION', '') or '').strip().lower()
    if flag in {'1', 'true', 'yes', 'on'}:
        return True
    if report.get('status') != 'success':
        return True
    return bool(report.get('autoRepairCount') or report.get('autoRepairs'))


def _write_validation_report(output_dir: str, report: Dict[str, Any]) -> str:
    """按需落盘轻量诊断报告；成功且无自修复时默认不写。"""
    if not _should_write_validation_report(report):
        return ''
    try:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, 'kanban_dsl.validation.json')
        payload = dict(report)
        payload['reportPath'] = path
        payload.setdefault('nextAction', 'patch_spec_or_emitter_and_rerun' if payload.get('status') == 'failed' else 'none')
        payload.setdefault('llmContext', {
            'onlyNeedRead': ['kanban_dsl.validation.json', '当前 kanban_spec.py 或会话中的 SPEC'],
            'doNotNeedRead': ['完整 kanban_dsl.json', '完整 kanban_dsl_emitter.py'],
        })
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return path
    except (TypeError, ValueError, IOError) as e:
        print(f'⚠️ DSL 校验报告落盘失败: {e}')
        return ''


def _build_dataset_for_widget(record: Dict[str, Any],
                              dataset_key: str,
                              kpi_metrics_in_dataset: List[Metric],
                              slot_data: Optional[List[List[Any]]],
                              sql: Optional[str],
                              source: Source,
                              slot_meta: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """为单个 widget 构造 lowerCamelCase dataset。

    Args:
        record: widget 元数据
        dataset_key: dataset 主键（KPI 共享 'kpi_overview'，其他 = widget_id）
        kpi_metrics_in_dataset: 当 dataset_key='kpi_overview' 时，整组 KPI metrics（聚合到 dataset.metrics）
        slot_meta: runner 生成的 slot 元数据，用于透传 sqlType/dataSourceId/connectionType/refreshInterval

    Returns:
        非文本 widget 返回 dataset dict；纯文本 widget 返回 None。
    """
    if record.get('type') == 'text':
        return None

    spec_obj = record.get('spec_obj')

    # 收集 metrics / dimensions（入库协议统一 lowerCamelCase）
    metrics_list: List[Dict[str, Any]] = []
    dims_list: List[Dict[str, Any]] = []

    if isinstance(spec_obj, Compare):
        m = spec_obj.metric
        metrics_list.append({
            'name': m.label or _metric_alias(m),
            'field': _metric_alias(m),
            'formula': m.expr,
            'description': m.description or m.label or '',
        })
        d = spec_obj.dim
        dims_list.append({
            'name': d.label or _dim_alias(d),
            'field': _dim_alias(d),
            'granularity': d.granularity if d.is_time else 'category',
            'description': d.description or d.label or '',
        })
    elif isinstance(spec_obj, Chart):
        for m in (spec_obj.metrics or []):
            metrics_list.append({
                'name': m.label or _metric_alias(m),
                'field': _metric_alias(m),
                'formula': m.expr,
                'description': m.description or m.label or '',
            })
        for d in (spec_obj.dims or []):
            dims_list.append({
                'name': d.label or _dim_alias(d),
                'field': _dim_alias(d),
                'granularity': d.granularity if d.is_time else 'category',
                'description': d.description or d.label or '',
            })
    elif kpi_metrics_in_dataset:
        # KPI dataset：聚合所有 KPI metrics 到一个 dataset
        for m in kpi_metrics_in_dataset:
            metrics_list.append({
                'name': m.label or _metric_alias(m),
                'field': _metric_alias(m),
                'formula': m.expr,
                'description': m.description or m.label or '',
            })

    # columns：从 slot_data 首行 header 推；columnType 从 source.columns 兜底
    src_col_types: Dict[str, str] = {}
    for col in (source.columns or []):
        if isinstance(col, dict):
            src_col_types[col.get('name', '')] = col.get('type', 'string')

    slot_data = _normalize_slot_data_for_display(slot_data)
    header_fields = [str(name) for name in ((slot_data[0] if slot_data else []) or [])]
    # 组件编辑器按 metrics/dimensions[].field 回查 Dataset columns；这里按图表语义对齐真实 header。
    _align_dataset_meta_to_headers(record, dims_list, metrics_list, header_fields)

    columns: List[Dict[str, Any]] = []
    if slot_data and isinstance(slot_data, list) and slot_data:
        dim_fields = {str(d.get('field') or '') for d in dims_list if isinstance(d, dict)}
        metric_fields = {str(m.get('field') or '') for m in metrics_list if isinstance(m, dict)}
        for name in (slot_data[0] or []):
            name_s = str(name)
            # 优先按 metric/dim 推断（聚合产物列名通常不在 source.columns 里）
            col_type = 'string'
            # Dim 命中 → 沿用 source 列类型；若是语义化维度别名（source/target/category/name）则保持 string。
            if name_s in dim_fields:
                col_type = _column_type_lower(src_col_types.get(name_s, 'string'))
            elif name_s in src_col_types:
                col_type = _column_type_lower(src_col_types[name_s])
            elif name_s in metric_fields:
                col_type = 'double'
            else:
                # KPI 单值 / 同环比衍生列 / 无元数据数值列默认 double；常见语义维度列默认 string。
                col_type = 'string' if name_s in {
                    'name', 'category', 'cat', 'source', 'target', 'parent',
                    'stage', 'stage_name', 'date', 'time', 'period', 'group',
                } else 'double'
            columns.append({'columnName': name_s, 'columnType': col_type})

    # data：序列化为 JSON 字符串（首行 header），保持 ensure_ascii=False
    data_str = json.dumps(slot_data, ensure_ascii=False) if slot_data else None

    dataset: Dict[str, Any] = {
        'key': dataset_key,
        'sql': sql or '',
        'metrics': metrics_list,
        'dimensions': dims_list,
    }
    if data_str is not None:
        dataset['data'] = data_str
    dataset['columns'] = columns

    slot_meta = slot_meta or {}
    refresh_interval = slot_meta.get('refreshInterval')
    if refresh_interval is not None:
        dataset['refreshInterval'] = refresh_interval
    sql_type = slot_meta.get('sqlType')
    if sql_type is not None:
        dataset['sqlType'] = sql_type
    data_source_id = str(slot_meta.get('dataSourceId') or '').strip()
    if data_source_id:
        dataset['dataSourceId'] = data_source_id
    connection_type = str(slot_meta.get('connectionType') or '').strip()
    if connection_type:
        dataset['connectionType'] = connection_type
    return dataset


# ---------------------------------------------------------------------------
# 主入口：spec + widget_records + slot_data → DSL dict + 落盘
# ---------------------------------------------------------------------------

def emit_dsl(spec: Spec,
             widget_records: List[Dict[str, Any]],
             slot_data_map: Dict[str, List[List[Any]]],
             sql_map: Dict[str, str],
             output_dir: str,
             slot_meta_map: Optional[Dict[str, Dict[str, Any]]] = None,
             save_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """生成 DSL JSON 并落盘到 {output_dir}/kanban_dsl.json。

    Args:
        spec: 看板 Spec 实例
        widget_records: runner 编译循环里收集的 widget 元数据列表，每项含：
            {
                'widget_id':  str,         # 全局唯一 ID（与 slot_key 对齐，文本类用 'widget-page-*'）
                'role':       str | None,  # 'page_title' / 'page_subtitle' / 'kpi' / 'chart' / 'note'
                'type':       str,         # 'kpi' / 'echarts' / 'table' / 'text'
                'kind':       str | None,  # 原 spec.kind（chart/compare 时有）
                'span':       int | None,
                'title':      str,
                'emoji':      str,
                'cfg':        dict | None, # ECharts options（runner 编译产出）
                'kpi_config': dict | None,
                'spec_obj':   Chart|Compare|None,
                'kpi_metric': Metric | None,
                'description': str | None,
            }
        slot_data_map: {slot_key: 2D 数组（首行 header）}，runner 编译循环里的 slot_data 字典
        sql_map:       {slot_key: 编译期 SQL}，runner _build_slot_meta 收集到的 sql 字段
        output_dir:    kanban_dsl.json 写入目录
        slot_meta_map: {slot_key: slot 元数据}，用于透传 sqlType/dataSourceId/connectionType
        save_meta:     基础保存参数；传入时 emitter 会合成最终 kanban_save_params.json 并一次性落盘

    Returns:
        生成的 DSL dict（同时已写入磁盘）
    """
    now = _now_iso8601()
    slot_meta_map = slot_meta_map or {}

    # 1. 构造 layout
    page_layout = _solve_layout(widget_records, spec)
    layout_index = {item['i']: item for item in page_layout}

    # 预收集：KPI 共享 dataset 的所有 metrics（按 widget_records 出现顺序）
    _kpi_metrics: List[Metric] = []
    _kpi_dataset_key = None
    for _r in widget_records:
        if _r.get('type') == 'kpi' and _r.get('kpi_metric') is not None:
            _kpi_metrics.append(_r['kpi_metric'])
            if _kpi_dataset_key is None:
                _kpi_dataset_key = _r.get('dataset_key') or 'kpi_overview'

    # 2. 构造 widgets + datasets
    widgets: List[Dict[str, Any]] = []
    datasets: List[Dict[str, Any]] = []
    seen_dataset_keys = set()
    kpi_value_fields = list((slot_data_map.get('kpi_overview') or [[]])[0] or [])
    kpi_seen_index = 0

    for r in widget_records:
        wid = r['widget_id']
        wtype = _widget_type_of(r)
        layout_item = layout_index.get(wid, {})
        w_cells = layout_item.get('w', GRID_COLS)
        h_cells = layout_item.get('h', HEIGHT_BY_KIND.get(wtype, 6))

        is_text_only = (wtype == 'text')
        is_page_title = (r.get('role') == 'page_title')

        # page-title 有副标题(description)时需要更大高度（title + subtitle 双行）
        if is_page_title and r.get('description') and h_cells < 3:
            h_cells = 3

        # Title.Text：title + emoji 内嵌
        emoji = r.get('emoji') or ''
        title_text = f'{emoji} {r["title"]}'.strip() if emoji else r['title']

        # ── Card / Title 派发 ──
        if is_text_only:
            # page-title 白底卡片（含副标题时更高）；note 透明背景。
            if is_page_title:
                card = {
                    'Padding': {'X': 12, 'Y': 6},
                    'Background': {'Color': '#ffffff', 'Opacity': 100},
                    'Border': {'Color': CARD_BORDER, 'Width': 1, 'Style': 'solid', 'Radius': CARD_RADIUS},
                }
            else:
                card = _default_card(transparent=True)
            if is_page_title:
                title_block = _default_title(title_text, kind='page')
                if r.get('description'):
                    title_block['Description'] = {'Show': True, 'Text': r['description']}
                    # 有副标题时加大上下内边距，避免文字贴边
                    title_block['Padding'] = {'X': 18, 'Y': 10}
                    card = {
                        'Padding': {'X': 12, 'Y': 8},
                        'Background': {'Color': '#ffffff', 'Opacity': 100},
                        'Border': {'Color': CARD_BORDER, 'Width': 1, 'Style': 'solid', 'Radius': CARD_RADIUS},
                    }
            else:
                title_block = _default_title(title_text, kind='card')
                if r.get('description'):
                    title_block['Description'] = {'Show': True, 'Text': r['description']}
        elif r.get('type') == 'kpi':
            # KPI 卡内边距：Y 从 16 降到 14，与 4 行高（80px）更协调，避免上下留白过多；
            # 数字在 chart 区域内 alignItems:center 已自居中，卡片本身不必再堆内边距。
            card = _default_card()
            card['Padding'] = {'X': 16, 'Y': 14}
            # 单位归属 value：不要把 "%" / "¥" 等度量单位拼到标题里，避免标题承担数值语义。
            title_block = _default_title(r['title'], kind='kpi-label')
            # KPI 副标题：若 metric 声明了 description，透传到 Title.Description，
            # 由 WidgetTitle 渲染为次级说明文字（与 page-title 分支的用法一致）。
            _kpi_metric_for_desc: Optional[Metric] = r.get('kpi_metric')
            _kpi_desc = getattr(_kpi_metric_for_desc, 'description', None) if _kpi_metric_for_desc else None
            if _kpi_desc:
                title_block['Description'] = {'Show': True, 'Text': str(_kpi_desc)}
        else:
            card = _default_card()
            title_block = _default_title(title_text, kind='card')
            if r.get('description'):
                title_block['Description'] = {'Show': True, 'Text': r['description']}

        # KPI 共享 dataset_key；其他 widget 1:1 走自己的 widget_id
        if r.get('type') == 'kpi':
            ds_key = r.get('dataset_key') or _kpi_dataset_key or 'kpi_overview'
        else:
            ds_key = wid

        widget: Dict[str, Any] = {
            'WidgetId': wid,
            'WidgetType': wtype,
            'DatasetName': None if is_text_only else ds_key,
            'Card': card,
            'Title': title_block,
            'Chart': None,
        }

        # ── 文本类：Chart=None，无 dataset ──
        if is_text_only:
            widgets.append(widget)
            continue

        # slot_data / sql 查表（在 dataset 构造和 Chart.Option 翻译里都要用）
        # KPI dataset：从 slot_data_map 中找 'kpi_overview'（runner 写入的固定 key）
        data_lookup_key = ds_key if r.get('type') != 'kpi' else 'kpi_overview'
        slot_data = _normalize_slot_data_for_widget(r, slot_data_map.get(data_lookup_key))
        sql = sql_map.get(data_lookup_key, '')
        slot_meta = slot_meta_map.get(data_lookup_key, {})

        # ── 收集 dataset（KPI 共享，其他 1:1）──
        if ds_key not in seen_dataset_keys:
            ds = _build_dataset_for_widget(
                r, ds_key,
                _kpi_metrics if r.get('type') == 'kpi' else [],
                slot_data, sql, spec.source, slot_meta,
            )
            if ds is not None:
                datasets.append(ds)
                seen_dataset_keys.add(ds_key)

        # ── Chart.Option 派发 ──
        chart_block = _default_chart_block()

        if r.get('type') == 'kpi':
            kpi_metric: Optional[Metric] = r.get('kpi_metric')
            if kpi_metric is None and spec.kpis:
                kpi_metric = spec.kpis[0]
            value_field = None
            if kpi_seen_index < len(kpi_value_fields):
                value_field = str(kpi_value_fields[kpi_seen_index])
            # 数值色采用"单色主导"策略（Linear / Stripe / Apple 风格）：
            # 统一使用 TITLE_COLOR（#0F172A 深墨蓝）作为数字色，避免一行多张 KPI 
            # "五彩斑斓"的装饰性屠杀。颜色应承载语义（好/坏/趋势）而非纯装饰；
            # 保留 KPI_VALUE_COLORS 供未来"按语义分色"（负向指标羻 / 正向指标绿）使用。
            # 层次靠"字号 32 vs 12"、"字重 600 vs 500"、"色值 深墨 vs 浅灰"完成，而非颜色。
            _kpi_color = TITLE_COLOR
            kpi_seen_index += 1
            chart_block['Legend'] = {'Show': False, 'Position': 'top',
                                     'Orient': 'horizontal', 'Color': None}
            chart_block['Tooltip'] = {'Show': False, 'BackgroundColor': None,
                                      'BorderColor': None, 'FontColor': None}
            # KPI Chart 区域四向 Padding：左侧 0 与 title 左对齐（视觉基线一致），
            # 右侧留 12px 防长数字撞卡右边；上下极小 padding 让数字与容器关系更紧密。
            # 对称原则：人眼对左右不平衡极敏感，左侧不再内缩避免"向左偏"视觉错觉。
            chart_block['Padding'] = {'X': 0, 'Y': 0, 'Left': 0, 'Right': 12,
                                      'Top': 2, 'Bottom': 2}
            # 高保真数值样式通道：面板 Chart.Text.Font.* 在前端优先于 indexCard.valueFontSize。
            # 现代审美默认值（对齐 Stripe / Linear / Notion 级 KPI）：
            #   Size=24 —— KPI 数字尺寸的"安全默认"：一行 5~6 张卡时单卡内宽 ~150~180px，
            #             长金额数字（10~12 位含千分位，如 135,702,970）用 32 会溢出截断，
            #             24 是既能保完整可读、又能与 12px 标题保持 2x 层次比的甜蜜点。
            #   Weight=600 —— Semibold，比 700 Bold 更精致，避免"用力过猛"
            #   LineHeight=1.15 —— 24px 数字用略宽行高，避免顶部/底部贴边
            #   LetterSpacing=0 —— 24px 已经不需要额外字距，保持紧凑不发散
            chart_block['Text'] = {
                'Font': {
                    'Family': None,
                    'Size': 24,
                    'Weight': 600,
                    'Color': _kpi_color,
                    'LineHeight': 1.15,
                    'LetterSpacing': 0,
                    'StrokeColor': None,
                    'StrokeWidth': 0,
                },
            }
            chart_block['Option'] = (
                _build_indexcard_option(kpi_metric, value_field=value_field, color=_kpi_color) if kpi_metric
                else json.dumps({'indexCard': {}}, ensure_ascii=False)
            )
        elif r.get('type') == 'table':
            spec_obj = r.get('spec_obj')
            if isinstance(spec_obj, Chart):
                chart_block['Option'] = _build_table_option(
                    spec_obj, slot_data, list(spec.source.columns),
                )
            else:
                chart_block['Option'] = _build_table_option(
                    Chart(kind='table', title='', metrics=[], dims=[]),  # type: ignore
                    slot_data, list(spec.source.columns),
                )
        else:
            # ECharts 族：cfg 由 emitter 按 widget_type + slot_data 翻译为完整 native option
            spec_obj = r.get('spec_obj')
            chart_block['Option'] = _build_native_echarts_option(
                wtype, r.get('cfg'), slot_data,
                spec_obj if isinstance(spec_obj, Chart) else None,
            )

        widget['Chart'] = chart_block
        widgets.append(widget)

    # 3. 顶层组装
    #    Meta 仅保留第一版 DSL 协议字段：
    #      - SchemaVersion：DSL 协议 schema 版本，仅升 schema 时递增
    #      - KanbanVersion：单块看板的业务版本号，本地生成初始为 1，运行态以服务端 Version 为准
    #      - Status：DSL 生成时刻为 DRAFT；发布态/预览态以 GetAiKanBan 返回的 Status/ViewStatus 为准
    dsl: Dict[str, Any] = {
        'Meta': {
            'SchemaVersion': DSL_VERSION,
            'KanbanVersion': 1,
            'Status': 'DRAFT',
            'Source': 'aidash',
            'DisplayName': spec.title,
            'Description': spec.subtitle or '',
            'CreatedAt': now,
            'UpdatedAt': now,
            'Author': 'ai-agent',
            'Tags': [spec.theme] if spec.theme else [],
        },
        'UiSettings': _build_ui_settings(spec.theme),
        'Pages': [{
            'DisplayName': spec.title or '无标题页面',
            'PageLayout': page_layout,
            'Widgets': widgets,
        }],
        'Datasets': datasets,
    }

    # 4. 入库前稳定化：确定性自修复 + 全量校验报告。
    #    自修复只处理可由 Dataset.columns / Widget.DatasetName 推断的协议字段，避免改变业务语义。
    auto_repairs = _autofix_render_contract(dsl, datasets)
    validation_report = _validate_render_contract_report(dsl, datasets)
    validation_report['autoRepairs'] = auto_repairs
    validation_report['autoRepairCount'] = len(auto_repairs)
    validation_path = _write_validation_report(output_dir, validation_report)
    if validation_path:
        validation_report['reportPath'] = validation_path
    dsl['_DslValidationReport'] = validation_report
    if auto_repairs:
        _suffix = f'（详见 {os.path.basename(validation_path)}）' if validation_path else ''
        print(f'🛠️ DSL 已完成确定性自修复: {len(auto_repairs)} 项{_suffix}')

    # 5. 落盘公共 DSL；内部诊断字段只随 emit_dsl 返回，不进入 kanban_dsl.json/HtmlContent。
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'kanban_dsl.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(_dsl_without_internal_fields(dsl), f, ensure_ascii=False, indent=2)
    print(f'📄 DSL 描述层已生成: {out_path}（{len(widgets)} widgets / {len(datasets)} datasets）')

    # 6. 写入 kanban_save_params.json 的 HtmlContent / SqlSlots 为 DSL + lowerCamelCase Dataset 协议形态
    #    （在 build_save_meta 之后跑，最终写入平台 SaveAiKanBan/UpdateAiKanBan 的就是这两个值）
    _patch_ok, _patch_error = _patch_save_params_with_dsl(output_dir, dsl, datasets, validation_report, save_meta)
    dsl['_SaveParamsPatched'] = _patch_ok
    if _patch_error:
        dsl['_SaveParamsPatchError'] = _patch_error

    return dsl


def _patch_save_params_with_dsl(output_dir: str,
                                dsl: Dict[str, Any],
                                datasets: List[Dict[str, Any]],
                                validation_report: Optional[Dict[str, Any]] = None,
                                save_meta: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """把页面/组件 DSL + Datasets 数组编码后写入最终 kanban_save_params.json
    的 HtmlContent / SqlSlots 字段。

    设计动机
    --------
    平台以 DSL JSON + lowerCamelCase Dataset 数组作为三端统一权威源：
      - HtmlContent = base64(json.dumps(不含 Datasets 的页面/组件 DSL)) 或 gzip+base64 大字段传输形态
      - SqlSlots    = base64(json.dumps(Datasets 数组)) 或 gzip+base64 大字段传输形态，是唯一 Dataset 入库源

    实现策略（最小侵入 + 时序安全）
    --------------------------------
runner 主流程时序：write_kanban_outputs → emit_dsl → update_to_kanban_list（UpdateAiKanBan/PREVIEW）。
    write_kanban_outputs 只完成 lint 并返回基础 save_meta；emit_dsl 在 DSL/Datasets 构造和校验成功后，
    将基础字段与 HtmlContent/SqlSlots 合并，并一次性原子写入 kanban_save_params.json。
    后续 preview 同步（UpdateAiKanBan）读的就是最终 params，PC/H5/embed 三端统一渲染源；
    发布保存（SaveAiKanBan）只提交 WorkspaceId + AccessKey，不再提交 HtmlContent / SqlSlots。

    失败策略
    --------
    kanban_dsl.json 本身仍完整落盘（含 Datasets），便于本地排障；但返回失败状态，让 runner 阻断后续
    PREVIEW 同步，避免把空值或旧 params 内容误写入新的 DSL 预览接口。
    """
    params_path = os.path.join(output_dir, 'kanban_save_params.json')
    params: Dict[str, Any] = dict(save_meta) if isinstance(save_meta, dict) else {}
    if not params and os.path.isfile(params_path):
        # 兼容纯 emit 单测/旧调用方：没有显式 save_meta 时才读取已有最终参数。
        try:
            with open(params_path, 'r', encoding='utf-8') as f:
                params = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            msg = f'DSL 同步保存参数：读取 kanban_save_params.json 失败，跳过覆盖: {e}'
            print(f'⚠️ {msg}')
            return False, msg
    if not params:
        msg = 'DSL 同步保存参数：缺少基础 save_meta，无法写入最终 kanban_save_params.json'
        print(f'⚠️ {msg}')
        return False, msg

    valid_datasets, dataset_error = _validate_lower_camel_datasets(datasets)
    if not valid_datasets:
        msg = f'DSL 同步保存参数：{dataset_error}'
        print(f'⚠️ {msg}')
        return False, msg

    render_report = validation_report if isinstance(validation_report, dict) else _validate_render_contract_report(dsl, datasets)
    if render_report.get('status') != 'success':
        issues = render_report.get('issues') or []
        first = issues[0] if issues else {}
        first_msg = str(first.get('message') or 'DSL 渲染契约错误')
        report_path = str(render_report.get('reportPath') or os.path.join(output_dir, 'kanban_dsl.validation.json'))
        msg = f'DSL 渲染契约错误：{first_msg}（共 {len(issues)} 个问题，详见 {report_path}）'
        print(f'⚠️ {msg}')
        return False, msg

    try:
        slim_dsl = _dsl_without_datasets(dsl)
        datasets_for_sqlslots, data_stripped, data_bytes = _strip_default_render_data_if_needed(datasets)
        if data_stripped:
            print(f'🪶 SqlSlots 默认渲染 data 超过服务端阈值，已按服务端同口径在生成端整组剥离: '
                  f'dataBytes={data_bytes}B, threshold={MAX_DEFAULT_RENDER_DATA_BYTES}B, '
                  f'datasets={len(datasets_for_sqlslots)}')

        dsl_json_str = json.dumps(slim_dsl, ensure_ascii=False)
        datasets_json_str = json.dumps(datasets_for_sqlslots, ensure_ascii=False)
        params['HtmlContent'] = _encode_update_payload(dsl_json_str, 'HtmlContent')
        params['SqlSlots'] = _encode_update_payload(datasets_json_str, 'SqlSlots')

        os.makedirs(output_dir, exist_ok=True)
        tmp_path = f'{params_path}.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(params, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, params_path)
        print(f'🔄 已一次性写入 kanban_save_params.json: HtmlContent={len(dsl_json_str)} chars '
              f'(no Datasets), SqlSlots={len(datasets_json_str)} chars '
              f'(datasets={len(datasets_for_sqlslots)}, dataStripped={data_stripped})')
        return True, ''
    except (TypeError, ValueError, IOError, OSError) as e:
        msg = f'DSL 同步保存参数：写入失败: {e}'
        print(f'⚠️ {msg}')
        return False, msg


__all__ = ['emit_dsl', 'DSL_VERSION', 'GRID_COLS']
