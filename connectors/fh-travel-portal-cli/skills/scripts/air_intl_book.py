#!/usr/bin/env python3
"""国际机票「选航班 → 选舱位 → 拼下单跳转」的 agent 驱动编排脚本。

子命令：
  inline  （推荐）批量查舱位并渲染「航班页内联舱位」页——舱位直接展开在航班行下，
          每个舱位一个「去下单」HTTPS forward 链接，点开直接进飞鹤下单页已免登。
          无复制指令、无自定义协议深链、无 JS shell。舱位抓取默认 ThreadPoolExecutor 并发
         （--workers，默认 6），单航班 1 个时自动串行。
          --scope best:N 为精选评分（直飞>>单中转>多中转、同机场中转、门到门+价格、
          非廉价航、可退改/含托运加分），0 直飞/大量中转场景用它，免得临场自写精选脚本。
  cabins  给定 serialNumber + 查询 priceId，调 intl_shopping_all_cab 取全部舱位，
          输出舱位清单并以 select-cabin 页渲染（每舱位一个「去下单」forward 链接）。
  order   给定 serialNumber + 舱位级 priceId，拼下单页跳转链接。
          默认 HTTPS forward（query authCode=forwardCode）。

依赖：mcp_proxy、mcp_envelope、sso_forward、air_intl_build_order_jump_url、air_intl_render_flight_options。
安全：调 MCP 经 fh CLI（凭据由 fh 自管）；查询结果 HTML 只写 shopping 下发的 infoCode/forwardCode。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
# 同目录的 air_intl_build_order_jump_url 不是包，不加 scripts/ 进 path 会 ImportError。
sys.path.insert(0, str(SCRIPT_DIR))

from mcp_proxy import McpProxy, McpProxyError  # noqa: E402
from unwrap_content import unwrap_envelope, EnvelopeError  # noqa: E402
from mcp_envelope import unwrap  # noqa: E402
from sso_forward import build_forward_url  # noqa: E402
from air_intl_build_order_jump_url import build_order_route  # noqa: E402
from portal_config import portal_host  # noqa: E402

DEFAULT_PORTAL_HOST = portal_host()
CABIN_CLASS = {"Y": "经济舱", "C": "商务舱", "F": "头等舱", "J": "超级经济舱", "W": "高端经济舱"}


def _flight_meta(flight: dict[str, Any]) -> dict[str, Any]:
    """从 parsed flight 取/算精选评分所需元数据（兼容缺新字段的老 parsed.json）。"""
    legs = flight.get("legs") or []
    stops = flight.get("stops")
    if stops is None:
        stops = max(0, len(legs) - 1)
    same_airport = flight.get("sameAirport")
    if same_airport is None:
        same_airport = all(
            str(legs[i].get("toCode") or "").strip() == str(legs[i + 1].get("fromCode") or "").strip()
            for i in range(len(legs) - 1)
        ) if len(legs) > 1 else True
    door = flight.get("doorToDoorMin") or flight.get("totalDurMin") or 0
    baggage = flight.get("baggage") or {}
    return {
        "stops": int(stops or 0),
        "sameAirport": bool(same_airport),
        "doorToDoorMin": int(door or 0),
        "lcc": bool(flight.get("lcc")),
        "hasCheckedBag": bool(baggage.get("check")),
        "refundable": bool(flight.get("refundable")),
        "changeable": bool(flight.get("changeable")),
    }


def _best_score(flight: dict[str, Any]) -> float:
    """精选评分，越小越好。设计原则（与 agent 人工精选口径一致）：
    直飞 >> 单中转 > 多中转；同机场中转加分；门到门耗时与价格线性计入；
    廉价航（supplier=IBELCC，无免费托运）重罚；可退改/含托运小幅加分。
    """
    meta = _flight_meta(flight)
    score = 0.0
    if flight.get("direct") and meta["stops"] == 0:
        score -= 5000.0
    elif meta["stops"] == 1:
        score -= 500.0
    else:
        score += 1500.0
    if meta["stops"] >= 1:
        score -= 300.0 if meta["sameAirport"] else 0.0
    score += meta["doorToDoorMin"] * 1.0
    try:
        score += float(flight.get("total") or 0) * 0.6
    except (TypeError, ValueError):
        pass
    if meta["lcc"]:
        score += 1200.0
    if meta["hasCheckedBag"]:
        score -= 60.0
    if meta["refundable"]:
        score -= 80.0
    if meta["changeable"]:
        score -= 80.0
    return score


def _cabin_label(cab_class: str, fare_basis: str) -> str:
    name = CABIN_CLASS.get((cab_class or "").upper(), cab_class or "舱位")
    return f"{name}（{fare_basis}）" if fare_basis else name


def _codes_from(data: dict[str, Any] | None) -> tuple[str, str]:
    data = data or {}
    return str(data.get("infoCode") or "").strip(), str(data.get("forwardCode") or "").strip()


def _resolve_selection(args) -> tuple[str, str]:
    """返回 (serialNumber, 查询 priceId)。优先用 --map + --option，其次直接用 --serial-number/--price-id。"""
    if args.map and args.option:
        import os
        mp = json.loads(Path(args.map).read_text(encoding="utf-8"))
        opt = mp.get("options", {}).get(args.option)
        if not opt:
            raise SystemExit(f"[错误] selection-map 中没有选项 {args.option}（可选：{', '.join(mp.get('options', {}).keys())}）")
        sn = opt.get("serialNumber")
        pid = opt.get("priceId")
        if not sn or not pid:
            raise SystemExit(f"[错误] 选项 {args.option} 缺少 serialNumber/priceId：{opt}")
        return sn, pid
    if args.serial_number and args.price_id:
        return args.serial_number, args.price_id
    raise SystemExit("[错误] 需提供 --map + --option，或 --serial-number + --price-id")


def _build_legs(group: dict[str, Any]) -> list[dict[str, Any]]:
    legs: list[dict[str, Any]] = []
    for trip in group.get("tripList", []) or []:
        for fl in trip.get("flightList", []) or []:
            air_line = fl.get("airLine", "") or ""
            # 国际 shopping 的 airLine 是六字连写（SZXSIN），没有分隔符。
            frm = air_line[:3].strip() or "--"
            to = (air_line[3:6] if len(air_line) >= 6 else "").strip() or "--"
            legs.append({
                "flightNo": fl.get("flightId", ""),
                # IATA 航司二字码在航班号前缀（CA123 → CA）。
                "airline": fl.get("flightId", "")[:2],
                "airlineCode": fl.get("flightId", "")[:2],
                "from": f"{frm} ({frm})",
                "to": f"{to} ({to})",
                "dep": fl.get("flyDate", ""),
                "arr": fl.get("arrDate", ""),
                "dur": fl.get("duration"),
                "aircraft": fl.get("type", ""),
            })
    return legs


def _parse_cabins(data: dict[str, Any]) -> list[dict[str, Any]]:
    """从 intl_shopping_all_cab 的 text JSON 解析舱位清单。"""
    groups = data.get("groupList") or []
    if not groups:
        return []
    # all_cab 一次查询对应一个报价组；只取第一组，多组是异常形态。
    group = groups[0]
    legs = _build_legs(group)
    cabins: list[dict[str, Any]] = []
    for idx, price in enumerate(group.get("priceList", []) or []):
        # 展示用第一程第一舱的舱等；总价在 price 上。往返也先按第一段舱等标签，避免把两段舱名拼进一格。
        trip = (price.get("tripList") or [{}])[0]
        cab = (trip.get("cabList") or [{}])[0]
        rule = trip.get("rule") or {}
        cabins.append({
            "index": idx,
            "priceId": price.get("priceId"),
            "total": price.get("totalPrice"),
            "fare": price.get("price"),
            "tax": price.get("tax"),
            # 费用拆分与渠道字段（v3.19.0）：附加费/服务费不计入 total；allowTicket=false 即需代购。
            "addPrice": price.get("addPrice"),
            "servicePrice": price.get("servicePrice"),
            "source": str(price.get("source") or ""),
            "allowTicket": bool(price.get("allowTicket", True)),
            "bigCustomer": str(price.get("customersId") or ""),
            "selfBig": bool(price.get("selfBigCustomersId")),
            "bigCustomerPrice": price.get("bigCustomerPrice") is True,
            "specialRate": price.get("specialRate"),
            # 特殊价限制规则（v3.19.1）：如「允许国籍：中国(CN)」→ 页面转写「限中国大陆乘客预订」
            "priceRules": [
                str(r.get("ruleDesc") or "").strip()
                for r in (price.get("ruleList") or [])
                if isinstance(r, dict) and str(r.get("ruleDesc") or "").strip()
            ],
            "cabin": _cabin_label(cab.get("cabClass"), cab.get("cab")),
            "fareName": cab.get("cab"),
            "recommend": bool(price.get("recommend")),
            "refundable": bool(rule.get("refund")),
            "changeable": bool(rule.get("change")),
            "upgradable": bool(rule.get("upgra")),
            "legs": legs,
            "totalDurMin": (group.get("tripList", [{}])[0].get("duration")) if group.get("tripList") else None,
        })
    return cabins


def _fetch_cabins(proxy: McpProxy, serial_number: str, price_id: str) -> list[dict[str, Any]]:
    """调 intl_shopping_all_cab 并解析舱位。失败/空返回 []（不抛，便于批量跳过）。"""
    try:
        resp = proxy.request("tools/call", {
            "name": "intl_shopping_all_cab",
            # internal=false：走对外购物舱位，和门户查询页对拍；true 是内部渠道价。
            "arguments": {"serialNumber": serial_number, "priceId": price_id, "internal": False},
        })
    except McpProxyError:
        return []
    result = resp.get("result", {})
    content = result.get("content") if isinstance(result, dict) else None
    if isinstance(content, list):
        for block in content:
            if block.get("type") == "text":
                try:
                    unwrap_envelope(json.loads(block["text"]))  # 仅用于尽早抛出 ok=false
                except json.JSONDecodeError:
                    pass
                except EnvelopeError as exc:
                    print(f"[警告] allcab 失败（serialNumber={serial_number}）：{exc}", file=sys.stderr)
                    return []
    data = unwrap(resp)
    if not isinstance(data, dict) or not data.get("groupList"):
        return []
    return _parse_cabins(data)


def _cabin_for_inline(cabin: dict[str, Any]) -> dict[str, Any]:
    """把 _parse_cabins 的舱位条目归一为 cabins_by_option.json 的条目（供 render inline-cabins 用）。"""
    return {
        "key": f"C{cabin.get('index', 0):03d}",
        "cabin": cabin.get("cabin"),
        "fareName": cabin.get("fareName"),
        "total": cabin.get("total"),
        "fare": cabin.get("fare"),
        "tax": cabin.get("tax"),
        "addPrice": cabin.get("addPrice"),
        "servicePrice": cabin.get("servicePrice"),
        "refundable": cabin.get("refundable"),
        "changeable": cabin.get("changeable"),
        "recommend": cabin.get("recommend"),
        "allowTicket": cabin.get("allowTicket", True),
        "bigCustomer": cabin.get("bigCustomer"),
        "selfBig": cabin.get("selfBig"),
        "bigCustomerPrice": cabin.get("bigCustomerPrice", False),
        "specialRate": cabin.get("specialRate"),
        "priceRules": cabin.get("priceRules") or [],
        "source": cabin.get("source"),
        "priceId": cabin.get("priceId"),
    }


def cmd_cabins(args) -> int:
    sn, pid = _resolve_selection(args)
    map_data: dict[str, Any] = {}
    if args.map:
        map_data = json.loads(Path(args.map).read_text(encoding="utf-8"))
    info_code, forward_code = _codes_from(map_data)
    proxy = McpProxy(timeout=120)
    try:
        resp = proxy.request("tools/call", {
            "name": "intl_shopping_all_cab",
            "arguments": {"serialNumber": sn, "priceId": pid, "internal": False},
        })
    except McpProxyError as exc:
        print(f"[错误] 舱位查询失败：{exc}", file=sys.stderr)
        return 1

    result = resp.get("result", {})
    content = result.get("content") if isinstance(result, dict) else None
    if isinstance(content, list):
        for block in content:
            if block.get("type") == "text":
                try:
                    unwrap_envelope(json.loads(block["text"]))
                except json.JSONDecodeError:
                    pass
                except EnvelopeError as exc:
                    print(f"[错误] 舱位查询被服务端拒绝：{exc}", file=sys.stderr)
                    return 1
    data = unwrap(resp)
    if not data or not data.get("groupList"):
        print("[错误] 舱位响应为空或格式异常，serialNumber 可能已过期（请重新查询）", file=sys.stderr)
        return 1

    cabins = _parse_cabins(data)
    if not cabins:
        print("[错误] 未解析到任何舱位", file=sys.stderr)
        return 1

    # 文本清单（供 agent 在对话里转述给用户）
    print(f"舱位清单（航班 serialNumber={sn}，查询 priceId={pid}）：")
    for c in cabins:
        tags = []
        if c["recommend"]:
            tags.append("推荐")
        tags.append("可退" if c["refundable"] else "不可退")
        tags.append("可改" if c["changeable"] else "不可改")
        print(f"  C{c['index']:03d}  {c['cabin']}  ¥{c['total']}  {'/'.join(tags)}  priceId={c['priceId']}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 归一化 JSON（供 air_intl_render_flight_options.py 渲染 select-cabin 页）
    flights = []
    mapping = {}
    for c in cabins:
        key = f"C{c['index']:03d}"
        flights.append({
            "optionKey": key, "rank": c["index"] + 1, "direct": len(c["legs"]) <= 1,
            "recommended": c["recommend"], "legs": c["legs"], "cabin": c["cabin"],
            "fareName": c["fareName"], "total": c["total"], "fare": c["fare"], "tax": c["tax"],
            "addPrice": c.get("addPrice"), "servicePrice": c.get("servicePrice"),
            "source": c.get("source", ""), "allowTicket": c.get("allowTicket", True),
            "bigCustomer": c.get("bigCustomer", ""), "selfBig": c.get("selfBig", False),
            "bigCustomerPrice": c.get("bigCustomerPrice", False),
            "specialRate": c.get("specialRate"),
            "priceRules": c.get("priceRules") or [],
            "totalDurMin": c["totalDurMin"], "baggage": {}, "refundable": c["refundable"],
            "changeable": c["changeable"], "upgradable": c["upgradable"],
            "agreement": bool(c.get("bigCustomer")) or bool(c.get("selfBig")) or c.get("bigCustomerPrice") is True,
            "priceId": c["priceId"],
        })
        mapping[key] = {"serialNumber": sn, "priceId": c["priceId"], "rank": c["index"] + 1}
    norm = {
        "serialNumber": sn,
        "infoCode": info_code or None,
        "forwardCode": forward_code or None,
        "flights": flights,
        "summary": "舱位选择（选航班后第二步）",
    }
    norm_path = out_dir / "cabins_normalized.json"
    norm_path.write_text(json.dumps(norm, ensure_ascii=False, indent=2), encoding="utf-8")

    # 渲染 select-cabin 页 + 写舱位 selection-map
    html_path = out_dir / "cabins.html"
    map_path = out_dir / "cabins.selection-map.json"
    try:
        # 走子进程而不是 import：渲染脚本自己的 CLI/编码隔离；失败仍保留上面的文本清单。
        subprocess.run([
            sys.executable, str(SCRIPT_DIR / "air_intl_render_flight_options.py"),
            str(norm_path), "--output", str(html_path), "--map-output", str(map_path),
            "--action", "select-cabin",
            # 没传 --title 时的占位文案，不是把查询锁死在北京/新加坡。
            "--title", args.title or "舱位选择 · 北京 → 新加坡",
            "--meta", args.meta or "选择舱位后拼下单跳转",
        ], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        print(f"[警告] 舱位页渲染失败（不影响文本清单）：{exc.stderr[-300:]}", file=sys.stderr)

    print("\n舱位选择页：", html_path)
    print("舱位映射文件：", map_path)
    print("\n下一步：回复你想订的舱位编号（如 C000 / C002），或舱位名，我执行 `order` 拼下单跳转。")
    return 0


def cmd_order(args) -> int:
    flight_items = [{"serialNumber": args.serial_number, "priceId": args.price_id}]
    route = build_order_route(
        flight_items, adult=args.adult, pay_type=args.pay_type,
        fly_type=args.fly_type, agent="1",
        application_id=args.application_id, dh=args.dh,
    )
    forward_code = args.forward_code
    if not forward_code and args.map:
        _, forward_code = _codes_from(json.loads(Path(args.map).read_text(encoding="utf-8")))
    if not forward_code:
        print("[错误] forward 链接需要 forwardCode（当次 intl_shopping 最外层，或 --map / --forward-code）", file=sys.stderr)
        return 1
    print(build_forward_url(route, args.portal_host, forward_code))
    print("\n说明：HTTPS forward 链接（query authCode=forwardCode），点开直接进飞鹤下单页已免登。")
    return 0


def cmd_inline(args) -> int:
    """批量查舱位 + 渲染「全量方案单页」（推荐，无复制、无自定义协议、无 server）。

    流程：读 parsed_shopping → 按 scope 选航班（best:N=精选评分，只查精选）→
    批量 intl_shopping_all_cab → 聚合 cabins_by_option.json →
    调 air_intl_render_flight_options.py --action inline-cabins 渲染**全量**航班列表：
    精选航班内联舱位表（每舱位一个 HTTPS forward「去下单」链接），
    其余航班带页内「查舱位」按钮，直接调用 busi intlShop（infoCode）并原地渲染。

    舱位抓取默认并发（--workers，默认 6）：每 worker 独立 McpProxy 实例（stateless 部署，
    无共享可变状态，线程安全），同 CLI 凭据复用；--workers 1 或仅 1 个航班时自动回退串行。
    """
    parsed_path = Path(args.parsed)
    data = json.loads(parsed_path.read_text(encoding="utf-8"))
    flights = data.get("flights")
    if not isinstance(flights, list) or not flights:
        print("[错误] parsed json 缺少 flights[]", file=sys.stderr)
        return 1
    serial_number = data.get("serialNumber")
    if not serial_number:
        print("[错误] parsed json 缺少 serialNumber", file=sys.stderr)
        return 1

    map_path = Path(args.map) if args.map else parsed_path.with_name(parsed_path.stem + ".selection-map.json")
    # priceId 直接取自 parsed flights（air_intl_parse_shopping 已写入），selection-map 仅作兼容回退。
    options: dict[str, Any] = {}
    if map_path.exists():
        try:
            sel_map = json.loads(map_path.read_text(encoding="utf-8"))
            opts = sel_map.get("options", {})
            if isinstance(opts, dict):
                options = opts
        except (OSError, json.JSONDecodeError):
            pass

    # 按 scope 选要查舱位的航班：(optionKey, serialNumber, priceId)
    scope = args.scope
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    picked_keys: set[str] | None = None
    if scope.startswith("best:"):
        # best:N（v2.6.0）：按精选评分取前 N（直飞>>单中转>多中转、同机场、
        # 门到门+价格、非廉价、可退改/含托运加分）。v3.0.0 起不再写子集文件：
        # 渲染输入保持**全量** parsed，仅对精选航班查舱位；其余航班在页面上
        # 其余航班由页面内按钮补查，保持零 server。
        try:
            best_n = int(scope.split(":", 1)[1])
        except ValueError:
            print(f"[错误] scope=best:N 的 N 非法：{scope}", file=sys.stderr)
            return 1
        scored = [
            (_best_score(fl), idx, fl)
            for idx, fl in enumerate(flights, 1)
            if fl.get("priceId") or (options.get(f"F{idx:03d}") or {}).get("priceId")
        ]
        scored.sort(key=lambda item: (item[0], item[1]))
        picked = scored[:best_n]
        picked_sorted = sorted(picked, key=lambda item: item[1])  # 保持原文件顺序，F 编号稳定
        print(f"best:{best_n} 精选（评分=门到门+价格*0.6，直飞/单中转/同机场/非廉价加分）：", file=sys.stderr)
        for score, idx, fl in picked_sorted:
            meta = _flight_meta(fl)
            tag = "直飞" if (fl.get("direct") and meta["stops"] == 0) else (
                f"中转{'·'.join(fl.get('transferAirports') or ['?'])}"
                + ("" if meta["sameAirport"] else "(跨机场)"))
            print(
                f"  F{idx:03d} score={score:.0f} ¥{fl.get('total', '--')} "
                f"[{meta['doorToDoorMin'] // 60}h{meta['doorToDoorMin'] % 60:02d}m] {tag}"
                f"{' · 廉价航' if meta['lcc'] else ''}{' · 退✓' if meta['refundable'] else ''}"
                f"{' · 改✓' if meta['changeable'] else ''}",
                file=sys.stderr,
            )
        picked_keys = {f"F{idx:03d}" for _, idx, _ in picked_sorted}

    targets: list[tuple[str, str, str]] = []
    top_n = 0
    if scope.startswith("top:"):
        try:
            top_n = int(scope.split(":", 1)[1])
        except ValueError:
            print(f"[错误] scope=top:N 的 N 非法：{scope}", file=sys.stderr)
            return 1
    for idx, fl in enumerate(flights, 1):
        key = f"F{idx:03d}"
        if picked_keys is not None and key not in picked_keys:
            continue  # best:N 模式只对精选航班查舱位；其余渲染为静态「查舱位」按钮
        pid = fl.get("priceId") or (options.get(key) or {}).get("priceId")
        if not pid:
            continue
        if scope == "direct" and not fl.get("direct"):
            continue
        if top_n and idx > top_n:
            # parsed 列表已经按推荐序排过，top:N 就是前 N 条，不是再按价格筛。
            continue
        targets.append((key, serial_number, str(pid)))

    if not targets:
        print("[错误] 当前 scope 下没有可查舱位的航班", file=sys.stderr)
        return 1

    proxy = McpProxy(timeout=120)

    cabins_by_option: dict[str, list[dict[str, Any]]] = {}
    ok_count = 0
    workers = max(1, getattr(args, "workers", 6))

    def _one_cabins(item: tuple[str, str, str]) -> tuple[str, list[dict[str, Any]]]:
        """单航班查舱位：每个 worker 独立 McpProxy（stateless 部署，无共享可变状态，线程安全）。"""
        key, sn, pid = item
        p = McpProxy(timeout=120) if workers > 1 else proxy
        return key, _fetch_cabins(p, sn, pid)

    if workers <= 1 or len(targets) <= 1:
        # 串行回退（保持逐条日志，便于排障）
        for i, (key, sn, pid) in enumerate(targets, 1):
            print(f"[{i}/{len(targets)}] {key} allcab ...", file=sys.stderr)
            cabins = _fetch_cabins(proxy, sn, pid)
            cabins_by_option[key] = [_cabin_for_inline(c) for c in cabins]
            if cabins:
                ok_count += 1
                print(f"   {key} -> {len(cabins)} 舱位", file=sys.stderr)
            else:
                print(f"   {key} -> 无舱位（航司偶发空舱位，跳过）", file=sys.stderr)
    else:
        print(f"并行查舱位：{len(targets)} 个航班，workers={workers}", file=sys.stderr)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            fut_map = {ex.submit(_one_cabins, t): t[0] for t in targets}
            for fut in as_completed(fut_map):
                key = fut_map[fut]
                try:
                    _, cabins = fut.result()
                except Exception as exc:  # noqa: BLE001
                    print(f"   {key} 异常: {exc}", file=sys.stderr)
                    cabins = []
                cabins_by_option[key] = [_cabin_for_inline(c) for c in cabins]
                if cabins:
                    ok_count += 1
                    print(f"   {key} -> {len(cabins)} 舱位", file=sys.stderr)
                else:
                    print(f"   {key} -> 无舱位（航司偶发空舱位，跳过）", file=sys.stderr)

    cabins_path = out_dir / "cabins_by_option.json"
    cabins_path.write_text(json.dumps(cabins_by_option, ensure_ascii=False, indent=2), encoding="utf-8")

    html_path = out_dir / "flights_inline.html"
    map_out_path = out_dir / "flights_inline.selection-map.json"
    cmd = [
        sys.executable, str(SCRIPT_DIR / "air_intl_render_flight_options.py"),
        str(parsed_path), "--output", str(html_path), "--map-output", str(map_out_path),
        "--action", "inline-cabins", "--cabins", str(cabins_path),
        "--cabins-out-dir", str(out_dir.resolve()),
        "--adult", args.adult, "--pay-type", args.pay_type, "--fly-type", args.fly_type,
        "--portal-host", args.portal_host,
        "--title", args.title or "航班方案 · 舱位内联",
    ]
    for m in args.meta or []:
        cmd += ["--meta", m]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        print(f"[错误] 内联舱位页渲染失败：{exc.stderr[-400:]}", file=sys.stderr)
        return 1

    # 产物自检（v2.6.0）：打印 resolve() 后的绝对路径并校验非空，
    # 防止相对路径/Git Bash 路径写错位置后 agent 还要全盘搜索。
    for label, path in (("内联舱位页", html_path), ("舱位聚合", cabins_path), ("选择映射", map_out_path)):
        resolved = path.resolve()
        if not resolved.exists() or resolved.stat().st_size == 0:
            print(f"[错误] 产物异常（不存在或为空）：{resolved}", file=sys.stderr)
            return 1
        print(f"{label}：{resolved}")

    print(f"\n批量查舱位：{ok_count}/{len(targets)} 个航班有舱位")
    print("说明：每个舱位的「去下单」是 HTTPS forward 链接（query authCode=forwardCode），点开直接进飞鹤下单页已免登。")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        # Windows 控制台默认 GBK，舱位中文/¥ 会崩。
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_c = sub.add_parser("cabins", help="查全部舱位并渲染舱位选择页")
    p_c.add_argument("--map", help="S3 选航班的 selection-map.json")
    p_c.add_argument("--option", help="选项编号，如 F090")
    p_c.add_argument("--serial-number", dest="serial_number", help="serialNumber（与 --price-id 二选一）")
    p_c.add_argument("--price-id", dest="price_id", help="查询 priceId（与 --serial-number 二选一）")
    p_c.add_argument("--out-dir", default=".", help="舱位页/映射输出目录")
    p_c.add_argument("--title", default="")
    p_c.add_argument("--meta", default="")

    p_o = sub.add_parser("order", help="拼下单页跳转链接（HTTPS forward）")
    p_o.add_argument("--serial-number", dest="serial_number", required=True)
    p_o.add_argument("--price-id", dest="price_id", required=True, help="舱位级 priceId（intl_shopping_all_cab 返回）")
    p_o.add_argument("--adult", default="1")
    p_o.add_argument("--fly-type", dest="fly_type", default="1", help="1=单程，2=往返，3=多程")
    p_o.add_argument("--pay-type", dest="pay_type", default="1", help="1=公费，0=自费")
    p_o.add_argument("--application-id", dest="application_id", default="")
    p_o.add_argument("--dh", default="")
    p_o.add_argument("--portal-host", dest="portal_host", default=DEFAULT_PORTAL_HOST)
    p_o.add_argument("--forward-code", dest="forward_code", default="", help="当次 intl_shopping 的 forwardCode")
    p_o.add_argument("--map", help="selection-map.json（可从中读 forwardCode）")

    p_i = sub.add_parser("inline", help="批量查舱位并渲染内联舱位页")
    p_i.add_argument("--parsed", required=True, help="air_intl_parse_shopping.py 的 parsed json（含 flights + serialNumber）")
    p_i.add_argument("--map", help="selection-map.json（可选兼容；priceId 默认直接取自 parsed flights）")
    p_i.add_argument("--out-dir", default=".", help="内联页/聚合输出目录")
    p_i.add_argument("--scope", default="direct", help="direct（默认，仅直飞）/ all / top:N（原始顺序前 N）/ best:N（精选评分前 N：直飞>单中转、同机场、门到门+价格、非廉价，0 直飞场景推荐）")
    p_i.add_argument("--title", default="")
    p_i.add_argument("--meta", action="append", default=[])
    p_i.add_argument("--adult", default="1")
    p_i.add_argument("--pay-type", dest="pay_type", default="1", help="1=公费，0=自费")
    p_i.add_argument("--fly-type", dest="fly_type", default="1", help="1=单程，2=往返，3=多程")
    p_i.add_argument("--portal-host", dest="portal_host", default=DEFAULT_PORTAL_HOST)
    p_i.add_argument("--workers", type=int, default=6, help="并行查舱位的线程数（1=串行回退，默认 6）")

    args = parser.parse_args()
    if args.cmd == "cabins":
        return cmd_cabins(args)
    if args.cmd == "order":
        return cmd_order(args)
    if args.cmd == "inline":
        return cmd_inline(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
