#!/usr/bin/env python3
"""render_chart.py — 把数据洞察结果渲染成自包含 HTML 图表（基于 ECharts）。

设计目标：
  - 纯标准库，无第三方依赖（任何 Python3 环境都能跑）
  - 产出单个自包含 .html（ECharts 走 CDN），用浏览器 / IDE 预览即可打开
  - 覆盖数据洞察最常用的三类图：bar(柱状-排名/对比)、line(折线-趋势)、pie(饼图-占比)

用法：
  # 方式1：spec 文件
  python3 render_chart.py --spec spec.json

  # 方式2：stdin 传 JSON
  echo '{"type":"bar","title":"各成员拜访量","x":["张三","李四"],"series":[{"name":"拜访次数","data":[187,170]}]}' | python3 render_chart.py --out chart.html

  # 方式3：命令行参数
  python3 render_chart.py --type line --title "日活趋势" \
      --x '["06-01","06-02","06-03"]' \
      --series '[{"name":"DAU","data":[120,135,150]}]' --out dau.html

spec JSON 结构：
  {
    "type":  "bar" | "line" | "pie",     # 必填
    "title": "图表标题",                  # 必填
    "x":     ["类目1","类目2", ...],      # bar/line 的 x 轴类目；pie 作为扇区名称
    "series":[                            # 一个或多个系列（pie 只取第一个系列的 data）
      {"name":"系列名","data":[v1, v2, ...]}
    ],
    "subtitle": "可选副标题",
    "out":   "输出路径.html"              # 可被 --out 覆盖
  }

退出码：0 成功；非 0 失败（错误打印到 stderr）。
"""

import argparse
import json
import os
import sys
import time

ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>__TITLE__</title>
<script src="__CDN__"></script>
<style>
  body { margin:0; font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background:#f7f8fa; }
  .wrap { max-width: 960px; margin: 24px auto; background:#fff; border-radius:12px; box-shadow:0 2px 12px rgba(0,0,0,.06); padding:20px; }
  #chart { width:100%; height:520px; }
  .hint { color:#8a8f99; font-size:12px; margin-top:8px; }
</style>
</head>
<body>
<div class="wrap">
  <div id="chart"></div>
  <div class="hint">由 nges-data-360 生成 · 数据范围已按当前用户行权限自动过滤</div>
</div>
<script>
  var option = __OPTION__;
  var chart = echarts.init(document.getElementById('chart'));
  chart.setOption(option);
  window.addEventListener('resize', function(){ chart.resize(); });
</script>
</body>
</html>
"""


def build_option(spec):
    """根据 spec 构造 ECharts option 字典。"""
    ctype = spec.get("type")
    title = spec.get("title", "")
    subtitle = spec.get("subtitle", "")
    x = spec.get("x", []) or []
    series_in = spec.get("series", []) or []

    if ctype not in ("bar", "line", "pie"):
        raise ValueError(f"不支持的图表类型: {ctype}（仅支持 bar/line/pie）")
    if not title:
        raise ValueError("缺少 title")

    title_block = {"text": title, "left": "center"}
    if subtitle:
        title_block["subtext"] = subtitle

    if ctype == "pie":
        if not series_in:
            raise ValueError("pie 需要 series[0].data")
        values = series_in[0].get("data", [])
        if len(x) != len(values):
            raise ValueError(f"pie 的 x({len(x)}) 与 data({len(values)}) 长度不一致")
        pie_data = [{"name": str(n), "value": v} for n, v in zip(x, values)]
        return {
            "title": title_block,
            "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
            "legend": {"top": "bottom"},
            "series": [{
                "name": series_in[0].get("name", title),
                "type": "pie",
                "radius": ["35%", "65%"],
                "data": pie_data,
                "label": {"formatter": "{b}\n{d}%"},
            }],
        }

    # bar / line
    if not series_in:
        raise ValueError("bar/line 需要至少一个 series")
    echarts_series = []
    for s in series_in:
        item = {"name": s.get("name", ""), "type": ctype, "data": s.get("data", [])}
        if ctype == "line":
            item["smooth"] = True
        if ctype == "bar":
            item["label"] = {"show": True, "position": "top"}
        echarts_series.append(item)

    return {
        "title": title_block,
        "tooltip": {"trigger": "axis"},
        "legend": {"top": "bottom"} if len(echarts_series) > 1 else {"show": False},
        "grid": {"left": "3%", "right": "4%", "bottom": "12%", "containLabel": True},
        "xAxis": {"type": "category", "data": [str(i) for i in x],
                  "axisLabel": {"interval": 0, "rotate": 30 if len(x) > 8 else 0}},
        "yAxis": {"type": "value"},
        "series": echarts_series,
    }


def render(spec, out_path):
    option = build_option(spec)
    html = (HTML_TEMPLATE
            .replace("__TITLE__", json.dumps(spec.get("title", ""), ensure_ascii=False).strip('"'))
            .replace("__CDN__", ECHARTS_CDN)
            .replace("__OPTION__", json.dumps(option, ensure_ascii=False)))
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def _load_spec(args):
    if args.spec:
        with open(args.spec, "r", encoding="utf-8") as f:
            return json.load(f)
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            return json.loads(data)
    # 命令行参数拼装
    if not (args.type and args.title):
        raise ValueError("请通过 --spec / stdin / (--type+--title+--series) 之一提供图表定义")
    return {
        "type": args.type,
        "title": args.title,
        "subtitle": args.subtitle or "",
        "x": json.loads(args.x) if args.x else [],
        "series": json.loads(args.series) if args.series else [],
    }


def main():
    p = argparse.ArgumentParser(description="把数据洞察结果渲染成自包含 HTML 图表")
    p.add_argument("--spec", help="spec JSON 文件路径")
    p.add_argument("--type", help="bar|line|pie")
    p.add_argument("--title", help="图表标题")
    p.add_argument("--subtitle", help="副标题")
    p.add_argument("--x", help="x 轴类目 JSON 数组")
    p.add_argument("--series", help="series JSON 数组")
    p.add_argument("--out", help="输出 HTML 路径")
    args = p.parse_args()

    try:
        spec = _load_spec(args)
        out = args.out or spec.get("out") or f"chart_{int(time.time())}.html"
        path = render(spec, out)
    except Exception as e:
        print(f"❌ 图表生成失败: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ 图表已生成: {path}")
    print("   用浏览器或 IDE 预览打开即可（需联网加载 ECharts CDN）。")


if __name__ == "__main__":
    main()
