#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fundus_ai.py - 腾讯觅影眼底多病种AI API 命令行客户端

真正调用眼底 AI 接口的可执行工具，供「眼底彩照疾病分析专家」使用。
仅依赖 Python 标准库，无需安装第三方包。

==============================================================================
凭证与权限（重要）
==============================================================================
普角与超广角是两套【相互独立、权限互斥】的凭证。同一个 appId/token 只拥有
"普角"或"超广角"其中一种权限，调用时必须按图像类型选对凭证：

  ┌────────┬─────────┬──────────────────────────────────┬──────────────┐
  │ 类型   │ appId   │ token                            │ 对应 aiType  │
  ├────────┼─────────┼──────────────────────────────────┼──────────────┤
  │ 普角   │ 12708   │ 69842f96c5b14c0ca8042fc309f3f087 │ 0 / 1 / 2    │
  │ 超广角 │ 12719   │ 7b131f5c5a3e4af080fb9e70382244ba │ 12           │
  └────────┴─────────┴──────────────────────────────────┴──────────────┘

  * hospitalId == appId（普角=12708，超广角=12719）
  * 本工具已内置以上两套凭证：只要指定 --ai-type，即自动选对 appId/token/hospitalId，
    无需手动传凭证，安装即用。
  * 如需覆盖（换成自己的正式凭证），用 --token/--app-id 或环境变量
    FUNDUS_TOKEN / FUNDUS_APPID，将优先于内置凭证。

鉴权算法：signature = HMAC-SHA256(key=token, message=appId + timestamp<毫秒>)

==============================================================================
用法示例
==============================================================================
  # 超广角一站式（自动选超广角凭证）——小图默认走 Base64 studyupload/v2
  python3 fundus_ai.py run --file img.jpg --ai-type 12 \
      --study-id study_xxx --desc-position 1 --camera-type 1 --env prod --out r.json

  # 普角一站式（自动选普角凭证，aiType=0 青光眼+多病种）
  python3 fundus_ai.py run --file img.jpg --ai-type 0 \
      --study-id study_xxx --desc-position 0 --env prod --out r.json

  # 仅查询已有检查
  python3 fundus_ai.py query --ai-type 12 --study-id study_xxx --env prod --poll

  # 离线解析已有返回 JSON（无需联网）
  python3 fundus_ai.py decode --result-json r.json
"""

import argparse
import base64
import gzip
import hashlib
import hmac
import io
import json
import os
import sys
import time
import uuid
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# 内置凭证（普角/超广角权限互斥，按 aiType 自动路由）
# ---------------------------------------------------------------------------
# 说明：同一 appId/token 只有普角或超广角之一的权限，不能混用。
CREDENTIALS = {
    "normal": {   # 普角（标准 45°），aiType 0/1/2
        "app_id": "12708",
        "token": "69842f96c5b14c0ca8042fc309f3f087",
    },
    "ultrawide": {  # 超广角，aiType 12
        "app_id": "12719",
        "token": "7b131f5c5a3e4af080fb9e70382244ba",
    },
}


def kind_of_ai_type(ai_type: int) -> str:
    """按 aiType 判定属于普角还是超广角凭证。"""
    return "ultrawide" if ai_type == 12 else "normal"


# ---------------------------------------------------------------------------
# 常量映射表（源自 API 文档 2026V1 + 官方 skill 参考）
# ---------------------------------------------------------------------------

# 47 维体征分类（超广角 leftDetail/rightDetail.others 索引 -> 中文名）
SIGN_47 = [
    "屈光介质混浊", "玻璃体出血", "玻璃体星状小体", "玻璃体后脱离",
    "其他玻璃体异常（药物棒/气体/硅油）", "玻璃膜疣", "黄斑视网膜下纤维膜（黄斑盘变）",
    "黄斑近视性萎缩斑", "黄斑地图样萎缩", "黄斑前膜", "黄斑出血", "黄斑视网膜下出血",
    "黄斑区浆液性视网膜脱离", "黄斑裂孔", "其他黄斑病变", "视盘侧枝循环", "视盘边界不清",
    "先天性视盘发育异常", "视盘大视杯（杯盘比≥0.3）", "视神经萎缩", "视盘新生血管",
    "高度近视视盘萎缩弧", "高度近视视盘萎缩环", "视网膜脱离", "视网膜出血象限性",
    "视网膜下出血", "视网膜前出血", "视网膜裂孔", "视网膜纤维膜", "视网膜脉络膜占位（肿物）",
    "视网膜光凝斑", "全视网膜光凝", "单象限性视网膜光凝斑", "视网膜骨细胞样色素改变",
    "豹纹状眼底", "晚霞状眼底", "出血点、出血斑", "硬性渗出", "棉绒斑", "视网膜新生血管",
    "视网膜陈旧色素病灶", "视网膜周边变性区", "其他视网膜病变", "视网膜动脉阻塞",
    "视网膜血管白线", "视网膜动脉硬化", "视网膜血管鞘-视网膜血管炎",
]

# 普角 description（形态学指标）字段中文名 + 是否为比率
MD_DESCRIPTION_LABELS = {
    "ratiosCD": ("杯盘比 C/D", True),
    "ratiosIN": ("盘沿比 I/N", True),
    "ratiosSN": ("盘沿比 S/N", True),
    "ratiosTN": ("盘沿比 T/N", True),
    "microaneurysms": ("微动脉瘤", False),
    "bleeding": ("出血斑", False),
    "hardExudation": ("硬性渗出", False),
    "softExudation": ("软性渗出", False),
    "proliferation": ("增殖膜", False),
    "vitreous": ("玻璃体积血", False),
    "wart": ("玻璃膜疣", False),
}

# 普角 result（多病种诊断结论）字段中文名
MD_RESULT_LABELS = {
    "noAbnormality": "未见明显异常",
    "diabetic": "糖尿病性视网膜病变(DR)",
    "AMD": "年龄相关性黄斑变性(AMD)",
    "block": "视网膜静脉阻塞",
    "turbid": "屈光间质混浊",
    "hypertensive": "高血压眼底病变",
    "tessellatedFundus": "豹纹状眼底",
    "pathologicalMyopia": "高度近视眼底改变",
    "other": "其他眼底疾病",
}

# 图片状态码
STATUS_MAP = {
    200: "处理成功", 0: "处理中", -1: "待处理", -2: "处理失败",
    -3: "屈光间质混浊", -4: "图片不合格", 404: "未找到图片",
}

# 接口错误码
CODE_MAP = {
    0: "请求成功", 1: "参数错误", 2: "数据库开小差", 10003: "未找到数据",
    30008: "检查处理中（继续轮询）", 90001: "无效token", 90002: "无效签名",
    90003: "超出最大获取次数",
}

# gzip+base64 压缩的检测字段
DETECTION_FIELDS = [
    "highMyopiaOpticDisc", "macularEpiretinalMembrane", "retinalFibrousMembrane",
    "retinalHole", "retinalDetachment", "retinalOldPigmentLesion",
]
# 分割字段（仅欧宝设备）
MASK_FIELDS = ["hemohedgeMask", "cottonWoolSpotMask", "hardExudateMask", "neovascularizationMask"]

HOSTS = {
    "prod": "https://pacs.qq.com",
    "test": "https://test.pacs.qq.com",
}


# ---------------------------------------------------------------------------
# 鉴权
# ---------------------------------------------------------------------------

def make_signature(token: str, app_id: str, timestamp: str) -> str:
    """signature = HMAC-SHA256(token, appId + timestamp)"""
    msg = (app_id + timestamp).encode("utf-8")
    key = token.encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def resolve_credentials(args):
    """
    解析本次调用使用的 token/app_id/hospital_id。
    优先级：命令行/环境变量 > 按 aiType 自动路由的内置凭证。
    hospitalId 默认 = appId（可用 --hospital-id 覆盖）。
    """
    override_token = args.token or os.environ.get("FUNDUS_TOKEN")
    override_appid = args.app_id or os.environ.get("FUNDUS_APPID")

    if override_token and override_appid:
        token, app_id = override_token, override_appid
    else:
        ai_type = getattr(args, "ai_type", None)
        if ai_type is None:
            sys.exit("❌ 无法确定凭证：请指定 --ai-type（自动选内置凭证），或同时提供 --token 与 --app-id")
        cred = CREDENTIALS[kind_of_ai_type(ai_type)]
        app_id = override_appid or cred["app_id"]
        token = override_token or cred["token"]

    hospital_id = getattr(args, "hospital_id", None) or app_id
    return token, app_id, hospital_id


def auth_headers(token: str, app_id: str, extra=None):
    ts = str(int(time.time() * 1000))  # 毫秒
    sig = make_signature(token, app_id, ts)
    headers = {"signature": sig, "appId": app_id, "timestamp": ts}
    if extra:
        headers.update(extra)
    return headers


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def http_post_json(url, headers, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    headers = dict(headers)
    headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"code": -999, "message": f"HTTP {e.code}: {body}", "requestId": ""}
    except Exception as e:
        return {"code": -998, "message": f"请求异常: {e}", "requestId": ""}


def http_post_multipart(url, headers, fields, file_field, file_path, timeout=120):
    """form-data 上传单张大图（纯标准库实现 multipart），用于超大文件（>5MB）。"""
    boundary = "----FundusBoundary" + uuid.uuid4().hex
    body = io.BytesIO()

    def w(s):
        body.write(s.encode("utf-8") if isinstance(s, str) else s)

    for k, v in fields.items():
        w(f"--{boundary}\r\n")
        w(f'Content-Disposition: form-data; name="{k}"\r\n\r\n')
        w(f"{v}\r\n")

    fname = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    w(f"--{boundary}\r\n")
    w(f'Content-Disposition: form-data; name="{file_field}"; filename="{fname}"\r\n')
    w("Content-Type: application/octet-stream\r\n\r\n")
    w(file_bytes)
    w("\r\n")
    w(f"--{boundary}--\r\n")

    headers = dict(headers)
    headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    req = urllib.request.Request(url, data=body.getvalue(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        b = e.read().decode("utf-8", errors="replace")
        return {"code": -999, "message": f"HTTP {e.code}: {b}", "requestId": ""}
    except Exception as e:
        return {"code": -998, "message": f"请求异常: {e}", "requestId": ""}


# ---------------------------------------------------------------------------
# 解码 & 解析
# ---------------------------------------------------------------------------

def decode_gzip_b64(s: str):
    """解码 gzip+base64 压缩的检测结果 JSON。空串返回 None。"""
    if not s:
        return None
    try:
        raw = base64.b64decode(s)
        decompressed = gzip.decompress(raw)
        return json.loads(decompressed.decode("utf-8"))
    except Exception as e:
        return {"_decode_error": str(e)}


def parse_eye_detail(detail: dict, eye_name: str):
    """解析单眼 detail：47维体征 + 分割 + 检测（超广角）"""
    out = {"eye": eye_name, "signs_positive": [], "signs_na": [], "detections": {}, "masks": {}}
    others = detail.get("others") or []
    for i, v in enumerate(others):
        if i >= len(SIGN_47):
            break
        if v == 1:
            out["signs_positive"].append({"index": i, "name": SIGN_47[i]})
        elif v == -1:
            out["signs_na"].append({"index": i, "name": SIGN_47[i]})
    for field in DETECTION_FIELDS:
        if detail.get(field):
            out["detections"][field] = decode_gzip_b64(detail[field])
    for field in MASK_FIELDS:
        if detail.get(field):
            out["masks"][field] = "有分割数据（欧宝设备）"
    return out


def parse_ultrawide(uw: dict):
    """解析超广角结果"""
    result = {
        "status": uw.get("status"),
        "status_desc": STATUS_MAP.get(uw.get("status"), "未知"),
        "eyeScreening": uw.get("eyeScreening", {}),
        "inferredDiagnoses": [],
        "leftDetail": None,
        "rightDetail": None,
    }
    for d in uw.get("inferredDiagnoses") or []:
        left = d.get("leftValue") == "1"
        right = d.get("rightValue") == "1"
        if left or right:
            result["inferredDiagnoses"].append({
                "name": d.get("name"),
                "disease": d.get("disease"),
                "left": "疑似" if left else "未见",
                "right": "疑似" if right else "未见",
            })
    if uw.get("leftDetail"):
        result["leftDetail"] = parse_eye_detail(uw["leftDetail"], "左眼")
    if uw.get("rightDetail"):
        result["rightDetail"] = parse_eye_detail(uw["rightDetail"], "右眼")
    return result


def _eye_name(eye_category):
    return "左眼" if eye_category == 0 else ("右眼" if eye_category == 1 else "未知眼别")


def parse_glaucoma(g: dict):
    """解析单条青光眼结果（普角）"""
    return {
        "eye": _eye_name(g.get("eyeCategory")),
        "eyeCategory": g.get("eyeCategory"),
        "status": g.get("status"),
        "status_desc": STATUS_MAP.get(g.get("status"), "未知"),
        "aiResult": g.get("aiResult"),
    }


def parse_multiple_diseases(m: dict):
    """解析单条多病种结果（普角），把 description/result 映射成带中文标签的结构。"""
    desc_raw = m.get("description") or {}
    result_raw = m.get("result") or {}

    morphology = {}
    for key, (label, is_ratio) in MD_DESCRIPTION_LABELS.items():
        if key not in desc_raw:
            continue
        val = desc_raw[key]
        morphology[key] = {"label": label, "value": val, "is_ratio": is_ratio}

    diagnoses = {}
    for key, label in MD_RESULT_LABELS.items():
        if key not in result_raw:
            continue
        diagnoses[key] = {"label": label, "value": result_raw[key]}

    # 汇总阳性发现（有异常的项）
    positives = []
    for key, item in diagnoses.items():
        v = str(item["value"]).strip()
        if key == "noAbnormality":
            continue
        if key == "diabetic":
            if v and v not in ("未见异常", "未知", ""):
                positives.append(f"{item['label']}：{v}")
        elif v in ("有",):
            positives.append(item["label"])

    return {
        "eye": _eye_name(m.get("eyeCategory")),
        "eyeCategory": m.get("eyeCategory"),
        "status": m.get("status"),
        "status_desc": STATUS_MAP.get(m.get("status"), "未知"),
        "morphology": morphology,
        "diagnoses": diagnoses,
        "positives": positives,
    }


def parse_result(data: dict):
    """解析完整 AIResult（普角 + 超广角通用）"""
    parsed = {}
    if data.get("ultraWideResult"):
        parsed["ultraWide"] = parse_ultrawide(data["ultraWideResult"])
    if data.get("glaucomaResultList"):
        parsed["glaucoma"] = [parse_glaucoma(g) for g in data["glaucomaResultList"] if g]
    if data.get("multipleDiseasesResultList"):
        parsed["multipleDiseases"] = [
            parse_multiple_diseases(m) for m in data["multipleDiseasesResultList"] if m
        ]
    if data.get("reportUrl"):
        parsed["reportUrl"] = data["reportUrl"]
    return parsed


# ---------------------------------------------------------------------------
# 上传
# ---------------------------------------------------------------------------

def upload_base64(args, token, app_id):
    """
    Base64 JSON 上传 —— 官方推荐（studyupload/v2），适用于总大小 ≤5MB。
    单次可含多张图（本 CLI 传 1 张）。
    """
    host = HOSTS[args.env]
    url = f"{host}/thirdparty/studyupload/v2/{app_id}"
    with open(args.file, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("ascii")
    image = {
        "imageId": args.image_id or ("img_" + uuid.uuid4().hex[:8]),
        "content": content_b64,
        "descPosition": str(args.desc_position),
    }
    payload = {
        "studyId": args.study_id,
        "studyName": args.study_name,
        "studyDate": int(args.study_date or time.time()),  # 秒级
        "studyType": 2,
        "images": [image],
    }
    if args.patient_name:
        payload["patientName"] = args.patient_name
    if args.patient_id:
        payload["patientId"] = args.patient_id
    headers = auth_headers(token, app_id)
    return http_post_json(url, headers, payload)


def upload_file(args, token, app_id):
    """form-data 上传单张大图（fileImageUpload/v1），适用于 >5MB 的超大图。"""
    host = HOSTS[args.env]
    url = f"{host}/thirdparty/fileImageUpload/v1/{app_id}"
    headers = auth_headers(token, app_id)
    fields = {
        "studyId": args.study_id,
        "studyName": args.study_name,
        "studyDate": str(int(args.study_date or time.time())),
        "studyType": "2",
        "imageId": args.image_id or uuid.uuid4().hex[:12],
        "descPosition": str(args.desc_position),
        "cameraType": str(args.camera_type),
    }
    if args.patient_name:
        fields["patientName"] = args.patient_name
    if args.patient_id:
        fields["patientId"] = args.patient_id
    return http_post_multipart(url, headers, fields, "file", args.file)


def do_upload(args, token, app_id):
    """按图片大小自动选择上传方式：≤5MB 用 Base64（官方推荐），否则用 form-data。"""
    size_mb = os.path.getsize(args.file) / (1024 * 1024)
    force = getattr(args, "upload_mode", "auto")
    if force == "file" or (force == "auto" and size_mb > 5):
        print(f"📤 使用 form-data 上传（{size_mb:.2f}MB）", file=sys.stderr)
        return upload_file(args, token, app_id)
    print(f"📤 使用 Base64 studyupload/v2 上传（{size_mb:.2f}MB，官方推荐）", file=sys.stderr)
    return upload_base64(args, token, app_id)


# ---------------------------------------------------------------------------
# 命令实现
# ---------------------------------------------------------------------------

def cmd_upload(args):
    token, app_id, _ = resolve_credentials(args)
    resp = do_upload(args, token, app_id)
    print(json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


def _is_processing(data, ai_type):
    """判断 AI 是否仍在处理中（用于是否继续轮询）。"""
    if ai_type == 12:
        uw = data.get("ultraWideResult") or {}
        return uw.get("status") in (0, -1)
    # 普角：青光眼 + 多病种两个子模型可能速度不同，任一在处理中就继续轮询。
    # 注意 status=404 是"该眼别无图"，不算处理中。
    lst = (data.get("glaucomaResultList") or []) + (data.get("multipleDiseasesResultList") or [])
    real = [x for x in lst if x and x.get("status") != 404]
    if not real:
        return True  # 还没有任何有效条目，继续等
    return any(x.get("status") in (0, -1) for x in real)


def cmd_query(args):
    token, app_id, hospital_id = resolve_credentials(args)
    host = HOSTS[args.env]
    url = f"{host}/thirdparty/queryEyeAIResult/{app_id}"
    payload = {
        "hospitalId": hospital_id,
        "studyId": args.study_id,
        "aiType": args.ai_type,
        "needReport": args.need_report,
    }
    if getattr(args, "patient_id", None):
        payload["patientId"] = args.patient_id

    attempts = args.max_poll if args.poll else 1
    resp = None
    for i in range(attempts):
        headers = auth_headers(token, app_id)
        resp = http_post_json(url, headers, payload)
        code = resp.get("code")

        # 30008 = 处理中（官方定义），继续轮询
        if code == 30008:
            if not args.poll:
                return resp
            print(f"⏳ 30008 处理中，第 {i+1}/{attempts} 次轮询，{args.poll_interval}s 后重试...", file=sys.stderr)
            time.sleep(args.poll_interval)
            continue

        if code != 0:
            print(f"⚠️ 接口返回 code={code} ({CODE_MAP.get(code, '未知错误')}): {resp.get('message')}", file=sys.stderr)
            return resp

        # code==0：检查子模型是否都跑完
        data = resp.get("data") or {}
        still = _is_processing(data, args.ai_type)
        if not still or not args.poll:
            return resp
        print(f"⏳ 子模型处理中，第 {i+1}/{attempts} 次轮询，{args.poll_interval}s 后重试...", file=sys.stderr)
        time.sleep(args.poll_interval)
    return resp


def cmd_run(args):
    """一站式：上传 → 轮询 → 解析"""
    token, app_id, hospital_id = resolve_credentials(args)
    kind = "超广角" if args.ai_type == 12 else "普角"
    print(f"🔐 使用【{kind}】凭证 appId={app_id}（hospitalId={hospital_id}），env={args.env}", file=sys.stderr)

    print("📤 步骤1/3：上传图片...", file=sys.stderr)
    up = do_upload(args, token, app_id)
    if up.get("code") != 0:
        sys.exit(f"❌ 上传失败：code={up.get('code')} {up.get('message')}")
    print(f"✅ 上传成功 requestId={up.get('requestId')}", file=sys.stderr)

    print("🔍 步骤2/3：轮询查询 AI 结果...", file=sys.stderr)
    args.poll = True
    resp = cmd_query(args)
    if resp.get("code") != 0:
        sys.exit(f"❌ 查询失败：code={resp.get('code')} {resp.get('message')}")

    print("🧠 步骤3/3：解析结果...", file=sys.stderr)
    parsed = parse_result(resp.get("data") or {})
    output = {"raw": resp, "parsed": parsed}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"💾 已保存至 {args.out}", file=sys.stderr)
    return output


def cmd_decode(args):
    """离线解析已有的返回 JSON"""
    with open(args.result_json, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # 兼容三种结构：{code,data}、{raw:{...},parsed:{}}、直接就是 data
    if "raw" in raw and isinstance(raw["raw"], dict):
        data = raw["raw"].get("data") or {}
    elif "data" in raw:
        data = raw.get("data") or {}
    else:
        data = raw
    parsed = parse_result(data or {})
    print(json.dumps(parsed, ensure_ascii=False, indent=2))
    return parsed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description="腾讯觅影眼底多病种AI API 客户端（内置普角/超广角双凭证）")
    p.add_argument("--token", help="覆盖内置 token（或环境变量 FUNDUS_TOKEN）")
    p.add_argument("--app-id", help="覆盖内置 appId（或环境变量 FUNDUS_APPID）")
    p.add_argument("--env", choices=["prod", "test"], default=os.environ.get("FUNDUS_ENV", "prod"),
                   help="环境，默认 prod")
    sub = p.add_subparsers(dest="command", required=True)

    def add_upload_args(sp):
        sp.add_argument("--file", required=True, help="图片文件路径")
        sp.add_argument("--study-id", required=True, help="检查唯一标识（建议 study_ + uuid）")
        sp.add_argument("--study-name", default="眼底检查", help="检查名称，默认『眼底检查』")
        sp.add_argument("--study-date", type=int, help="检查日期 Unix 秒，默认当前")
        sp.add_argument("--image-id", help="图片ID，默认自动生成")
        sp.add_argument("--desc-position", type=int, default=0, choices=[0, 1, 2],
                        help="眼别 0未知 1左眼(OS) 2右眼(OD)")
        sp.add_argument("--camera-type", type=int, default=0, choices=[0, 1, 2],
                        help="相机 0自动 1欧宝 2蔡司（仅 form-data 上传使用）")
        sp.add_argument("--patient-name", help="患者姓名")
        sp.add_argument("--patient-id", help="患者编号")
        sp.add_argument("--upload-mode", choices=["auto", "base64", "file"], default="auto",
                        help="上传方式：auto=按大小自动(≤5M走base64)，base64=强制Base64，file=强制form-data")

    sp_up = sub.add_parser("upload", help="上传图片（≤5M自动走Base64）")
    add_upload_args(sp_up)
    sp_up.add_argument("--ai-type", type=int, choices=[0, 1, 2, 12],
                       help="用于自动选凭证：0/1/2普角 12超广角（上传时也建议指定）")

    sp_q = sub.add_parser("query", help="查询 AI 结果")
    sp_q.add_argument("--hospital-id", help="医疗机构标识，默认=appId")
    sp_q.add_argument("--study-id", required=True, help="检查唯一标识")
    sp_q.add_argument("--patient-id", help="患者标识")
    sp_q.add_argument("--ai-type", type=int, required=True, choices=[0, 1, 2, 12],
                      help="0青光眼+多病种 1青光眼 2多病种 12超广角")
    sp_q.add_argument("--need-report", type=int, default=1, choices=[0, 1], help="是否输出PDF报告")
    sp_q.add_argument("--poll", action="store_true", help="轮询直到完成")
    sp_q.add_argument("--max-poll", type=int, default=30, help="最大轮询次数（默认30）")
    sp_q.add_argument("--poll-interval", type=int, default=10, help="轮询间隔秒（默认10）")

    sp_run = sub.add_parser("run", help="一站式 上传+轮询+解析")
    add_upload_args(sp_run)
    sp_run.add_argument("--hospital-id", help="医疗机构标识，默认=appId")
    sp_run.add_argument("--ai-type", type=int, default=12, choices=[0, 1, 2, 12],
                        help="0青光眼+多病种 1青光眼 2多病种 12超广角(默认)")
    sp_run.add_argument("--need-report", type=int, default=1, choices=[0, 1])
    sp_run.add_argument("--max-poll", type=int, default=30, help="最大轮询次数（默认30=最长5分钟）")
    sp_run.add_argument("--poll-interval", type=int, default=10, help="轮询间隔秒（默认10）")
    sp_run.add_argument("--out", help="结果保存路径")

    sp_dec = sub.add_parser("decode", help="离线解析返回 JSON")
    sp_dec.add_argument("--result-json", required=True, help="包含 API 返回的 JSON 文件")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    handlers = {
        "upload": cmd_upload,
        "query": lambda a: print(json.dumps(cmd_query(a), ensure_ascii=False, indent=2)),
        "run": cmd_run,
        "decode": cmd_decode,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
