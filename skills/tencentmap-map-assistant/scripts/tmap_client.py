"""
TencentMap_map-assistant · 客户端

封装腾讯位置服务 C 端能力：
- 旅游攻略 travel_guide → 含小程序入口图（二维码）
- 地点搜索 / POI 详情 / 周边 / 路线 → 数据
- 地址坐标互转 / 输入补全 / IP 定位 / 行政区划 / 距离矩阵 → 数据

key 策略：
- 检测顺序：用户传入参数 → TMAP_KEY 环境变量 → skill 包内 .env 文件
- 若三者都没有 → 走体验通道（h5gw + key=none + apptag）继续完成任务，额度和稳定性受限。
"""

import os
import json
import time
import base64
import hashlib
import hmac
import random
import string
from typing import Any, Dict, List, Optional, Tuple

import requests


# ============================================================
# 常量
# ============================================================

# 创建指南/二维码网关签名密钥
_SIGN_SECRET = "cd0da99c92037580fc272060da23d384"

# 运营固定 user_id（攻略入库使用）
_OPERATION_USER_ID = "50000000002"

# 服务端点
_WS_BASE = "https://apis.map.qq.com"           # 正式 key 通道
_H5GW_BASE = "https://h5gw.map.qq.com"         # 体验通道（key=none + apptag + jsonp）
_A2A_URL = "https://h5gw.map.qq.com/aichat/v1/a2a"   # AI 旅游攻略 A2A（体验通道）
# 旅游攻略保存并出二维码（保存+出码合一接口，正式公网域名）
_TG_SAVE_QR_URL = "https://h5gw.map.qq.com/travelguide/saveandgenqrcode"

# 小程序原始 ID
_MINI_PROGRAM_USERNAME = "gh_ff25a9b4394d"

# 请求超时
_TIMEOUT = 60
_A2A_TIMEOUT = 300  # SSE 长连接

# 地点搜索/输入提示富信息字段（评分、人均、营业时间）
_RICH_ADDED_FIELDS = "star_level,avg_price,opening_hours"

# 体验通道：每个 path 对应专用 apptag
_APPTAG_MAP = {
    "/ws/geocoder/v1":             "lbs_geocoder",
    "/ws/place/v1/search":         "h5mutipos_place_search",
    "/ws/place/v1/suggestion":     "lbsplace_sug",
    "/ws/place/v1/detail":         "lbsplace_detail",
    "/ws/location/v1/ip":          "lbslocation_ip",
    "/ws/district/v1/list":        "lbsdistrict_list",
    "/ws/district/v1/getchildren": "lbsdistrict_getchildren",
    "/ws/district/v1/search":      "lbsdistrict_search",
    "/ws/direction/v1/driving":    "lbsdirection_driving",
    "/ws/direction/v1/transit":    "lbsdirection_transit",
    "/ws/direction/v1/walking":    "lbsdirection_walking",
    "/ws/direction/v1/bicycling":  "lbsdirection_bicycling",
    "/ws/distance/v1/matrix":      "lbsdistance_matrix",
    "/ws/weather/v1":              "lbs_weather",
}


# ============================================================
# .env 解析（极简手写，不依赖 python-dotenv）
# ============================================================

def _load_env_file(env_path: str) -> Dict[str, str]:
    """读取 .env 风格的 KEY=VALUE 文件，忽略注释行/空行。返回 dict。"""
    out: Dict[str, str] = {}
    if not os.path.exists(env_path):
        return out
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, _, v = s.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and v:
                    out[k] = v
    except Exception:
        pass
    return out


def _resolve_key(passed_key: Optional[str]) -> Tuple[Optional[str], str]:
    """按 用户传入 → 环境变量 → skill 包内 .env 文件 顺序解析 key。

    :return: (key, source) — key 可能为 None（走体验通道），source 标识来源
    """
    if passed_key:
        return passed_key, "argument"
    env_key = os.environ.get("TMAP_KEY")
    if env_key:
        return env_key, "env"
    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(skill_root, ".env")
    file_env = _load_env_file(env_file)
    file_key = file_env.get("TMAP_KEY")
    if file_key:
        # 同步写入 os.environ 以便后续模块读取
        os.environ["TMAP_KEY"] = file_key
        return file_key, "dotenv"
    return None, "experience"


def save_key_to_dotenv(key: str) -> str:
    """把客户提供的正式 key 持久化到 skill 包内 .env 文件。

    :return: .env 文件绝对路径
    """
    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(skill_root, ".env")
    # 已有内容则替换 TMAP_KEY 一行，否则追加
    existing = _load_env_file(env_path)
    existing["TMAP_KEY"] = key
    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")
    os.environ["TMAP_KEY"] = key
    return env_path


# ============================================================
# TmapClient
# ============================================================

class TmapClient:
    """腾讯位置服务地图助手客户端。

    用法：
        # 1) 客户已配置 TMAP_KEY → 直接用
        client = TmapClient()

        # 2) 客户传入正式 key（也会同步落到 .env）
        client = TmapClient(key="XXX-XXX-XXX-XXX-XXX-XXX", persist=True)

        # 3) 客户未配置 → 走体验通道（不传 key 即可）
        client = TmapClient()
    """

    def __init__(
        self,
        key: Optional[str] = None,
        qrcode_dir: Optional[str] = None,
        persist: bool = False,
    ):
        resolved, source = _resolve_key(key)
        self.key = resolved                       # None 表示体验通道
        self.key_source = source                  # 'argument' / 'env' / 'dotenv' / 'experience'
        self.is_experience_mode = resolved is None
        if persist and key:
            save_key_to_dotenv(key)
            self.key_source = "dotenv"

        if qrcode_dir is None:
            qrcode_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "qrcodes")
        self.qrcode_dir = qrcode_dir
        os.makedirs(self.qrcode_dir, exist_ok=True)

        # 成品 markdown / json 落盘目录（让 Agent 走文件路径，原样输出）
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
        os.makedirs(self.output_dir, exist_ok=True)

    # ------------------------------------------------------------
    # 私有：底层调用
    # ------------------------------------------------------------

    def _rich_params(self) -> Dict[str, Any]:
        """富信息字段参数（评分 star_level / 人均 avg_price / 营业时间 opening_hours）。"""
        return {"get_rich": 1, "added_fields": _RICH_ADDED_FIELDS}

    def _ws_get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """通用 WebService GET，自动选通道。

        - 体验通道（self.key is None）→ 走 h5gw（key=none + apptag + jsonp 包裹）
        - 正式 key → 走 apis.map.qq.com
        """
        import re
        params = {k: v for k, v in params.items() if v is not None and v != ""}
        if self.is_experience_mode:
            base = _H5GW_BASE
            params["key"] = "none"
            params["apptag"] = _APPTAG_MAP.get(path, "lbs")
            params["output"] = "jsonp"
            params["callback"] = "cb"
        else:
            base = _WS_BASE
            params["key"] = self.key

        url = f"{base}{path}"
        r = requests.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        text = r.text.strip()
        # h5gw 返回 jsonp：name&&callback({...});
        m = re.match(r"^[a-zA-Z_][\w]*&&[a-zA-Z_][\w]*\((.*)\);?\s*$", text, re.S)
        if m:
            text = m.group(1)
        elif text.startswith(("qq.maps.callback(", "callback(", "cb(")):
            text = text[text.index("(") + 1 : text.rindex(")")]
        data = json.loads(text)
        if data.get("status") != 0:
            raise TmapError(data.get("status"), data.get("message", "unknown error"), path, data)
        return data

    def _sign_headers(self, markdown_b64: str, qimei36: str) -> Dict[str, str]:
        """生成 saveandgenqrcode 接口的 HMAC-SHA256 签名头。

        签名串按字母序拼接（markdown_content 用 base64 原值，不再哈希）：
            markdown_content=<b64>&nonce=<16位>&qimei36=<>&timestamp=<秒>
        X-Sign = HMAC-SHA256(签名串, _SIGN_SECRET)
        """
        timestamp = str(int(time.time()))
        nonce = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        sign_str = (
            f"markdown_content={markdown_b64}"
            f"&nonce={nonce}"
            f"&qimei36={qimei36}"
            f"&timestamp={timestamp}"
        )
        sign = hmac.new(_SIGN_SECRET.encode(), sign_str.encode(), hashlib.sha256).hexdigest()
        return {
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Sign": sign,
            "tmap-userid": _OPERATION_USER_ID,
            "Content-Type": "application/json",
        }

    def _a2a_stream(self, query: str, lat: float, lng: float) -> Dict[str, Any]:
        """A2A 旅游攻略 SSE 长连接，聚合 plan_summary + plan_days。"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "message/stream",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": query}],
                    "metadata": {
                        "brand": "oppo",
                        "device_id": "skill-" + uuid_hex(16),
                        "latitude": lat,
                        "longitude": lng,
                        "osVersion": "16.1",
                        "theme": "light",
                        "traceId": uuid_hex(16),
                    },
                }
            },
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        url = f"{_A2A_URL}?key=none&apptag=lbs_ai_chat_a2a"
        with requests.post(url, json=payload, headers=headers, stream=True, timeout=_A2A_TIMEOUT) as r:
            r.raise_for_status()
            raw = b""
            for chunk in r.iter_content(chunk_size=None):
                raw += chunk

        # SSE 必须按 \n\n 切事件，不能用 iter_lines
        text = raw.decode("utf-8", errors="replace")
        plan_summary = None
        plan_days: List[Dict[str, Any]] = []
        for blk in text.split("\n\n"):
            if not blk.strip():
                continue
            data_lines = [l[5:].lstrip() for l in blk.split("\n") if l.startswith("data:")]
            if not data_lines:
                continue
            try:
                ev = json.loads("\n".join(data_lines))
            except Exception:
                continue
            res = ev.get("result", {})
            if res.get("kind") != "artifact-update":
                continue
            art = res.get("artifact", {})
            name = art.get("name", "")
            for p in art.get("parts", []):
                if "data" not in p:
                    continue
                if name == "plan_summary":
                    plan_summary = p["data"]
                elif name == "plan_day":
                    plan_days.append(p["data"])

        if plan_summary is None and not plan_days:
            raise TmapError(-1, "A2A 未返回攻略数据，可能是 query 不含明确目的地或服务端限流", "a2a", {})

        return {"plan_summary": plan_summary, "plan_days": plan_days}

    def _build_markdown(self, plan_days: List[Dict[str, Any]], city: str, title: str) -> str:
        """A2A plan_days → 旅游攻略保存接口要求的 markdown 格式。"""
        total_pois = sum(len(d.get("items", [])) for d in plan_days)
        n_days = len(plan_days)

        def link(p: Dict[str, Any], day: int, num: int) -> str:
            name = p["location_name"]
            poi_id = p["poi_uid"]
            lat = int(round(float(p["latitude"]) * 1e6))
            lng = int(round(float(p["longitude"]) * 1e6))
            return f"[{name}](city={city}&day={day}&poi_id={poi_id}&num={num}&lat={lat}&lng={lng}&type=1&source=fix)"

        lines: List[str] = [
            f"### {title}",
            f"{n_days}天～{total_pois}个地点",
            "由腾讯地图 AI 攻略生成",
            "",
            "### 📋 行程总览",
        ]
        for di, day in enumerate(plan_days, 1):
            pois = day.get("items", [])
            arrow = " -> ".join(link(p, di, ni) for ni, p in enumerate(pois, 1))
            lines.append(f"Day {di}：{arrow}")
        lines.append("")
        lines.append("### 📖 行程详情")
        for di, day in enumerate(plan_days, 1):
            lines.append(f"#### Day {di}：{day.get('day_title', f'第{di}天')}")
            pois = day.get("items", [])
            arrow = " -> ".join(link(p, di, ni) for ni, p in enumerate(pois, 1))
            lines.append(arrow)
            lines.append("")
        return "\n".join(lines)

    def _save_and_gen_qrcode(self, query: str, markdown: str, save_name: Optional[str] = None) -> Dict[str, Any]:
        """调 saveandgenqrcode：保存攻略并生成小程序二维码（一步完成）。

        返回 {"travel_guide_id", "qr_code"(data URI), "qr_path"(本地PNG), "expire_seconds"}。
        """
        markdown_b64 = base64.b64encode(markdown.encode("utf-8")).decode("ascii")
        qimei36 = "skill_" + uuid_hex(16)
        body = {
            "user_id": _OPERATION_USER_ID,
            "user_query": query,
            "markdown_content": markdown_b64,
            "json_content": "",
            "is_check": False,
            "sync_save_route": True,   # 同步校验 POI ID 真实性（耗时 +3-5s，内容更准）
            "qimei36": qimei36,
            "env_version": "release",
        }
        headers = self._sign_headers(markdown_b64, qimei36)
        r = requests.post(_TG_SAVE_QR_URL, json=body, headers=headers, timeout=_TIMEOUT * 2)
        r.raise_for_status()
        resp = r.json()
        if resp.get("code") != 0:
            raise TmapError(resp.get("code"), resp.get("msg", "save&gen qrcode failed"), "saveandgenqrcode", resp)
        data = resp["data"]
        tg_id = data["travel_guide_id"]
        qr = data["qr_code"]
        # 二维码落盘
        png_b64 = qr.split(",", 1)[1] if qr.startswith("data:image/png;base64,") else qr
        fname = save_name or f"travel_guide_{tg_id}.png"
        qr_path = os.path.join(self.qrcode_dir, fname)
        with open(qr_path, "wb") as f:
            f.write(base64.b64decode(png_b64))
        return {
            "travel_guide_id": tg_id,
            "qr_code": qr,
            "qr_path": qr_path,
            "expire_seconds": data.get("expire_seconds"),
        }

    # ------------------------------------------------------------
    # 旅游攻略 — 含腾讯地图小程序入口图（二维码）
    # ------------------------------------------------------------

    def travel_guide(self, query: str, lat: float = 30.572815, lng: float = 104.066801) -> Dict[str, Any]:
        """生成 AI 旅游攻略并入库出腾讯地图小程序入口图。

        :param query: 用户原始 query，例如 "武汉5天精华游"
        :param lat/lng: 用户当前位置（用于 A2A 上下文，不影响目的地）
        :return: {summary, days, travel_guide_id, qr_code, qr_path, mini_program_username}
        """
        a2a = self._a2a_stream(query, lat, lng)
        summary = a2a["plan_summary"] or {}
        days = a2a["plan_days"]
        title = summary.get("summary_title") or query

        # 从第一个 POI 推城市
        city = ""
        for d in days:
            for it in d.get("items", []):
                city = it.get("city_name", "")
                if city:
                    break
            if city:
                break

        markdown = self._build_markdown(days, city or "未知", title)
        saved = self._save_and_gen_qrcode(query, markdown)
        tg_id = saved["travel_guide_id"]

        result = {
            "title": title,
            "summary": summary,
            "days": days,
            "city": city,
            "travel_guide_id": tg_id,
            "qr_code": saved["qr_code"],
            "qr_path": saved["qr_path"],
            "expire_seconds": saved["expire_seconds"],
            "mini_program_username": _MINI_PROGRAM_USERNAME,
        }

        # 强制落盘（utf-8）—— 让 Agent 走文件路径原样输出，不靠自己拼 markdown
        json_path = os.path.join(self.output_dir, f"{tg_id}.json")
        md_path = os.path.join(self.output_dir, f"{tg_id}.md")
        result_for_json = {k: v for k, v in result.items() if k != "qr_code"}
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_for_json, f, ensure_ascii=False, indent=2)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.format_for_reply(result))
        result["output_json"] = json_path
        result["output_markdown"] = md_path
        return result

    # ------------------------------------------------------------
    # 把 result 渲染成「可直接贴给用户」的成品 markdown（含末尾二维码）
    # ------------------------------------------------------------

    @staticmethod
    def format_for_reply(result: Dict[str, Any]) -> str:
        """把 travel_guide 的返回 dict 渲染成可直接发给用户的成品 markdown。

        按 A2A 攻略 item 的真实字段组织（无 rich 评分/人均字段）：
        location_name / location_desc(含时段) / location_position(地址) /
        review(推荐理由) / location_intro / tips / image_url。
        末尾附腾讯地图小程序入口二维码。Agent 拿到后原样作为回复正文即可。
        """
        if not result:
            return ""
        title = result.get("title", "旅行攻略")
        days = result.get("days", []) or []
        qr_path = result.get("qr_path", "")
        city = result.get("city", "")

        lines: List[str] = []
        lines.append(f"# {title}")
        if city:
            lines.append(f"目的地：**{city}** · 共 {len(days)} 天 · 由腾讯地图 AI 生成")
        lines.append("")

        for di, day in enumerate(days, 1):
            day_title = day.get("day_title", f"第 {di} 天")
            day_desc = day.get("day_desc", "")
            lines.append(f"## Day {di}：{day_title}")
            if day_desc:
                lines.append(f"> {day_desc}")
            lines.append("")
            for pi, poi in enumerate(day.get("items", []), 1):
                name = poi.get("location_name", "")
                desc = poi.get("location_desc", "")
                addr = poi.get("location_position", "")
                review = poi.get("review", "")
                intro = poi.get("location_intro", "")
                tips = poi.get("tips") or []

                lines.append(f"**{pi}. {name}**")
                if desc:
                    lines.append(f"- ⏰ {desc}")
                if addr:
                    lines.append(f"- 📍 {addr}")
                if review:
                    lines.append(f"- 💡 {review}")
                elif intro:
                    lines.append(f"- 💡 {intro}")
                for tip in tips:
                    if tip:
                        lines.append(f"- 📌 {tip}")
                lines.append("")

        if qr_path:
            lines.append("---")
            lines.append(f"![腾讯地图小程序入口图]({qr_path})")
            lines.append("")
            lines.append("👆 扫码进入腾讯地图小程序，可联动小程序继续完善攻略、与朋友共同编辑行程、规划多人出行。")

        return "\n".join(lines)

    def poi_search(
        self,
        keyword: str,
        region: Optional[str] = None,
        location: Optional[str] = None,
        page_size: int = 10,
        page_index: int = 1,
    ) -> Dict[str, Any]:
        """POI 关键词搜索（按城市或中心点）。

        :param keyword: 搜索词，必填
        :param region: 城市/区域，例如 "深圳" / "武汉"
        :param location: 中心点 "lat,lng"，与 region 二选一
        :param page_size: 每页 1-20，默认 10
        :param page_index: 页码，默认 1
        :return: 官方原生响应 {status, message, count, data: [...POI]}
        """
        if not region and not location:
            raise ValueError("region 和 location 至少传一个")

        boundary = f"region({region})" if region else f"nearby({location},5000)"
        params = {
            "keyword": keyword,
            "boundary": boundary,
            "page_size": min(page_size, 20),
            "page_index": page_index,
        }
        params.update(self._rich_params())
        return self._ws_get("/ws/place/v1/search", params)

    def poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """根据 POI ID 取详情。

        :param poi_id: POI 唯一 ID（来自 poi_search/poi_sug 返回，或 A2A 攻略里的 poi_uid）
        :return: 官方原生响应 {status, message, data: [...POI 详情]}
        """
        return self._ws_get("/ws/place/v1/detail", {"id": poi_id})

    def poi_nearby(
        self,
        keyword: str,
        location: str,
        radius: int = 1000,
        page_size: int = 10,
        page_index: int = 1,
    ) -> Dict[str, Any]:
        """周边搜索（圆形范围）。

        :param keyword: 搜索词，必填，例如 "咖啡" / "加油站"
        :param location: 中心点 "lat,lng"，必填
        :param radius: 半径，米，取值 10-1000（官方上限 1000）
        :param page_size: 每页 1-20，默认 10
        :param page_index: 页码，默认 1
        :return: 官方原生响应 {status, message, count, data: [...POI]}
        """
        radius = max(10, min(int(radius), 1000))
        params = {
            "keyword": keyword,
            "boundary": f"nearby({location},{radius},1)",
            "page_size": min(page_size, 20),
            "page_index": page_index,
        }
        params.update(self._rich_params())
        return self._ws_get("/ws/place/v1/search", params)


    def direction(
        self,
        from_addr: str,
        to_addr: str,
        mode: str = "driving",
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """路线规划。先把起终点地址/景点名转坐标，再调腾讯路线接口。

        :param from_addr: 起点地址 / POI 名 / "lat,lng"
        :param to_addr: 终点地址 / POI 名 / "lat,lng"
        :param mode: driving / transit / walking / bicycling，默认 driving
        :param region: 城市名，辅助把"象鼻山"这类景点名解析到正确城市
        :return: 腾讯路线规划接口的原生响应（status / message / result，方案在 result.routes）
        """
        if mode not in ("driving", "transit", "walking", "bicycling"):
            raise ValueError(f"mode 必须是 driving/transit/walking/bicycling, got {mode}")

        f_loc = self._resolve_location(from_addr, region=region)
        t_loc = self._resolve_location(to_addr, region=region)
        return self._ws_get(f"/ws/direction/v1/{mode}", {
            "from": f"{f_loc['lat']},{f_loc['lng']}",
            "to": f"{t_loc['lat']},{t_loc['lng']}",
        })

    # ------------------------------------------------------------
    # 数据型原子能力（无跳转）
    # ------------------------------------------------------------

    def geocoder(self, address: str, policy: int = 1) -> Dict[str, Any]:
        """地址 / 地标名 / POI 名 → 坐标。

        :param address: 地址或地点名。可含城市更准；不含城市时靠 policy=1 兜底。
        :param policy: 解析策略。0=标准（地址须含城市，否则报 348）；
                       1=宽松（默认，允许无城市，支持景点/地标/POI 名，如"象鼻山"）。
        :return: 官方原生响应 {status, message, result: {location, address_components, ...}}
        """
        return self._ws_get("/ws/geocoder/v1", {
            "address": address,
            "policy": policy,
        })

    def regeocoder(self, lat: float, lng: float, get_poi: bool = False) -> Dict[str, Any]:
        """坐标 → 地址（可选返周边 POI）。

        :return: 官方原生响应 {status, message, result: {address, address_component, ...}}
        """
        return self._ws_get("/ws/geocoder/v1", {
            "location": f"{lat},{lng}",
            "get_poi": 1 if get_poi else 0,
        })

    def poi_sug(self, keyword: str, region: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        """关键词输入补全。

        :return: 官方原生响应 {status, message, count, data: [...候选 POI]}
        """
        params = {
            "keyword": keyword,
            "region": region,
            "location": location,
        }
        params.update(self._rich_params())
        return self._ws_get("/ws/place/v1/suggestion", params)

    def ip_location(self, ip: Optional[str] = None) -> Dict[str, Any]:
        """IP 定位（不传则定位调用方 IP）。

        :return: 官方原生响应 {status, message, result: {ip, location, ad_info}}
        """
        params = {}
        if ip:
            params["ip"] = ip
        return self._ws_get("/ws/location/v1/ip", params)

    def district_list(self) -> Dict[str, Any]:
        """全国行政区划列表（省级）。

        :return: 官方原生响应 {status, message, result: [...]}
        """
        return self._ws_get("/ws/district/v1/list", {})

    def district_children(self, parent_id: str) -> Dict[str, Any]:
        """根据父级 ID 获取下级行政区划。

        :return: 官方原生响应 {status, message, result: [...]}
        """
        return self._ws_get("/ws/district/v1/getchildren", {"id": parent_id})

    def district_search(self, keyword: str) -> Dict[str, Any]:
        """关键词搜索行政区划。

        :return: 官方原生响应 {status, message, result: [...]}
        """
        return self._ws_get("/ws/district/v1/search", {"keyword": keyword})

    def distance_matrix(
        self,
        from_list: List[str],
        to_list: List[str],
        mode: str = "driving",
    ) -> Dict[str, Any]:
        """距离矩阵（多对多）。

        :param from_list: 起点列表 ["lat,lng", ...]
        :param to_list: 终点列表 ["lat,lng", ...]
        :param mode: driving/walking/bicycling
        :return: 官方原生响应 {status, message, result: {rows: [...]}}
        """
        return self._ws_get("/ws/distance/v1/matrix", {
            "mode": mode,
            "from": ";".join(from_list),
            "to": ";".join(to_list),
        })

    def weather(self, adcode: Optional[str] = None, location: Optional[str] = None,
                type: str = "now") -> Dict[str, Any]:
        """天气查询。adcode 与 location 二选一。

        :param adcode: 行政区划代码，如北京 "110000"
        :param location: 坐标 "lat,lng"
        :param type: "now" 实时天气 / "future" 预报，默认 now
        :return: 官方原生响应 {status, message, result}
        """
        if not adcode and not location:
            raise ValueError("adcode 和 location 至少传一个")
        params: Dict[str, Any] = {"type": type}
        if adcode:
            params["adcode"] = adcode
        if location:
            params["location"] = location
        return self._ws_get("/ws/weather/v1", params)

    # ------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------

    def _resolve_location(self, addr: str, region: Optional[str] = None) -> Dict[str, float]:
        """地址 / POI 名 / 'lat,lng' → {lat, lng}

        优先级：① 已是坐标直接用 → ② geocoder 结构化地址解析
        → ③ 回退 poi_sug/poi_search（景点名、店名等非标准地址走这条）。
        """
        # ① 已经是 "lat,lng"
        addr_clean = addr.strip()
        if "," in addr_clean:
            parts = addr_clean.split(",")
            if len(parts) == 2:
                try:
                    lat = float(parts[0].strip())
                    lng = float(parts[1].strip())
                    return {"lat": lat, "lng": lng}
                except (ValueError, TypeError):
                    pass
        # ② 地址/地点名解析（geocoder 默认 policy=1，支持景点名）
        #    有 region 时拼到地址前，消除同名歧义（如"象鼻山"→"桂林象鼻山"）
        addr_for_geo = addr_clean
        if region and not addr_clean.startswith(region) and region not in addr_clean:
            addr_for_geo = f"{region}{addr_clean}"
        try:
            geo = self.geocoder(addr_for_geo)
            loc = (geo.get("result") or {}).get("location", {})
            if loc.get("lat") is not None and loc.get("lng") is not None:
                return {"lat": loc["lat"], "lng": loc["lng"]}
        except TmapError:
            pass  # 极少数解析不了的，转 POI 搜索兜底
        # ③ POI 搜索兜底：sug 优先（更宽容），再 search
        for finder in (
            lambda: self.poi_sug(addr, region=region).get("data", []),
            lambda: self.poi_search(addr, region=region, page_size=1).get("data", []),
        ):
            try:
                pois = finder()
            except Exception:
                pois = []
            if pois:
                loc = pois[0].get("location") or {}
                if isinstance(loc, str) and "," in loc:  # sug 的 location 可能是字符串
                    try:
                        lat, lng = [float(x) for x in loc.split(",")]
                        return {"lat": lat, "lng": lng}
                    except Exception:
                        pass
                if loc.get("lat") is not None and loc.get("lng") is not None:
                    return {"lat": loc["lat"], "lng": loc["lng"]}
        raise TmapError(348, f"无法解析地址/地点：{addr}（请补充城市或换更具体的名称）", "/_resolve_location", {})


# ============================================================
# 异常 & 工具
# ============================================================

class TmapError(Exception):
    def __init__(self, code: Any, message: str, api: str, raw: Any):
        self.code = code
        self.message = message
        self.api = api
        self.raw = raw
        super().__init__(f"[{api}] code={code} msg={message}")


def uuid_hex(n: int = 16) -> str:
    return "".join(random.choices("0123456789abcdef", k=n))


# ============================================================
# CLI（开发自测用）
# ============================================================

if __name__ == "__main__":
    import sys
    c = TmapClient()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "geocoder"
    if cmd == "geocoder":
        print(json.dumps(c.geocoder("深圳市腾讯滨海大厦"), ensure_ascii=False, indent=2))
    elif cmd == "regeocoder":
        print(json.dumps(c.regeocoder(22.540601, 113.93397, get_poi=True), ensure_ascii=False, indent=2))
    elif cmd == "poi_search":
        print(json.dumps(c.poi_search("黄鹤楼", region="武汉"), ensure_ascii=False, indent=2))
    elif cmd == "poi_detail":
        print(json.dumps(c.poi_detail("7025968886543661739"), ensure_ascii=False, indent=2))
    elif cmd == "poi_nearby":
        print(json.dumps(c.poi_nearby("咖啡", location="22.540601,113.93397", radius=1000), ensure_ascii=False, indent=2))
    elif cmd == "poi_sug":
        print(json.dumps(c.poi_sug("黄鹤楼", region="武汉"), ensure_ascii=False, indent=2))
    elif cmd == "ip":
        print(json.dumps(c.ip_location(), ensure_ascii=False, indent=2))
    elif cmd == "district_list":
        print(json.dumps(c.district_list(), ensure_ascii=False, indent=2))
    elif cmd == "direction":
        print(json.dumps(c.direction("深圳北站", "深圳湾口岸", "driving"), ensure_ascii=False, indent=2))
    elif cmd == "travel_guide":
        print(json.dumps(c.travel_guide(sys.argv[2] if len(sys.argv) > 2 else "武汉5天精华游"), ensure_ascii=False, indent=2))
    else:
        print(f"unknown cmd: {cmd}")
