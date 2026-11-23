# -*- coding: utf-8 -*-
"""国内机票一条龙：城市码 → domestic_shopping → 交互分析页。

单程: Top 展开 + 免登下单；往返(--return): 推荐往返——一次 journeyType=1
查询出一张往返组合页（每行=去程舱位×返程舱位固定组合）。

**标准交付**：省略 `--run-id` 时脚本自己发号（stdout 一行 + `fh-last-task-id.txt`）。
`--raw` 续跑才传入已有 `--run-id`。
present_files 打开 `run_summary.json` 的 `html`。不要改用宿主手调 MCP。
**严禁为此启动任何本地 HTTP server。**

用法（任意本机 python，标准库即可）:
  python scripts/air_domestic_query.py --from 北京 --to 上海 --date 2026-09-15
  python scripts/air_domestic_query.py --from 深圳 --to 成都 --date 2026-09-11 --adults 1
  python scripts/air_domestic_query.py --from 长沙 --to 三亚 --date 2026-09-25 --return 2026-10-06
      （--return = 推荐往返：**一次** journeyType=1 查询（airLegs 两项互反），
        出一张往返组合页。严禁用两次单程查询代替。）

查询口径（固定，勿改）：official=true、sortBy=DEPARTURE_TIME、
withCabinRules=true、needRefundChangeRule=false（shopping 不带退改文案，页内点退改补查）。

产物（都在本轮任务目录内）:
  shopping.json + page.html + run_summary.json

成功才写 `run_summary.json`：`{"ok": true, "html": "<abs>", "shopping": "<abs>", "runDir": "<abs>"}`。
失败写 `{"ok": false, "runDir": "<abs>", "error": "..."}`，没有 html。
打开 `html`，不要当日志读。

失败即停：退出非 0。没有 page.html 时把同一条命令再跑一次；401 先修 token。
不要改走宿主手调 shopping。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import query_run
from query_run import QueryRun, normalize_date

SCRIPTS = Path(__file__).resolve().parent
PY = sys.executable

_run: QueryRun | None = None


def _log(msg: str) -> None:
    if _run:
        _run.log(msg)
    else:
        print(msg, flush=True)


def _err(msg: str) -> None:
    if _run:
        _run.err(msg)
    else:
        print(msg, file=sys.stderr, flush=True)


def _run_step(title: str, cmd: list[str]) -> tuple[int, str, str]:
    assert _run is not None
    return _run.run_step(title, cmd)


def _resolve_city(name: str) -> str:
    """国内城市码：本地缓存优先，未命中自动 air_city(scope=DOMESTIC) 并回写缓存。"""
    _, out, _ = _run_step(
        f"S1 城市码[{name}]",
        [PY, str(SCRIPTS / "air_domestic_resolve_city.py"), "--json", name],
    )
    data = json.loads(out)
    if not data or not data[0].get("found"):
        raise SystemExit(
            f"[失败] 城市 {name!r} 解析失败（缓存与 air_city 均无候选）。"
            f"请确认城市名后重试。"
        )
    return str(data[0]["code"])


def _shopping_params(from_code: str, to_code: str, fly_date: str, adults: int,
                     ret_date: str = "") -> str:
    """domestic_shopping 入参。固定口径：official=true、sortBy=DEPARTURE_TIME、
    withCabinRules=true、needRefundChangeRule=false（须显式传；Java 不传仍会开退改）。

    单程(默认): journeyType=0。
    推荐往返(ret_date 非空): journeyType=1 + airLegs 两项互反。
    """
    search: dict[str, Any] = {
        "journeyType": 1 if ret_date else 0,
        "passengerNum": adults,
        "official": True,
        "sortBy": "DEPARTURE_TIME",
        "withCabinRules": True,
        "needRefundChangeRule": False,
        "airLegs": [{"fromCity": from_code, "toCity": to_code, "flyDate": fly_date}],
    }
    if ret_date:
        search["airLegs"].append({"fromCity": to_code, "toCity": from_code, "flyDate": ret_date})
    return json.dumps({
        "name": "domestic_shopping",
        "arguments": {"searchParams": search},
    }, ensure_ascii=False)


def _query_leg(tag: str, from_code: str, to_code: str, fly_date: str, adults: int,
               raw_path: Path, ret_date: str = "", *,
               from_city: str = "", to_city: str = "") -> None:
    params = _shopping_params(from_code, to_code, fly_date, adults, ret_date)
    _run_step(
        f"S2 domestic_shopping {tag}",
        [PY, str(SCRIPTS / "fh_travel.py"), "tools/call", params, "--out", str(raw_path)],
    )
    if not raw_path.exists() or raw_path.stat().st_size < 100:
        raise SystemExit(f"[失败] 查询响应文件异常: {raw_path}")


def _render_page(from_city: str, to_city: str, from_code: str, to_code: str,
                 fly_date: str, adults: int, top_open: int, raw_path: Path, out_html: Path) -> None:
    cmd = [
        PY, str(SCRIPTS / "air_domestic_oneway_render_page.py"), str(raw_path),
        "--from-city", from_city, "--to-city", to_city,
        "--from-code", from_code, "--to-code", to_code,
        "--date", fly_date, "--adult", str(adults), "--top-open", str(top_open),
        "--full-note", "--out", str(out_html),
    ]
    _, out, _ = _run_step(
        f"S3 出页 {from_city}→{to_city} {fly_date}",
        cmd,
    )
    if out.strip():
        _log("\n" + out.rstrip())


def _render_roundtrip_page(from_city: str, to_city: str, fly_date: str, ret_date: str,
                           adults: int, raw_path: Path, out_html: Path) -> None:
    """推荐往返出页：air_domestic_roundtrip_render_page.py（每行=去×回舱位固定组合）。"""
    cmd = [
        PY, str(SCRIPTS / "air_domestic_roundtrip_render_page.py"), str(raw_path),
        "--from-city", from_city, "--to-city", to_city,
        "--go-date", fly_date, "--ret-date", ret_date,
        "--adult", str(adults), "--full-note", "--out", str(out_html),
    ]
    _, out, _ = _run_step(
        f"S3 出页(推荐往返) {from_city}⇄{to_city} {fly_date}/{ret_date}",
        cmd,
    )
    if out.strip():
        _log("\n" + out.rstrip())


def main() -> int:
    query_run.configure_stdio()

    ap = argparse.ArgumentParser(description="国内机票一条龙（城市码→查询→交互页；--return 为推荐往返：一次 journeyType=1 出往返组合页）")
    ap.add_argument("--from", dest="from_city", required=True, help="出发城市（中文，如 北京）")
    ap.add_argument("--to", dest="to_city", required=True, help="到达城市（中文，如 上海）")
    ap.add_argument("--date", required=True, help="出发日期 YYYY-MM-DD（兼容 2026.9.15 / 9.15=当年）")
    ap.add_argument("--return", dest="return_date", default="",
                    help="回程日期（传入即推荐往返：一次 journeyType=1 查询出一张往返组合页）")
    ap.add_argument("--raw", type=Path,
                    help="已有 domestic_shopping 原始 JSON 时跳过 S2 只出页（排障用，非标准路径）")
    ap.add_argument("--adults", type=int, default=1, help="人数（默认 1，同步下单页 adultCount）")
    ap.add_argument("--top-open", type=int, default=5, help="默认展开舱位的推荐航班数（默认 5）")
    ap.add_argument("--run-id", default="",
                    help="省略则自动发号并写入 fh-last-task-id.txt；--raw 续跑才需要传入")
    ap.add_argument("--present-dir", default="",
                    help="把最终 html 再复制到此目录（相对当前目录），summary 的 html 指向副本")
    args = ap.parse_args()
    global _run
    _run = QueryRun(args.run_id)

    runs = _run.dir()
    page = runs / "page.html"
    _log(f"run-dir: {runs.resolve()}")

    t_all = time.time()
    fly_date = normalize_date(args.date)
    is_roundtrip = bool(args.return_date)
    ret_date = normalize_date(args.return_date) if is_roundtrip else ""

    from_code = _resolve_city(args.from_city)
    to_code = _resolve_city(args.to_city)
    _log(f"城市码: {args.from_city}={from_code}  {args.to_city}={to_code}")

    raw_path = args.raw.resolve() if args.raw else runs / "shopping.json"
    if args.raw:
        if not raw_path.exists():
            raise SystemExit(f"[失败] --raw 文件不存在: {raw_path}")
        _log(f"\n[S2] 使用已有原始查询结果续跑: {raw_path}")
    elif is_roundtrip:
        _query_leg(f"REC {from_code}→{to_code}→{from_code} {fly_date}/{ret_date}",
                   from_code, to_code, fly_date, args.adults, raw_path, ret_date=ret_date,
                   from_city=args.from_city, to_city=args.to_city)
    else:
        _query_leg(f"{from_code}→{to_code} {fly_date}", from_code, to_code, fly_date,
                   args.adults, raw_path,
                   from_city=args.from_city, to_city=args.to_city)

    _log(f"shopping-json: {raw_path.resolve()}")
    if is_roundtrip:
        _render_roundtrip_page(args.from_city, args.to_city, fly_date, ret_date,
                               args.adults, raw_path, page)
    else:
        _render_page(args.from_city, args.to_city, from_code, to_code, fly_date,
                     args.adults, args.top_open, raw_path, page)

    if not page.exists() or page.stat().st_size < 500:
        raise SystemExit(f"[失败] 交互页异常: {page}")

    _run.write_ok(raw_path, html=page, present_dir=args.present_dir)
    _log("\n" + "=" * 72)
    _log(f"done in {time.time() - t_all:.1f}s")
    _log(f"html: {page.resolve()}")
    if is_roundtrip:
        _log("页面说明: 推荐往返组合页 · 每行=去程舱位×返程舱位固定组合（往返组合价，"
             "≠两段单程价相加）· 总价含税 · 「行李政策|退改政策」弹层读本次查询文本 · "
             "预订=单选组合（免登下单跳转待接）。")
    else:
        _log("页面说明: 前 %d 班默认展开舱位 · 「去下单」免登跳转飞鹤下单页 · "
             "「更多」展开本次 shopping 已返回的舱位（不重查接口）。" % args.top_open)
    _log("serialNumber 为短时效会话；过期后请重跑本脚本再下单。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as exc:
        if exc.code not in (0, None) and _run:
            err = exc.code if isinstance(exc.code, str) else f"exit={exc.code}"
            _run.write_fail(str(err))
        raise
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _err(f"[错误] {exc}")
        if _run:
            _run.write_fail(str(exc))
        raise SystemExit(1)
