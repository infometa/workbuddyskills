# Copyright 2024-2026 Kaku Li (https://github.com/likaku)
# Licensed under the Apache License, Version 2.0 — see LICENSE and NOTICE.
# Part of "Mck-ppt-design-skill" (McKinsey PPT Design Framework).
# NOTICE: This file must be retained in all copies or substantial portions.
#
"""Cover Image Generator — 腾讯混元 API + rembg 抠图 + 冷灰蓝 + McKinsey 几何弧线.

输出: 1920×1080 RGBA PNG，主体抠图透明底，几何弧线铺满画面，用作 PPT 全幅垫底。

Usage:
    from mck_ppt.cover_image import generate_cover_image
    path = generate_cover_image('AI的能力边界', output_path='cover.png')
"""

from __future__ import annotations

import base64
import json
import math
import os
import tempfile
import time
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
from rembg import remove as rembg_remove

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models


# ── 主题 → 实物关键词 ─────────────────────────────────────────────────
_METAPHOR_MAP = {
    'AI': '一块高端三风扇游戏显卡，厚重散热装甲，RGB灯带，银黑配色，45度俯视角',
    '人工智能': '一块高端三风扇游戏显卡，厚重散热装甲，RGB灯带，银黑配色，45度俯视角',
    '随机': '三颗金属骰子，银色抛光，45度角摆放',
    '数据': '一块M.2固态硬盘，黑色PCB电路板，金手指',
    '安全': '一把现代智能门锁，银色金属面板，极简设计',
    '医疗': '一个银色听诊器和几颗彩色胶囊药丸',
    '医药': '一个银色听诊器和几颗彩色胶囊药丸',
    '金融': '一张银色金属质感芯片银行卡，45度角',
    '教育': '一台银色笔记本电脑半开合状态，侧面视角',
    '能源': '一块深蓝色太阳能电池板，俯视角',
    '建筑': '一个白色3D打印建筑模型，现代风格',
    '科技': '一块方形芯片封装，银色金属盖，俯视角',
    '创新': '一副白色VR头显设备，侧面视角',
    '战略': '一枚银色金属国际象棋国王棋子',
    '平台': '几块彩色乐高积木拼接在一起',
    '数字化': '一个智能手表，圆形表盘，银色表带',
    '芯片': '一块方形芯片封装，银色金属盖，俯视角',
    '大脑': '一个透明树脂人脑模型，底座支撑',
    '神经': '一个透明树脂人脑模型，底座支撑',
    '创造力': '几支彩色马克笔散落排列',
    '算法': '一个三阶魔方，白色为主色调',
    '计算': '一块高端三风扇游戏显卡，厚重散热装甲，银黑配色',
    '机器人': '一只白色机械臂关节特写',
    '云': '一台银色Mac Mini电脑，正面视角',
}

_PROMPT_TEMPLATE = (
    "真实产品摄影照片，{object_desc}，"
    "纯白色背景，轮廓清晰锐利，"
    "影棚灯光，超高清"
)


def _find_metaphor(title: str) -> str:
    for keyword, metaphor in _METAPHOR_MAP.items():
        if keyword in title:
            return metaphor
    return '一个银色金属几何雕塑'


def _build_prompt(title: str) -> str:
    return _PROMPT_TEMPLATE.format(object_desc=_find_metaphor(title))


# ═══════════════════════════════════════════════════════════════════════
# 后处理
# ═══════════════════════════════════════════════════════════════════════

def _professional_remove_bg(img: Image.Image) -> Image.Image:
    """rembg 专业抠图，只保留主体。"""
    return rembg_remove(img).convert('RGBA')


def _apply_cool_blue_tint(img: Image.Image) -> Image.Image:
    """冷灰蓝色调 + 调淡50%，只处理非透明像素。"""
    img = img.convert('RGBA')
    arr = np.array(img, dtype=np.float32)
    alpha = arr[:, :, 3]
    mask = alpha > 10

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    sat = 0.30
    r_new = (gray + (r - gray) * sat) * 0.85 * 0.5 + 255.0 * 0.5
    g_new = (gray + (g - gray) * sat) * 0.92 * 0.5 + 255.0 * 0.5
    b_new = np.minimum((gray + (b - gray) * sat) * 1.18, 255.0) * 0.5 + 255.0 * 0.5

    arr[:, :, 0][mask] = np.clip(r_new[mask], 0, 255)
    arr[:, :, 1][mask] = np.clip(g_new[mask], 0, 255)
    arr[:, :, 2][mask] = np.clip(b_new[mask], 0, 255)

    return Image.fromarray(arr.astype(np.uint8))


def _place_subject_right(subject: Image.Image, canvas_w: int, canvas_h: int) -> Image.Image:
    """将抠图主体放到画布右侧，参考McKinsey样本比例.

    主体约占画面高66%、宽42%，位于右侧偏中上。
    """
    canvas = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))

    bbox = subject.getbbox()
    if not bbox:
        return canvas
    cropped = subject.crop(bbox)
    cw, ch = cropped.size

    # 主体缩放到画布高度的 ~66%（原55% × 1.2 放大20%）
    target_h = int(canvas_h * 0.66)
    scale = target_h / ch
    target_w = int(cw * scale)
    # 宽度上限 42%（原35% × 1.2）
    if target_w > int(canvas_w * 0.42):
        target_w = int(canvas_w * 0.42)
        scale = target_w / cw
        target_h = int(ch * scale)

    resized = cropped.resize((target_w, target_h), Image.LANCZOS)

    # 原位置：右下角 x = canvas_w - target_w + 5%, y = canvas_h - target_h + 5%
    # 左移30%: x -= canvas_w * 0.30,  上移30%: y -= canvas_h * 0.30
    x = canvas_w - target_w + int(target_w * 0.05) - int(canvas_w * 0.10)
    y = canvas_h - target_h + int(target_h * 0.05) - int(canvas_h * 0.18)
    canvas.paste(resized, (x, y), resized)

    return canvas


def _draw_mck_curves(img: Image.Image) -> Image.Image:
    """McKinsey 风格弧线 — 丝带在中间折叠翻转效果.

    一束平行线从左下平行流入，到画面中心时像丝带被折叠翻转——
    上面的线交叉到下面、下面的交叉到上面，然后继续向右上发散。
    整体像一条被扭转了一下的丝绸缎带。
    """
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    w, h = img.size

    n_lines = 24
    for i in range(n_lines):
        # 每条线的归一化位置 [-1, 1]
        t = (i - (n_lines - 1) / 2.0) / ((n_lines - 1) / 2.0)

        center_dist = abs(t)
        alpha = int(105 * (1.0 - center_dist * 0.6))
        line_w = 2 if center_dist < 0.5 else 1
        color = (55, 105, 165, alpha)

        spread = t * h * 0.20  # 每条线的 y 偏移

        points = []
        n_seg = 300
        for s in range(n_seg + 1):
            frac = s / n_seg

            # 基础路径：左下 → 中心 → 右上
            p0x, p0y = w * 0.00, h * 1.05
            p1x, p1y = w * 0.30, h * 0.50
            p2x, p2y = w * 0.70, h * 0.50
            p3x, p3y = w * 1.00, h * -0.05

            u = 1 - frac
            bx = u**3*p0x + 3*u**2*frac*p1x + 3*u*frac**2*p2x + frac**3*p3x
            by = u**3*p0y + 3*u**2*frac*p1y + 3*u*frac**2*p2y + frac**3*p3y

            # 丝带折叠：中心处微微翻转，不是完全收紧
            # tanh 斜率降低 → 过渡更缓，折叠更柔和
            twist = math.tanh((frac - 0.50) * 5.0)  # 原来12.0太急，5.0更柔和

            offset_y = spread * twist

            # 折叠处线条略微靠近但不完全贴合
            # tightness 最小值从0.65提高到0.80 → 不会收太紧
            tightness = 1.0 - 0.20 * math.exp(-((frac - 0.50) ** 2) / (2 * 0.06 ** 2))
            offset_y *= tightness

            points.append((bx, by + offset_y))

        for j in range(len(points) - 1):
            draw.line([points[j], points[j + 1]], fill=color, width=line_w)

    return Image.alpha_composite(img, overlay)


def _post_process(image_path: str) -> str:
    """后处理流水线:
    1. rembg 专业抠图
    2. 冷灰蓝 + 调淡50%
    3. 放置到 1920×1080 画布右侧
    4. 全幅 McKinsey 几何弧线
    5. 保存 RGBA PNG
    """
    img = Image.open(image_path).convert('RGB')
    print(f"   API 原始尺寸: {img.size[0]}×{img.size[1]}")

    # 1. 抠图
    print("   🔪 rembg 抠图中 …")
    img = _professional_remove_bg(img)
    print("   ✅ 抠图完成")

    # 2. 冷灰蓝 + 调淡
    img = _apply_cool_blue_tint(img)

    # 3. 放到 1920×1080 画布，主体在右侧
    canvas = _place_subject_right(img, 1920, 1080)

    # 4. McKinsey 弧线铺满画面
    canvas = _draw_mck_curves(canvas)

    print(f"   输出尺寸: {canvas.size[0]}×{canvas.size[1]} (RGBA 透明底)")
    canvas.save(image_path, 'PNG')
    return image_path


# ═══════════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════════

def generate_cover_image(title: str, output_path: str | None = None) -> str:
    """根据标题调用腾讯混元2.0 API 生成封面图片.

    使用 SubmitHunyuanImageJob (混元2.0) 异步生成，质量更高。
    Returns: 1920×1080 RGBA PNG (透明底 + 冷灰蓝 + 几何弧线) 路径。
    """
    secret_id = os.environ.get('TENCENT_SECRET_ID')
    secret_key = os.environ.get('TENCENT_SECRET_KEY')
    if not secret_id or not secret_key:
        raise EnvironmentError(
            "请设置环境变量 TENCENT_SECRET_ID 和 TENCENT_SECRET_KEY"
        )

    prompt = _build_prompt(title)
    print(f"🎨 Generating cover image (混元2.0) …\n   Prompt: {prompt}")

    cred = credential.Credential(secret_id, secret_key)
    hp = HttpProfile()
    hp.endpoint = "hunyuan.tencentcloudapi.com"
    cp = ClientProfile()
    cp.httpProfile = hp
    client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou", cp)

    # ── Step 1: 提交异步生图任务 ──────────────────────────────
    req = models.SubmitHunyuanImageJobRequest()
    req.from_json_string(json.dumps({
        "Prompt": prompt,
        "NegativePrompt": "文字,水印,多个物体,杂乱,黑色背景,人物,动漫",
        "Resolution": "1024:1024",
        "LogoAdd": 0,
        "Num": 1,
        "Revise": 0,
    }))

    resp = client.SubmitHunyuanImageJob(req)
    job_id = resp.JobId
    print(f"   📋 Job submitted: {job_id}")

    # ── Step 2: 轮询等待任务完成 ──────────────────────────────
    max_wait = 120  # 最多等2分钟
    poll_interval = 3
    elapsed = 0
    result_urls = None

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        query_req = models.QueryHunyuanImageJobRequest()
        query_req.from_json_string(json.dumps({"JobId": job_id}))
        query_resp = client.QueryHunyuanImageJob(query_req)

        status = query_resp.JobStatusCode
        if status == "5":  # 处理完成
            result_urls = query_resp.ResultImage
            print(f"   ✅ Job completed ({elapsed}s)")
            break
        elif status == "4":  # 处理失败
            raise RuntimeError(f"混元2.0生图失败: {query_resp.JobStatusMsg}")
        else:
            print(f"   ⏳ Waiting… ({elapsed}s, status={status})")

    if not result_urls:
        raise RuntimeError(f"混元2.0生图超时 ({max_wait}s)")

    # ── Step 3: 下载图片 ──────────────────────────────────────
    img_url = result_urls[0]
    print(f"   📥 Downloading image…")

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='_cover.png', prefix='mck_')
        os.close(fd)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    urllib.request.urlretrieve(img_url, output_path)

    # ── Step 4: 后处理 ────────────────────────────────────────
    _post_process(output_path)

    print(f"✅ Cover image saved: {output_path} ({os.path.getsize(output_path):,} bytes)")
    return output_path