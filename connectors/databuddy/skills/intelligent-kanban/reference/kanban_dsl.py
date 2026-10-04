"""
看板 DSL —— L3 颗粒度声明式 Spec。

LLM 唯一编写文件 kanban_spec_*.py，只构造一个 Spec 实例。
runner 接收 Spec 编译为 SQL/SLOT_DATA/sqlSlots/DSL widgets，调用 builder 落盘 kanban_save_params.json，
随后 kanban_dsl_emitter 覆盖 HtmlContent(DSL)/SqlSlots(Datasets)，三端统一入库。

设计原则：
1. **统一抽象**：dim/x/y/path/source_dim/target_dim/nodes/group → 全部统一为 Dim
                metric/value/o/c/l/h/indicators → 全部统一为 Metric（带可选 role）
2. **三态数据形态**：series（一维）/matrix（二维交叉）/hierarchy（多层路径）自动识别
3. **逃生口**：复杂 SQL 走 raw_sql=，仍走 builder 全 lint
4. **类型安全**：dataclass + 必填校验，构造期就拦截大部分错误
5. **extras 兜底**：任何超出抽象的 echarts 原生配置走 extras=，零妥协灵活性
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union
import sys as _sys
import re as _re


# ===== SQL 字符串字面量自动归一化（治本：从 DSL 构造期消除双引号字面量误用） =====
#
# 背景（SKILL.md P0-10 ④）：Spark/DuckDB 中双引号是**列引用**，不是字符串。
# LLM 用 Python 双引号包 SQL 时极易把内层字符串也写成双引号：
#   SUM(CASE WHEN status = "delivered" THEN 1 ELSE 0 END)
# DuckDB Binder 找不到列 "delivered" → CASE 静默退化为 NULL → SUM=0（KPI 假 0）。
#
# 本工具用字符串感知扫描（与 runner._strip_string_literals 同款思路），
# 把所有**双引号包裹的字面量**改写为单引号，并 stderr 打软告警。
# - 跳过单引号已包字符串内部（避免误伤 'I love "quoted"'）
# - 跳过反引号包裹标识符（`col_name`，那是真列引用）
# - "" 双双引号是 Spark 内部转义 → 转为单引号内 \" 不需要（直接拼为含 " 的内容用 '' 转义不可行，
#   但 Spark 的 ""→" 与 DuckDB 的 ''→' 行为一致，这里我们按"内容里允许出现 \""保守处理：
#   遇到 "" 视为字符串内部的字面量 "，输出时用 \"（DuckDB/Spark 都接受 \" 转义）
#
# 该函数对**已正确使用单引号**或**不含双引号字面量**的 SQL 完全幂等无副作用。

def _normalize_sql_string_literals(expr: str, *, ctx: str = '') -> str:
    """把 SQL 表达式里的双引号字符串字面量改写为单引号字面量。

    Args:
        expr: 原始 SQL 表达式（dim/metric/raw_sql 等）
        ctx:  上下文标识（如 'Metric.expr@KPI 总额'），仅用于软告警显示

    Returns:
        归一化后的 SQL 表达式；若未触发改写则原样返回。

    设计原则：
    - 字符串感知扫描：跳过单引号字符串内部 + 反引号标识符内部
    - 双引号包裹的内容视为字面量误用，整体替换为单引号字面量
    - 内容含单引号 → 用 '' 转义；内容含 "" → 视为字符串内 "，转为 \"
    - 触发改写时 stderr 打一行软告警（不 raise，避免为单一 SQL 纠偏触发整轮重跑）
    """
    if not expr or '"' not in expr:
        return expr

    out: List[str] = []
    i = 0
    n = len(expr)
    in_single = False   # 在 '...' 内
    in_backtick = False # 在 `...` 内
    changed_segments: List[str] = []

    while i < n:
        ch = expr[i]
        if in_single:
            out.append(ch)
            if ch == "'":
                # 处理 '' 转义
                if i + 1 < n and expr[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                in_single = False
            i += 1
            continue
        if in_backtick:
            out.append(ch)
            if ch == '`':
                in_backtick = False
            i += 1
            continue
        if ch == "'":
            in_single = True
            out.append(ch)
            i += 1
            continue
        if ch == '`':
            in_backtick = True
            out.append(ch)
            i += 1
            continue
        if ch == '"':
            # 抓取整段 "...."（含 "" 转义）
            j = i + 1
            buf: List[str] = []
            closed = False
            while j < n:
                c2 = expr[j]
                if c2 == '"':
                    if j + 1 < n and expr[j + 1] == '"':
                        # "" → 字面量内的 "
                        buf.append('"')
                        j += 2
                        continue
                    closed = True
                    j += 1
                    break
                buf.append(c2)
                j += 1
            if not closed:
                # 未闭合双引号：保守原样输出，不动
                out.append(expr[i:])
                break
            content = ''.join(buf)
            # 改写为单引号字面量：内容中的 ' 需用 '' 转义；内容中的 " 用 \" 转义
            escaped = content.replace("'", "''").replace('"', '\\"')
            out.append("'" + escaped + "'")
            changed_segments.append(f'"{content}"→\'{escaped}\'')
            i = j
            continue
        out.append(ch)
        i += 1

    new_expr = ''.join(out)
    if changed_segments:
        try:
            tag = f'[{ctx}] ' if ctx else ''
            print(
                f'⚠️  [DSL 软告警] {tag}SQL 字面量双引号已自动改写为单引号 '
                f'（Spark/DuckDB 双引号=列引用，单引号=字符串）：'
                + ' | '.join(changed_segments[:3])
                + (f' …(+{len(changed_segments)-3})' if len(changed_segments) > 3 else ''),
                file=_sys.stderr,
            )
        except Exception:
            pass
    return new_expr


# ===== raw_sql 标识符引号纠偏（FROM/JOIN 后单/双引号包标识符 → 反引号） =====
#
# 背景：远端 Spark PARSE_SYNTAX_ERROR Top1 来源是 raw_sql 里 `FROM 'tbl'` / `JOIN 'tbl'`：
#   - LLM 习惯按 ANSI SQL 写 `JOIN "tbl"` 包标识符 → 后续 _normalize_sql_string_literals
#     无差别把所有 `"..."` 治成 `'...'` → Spark 把 'tbl' 当字符串字面量 → PARSE_SYNTAX_ERROR；
#   - 或 LLM 直接写 `JOIN 'tbl'`（误解为 ANSI）；
#   本地 DuckDB 对 `FROM 'tbl'` 行为更宽松（甚至当 csv 路径），无法暴露问题，
#   导致"本地预览成功 / 远端入库失败"的失真陷阱。
#
# 治理策略（必须**先于** _normalize_sql_string_literals 执行）：
#   FROM/JOIN/逗号（FROM 列表分隔）/USING 后紧跟 'X' 或 "X"，且 X 形似标识符
#   （满足 `^[\w.\-]+$` 且非数字字面量）→ 改写为 `` `X` ``（反引号包裹）。
#   字符串字面量内部 / 反引号内部 / CTE 别名不命中。

# 标识符形态：英文字母/数字/下划线/点/连字符；至少含一个字母；禁纯数字
_RAW_SQL_IDENT_RE = _re.compile(r'^[A-Za-z_][\w.\-]*$')

# FROM/JOIN 关键字上下文（紧邻空白后的引号位置才算）。
# 注意：故意**不**包含 `,`（无法区分 FROM 多表 / SELECT 列表 / 函数参数）和
#       `USING`（USING 后紧跟的是列名列表非表名）。漏检由用户改用 JOIN 兜底。
_RAW_SQL_TABLE_CTX_RE = _re.compile(
    r'\b(?:FROM|JOIN)\b\s*$', _re.IGNORECASE
)


def _normalize_raw_sql_identifiers(sql: str, *, ctx: str = '') -> str:
    """把 raw_sql 中 FROM/JOIN/USING/, 后紧跟的 'X' 或 "X" 改写为 `X`（反引号）。

    仅当 X 形似标识符（含点的三段式 / 含连字符的 hive 表名等）时才改写；
    否则保持原样（普通字符串字面量、子查询别名 AS 'name' 不命中）。

    与 _normalize_sql_string_literals 配合：
      raw_sql ─┬─ _normalize_raw_sql_identifiers  # 第一步：标识符场景的引号纠偏
               └─ _normalize_sql_string_literals  # 第二步：剩余双引号字面量改单引号
    """
    if not sql or ('"' not in sql and "'" not in sql):
        return sql

    out: List[str] = []
    i = 0
    n = len(sql)
    in_single = False
    in_backtick = False
    in_dquote_literal = False  # 仅在不处于 FROM/JOIN 上下文时才视为字面量
    rewrites: List[str] = []

    def _is_table_ctx() -> bool:
        # 用已收集的 out 字符串末尾判断（含空白）；keyword 必须是独立词
        tail = ''.join(out[-32:]) if out else ''
        return bool(_RAW_SQL_TABLE_CTX_RE.search(tail))

    while i < n:
        ch = sql[i]
        # 已在单引号字符串内：仅处理闭合 + '' 转义
        if in_single:
            out.append(ch)
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                in_single = False
            i += 1
            continue
        # 已在反引号内：透传
        if in_backtick:
            out.append(ch)
            if ch == '`':
                in_backtick = False
            i += 1
            continue
        if ch == '`':
            in_backtick = True
            out.append(ch)
            i += 1
            continue
        # 双引号或单引号开头：先看上下文是否是 FROM/JOIN/USING/,
        if ch == '"' or ch == "'":
            quote = ch
            # 抓取整段（含转义）
            j = i + 1
            buf: List[str] = []
            closed = False
            while j < n:
                c2 = sql[j]
                if c2 == quote:
                    # 转义：双双引号 / 双单引号
                    if j + 1 < n and sql[j + 1] == quote:
                        buf.append(quote)
                        j += 2
                        continue
                    closed = True
                    j += 1
                    break
                buf.append(c2)
                j += 1
            content = ''.join(buf)
            if closed and _is_table_ctx() and _RAW_SQL_IDENT_RE.match(content):
                # 改写为反引号
                out.append('`' + content + '`')
                rewrites.append(f'{quote}{content}{quote}→`{content}`')
                i = j
                continue
            # 否则保持原样进入字面量分支
            if not closed:
                out.append(sql[i:])
                break
            if quote == "'":
                # 仍按字面量原样输出
                out.append(quote)
                # 内部内容（含原始 '' 转义）原样回填
                k = i + 1
                while k < j:
                    out.append(sql[k])
                    k += 1
                i = j
                continue
            else:
                # 双引号未识别为标识符：原样回吐让 _normalize_sql_string_literals 处理
                out.append(quote)
                k = i + 1
                while k < j:
                    out.append(sql[k])
                    k += 1
                i = j
                continue
        out.append(ch)
        i += 1

    new_sql = ''.join(out)
    if rewrites:
        try:
            tag = f'[{ctx}] ' if ctx else ''
            print(
                f'⚠️  [DSL 软告警] {tag}raw_sql 中 FROM/JOIN 后引号包裹的标识符已自动改为反引号 '
                f'（Spark 单/双引号=字符串字面量，反引号=标识符）：'
                + ' | '.join(rewrites[:3])
                + (f' …(+{len(rewrites)-3})' if len(rewrites) > 3 else ''),
                file=_sys.stderr,
            )
        except Exception:
            pass
    return new_sql


# ===== Dim：统一维度抽象 =====

@dataclass(frozen=True)
class Dim:
    """统一维度抽象。覆盖：裸列名 / SQL 表达式 / 时间分桶。

    Args:
        expr:        SQL 表达式或裸列名（必填）
        alias:       SQL/SLOT 列别名（默认从 expr 派生）
        label:       显示名（入库 dimensions[].name，如 '月份' / '品类'；缺省回退 alias/expr）
        granularity: 维度粒度。
                     - 时间粒度：day/week/month/quarter/year（runner 走时间分桶）
                     - 业务粒度：category/product/region/channel/... 任意非空字符串
                     - None：runner 视为非时间维度（裸列名/SQL 表达式）
        description: 业务说明（入库 dimensions[].description）
        col_type:    string/date/timestamp/unix（时间维度需要；date/timestamp 走裸列，Unix 秒/毫秒分桶请用 raw_sql 显式 FROM_UNIXTIME）

    示例：
        Dim('product_type', label='品类', granularity='category')
        Dim('time', label='月份', granularity='month')
        Dim("CASE WHEN p<20 THEN 'L' ELSE 'H' END", label='价格段')
    """
    expr: str
    alias: Optional[str] = None
    label: Optional[str] = None
    granularity: Optional[str] = None
    description: Optional[str] = None
    col_type: str = 'string'

    _TIME_GRAN = ('day', 'week', 'month', 'quarter', 'year')
    _TYPES = ('string', 'date', 'timestamp', 'unix')

    def __post_init__(self):
        if not self.expr or not str(self.expr).strip():
            raise ValueError('[DSL] Dim.expr 不能为空')
        if self.granularity is not None and not str(self.granularity).strip():
            raise ValueError('[DSL] Dim.granularity 不能为空字符串（None 表示非时间维度）')
        if self.col_type not in self._TYPES:
            raise ValueError(f'[DSL] Dim.col_type 必须 ∈ {self._TYPES}，得到: {self.col_type!r}')
        # SQL 字面量归一化（双引号→单引号），治理 LLM 高频误用
        normalized = _normalize_sql_string_literals(
            self.expr, ctx=f'Dim.expr alias={self.alias!r}'
        )
        if normalized != self.expr:
            object.__setattr__(self, 'expr', normalized)

    @property
    def is_time(self) -> bool:
        return self.granularity in self._TIME_GRAN


def dim(expr: str, alias: Optional[str] = None, **kw) -> Dim:
    """便捷工厂：dim('product_type') / dim('time', granularity='month')。"""
    return Dim(expr=expr, alias=alias, **kw)


def time_dim(col: str, granularity: str = 'month', col_type: str = 'string', **kw) -> Dim:
    """时间维度便捷工厂：time_dim('time','month', label='月份')。

    **kw 透传给 Dim（支持 alias/label/description 等所有 Dim 字段）。

    🛡️ label 兜底（消除「前端轴名永远是 'time'」的软陷阱）：
        若调用方未显式传 label，自动注入 `f'{col}({granularity})'`，
        例如 time_dim('order_purchase_timestamp','month') →
        label='order_purchase_timestamp(month)'。用户传了 label='月份' 则尊重原值。
        反例 9（time_dim 无 label）由此默认避免；如需保持纯净 col 输出可显式 label=''。
    """
    if 'label' not in kw or kw.get('label') is None:
        kw['label'] = f'{col}({granularity})'
    return Dim(expr=col, granularity=granularity, col_type=col_type, **kw)


# ===== Metric：统一度量抽象 =====

@dataclass(frozen=True)
class Metric:
    """统一度量抽象。覆盖：聚合指标 / 派生比率 / 角色化字段（K线OCLH、雷达轴）。

    Args:
        expr:      聚合 SQL 表达式（如 'SUM(sales)' 或 'SUM(a)/NULLIF(SUM(b),0)*100'）
        alias:     SLOT 列别名（默认从 expr 派生）
        label:     显示标签（KPI / 雷达轴名）
        role:      角色标签（candlestick: open/close/low/high；boxplot: value）
        format:    数字格式（用于 KPI/gauge formatter，如 ',.0f' / '.1f'）
        prefix:    数值前缀（如 '¥'）
        suffix:    数值后缀（如 '%'）
        normalize: 'max-norm' 时按最大值归一化到 100（雷达图常用）
        target:    目标值（gauge 专用，用于设置 max）

    示例：
        Metric('SUM(sales)')                                     # 普通聚合
        Metric('SUM(sales)', label='销售额', format=',.0f')       # KPI
        Metric('MIN(price)', role='low')                          # K线
        Metric('SUM(sales)', normalize='max-norm', label='销售')  # 雷达
    """
    expr: str
    alias: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None  # 入库 metrics[].description
    role: Optional[str] = None
    format: str = ','
    prefix: str = ''
    suffix: str = ''
    normalize: Optional[str] = None
    target: Optional[float] = None
    # KPI 专用：自定义 FROM 子句（表名 / 子查询 / JOIN 串），覆盖 spec.source.table。
    # 取值示例：
    #   - 'cat.db.order_items'                                      → 跨主表的另一张表聚合
    #   - 'cat.db.orders o JOIN cat.db.order_items oi ON o.id=oi.id'→ JOIN 后聚合
    #   - '(SELECT price FROM cat.db.items WHERE status="paid") t' → 子查询聚合
    # 仅当 role='kpi' 时生效；非 KPI 角色（K线/雷达/箱线）仍受 spec.source.table 约束。
    # runner 把 KPI 编译为 `SELECT {expr} AS alias FROM {from_sql or spec.source.table}`，
    # 所以 expr 仍必须是聚合表达式（SUM/COUNT/AVG/...），from_sql 只决定数据来源。
    from_sql: Optional[str] = None

    _ROLES = (None, 'open', 'close', 'low', 'high', 'value', 'kpi')
    _NORMS = (None, 'max-norm')

    def __post_init__(self):
        if not self.expr or not str(self.expr).strip():
            raise ValueError('[DSL] Metric.expr 不能为空')
        if self.role not in self._ROLES:
            raise ValueError(f'[DSL] Metric.role 必须 ∈ {self._ROLES}，得到: {self.role!r}')
        if self.normalize not in self._NORMS:
            raise ValueError(f'[DSL] Metric.normalize 必须 ∈ {self._NORMS}，得到: {self.normalize!r}')
        # SQL 字面量归一化（双引号→单引号），治理 LLM 高频误用
        normalized = _normalize_sql_string_literals(
            self.expr, ctx=f'Metric.expr label={self.label!r}'
        )
        if normalized != self.expr:
            object.__setattr__(self, 'expr', normalized)


def metric(expr: str, **kw) -> Metric:
    """便捷工厂：metric('SUM(sales)', label='销售额')。"""
    return Metric(expr=expr, **kw)


def kpi(expr: str, label: str, **kw) -> Metric:
    """KPI 便捷工厂：自动设置 role='kpi'，label 必填。

    兼容性吞噬：`emoji=` 在 KPI 中无效（KPI 卡片由 Spec.kpis 整体承载图标），
    若误传则**静默丢弃**（不再打软告警，避免 LLM 误用 chart() 风格写 kpi() 时
    在控制台刷屏；KPI 卡片头会用 spec.title 的 emoji 自动填充）。
    同样吞噬 `span=` / `slot_key=` 等仅 Chart 适用的字段。

    🛑 expr 必须是**聚合表达式**或常量（runner 编译为
    `SELECT {expr} AS alias FROM {from_sql or 主表}`，expr 必须能在 SELECT 上求值）。
    LLM 高频踩坑：把派生指标名（如 'total_gmv' / 'gmv_total'）当 expr 写进来 →
    编译产物 `SELECT total_gmv FROM olist_orders` 永远报 `Column not found` → 平台
    周期刷新一直 0。

    ✅ 跨表/JOIN 聚合：传 `from_sql=` 指定数据源（覆盖 spec.source.table），
       仍在主表所在 KPI batch 中以**标量子查询**形式合并执行，渲染真实数据：
         kpi('SUM(oi.price)', '订单商品总额',
             from_sql='cat.db.olist_orders o JOIN cat.db.order_items oi ON o.order_id=oi.order_id',
             prefix='¥', format=',.0f')
       runner 编译为：
         (SELECT SUM(oi.price) FROM <from_sql>) AS `订单商品总额`
       多张 KPI 可各自带不同 from_sql，仍拼成一条 SQL 一次性下发。
    """
    _CHART_ONLY = ('emoji', 'span', 'slot_key', 'order_by', 'limit', 'stacked',
                   'dual_axis', 'smooth', 'extras', 'kind', 'title', 'dims', 'metrics')
    for k in [k for k in list(kw.keys()) if k in _CHART_ONLY]:
        kw.pop(k, None)

    # —— KPI expr 形态契约（防"裸列名"静默失败 P0 陷阱）——
    # 合法形态：① 含聚合函数  ② 纯常量  ③ 传了 from_sql 的标量子查询语义（由 from_sql 兜底语义）
    # 非法形态：裸列名 / 派生标识符 / 含运算符但无聚合 且 没传 from_sql →
    #          runner 编译出 `SELECT <expr> FROM 主表`，主表无该列时永远 0/报错。
    _expr_norm = (expr or '').strip()
    _from_sql = (kw.get('from_sql') or '').strip()
    if _expr_norm and not _from_sql:
        _agg_re = _re.compile(
            r'\b(SUM|AVG|COUNT|MIN|MAX|PERCENTILE|PERCENTILE_APPROX|STDDEV|STDDEV_POP|STDDEV_SAMP|'
            r'VARIANCE|VAR_POP|VAR_SAMP|FIRST|LAST|FIRST_VALUE|LAST_VALUE|COLLECT_LIST|COLLECT_SET|'
            r'BIT_AND|BIT_OR|BIT_XOR|BOOL_AND|BOOL_OR|APPROX_COUNT_DISTINCT|APPROX_QUANTILE)\s*\(',
            _re.I,
        )
        # 常量字面量：纯数字 / 'xxx' / NULL / TRUE / FALSE
        _const_re = _re.compile(
            r"""^\s*(
                -?\d+(\.\d+)?            # 数字
                | '([^']|'')*'           # 单引号字符串
                | NULL | TRUE | FALSE    # 关键字常量
            )\s*$""",
            _re.I | _re.X,
        )
        if not _agg_re.search(_expr_norm) and not _const_re.match(_expr_norm):
            raise ValueError(
                f'[DSL] kpi("{_expr_norm}", "{label}") expr 不含聚合函数且非常量、且未指定 from_sql。\n'
                f'  原因：runner 把 KPI 编译为 `SELECT {_expr_norm} AS alias FROM {{主表}}`，\n'
                f'        expr 必须能在主表 SELECT 上求值；裸列名/派生标识符在主表不存在时\n'
                f'        会让 SQL 报 `Column not found`，平台周期刷新永远 0。\n'
                f'  ✅ 修法 A（主表内可聚合）：\n'
                f'      kpi("SUM(amount)", "{label}", prefix="¥", format=",.0f")\n'
                f'  ✅ 修法 B（跨表/JOIN 聚合，最常用）：\n'
                f'      kpi("SUM(oi.price)", "{label}",\n'
                f'          from_sql="cat.db.olist_orders o JOIN cat.db.order_items oi ON o.order_id=oi.order_id",\n'
                f'          prefix="¥", format=",.0f")\n'
                f'  ✅ 修法 C（子查询聚合）：\n'
                f'      kpi("SUM(price)", "{label}",\n'
                f'          from_sql="(SELECT price FROM cat.db.items WHERE status=\\"paid\\") t")'
            )

    return Metric(expr=expr, label=label, role='kpi', **kw)


# ===== Source：数据源 =====

@dataclass
class Source:
    """看板数据源。

    runner 自动按物理表拼"全量取数 SQL"（`SELECT * FROM table LIMIT N`），
    走 wedatacli query-sql 取数拿 csv，本地 DuckDB 按 columns 投影视图喂所有图表。

    Args:
        table: 表名（schema.table 形式）
        columns: 列名列表（字符串或 {name,type,is_partition} dict 都接受）
        time_col: 主时间列（用于 string 时间解析嗅探）
        time_type: string / date / timestamp / unix（datetime 按 timestamp 填；Unix 分桶需 raw_sql 显式 FROM_UNIXTIME）
        limit: 全量取数上限
        where: 可选全局 where 子句
    """
    table: str
    columns: Sequence[Union[str, Dict[str, Any]]]
    time_col: Optional[str] = None
    time_type: str = 'string'
    limit: int = 10_000
    where: Optional[str] = None

    def __post_init__(self):
        # 自动把自己注入模块级上下文，让后续构造的 Chart 在 __post_init__ 里
        # 能查到当前 Source 的 columns 类型，避免 double 裸列被启发式误判为分类列。
        # 利用 Python "先求实参 → 再调 Spec.__init__" 的求值顺序：
        # spec 文件里 source 永远比 chart 早实例化，因此此处注入时机正确。
        global _LATEST_SOURCE
        _LATEST_SOURCE = self

        # ── C3 软告警：columns 缺 type 字段时，scatter/数值列豁免将退化 ──
        # 设计动机（与 SKILL.md 反例 13 对齐）：
        #   _is_numeric_column 仅在 columns 元素是 {name,type,...} dict 时才能命中数值类型
        #   并撤销"裸列名→分类列"的保守误判。如果 LLM 只写 columns=['a','b','c']（纯 str），
        #   ⑪ scatter 形态硬契约会强制要求 `* 1.0`/CASE 包装，报错文案易被误读为
        #   "dim 表达式写错了"，引导 LLM 去改 dim 而不是补 type。
        #   此处构造期打一行 stderr 软告警（不 raise，避免为单一 columns 缺 type 触发整轮重跑），
        #   让根因（column 缺 type）直接出现在控制台首行。
        try:
            has_any_dict_with_type = any(
                isinstance(c, dict) and 'name' in c and 'type' in c
                for c in self.columns
            )
            if self.columns and not has_any_dict_with_type:
                print(
                    f'⚠️  [DSL 软告警] Source.columns 全部为纯字符串（缺 type 字段），'
                    f'scatter/数值列豁免将退化为文本启发式：裸数值列（如 double/decimal）'
                    f'会被误判为分类列，触发 ⑪ scatter 硬契约误报。\n'
                    f'  ✅ 建议改为 dict 形态：columns=[{{"name":"col","type":"double"}}, ...]'
                    f'（type 取自 SKILL.md 表 schema 的真实类型，整列抄全）',
                    file=_sys.stderr,
                )
        except Exception:
            pass

    def column_names(self) -> List[str]:
        out: List[str] = []
        for c in self.columns:
            if isinstance(c, str):
                out.append(c)
            elif isinstance(c, dict) and 'name' in c:
                out.append(c['name'])
            else:
                raise ValueError(f'[DSL] Source.columns 元素必须是 str 或 {{name,...}} dict，得到: {c!r}')
        return out

    def column_types(self) -> Dict[str, str]:
        """返回 {列名: 类型小写串}，仅对 dict 形态的元素有效。

        runner 真正读取 csv 时会做更精确的类型推断；这里仅用于 DSL 构造期
        的"裸列名→数值列"豁免（消除 `* 1.0` 咒语）。
        """
        out: Dict[str, str] = {}
        for c in self.columns:
            if isinstance(c, dict) and 'name' in c and 'type' in c:
                out[c['name']] = str(c['type']).lower().strip()
        return out


# 模块级"最近构造的 Source"上下文。
# 设计动机：Chart.__post_init__ 单独构造时拿不到 Source，只能用文本启发式，
#   把 double 裸列名误判为分类列，逼用户写 `col * 1.0` 这种"咒语"。
#   利用 Python 求值顺序"先构造 Source 实参 → 再构造 Chart 实参 → 最后调 Spec.__init__"，
#   让 Source.__post_init__ 自动把自己注入此 context，Chart 启发式即可在裁定
#   "裸列是否分类"时先查 columns 类型，命中数值类型直接放行。
#   多 Spec 共存时以"最近构造的 Source"为准（实际场景一个进程只跑一个 spec）。
_LATEST_SOURCE: Optional['Source'] = None


def _current_source() -> Optional['Source']:
    return _LATEST_SOURCE


# 视为"数值列"的类型集合（覆盖 Spark/Hive/Presto/MySQL/PG/Iceberg 常见命名）。
# 命中即可在 scatter 启发式中豁免（撤销"裸列名 → 分类列"的保守误判）。
_NUMERIC_TYPE_PREFIXES = (
    'tinyint', 'smallint', 'int', 'integer', 'bigint',
    'float', 'double', 'real', 'decimal', 'numeric',
    'long', 'short', 'byte',
)


def _is_numeric_column(col: str) -> bool:
    """查询当前 _LATEST_SOURCE 内 column 类型，命中数值类型返回 True；
    若没有 source 上下文 / column 类型未声明，返回 False（保守降级到文本启发式）。
    """
    s = _current_source()
    if s is None:
        return False
    types = s.column_types()
    t = types.get(col, '')
    if not t:
        return False
    return any(t.startswith(p) for p in _NUMERIC_TYPE_PREFIXES)


# ────────────────────────────────────────────────────────────────────────
# 类型规范化：把 source.columns 各种方言的类型名 → Dim.col_type 枚举值
# ────────────────────────────────────────────────────────────────────────
# 支持的真实方言（Iceberg / Delta / Spark / Hive / ClickHouse / Presto / MySQL / PG）：
#   - date / date32                                     → 'date'
#   - timestamp / timestamp(N) / timestamp_tz(N)
#     timestamp_ntz / timestamp_ltz / datetime / datetime(N) → 'timestamp'
#   - 其它                                              → ''（不回填，沿用默认 string）
# 注意：数值型 Unix 秒/毫秒不会按列名启发式自动归一，需在 raw_sql 中显式 FROM_UNIXTIME。
_TIMESTAMP_TYPE_PREFIXES = (
    'timestamp', 'datetime',  # spark/iceberg/hive 主流
)
_DATE_TYPE_PREFIXES = ('date',)
def _normalize_col_type(raw_type: str) -> str:
    """把 source.columns 的真实类型字符串映射到 Dim.col_type 四值之一。

    返回 '' 表示无法归一（保持调用方原默认值，不污染）。
    """
    if not raw_type:
        return ''
    t = str(raw_type).lower().strip()
    # 去掉精度后缀：timestamp(6) → timestamp，varchar(255) → varchar
    import re as _re_n
    t_base = _re_n.sub(r'\s*\(.*?\)\s*', '', t).strip()
    # timestamp 系列：timestamp / timestamp_tz / timestamp_ntz / timestamp_ltz / datetime
    if any(t_base.startswith(p) for p in _TIMESTAMP_TYPE_PREFIXES):
        return 'timestamp'
    # date 系列：date / date32
    if any(t_base.startswith(p) for p in _DATE_TYPE_PREFIXES):
        return 'date'
    return ''


def source(table: str, columns: Sequence[Union[str, Dict[str, Any]]], **kw) -> Source:
    return Source(table=table, columns=list(columns), **kw)


# ===== Chart：统一图表抽象（L3 核心） =====

@dataclass
class Chart:
    """单个图表组件（L3 统一抽象）。

    必填：
        kind:    图表类型，∈ SUPPORTED_KINDS
        title:   卡片标题

    数据描述（统一为 dims + metrics）：
        dims:    维度列表（List[Dim] 或 List[str] 自动包装）
        metrics: 度量列表（List[Metric] 或 List[str] 自动包装）

    数据形态自动识别（runner 内部按 kind 派发）：
        - series   ：单 dim + n metrics（line/bar/pie/funnel/radar）
        - point    ：散点 scatter，dims[0]→x，metrics[0]→y，dims[1?]→group
        - matrix   ：双 dim + 1 metric（heatmap/sankey/graph）
        - hierarchy：多 dim path + 1 metric（treemap/sunburst）
        - kpi_like ：单 metric（gauge）
        - role     ：角色化 metrics（candlestick: o/c/l/h；boxplot: value+group）
        - table    ：列出 dims（直接展示）

    渲染控制：
        span:        占用列数（1~grid_columns）；None=由 runner 按形状偏好自动决定（推荐）
        emoji:       标题前的 emoji
        order_by:    排序键（'-SUM(sales)' 倒序，'name' 升序，None 默认）
        limit:       结果行数上限（自动 TopN+Others 防偏态）
        stacked:     堆叠（bar/line）
        dual_axis:   双轴 metric 索引数组（[1] 表示第 2 个 metric 走右轴）
        smooth:      折线平滑

    高级：
        extras:      透传给前端 echarts 的额外配置（任意 dict）
        slot_key:    SLOT 键，默认从 title 派生
        raw_sql:     ⚠️ 逃生口
        slot_columns: raw_sql 模式下显式列序
        escape_hatch: True 时允许 raw_sql
    """
    kind: str
    title: str

    # —— 统一数据描述 ——
    dims: List[Union[Dim, str]] = field(default_factory=list)
    metrics: List[Union[Metric, str]] = field(default_factory=list)

    # —— 渲染控制 ——
    span: Optional[int] = None  # None=runner 按形状偏好自动决定
    emoji: str = ''
    slot_key: Optional[str] = None
    order_by: Optional[str] = None
    limit: Optional[int] = None
    stacked: bool = False
    dual_axis: Optional[List[int]] = None
    smooth: bool = True

    # —— 入库协议字段 ——
    refresh_interval: Optional[int] = None  # 秒；None=runner 按 kind 分级推断

    # —— 透传 / 逃生口 ——
    extras: Dict[str, Any] = field(default_factory=dict)
    raw_sql: Optional[str] = None
    slot_columns: Optional[List[str]] = None
    escape_hatch: bool = False

    # —— Spec 级集中预检 ——
    # chart(...) 工厂默认延迟非 raw_sql 契约错误到 Spec.__post_init__ 汇总抛出，
    # 避免一次只暴露一个图表错误导致反复重写；直接调用 Chart(...) 仍保持 fail-fast。
    _defer_validation: bool = field(default=False, repr=False, compare=False)
    _validation_errors: List[str] = field(default_factory=list, init=False, repr=False, compare=False)

    SUPPORTED_KINDS = (
        'line', 'bar', 'pie', 'scatter', 'radar', 'funnel', 'gauge',
        'heatmap', 'candlestick', 'treemap', 'sankey', 'boxplot',
        'sunburst', 'graph', 'parallel', 'table',
    )

    # —— 图表契约表（kind → 形状/类型/角色/语义约束）——
    # 把 runner 14 处 raise ValueError(f'[Runner] xxx') 一次性前置到 DSL 构造期。
    # 字段：
    #   dims:    (min, max, '说明')        max=None 表示不限
    #   metrics: (min, max, '说明')
    #   metric_roles: 必填角色集合（candlestick: open/close/low/high）
    #   value_must_be_row_level: True → metrics[0].expr 不能包含聚合（boxplot）
    _CONTRACTS = {
        'line':        {'dims': (1, 2, '分组维(+可选 group)'),  'metrics': (1, None, '≥1 个度量')},
        'bar':         {'dims': (1, 2, '分组维(+可选 group)'),  'metrics': (1, None, '≥1 个度量')},
        'pie':         {'dims': (1, 1, '分组维'),               'metrics': (1, 1, '单度量')},
        # sampling_rule（数据保真硬契约，构造期 raise）：
        #   'limit_requires_order_by'  ：行级模式下 c.limit 必须配 c.order_by（否则远端无序抽稀失真）
        #   'must_aggregate_or_limit'  ：dims 必须含聚合表达式 或 c.limit ≤ 上限（否则爆数据）
        #   'edge_mode_needs_limit'    ：边模式（dims≥2）必须 c.limit（否则边数失控）
        # cardinality_hint：仅文档/报错文案用，不参与构造期校验（执行期由 runner 软兜底）
        'scatter':     {'dims': (1, 2, 'x 轴(+可选色标)'),      'metrics': (1, 1, 'y 轴'),
                        'sampling_rule': 'limit_requires_order_by',
                        'cardinality_hint': '行级模式 limit 必配 order_by；大数据量请用 CASE WHEN 分桶聚合'},
        'radar':       {'dims': (1, 1, '分组维'),               'metrics': (3, None, '≥3 个度量轴')},
        'funnel':      {'dims': (0, 0, '不需要 dims'),          'metrics': (2, None, '每个 metric 一个阶段')},
        'gauge':       {'dims': (0, 0, '不需要 dims'),          'metrics': (1, 1, '单度量')},
        'heatmap':     {'dims': (2, 2, 'x×y'),                  'metrics': (1, 1, '单度量值'),
                        'cardinality_hint': '建议两维基数 ≤ 30（runner 在 X×Y > 900 时自动按各自 Top30 截断+软告警）'},
        'candlestick': {'dims': (1, 1, '时间轴'),               'metrics': (4, 4, '4 个角色'),
                        'metric_roles': {'open', 'close', 'low', 'high'}},
        'treemap':     {'dims': (1, None, '层级路径'),          'metrics': (1, 1, '单度量值'),
                        'cardinality_hint': '单层 >100 类目时 runner 自动取 Top50（避免基数爆炸）'},
        'sunburst':    {'dims': (1, None, '层级路径'),          'metrics': (1, 1, '单度量值'),
                        'cardinality_hint': '单层 >100 类目时 runner 自动取 Top50；多层每父 Top12（level_limit）'},
        'sankey':      {'dims': (2, 2, 'source/target'),        'metrics': (1, 1, '权重')},
        'boxplot':     {'dims': (1, 1, '分组维'),               'metrics': (1, 1, '值列(行级表达式)'),
                        'value_must_be_row_level': True},
        'graph':       {'dims': (1, 2, '节点 或 source/target'),'metrics': (0, 1, '边模式权重'),
                        'sampling_rule': 'edge_mode_needs_limit',
                        'cardinality_hint': '边模式建议 limit ≤ 30，否则关系图退化为毛球'},
        'parallel':    {'dims': (3, None, '前 N-1 轴 + 最后分类'),'metrics': (0, 0, 'parallel 不要 metrics'),
                        'sampling_rule': 'must_aggregate_or_limit',
                        'cardinality_hint': '必须按业务维度聚合（前 N-1 轴用 SUM/AVG/...）；分类维基数建议 ≤ 20'},
        'table':       {'dims': (1, None, '明细列（无聚合时 runner 自动 LIMIT 50；聚合后>500 行截 50+软告警）'),
                        'metrics': (0, None, '可选聚合列'),
                        'sampling_rule': 'limit_requires_order_by',
                        'cardinality_hint': '显式 limit 必配 order_by；推荐"维度聚合 + order_by"取 Top50 而非粗暴截明细'},
    }

    def __post_init__(self):
        if self.kind not in self.SUPPORTED_KINDS:
            # 治本：给出常见误用 → 正确入口的指路文案，避免 LLM 反复换 kind 试错
            _GUIDE = {
                'kpi':     'KPI 取数请用 `kpi(expr, label, prefix=, format=, from_sql=...)` 工厂，会合并到 Spec.kpis 一次性执行；KPI 不是 Chart kind',
                'compare': '同环比请用 `compare(title=..., dim=time_dim(...), metric=metric(...), kinds=["mom"|"yoy"|"wow"])`；如必须 raw_sql 自算 LAG 则用 kind="line" + 三列 [time, curr, prev_pct]',
                'kanban':  '看板顶层是 `Spec(...)`，不是 Chart kind',
                'card':    '"card" 不是 Chart kind；KPI 卡片走 `kpi(...)`，文本/数值卡片走 `kind="gauge"` 或自定义 SELECT + `kind="table"`',
                'metric':  '"metric" 不是 Chart kind；度量定义用 `metric(expr, label=, ...)` 喂给 chart/kpi',
                'number':  '单值卡片用 `kpi(...)` 进 Spec.kpis；不要 chart(kind="number")',
                'text':    '"text" 不是 Chart kind；纯文本说明放 Spec.subtitle',
                'map':     '当前 16 种 kind 不含 map；地理可用 `heatmap`（2D）或 `scatter`（经纬度散点）替代',
                'area':    '面积图用 `chart(kind="line", stacked=True, ...)`',
                'donut':   '环图用 `chart(kind="pie", ...)`（前端样式可走 extras 传 echarts radius）',
                'column':  '柱状图请用 `kind="bar"`',
                'kde':     '密度估计当前不支持，用 `histogram` 思路：raw_sql + CASE WHEN 分桶 + `kind="bar"`',
                'histogram': 'histogram 用 raw_sql + CASE WHEN 分桶 + `kind="bar"`',
            }
            tip = _GUIDE.get(str(self.kind).lower(), '')
            extra = f'\n  💡 {tip}' if tip else ''
            raise ValueError(
                f'[DSL] Chart.kind 必须 ∈ {self.SUPPORTED_KINDS}，得到: {self.kind!r}{extra}'
            )
        if self.span is not None and self.span < 1:
            raise ValueError(f'[DSL] Chart.span 必须 ≥ 1 或为 None，得到: {self.span}')

        # 字符串自动包装为 Dim/Metric
        self.dims = [d if isinstance(d, Dim) else Dim(expr=str(d)) for d in (self.dims or [])]
        self.metrics = [m if isinstance(m, Metric) else Metric(expr=str(m)) for m in (self.metrics or [])]

        # raw_sql 校验
        # 治本：LLM 一旦显式写了 raw_sql=...，逃生口意图已表达，无需再要求重复声明
        # escape_hatch=True。这里改为「自动补齐」（完全静默），消灭一整轮"忘写
        # escape_hatch 重跑"的返工。slot_columns 仍硬性要求（列序契约无法默认推
        # 断，错了静默乱位更危险）。
        # 🛑 故意不打印任何提示：[DSL] 阶段输出会落在 runner 启动前的 stdout 顶部，
        #    LLM 模糊匹配 SKILL.md 的「⚠️ [软告警] 原样抄入」契约时会把这条带进
        #    Step E 概览，对终端用户毫无价值（属开发者自查项）。教育靠 SKILL.md
        #    与 raw_sql(...) 工厂的存在，不靠 runtime 唠叨。
        if self.raw_sql and not self.escape_hatch:
            object.__setattr__(self, 'escape_hatch', True)
        if self.raw_sql and not self.slot_columns:
            raise ValueError(
                f'[DSL] Chart "{self.title}" 使用 raw_sql 必须同时指定 slot_columns=[...]'
            )
        # raw_sql 归一化（两步走）：
        #   1) FROM/JOIN/USING/, 后引号包标识符 → 反引号（远端 PARSE_SYNTAX_ERROR Top1 兜底）
        #   2) 剩余双引号字面量 → 单引号（DuckDB Binder 列名假装陷阱）
        # 顺序关键：标识符纠偏必须先于字面量归一化，否则 "tbl" 已被治成 'tbl' 后无法回头识别
        if self.raw_sql:
            self.raw_sql = _normalize_raw_sql_identifiers(
                self.raw_sql, ctx=f'Chart.raw_sql title={self.title!r}'
            )
            self.raw_sql = _normalize_sql_string_literals(
                self.raw_sql, ctx=f'Chart.raw_sql title={self.title!r}'
            )

        # —— 契约校验（仅非 raw_sql 模式）：把 runner 的形状/角色/语义错误前置到这里 ——
        if not self.raw_sql:
            try:
                self._check_contract()
            except ValueError as ex:
                if self._defer_validation:
                    self._validation_errors.append(str(ex))
                else:
                    raise

        # slot_key 默认派生（英文/数字/下划线 title 直接 slug；中文等不可读字符 → 留空，
        # 交由 Spec.__post_init__ 统一按 {kind}_{n} 编号，保证 key 全部为人类可读英文）
        # slug 残渣 < 3 字符（如 '7' / 'k'）也视作不可读，避免出现 7_line / k_candlestick 这类无语义 key
        if self.slot_key is None:
            import re as _re
            base = _re.sub(r'[^a-zA-Z0-9_]+', '_', self.title.lower()).strip('_')
            if base and len(base) >= 3:
                self.slot_key = f'{base[:24]}_{self.kind}'
            # else: 留 None，让 Spec 统一分配 {kind}_{n}（避免不可读哈希前缀）

    # ----------------------------------------------------------------------
    # 契约校验：把 runner 的 14 处形状/角色/语义错误统一前置到 DSL 构造期
    # ----------------------------------------------------------------------
    def _known_select_aliases(self) -> Optional[set]:
        """返回本图 SELECT 实际可能的输出别名集合（与 runner 各 _ad_* 路径严格一致）。

        返回 None 表示该 kind 不做别名校验（比如 raw_sql / 多分支图表）。
        命名规则与 runner 中 _dim_sql / _metric_alias_of / 各 _ad_* 内的硬编码完全对齐：
          - 普通 dim：alias 优先；否则裸列名 / 时间维派生 `<col>_<gran>` / 表达式派生 _metric_alias
          - metric ：alias 优先；否则 _metric_alias(expr)
          - kind 专属硬编码：scatter→x/y/category；compare/heatmap/sankey/candlestick/...
        """
        import re as _re_a

        def _bare_alias(expr: str) -> str:
            s = expr.strip().strip('`').strip('"')
            if _re_a.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', s):
                return s
            # 与 runner._metric_alias 的兜底分支保持一致：snake_case 化、去纯数字片段
            cleaned = _re_a.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')
            parts = [p for p in cleaned.split('_') if p and not p.isdigit()]
            return '_'.join(parts) or 'metric'

        def _dim_alias(d: Dim) -> str:
            if d.alias:
                return d.alias
            if d.is_time:
                return f'{d.expr.strip()}_{d.granularity}'
            return _bare_alias(d.expr)

        def _metric_simple_alias(m: Metric) -> str:
            # 简化版的 runner._metric_alias（仅做"够用"的别名预测，复杂分支统一回退裸前缀）。
            if m.alias:
                return m.alias
            s = (m.expr or '').strip()
            mm = _re_a.match(
                r'^(?P<f>SUM|AVG|COUNT|MIN|MAX|FIRST|LAST)\s*\(\s*(?:DISTINCT\s+)?(?P<c>[^)]+?)\s*\)$',
                s, flags=_re_a.IGNORECASE,
            )
            if mm:
                f = mm.group('f').lower()
                c = mm.group('c').strip().strip('`').strip('"')
                if c == '*':
                    return f'{f}_count'
                if _re_a.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', c):
                    distinct = bool(_re_a.search(r'DISTINCT', s, _re_a.IGNORECASE))
                    return f'{f}_distinct_{c}' if distinct else f'{f}_{c}'
            return _bare_alias(s)

        # ── kind 专属硬编码（与 runner 各 _ad_* 路径完全一致）──
        if self.kind == 'scatter':
            out = {'x', 'y'}
            if len(self.dims) >= 2:
                out.add('category')
            return out
        if self.kind == 'sankey':
            return {'source', 'target', 'value'}
        if self.kind == 'heatmap':
            # runner._ad_heatmap 不消费用户 order_by，且实际 SELECT 列为 dim/metric 派生别名；跳过校验。
            return None
        if self.kind == 'candlestick':
            # runner._ad_candle 固定输出 date/open/close/low/high，且固定 ORDER BY date。
            return {'date', 'open', 'close', 'low', 'high'}
        if self.kind == 'graph':
            # 节点模式 / 边模式 alias 不固定，跳过校验
            return None
        if self.kind in ('treemap', 'sunburst'):
            # runner 输出 name/value/(parent)，不消费用户 order_by；跳过校验避免误报。
            return None
        if self.kind == 'parallel':
            # parallel 不走 ORDER BY 远端，跳过
            return None

        # ── 通用：line/bar/pie/radar/funnel/gauge/boxplot/table ──
        out = set()
        for d in self.dims:
            out.add(_dim_alias(d))
        for m in self.metrics:
            out.add(m.alias or _metric_simple_alias(m))
        return out or None

    def _check_contract(self):
        ct = self._CONTRACTS.get(self.kind)
        if not ct:
            return

        # ① dims 元素类型必须是 Dim（runner._dim_sql 才不会炸）
        for i, d in enumerate(self.dims):
            if not isinstance(d, Dim):
                raise ValueError(
                    f'[DSL] Chart "{self.title}" dims[{i}] 必须是 Dim 实例，'
                    f'得到 {type(d).__name__}（裸字符串会自动 wrap，但 Metric 对象不允许塞进 dims）'
                )
        # ② metrics 元素类型必须是 Metric
        for i, m in enumerate(self.metrics):
            if not isinstance(m, Metric):
                raise ValueError(
                    f'[DSL] Chart "{self.title}" metrics[{i}] 必须是 Metric 实例，'
                    f'得到 {type(m).__name__}'
                )
        # ③ dims 数量
        dmin, dmax, dhelp = ct['dims']
        if len(self.dims) < dmin or (dmax is not None and len(self.dims) > dmax):
            raise ValueError(
                f'[DSL] Chart "{self.title}" (kind={self.kind}) 需要 dims '
                f'数量 ∈ [{dmin}, {dmax if dmax is not None else "∞"}]（{dhelp}），实际 {len(self.dims)}'
            )
        # ④ metrics 数量
        mmin, mmax, mhelp = ct['metrics']
        if len(self.metrics) < mmin or (mmax is not None and len(self.metrics) > mmax):
            raise ValueError(
                f'[DSL] Chart "{self.title}" (kind={self.kind}) 需要 metrics '
                f'数量 ∈ [{mmin}, {mmax if mmax is not None else "∞"}]（{mhelp}），实际 {len(self.metrics)}'
            )
        # ⑤ 必填角色（candlestick: open/close/low/high）
        need_roles = ct.get('metric_roles')
        if need_roles:
            actual = {m.role for m in self.metrics if m.role}
            miss = need_roles - actual
            if miss:
                raise ValueError(
                    f'[DSL] Chart "{self.title}" (kind={self.kind}) 缺少角色 metrics：{sorted(miss)}。'
                    f'示例：metric("MIN(price)", role="low")'
                )
        # ⑤bis gauge 语义硬约束：必须有量程上限（否则前端无刻度参考，用户无法判断达成度）
        if self.kind == 'gauge' and self.metrics:
            if self.metrics[0].target is None:
                raise ValueError(
                    f'[DSL] Chart "{self.title}" (kind=gauge) 缺 metric.target。\n'
                    f'  原因：gauge 语义是"当前值 vs 目标值"，无 target 时前端只有指针无刻度，用户无法判断达成度。\n'
                    f'  ✅ 比率型 metric（如 SUM(x)*100.0/N）：target=100.0（百分比刻度）\n'
                    f'  ✅ 绝对值 metric（如 SUM(x)）：target=<用户目标数值>（如 100000）'
                )
        # ⑥ 语义陷阱：boxplot value 不能是聚合（runner 内部已对其做 percentile_approx）
        if ct.get('value_must_be_row_level') and self.metrics:
            import re as _re
            v_expr = self.metrics[0].expr
            if _re.search(r'\b(SUM|AVG|COUNT|MIN|MAX|PERCENTILE|STDDEV|VARIANCE)\s*\(', v_expr, _re.I):
                raise ValueError(
                    f'[DSL] Chart "{self.title}" (kind={self.kind}) metrics[0] 必须是行级数值表达式，'
                    f'不能是聚合：{v_expr!r}（boxplot 内部已对其做 percentile_approx 求五数概括，'
                    f'再喂聚合会退化成单点导致前端无数据）。\n'
                    f'  ✅ 行级例：metric("price") / metric("DATEDIFF(spark_safe_to_timestamp(end_time), spark_safe_to_timestamp(start_time))")\n'
                    f'  ✅ 若表无行级数值列，请改用 bar/heatmap 展示分类计数/占比'
                )

        # ⑦ 通用陷阱：dim 表达式不能含聚合（消除 scatter/bar/pie 等"GROUP BY 含聚合"返工）
        # 例外：parallel 的前 N-1 维允许聚合（按设计就是把聚合结果当轴值），最后一维必须是分类。
        import re as _re_dim
        agg_pat = _re_dim.compile(r'\b(SUM|AVG|COUNT|MIN|MAX|PERCENTILE|STDDEV|VARIANCE)\s*\(', _re_dim.I)
        for i, d in enumerate(self.dims):
            is_parallel_axis = (self.kind == 'parallel' and i < len(self.dims) - 1)
            is_table = (self.kind == 'table')  # table 允许 dim 含聚合作为列
            if is_parallel_axis or is_table:
                continue
            if agg_pat.search(d.expr):
                raise ValueError(
                    f'[DSL] Chart "{self.title}" (kind={self.kind}) dims[{i}].expr 不能含聚合函数：{d.expr!r}\n'
                    f'  原因：维度会进 GROUP BY，聚合表达式不能在 GROUP BY 中。\n'
                    f'  ✅ 应放到 metrics：metric("{d.expr}", label="...")\n'
                    f'  ✅ 若想按聚合结果分桶：dim("CASE WHEN ... THEN ... END", alias="bucket")'
                )

        # ⑧ order_by 防御：引用 dim 时必须是 alias（非聚合表达式）；引用 metric 别名时必须存在
        if self.order_by:
            import re as _re_ob
            ob_text = str(self.order_by).strip()
            ob_desc = ob_text.startswith('-') or bool(_re_ob.search(r'\s+DESC\s*$', ob_text, flags=_re_ob.I))
            ob_raw = ob_text.lstrip('-').strip()
            ob_raw = _re_ob.sub(r'\s+(ASC|DESC)\s*$', '', ob_raw, flags=_re_ob.I).strip()
            # 数字索引：必须在 dims+metrics 总数范围内
            if ob_raw.lstrip('+-').isdigit():
                idx = int(ob_raw.lstrip('+-'))
                total_cols = len(self.dims) + len(self.metrics)
                if total_cols and (idx < 0 or idx >= total_cols):
                    raise ValueError(
                        f'[DSL] Chart "{self.title}" order_by={self.order_by!r} 数字索引越界 '
                        f'（共 {total_cols} 列，合法范围 0..{total_cols - 1}）'
                    )
            # ⑧bis 数据保真：order_by 含聚合表达式（如 '-COUNT(order_id)'）→ Spark
            #   ORDER BY 子句不允许直接重复聚合函数。若该聚合表达式恰好等于某 metric.expr，
            #   自动重写为 SELECT 实际输出别名，消除"DSL 校验通过但远端 Column not found"返工。
            elif agg_pat.search(ob_raw):
                # 找出与 ob_raw 等价的 metric（按 expr 完全匹配，去除两端空白）
                norm_ob = ' '.join(ob_raw.split())
                hit_idx = -1
                hit_metric = None
                for i, m in enumerate(self.metrics):
                    if ' '.join(str(m.expr).split()) == norm_ob:
                        hit_idx = i
                        hit_metric = m
                        break
                if hit_metric is not None:
                    fixed_alias_by_kind = {
                        'scatter': {0: 'y'},
                        'sankey': {0: 'value'},
                    }
                    fixed_alias = fixed_alias_by_kind.get(self.kind, {}).get(hit_idx)
                    if fixed_alias:
                        new_alias = fixed_alias
                    else:
                        # 派生 alias（与 runner._metric_alias_of 同语义）
                        new_alias = (hit_metric.alias or '').strip()
                        if not new_alias:
                            # 与 runner 的 _metric_alias 派生规则一致：取聚合函数 + 列名片段
                            slug = _re_ob.sub(r'[^a-zA-Z0-9_]+', '_',
                                              str(hit_metric.expr).lower()).strip('_')
                            new_alias = (slug[:32] or 'metric').rstrip('_')
                            # 强制把 alias 写回 metric（确保 SELECT 也按此 alias 输出列）
                            try:
                                object.__setattr__(hit_metric, 'alias', new_alias)
                            except Exception:
                                pass
                    direction = '-' if ob_desc else ''
                    self.order_by = f'{direction}{new_alias}'
                    ob_raw = new_alias
                    import sys as _sys
                    print(f'⚠️  [DSL] Chart "{self.title}" order_by 含聚合表达式，'
                          f'已自动重写为实际输出别名: order_by={self.order_by!r} '
                          f'（远端 Spark ORDER BY 子句不允许直写聚合，必须引用 SELECT 别名）',
                          file=_sys.stderr)
                else:
                    raise ValueError(
                        f'[DSL] Chart "{self.title}" order_by={self.order_by!r} 含聚合函数但'
                        f'未在 metrics 中找到匹配项。\n'
                        f'  原因：远端 Spark ORDER BY 子句不允许直写聚合表达式。\n'
                        f'  ✅ 修法：给目标 metric 显式 alias，order_by 引用别名：\n'
                        f'      metric("{ob_raw}", alias="cnt") + order_by="-cnt"'
                    )

            # ⑧ter 别名硬校验：消除"order_by 引用了 SELECT 不输出的别名"返工
            # 设计动机：scatter/sankey 的 SELECT 输出别名硬编码为 `y`/`value`，
            #   与 metric.alias 无关；LLM 写 metric('SUM(volume)', alias='volume') +
            #   order_by='-volume' 会通过远端 Spark 时报 `Column volume not found`。
            #   构造期把每种 kind 的实际 SELECT 输出别名集合算出来，提前 raise。
            if not ob_raw.lstrip('+-').isdigit():
                known = self._known_select_aliases()
                if known is not None and ob_raw and ob_raw not in known:
                    hint = ''
                    if self.kind == 'scatter':
                        hint = '\n  ✅ scatter 排 y 值请写：order_by="-y"'
                    elif self.kind == 'sankey':
                        hint = '\n  ✅ sankey 排权重请写：order_by="-value"'
                    # label vs alias 陷阱指路：LLM 常把 label 当别名用；
                    # 若目标 metric 的 label 命中 ob_raw，直接告诉他补 alias= 即可
                    label_hint = ''
                    for _m in self.metrics:
                        if getattr(_m, 'label', None) == ob_raw and not getattr(_m, 'alias', None):
                            label_hint = (
                                f'\n  💡 metric(label={ob_raw!r}) 中 label 只是展示名，'
                                f'不是 SELECT 输出别名；补一个 alias={ob_raw!r} 即可让 order_by 引用生效。'
                            )
                            break
                    raise ValueError(
                        f'[DSL] Chart "{self.title}" (kind={self.kind}) order_by={self.order_by!r} '
                        f'引用了不存在的别名。\n'
                        f'  原因：本图 SELECT 实际输出别名为 {sorted(known)}，远端 ORDER BY 引用'
                        f'其它名称会触发 "Column not found"。\n'
                        f'  ✅ 修法：order_by 仅可使用上述别名之一（前缀 "-" 表降序）'
                        f'{hint}{label_hint}'
                    )

        # ⑨ 数据保真硬契约（sampling_rule）：构造期就拦截"会失真/会爆数据"的形态
        # 设计动机：远端 Spark 与本地 DuckDB/Pandas 都按 SQL 物理顺序输出，未配 order_by 的
        #   LIMIT N 等同于"随机抽 N 行"——散点云/明细表的极值与代表性样本会被静默丢弃。
        #   构造期 raise 比 runner 跑完 SQL 才发现快 10~60s，且报错信息直接指引怎么改。
        rule = ct.get('sampling_rule')
        if rule == 'limit_requires_order_by':
            # scatter / table 行级模式：c.limit 必须配 c.order_by
            # 例外：dims 中已含聚合表达式 → GROUP BY 自然收敛行数，无需额外 order_by
            has_agg_dim = any(
                agg_pat.search(d.expr) for d in self.dims
            ) if self.dims else False
            has_agg_metric = any(
                agg_pat.search(m.expr) for m in self.metrics
            ) if self.metrics else False
            if self.limit is not None and not self.order_by \
                    and not has_agg_dim and not has_agg_metric:
                raise ValueError(
                    f'[DSL] Chart "{self.title}" (kind={self.kind}) 行级模式下 '
                    f'limit={self.limit} 必须同时设置 order_by，否则远端 SQL 是 '
                    f'`LIMIT {self.limit}` 无序抽稀，会丢失极值与代表性样本。\n'
                    f'  ✅ 修法 A（推荐）：order_by="-y_metric" 取 Top{self.limit}\n'
                    f'  ✅ 修法 B（大数据）：用 CASE WHEN 把 dims 改成业务分桶 '
                    f'（runner 自动 GROUP BY，行数天然收敛）\n'
                    f'  ✅ 修法 C：去掉 limit，改用更粗的聚合维度（如年月/品类）'
                )
        elif rule == 'must_aggregate_or_limit':
            # parallel：必须按业务维度聚合（dims 含 SUM/AVG/...）或显式 limit ≤ 上限
            # 否则 50w 行原始记录直接送前端 echarts.parallel，浏览器必死
            has_agg_dim = any(agg_pat.search(d.expr) for d in self.dims)
            _MAX_LIMIT = 1000  # parallel/类似图的硬上限：超过此值视为"实质上没限制"
            if not has_agg_dim and (self.limit is None or self.limit > _MAX_LIMIT):
                raise ValueError(
                    f'[DSL] Chart "{self.title}" (kind={self.kind}) 必须按业务维度聚合，'
                    f'或显式设置 limit ≤ {_MAX_LIMIT}（当前 limit={self.limit}）。\n'
                    f'  原因：原始行数过万时 echarts.{self.kind} 会渲染卡死/浏览器崩溃。\n'
                    f'  ✅ 修法 A（推荐）：前 N-1 轴用聚合表达式，按最后一维分类聚合\n'
                    f'      dims=[\n'
                    f'        dim("AVG(metric_a)", alias="avg_a"),\n'
                    f'        dim("AVG(metric_b)", alias="avg_b"),\n'
                    f'        dim("category"),  # 最后一维必须是分类\n'
                    f'      ]\n'
                    f'  ✅ 修法 B：保持行级形态但显式 limit + order_by 取 Top500'
                )
        elif rule == 'edge_mode_needs_limit':
            # graph 边模式（dims≥2）：必须 limit，否则边数失控，关系图变毛球
            if len(self.dims) >= 2 and self.limit is None:
                raise ValueError(
                    f'[DSL] Chart "{self.title}" (kind={self.kind}) 边模式必须设置 limit，'
                    f'否则关系图边数失控会退化为毛球。\n'
                    f'  ✅ 推荐：limit=30, order_by="-value"（默认按权重 DESC 取 Top30 边）'
                )

        # ⑩ parallel 形态硬契约：前 N-1 维必须**全部**是聚合表达式（含 SUM/AVG/COUNT/MIN/MAX/...）
        # 设计动机：parallel 是"分类聚合后多维剖面图"，每条折线 = 一个分类（最后一维）的多维聚合值。
        #   如果前 N-1 维有任意一个不是聚合表达式（如 HOUR(time) / status / category 等行级表达式），
        #   GROUP BY 只对最后一维分组 → 该行级表达式既不在 GROUP BY 也不是聚合 → Spark/DuckDB 严格模式
        #   静默剔除该轴或返回空集，前端 echarts 拿到的只有表头无数据行 → 图表完全空白。
        #   上轮"订单驾驶舱 parallel_1 空白"的源头就是 dim("HOUR(...)") 与聚合 dim 混排。
        if self.kind == 'parallel' and len(self.dims) >= 2:
            non_agg_axes = []
            for i, d in enumerate(self.dims[:-1]):
                if not agg_pat.search(d.expr):
                    non_agg_axes.append((i, d.expr))
            if non_agg_axes:
                bad_list = '; '.join(f'dims[{i}]={expr!r}' for i, expr in non_agg_axes)
                raise ValueError(
                    f'[DSL] Chart "{self.title}" (kind=parallel) 前 N-1 个维度**必须全部是聚合表达式**，'
                    f'最后一维才是分类。检测到非聚合轴：{bad_list}\n'
                    f'  原因：parallel 按最后一维 GROUP BY，前 N-1 轴若不是聚合表达式，GROUP BY 既不包含'
                    f'它也不视作聚合，远端会静默剔除/返空 → 图表表头无数据行（完全空白）。\n'
                    f'  ✅ 行级表达式必须包成聚合：dim("HOUR(time)") → dim("AVG(HOUR(time))", alias="avg_hour")\n'
                    f'  ✅ 业务量/客户数：dim("COUNT(order_id)", alias="order_cnt")\n'
                    f'  ✅ 最后一维保持分类：dim("order_status", label="状态")'
                )

        # ⑪ scatter 形态硬契约：至少要有一个**数值轴**（聚合表达式 或 行级数值表达式），不能两轴都是分类。
        # 设计动机：scatter 的语义是"两个数值变量的分布关系"。echarts.scatter 默认 xAxis.type='value'
        #   （数值轴），传字符串类目 → NaN 或全部聚成竖线，散点图退化失去语义。
        #   常见误用：dim("order_status") 当 x 轴；正确做法是把分类换成数值（如 DATEDIFF(...)）
        #   或 CASE WHEN 业务分桶后的数值序号。
        if self.kind == 'scatter' and self.dims:
            import re as _re
            x_dim = self.dims[0]
            x_expr = (x_dim.expr or '').strip()
            # 启发式：含聚合 / 含数值运算符（DATEDIFF/HOUR/+/-/*/CASE WHEN ... THEN num）/纯数字 → 视为数值
            #         单纯裸列名（仅由字母/下划线/.组成）→ 视为分类（疑似失真）
            is_numeric_expr = bool(
                agg_pat.search(x_expr)
                or _re.search(
                    r'\b(DATEDIFF|DATE_DIFF|HOUR|MINUTE|SECOND|YEAR|MONTH|DAY|WEEK|UNIX_TIMESTAMP|'
                    r'TIMESTAMPDIFF|TIME_TO_SEC|LENGTH|SIZE|ABS|ROUND|CEIL|FLOOR|MOD|POWER|LOG|EXP|'
                    r'SQRT|CAST|TRY_CAST|CONVERT)\s*\(',
                    x_expr, _re.I,
                )
                or _re.search(r'[+\-*/]', x_expr)
                or _re.search(r'\bCASE\s+WHEN\b.+\bTHEN\s+-?\d', x_expr, _re.I | _re.S)
                or _re.fullmatch(r'-?\d+(\.\d+)?', x_expr)
            )
            looks_like_bare_column = bool(_re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', x_expr))
            # 若 Spec 已注入 source 上下文且裸列名命中数值类型 → 撤销"分类列"保守误判。
            # 设计动机：DSL 单看表达式文本无法感知列实际类型，会把 double 裸列误判为分类。
            #   通过 _SOURCE_CTX 拿到 Source.columns 的 type 字段后，命中数值类型直接放行，
            #   消除 LLM 必须写 `col * 1.0` 才能通过校验的"咒语"。
            if looks_like_bare_column and _is_numeric_column(x_expr):
                is_numeric_expr = True
            if looks_like_bare_column and not is_numeric_expr:
                raise ValueError(
                    f'[DSL] Chart "{self.title}" (kind=scatter) dims[0]={x_expr!r} 看起来是**分类列**'
                    f'（裸列名且非数值表达式）。\n'
                    f'  原因：echarts.scatter 默认 xAxis.type="value" 是数值轴，传字符串类目会 NaN '
                    f'或退化为单条竖线，散点图丧失"两个数值变量分布关系"的语义。\n'
                    f'  ✅ 修法 A（推荐·业务分桶）：用 CASE WHEN 把分类映射到数值序号\n'
                    f'      dim("CASE WHEN status=\'paid\' THEN 1 WHEN status=\'shipped\' THEN 2 ELSE 0 END",\n'
                    f'          alias="status_score")\n'
                    f'  ✅ 修法 B（数值列）：换成真正的数值列/聚合\n'
                    f'      dim("DATEDIFF(spark_safe_to_timestamp(approved_at), '
                    f'spark_safe_to_timestamp(purchase_at))", alias="approve_days")\n'
                    f'  ✅ 修法 C（不是真散点需求）：换 kind="bar" 做分类对比'
                )

        # ⑫ candlestick 角色硬契约：4 个角色 expr 不能"完全同源"（去除空白后字面相同）。
        # 设计动机：candlestick 的视觉表达 = 4 角色的差异（开盘 / 收盘 / 最低 / 最高）。
        #   如果 4 个 metric.expr 完全一样（如全是 COUNT(order_id)），那 4 个角色每行都相等，
        #   K 线在每个时间点退化为"一字"（开=收=高=低，无任何振幅），渲染等同于一条直线。
        #   这是用户拿没有价格序列的表硬套 K 线时的典型踩坑（如订单事实表 + 4×COUNT）。
        if self.kind == 'candlestick' and len(self.metrics) == 4:
            normalized = [' '.join(str(m.expr).split()).upper() for m in self.metrics]
            if len(set(normalized)) == 1:
                raise ValueError(
                    f'[DSL] Chart "{self.title}" (kind=candlestick) 4 个角色 metric 表达式完全相同：'
                    f'{normalized[0]!r}\n'
                    f'  原因：K 线的视觉语义来自 open/close/low/high 的差异，4 个 expr 一样会让每根 K 线'
                    f'退化为"一字"（开=收=高=低，无振幅），等同于一条直线。\n'
                    f'  ✅ 修法 A（有真实价格序列）：metric("MIN(price)", role="low") + '
                    f'metric("MAX(price)", role="high") + metric("FIRST(price)", role="open") 等\n'
                    f'  ✅ 修法 B（订单事实表无价格列）：用业务语义的不同聚合：\n'
                    f'      open  = COUNT(order_id)                        -- 当日订单数\n'
                    f'      close = SUM(CASE WHEN status=\'delivered\' THEN 1 ELSE 0 END)  -- 已交付数\n'
                    f'      low   = LEAST(COUNT(order_id), COUNT(DISTINCT customer_id))\n'
                    f'      high  = GREATEST(COUNT(order_id), COUNT(DISTINCT customer_id))\n'
                    f'  ✅ 修法 C（数据不适合）：换 kind="bar" 或 "line" 表达单一聚合走势'
                )


def chart(kind: str, title: str, **kw) -> Chart:
    """便捷工厂。

    形参误用护栏（治本：消除"chart 当作 raw_sql 用"的返工死循环）：
        * ``from_sql`` / ``sql``：chart() 只承载 DSL 声明式绑定（dims/metrics/order_by/limit/...），
          跨表 JOIN / 手写 SQL 请改用 ``raw_sql(title=..., sql=..., slot_columns=[...], kind=...)``；
          跨表 KPI 单值请改用 ``kpi(expr, label, from_sql='cat.db.t1 a JOIN cat.db.t2 b ON ...')``。
    """
    _CHART_NOT_ACCEPT = {'from_sql', 'sql'}
    bad = sorted(_CHART_NOT_ACCEPT & set(kw.keys()))
    if bad:
        raise ValueError(
            f'[DSL] chart(kind={kind!r}, title={title!r}) 不支持参数 {bad}。\n'
            f'  原因：chart() 只承载 DSL 声明式绑定（dims/metrics/order_by/limit/...），不接受手写 SQL。\n'
            f'  ✅ 跨表 JOIN / 手写 SELECT：改用 raw_sql(title=..., sql=..., slot_columns=[...], kind=...)。\n'
            f'  ✅ 跨表 KPI 单值：改用 kpi(expr, label, from_sql="cat.db.t1 a JOIN cat.db.t2 b ON ...")。'
        )
    kw.setdefault('_defer_validation', True)
    return Chart(kind=kind, title=title, **kw)


def raw_sql(title: str, sql: str, slot_columns: List[str], kind: str = 'table', **kw) -> Chart:
    """逃生口工厂。

    形参白名单（治本：消除 raw_sql ** 黑洞导致的 TypeError 返工）：
        title / sql / slot_columns / kind / span / emoji / order_by /
        limit / stacked / dual_axis / smooth / extras / refresh_interval
    误用 Metric 字段（format/suffix/prefix/target/normalize/role/from_sql）
    或 dims/metrics —— 一律构造期 raise，给出指路文案。
    """
    # —— 形参黑名单（按"误用类型"分组报错，让 LLM 一次到位）——
    _METRIC_FIELDS = {'format', 'suffix', 'prefix', 'target', 'normalize', 'role', 'from_sql'}
    _NOT_FOR_RAW_SQL = {'dims', 'metrics'}  # raw_sql 是手写 SELECT，不再走 DSL 字段

    bad_metric = sorted(_METRIC_FIELDS & set(kw.keys()))
    bad_struct = sorted(_NOT_FOR_RAW_SQL & set(kw.keys()))
    if bad_metric:
        raise ValueError(
            f'[DSL] raw_sql "{title}" 不支持参数 {bad_metric} —— 这些是 Metric 的字段，'
            f'raw_sql 模式下数值格式化必须写进 SELECT 表达式（如 `CAST(amount AS DECIMAL(18,2))`、'
            f'`CONCAT(ROUND(rate,1), \'%\')`）。如需 KPI 卡片样式（带 prefix/suffix/format），'
            f'改用 `kpi(expr, label, prefix=..., format=..., from_sql=...)`，runner 会编译为'
            f'标量子查询合并到 KPI batch SQL。'
        )
    if bad_struct:
        raise ValueError(
            f'[DSL] raw_sql "{title}" 不支持参数 {bad_struct} —— raw_sql 模式下'
            f'整段 SELECT 由你手写，框架不再用 dims/metrics 构造 SQL。slot_columns 已'
            f'承担列序契约。'
        )

    # —— kind 指路（在 Chart.__post_init__ 报错前先给"为什么 raw_sql 不能产 KPI/同环比"）——
    if kind == 'kpi':
        raise ValueError(
            f'[DSL] raw_sql "{title}" 不能产出 KPI（kind="kpi" 不在 Chart.SUPPORTED_KINDS 中）。'
            f'KPI 取数请用 `kpi(expr, label, prefix=, format=, from_sql="cat.db.t1 a JOIN cat.db.t2 b ON ...")`，'
            f'runner 会把 from_sql 编译为标量子查询，所有 KPI 仍合并到一条 SQL 一次性执行。'
        )
    if kind == 'compare':
        raise ValueError(
            f'[DSL] raw_sql "{title}" 不能产出同环比（kind="compare" 不在 Chart.SUPPORTED_KINDS 中）。'
            f'两种修法：① 优先 `compare(title=..., dim=time_dim(...), metric=metric(...), kinds=["mom"])`'
            f'（runner 自动 WITH 双层 + NULLIF 防除零）；② 必须 raw_sql 时改 `kind="line"`，SELECT 出'
            f'`[time, curr, prev_pct]` 三列（用 LAG 自算环比），slot_columns 同序，前端按多系列折线渲染。'
        )

    return Chart(
        kind=kind,
        title=title,
        raw_sql=sql,
        slot_columns=slot_columns,
        escape_hatch=True,
        **kw,
    )


# ===== Compare：同环比独立类型 =====

@dataclass
class Compare:
    """同环比图（独立类型，runner 自动 WITH 双层 + NULLIF 防除零）。

    Args:
        title:  卡片标题
        dim:    时间维度（必须是带 granularity 的 Dim）
        metric: 单度量（Metric 或 str）
        kinds:  ['mom'] / ['yoy'] / ['mom','yoy'] / ['wow']
        span:   卡片宽度；None=runner 按形状偏好自动决定（compare 默认走宽幅 4）
        emoji:  emoji
        slot_key: SLOT 键
    """
    title: str
    dim: Dim
    metric: Union[Metric, str]
    kinds: List[str] = field(default_factory=lambda: ['mom'])
    span: Optional[int] = None
    emoji: str = ''
    slot_key: Optional[str] = None
    refresh_interval: Optional[int] = None  # 秒；None=runner 按分级推断（同环比走 300）

    _ALLOWED = ('mom', 'yoy', 'wow')

    def __post_init__(self):
        if not isinstance(self.dim, Dim):
            raise ValueError(f'[DSL] Compare.dim 必须是 Dim 实例，得到: {type(self.dim).__name__}')
        if not self.dim.is_time:
            raise ValueError(f'[DSL] Compare.dim 必须是时间维度（granularity 不为 None）')
        for k in self.kinds:
            if k not in self._ALLOWED:
                raise ValueError(f'[DSL] Compare.kinds 元素必须 ∈ {self._ALLOWED}，得到: {k!r}')
        # 自动包装 metric
        if not isinstance(self.metric, Metric):
            self.metric = Metric(expr=str(self.metric))
        # ────────────────────────────────────────────────────────────────
        # Compare metric.from_sql 不支持告知（治本：消除"KPI 能用 from_sql，
        # 我以为 Compare 也能"的高频外推误用）
        # ────────────────────────────────────────────────────────────────
        # 背景：Metric.from_sql 是 KPI 专用字段（runner 编译为标量子查询合并到
        #       KPI batch SQL）。Compare 由 runner 编译成 `WITH ... FROM
        #       <Spec.source.table>` 双层 SQL，不读 metric.from_sql，会被静默
        #       丢弃 → 远端 Spark 报 column not found（如主表无 price 字段，
        #       而 LLM 写 `compare(metric=metric('SUM(oi.price)', from_sql=...))`）。
        # 行为：构造期 raise，文案给出修法 A（切主表）/ 修法 B（改 raw_sql + LAG）。
        _from_sql = (getattr(self.metric, 'from_sql', None) or '').strip()
        if _from_sql:
            raise ValueError(
                f'[DSL] Compare "{self.title}" 的 metric 传了 from_sql='
                f'`{_from_sql[:80]}{"..." if len(_from_sql) > 80 else ""}`，'
                f'但 compare(...) 不支持 from_sql / 跨表 JOIN —— 同环比 SQL 仅在 '
                f'Spec.source 主表上跑双层 WITH，metric.from_sql 会被静默丢弃，'
                f'远端 Spark 必报 column not found。\n'
                f'  说明：from_sql 是 KPI 专用字段（kpi(...) 跨表聚合），'
                f'compare/chart 类的 metric 都不读这个字段。\n'
                f'  修法 A（推荐，单表内同环比）：把 source 切到含目标列的表，'
                f'metric 改写为不带 from_sql 的纯聚合表达式（如 `SUM(price)`），'
                f'dim 用主表的时间列即可。\n'
                f'  修法 B（必须跨表的同环比）：删掉这个 compare(...)，改用 '
                f'raw_sql(title=..., sql=..., slot_columns=[...], kind=\'line\')'
                f'（内部自动 escape_hatch=True），在 SQL 里手写 '
                f'`LAG(...) OVER (ORDER BY month)` + JOIN + '
                f'`100*(curr-prev)/NULLIF(prev,0)` 计算环比；表名一律用反引号包裹的'
                f'完整三段式 `` `cat.db.t` ``，禁单/双引号。参考 '
                f'kanban_spec_example.py 第 7 节。'
            )
        if self.slot_key is None:
            import re as _re
            base = _re.sub(r'[^a-zA-Z0-9_]+', '_', self.title.lower()).strip('_')
            if base and len(base) >= 3:
                self.slot_key = f'{base[:24]}_compare'
            # else: 留 None，由 Spec.__post_init__ 按 compare_{n} 统一编号


def compare(title: str, dim: Dim, metric: Union[Metric, str],
            kinds: Optional[List[str]] = None, **kw) -> Compare:
    return Compare(
        title=title, dim=dim, metric=metric,
        kinds=list(kinds) if kinds else ['mom'], **kw,
    )


# ===== 顶层 Spec =====

@dataclass
class Spec:
    """看板顶层声明。LLM 在 spec 文件里只构造一个 Spec 实例。

    workspace_id：留空即可。wedatacli 会自动从凭据文件解析当前沙箱的 workspace。
    仅在用户明确要求写入到另一个工作空间时才显式传值。
    """
    title: str
    source: Source
    workspace_id: str = ''  # 留空 → wedatacli 内部自动注入
    kpis: List[Metric] = field(default_factory=list)
    charts: List[Union[Chart, Compare]] = field(default_factory=list)
    subtitle: str = ''
    resource_id: str = ''
    theme: str = 'retail'
    grid_columns: int = 4

    def __post_init__(self):
        if not self.title:
            raise ValueError('[DSL] Spec.title 不能为空')
        if not isinstance(self.source, Source):
            raise ValueError('[DSL] Spec.source 必须是 Source 实例')
        if not self.kpis and not self.charts:
            raise ValueError('[DSL] Spec.kpis 与 Spec.charts 不能同时为空')
        # KPI 校验：必须有 label
        for k in self.kpis:
            if not isinstance(k, Metric):
                raise ValueError(f'[DSL] Spec.kpis 元素必须是 Metric，得到: {type(k).__name__}')
            if not k.label:
                raise ValueError(f'[DSL] KPI Metric 必须设置 label（expr={k.expr}）')

        # ────────────────────────────────────────────────────────────────
        # 类型上下文自动传播：从 Source.columns 推断 Dim.col_type
        # ────────────────────────────────────────────────────────────────
        # 设计动机（消除 timestamp_tz / date 时间列的 4 轮典型返工）：
        #   1) 用户在 source(columns=[...]) 中已显式声明列类型（如 timestamp_tz(6)）
        #   2) 但 time_dim(col, gran) 的 col_type 默认硬编码 'string'，runner 无脑套
        #      spark_safe_to_timestamp 包装链 → DuckDB Binder Error
        #   3) 类型信息明明已经在 spec 里，却没传播到 Dim → 这是"信息断层"
        #
        # 修复策略（最小侵入、绝对兼容）：
        #   - 仅当 Dim.col_type 是默认值 'string'（即用户未显式覆盖）才回填
        #   - 仅对裸列名（_is_bare_col）的时间 Dim 生效，不影响表达式
        #   - 多源类型规范化（_normalize_col_type）：tz/ntz/ltz/(N) 等后缀统一映射
        #   - 同时挂 _column_type_map 到 Spec 上，供 builder lint 拿到列类型上下文
        #     做 DATEDIFF/YEAR/MONTH 等反模式校验的"类型豁免"
        col_type_map: Dict[str, str] = {}
        try:
            for c in self.source.columns:
                if isinstance(c, dict) and 'name' in c and 'type' in c:
                    norm = _normalize_col_type(str(c['type']))
                    if norm:
                        col_type_map[str(c['name'])] = norm
        except Exception:
            pass
        # 暴露给 runner / builder lint
        self._column_type_map = col_type_map

        if col_type_map:
            def _propagate(d: Optional['Dim']) -> None:
                """对裸列名时间 Dim：col_type 仍是默认 'string' 时回填真实类型。"""
                if d is None or not isinstance(d, Dim):
                    return
                if not d.is_time:
                    return
                if d.col_type != 'string':
                    return  # 用户已显式覆盖，尊重
                expr = (d.expr or '').strip().strip('`').strip('"')
                if not expr:
                    return
                # 仅对裸列名生效（表达式包装由用户自负）
                import re as _re_t
                if not _re_t.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', expr):
                    return
                real_type = col_type_map.get(expr)
                if real_type and real_type in Dim._TYPES:
                    # Dim 是 frozen dataclass，必须走 object.__setattr__
                    object.__setattr__(d, 'col_type', real_type)

            for c in self.charts:
                if isinstance(c, Chart):
                    for d in c.dims:
                        _propagate(d)
                elif isinstance(c, Compare):
                    _propagate(c.dim)

        # ────────────────────────────────────────────────────────────────
        # Spec 级集中预检：一次性暴露所有 chart 契约 / 窗口聚合结构错误
        # ────────────────────────────────────────────────────────────────
        # 背景：LLM 返工最耗时的模式不是"不会修"，而是 Chart(...) 在第一个错误处
        #       fail-fast，修完一个 scatter/table 后才暴露下一个同类问题。chart()
        #       工厂已把非 raw_sql 契约错误延迟到这里；本段汇总所有图，统一抛出。
        try:
            import re as _re_pre
            _problems: List[str] = []
            _agg_call_re = _re_pre.compile(
                r'\b(MIN|MAX|SUM|AVG|COUNT|PERCENTILE|PERCENTILE_APPROX|STDDEV|VARIANCE)\s*\(',
                _re_pre.IGNORECASE,
            )
            _nested_agg_re = _re_pre.compile(
                r'\b(MIN|MAX|SUM|AVG|COUNT|PERCENTILE|PERCENTILE_APPROX|STDDEV|VARIANCE)\s*\('
                r'[^)]*\b(MIN|MAX|SUM|AVG|COUNT|PERCENTILE|PERCENTILE_APPROX|STDDEV|VARIANCE)\s*\(',
                _re_pre.IGNORECASE,
            )
            _window_re = _re_pre.compile(
                r'\b(LAG|LEAD|ROW_NUMBER|RANK|DENSE_RANK|FIRST_VALUE|LAST_VALUE|NTILE|PERCENT_RANK|CUME_DIST)\s*\('
                r'|\bOVER\s*\(',
                _re_pre.IGNORECASE,
            )

            def _has_agg(expr: str) -> bool:
                return bool(_agg_call_re.search(expr or ''))

            def _collect_expr_problem(owner: str, expr: str) -> None:
                if not expr:
                    return
                if _nested_agg_re.search(expr):
                    _problems.append(
                        f'{owner}: 检测到嵌套聚合 `{expr}`。普通 DSL chart 会把 metric 放进同层 SELECT/GROUP BY，'
                        f'Spark/DuckDB 都不支持 AGG(AGG(...))；请改用 raw_sql + WITH 子查询先算内层聚合，'
                        f'外层再做窗口/累计/分位统计。'
                    )
                if _window_re.search(expr):
                    _problems.append(
                        f'{owner}: 检测到窗口函数 `{expr}`。普通 DSL metric/dim 不支持同层窗口表达式；'
                        f'累计趋势/移动排名/自算同环比请改用 raw_sql(kind="line"/"table")，'
                        f'采用 `WITH agg AS (...) SELECT ..., LAG/SUM(...) OVER (ORDER BY <agg_alias>) FROM agg` 双层结构。'
                    )

            def _collect_order_by_problem(c: Chart) -> None:
                """不依赖 _check_contract 完整跑完的 order_by 别名预检。"""
                if not c.order_by or c.raw_sql:
                    return
                ob_text = str(c.order_by).strip()
                ob_desc = ob_text.startswith('-') or bool(
                    _re_pre.search(r'\s+DESC\s*$', ob_text, flags=_re_pre.IGNORECASE)
                )
                ob_raw = ob_text.lstrip('-').strip()
                ob_raw = _re_pre.sub(
                    r'\s+(ASC|DESC)\s*$', '', ob_raw, flags=_re_pre.IGNORECASE
                ).strip()
                if not ob_raw or ob_raw.lstrip('+-').isdigit():
                    return
                if _agg_call_re.search(ob_raw):
                    norm_ob = ' '.join(ob_raw.split())
                    matched = any(
                        isinstance(m, Metric) and ' '.join(str(m.expr).split()) == norm_ob
                        for m in (c.metrics or [])
                    )
                    if matched:
                        return  # _check_contract 会按 kind 自动重写为实际输出别名
                    _problems.append(
                        f'[DSL] Chart "{c.title}" order_by={c.order_by!r} 含聚合函数但未在 metrics 中找到匹配项。'
                        f'请给目标 metric 显式 alias 并让 order_by 引用该 alias，或把 order_by 改为已有输出别名。'
                    )
                    return
                known = c._known_select_aliases()
                if known is not None and ob_raw not in known:
                    hint = ''
                    if c.kind == 'scatter':
                        hint = '；scatter 排 y 值请写 order_by="-y"'
                    elif c.kind == 'table':
                        hint = '；time_dim(col, gran) 输出别名是 `col_gran`，如 `date_day`'
                    elif c.kind == 'sankey':
                        hint = '；sankey 排权重请写 order_by="-value"'
                    # label vs alias 陷阱指路：若目标 metric 的 label 命中 ob_raw 且未显式 alias，补 alias= 即可
                    for _m in (c.metrics or []):
                        if isinstance(_m, Metric) and getattr(_m, 'label', None) == ob_raw and not getattr(_m, 'alias', None):
                            hint += (
                                f'；💡 metric(label={ob_raw!r}) 里 label 只是展示名，不是 SELECT 输出别名，'
                                f'补一个 alias={ob_raw!r} 即可让 order_by 引用生效'
                            )
                            break
                    _problems.append(
                        f'[DSL] Chart "{c.title}" (kind={c.kind}) order_by={c.order_by!r} 引用了不存在的别名。'
                        f'本图 SELECT 实际输出别名为 {sorted(known)}，order_by 只能引用这些别名{hint}。'
                    )

            for _ci, _c in enumerate(self.charts):
                if isinstance(_c, Chart):
                    for _msg in getattr(_c, '_validation_errors', []) or []:
                        _problems.append(_msg)
                    if not _c.raw_sql:
                        _contract_msg = ''
                        try:
                            _c._check_contract()
                        except ValueError as _ex:
                            _contract_msg = str(_ex)
                            if _contract_msg not in _problems:
                                _problems.append(_contract_msg)
                        if 'order_by=' not in _contract_msg:
                            _collect_order_by_problem(_c)
                        for _di, _d in enumerate(_c.dims):
                            if isinstance(_d, Dim):
                                _collect_expr_problem(f'Chart "{_c.title}" dims[{_di}]', _d.expr or '')
                        for _mi, _m in enumerate(_c.metrics):
                            if isinstance(_m, Metric):
                                _collect_expr_problem(f'Chart "{_c.title}" metrics[{_mi}]', _m.expr or '')
                        # scatter 不是气泡图：size 只能走 extras 透传，不能塞第 2/3 个 metric。
                        if _c.kind == 'scatter' and len(_c.metrics) == 1 and isinstance(_c.extras, dict):
                            _size_signals = {'symbolSize', 'symbol_size', 'sizeField', 'visualMap'}
                            if any(k in _c.extras for k in _size_signals) and not _has_agg(_c.metrics[0].expr):
                                # 合法透传，不做任何拦截；这里保留注释作为 spec 重写问题的代码锚点。
                                pass
                    else:
                        # raw_sql 会继续走 builder sqlSlots 全 lint；这里只做低成本列序空值兜底。
                        if not _c.slot_columns:
                            _problems.append(
                                f'[DSL] Chart "{_c.title}" 使用 raw_sql 必须同时指定非空 slot_columns=[...]，'
                                f'且顺序与 SELECT 输出列严格一致。'
                            )
                elif isinstance(_c, Compare):
                    if isinstance(_c.metric, Metric):
                        _collect_expr_problem(f'Compare "{_c.title}" metric', _c.metric.expr or '')
                    if isinstance(_c.dim, Dim):
                        _collect_expr_problem(f'Compare "{_c.title}" dim', _c.dim.expr or '')

            if _problems:
                _uniq: List[str] = []
                _seen_msg: set = set()
                for _p in _problems:
                    if _p not in _seen_msg:
                        _uniq.append(_p)
                        _seen_msg.add(_p)
                raise ValueError(
                    f'[DSL] Spec 全局契约预检失败（共 {len(_uniq)} 处）。'
                    f'请一次性修完下列所有问题后再重跑 build_kanban：\n'
                    + '\n\n'.join(f'{i+1}. {p}' for i, p in enumerate(_uniq))
                )
        except ValueError:
            raise
        except Exception:
            # 预检只增不减；意外异常不阻断原有构造路径。
            pass

        # slot_key 兜底分配 + 重复去重（两道防线）：
        # 1) Chart/Compare 在 __post_init__ 阶段对中文等不可读 title 留空 slot_key，
        #    由此处按全局 {kind}_{n} 编号，避免 c_<md5> 这类不可读 key。
        # 2) 不同 chart 的 title 经 slug 截断后碰撞到同一个 slot_key（例如「品类销售Top10」、
        #    「品类销量Top10」、「单品销售Top10」、「毛利Top10品类」slug 后都只剩 'top10'，
        #    派生出相同 'top10_bar'），多个 chart 共用一个 SQL slot 会导致只有第一个图
        #    渲染正确，其余 chart 数据被覆盖或为空。这里对重复 key 强制重命名，
        #    保留首次出现，后续同 key 改为 {kind}_{n}。
        _kind_counter: Dict[str, int] = {}
        _used_keys: set = set()
        # 第一遍：扫描已显式赋值且唯一的 slot_key（保留首次出现）
        _seen_first: set = set()
        for c in self.charts:
            sk = getattr(c, 'slot_key', None)
            if sk and sk not in _seen_first:
                _seen_first.add(sk)
                _used_keys.add(sk)
        # 第二遍：分配 / 去重
        _seen_now: set = set()
        for c in self.charts:
            kind_name = getattr(c, 'kind', None) or 'compare'
            sk = getattr(c, 'slot_key', None)
            need_rename = (not sk) or (sk in _seen_now)  # 空 OR 与前面已落地的重复
            if not need_rename:
                _seen_now.add(sk)
                continue
            # 兜底分配新 key
            n = _kind_counter.get(kind_name, 0) + 1
            candidate = f'{kind_name}_{n}'
            while candidate in _used_keys or candidate in _seen_now:
                n += 1
                candidate = f'{kind_name}_{n}'
            _kind_counter[kind_name] = n
            _used_keys.add(candidate)
            _seen_now.add(candidate)
            c.slot_key = candidate

        # ────────────────────────────────────────────────────────────────
        # Compare 主表列校验（消除「compare 跨表试错」的死亡螺旋）
        # ────────────────────────────────────────────────────────────────
        # 背景：compare(...) 由 runner 编译成 `WITH ... FROM <Spec.source.table>` 双层 SQL，
        #       不接受 raw_sql / from_sql / 跨表 JOIN（Compare 类没有 from_sql 字段）。
        #       LLM 真实返工链：source 主表 = orders（无 price 字段）→ 写
        #       `compare(metric=metric('SUM(i.price)'))` → runner 拼出
        #       `SELECT SUM(i.price) FROM orders` → 远端报 column not found / parse error。
        #       LLM 不知道这条限制，会陷入"换主表→raw_sql 引号错→再换主表"的循环。
        #
        # 校验策略（保守 + 0 误报）：
        #   1) 仅识别"带表别名"的列引用 `<alias>.<col>` 形态——这是 100% 跨表的铁证
        #      （主表度量永远不需要写 `t.col`，runner 在 SQL 里也不会引入别名）。
        #   2) 不识别"裸列名不在 source.columns"——避免误伤用户用 view / 列声明不全的场景。
        #   3) 仅当 source.columns 已声明（col_type_map 非空）时启用，否则放过。
        # ────────────────────────────────────────────────────────────────
        try:
            import re as _re_cmp
            # 排除 SQL 函数链式调用形态：func(.) 或 quoted "x.y" 等不算"表别名引用"
            # 这里只关心标识符形态：连续两个 ASCII 标识符之间夹一个点
            _alias_col_re = _re_cmp.compile(
                r'(?<![A-Za-z0-9_."`\'])'         # 左边界：不是标识符 / 引号
                r'([A-Za-z_][A-Za-z0-9_]*)'       # 表别名
                r'\.'
                r'([A-Za-z_][A-Za-z0-9_]*)'       # 列名
                r'(?![A-Za-z0-9_(])'              # 右边界：不是标识符开头、不是函数调用
            )
            for _c in self.charts:
                if not isinstance(_c, Compare):
                    continue
                _expr = ''
                if isinstance(_c.metric, Metric):
                    _expr = _c.metric.expr or ''
                else:
                    _expr = str(_c.metric) if _c.metric is not None else ''
                if not _expr:
                    continue
                # 抽出所有 `<alias>.<col>` 形态
                _hits = _alias_col_re.findall(_expr)
                if not _hits:
                    continue
                # 把表别名集合排重；列名顺序保留
                _aliases = sorted({h[0] for h in _hits})
                _cols = []
                _seen_col: set = set()
                for _, _col in _hits:
                    if _col not in _seen_col:
                        _cols.append(_col)
                        _seen_col.add(_col)
                _src_table = getattr(self.source, 'table', '') or '<unknown>'
                raise ValueError(
                    f'[DSL] Compare "{_c.title}" 的 metric 引用了带表别名的列 '
                    f'`{".".join([_aliases[0], _cols[0]])}`'
                    f'（共 {len(_hits)} 处：alias={_aliases}，cols={_cols}）。\n'
                    f'  原因：compare(...) 仅在 Spec.source 主表 `{_src_table}` 上跑同环比 SQL，'
                    f'不接受 raw_sql / from_sql / 跨表 JOIN，主表上下文里没有任何表别名。\n'
                    f'  修法 A（推荐，单表内同环比）：把 source 切到含上述列的表，metric 改写为不带别名的'
                    f'纯聚合表达式（如 `SUM(price)`），dim 用主表的时间列即可。\n'
                    f'  修法 B（必须跨表的同环比）：删掉这个 compare(...)，改用 raw_sql + chart(\'line\', '
                    f'escape_hatch=True, slot_columns=[...])，在 SQL 里手写 `LAG(...) OVER (ORDER BY month)` '
                    f'+ JOIN + `100*(curr-prev)/NULLIF(prev,0)` 计算环比；表名一律用反引号包裹的完整三段式 '
                    f'`` `cat.db.t` ``，禁单/双引号。参考 kanban_spec_example.py 第 7 节。'
                )
        except ValueError:
            raise
        except Exception:
            # 任何意外异常不阻断 Spec 构造（保守原则：校验只增不减）
            pass

        # ────────────────────────────────────────────────────────────────
        # 日期差方言前置校验（必须在"列引用存在性校验"之前执行）
        # ────────────────────────────────────────────────────────────────
        # 背景：LLM 写"剩余天数 / 超预计送达 / 履约延误"这类风险看板时，高频踩四种坑：
        #   ① DATEDIFF(DAY, start, end)        ← SQL Server / Presto 关键字风格三参
        #   ② DATE_DIFF('day', start, end)     ← Presto 字符串风格三参（builder lint 已查，但太晚）
        #   ③ DATE_DIFF(DAY, start, end)       ← Presto 关键字风格三参
        #   ④ DATE_DIFF(end, start)            ← 函数名拼错（Spark 是 DATEDIFF 没下划线）
        # 当前 runner / 远端 Spark 仅支持 Spark 两参 `DATEDIFF(end, start)`，前 4 种都会:
        #   - ①③ 走到"列引用存在性校验"被识别为"未声明列 DAY"，错误信息误导 LLM 反复改列名
        #   - ② 通过 DSL 但 builder lint 才报错，浪费一次取数往返
        #   - ④ 走到列引用校验报"未声明列 DATE_DIFF"，与列名拼错错误混淆
        # 这里直接前置拦截，错误文案带 canonical Spark 写法 + 风险看板模板，0 试错落地。
        # ────────────────────────────────────────────────────────────────
        try:
            import re as _re_dd

            # 三参数 DATEDIFF（关键字 DAY/MONTH/YEAR 等开头，无引号）—— 含 ②③①
            #   匹配 `DATEDIFF(DAY,` / `DATE_DIFF(MONTH,` / `DATE_DIFF('day',` 等
            #   注意必须用 (?: ... ) 非捕获组，且大小写不敏感
            _DD_3ARG_RE = _re_dd.compile(
                r'\bDATE_?DIFF\s*\(\s*'
                r"(?:'(?:day|month|year|week|hour|minute|second|quarter)'"  # 字符串风格 'day'
                r"|\"(?:day|month|year|week|hour|minute|second|quarter)\""  # 双引号风格 "day"
                r"|(?:DAY|MONTH|YEAR|WEEK|HOUR|MINUTE|SECOND|QUARTER))"      # 关键字风格 DAY
                r'\s*,',
                _re_dd.IGNORECASE,
            )
            # 函数名 DATE_DIFF（带下划线）—— 含 ④（任意参数数都是错的，Spark 函数名是 DATEDIFF）
            _DATE_DIFF_NAME_RE = _re_dd.compile(r'\bDATE_DIFF\s*\(', _re_dd.IGNORECASE)

            def _scan_date_diff_dialect(expr: str):
                """返回 (kind, sample) 或 None。kind∈{'3arg','wrong_name'}。"""
                if not expr:
                    return None
                m3 = _DD_3ARG_RE.search(expr)
                if m3:
                    return ('3arg', m3.group(0))
                mn = _DATE_DIFF_NAME_RE.search(expr)
                if mn:
                    return ('wrong_name', mn.group(0))
                return None

            _dd_problems: List[str] = []  # 收集所有命中点

            # 收集所有 DSL 路径下的 expr（raw_sql 跳过——逃生口走 builder lint）
            for _i, _k in enumerate(self.kpis):
                if not isinstance(_k, Metric):
                    continue
                if getattr(_k, 'from_sql', None):
                    # from_sql 是手写 JOIN/SELECT 片段，按 raw_sql 处理跳过
                    continue
                _hit = _scan_date_diff_dialect(_k.expr or '')
                if _hit:
                    _dd_problems.append(
                        f'  KPI #{_i+1} (label={_k.label!r}): expr=`{_k.expr}` → 命中 `{_hit[1]}` ({_hit[0]})'
                    )

            for _ci, _c in enumerate(self.charts):
                if isinstance(_c, Chart):
                    if _c.escape_hatch or _c.raw_sql:
                        continue
                    for _di, _d in enumerate(_c.dims):
                        if isinstance(_d, Dim):
                            _hit = _scan_date_diff_dialect(_d.expr or '')
                            if _hit:
                                _dd_problems.append(
                                    f'  Chart "{_c.title}" dims[{_di}]: expr=`{_d.expr}` → 命中 `{_hit[1]}` ({_hit[0]})'
                                )
                    for _mi, _m in enumerate(_c.metrics):
                        if isinstance(_m, Metric):
                            _hit = _scan_date_diff_dialect(_m.expr or '')
                            if _hit:
                                _dd_problems.append(
                                    f'  Chart "{_c.title}" metrics[{_mi}] (label={_m.label!r}): '
                                    f'expr=`{_m.expr}` → 命中 `{_hit[1]}` ({_hit[0]})'
                                )
                elif isinstance(_c, Compare):
                    if isinstance(_c.dim, Dim):
                        _hit = _scan_date_diff_dialect(_c.dim.expr or '')
                        if _hit:
                            _dd_problems.append(
                                f'  Compare "{_c.title}" dim: expr=`{_c.dim.expr}` → 命中 `{_hit[1]}` ({_hit[0]})'
                            )
                    if isinstance(_c.metric, Metric):
                        _hit = _scan_date_diff_dialect(_c.metric.expr or '')
                        if _hit:
                            _dd_problems.append(
                                f'  Compare "{_c.title}" metric: expr=`{_c.metric.expr}` → 命中 `{_hit[1]}` ({_hit[0]})'
                            )

            if _dd_problems:
                raise ValueError(
                    f'[DSL] 检测到非 Spark 日期差方言（共 {len(_dd_problems)} 处），远端 Spark 与本地 runner '
                    f'仅支持两参数写法 `DATEDIFF(end, start)`：\n'
                    + '\n'.join(_dd_problems) + '\n'
                    f'  ❌ 禁用形态（任一命中即报）：\n'
                    f'     • DATEDIFF(DAY, start, end)        ← SQL Server / Presto 关键字风格三参\n'
                    f'     • DATE_DIFF(\'day\', start, end)     ← Presto 字符串风格三参\n'
                    f'     • DATE_DIFF(DAY, start, end)       ← Presto 关键字风格三参\n'
                    f'     • DATE_DIFF(end, start)            ← 函数名拼错（Spark 函数名是 DATEDIFF，无下划线）\n'
                    f'  ✅ canonical Spark 写法（两参，返回 end-start 的天数差）：\n'
                    f'     DATEDIFF(end, start)\n'
                    f'  ✅ string 时间列先包 spark_safe_to_timestamp；timestamp/date 直接裸写；Unix 秒/毫秒先显式 FROM_UNIXTIME：\n'
                    f'     DATEDIFF(spark_safe_to_timestamp(order_delivered_at), spark_safe_to_timestamp(order_purchase_at))\n'
                    f'  ✅ 与"当前时间"对比（剩余天数 / 超时判断）：\n'
                    f'     DATEDIFF(spark_safe_to_timestamp(order_estimated_delivery_ts), CURRENT_TIMESTAMP)  AS remaining_days\n'
                    f'     -- 越小越紧急，order_by 用 \'remaining_days\'（升序）；\n'
                    f'     -- 历史数据集请用数据快照日代替 CURRENT_TIMESTAMP，避免历史订单全被判超时。\n'
                    f'  📚 风险看板完整模板见 kanban_spec_example.py 5.17 节「SLA / 履约风险看板」。'
                )
        except ValueError:
            raise
        except Exception:
            # 任何意外异常不阻断 Spec 构造（保守原则：校验只增不减）
            pass

        # ────────────────────────────────────────────────────────────────
        # 列引用存在性校验（消除「LLM 抄 example 字段名 / 拼错列名」幻觉）
        # ────────────────────────────────────────────────────────────────
        # 背景：LLM 写 spec 时最高频幻觉之一——把 kanban_spec_example.py 里的
        #       示例字段（amount/cost/qty/price/category/region 等）当默认字段直接抄到
        #       新表 spec 里，结果远端 Spark 报 `cannot resolve 'amount'`，看板出空集。
        #       DuckDB 本地体检在用户端是 stderr 报错，不直接显示在 LLM 上下文，导致
        #       LLM 反复"换表达式 / 加 CAST"瞎改，并不会想到"列根本不存在"。
        #
        # 校验策略（保守 + 0 误报）：
        #   1) 仅当 col_type_map 非空（即 source.columns 用 dict 形态完整声明 type）
        #      时启用——纯字符串 columns 视为 schema 不完整，跳过校验避免误伤。
        #   2) 仅校验 Chart.dims/metrics、Compare.dim/metric、Spec.kpis 这三处 DSL 表达式；
        #      raw_sql（escape_hatch=True）显式跳过——用户在 raw_sql 里写完整 SQL，
        #      可以引用任意伴随视图列 / 副表列，DSL 不应介入。
        #   3) 提取裸标识符前**先剥离单引号字符串字面量**（如 CASE WHEN status='paid'）。
        #   4) 排除 SQL 关键字 / 内置函数 / 类型字面量 / DSL helper 函数名。
        #   5) 排除带表别名的 `a.col` 形态（已被前面的 Compare 跨表校验或 raw_sql 覆盖）。
        #   6) 任何意外异常不阻断 Spec 构造。
        # ────────────────────────────────────────────────────────────────
        try:
            # 独立从 source.columns 收集所有声明列名（dict 形态全收；
            # 纯字符串形态视为 schema 不完整 → 跳过校验避免误伤）。
            # 不复用 col_type_map（它只对 timestamp/date 类型回填，
            # 不能代表"全部已声明列"）。
            _declared_cols: set = set()
            _all_dict = True
            for _c in self.source.columns:
                if isinstance(_c, dict) and 'name' in _c:
                    _declared_cols.add(str(_c['name']))
                else:
                    _all_dict = False
                    break

            if _all_dict and _declared_cols:  # 仅在 schema 完整声明时启用
                import re as _re_col
                _declared = _declared_cols
                # SQL 关键字 + 常用函数 + DSL helper（小写匹配，比较时全部 lower）
                _SQL_RESERVED = {
                    # 关键字
                    'select', 'from', 'where', 'group', 'by', 'order', 'having',
                    'and', 'or', 'not', 'in', 'is', 'null', 'as', 'on', 'with',
                    'when', 'then', 'else', 'end', 'case', 'distinct', 'all',
                    'between', 'like', 'ilike', 'union', 'intersect', 'except',
                    'asc', 'desc', 'true', 'false',
                    # 聚合 / 数值函数
                    'sum', 'count', 'avg', 'min', 'max', 'first', 'last',
                    'least', 'greatest', 'abs', 'round', 'floor', 'ceil',
                    'percentile_approx', 'stddev', 'variance',
                    'nullif', 'coalesce', 'if', 'ifnull', 'cast', 'try_cast',
                    'concat', 'substring', 'substr', 'length', 'lower', 'upper',
                    'trim', 'replace', 'split',
                    # 时间函数（含 Spark/DuckDB 共用）
                    'year', 'month', 'day', 'hour', 'minute', 'second',
                    'date', 'date_format', 'date_add', 'date_sub', 'date_trunc',
                    'datediff', 'to_date', 'to_timestamp', 'unix_timestamp',
                    'from_unixtime', 'current_timestamp', 'current_date', 'now',
                    # DSL spark_safe_* 白名单（runner 注入）
                    'spark_safe_to_timestamp', 'spark_safe_to_date',
                    'spark_safe_datediff', 'spark_safe_date_format',
                    'spark_safe_week_format', 'spark_safe_to_timestamp_extended',
                    # 窗口函数（虽然 raw_sql 才用，DSL 路径理论上不会出现，但放宽不影响）
                    'row_number', 'rank', 'dense_rank', 'lag', 'lead', 'over',
                    'partition', 'rows', 'preceding', 'following', 'current', 'row', 'unbounded',
                    # SQL 类型字面量（CAST(x AS BIGINT)）
                    'bigint', 'int', 'integer', 'double', 'float', 'decimal',
                    'varchar', 'string', 'boolean', 'timestamp', 'time',
                }
                # 剥单引号字符串字面量；保留双引号包裹的标识符（DuckDB 风格列名）
                _STRLIT_RE = _re_col.compile(r"'(?:''|[^'])*'")
                # 带表别名形态：连续两个标识符之间夹一个点（已被 Compare 校验或 raw_sql 覆盖，此处需排除）
                _ALIAS_DOT_RE = _re_col.compile(
                    r'\b[A-Za-z_][A-Za-z0-9_]*\s*\.\s*[A-Za-z_][A-Za-z0-9_]*\b'
                )
                # 裸标识符
                _IDENT_RE = _re_col.compile(r'\b[A-Za-z_][A-Za-z0-9_]*\b')

                def _extract_unknown_cols(expr: str) -> List[str]:
                    """从单个 SQL 表达式中提取未声明的列引用。"""
                    if not expr:
                        return []
                    s = _STRLIT_RE.sub("''", expr)        # 剥单引号字面量
                    s = _ALIAS_DOT_RE.sub(' ', s)          # 移除带别名的列引用
                    unknown: List[str] = []
                    seen: set = set()
                    for m in _IDENT_RE.finditer(s):
                        ident = m.group(0)
                        if ident in seen:
                            continue
                        seen.add(ident)
                        low = ident.lower()
                        if low in _SQL_RESERVED:
                            continue
                        if ident in _declared:
                            continue
                        # 仅在拿到列名是合法标识符时报告（前面正则已保证）
                        unknown.append(ident)
                    return unknown

                _problems: List[str] = []   # [(loc, expr, unknowns)]

                # 收集所有 DSL 路径下的 expr（raw_sql 跳过）
                # —— Spec.kpis ——
                for _i, _k in enumerate(self.kpis):
                    if not isinstance(_k, Metric):
                        continue
                    # 跨表 KPI（from_sql 非空）跳过——LLM 已显式声明换源
                    if getattr(_k, 'from_sql', None):
                        continue
                    _unk = _extract_unknown_cols(_k.expr or '')
                    if _unk:
                        _problems.append(
                            f'  KPI #{_i+1} (label={_k.label!r}): expr=`{_k.expr}` → 未声明列 {_unk}'
                        )

                # —— Spec.charts ——
                for _ci, _c in enumerate(self.charts):
                    if isinstance(_c, Chart):
                        # raw_sql 路径直接跳过
                        if _c.escape_hatch or _c.raw_sql:
                            continue
                        for _di, _d in enumerate(_c.dims):
                            if isinstance(_d, Dim):
                                _unk = _extract_unknown_cols(_d.expr or '')
                                if _unk:
                                    _problems.append(
                                        f'  Chart "{_c.title}" dims[{_di}]: expr=`{_d.expr}` → 未声明列 {_unk}'
                                    )
                        for _mi, _m in enumerate(_c.metrics):
                            if isinstance(_m, Metric):
                                _unk = _extract_unknown_cols(_m.expr or '')
                                if _unk:
                                    _problems.append(
                                        f'  Chart "{_c.title}" metrics[{_mi}] (label={_m.label!r}): expr=`{_m.expr}` → 未声明列 {_unk}'
                                    )
                    elif isinstance(_c, Compare):
                        # Compare.dim
                        if isinstance(_c.dim, Dim):
                            _unk = _extract_unknown_cols(_c.dim.expr or '')
                            if _unk:
                                _problems.append(
                                    f'  Compare "{_c.title}" dim: expr=`{_c.dim.expr}` → 未声明列 {_unk}'
                                )
                        # Compare.metric
                        if isinstance(_c.metric, Metric):
                            _unk = _extract_unknown_cols(_c.metric.expr or '')
                            if _unk:
                                _problems.append(
                                    f'  Compare "{_c.title}" metric: expr=`{_c.metric.expr}` → 未声明列 {_unk}'
                                )

                if _problems:
                    _src_table = getattr(self.source, 'table', '') or '<unknown>'
                    _all_cols = sorted(_declared)
                    _preview = (', '.join(_all_cols[:20])
                                + (f', ... (+{len(_all_cols)-20} more)' if len(_all_cols) > 20 else ''))
                    raise ValueError(
                        f'[DSL] Spec 引用了 source.columns 未声明的列（共 {len(_problems)} 处）:\n'
                        + '\n'.join(_problems) + '\n'
                        f'  source.table = `{_src_table}`\n'
                        f'  已声明列（{len(_all_cols)} 个）：{_preview}\n'
                        f'  根因：LLM 高频幻觉——把 kanban_spec_example.py 里的示例字段'
                        f'（amount/cost/qty/price/category/region/channel/user_id 等）当作默认字段抄到新表，\n'
                        f'        结果远端 Spark 报 `cannot resolve` 看板空集。\n'
                        f'  修法 A（首选）：检查 Step B 输出的 schema，把真实存在的列名替换到 expr 中；\n'
                        f'                   如果列名拼写正确但漏写到 source.columns，把它补进列声明（同时带上正确 type）。\n'
                        f'  修法 B（聚合派生）：派生指标用 NULLIF/CASE WHEN 的，确保引用的列在 source.columns 里出现。\n'
                        f'  修法 C（必须跨表）：改走 raw_sql 工厂 + escape_hatch=True + slot_columns=[...]；\n'
                        f'                       或 KPI 用 kpi(expr=..., from_sql=\'cat.db.t1 a JOIN cat.db.t2 b ON ...\')。'
                    )
        except ValueError:
            raise
        except Exception:
            # 任何意外异常不阻断 Spec 构造（保守原则：校验只增不减）
            pass


__all__ = [
    'Dim', 'dim', 'time_dim',
    'Metric', 'metric', 'kpi',
    'Source', 'source',
    'Chart', 'chart', 'raw_sql',
    'Compare', 'compare',
    'Spec',
]
