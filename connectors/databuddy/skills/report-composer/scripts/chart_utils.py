"""
chart_utils.py —— 从 pandas DataFrame 生成 ECharts option (dict) 的统一工具函数。

本脚本是 report-composer skill 生成数据产出 HTML 时的 Python 图表工具，
对应 reference/html.md 第 h 节「df_to_echarts_option() 工具函数规范」。

设计目标:
    - 单一入口 df_to_echarts_option() 覆盖 line / bar / pie / scatter / heatmap 5 种图表
    - 内置 NaN → None 转换（ECharts 吃 null 不吃 NaN）
    - 内置时间字段规范化（ISO 字符串或毫秒时间戳，杜绝 datetime64[ns]）
    - 内置浅色主题色序，自动注入 series.itemStyle.color
    - 大数据量自动启用 progressive + large
依赖:
    pip install pandas

使用方式:
    from chart_utils import df_to_echarts_option
    option = df_to_echarts_option(df, 'line', x='date', y='revenue', color='category')
    # 内嵌到 HTML:
    #     var opt = <json.dumps(option, ensure_ascii=False)>;
    #     chart.setOption(opt);
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Union

import pandas as pd

# -----------------------------------------------------------------------------
# 主题色序（与 html.md §c CSS 变量对齐）
# -----------------------------------------------------------------------------
DEFAULT_THEME_COLORS: List[str] = [
    "#636EFA",  # --color-primary
    "#00CC96",  # --color-secondary
    "#EF553B",  # --color-danger
    "#d4880f",  # --color-warning
    "#AB63FA",
    "#FFA15A",
    "#19D3F3",
    "#FF6692",
]

# 大数据量阈值（单 series 超过此阈值自动启用 progressive + large）
LARGE_THRESHOLD: int = 10_000


# -----------------------------------------------------------------------------
# 移动端 media query 模板（ECharts 原生 media，按容器宽度自动切换）
# -----------------------------------------------------------------------------
# 容器级配置（title/legend/grid/axisLabel）merge 安全，series 仅 pie/heatmap 改
# grid.left/right 取小值：containLabel=True 时 ECharts 已自动给轴标签留位，
# left/right 只是"标签框外侧到容器边的留白"，设大（如 40-60）= 纯浪费左/右空隙。
_MEDIA_768_BASE: dict = {
    "title": {"textStyle": {"fontSize": 14}},
    "legend": {"top": 32, "textStyle": {"fontSize": 11}, "itemGap": 8},
    "grid": {"top": 70, "bottom": 50, "left": 8, "right": 12, "containLabel": True},
    "xAxis": {"axisLabel": {"fontSize": 11}},
    "yAxis": {"axisLabel": {"fontSize": 11}},
}

_MEDIA_480_BASE: dict = {
    "title": {"textStyle": {"fontSize": 13}},
    "legend": {
        "bottom": 5, "top": "auto", "left": "center",
        "textStyle": {"fontSize": 10}, "itemGap": 6,
        "itemWidth": 14, "itemHeight": 8,
    },
    "grid": {"top": 50, "bottom": 60, "left": 8, "right": 8, "containLabel": True},
    "xAxis": {"axisLabel": {"fontSize": 10, "rotate": 30}},
    "yAxis": {"axisLabel": {"fontSize": 10}},
}


def _build_media(chart_type: str) -> List[dict]:
    """构造 ECharts 原生 media 字段，按 chart_type 给出 768/480 两档覆盖。

    ECharts merge 顺序：按数组顺序逐个 merge，后写覆盖先写。
    所以 768 写在前、480 写在后——480px 容器同时匹配两个 query，
    最终走 480 覆盖后的效果。
    """
    m768 = {k: dict(v) if isinstance(v, dict) else v for k, v in _MEDIA_768_BASE.items()}
    m480 = {k: dict(v) if isinstance(v, dict) else v for k, v in _MEDIA_480_BASE.items()}

    if chart_type == "pie":
        # 饼图三档：默认 outside label + name；768 仅显百分比；480 隐藏 label
        # 图例统一放底部（基础 option + _MEDIA_480_BASE 已是底部），避免顶部图例与外侧引导线标签打架
        m768["legend"] = {"bottom": 8, "top": "auto", "left": "center",
                          "textStyle": {"fontSize": 11}, "itemGap": 8}
        m768["series"] = [{
            "label": {"show": True, "formatter": "{d}%", "fontSize": 10},
        }]
        m480["series"] = [{
            "radius": ["28%", "58%"],
            "center": ["50%", "42%"],
            "label": {"show": False},
        }]
        # pie 没有 xAxis/yAxis，删掉避免无效 key
        m768.pop("xAxis", None); m768.pop("yAxis", None)
        m480.pop("xAxis", None); m480.pop("yAxis", None)

    elif chart_type == "bar":
        # 柱图 480：柱顶 label 隐藏避免拥挤
        m480["series"] = [{"label": {"show": False}}]

    elif chart_type == "heatmap":
        # 热力图 480：x 轴标签旋转 45 + visualMap 缩到底部
        m480["xAxis"]["axisLabel"]["rotate"] = 45
        m480["visualMap"] = {
            "orient": "horizontal", "bottom": 0, "left": "center",
            "itemWidth": 12, "itemHeight": 80,
            "textStyle": {"fontSize": 10},
        }

    return [
        {"query": {"maxWidth": 768}, "option": m768},
        {"query": {"maxWidth": 480}, "option": m480},
    ]


# -----------------------------------------------------------------------------
# 内部工具
# -----------------------------------------------------------------------------
def _clean_nan(df: pd.DataFrame) -> pd.DataFrame:
    """NaN / NaT → None，避免 ECharts 收到 JSON 中的 NaN 字面量（非法 JSON）。"""
    return df.where(pd.notna(df), None)


def _is_datetime_series(s: pd.Series) -> bool:
    """检测列是否是时间类型（含时区/不含时区均返回 True）。"""
    return pd.api.types.is_datetime64_any_dtype(s)


def _to_iso(s: pd.Series) -> pd.Series:
    """将时间列转为 ISO 8601 字符串，ECharts type='time' 可直接解析。"""
    # utc=False 保留原时区信息；NaT → None 后续由 _clean_nan 统一处理
    return s.dt.strftime("%Y-%m-%dT%H:%M:%S")


def _normalize_x_values(df: pd.DataFrame, x: str) -> List[Any]:
    """将 x 列规范化为 ECharts 可用的列表：时间列转 ISO 字符串，其余原样。"""
    col = df[x]
    if _is_datetime_series(col):
        col = _to_iso(col)
    return col.where(pd.notna(col), None).tolist()


def _normalize_numeric(values: Iterable[Any]) -> List[Any]:
    """将 numpy 数值 / NaN 规范化为 Python 原生类型（兼容 json.dumps）。"""
    out: List[Any] = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        # pandas NaN
        try:
            if pd.isna(v):
                out.append(None)
                continue
        except (TypeError, ValueError):
            pass
        # numpy scalar → python scalar
        if hasattr(v, "item"):
            try:
                out.append(v.item())
                continue
            except Exception:
                pass
        out.append(v)
    return out


def _pick_colors(n: int, theme_colors: Optional[Sequence[str]]) -> List[str]:
    colors = list(theme_colors) if theme_colors else DEFAULT_THEME_COLORS
    if n <= len(colors):
        return colors[:n]
    # 颜色不够时循环使用
    return [colors[i % len(colors)] for i in range(n)]


def _large_opts(length: int) -> dict:
    """单 series 大数据量时注入的性能选项。"""
    if length >= LARGE_THRESHOLD:
        return {"progressive": 2000, "large": True, "largeThreshold": 2000}
    return {}


def _x_axis_type(df: pd.DataFrame, x: str, chart_type: str) -> str:
    """根据 x 列 dtype + 图表类型推导 xAxis.type。"""
    if chart_type == "scatter":
        return "value" if pd.api.types.is_numeric_dtype(df[x]) else "category"
    if _is_datetime_series(df[x]):
        return "time"
    if chart_type in ("bar",):
        return "category"
    # line: 时间列已在上面处理；非时间 → category
    return "category"


# -----------------------------------------------------------------------------
# 主入口
# -----------------------------------------------------------------------------
def df_to_echarts_option(
    df: pd.DataFrame,
    chart_type: str,
    x: str,
    y: Union[str, List[str]],
    color: Optional[str] = None,
    *,
    theme_colors: Optional[Sequence[str]] = None,
    title: Optional[str] = None,
    **kwargs: Any,
) -> dict:
    """
    从 DataFrame 生成 ECharts option (dict)。

    参数:
        df           : pandas.DataFrame
        chart_type   : 'line' | 'bar' | 'pie' | 'scatter' | 'heatmap'
        x            : 类别/时间/数值轴列名
        y            : 数值列名，line/bar 支持 list[str] 多列堆叠
        color        : 分组列名（line/bar/scatter）；传入后按该列 groupby 拆系列
        theme_colors : 主题色序，默认使用 DEFAULT_THEME_COLORS
        title        : 图表标题（可选；通常由外层 HTML 的 <h2> 承担）
        **kwargs     : 各图表类型的额外参数，见各函数 docstring

    返回:
        dict —— ECharts 响应式 option，结构为 {baseOption, media}，
                可 json.dumps 后内嵌 HTML 直接 chart.setOption(option)
                ECharts 按 chart 容器宽度自动匹配 media query 切换样式（768 / 480 两档）

    主题色会自动注入每个 series 的 itemStyle.color。
    """
    if df is None or df.empty:
        return {"title": {"text": title or "", "left": "center"},
                "xAxis": {"type": "category", "data": []},
                "yAxis": {"type": "value"},
                "series": []}

    df = _clean_nan(df.copy())
    chart_type = chart_type.lower()

    if chart_type == "line":
        base = _line_option(df, x=x, y=y, color=color, theme_colors=theme_colors,
                            title=title, **kwargs)
    elif chart_type == "bar":
        base = _bar_option(df, x=x, y=y, color=color, theme_colors=theme_colors,
                           title=title, **kwargs)
    elif chart_type == "pie":
        base = _pie_option(df, x=x, y=y, theme_colors=theme_colors, title=title, **kwargs)
    elif chart_type == "scatter":
        base = _scatter_option(df, x=x, y=y, color=color, theme_colors=theme_colors,
                               title=title, **kwargs)
    elif chart_type == "heatmap":
        base = _heatmap_option(df, x=x, y=y, theme_colors=theme_colors,
                               title=title, **kwargs)
    else:
        raise ValueError(
            f"Unsupported chart_type: {chart_type!r}. "
            "Must be one of: line, bar, pie, scatter, heatmap."
        )

    return {"baseOption": base, "media": _build_media(chart_type)}


# -----------------------------------------------------------------------------
# line
# -----------------------------------------------------------------------------
def _line_option(df: pd.DataFrame, x: str, y, color, theme_colors, title,
                 smooth: bool = False, stack: bool = False, **_) -> dict:
    """
    line / 趋势图.

    kwargs:
        smooth: bool, 平滑曲线
        stack : bool, 堆叠
    """
    y_cols: List[str] = [y] if isinstance(y, str) else list(y)

    # 1) 处理 x 轴
    xaxis_type = _x_axis_type(df, x, "line")
    if xaxis_type == "time":
        # time 轴 data 用 [[ts, v], ...] 形式，x 列转 ISO；不在 xAxis.data 中列举
        x_values = _normalize_x_values(df, x)
    else:
        # category / 其他：xAxis.data 需要去重保持顺序
        x_values = _normalize_x_values(df, x)

    # 2) 切系列
    series: List[dict] = []
    if color and color in df.columns:
        groups = list(df.groupby(color, sort=False))
        colors = _pick_colors(len(groups), theme_colors)
        for i, (name, g) in enumerate(groups):
            for yc in y_cols:
                sname = f"{name}" if len(y_cols) == 1 else f"{name} · {yc}"
                series.append(_build_line_series(
                    name=sname,
                    xaxis_type=xaxis_type,
                    x_values=_normalize_x_values(g, x),
                    y_values=_normalize_numeric(g[yc].tolist()),
                    color=colors[i % len(colors)],
                    smooth=smooth,
                    stack=stack,
                ))
    else:
        colors = _pick_colors(len(y_cols), theme_colors)
        for i, yc in enumerate(y_cols):
            series.append(_build_line_series(
                name=yc,
                xaxis_type=xaxis_type,
                x_values=x_values,
                y_values=_normalize_numeric(df[yc].tolist()),
                color=colors[i],
                smooth=smooth,
                stack=stack,
            ))

    option: dict = {
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 36, "left": "center", "orient": "horizontal"},
        "grid": {"top": 90 if title else 70, "bottom": 60, "left": 8, "right": 16,
                 "containLabel": True},
        "xAxis": {"type": xaxis_type} if xaxis_type == "time"
                 else {"type": xaxis_type, "data": _dedup_keep_order(x_values)},
        "yAxis": {"type": "value"},
        "series": series,
    }
    if title:
        option["title"] = {"text": title, "left": "center", "top": 8,
                           "textStyle": {"fontSize": 16}}
    return option


def _build_line_series(name, xaxis_type, x_values, y_values, color,
                       smooth: bool, stack: bool) -> dict:
    s: dict = {
        "name": name,
        "type": "line",
        "itemStyle": {"color": color},
        "lineStyle": {"color": color, "width": 2},
        "symbolSize": 6,
        "smooth": bool(smooth),
        # 与 bar/pie 对齐：调用方一旦开启 label，重叠的自动隐藏（ECharts 5+）
        "labelLayout": {"hideOverlap": True},
    }
    if stack:
        s["stack"] = "total"
        s["areaStyle"] = {"opacity": 0.15}
    if xaxis_type == "time":
        s["data"] = [[xv, yv] for xv, yv in zip(x_values, y_values)]
    else:
        s["data"] = y_values
    s.update(_large_opts(len(y_values)))
    return s


# -----------------------------------------------------------------------------
# bar
# -----------------------------------------------------------------------------
def _bar_option(df: pd.DataFrame, x: str, y, color, theme_colors, title,
                horizontal: bool = False, stack: bool = False, **_) -> dict:
    """
    bar / 分类对比.

    kwargs:
        horizontal: bool, 水平柱图
        stack     : bool, 堆叠
    """
    y_cols: List[str] = [y] if isinstance(y, str) else list(y)
    x_values = _normalize_x_values(df, x)
    categories = _dedup_keep_order(x_values)

    series: List[dict] = []
    num_categories = len(categories)
    if color and color in df.columns:
        # 按 color 拆系列：同一 x 下有多个分组
        pivot = df.pivot_table(index=x, columns=color, values=y_cols[0],
                               aggfunc="sum", observed=False)
        pivot = pivot.reindex(categories)
        groups = list(pivot.columns)
        colors = _pick_colors(len(groups), theme_colors)
        for i, g in enumerate(groups):
            series.append(_build_bar_series(
                name=str(g),
                y_values=_normalize_numeric(pivot[g].tolist()),
                color=colors[i % len(colors)],
                stack=stack,
                show_label=(len(groups) <= 3),
                num_categories=num_categories,
            ))
    else:
        colors = _pick_colors(len(y_cols), theme_colors)
        for i, yc in enumerate(y_cols):
            series.append(_build_bar_series(
                name=yc,
                y_values=_normalize_numeric(df[yc].tolist()),
                color=colors[i],
                stack=stack,
                show_label=(len(y_cols) == 1),
                num_categories=num_categories,
            ))

    value_axis = {"type": "value", "axisLabel": {"color": "#666"}}
    category_axis = {"type": "category", "data": categories,
                     "axisLabel": {"color": "#666"}}
    if horizontal:
        x_axis, y_axis = value_axis, category_axis
    else:
        x_axis, y_axis = category_axis, value_axis

    option: dict = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"top": 36, "left": "center", "orient": "horizontal"},
        "grid": {"top": 90 if title else 70, "bottom": 60, "left": 8, "right": 16,
                 "containLabel": True},
        "xAxis": x_axis,
        "yAxis": y_axis,
        "series": series,
    }
    if title:
        option["title"] = {"text": title, "left": "center", "top": 8,
                           "textStyle": {"fontSize": 16}}
    return option


def _build_bar_series(name, y_values, color, stack: bool, show_label: bool,
                      num_categories: int = 0) -> dict:
    s: dict = {
        "name": name,
        "type": "bar",
        "itemStyle": {"color": color},
        "data": y_values,
        # ECharts 5+ 自动检测 label 重叠：能显示的显示，重叠的隐藏
        "labelLayout": {"hideOverlap": True},
    }
    if stack:
        s["stack"] = "total"
    # 分类 ≤ 4 才显 label（≥ 5 必挤，靠 tooltip + 表格补数值）
    if show_label and num_categories and num_categories <= 4:
        s["label"] = {"show": True, "position": "top", "color": "#333"}
    s.update(_large_opts(len(y_values)))
    return s


# -----------------------------------------------------------------------------
# pie
# -----------------------------------------------------------------------------
def _pie_option(df: pd.DataFrame, x: str, y, theme_colors, title,
                ring: bool = False, top_n: Optional[int] = None, **_) -> dict:
    """
    pie / 占比.

    kwargs:
        ring : bool, 环形图
        top_n: int, 只取 Top N，其余归为 '其他'
    """
    if isinstance(y, list):
        raise ValueError("pie 的 y 参数必须是单个数值列名（str），不支持 list。")

    data_df = df[[x, y]].copy()
    data_df = data_df.groupby(x, as_index=False, observed=False)[y].sum()
    data_df = data_df.sort_values(y, ascending=False)

    if top_n and len(data_df) > top_n:
        top = data_df.head(top_n)
        rest_sum = data_df.iloc[top_n:][y].sum()
        data_df = pd.concat(
            [top, pd.DataFrame([{x: "其他", y: rest_sum}])],
            ignore_index=True,
        )

    names = data_df[x].tolist()
    values = _normalize_numeric(data_df[y].tolist())
    colors = _pick_colors(len(names), theme_colors)
    pie_data = [{"name": str(n), "value": v, "itemStyle": {"color": colors[i]}}
                for i, (n, v) in enumerate(zip(names, values))]

    series = [{
        "name": y,
        "type": "pie",
        "radius": ["40%", "70%"] if ring else "70%",
        "center": ["50%", "46%"],
        "data": pie_data,
        "avoidLabelOverlap": True,
        "label": {"show": True, "formatter": "{b}: {d}%"},
        "labelLayout": {"hideOverlap": True},
        "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0,
                                   "shadowColor": "rgba(0,0,0,0.2)"}},
    }]
    option: dict = {
        "tooltip": {"trigger": "item", "formatter": "{b}<br/>{c} ({d}%)"},
        # 图例放底部：饼图外侧引导线标签集中在上半圈，顶部图例会与标签打架
        "legend": {"bottom": 8, "left": "center", "orient": "horizontal"},
        "series": series,
    }
    if title:
        option["title"] = {"text": title, "left": "center", "top": 8,
                           "textStyle": {"fontSize": 16}}
    return option


# -----------------------------------------------------------------------------
# scatter
# -----------------------------------------------------------------------------
def _scatter_option(df: pd.DataFrame, x: str, y, color, theme_colors, title,
                    size: Optional[str] = None, **_) -> dict:
    """
    scatter / 散点 & 气泡.

    kwargs:
        size: str, 气泡大小取值列名（数值列）
    """
    if isinstance(y, list):
        raise ValueError("scatter 的 y 参数必须是单个数值列名（str）。")

    x_values = _normalize_numeric(df[x].tolist())
    y_values = _normalize_numeric(df[y].tolist())

    def _point(xi, yi, si=None):
        if si is None:
            return [xi, yi]
        return [xi, yi, si]

    series: List[dict] = []
    if color and color in df.columns:
        groups = list(df.groupby(color, sort=False))
        colors = _pick_colors(len(groups), theme_colors)
        for i, (name, g) in enumerate(groups):
            gx = _normalize_numeric(g[x].tolist())
            gy = _normalize_numeric(g[y].tolist())
            gs = _normalize_numeric(g[size].tolist()) if size and size in g.columns else None
            data = [_point(gx[j], gy[j], gs[j] if gs is not None else None)
                    for j in range(len(gx))]
            series.append({
                "name": str(name),
                "type": "scatter",
                "itemStyle": {"color": colors[i % len(colors)], "opacity": 0.8},
                "symbolSize": (lambda v: max(6, min(40, float(v[2]) ** 0.5))) if gs is not None else 10,
                "data": data,
                # 与 bar/pie 对齐：调用方一旦开启 label，重叠的自动隐藏（ECharts 5+）
                "labelLayout": {"hideOverlap": True},
                **_large_opts(len(data)),
            })
    else:
        colors = _pick_colors(1, theme_colors)
        gs = _normalize_numeric(df[size].tolist()) if size and size in df.columns else None
        data = [_point(x_values[j], y_values[j], gs[j] if gs is not None else None)
                for j in range(len(x_values))]
        series.append({
            "name": y,
            "type": "scatter",
            "itemStyle": {"color": colors[0], "opacity": 0.8},
            "symbolSize": (lambda v: max(6, min(40, float(v[2]) ** 0.5))) if gs is not None else 10,
            "data": data,
            # 与 bar/pie 对齐：调用方一旦开启 label，重叠的自动隐藏（ECharts 5+）
            "labelLayout": {"hideOverlap": True},
            **_large_opts(len(data)),
        })

    option: dict = {
        "tooltip": {"trigger": "item"},
        "legend": {"top": 36, "left": "center", "orient": "horizontal"},
        "grid": {"top": 90 if title else 70, "bottom": 60, "left": 8, "right": 16,
                 "containLabel": True},
        "xAxis": {"type": "value", "name": x, "axisLabel": {"color": "#666"}},
        "yAxis": {"type": "value", "name": y, "axisLabel": {"color": "#666"}},
        "series": series,
    }
    if title:
        option["title"] = {"text": title, "left": "center", "top": 8,
                           "textStyle": {"fontSize": 16}}
    return option


# -----------------------------------------------------------------------------
# heatmap
# -----------------------------------------------------------------------------
def _heatmap_option(df: pd.DataFrame, x: str, y, theme_colors, title,
                    x_order: Optional[List[str]] = None,
                    y_order: Optional[List[str]] = None,
                    **kwargs) -> dict:
    """
    heatmap / 二维热力图.

    约定:
        x, y   : 二维坐标轴列名
        value  : 值列名，通过 kwargs['value'] 或 y 参数中列表传入

    这里 y 不作为数值列，而是第二坐标轴。值列通过 kwargs['value'] 指定。
    """
    value = kwargs.get("value")
    if isinstance(y, list):
        raise ValueError("heatmap 的 y 参数必须是单个列名（str），值列通过 kwargs['value'] 指定。")
    if not value or value not in df.columns:
        raise ValueError("heatmap 必须提供 kwargs['value']，且其为 df 中的数值列。")

    x_labels = x_order or _dedup_keep_order(df[x].tolist())
    y_labels = y_order or _dedup_keep_order(df[y].tolist())
    x_index = {v: i for i, v in enumerate(x_labels)}
    y_index = {v: i for i, v in enumerate(y_labels)}

    data: List[list] = []
    values_numeric = _normalize_numeric(df[value].tolist())
    for xi, yi, val in zip(df[x].tolist(), df[y].tolist(), values_numeric):
        if xi not in x_index or yi not in y_index or val is None:
            continue
        data.append([x_index[xi], y_index[yi], val])

    finite_vals = [d[2] for d in data if isinstance(d[2], (int, float))]
    vmin = min(finite_vals) if finite_vals else 0
    vmax = max(finite_vals) if finite_vals else 1

    colors = _pick_colors(3, theme_colors)
    option: dict = {
        "tooltip": {"position": "top"},
        "grid": {"top": 90 if title else 70, "bottom": 80, "left": 8, "right": 16,
                 "containLabel": True},
        "xAxis": {"type": "category", "data": x_labels, "splitArea": {"show": True}},
        "yAxis": {"type": "category", "data": y_labels, "splitArea": {"show": True}},
        "visualMap": {
            "min": vmin, "max": vmax,
            "calculable": True, "orient": "horizontal",
            "left": "center", "bottom": 10,
            "inRange": {"color": ["#f0f7ff", colors[0], colors[2]]},
        },
        "series": [{
            "name": value,
            "type": "heatmap",
            "data": data,
            "label": {"show": len(data) <= 100},
            "emphasis": {"itemStyle": {"shadowBlur": 10,
                                       "shadowColor": "rgba(0,0,0,0.3)"}},
            **_large_opts(len(data)),
        }],
    }
    if title:
        option["title"] = {"text": title, "left": "center", "top": 8,
                           "textStyle": {"fontSize": 16}}
    return option


# -----------------------------------------------------------------------------
# 通用辅助
# -----------------------------------------------------------------------------
def _dedup_keep_order(values: Iterable[Any]) -> List[Any]:
    seen = set()
    out: List[Any] = []
    for v in values:
        key = (type(v).__name__, v)
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


# -----------------------------------------------------------------------------
# 使用示例
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    # 构造一份模拟 DataFrame
    dates = pd.date_range("2025-01-01", periods=6, freq="MS")
    demo = pd.DataFrame({
        "date": list(dates) * 2,
        "category": ["电子"] * 6 + ["服饰"] * 6,
        "revenue": [1200, 1500, 900, 2100, 1800, 2300,
                    800, 950, 1100, 1600, 1450, 1700],
    })

    print("=== line with color ===")
    opt_line = df_to_echarts_option(
        demo, "line", x="date", y="revenue", color="category",
        title="月度销售趋势", smooth=True,
    )
    print(json.dumps(opt_line, ensure_ascii=False, indent=2)[:500], "...")

    print("\n=== bar (aggregated) ===")
    agg = demo.groupby("category", as_index=False)["revenue"].sum()
    opt_bar = df_to_echarts_option(agg, "bar", x="category", y="revenue",
                                   title="品类总销售额")
    print(json.dumps(opt_bar, ensure_ascii=False, indent=2)[:500], "...")

    print("\n=== pie ===")
    opt_pie = df_to_echarts_option(agg, "pie", x="category", y="revenue",
                                   title="品类占比", ring=True)
    print(json.dumps(opt_pie, ensure_ascii=False, indent=2)[:500], "...")

    print("\n=== scatter ===")
    scatter_df = pd.DataFrame({
        "gmv": [100, 200, 300, 400, 500],
        "orders": [10, 22, 35, 48, 60],
        "region": ["SP", "SP", "RJ", "RJ", "MG"],
        "size": [30, 50, 70, 90, 110],
    })
    opt_scatter = df_to_echarts_option(
        scatter_df, "scatter", x="gmv", y="orders",
        color="region", size="size", title="GMV vs 订单数",
    )
    print(json.dumps(opt_scatter, ensure_ascii=False, indent=2)[:500], "...")

    print("\n=== heatmap ===")
    heat_df = pd.DataFrame({
        "category": ["电子", "电子", "服饰", "服饰"],
        "region":   ["SP",  "RJ",   "SP",   "RJ"],
        "value":    [123,    89,     56,     78],
    })
    opt_heat = df_to_echarts_option(
        heat_df, "heatmap", x="category", y="region",
        value="value", title="品类×地区热力图",
    )
    print(json.dumps(opt_heat, ensure_ascii=False, indent=2)[:500], "...")

    print("\nAll OK.")
