# -*- coding: utf-8 -*-
"""国际机票一条龙：城市码 → 组合查询 → 决策级摘要 → 精选舱位内联下单页。

把 S1(resolve) → S2(intl_shopping) → S3(parse) → S3′(inline best:N) 四次工具往返
压缩为**一次调用**。省略 `--run-id` 时脚本自己发号（stdout 一行 + `fh-last-task-id.txt`）。
`--raw` 续跑才传入已有 `--run-id`。
present_files 打开 `run_summary.json` 的 `html`。
**严禁为此启动任何本地 HTTP server。**

用法（任意本机 python，标准库即可）:
  python scripts/air_intl_query.py --from 北京 --to 新加坡 --date 2026-09-20
  python scripts/air_intl_query.py --from 深圳 --to 巴厘岛 --date 2026-09-16 --scope best:5
  python scripts/air_intl_query.py --from 北京 --to 莫斯科 --date 2026-09-20 --return 2026-09-25
  python scripts/air_intl_query.py --from 北京 --to 香港 --date 2026-10-01 --skip-cabins
  python scripts/air_intl_query.py --raw runs/raw_intl_shopping.json --from 深圳 --to 首尔 --date 2026-09-08

产物（本轮任务目录）:
  <runs>/raw_intl_shopping.json   原始 JSON-RPC 响应
  <runs>/parsed.json              解析结果（可直接回喂 air_intl_parse_shopping.py 重印摘要）
  <runs>/run_summary.json          成功 ok/html/shopping/runDir；失败 ok=false + error
  <runs>/_inline/flights_inline.html   全量方案单页：精选内联舱位+免登下单链接，
                                       其余航班带「查舱位」按钮（页内 fetch busi intlShop，头 infoCode）
  <runs>/_inline/cabins_by_option.json 精选航班的舱位聚合

失败即停：打印出错步骤和 stderr 后退出非 0。不要改跑城市或拆步脚本。
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


def _build_trip_list(
    from_code: str,
    to_code: str,
    fly_date: str,
    *,
    from_is_city: bool = False,
    to_is_city: bool = False,
    return_date: str = "",
) -> list[dict[str, Any]]:
    """构造一次 intl_shopping 的完整行程；普通往返仍是一个组合查询。"""
    trips: list[dict[str, Any]] = [{
        "fromCity": from_code,
        "toCity": to_code,
        "flyDate": fly_date,
        "isFromCity": from_is_city,
        "isToCity": to_is_city,
    }]
    if return_date:
        trips.append({
            "fromCity": to_code,
            "toCity": from_code,
            "flyDate": return_date,
            "isFromCity": to_is_city,
            "isToCity": from_is_city,
        })
    return trips


def _build_shopping_arguments(
    from_code: str,
    to_code: str,
    fly_date: str,
    *,
    adults: int = 1,
    from_is_city: bool = False,
    to_is_city: bool = False,
    return_date: str = "",
) -> dict[str, Any]:
    """返回一次 intl_shopping 的参数，禁止把往返拆成两次单程请求。"""
    return {
        "language": "cn",
        "passengerType": "ADT",
        "passengerCount": adults,
        "tripList": _build_trip_list(
            from_code,
            to_code,
            fly_date,
            from_is_city=from_is_city,
            to_is_city=to_is_city,
            return_date=return_date,
        ),
    }


def _resolve_city(name: str, role: str) -> tuple[str, bool]:
    """返回 (查询码, isCity 聚合标志)。聚合码优先；无聚合取第一个机场码。"""
    _, out, _ = _run_step(
        f"S1 城市码[{name}]",
        [PY, str(SCRIPTS / "air_intl_resolve_city.py"), "--json", name],
    )
    data = json.loads(out)
    if not data or not data[0].get("found"):
        raise SystemExit(
            f"[失败] 城市 {name!r} 解析失败（缓存未命中且 air_city 无可用候选）。"
            f"检查城市名或登录态后，重跑同一条龙即可；不要手工并行 --ingest。"
        )
    city = data[0]["cities"][0]
    agg = city.get("aggregate") or ""
    if agg:
        return str(agg), True
    airports = [a for a in (city.get("airports") or []) if a.get("code")]
    if not airports:
        raise SystemExit(f"[失败] 城市 {name!r} 既无聚合码也无机场码: {city}")
    return str(airports[0]["code"]), False


def main() -> int:
    query_run.configure_stdio()

    ap = argparse.ArgumentParser(description="国际机票一条龙（城市码→查询→摘要→舱位下单页）")
    ap.add_argument("--from", dest="from_city", default="", help="出发城市（中文，如 北京；--raw 时用于页面标题）")
    ap.add_argument("--to", dest="to_city", default="", help="目的城市（中文，如 新加坡；--raw 时用于页面标题）")
    ap.add_argument("--date", default="", help="出发日期 YYYY-MM-DD（兼容 2026.9.20 / 9.20=当年）")
    ap.add_argument("--raw", type=Path, help="已有 intl_shopping 原始结果；跳过 S1/S2，继续标准解析和 inline 页面")
    ap.add_argument("--return", dest="return_date", default="",
                    help="回程日期（传入即往返查询；兼容 9.25 / 2026.9.25）")
    ap.add_argument("--adults", type=int, default=1, help="成人数（默认 1）")
    ap.add_argument("--scope", default="best:5",
                    help="精选范围：best:N（默认 5，评分精选并内联舱位）/ direct / top:N / all")
    ap.add_argument("--rows", type=int, default=15, help="parse 摘要行数（默认 15）")
    ap.add_argument("--skip-cabins", action="store_true", help="只查+解析+渲染航班页，不批量查舱位")
    ap.add_argument("--title", default="", help="页面标题（默认 '<出发> ⇄ <目的> · <日期>'）")
    ap.add_argument("--run-id", default="",
                    help="省略则自动发号并写入 fh-last-task-id.txt；--raw 续跑才需要传入")
    ap.add_argument("--present-dir", default="",
                    help="把最终 html 再复制到此目录（相对当前目录），summary 的 html 指向副本")
    args = ap.parse_args()
    if args.raw is None and (not args.from_city or not args.to_city or not args.date):
        ap.error("正常查询必须提供 --from、--to、--date；使用 --raw 时仍建议提供它们用于页面标题")
    global _run
    _run = QueryRun(args.run_id)

    t_all = time.time()
    fly_date = normalize_date(args.date) if args.date else ""
    is_roundtrip = bool(args.return_date)
    ret_date = normalize_date(args.return_date) if is_roundtrip else ""

    from_code = to_code = ""
    from_is_city = to_is_city = False
    if args.raw is None:
        from_code, from_is_city = _resolve_city(args.from_city, "from")
        to_code, to_is_city = _resolve_city(args.to_city, "to")
        _log(f"城市码: {args.from_city}={from_code}(isCity={from_is_city})  "
             f"{args.to_city}={to_code}(isCity={to_is_city})")

    runs = _run.dir()
    html_path = (runs / "_inline" / "flights_inline.html").resolve()
    _log(f"run-dir: {runs.resolve()}")

    # S2 组合查询（--raw 仅排障续跑；标准路径不要宿主手调 shopping）。
    # 往返 = 一次请求内的两段（去程 + 反向回程）；单程 = 一段。
    shopping_args = _build_shopping_arguments(
        from_code,
        to_code,
        fly_date,
        adults=args.adults,
        from_is_city=from_is_city,
        to_is_city=to_is_city,
        return_date=ret_date,
    )
    call_params = json.dumps({
        "name": "intl_shopping",
        "arguments": shopping_args,
    }, ensure_ascii=False)
    raw_path = args.raw.resolve() if args.raw else runs / "raw_intl_shopping.json"
    route_desc = f"{from_code}⇄{to_code} {fly_date}/{ret_date}" if is_roundtrip else f"{from_code}→{to_code} {fly_date}"
    if args.raw:
        if not raw_path.exists():
            raise SystemExit(f"[失败] --raw 文件不存在: {raw_path}")
        _log(f"\n[S2] 使用已有原始查询结果续跑: {raw_path}")
    else:
        _run_step(
            f"S2 intl_shopping {route_desc}",
            [PY, str(SCRIPTS / "fh_travel.py"), "tools/call", call_params, "--out", str(raw_path)],
        )
    if not raw_path.exists() or raw_path.stat().st_size < 100:
        raise SystemExit(f"[失败] 查询响应文件异常: {raw_path}")
    _log(f"shopping-json: {raw_path.resolve()}")

    # S3 解析（stdout 即决策级摘要：行李/退改/中转停留/同机场/廉价航/门到门）
    parsed_path = runs / "parsed.json"
    _, summary_out, _ = _run_step(
        "S3 air_intl_parse_shopping 决策级摘要",
        [PY, str(SCRIPTS / "air_intl_parse_shopping.py"), str(raw_path),
         "--output", str(parsed_path), "--rows", str(args.rows)],
    )
    _log("\n" + summary_out.rstrip())
    _log(f"parsed-json: {parsed_path.resolve()}")

    if args.skip_cabins:
        _log(f"\n[--skip-cabins] 未查舱位。航班页渲染: {PY} {SCRIPTS / 'air_intl_render_flight_options.py'} …（见 air-intl-search.md）")
        _run.write_ok(raw_path, parsed=str(parsed_path.resolve()))
        _log(f"\n完成，总耗时 {time.time() - t_all:.1f}s。解析产物: {parsed_path.resolve()}")
        _log(f"run-dir: {runs.resolve()}")
        _log(f"shopping-json: {raw_path.resolve()}")
        _log(f"parsed-json: {parsed_path.resolve()}")
        _log(f"\ndone in {time.time() - t_all:.1f}s")
        return 0

    # S3′ best:N 批量查舱位 + 渲染全量单页（top:N 内联舱位，其余带「查舱位」按钮）
    title = args.title or (
        f"{args.from_city} ⇄ {args.to_city} · {fly_date}–{ret_date}" if is_roundtrip
        else f"{args.from_city} → {args.to_city} · {fly_date}")
    meta = f"{args.adults} 成人 · {'往返' if is_roundtrip else '单程'}"
    fly_type = "2" if is_roundtrip else "1"
    inline_cmd = [
        PY, str(SCRIPTS / "air_intl_book.py"), "inline",
        "--parsed", str(parsed_path), "--out-dir", str(runs / "_inline"),
        "--scope", args.scope, "--title", title, "--meta", meta,
        "--fly-type", fly_type,
        "--adult", str(args.adults),
    ]
    _, inline_out, _ = _run_step(
        f"S3′ inline --scope {args.scope}",
        inline_cmd,
    )
    if inline_out.strip():
        _log("\n" + inline_out.rstrip())

    html = html_path
    if not html.exists() or html.stat().st_size < 500:
        raise SystemExit(f"[失败] 内联舱位页异常: {html}（检查上方 air_intl_book 输出）")
    html_text = html.read_text(encoding="utf-8", errors="replace")
    # 契约标记取页面真实产物（舱位容器 + 去下单链接），不要校验 action 字面量：
    # v3.x 页面已不在 HTML 里吐 "inline-cabins" 字符串，校验它会导致每条查询都误判失败。
    if 'class="cab-wrap' not in html_text or '去下单' not in html_text:
        raise SystemExit(f"[失败] 页面契约校验失败: {html} 不含内联舱位或去下单链接，禁止交付")

    _run.write_ok(raw_path, html=html, present_dir=args.present_dir)
    _log("\n" + "=" * 72)
    _log(f"完成，总耗时 {time.time() - t_all:.1f}s")
    _log(f"交付（present_files 首位，不要启动任何 server）: {html}")
    _log(f"解析数据: {parsed_path.resolve()}")
    _log(f"run-dir: {runs.resolve()}")
    _log(f"shopping-json: {raw_path.resolve()}")
    _log(f"parsed-json: {parsed_path.resolve()}")
    _log(f"html: {html}")
    _log("页面内 Top 精选已内联舱位并提供去下单链接；其余航班保留页内查舱位入口。")
    _log("serialNumber 为短时效会话；过期后 allcab 返回空舱位，重跑本脚本即可。")
    return 0


def _code_tag(code: str) -> str:
    return code.upper().replace(" ", "")


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
