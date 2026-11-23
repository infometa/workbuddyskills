#!/usr/bin/env python3
"""免登跳转基建：编码、拼 route、包 /oauth2/forward。

产品脚本只负责前端 path、hash 和业务字段；本库不写死任何城市/日期/页面。
契约见 references/sso-forward.md。

库用法：
  from sso_forward import (
      encode_value, join_query, assemble_route, encode_json_param,
      build_forward_url,
  )

不调 MCP、不取 token。跳转用 shopping 下发的 forwardCode（query authCode）；
页内补查用 infoCode（请求头 X-Auth-Code）。
"""

from __future__ import annotations

import json
from urllib.parse import quote, urlparse

from portal_config import forward_base as _cfg_forward_base
from portal_config import portal as _cfg_portal

_p0 = _cfg_portal()
# 兼容旧 `from sso_forward import DEFAULT_PORTAL_HOST`；真源仍是 config.json。
DEFAULT_PORTAL_HOST = _p0["host"]
FORWARD_PATH = _p0["forwardPath"]


def encode_value(value: str | None) -> str:
    """Encode a single value for the redirectPage payload.

    - Chinese / non-ASCII → double encode (server decodes once, then Tomcat needs
      the value to still be ASCII to write the Location header).
    - ASCII → single encode. A literal space becomes %20 (single), which the
      server's URI parser accepts; it must NOT be decoded to a raw space.
    """
    if value is None:
        return ""
    if any(ord(ch) > 0x7F for ch in value):
        return quote(quote(value, safe=""))
    # safe=""：默认 quote 会放过 /，redirectPage 里的 / 裸着会被当成 URL 路径切开。
    return quote(value, safe="")


def join_query(fields: dict[str, str] | list[tuple[str, str]], *, encode: bool = True) -> str:
    """Join k=v pairs. Empty/None values are omitted. Order is insertion order."""
    if isinstance(fields, dict):
        items = list(fields.items())
    else:
        items = list(fields)
    parts: list[str] = []
    for key, value in items:
        if value in (None, ""):
            # 列表页空表单字段不要出现在 hash。已编过的值请用 encode=False，否则 % 会变成 %25。
            continue
        parts.append(f"{key}={encode_value(value) if encode else value}")
    return "&".join(parts)


def assemble_route(page: str, hash_path: str, query: str = "") -> str:
    """page + '#' + hash_path + query.

    hash_path examples: '/?' (list page, query appended after '?'),
    '/bookingPricing' (order page, a '?' is inserted before query).
    """
    if not hash_path.startswith("/"):
        # Vue hash 路由必须以 / 开头，缺了前端匹配不到页。
        hash_path = "/" + hash_path
    if not query:
        if hash_path.endswith("?"):
            return f"{page}#{hash_path}"
        return f"{page}#{hash_path}"
    if hash_path.endswith("?"):
        # 列表页自带 /?，query 直接接在问号后；下单页是 /bookingPricing，要自己补 ?。
        return f"{page}#{hash_path}{query}"
    return f"{page}#{hash_path}?{query}"


def encode_json_param(obj: object, *, safe: str = ",/") -> str:
    """Percent-encode a JSON value for one query field (e.g. flightList).

    Default safe=',/' matches the international order page: commas and slashes
    in priceId stay bare in the fragment.
    """
    # 紧凑 JSON 且保留中文：多空格会变成 %20，和门户前端 JSON.parse 对不上。
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return quote(raw, safe=safe)


def build_forward_url(route: str, portal_host: str, auth_code: str = "") -> str:
    """Wrap a route into /oauth2/forward（redirectPage = 整段路由编码一次）。

    redirectPage must be *the whole route encoded once* so the server receives the
    raw route as one query param. auth_code 是 shopping 下发的 forwardCode（query 名 authCode）。
    forward 基址引用 config.json（portal_config）；portal_host 非空时只替换主机名。
    """
    fb = _cfg_forward_base()
    if portal_host:
        p = urlparse(fb)
        base = f"{p.scheme}://{portal_host}{p.path}"
    else:
        base = fb
    # 整段 route 再 quote 一次：服务端只解 redirectPage 这一层，拿到的是前端 hash 原文。
    url = f"{base}?redirectPage={quote(route, safe='')}"
    if auth_code:
        url += f"&authCode={quote(auth_code, safe='')}"
    return url


# 国内下单页（免登 forward 的 redirectPage 目标，路径与 crmdev 前端一致）：
#   https://<portal 前端 host>/VuePage/domestic/index.html#/bookingPricing
DOMESTIC_FRONTEND_PAGE = "/VuePage/domestic/index.html"
DOMESTIC_ORDER_ROUTE = "/bookingPricing"


def build_domestic_order_route(
    serial_number: str,
    flight_id: str,
    cab_id: str,
    adult: str = "1",
    pay_type: str = "1",
    fly_type: str = "1",
    agent: str = "1",
    application_id: str = "",
    dh: str = "",
) -> str:
    """国内下单页路由 `#/bookingPricing`（前端页面消费本路由 query）。

    字段全部在最外层，**不要**再传 flightList。选舱之后才有 cabId。
    单程 / 推荐往返同一形态：serialNumber + flightId + cabId。
    推荐往返：serialNumber 共用一次查询会话；flightId 取第一程（去程）航段航班号；
    cabId 取第一程（去/回 cabId 相同）；flyType=2。
    flyType: 1=单程 2=往返；adultCount=查询 passengerNum；payType: 1=公费(对应查询
    official=true) 0=自费；agent 固定 '1'；applicationId/dh 出差单信息，缺省省略。
    """
    fields = {
        "serialNumber": serial_number or "",
        "flightId": flight_id or "",
        "cabId": cab_id or "",
        "flyType": fly_type,
        "adultCount": str(int(adult or 1)),
        "payType": pay_type,
        "agent": agent,
    }
    if application_id:
        fields["applicationId"] = application_id
    if dh:
        fields["dh"] = dh
    return assemble_route(DOMESTIC_FRONTEND_PAGE, DOMESTIC_ORDER_ROUTE, join_query(fields, encode=True))
