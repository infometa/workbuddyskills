"""
============================================================================
kanban_spec_example.py —— 智能看板【全量参考示范】（LLM 唯一可抄的范本）
============================================================================

本文件目的：
  把 SKILL.md 的硬约束（P0）+ kanban_dsl.py 的所有合法字段，
  用一个可直接 `python3 kanban_spec_example.py` 跑通的零售驾驶舱样例
  全部演示一遍。LLM 写新 spec 时**只需照抄结构、改 source/kpis/charts**。

🛑 LLM 必读（违反 = 执行失败）：
  1. 必须 `Spec(...)` + `build_kanban(spec)`，禁止手写 builder/runner 调用链。
  2. reference/ 下三个文件全部只读（kanban_dsl.py / kanban_runner.py / kanban_builder.py）。
  3. 能用 DSL 字段表达的就**绝不**用 raw_sql；逃生口必须 `escape_hatch=True` + `slot_columns=`。
  4. `Spec.charts` 至少 5 种不同 `kind`（本文件演示 16 种全集，实战按需挑选）。
  5. 同环比**只能**用 `compare(...)`，不准用 `chart('line', metrics=['SUM(x)','mom_x'])` 假装。
  6. workspace_id 留空，wedatacli 自动注入。
7. 不声明任何 file_id 字段，runner 自动从 <workspace_folder>/.kanban_output/kanban_save_params.json 读取已有 AccessKey 覆盖 PREVIEW。

DSL 能力边界速记（用于决策"何时走 raw_sql"）：
  ✅ 已支持：
     - 16 类 echarts kind（line/bar/pie/scatter/radar/funnel/gauge/heatmap/
       candlestick/treemap/sankey/boxplot/sunburst/graph/parallel/table）
     - 时间分桶（time_dim 自动 spark_safe_*）
     - SQL 表达式维度（dim('CASE WHEN ... END', alias='...')）
     - 派生比率度量（metric('SUM(a)/NULLIF(SUM(b),0)*100', ...)）
     - 同环比 mom / wow / yoy 任意组合（Compare 类）
     - TopN + Others 自动归并（chart 设 limit）
     - K线 OCLH（metric.role='open/close/low/high'）
     - 雷达归一化（metric.normalize='max-norm'）
     - Gauge 上限（metric.target=...）
     - 透传 echarts 原生配置（chart 的 extras={...}）
  ❌ 不支持（必须走 raw_sql）：
     - 通用窗口函数：ROW_NUMBER / RANK / DENSE_RANK / PERCENT_RANK
     - PARTITION BY 分组排名（"按地区各自的 MoM" 也只能 raw_sql）
     - 累计求和 / 移动平均 / 滑动窗口（SUM OVER ROWS BETWEEN ...）
     - 多 CTE / UNION / 自连接 / 嵌套子查询
     - 复杂 JOIN（DSL 的 source 单表）
"""

import os
import sys

# ===== 1. 引导 reference 路径（固定写法，不要改）=====
_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN_ROOT = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '')


def _pick_ref_dir():
    """按显式配置、本地目录、新旧部署布局依次探测 reference/。"""
    explicit = os.environ.get('KANBAN_REFERENCE_DIR', '').strip()
    if explicit and os.path.isdir(explicit):
        return explicit

    local = os.path.join(_HERE, 'reference')
    if os.path.isdir(local):
        return local

    if _PLUGIN_ROOT:
        for sub in (
            ('scenarios', 'data-analysis', 'skills', 'intelligent-kanban', 'reference'),
            ('l3-skill-scenario', 'intelligent-kanban', 'reference'),
            ('intelligent-kanban', 'reference'),
        ):
            candidate = os.path.join(_PLUGIN_ROOT, *sub)
            if os.path.isdir(candidate):
                return candidate

    return local


_REF = _pick_ref_dir()
sys.path.insert(0, _REF)

# ===== 2. 仅从 kanban_dsl 导入工厂，不要从 runner/builder 导入任何东西 =====
from kanban_dsl import (
    Spec, source,
    kpi, metric, Metric,
    dim, time_dim, Dim,
    chart, compare, raw_sql,
)
from kanban_runner import build_kanban


# ============================================================================
# 3. 数据源声明
#    - columns 直接抄 prefetch_table.py 输出的 schema JSON
#    - time_col / time_type 必填（runner 用它 parse_time_column 本地解析）
#    - where 是可选全局过滤（不带 WHERE 关键字，runner 自动拼）
# ============================================================================

SRC = source(
    table='retail_db.dwd.fact_sales_daily',
    columns=[
        {'name': 'time',          'type': 'string'},   # 主时间列（必填）
        {'name': 'category',      'type': 'string'},
        {'name': 'sub_category',  'type': 'string'},
        {'name': 'region',        'type': 'string'},
        {'name': 'channel',       'type': 'string'},
        {'name': 'product_id',    'type': 'string'},
        {'name': 'product_name',  'type': 'string'},
        {'name': 'price',         'type': 'double'},
        {'name': 'amount',        'type': 'double'},
        {'name': 'cost',          'type': 'double'},
        {'name': 'qty',           'type': 'bigint'},
        {'name': 'user_id',       'type': 'string'},
        {'name': 'open_price',    'type': 'double'},   # 用于 candlestick 演示
        {'name': 'close_price',   'type': 'double'},
        {'name': 'high_price',    'type': 'double'},
        {'name': 'low_price',     'type': 'double'},
    ],
    time_col='time',
    time_type='string',          # string / date / timestamp / unix
    where="amount IS NOT NULL",  # 可选；不带 WHERE 关键字
    limit=10_000,                # 全量取数上限（默认 1w 行，看板端 duckdb 聚合 + top_k 后精度足够）
)


# ============================================================================
# 4. KPI（顶部数字卡片）
#    - 至少 3 个；用 kpi() 工厂自动 role='kpi'
#    - label 必填；prefix/suffix/format 控制展示
# ============================================================================

KPIS = [
    kpi('SUM(amount)',
        label='总销售额',
        prefix='¥', format=',.0f'),
    kpi('SUM(amount) - SUM(cost)',
        label='总毛利',
        prefix='¥', format=',.0f'),
    kpi('(SUM(amount) - SUM(cost)) * 100.0 / NULLIF(SUM(amount), 0)',
        label='毛利率',
        format='.1f', suffix='%'),
    kpi('COUNT(DISTINCT user_id)',
        label='购买用户数',
        format=',.0f'),
    kpi('SUM(amount) / NULLIF(COUNT(DISTINCT user_id), 0)',
        label='客单价',
        prefix='¥', format=',.0f'),
]


# ============================================================================
# 5. Charts —— 全量演示 16 类 kind 的合法写法
#    实战中按业务挑 5~10 个；本文件作为参考字典保留全集。
# ----------------------------------------------------------------------------
# 选型决策表（Step B 拿到 schema 后先查表，再抄对应 5.x 正例）
# ----------------------------------------------------------------------------
# 字段组合形态                                  首选 kind                    语义触发条件                   详见
# ──────────────────────────────────────────────────────────────────────────
# A. 时间列 + 1~3 数值列                         line                         看趋势/演化                    5.1
# B. 时间列 + 分类列(≤8) + 1 数值列              line(stacked=True)           看分品类的趋势演化             5.1
# C. 时间列 + OCLH 四数值列                      candlestick                  价格/股价波动（必有 4 角色）   5.9
# D. 时间列 + 单一数值列(看周期对比)             compare(mom/yoy/wow)         同环比指标卡（不要用 line+'mom_xxx' 假装） 6
# ──────────────────────────────────────────────────────────────────────────
# E. 低基数分类(≤20) + 1 数值列                  bar                          排名/对比，配 limit=10+TopN    5.2
# F. 低基数分类(≤8)  + 1 数值列                  pie                          占比 100% 累加才用 pie         5.3
# G. 低基数分类 + ≥3 可归一化数值列              radar                        多维评分对比（normalize必填） 5.5
# H. 阶段分类(同表 CASE WHEN) + 计数             funnel                       漏斗：metric 数=阶段数，无dims 5.6
# I. 单一比率/达成率(0~target)                   gauge                        单值 + target 上限             5.7
# ──────────────────────────────────────────────────────────────────────────
# J. 两个低基数分类 + 1 数值列                   heatmap                      二维交叉分布                   5.8
# K. 流出方→流入方(有方向) + 数值列              sankey                       强调单向流量大小               5.12
# L. 节点+真实关联(无方向/共现)                  graph(边模式 dims=2)         强调网络拓扑                   5.14
# ──────────────────────────────────────────────────────────────────────────
# M. ≥2 层父子分类 + 1 数值列                    treemap / sunburst           层级占比(treemap矩形/sunburst环形) 5.10/5.11
# N. 1 分类(低基数) + 1 行级数值列(看分布)       boxplot                      分组分布五数概括               5.13
# O. ≥3 聚合数值列 + 1 分类列                    parallel                     多维度横向对比                 5.15
# P. 明细列表(≥4 列, 含主键/名称)                table                        明细查询，dims=列序            5.16
# ──────────────────────────────────────────────────────────────────────────
# Q. 累计/移动/排名/PARTITION/UNION/JOIN         raw_sql                      DSL 表达不出，必走逃生口        7
# ──────────────────────────────────────────────────────────────────────────
# 使用方式：
#   ① 先按"字段组合形态"匹配自己手里的 schema，命中哪行就抄哪一节正例；
#   ② 同一形态可能有多种写法（如形态 J 既能低基数双维直出，也能 raw_sql Top30 兜底），按"语义触发条件"+"数据规模"组合判断；不同 kind 之间（heatmap vs sankey vs graph）按各自的语义触发条件区分，不要互相替代；
#   ③ 凑齐 ≥5 种不同 kind 满足 P0-4，但选型必须有语义依据，不准为多样性硬塞；
#   ④ 数据保真自适应（P0-12）见对应 5.x 正例顶部注释，决策表不重复展开；
#   ⑤ DSL 新增 kind 时先改本表再补 5.x 正例，避免脱节。
# ============================================================================

CHARTS = [

    # ---------- 5.1 line：时间趋势（最常用）----------
    # dims[0]=分组维（通常时间），metrics 多个 → 多系列折线
    chart(
        kind='line', title='日销售趋势', emoji='📈', span=4,
        dims=[time_dim('time', 'day')],          # 自动 spark_safe_date_format
        metrics=[
            metric('SUM(amount)', label='销售额', format=',.0f'),
            metric('SUM(qty)',    label='件数',   format=',.0f'),
        ],
        smooth=True,
        dual_axis=[1],                            # 第 2 个 metric 走右轴
        stacked=False,
    ),

    # ---------- 5.2 bar：分类对比 + TopN ----------
    chart(
        kind='bar', title='品类销售 TopN', emoji='📊', span=2,
        dims=[dim('category', label='品类')],
        metrics=[metric('SUM(amount)', label='销售额', format=',.0f')],
        order_by='-SUM(amount)',                  # 按指标降序；'name' 升序
        limit=10,                                 # 自动 TopN+Others 防偏态
    ),

    # ---------- 5.3 pie：占比 ----------
    chart(
        kind='pie', title='渠道占比', emoji='🥧', span=2,
        dims=[dim('channel', label='渠道')],
        metrics=[metric('SUM(amount)', label='销售额')],
        limit=8,
    ),

    # ---------- 5.4 scatter：散点（dims[0]=x, dims[1?]=color, metrics[0]=y；不支持 size 度量）----------
    # ⚠️ dims 必须是行级表达式或裸列名，**不能含聚合**（聚合放 metrics）。
    #     若想"按聚合结果作 x 轴"，请用 CASE WHEN 行级分桶 + dim 别名。
    #
    # ✅ 类型感知放行：source.columns 用 dict 形态声明 type 后（如 {'name':'price','type':'double'}），
    #     DSL 会自动把数值类型的裸列名识别为数值表达式，无需任何包装。
    #     ❌ 仅当 source 用纯字符串列名（无 type 信息）时，DSL 退回保守启发式，需要：
    #         dims=[dim('price * 1.0', alias='price', label='价格')]    # 用 *1.0 让正则命中算术
    #     本文件 SRC 已用 dict 声明 type，因此可以直接 dim('price', label='价格')
    #
    # 🎯 数据保真自适应（P0-12）：本写法属于「业务分桶聚合」形态，是 scatter 的最佳实践——
    #     - metrics[0]=SUM(qty) 含聚合 → runner 自动 GROUP BY price_tier, category
    #     - 输出行数 = 价格段数(3) × 品类数 ≈ 30 行，与底表 N 解耦，HTML 体积稳定
    #     - 100% 保留分布形状（每个桶的 SUM 精确），仅丢点级散布噪声（>50K 行时本就糊成一团）
    #     底表 ≤ 500 行的小数据场景请改用「行级全量」：
    #         dims=[dim('price * 1.0', alias='price', label='价格'), dim('category')],
    #         metrics=[metric('qty')], limit=500, order_by='-y'
    #     （⚠️ scatter SELECT 输出别名固定为 x/y/category，order_by 只能引用这些别名，不能用 metric.alias）
    chart(
        kind='scatter', title='价格区间-销量散点', emoji='🔬', span=2,
        dims=[
            dim("CASE WHEN price < 50 THEN '<50' "
                "WHEN price < 200 THEN '50-200' ELSE '200+' END",
                alias='price_tier', label='价格段'),
            dim('category', label='品类'),         # 第 2 维作为颜色分组
        ],
        metrics=[metric('SUM(qty)', label='总件数')],
    ),

    # ---------- 5.5 radar：多维雷达（≥3 metrics + normalize='max-norm'）----------
    chart(
        kind='radar', title='品类多维评分', emoji='🎯', span=2,
        dims=[dim('category', label='品类')],
        metrics=[
            metric('SUM(amount)', label='销售额', normalize='max-norm'),
            metric('SUM(qty)',    label='件数',   normalize='max-norm'),
            metric('AVG(price)',  label='均价',   normalize='max-norm'),
            metric('COUNT(DISTINCT user_id)', label='用户', normalize='max-norm'),
        ],
        limit=6,
    ),

    # ---------- 5.6 funnel：漏斗（不要 dims；每个 metric 一个阶段）----------
    chart(
        kind='funnel', title='转化漏斗', emoji='🪜', span=2,
        metrics=[
            metric('COUNT(DISTINCT user_id)',                        label='浏览用户'),
            metric('COUNT(DISTINCT CASE WHEN qty>0 THEN user_id END)', label='下单用户'),
            metric('COUNT(DISTINCT CASE WHEN amount>0 THEN user_id END)', label='付款用户'),
        ],
    ),

    # ---------- 5.7 gauge：仪表盘（单 metric + target=上限）----------
    chart(
        kind='gauge', title='毛利率达成', emoji='⏱️', span=2,
        metrics=[
            metric(
                expr='(SUM(amount) - SUM(cost)) * 100.0 / NULLIF(SUM(amount), 0)',
                label='毛利率', format='.1f', suffix='%',
                target=40.0,                       # gauge 量程上限
            ),
        ],
    ),

    # ---------- 5.8 heatmap：双维热力（dims[0]=x, dims[1]=y, metrics[0]=值）----------
    chart(
        kind='heatmap', title='品类×渠道热力', emoji='🔥', span=2,
        dims=[
            dim('category', label='品类'),
            dim('channel',  label='渠道'),
        ],
        metrics=[metric('SUM(amount)', label='销售额')],
    ),

    # ---------- 5.9 candlestick：K 线（dims[0]=时间, 4 个 role 化 metric）----------
    # ⚠️ 真实价格序列优先 FIRST/LAST（开盘=首笔、收盘=末笔），更贴近金融语义；
    #     此处用 AVG 是因为示例底表同一天有多条记录、需聚合后才有意义。
    #     无价格族列时不要硬凑 candlestick——见 kanban_spec_pitfalls.py 反例 22。
    chart(
        kind='candlestick', title='价格 K 线', emoji='🕯️', span=4,
        dims=[time_dim('time', 'day')],
        metrics=[
            metric('AVG(open_price)',  role='open',  label='开'),
            metric('AVG(close_price)', role='close', label='收'),
            metric('MIN(low_price)',   role='low',   label='低'),
            metric('MAX(high_price)',  role='high',  label='高'),
        ],
    ),

    # ---------- 5.10 treemap：层级矩形树图（dims=路径，自动 TopN+Others）----------
    chart(
        kind='treemap', title='品类→子类→商品 树图', emoji='🌳', span=2,
        dims=[
            dim('category',     label='品类'),
            dim('sub_category', label='子类'),
            dim('product_name', label='商品'),
        ],
        metrics=[metric('SUM(amount)', label='销售额')],
        extras={'level_limit': 10},                # 每父节点叶层 TopN（默认 12）
    ),

    # ---------- 5.11 sunburst：旭日图（同 treemap 数据形态）----------
    chart(
        kind='sunburst', title='地区→渠道 旭日', emoji='☀️', span=2,
        dims=[
            dim('region',  label='地区'),
            dim('channel', label='渠道'),
        ],
        metrics=[metric('SUM(amount)', label='销售额')],
    ),

    # ---------- 5.12 sankey：桑基图（dims[0,1]=source/target, metrics[0]=权重）----------
    # ⚠️ sankey 是标准双维 GROUP BY（source × target），与 graph 节点模式的 LEAD 串链完全不同。
    #     dims[0]=流出方, dims[1]=流入方，两者之间必须有真实业务流向关系。
    chart(
        kind='sankey', title='地区→品类 流向', emoji='🌊', span=4,
        dims=[
            dim('region',   label='地区'),
            dim('category', label='品类'),
        ],
        metrics=[metric('SUM(amount)', label='权重')],
        limit=30,
    ),

    # ---------- 5.13 boxplot：箱线图（dims[0]=分组, metrics[0]=值）----------
    # 🎯 数据保真自适应（P0-12）：boxplot 输出行数 = 分类基数（与底表 N 解耦）。
    #     - category 是低基数维（通常 ≤ 20）→ DSL 直出，runner 内部 percentile_approx
    #       输出 5 数概括，**100% 精确**，无论底表 1 行还是 1 亿行结果一致
    #     - 风险点不在 metrics 行数，而在 dims 基数：若 dims 用 product_id/user_id 等
    #       高基数列，会产生几万个箱子 → 前端崩溃。高基数场景请查 kanban_spec_pitfalls.py
    #       反例 15 的 raw_sql 修法（Top20 主力分组 + percentile_approx）。
    chart(
        kind='boxplot', title='品类价格分布', emoji='📦', span=2,
        dims=[dim('category', label='品类')],
        metrics=[metric('price', label='价格')],   # 注意：boxplot 的 metric 是行级表达式
    ),

    # ---------- 5.14 graph：关系图（两种模式按业务语义二选一）----------
    # 模式 A·节点模式（dims=1）：runner 用 LEAD OVER (ORDER BY metric DESC) 把 Top-K
    #     节点串成链式边（第1名→第2名→第3名…）。⚠️ 生成的边是「排名相邻」而非真实
    #     业务关系，仅适合「想直观看 Top-K 节点权重」、不在意边语义的场景；若用户问
    #     的是「关联/流向/网络结构」，请改用边模式或 sankey。
    # 模式 B·边模式（dims=2 + limit）：dims=[source, target] 之间必须有真实隶属/关联
    #     关系——但与 5.12 sankey 的差别在于：sankey 强调「单向流量大小」（流出→流入），
    #     graph 强调「网络拓扑/共现」。两者的 dims 不应完全相同，否则只是换皮。
    # 此处演示模式 A（节点权重视图），与 5.12 sankey「地区→品类 流向」语义错开。
    chart(
        kind='graph', title='Top 品类节点权重', emoji='🕸️', span=2,
        dims=[dim('category', label='品类')],     # 节点模式：单维
        metrics=[metric('SUM(amount)', label='销售额')],
        limit=10,                                  # Top-K 节点数；K 越大链越长
    ),

    # ---------- 5.15 parallel：平行坐标（dims[0..-2]=轴, dims[-1]=分类）----------
    chart(
        kind='parallel', title='地区多维平行坐标', emoji='📐', span=2,
        dims=[
            dim('SUM(amount)',                alias='amount_sum', label='销售额'),
            dim('SUM(qty)',                   alias='qty_sum',    label='件数'),
            dim('AVG(price)',                 alias='avg_price',  label='均价'),
            dim('COUNT(DISTINCT user_id)',    alias='uv',         label='用户'),
            dim('region', label='地区'),                                   # 最后一维=分类
        ],
    ),

    # ---------- 5.16 table：明细表（span 自动撑满整行）----------
    # 注意：table 的 dims 即列序，不要给 metrics
    chart(
        kind='table', title='Top50 商品明细', emoji='📋', span=4,
        dims=[
            dim('product_id',   label='商品ID'),
            dim('product_name', label='商品名'),
            dim('category',     label='品类'),
            dim('SUM(amount)',  alias='amount', label='销售额'),
            dim('SUM(qty)',     alias='qty',    label='件数'),
        ],
        order_by='-amount',
        limit=50,
    ),

    # ---------- 5.17 SLA / 履约风险看板（运营值班视图）----------
    # 适用形态：表里同时含「时间戳列 + 状态列 + 预计送达/截止时间列」时（电商履约 / 工单 SLA /
    #          作业截止 / 运维 SLA），用本节模板组合 5 张图即可一眼看出"卡住的 / 超时的 / 即将到期的"。
    # 设计要点（落实 P0-12 与"日期差方言前置校验"）：
    #   1. 日期差表达式只用 Spark 两参 `DATEDIFF(end, start)`；
    #      ⚠️ 严禁三参数 `DATEDIFF(DAY, ...)` / `DATE_DIFF('day', ...)`，DSL 构造期会直接 raise。
    #   2. 时间列在 `raw_sql` 路径外做差/比较时，必须包 `spark_safe_to_timestamp(col)`
    #      （即使 source.columns 声明为 timestamp 也建议显式包，以兼容本地 DuckDB CSV 字符串）。
    #   3. "剩余天数 / 紧急度"用同一个 CASE WHEN 风险等级表达式跨图复用，保证 KPI/饼图/明细口径一致。
    #   4. 风险等级排序：用 `risk_score` 数值列（高=紧急）做 order_by，避免按文本字典序排乱顺序。
    #   5. 历史数据集警示：用 CURRENT_TIMESTAMP 与 2016~2018 历史订单比较会把存量全判超时；
    #      真实在线履约表才用 CURRENT_TIMESTAMP，历史回溯请用数据快照日（如下方 _DEADLINE_NOW 锚点）。
    #
    # 字段约定（按需对照 Step B schema 替换）：
    #   - order_id / order_status                                 主键 + 状态
    #   - order_purchase_at / order_delivered_at                  下单 / 实际送达
    #   - order_estimated_delivery_ts                             预计送达
    #   - is_delivered / is_canceled / is_delayed                 状态衍生标记（若无可用 CASE 推导）
    #
    # ⚠️ 本节为参考模板，不在本文件 SPEC.charts 默认引用（避免和示例底表 schema 冲突）。
    #     实战时把下方 _RISK_LEVEL_EXPR / _REMAINING_DAYS_EXPR 复制到自己的 spec 中复用即可。

    # 风险锚点：在线表用 'CURRENT_TIMESTAMP'；历史回溯时改成数据快照日（如 "spark_safe_to_timestamp('2018-09-01')"）
    # _DEADLINE_NOW = 'CURRENT_TIMESTAMP'
    #
    # 跨图复用的核心表达式（写真实 spec 时把这两个常量贴进去，5 张图全用同一份）：
    #
    # _REMAINING_DAYS_EXPR = (
    #     "DATEDIFF(spark_safe_to_timestamp(order_estimated_delivery_ts), "
    #     + _DEADLINE_NOW + ")"
    # )
    #
    # _RISK_LEVEL_EXPR = (
    #     "CASE "
    #     "  WHEN order_status='canceled' THEN '已取消' "
    #     "  WHEN order_status='delivered' AND DATEDIFF("
    #     "        spark_safe_to_timestamp(order_delivered_at), "
    #     "        spark_safe_to_timestamp(order_estimated_delivery_ts))>0 THEN '已延误送达' "
    #     "  WHEN order_status<>'delivered' AND spark_safe_to_timestamp(order_estimated_delivery_ts) "
    #     "        < " + _DEADLINE_NOW + " THEN '超预计未送达' "
    #     "  WHEN order_status<>'delivered' AND " + _REMAINING_DAYS_EXPR + " <= 2 THEN '即将到期' "
    #     "  WHEN order_status='delivered' THEN '正常送达' "
    #     "  ELSE '履约中' END"
    # )
    #
    # _RISK_SCORE_EXPR = (    # 数值化便于排序（越大越紧急）
    #     "CASE "
    #     "  WHEN order_status<>'delivered' AND spark_safe_to_timestamp(order_estimated_delivery_ts) "
    #     "        < " + _DEADLINE_NOW + " THEN 3 "
    #     "  WHEN order_status<>'delivered' AND " + _REMAINING_DAYS_EXPR + " <= 2 THEN 2 "
    #     "  WHEN order_status='delivered' AND DATEDIFF("
    #     "        spark_safe_to_timestamp(order_delivered_at), "
    #     "        spark_safe_to_timestamp(order_estimated_delivery_ts))>0 THEN 1 "
    #     "  ELSE 0 END"
    # )
    #
    # SLA_KPIS = [
    #     kpi('COUNT(*)', label='总订单', format=',.0f'),
    #     kpi("SUM(CASE WHEN order_status<>'delivered' AND "
    #         "spark_safe_to_timestamp(order_estimated_delivery_ts) < " + _DEADLINE_NOW + " THEN 1 ELSE 0 END)",
    #         label='超预计未送达', format=',.0f'),
    #     kpi("SUM(CASE WHEN order_status<>'delivered' AND " + _REMAINING_DAYS_EXPR + " <= 2 "
    #         "AND spark_safe_to_timestamp(order_estimated_delivery_ts) >= " + _DEADLINE_NOW + " THEN 1 ELSE 0 END)",
    #         label='2 日内到期', format=',.0f'),
    #     kpi("AVG(CASE WHEN order_status='delivered' THEN DATEDIFF("
    #         "spark_safe_to_timestamp(order_delivered_at), "
    #         "spark_safe_to_timestamp(order_purchase_at)) END)",
    #         label='平均履约天数', format='.1f', suffix='天'),
    # ]
    #
    # SLA_CHARTS = [
    #     # ① 风险等级饼图：一眼看清结构
    #     chart('pie', '风险等级分布', emoji='🚨', span=2,
    #           dims=[dim(_RISK_LEVEL_EXPR, alias='risk_level', label='风险')],
    #           metrics=[metric('COUNT(*)', label='订单数')]),
    #     # ② 紧急程度柱图（按 risk_score 数值排序，避免文本字典序乱）
    #     chart('bar', '紧急程度分布', emoji='⏰', span=2,
    #           dims=[dim(_RISK_LEVEL_EXPR, alias='risk_level', label='风险')],
    #           metrics=[metric('COUNT(*)', label='订单数')],
    #           order_by='-MAX(' + _RISK_SCORE_EXPR + ')'),     # 按风险分数降序，紧急在前
    #     # ③ 剩余天数趋势：每日新增订单 × 平均剩余天数（看积压趋势）
    #     chart('line', '日新增订单与平均剩余天数', emoji='📉', span=4,
    #           dims=[time_dim('order_purchase_at', 'day', label='下单日')],
    #           metrics=[
    #               metric('COUNT(*)', label='新增订单'),
    #               metric('AVG(' + _REMAINING_DAYS_EXPR + ')', label='平均剩余天数', format='.1f'),
    #           ],
    #           dual_axis=[1]),
    #     # ④ 状态分布：bar 比 pie 更适合 ≥6 个状态
    #     chart('bar', '订单状态分布', emoji='📊', span=2,
    #           dims=[dim('order_status', label='状态')],
    #           metrics=[metric('COUNT(*)', label='订单数')],
    #           order_by='-COUNT(*)'),
    #     # ⑤ 高风险明细 Top30：order_by 用剩余天数升序，负数（已超时）排最前
    #     chart('table', '高风险订单明细 Top30', emoji='🔴', span=4,
    #           dims=[
    #               dim('order_id',                label='订单ID'),
    #               dim(_RISK_LEVEL_EXPR,          alias='risk_level',     label='风险'),
    #               dim('order_status',            label='状态'),
    #               dim('order_estimated_delivery_ts', label='预计送达'),
    #               dim(_REMAINING_DAYS_EXPR,      alias='remaining_days', label='剩余天数'),
    #           ],
    #           order_by='remaining_days', limit=30),  # ✅ 升序：最紧急在前
    # ]


    # ========================================================================
    # 6. 同环比卡片 —— 必须用 compare()，不许用 chart('line', metrics=[...mom])
    # ========================================================================

    # 月度环比
    compare(
        title='月度销售环比',
        dim=time_dim('time', 'month'),                    # 必须时间维度
        metric=metric('SUM(amount)', label='销售额', format=',.0f'),
        kinds=['mom'],                                    # ['mom'|'yoy'|'wow'] 任意组合
        emoji='📊', span=2,
    ),

    # 同时跑 mom + yoy（双指标双 y 轴自动配置）
    compare(
        title='销售环比+同比',
        dim=time_dim('time', 'month'),
        metric=metric('SUM(amount)', label='销售额'),
        kinds=['mom', 'yoy'],
        emoji='📈', span=2,
    ),


    # ========================================================================
    # 7. raw_sql 逃生口 —— 仅当 DSL 表达不出时才用！
    #    必须满足：escape_hatch=True + slot_columns=[...] 显式列序
    #    适用场景（且仅限于这些）：
    #      - ROW_NUMBER / RANK / DENSE_RANK 通用窗口
    #      - PARTITION BY 分组排名（如"各地区各自 TopN 商品"）
    #      - 累计求和 / 移动平均 / 滑动窗口
    #      - 多 CTE / UNION / 复杂 JOIN
    #    ⚠️ 警告：
    #      - 本地 Pandas 端 _compile_raw 不切片真实数据，只给表头，
    #        预览数据完全靠平台 sqlSlots 跑 → 必须保证 SQL 自身正确
    #      - 时间字段必须 spark_safe_*（H11/H12/H13）；同环比必须 WITH 双层（H32）
    #        否则 builder lint 会拦截
    # ========================================================================

    # 示例 7.1：分地区各自 Top3 商品（PARTITION BY，DSL 不支持）
    raw_sql(
        title='各地区 Top3 商品',
        kind='table',
        emoji='🏆', span=4,
        slot_columns=['region', 'product_name', 'amount', 'rk'],   # 必须与 SELECT 列序一致
        sql=(
            "WITH agg AS (\n"
            "  SELECT region, product_name, SUM(amount) AS amount\n"
            "  FROM retail_db.dwd.fact_sales_daily\n"
            "  WHERE amount IS NOT NULL\n"
            "  GROUP BY region, product_name\n"
            "),\n"
            "ranked AS (\n"
            "  SELECT region, product_name, amount,\n"
            "         ROW_NUMBER() OVER (PARTITION BY region ORDER BY amount DESC) AS rk\n"
            "  FROM agg\n"
            ")\n"
            "SELECT region, product_name, amount, rk\n"
            "FROM ranked\n"
            "WHERE rk <= 3\n"
            "ORDER BY region, rk"
        ),
    ),

    # 示例 7.2：7 日移动平均（窗口 ROWS BETWEEN，DSL 不支持）
    # ⚠️ 时间字段必须用 spark_safe_date_format，不要直接 DATE_FORMAT/CAST
    raw_sql(
        title='销售额 7 日移动平均',
        kind='line',
        emoji='〰️', span=4,
        slot_columns=['day', 'amount', 'amount_ma7'],
        sql=(
            "WITH agg AS (\n"
            "  SELECT spark_safe_date_format(time, 'yyyy-MM-dd') AS day,\n"
            "         SUM(amount) AS amount\n"
            "  FROM retail_db.dwd.fact_sales_daily\n"
            "  WHERE amount IS NOT NULL\n"
            "  GROUP BY spark_safe_date_format(time, 'yyyy-MM-dd')\n"
            ")\n"
            "SELECT day, amount,\n"
            "       AVG(amount) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS amount_ma7\n"
            "FROM agg\n"
            "ORDER BY day"
        ),
    ),
    # ========================================================================
    # 7.5 多表场景 —— 主表 + 伴随表（runner 自动注册 DuckDB 伴随视图）
    # ----------------------------------------------------------------------
    # 何时启用（机械判定）：用户明确提到 ≥2 个数据来源（多张表 / 多业务方向，
    #   如 "订单和商品" / "学情+作业"）→ 多表流程；只提一个 → 单表，不要画蛇添足。
    #
    # 设计取舍：Spec.source 仍是单源（主表，选数据量更大或语义更核心的那张），
    #   其他表通过 raw_sql chart 跨表查询。Step B 一条 prefetch 命令搞定所有表：
    #     prefetch_table.py --tables "catalog.db.orders,catalog.db.products,..."
    #   （英文逗号分隔；脚本内部并行召回 + 后台并行预取）
    #
    # 运行时 runner 会打印 `🔗 多表伴随视图已注册（raw_sql 可直接 JOIN）：xxx`
    #   ——这是多表生效的唯一信号，未出现说明 prefetch 没覆盖到副表。
    #
    # 🛑 多表硬约束（与 P0-3 完全一致）：
    #   - raw_sql 中表名必须写完整三段式 catalog.db.table（与 Spec.source.table 同款）
    #   - 禁止写短名（FROM products）或本地占位名（_kb_src/main_data）
    #     虽然 runner 本地有短名视图兜底，但入库即 Spark TABLE_OR_VIEW_NOT_FOUND
    #   - 仍受 P0-4（≥5 种 chart_type）和 P0-12（保真自适应）约束
    # ========================================================================

    # ---------- 7.5.1 多表【独立展示】：副表用 raw_sql 工厂直查 ----------
    raw_sql(
        title='商品类目 Top10（来自 products 副表）',
        kind='bar', span=2, emoji='🏷️',
        slot_columns=['category', 'cnt'],          # 顺序必须与 SELECT 输出严格一致
        sql=(
            "SELECT product_category_name AS category, COUNT(*) AS cnt\n"
            "FROM catalog.db.products\n"           # ← 完整三段式，禁短名
            "WHERE product_category_name IS NOT NULL\n"
            "GROUP BY product_category_name\n"
            "ORDER BY `cnt` DESC LIMIT 10"
        ),
    ),

    # ---------- 7.5.2 多表【JOIN 关联】：跨表手写 JOIN（订单 join 商品看品类销售）----------
    raw_sql(
        title='品类销售 Top10（orders × products JOIN）',
        kind='bar', span=2, emoji='🔗',
        slot_columns=['category', 'amount'],
        sql=(
            "SELECT p.product_category_name AS category,\n"
            "       SUM(o.amount) AS amount\n"
            "FROM catalog.db.orders o\n"           # 主表（与 Spec.source.table 同款）
            "INNER JOIN catalog.db.order_items oi ON o.order_id = oi.order_id\n"
            "INNER JOIN catalog.db.products p     ON oi.product_id = p.product_id\n"
            "WHERE p.product_category_name IS NOT NULL\n"
            "GROUP BY p.product_category_name\n"
            "ORDER BY amount DESC LIMIT 10"
        ),
    ),

    # ---------- 7.5.3 多表【UNION ALL】：一张 line 画两表趋势 ----------
    # 关键：两个 SELECT 输出列必须**完全同名同序**，否则 UNION 会按位置错位拼接
    raw_sql(
        title='订单数 vs 商品上架数 月度趋势',
        kind='line', span=4, emoji='📈',
        slot_columns=['month', 'series', 'cnt'],
        sql=(
            "SELECT spark_safe_date_format(order_purchase_timestamp,'yyyy-MM') AS month,\n"
            "       'orders' AS series, COUNT(*) AS cnt\n"
            "FROM catalog.db.orders\n"
            "GROUP BY spark_safe_date_format(order_purchase_timestamp,'yyyy-MM')\n"
            "UNION ALL\n"
            "SELECT spark_safe_date_format(created_at,'yyyy-MM') AS month,\n"
            "       'products' AS series, COUNT(*) AS cnt\n"
            "FROM catalog.db.products\n"
            "GROUP BY spark_safe_date_format(created_at,'yyyy-MM')\n"
            "ORDER BY month, series"
        ),
    ),
]


# ============================================================================
# 8. 顶层 Spec —— LLM 唯一构造的对象
# ============================================================================

SPEC = Spec(
    title='🏢 零售业务驾驶舱（全量参考示范）',

    # workspace_id 必须留空，wedatacli 自动注入！禁止 echo $TENCENTCLOUD_WORKSPACE_ID 探测
    # workspace_id='',

    source=SRC,
    kpis=KPIS,
    charts=CHARTS,

    # ---- 渲染配置 ----
    theme='retail',          # retail / alarm / operations / education / executive
    grid_columns=4,          # 默认 4 列；span ≤ grid_columns

    # ---- 三端统一入库 ----
    # 无需配置：runner 自动完成 emit_dsl + UpdateAiKanBan(PREVIEW) 写入；
# AccessKey 由 runner 从 <workspace_folder>/.kanban_output/kanban_save_params.json 自动读取，无需在 spec 中传。
)


if __name__ == '__main__':
    # 唯一允许的入口：build_kanban(SPEC)
    # runner 内部顺序：
    #   1) 全量取数 SQL → wedatacli query-sql（lakehouse + OLAP 同协议）→ CSV
    #   2) parse_time_column 解析时间字段
    #   3) 编译 Spec → SLOT_DATA / sqlSlots
    #   4) write_kanban_outputs（builder lint 兜底 + 准备 save_meta）
    #   5) emit_dsl（落 kanban_dsl.json + 一次性写入 kanban_save_params.json 的 HtmlContent/SqlSlots 为 DSL/Datasets）
    #   6) update_to_kanban_list（UpdateAiKanBan 写 PREVIEW；三端统一入库权威源）
    #   7) print 追问语 → 立即 stop（等用户输入"保存"/"更新"再走 Step G）
    build_kanban(SPEC)


# ============================================================================
# 9. 反例字典 → 已迁移至同目录 kanban_spec_pitfalls.py（按需查阅）
# ----------------------------------------------------------------------------
# 写新 spec 时**不必读** pitfalls：本文件 1-8 节的 16 类正例已涵盖所有合法形态。
# 仅当跑 build_kanban 后看到下列信号时，再 read kanban_spec_pitfalls.py 对账：
#   ① stderr 出现 [DSL] Chart "..." (kind=...) ... → 报错文本本身已含修法 A/B/C，
#      多数情况按提示改即可；需要更详细解释时再查 pitfalls 对应反例。
#   ② stderr 出现 ⚠️ [Runner][软告警] xxx 已应用 ORDER BY/LIMIT 兜底 → 不影响出图，
#      下次写 spec 时若想避免软告警，查 pitfalls 反例 14/15/19 写更优形态。
# 22 类反例索引见 pitfalls 文件头注释，按 [DSL] 报错关键字 grep 即可命中。
# ============================================================================
