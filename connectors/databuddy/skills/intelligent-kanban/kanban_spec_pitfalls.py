"""
============================================================================
kanban_spec_pitfalls.py —— 智能看板【反例字典】（按需查阅，非必读）
============================================================================

本文件目的：
  集中收录 22 类「DSL 在构造期就直接 raise」或「runner 软告警」的写法陷阱，
  每条都给「❌ 现象 / 根因 / ✅ 修法 A/B/C」，让 LLM 看到 [DSL] 报错或
  ⚠️ [Runner][软告警] 时可定位到对应反例直接照抄修法。

🛑 本文件不是必读：
  - 写新 spec 时只读 kanban_spec_example.py 即可（已含 16 类正例 + 数据保真要点）；
  - 仅当跑 runner 后看到 [DSL] / ⚠️ 软告警时，按下方索引 grep 关键字定位到对应反例。

📖 反例索引（按 [DSL] 报错关键字 / 现象快速定位）：
  反例 1  : boxplot 用聚合表达式 → 退化单点
  反例 2  : radar 只给 1~2 个 metric → 无意义
  反例 3  : parallel dims 不足 3 个 → 无意义
  反例 4  : candlestick 缺 open/close/low/high 角色
  反例 5  : Metric 塞进 dims / Dim 塞进 metrics → 错位
  反例 6  : chart('line', metrics=['mom_xxx']) 假装同环比
  反例 7  : funnel/gauge 给了 dims（多余）
  反例 8  : raw_sql 不带 escape_hatch / slot_columns
  反例 9  : time_dim 不传 label → 前端轴名是 'time'
  反例 10 : dim 表达式含聚合（GROUP BY 不能含聚合）
  反例 11 : order_by 数字索引越界
  反例 12 : 手写 CAST/TRY_CAST 兜底（runner 已按 source.columns 类型读 CSV）
  反例 13 : source.columns 漏写 type → AVG/SUM 在 VARCHAR 列上报 No function matches
  反例 14 : scatter 朴素 limit（无 order_by）→ 砍随机行致失真   ⚠️ DSL 已 raise
  反例 15 : boxplot 用高基数维度 → 渲染崩溃
  反例 16 : parallel 行级裸列 → 爆数据                        ⚠️ DSL 已 raise
  反例 17 : graph 边模式无 limit → 关系图变毛球               ⚠️ DSL 已 raise
  反例 18 : table 显式 limit 但无 order_by → 抽样失真         ⚠️ DSL 已 raise
  反例 19 : heatmap 高基数双维 → 单元格不可见
  反例 20 : parallel 前 N-1 维混入行级表达式 → 表头无数据行   ⚠️ DSL 已 raise
  反例 21 : scatter 裸分类列做 dims[0] → 退化为竖线           ⚠️ DSL 已 raise
  反例 22 : candlestick 4 角色 expr 完全相同 → 一字 K 线      ⚠️ DSL 已 raise
  反例 23 : 日期差方言（DATE_DIFF / DATEDIFF 三参数）→ 链式返工 ⚠️ DSL 已 raise
  反例 24 : 普通 DSL 写窗口/嵌套聚合累计趋势 → GROUP BY 冲突     ⚠️ DSL 已 raise
  反例 25 : raw_sql 裸时间函数 / 同层窗口 → sqlSlots lint 拦截

  标 "⚠️ DSL 已 raise" 的反例：报错文本本身就带完整修法 A/B/C，按提示改即可，
  不用读本文件；其余反例多在 runner 软告警 / 前端无数据时才需要查。

本区块用 `if False:` 包裹，永不执行；仅作字典查阅用，导入后无副作用。
============================================================================
"""

import os
import sys

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

from kanban_dsl import (
    Spec, source,
    kpi, metric, Metric,
    dim, time_dim, Dim,
    chart, compare, raw_sql,
)


if False:
    # ---------- ❌ 反例 1：boxplot 用聚合表达式 ----------
    # 现象：跑通 → 前端无数据。原因：runner 内部已对 boxplot value 做
    #       percentile_approx 求五数概括；再喂聚合 → 退化成单点。
    chart('boxplot', '各状态订单分布',
          dims=['status'],
          metrics=['COUNT(order_id)'])           # ❌ 聚合
    # ✅ 修法 A：表里有行级数值列时直接用
    chart('boxplot', '各品类价格分布',
          dims=['category'],
          metrics=[metric('price', label='价格')])
    # ✅ 修法 B：表里没有行级数值列时换 bar 展示分类计数
    chart('bar', '各状态订单数',
          dims=['status'],
          metrics=[metric('COUNT(order_id)', label='订单数')],
          order_by='-COUNT(order_id)')

    # ---------- ❌ 反例 2：radar 只给 1~2 个 metric ----------
    # 雷达至少 3 个轴才有意义
    chart('radar', '单轴雷达',
          dims=['category'],
          metrics=[metric('SUM(amount)', label='销售')])         # ❌ <3
    # ✅ 修法：≥3 个 metric，全部 normalize='max-norm'
    chart('radar', '品类多维',
          dims=['category'],
          metrics=[
              metric('SUM(amount)', label='销售', normalize='max-norm'),
              metric('SUM(qty)',    label='件数', normalize='max-norm'),
              metric('AVG(price)',  label='均价', normalize='max-norm'),
          ])

    # ---------- ❌ 反例 3：parallel dims 不足 3 个 ----------
    # 平行坐标 dims = 前 N-1 轴 + 最后 1 个分类，至少 3 个
    chart('parallel', '两轴平行',
          dims=['amount', 'qty'])                                # ❌ <3
    # ✅ 修法：至少 3 个 dim（含最后一维分类）
    chart('parallel', '多维平行',
          dims=[
              dim('SUM(amount)', alias='amt', label='销售额'),
              dim('SUM(qty)',    alias='qty', label='件数'),
              dim('AVG(price)',  alias='ap',  label='均价'),
              dim('region',                    label='地区'),    # 最后一维=分类
          ])

    # ---------- ❌ 反例 4：candlestick 缺角色 ----------
    chart('candlestick', '半截 K 线',
          dims=[time_dim('time','day')],
          metrics=[
              metric('AVG(open_price)',  role='open'),
              metric('AVG(close_price)', role='close'),
          ])                                                     # ❌ 缺 low/high
    # ✅ 修法：4 个 metric 角色全齐
    chart('candlestick', 'K 线',
          dims=[time_dim('time','day')],
          metrics=[
              metric('AVG(open_price)',  role='open',  label='开'),
              metric('AVG(close_price)', role='close', label='收'),
              metric('MIN(low_price)',   role='low',   label='低'),
              metric('MAX(high_price)',  role='high',  label='高'),
          ])

    # ---------- ❌ 反例 5：把 Metric 塞进 dims / 把字段塞进 metrics 当维度 ----------
    chart('bar', '错位',
          dims=[metric('SUM(x)')],                               # ❌ Metric 进 dims
          metrics=[dim('category')])                             # ❌ Dim 进 metrics
    # ✅ 修法：维度走 dim/time_dim，度量走 metric
    chart('bar', '正确',
          dims=[dim('category', label='品类')],
          metrics=[metric('SUM(amount)', label='销售额')])

    # ---------- ❌ 反例 6：用 chart('line', metrics=[..., 'mom_xxx']) 假装同环比 ----------
    chart('line', '月环比',
          dims=[time_dim('time','month')],
          metrics=['SUM(amount)', 'mom_amount'])                 # ❌ 假同环比
    # ✅ 修法：必须用独立的 compare()
    compare(title='月度销售环比',
            dim=time_dim('time','month'),
            metric=metric('SUM(amount)', label='销售额'),
            kinds=['mom'])

    # ---------- ❌ 反例 7：funnel/gauge 给了 dims ----------
    chart('funnel', '错漏斗', dims=['stage'],                     # ❌ funnel 不要 dims
          metrics=[metric('COUNT(*)', label='UV1'),
                   metric('COUNT(DISTINCT user_id)', label='UV2')])
    chart('gauge', '错仪表', dims=['region'],                     # ❌ gauge 不要 dims
          metrics=[metric('SUM(done)*100.0/NULLIF(SUM(total),0)',
                          label='完成率', target=100.0)])
    # ✅ 修法：funnel/gauge 都不需要 dims；每个 metric.label 即阶段名/标题
    chart('funnel', '转化漏斗',
          metrics=[metric('COUNT(DISTINCT user_id)',                                  label='浏览'),
                   metric('COUNT(DISTINCT CASE WHEN qty>0 THEN user_id END)',         label='下单'),
                   metric('COUNT(DISTINCT CASE WHEN amount>0 THEN user_id END)',      label='付款')])
    chart('gauge', '完成率',
          metrics=[metric('SUM(done)*100.0/NULLIF(SUM(total),0)',
                          label='完成率', format='.1f', suffix='%', target=100.0)])

    # ---------- ❌ 反例 8：raw_sql 不带 escape_hatch / slot_columns ----------
    raw_sql(title='没声明逃生口',
            kind='table',
            sql='SELECT a,b FROM t',
            slot_columns=[])                                     # ❌ 列序为空
    # ✅ 修法：escape_hatch=True 由工厂自动给；slot_columns 必须**严格**等于 SELECT 列序
    raw_sql(title='地区 Top3',
            kind='table', span=4,
            slot_columns=['region','product_name','amount','rk'],
            sql="WITH ... SELECT region, product_name, amount, rk FROM ranked")

    # ---------- ❌ 反例 9：time_dim 不传 label，前端轴标签全是 'time' ----------
    chart('line', '时间无标签',
          dims=[time_dim('time','month')],                       # ⚠️ 能跑，但前端轴名=time
          metrics=['SUM(amount)'])
    # ✅ 推荐：time_dim 也支持 label/alias 等所有 Dim 字段
    chart('line', '月销售',
          dims=[time_dim('time','month', label='月份')],
          metrics=[metric('SUM(amount)', label='销售额')])

    # ---------- ❌ 反例 10：dim 表达式含聚合（GROUP BY 不能含聚合）----------
    # 报错：[DSL] Chart "..." dims[0].expr 不能含聚合函数
    # 例外：parallel 的前 N-1 维 / table 的列允许聚合（设计就是把聚合结果当列/轴）
    chart('scatter', '价格-销量',
          dims=[dim('AVG(price)', alias='avg_price')],            # ❌ 聚合进 dim
          metrics=[metric('SUM(qty)')])
    # ✅ 修法 A：用行级 CASE WHEN 分桶
    chart('scatter', '价格区间-销量',
          dims=[dim("CASE WHEN price<50 THEN 'L' "
                    "WHEN price<200 THEN 'M' ELSE 'H' END",
                    alias='price_tier', label='价格段')],
          metrics=[metric('SUM(qty)', label='件数')])
    # ✅ 修法 B：聚合放 metrics，分组维换裸列
    chart('bar', '品类件数',
          dims=[dim('category', label='品类')],
          metrics=[metric('AVG(price)', label='均价'),
                   metric('SUM(qty)',   label='件数')])

    # ---------- ❌ 反例 11：order_by 用数字索引时把 dims 当 0 号 / 越界 ----------
    # runner 0-based → SQL 1-based 自动转换。但**索引必须在 dims+metrics 总数内**，
    # 否则 DSL 直接拒绝，避免到 DuckDB 才报 'ORDER BY position out of range'。
    chart('bar', '越界排序',
          dims=[dim('category')],
          metrics=[metric('SUM(amount)')],
          order_by='-5')                                          # ❌ 总共 2 列，索引 5 越界
    # ✅ 修法：用别名/表达式更直观，避免数字索引
    chart('bar', '按销售降序',
          dims=[dim('category', label='品类')],
          metrics=[metric('SUM(amount)', label='销售额')],
          order_by='-SUM(amount)')                                # ✅ 推荐：表达式
    # 或用 dim/metric 别名
    chart('bar', '按品类升序',
          dims=[dim('category', alias='cat', label='品类')],
          metrics=[metric('SUM(amount)', label='销售额')],
          order_by='cat')                                         # ✅ 用 dim alias

    # ---------- ❌ 反例 12：CSV 中 NULL 字面量被当字符串 'null' 触发 CAST 失败 ----------
    # 这是历史返工最高频的坑：在 spec 里手写 CAST(col AS BIGINT) 试图修复，结果遇到
    # 'null' 字符串还是炸。runner 已在 _open_duck 用 read_csv(columns=..., nullstr=[...])
    # 显式按 source.columns 类型读取，**所以 spec 不要再手写 CAST/TRY_CAST 兜底**。
    chart('bar', '手写 CAST 兜底',
          dims=[dim('category')],
          metrics=['SUM(TRY_CAST(amount AS DOUBLE))'])             # ❌ 没必要
    # ✅ 修法：source.columns 写对类型即可，runner 会让 DuckDB 按类型读 CSV
    # source(table='...', columns=[
    #     {'name':'amount','type':'double'},   # ← 关键：把类型抄全
    #     {'name':'qty',   'type':'bigint'},
    # ], time_col='time', time_type='string')
    chart('bar', '直接聚合',
          dims=[dim('category')],
          metrics=[metric('SUM(amount)', label='销售额')])         # ✅ 直接 SUM

    # ---------- ❌ 反例 13：source.columns 漏写类型，整列被推断为 VARCHAR ----------
    # 现象：'AVG/SUM 在 VARCHAR 列上报 No function matches'。
    # 根因：columns 里只给了 name 没给 type → DuckDB 自动推断不可靠。
# ✅ 修法：prefetch_table.py 输出的 schema JSON 中 type 字段必须**整列抄过来**，不要省略。

    pass

    # ---------- ❌ 反例 14：scatter 行级裸列 + 朴素 limit（无 order_by）→ 数据失真 ----------
    # 现象：底表 100w 行，写 limit=1000 想控制 HTML 体积。
    # 根因：runner 生成 SQL 是 `SELECT x,y FROM t LIMIT 1000`，**砍掉的是不可控的随机 1000 行**。
    #       散点云的极值（min/max/p99）大概率被砍 → 相关性、上沿、离群点全丢，统计意义为零。
    # 结果：图能渲染、HTML 也小，但用户看到的是「失真的散点云」，比不画还误导。
    chart('scatter', '价格-销量散点',
          dims=[dim('price'), dim('category')],
          metrics=[metric('qty')],
          limit=1000)                                            # ❌ 无 order_by 的 LIMIT
    # ✅ 修法 A：小数据（≤ 500 行）→ 不要 limit 或设大 limit + order_by 兜底
    #     提示：source.columns 用 dict 形态声明 type 后，double 裸列可直接喂给 dims[0]；
    #          仅当 source 用纯字符串列名时才需要 `dim('price * 1.0', alias='price')`。
    chart('scatter', '价格-销量散点（小数据全展示）',
          dims=[dim('price', label='价格'), dim('category', label='品类')],
          metrics=[metric('qty', label='件数')],
          limit=500, order_by='-y')                              # ✅ scatter SELECT 输出固定为 x/y/category；order_by 必须用 -y 而非 metric.alias
    # ✅ 修法 B：大数据（> 50K 行）→ 用 CASE WHEN 业务分桶，让 runner 自动聚合（见 example 5.4）
    chart('scatter', '价格区间-销量分布',
          dims=[
              dim("CASE WHEN price<50 THEN '<50' "
                  "WHEN price<200 THEN '50-200' ELSE '200+' END",
                  alias='price_tier', label='价格段'),
              dim('category', label='品类'),
          ],
          metrics=[metric('SUM(qty)', label='总件数')])          # ✅ 含聚合 → 自动 GROUP BY

    # ---------- ❌ 反例 15：boxplot 用高基数维度（product_id/user_id 等）→ 渲染崩溃 ----------
    # 现象：dims 给 product_id（基数过万）→ 输出 SLOT 数万行，前端 echarts 渲染崩。
    # 根因：boxplot 行数 = 分类基数；basic 直出无 limit 兜底（_ad_box SQL 不应用 c.limit）。
    # 同时：单箱样本量极少（每个 product_id 可能只有几行）→ 五数概括统计意义失效。
    chart('boxplot', '商品价格分布',
          dims=[dim('product_id', label='商品ID')],               # ❌ 基数过万
          metrics=[metric('price', label='价格')])
    # ✅ 修法 A：换 kind 为 bar，做价格分桶直方图（高基数下更有业务意义）
    chart('bar', '商品价格分布直方图',
          dims=[dim("CASE WHEN price<50 THEN '<50' "
                    "WHEN price<200 THEN '50-200' "
                    "WHEN price<1000 THEN '200-1000' ELSE '1000+' END",
                    alias='price_bucket', label='价格段')],
          metrics=[metric('COUNT(*)', label='商品数')],
          order_by='price_bucket')
    # ✅ 修法 B：分类基数 20~100（如 sub_category）→ 走 raw_sql 限定 Top20 主力分组
    raw_sql(
        title='Top20 子类价格箱线',
        kind='boxplot', span=4,
        slot_columns=['category', 'min', 'q1', 'median', 'q3', 'max'],
        sql=(
            "WITH top_grp AS (\n"
            "  SELECT sub_category FROM retail_db.dwd.fact_sales_daily\n"
            "  WHERE amount IS NOT NULL\n"
            "  GROUP BY sub_category ORDER BY COUNT(*) DESC LIMIT 20\n"
            ")\n"
            "SELECT t.sub_category AS category,\n"
            "       MIN(t.price) AS `min`,\n"
            "       percentile_approx(t.price, 0.25) AS q1,\n"
            "       percentile_approx(t.price, 0.5)  AS median,\n"
            "       percentile_approx(t.price, 0.75) AS q3,\n"
            "       MAX(t.price) AS `max`\n"
            "FROM retail_db.dwd.fact_sales_daily t\n"
            "INNER JOIN top_grp USING(sub_category)\n"
            "WHERE t.amount IS NOT NULL\n"
            "GROUP BY t.sub_category\n"
            "ORDER BY MAX(t.price) DESC"
        ),
    )

    # ---------- ❌ 反例 16：parallel 行级原始数据无聚合 → 爆数据 ----------
    # 现象：50w 行底表，dims 全是裸列名，echarts.parallel 直接渲染 50w 条线 → 浏览器死掉。
    # 根因：parallel 是"多维平行坐标轴"，每行一条折线；行数 = 底表行数。
    # DSL 构造期硬约束（sampling_rule='must_aggregate_or_limit'）会直接 raise，
    # 但若用 raw_sql 旁路绕过 DSL，runner 还会自动 LIMIT 500 兜底（仍打软告警）。
    chart('parallel', '多维剖面（错误）',
          dims=[
              dim('lat'),                                         # ❌ 行级裸列
              dim('lng'),                                         # ❌ 行级裸列
              dim('zip'),                                         # ❌ 行级裸列
              dim('state'),                                       # 最后一维分类（OK）
          ])                                                      # ❌ 既无 limit 也无聚合
    # ✅ 修法 A（推荐，按业务维度聚合）：前 N-1 轴改为聚合表达式
    chart('parallel', '州维多指标剖面',
          dims=[
              dim('AVG(lat)', alias='avg_lat', label='均纬'),
              dim('AVG(lng)', alias='avg_lng', label='均经'),
              dim('AVG(zip)', alias='avg_zip', label='均邮编'),
              dim('state', label='州'),                           # 最后一维 = 分类色标
          ])                                                      # runner 自动 GROUP BY state
    # ✅ 修法 B（小数据 TopN）：保持行级形态但显式 limit ≤ 1000
    chart('parallel', '行级 Top500 剖面',
          dims=[dim('lat'), dim('lng'), dim('zip'), dim('state')],
          limit=500)                                              # 显式 limit ≤ 1000 即可

    # ---------- ❌ 反例 17：graph 边模式无 limit → 关系图变毛球 ----------
    # 现象：state×city = 27×8000 共 8000+ 边一次性渲染，echarts force layout 卡死。
    # 根因：边数 = source 基数 × target 基数；不限边数则视觉退化为黑色毛球，无法读出关系。
    # DSL 构造期硬约束（sampling_rule='edge_mode_needs_limit'）会直接 raise。
    # ⚠️ 另：节点模式（dims=1）用 LEAD 窗口函数串联 Top-K 节点，生成的边是
    #     "排名相邻"而非真实业务关联，容易误导。推荐优先使用边模式（dims=[source, target]）。
    chart('graph', '州→城市关系',
          dims=[dim('state'), dim('city')],                       # 边模式（dims=2）
          metrics=[metric('COUNT(*)')])                           # ❌ 缺 limit
    # ✅ 修法：limit + order_by 取 Top30 关键边
    chart('graph', '州→城市 Top30 关系',
          dims=[dim('state', label='州'), dim('city', label='城市')],
          metrics=[metric('COUNT(*)', label='记录数')],
          limit=30, order_by='-COUNT(*)')

    # ---------- ❌ 反例 18：table 显式 limit 但无 order_by → 抽样失真 ----------
    # 现象：底表 50w 行，写 limit=30 想看明细。
    # 根因：runner 生成 `SELECT ... FROM t LIMIT 30`，远端 Spark 按物理扫描顺序返回前 30 行
    #       → 几乎全是同一个州/同一邮编段，**完全没代表性**（连"采样"都谈不上）。
    # DSL 构造期硬约束（sampling_rule='limit_requires_order_by'）会直接 raise。
    chart('table', '原始明细 Top30',
          dims=['state', 'city', 'zip', 'lat', 'lng'],
          limit=30)                                               # ❌ 缺 order_by
    # ✅ 修法 A：补 order_by，让截断有业务含义
    chart('table', '邮编最大 Top30',
          dims=[dim('state', label='州'), dim('city', label='城市'),
                dim('zip', label='邮编')],
          order_by='-zip', limit=30)
    # ✅ 修法 B（推荐大数据量）：改用聚合维度，runner 自动收敛行数
    chart('table', '州·城市记录榜',
          dims=['state', 'city'],
          metrics=[metric('COUNT(*)', label='记录数'),
                   metric('AVG(lat)', label='均纬'),
                   metric('AVG(lng)', label='均经')],
          order_by='-COUNT(*)')                                   # 聚合后 runner 自动 >500 截 50

    # ---------- ❌ 反例 19：heatmap 高基数双维 → 单元格不可见 ----------
    # 现象：dims=[city, product]（8000×5000）→ 4000w 单元格送前端，浏览器死掉。
    # 根因：heatmap 单元格 = X 基数 × Y 基数；超过 30×30=900 时单元格像素 < 1，不可读。
    # 双层防护：① 写 spec 时就避免高基数双维；② 即使写了，runner 在 X×Y > 900 时
    #          自动按 X、Y 各自 Top30（按总值排序）交叉截断，并打软告警。
    chart('heatmap', '城市×品类热力（高基数）',
          dims=['city', 'product'],                                # ❌ 8000×5000 基数双维
          metrics=[metric('COUNT(*)')])
    # ✅ 修法 A：换更粗的维度（city → state, product → category）
    chart('heatmap', '州×品类热力',
          dims=[dim('state', label='州'), dim('category', label='品类')],
          metrics=[metric('COUNT(*)', label='记录数')])
    # ✅ 修法 B（必须用细维度时）：raw_sql 用 CTE 显式取各维 Top30 后再交叉
    raw_sql(
        title='Top30 城市 × Top30 品类热力',
        kind='heatmap', span=4,
        slot_columns=['city', 'category', 'cnt'],
        sql=(
            "WITH top_city AS (\n"
            "  SELECT city FROM retail_db.dwd.fact_sales_daily\n"
            "  GROUP BY city ORDER BY COUNT(*) DESC LIMIT 30\n"
            "), top_cat AS (\n"
            "  SELECT category FROM retail_db.dwd.fact_sales_daily\n"
            "  GROUP BY category ORDER BY COUNT(*) DESC LIMIT 30\n"
            ")\n"
            "SELECT t.city, t.category, COUNT(*) AS cnt\n"
            "FROM retail_db.dwd.fact_sales_daily t\n"
            "INNER JOIN top_city USING(city)\n"
            "INNER JOIN top_cat  USING(category)\n"
            "GROUP BY t.city, t.category\n"
            "ORDER BY t.city, t.category"
        ),
    )

    # ---------- ❌ 反例 20：parallel 前 N-1 维混入行级表达式 → 图表表头无数据行 ----------
    # 现象：parallel 跑通无报错，HTML 渲染出来只有坐标轴框架和表头，**一条折线都没有**。
    # 根因：parallel 的语义是「按最后一维分组的多维聚合剖面」，runner 生成的 SQL 形如：
    #         SELECT <axis_1>, <axis_2>, ..., <axis_N-1>, <category> AS dim_last
    #         FROM t GROUP BY <category>
    #       前 N-1 个 axis 必须是聚合表达式（SUM/AVG/COUNT/...），它们才能在 GROUP BY <category>
    #       的语境下合法存在。一旦混入裸列名 / 行级表达式（如 HOUR(time) / status / lat 等）：
    #         · Spark 严格模式 → 直接报 `not in GROUP BY clause and is not an aggregate function`
    #         · DuckDB 宽松模式 → 静默剔除 / 任意取一行 → 远端聚合后**返空集** → 表头无数据行
    # 注意：DSL 构造期硬约束（sampling_rule='must_aggregate_or_limit' + parallel 形态契约）
    #       会在 Chart(...) 那一刻直接 raise `[DSL] Chart "..." (kind=parallel) 前 N-1 个维度
    #       必须全部是聚合表达式`，根本走不到 SQL 层。
    chart('parallel', '订单履约多维剖面（错误：混入 HOUR）',
          dims=[
              dim('COUNT(order_id)',                alias='order_cnt'),  # ✅ 聚合
              dim('HOUR(approved_at)',              alias='approve_hr'),  # ❌ 行级！
              dim('AVG(price)',                     alias='avg_price'),  # ✅ 聚合
              dim('order_status', label='状态'),                           # 最后一维=分类
          ])
    chart('parallel', '州维多指标剖面（错误：第二轴是裸列）',
          dims=[
              dim('AVG(lat)', alias='avg_lat'),                           # ✅
              dim('zip',      alias='zip_raw'),                           # ❌ 裸列
              dim('AVG(lng)', alias='avg_lng'),                           # ✅
              dim('state', label='州'),
          ])
    # ✅ 修法 A（推荐·把行级表达式包成聚合）：让运算先发生再聚合
    chart('parallel', '订单履约多维剖面',
          dims=[
              dim('COUNT(order_id)',                       alias='order_cnt',  label='订单数'),
              dim('AVG(HOUR(approved_at))',                alias='avg_hour',   label='均审批时'),
              dim('AVG(price)',                            alias='avg_price',  label='均价'),
              dim('AVG(DATEDIFF(spark_safe_to_timestamp(delivered_at), '
                  'spark_safe_to_timestamp(purchase_at)))', alias='avg_lead',   label='平均时长'),
              dim('order_status', label='状态'),                            # 最后一维=分类
          ])
    # ✅ 修法 B（数据形态确实需要行级原始值）：改用 limit ≤ 1000 的行级 parallel
    chart('parallel', '行级 Top500 订单剖面',
          dims=[dim('price'), dim('qty'), dim('lead_days'), dim('order_status')],
          limit=500, order_by='-price')                                  # 显式 limit + order_by

    # ---------- ❌ 反例 21：scatter x 轴用裸分类列 → 退化为竖线 / NaN ----------
    # 现象：scatter 渲染出来所有点垂直堆在 x=0 / x=NaN 一处，或者只有一条竖线，散点图
    #       的「两个数值变量分布关系」语义完全丧失。
    # 根因：echarts.scatter 默认 xAxis.type='value' 是数值轴，传字符串类目时：
    #         · 部分版本 → NaN 全部叠在原点
    #         · 部分版本 → 强制按字典序映射成 1/2/3... 但失去原始语义
    #       散点图的全部价值在于「x 与 y 的相关性」，x 是分类时这种相关性无从谈起，应该
    #       用 bar/heatmap 表达「分类 × 度量」，而不是硬套 scatter。
    # DSL 构造期硬约束会直接 raise `[DSL] Chart "..." (kind=scatter) dims[0]='...'
    # 看起来是分类列`，把这类误用堵在源头。
    chart('scatter', '状态-审批时长散点（错误：x 是分类）',
          dims=[
              dim('order_status', label='状态'),                          # ❌ 裸分类列
              dim('region', label='地区'),
          ],
          metrics=[metric('AVG(lead_days)', label='均时长')])
    # ✅ 修法 A（业务分桶·推荐）：把分类映射为有序数值序号，保留分类语义同时拥有数值轴
    chart('scatter', '状态评分-审批时长散点',
          dims=[
              dim("CASE WHEN order_status='created'   THEN 1 "
                  "      WHEN order_status='approved' THEN 2 "
                  "      WHEN order_status='shipped'  THEN 3 "
                  "      WHEN order_status='delivered' THEN 4 "
                  "      ELSE 0 END",
                  alias='status_score', label='状态评分'),               # ✅ 数值映射
              dim('region', label='地区'),                                # 第二维=色标
          ],
          metrics=[metric('AVG(lead_days)', label='均时长')])
    # ✅ 修法 B（两轴都换成真正的数值列/聚合）：才是 scatter 的最佳形态
    #     提示：source.columns 已用 dict 形态声明 type 时，double 裸列名可直接传入 dims[0]
    #           （DSL 会按 type 字段放行）；只有纯字符串列名（无 type 元信息）时才需要
    #           `dim('price * 1.0', alias='price')` 这种 *1.0 包装。
    chart('scatter', '审批时长-履约时长散点',
          dims=[
              dim('DATEDIFF(spark_safe_to_timestamp(approved_at), '
                  'spark_safe_to_timestamp(purchase_at))',
                  alias='approve_days', label='审批天数'),                # ✅ 行级数值
              dim('region', label='地区'),
          ],
          metrics=[metric('AVG(lead_days)', label='均履约天数')])
    # ✅ 修法 C（其实需求不是散点）：换 kind='bar' 直接做分类对比，更直观
    chart('bar', '各状态平均审批时长',
          dims=[dim('order_status', label='状态')],
          metrics=[metric('AVG(lead_days)', label='均时长')],
          order_by='-AVG(lead_days)')

    # ---------- ❌ 反例 22：candlestick 4 角色 expr 完全相同 → 一字 K 线 ----------
    # 现象：K 线每个时间点都是一根孤零零的横线（开=收=高=低），整张图视觉等同于折线
    #       且毫无振幅，candlestick 完全失去存在意义。
    # 根因：candlestick 的视觉语义来源于 4 个角色的差异（开盘 / 收盘 / 最低 / 最高）。
    #       当 spec 把 4 个 metric.expr 写成同一个聚合（如全是 COUNT(order_id)），
    #       SQL 生成的 4 列每行数值完全相等 → echarts.candlestick 收到 [c, c, c, c] →
    #       实心矩形高度=0、影线长度=0 → 退化成一条横线。
    # 典型踩坑：用户拿没有真实价格序列的事实表（如订单事实表）硬套 candlestick，
    #       4 个角色全用 COUNT 凑数；或者复制粘贴时手抖把 4 行 metric 写成同一个 expr。
    # DSL 构造期硬约束会直接 raise `[DSL] Chart "..." (kind=candlestick) 4 个角色
    # metric 表达式完全相同：'COUNT(ORDER_ID)'`。
    chart('candlestick', '订单 K 线（错误：4 角色全 COUNT）',
          dims=[time_dim('time','day')],
          metrics=[
              metric('COUNT(order_id)', role='open',  label='开'),       # ❌
              metric('COUNT(order_id)', role='close', label='收'),       # ❌ 与 open 同源
              metric('COUNT(order_id)', role='low',   label='低'),       # ❌
              metric('COUNT(order_id)', role='high',  label='高'),       # ❌
          ])
    # ✅ 修法 A（真实价格序列·首选）：四角色对应业务上的开盘/收盘/最低/最高
    chart('candlestick', '价格 K 线',
          dims=[time_dim('time','day')],
          metrics=[
              metric('FIRST(price)', role='open',  label='开'),          # 当日首单价
              metric('LAST(price)',  role='close', label='收'),          # 当日末单价
              metric('MIN(price)',   role='low',   label='低'),
              metric('MAX(price)',   role='high',  label='高'),
          ])
    # ✅ 修法 B（无价格列·业务语义凑差异）：用不同业务聚合让 4 角色天然分化
    chart('candlestick', '订单业务 K 线',
          dims=[time_dim('time','day')],
          metrics=[
              metric('COUNT(order_id)',                                   role='open',  label='总订单'),
              metric("SUM(CASE WHEN order_status='delivered' THEN 1 ELSE 0 END)",
                                                                          role='close', label='已交付'),
              metric('LEAST(COUNT(order_id), COUNT(DISTINCT customer_id))',
                                                                          role='low',   label='下界'),
              metric('GREATEST(COUNT(order_id), COUNT(DISTINCT customer_id))',
                                                                          role='high',  label='上界'),
          ])
    # ✅ 修法 C（数据不适合 K 线）：直接换 line/bar，别硬套
    chart('line', '日订单数走势',
          dims=[time_dim('time','day')],
          metrics=[metric('COUNT(order_id)', label='订单数')])

    # ---------- ❌ 反例 23：日期差方言（DATE_DIFF / DATEDIFF 三参数）→ 链式返工 ----------
    # 现象：写「剩余天数 / 超预计送达 / 履约延误」类风险看板时，LLM 高频踩四种坑：
    #         ① DATEDIFF(DAY, start, end)       ← SQL Server / Presto 关键字风格三参
    #         ② DATE_DIFF('day', start, end)    ← Presto 字符串风格三参
    #         ③ DATE_DIFF(DAY, start, end)      ← Presto 关键字风格三参
    #         ④ DATE_DIFF(end, start)           ← 函数名拼错（Spark 是 DATEDIFF 没下划线）
    # 链式返工链路（DSL 拦截前）：①③ 走"列引用强校验"被识别为「未声明列 DAY」→ LLM 反复改
    #   列名；② builder lint 才报 PRESTO_DATEDIFF，浪费一次取数往返；④ 报「未声明列 DATE_DIFF」
    #   与列名拼写错误混淆。最终常以"删掉超时/紧急程度核心逻辑"换跑通，业务表达降级。
    # 根因：远端 Spark 与本地 runner 仅支持 Spark 两参 `DATEDIFF(end, start)`，三参版/带下划
    #   线版都属于 Presto / SQL Server 方言。
    # DSL 构造期硬约束（前置于列引用校验）会直接 raise:
    #   `[DSL] 检测到非 Spark 日期差方言（共 N 处）...`，文案带 canonical 写法 + 风险模板指引。
    chart('bar', '紧急程度分布（错误：关键字三参）',
          dims=[
              dim("CASE WHEN DATEDIFF(DAY, CURRENT_TIMESTAMP, "           # ❌ ①
                  "spark_safe_to_timestamp(order_estimated_delivery_ts))<0 "
                  "THEN '超时' ELSE '正常' END",
                  alias='risk_level', label='风险'),
          ],
          metrics=[metric('COUNT(*)', label='订单数')])
    chart('bar', '紧急程度分布（错误：Presto 字符串三参）',
          dims=[
              dim("CASE WHEN DATE_DIFF('day', "                            # ❌ ②
                  "spark_safe_to_timestamp(order_purchase_at), "
                  "CURRENT_TIMESTAMP)>30 THEN '超时' ELSE '正常' END",
                  alias='risk_level')],
          metrics=[metric('COUNT(*)')])
    chart('bar', '紧急程度分布（错误：函数名拼错）',
          dims=[dim('order_status')],
          metrics=[metric('AVG(DATE_DIFF(spark_safe_to_timestamp(end_at), '   # ❌ ④
                          'spark_safe_to_timestamp(start_at)))', label='均时长')])
    # ✅ 修法 A（首选·剩余天数 / 超时判断·与当前时间比较）：两参 + spark_safe_to_timestamp
    chart('bar', '紧急程度分布',
          dims=[
              dim("CASE "
                  "  WHEN order_status='canceled' THEN '已取消' "
                  "  WHEN is_delivered=1 AND DATEDIFF("
                  "        spark_safe_to_timestamp(order_delivered_at), "
                  "        spark_safe_to_timestamp(order_estimated_delivery_ts))>0 THEN '已延误送达' "
                  "  WHEN is_delivered=0 AND spark_safe_to_timestamp(order_estimated_delivery_ts) "
                  "        < CURRENT_TIMESTAMP THEN '超预计未送达' "
                  "  WHEN is_delivered=0 AND DATEDIFF("
                  "        spark_safe_to_timestamp(order_estimated_delivery_ts), "
                  "        CURRENT_TIMESTAMP) <= 2 THEN '即将到期' "
                  "  WHEN is_delivered=1 THEN '正常送达' "
                  "  ELSE '履约中' END",
                  alias='risk_level', label='风险'),
          ],
          metrics=[metric('COUNT(*)', label='订单数')],
          order_by='-COUNT(*)')
    # ✅ 修法 B（履约时长统计·两个时间列差）：两参 + spark_safe_to_timestamp
    chart('bar', '各状态平均履约时长',
          dims=[dim('order_status', label='状态')],
          metrics=[metric(
              'AVG(DATEDIFF(spark_safe_to_timestamp(order_delivered_at), '
              'spark_safe_to_timestamp(order_purchase_at)))',
              label='均履约天数', format='.1f')],
          order_by='-AVG(DATEDIFF(spark_safe_to_timestamp(order_delivered_at), '
                   'spark_safe_to_timestamp(order_purchase_at)))')
    # ✅ 修法 C（剩余天数指标，越小越紧急 → 升序排）：两参，order_by 不带负号
    chart('table', '高风险订单明细 Top30',
          dims=[
              dim('order_id', label='订单'),
              dim('order_status', label='状态'),
              dim('order_estimated_delivery_ts', label='预计送达'),
              dim('DATEDIFF(spark_safe_to_timestamp(order_estimated_delivery_ts), '
                  'CURRENT_TIMESTAMP)',
                  alias='remaining_days', label='剩余天数'),
          ],
          order_by='remaining_days', limit=30)                    # ✅ 升序：负数（已超时）排最前
    # ⚠️ 历史数据集警示：Olist 类历史订单表用 CURRENT_TIMESTAMP 会把 2016~2018 全部判超时；
    #     更稳的策略是用数据快照日（如 source.where 里固定的 stat_date）或数据集最大时间作为锚点：
    #         dim('DATEDIFF(spark_safe_to_timestamp(order_estimated_delivery_ts), '
    #             "spark_safe_to_timestamp('2018-09-01'))", alias='remaining_days')
    #     真实在线履约表才用 CURRENT_TIMESTAMP。

    # ---------- ❌ 反例 24：普通 DSL 写窗口/嵌套聚合累计趋势 ----------
    # 现象：想做累计销售额，直接在 line metric 写 SUM(SUM(sales)) OVER (ORDER BY date)。
    # 根因：普通 DSL chart 会生成同层 SELECT + GROUP BY；metric 里再写窗口/嵌套聚合会触发
    #       Spark/DuckDB 的 nested aggregate 或 GROUP BY/window scope 冲突。
    # DSL 构造期会在 Spec 全局预检里一次性 raise：`检测到嵌套聚合` + `检测到窗口函数`。
    chart('line', '累计销售趋势（错误）',
          dims=[time_dim('date', 'day')],
          metrics=[metric('SUM(SUM(sales_revenue)) OVER (ORDER BY date)', label='累计销售')])
    # ✅ 修法：改 raw_sql，用 WITH 先聚合到日/月，再在外层做窗口累计；slot_columns 与 SELECT 同序。
    raw_sql(
        title='累计销售趋势', kind='line', span=4,
        slot_columns=['date_day', 'sales_revenue', 'cum_sales_revenue'],
        sql=(
            "WITH daily AS (\n"
            "  SELECT DATE_FORMAT(date, 'yyyy-MM-dd') AS date_day,\n"
            "         SUM(sales_revenue) AS sales_revenue\n"
            "  FROM retail_db.dwd.fact_sales_daily\n"
            "  GROUP BY DATE_FORMAT(date, 'yyyy-MM-dd')\n"
            ")\n"
            "SELECT date_day, sales_revenue,\n"
            "       SUM(sales_revenue) OVER (ORDER BY date_day) AS cum_sales_revenue\n"
            "FROM daily ORDER BY date_day"
        ),
    )

    # ---------- ❌ 反例 25：raw_sql 不是完全自由逃生口 ----------
    # 现象：用 raw_sql 绕过 DSL 后，裸写 DATE_FORMAT/YEAR/LPAD 或单层 LAG，sqlSlots lint 拦截。
    # 根因：raw_sql 只跳过 DSL 构造器，不跳过平台 sqlSlots 合规校验；lakehouse string 时间字段
    #       必须用 spark_safe_*，窗口函数必须 WITH 双层。OLAP sql_type=3 则按目标方言，禁 spark_safe_*。
    raw_sql(
        title='周销售趋势（错误）', kind='line', span=4,
        slot_columns=['week', 'sales', 'mom_pct'],
        sql=(
            "SELECT CONCAT(YEAR(order_time), '-W', LPAD(WEEKOFYEAR(order_time), 2, '0')) AS week,\n"
            "       SUM(sales) AS sales,\n"
            "       (SUM(sales)-LAG(SUM(sales)) OVER (ORDER BY week)) / NULLIF(LAG(SUM(sales)) OVER (ORDER BY week),0) AS mom_pct\n"
            "FROM retail_db.dwd.fact_sales_daily GROUP BY week ORDER BY week"
        ),
    )
    # ✅ 修法（lakehouse string 时间）：helper + WITH 双层；date/timestamp 物理列可用原生 DATE_FORMAT。
    raw_sql(
        title='周销售趋势', kind='line', span=4,
        slot_columns=['week', 'sales', 'mom_pct'],
        sql=(
            "WITH weekly AS (\n"
            "  SELECT spark_safe_week_format(order_time) AS week, SUM(sales) AS sales\n"
            "  FROM retail_db.dwd.fact_sales_daily\n"
            "  WHERE spark_safe_to_timestamp(order_time) IS NOT NULL\n"
            "  GROUP BY spark_safe_week_format(order_time)\n"
            ")\n"
            "SELECT week, sales,\n"
            "       (sales - LAG(sales) OVER (ORDER BY week)) / NULLIF(LAG(sales) OVER (ORDER BY week), 0) AS mom_pct\n"
            "FROM weekly ORDER BY week"
        ),
    )
