#!/usr/bin/env python3
"""批量生图「提交计划」生成器（WorkRally MCP 版）。

本脚本**不发起任何网络请求**——它只把你要批量生成的清单整理成 JSONL，
再由 Agent 按清单逐条调用 MCP 工具 `canvas_generate_image` 提交。

为什么不让脚本自己提交？
    MCP 工具只能由 Agent 侧发起，本地脚本无法直接调用 MCP。
    因此把「定义清单」和「执行提交」分开：脚本负责前者（可复现、可 review），
    Agent 负责后者（走 MCP，无需 workrally CLI 与 API Key）。

用法：
    python3 make_batch_plan.py > /tmp/workrally/batch_plan.jsonl

输出每行一条：
    {"name": "CAT01_FMCG_TVC", "prompt": "..."}

提交时按行调用：
    canvas_generate_image(
        prompt="<prompt>", model="<model_id>", aspect_ratio="16:9",
        resolution=<来自 canvas_image_model_list 的 resolution_options[].value>,
        count=1, task_name="<name>", short_series_project_id="<短番项目ID>")
把返回的 task_ids[0] 记到 ledger（name -> task_id），供后续 canvas_get_task 与补漏使用。

节奏：小批提交（每批 ≤ 4 个，批间隔 12 秒），不要一次并发轰炸。
"""
import json
import sys

ASPECT = "16:9"

BASE_TAIL = (
    "anamorphic 2.39:1 framing, ARRI Alexa 65 large-format, micro film grain, "
    "brutalist industrial cinema aesthetic, 8K hyperreal, deep cinematic color grade, "
    "no text, no logo"
)

# === 在这里定义你的批量清单： (name, prompt) ===
PLAN = [
    # --- CAT 01 FMCG ---
    ("CAT01_FMCG_TVC", "Cinematic FMCG TVC commercial still. Slow-motion milk splash crowning a crystal glass on dark slate, soft north window light"),
    ("CAT01_FMCG_CG", "Cinematic FMCG CG render. Exploded view of a glossy dairy carton with droplets and graphical particles flowing, neutral cyclorama studio"),
    ("CAT01_FMCG_KV", "Cinematic FMCG key visual poster. Stack of premium dairy products on a stone pedestal, single rim light from screen-left, deep bone and honey palette"),
    ("CAT01_FMCG_PHOTO", "Cinematic FMCG e-commerce product photography. Single milk bottle on a clean cream gradient backdrop, soft beauty dish key, ultra-sharp label texture"),

    # --- CAT 02 AUTO ---
    ("CAT02_AUTO_TVC", "Cinematic automotive TVC still. Sleek matte-graphite electric SUV at high speed on a coastal mountain highway at dusk, motion blur, low tracking angle, deep cobalt twilight"),
    ("CAT02_AUTO_CG", "Cinematic automotive CG render. Floating exploded-view of an electric vehicle chassis revealing battery pack and motors, glowing wireframe overlays, dark studio void"),
    ("CAT02_AUTO_KV", "Cinematic automotive key visual poster. Three-quarter front portrait of a flagship EV in a foggy concrete tunnel, dramatic single beam light"),
    ("CAT02_AUTO_PHOTO", "Cinematic automotive product photography. Macro shot of carbon-fiber alloy wheel and brake caliper, polished concrete floor, controlled studio fill"),

    # --- CAT 03 BEAUTY ---
    ("CAT03_BEAUTY_TVC", "Cinematic beauty TVC still. Glistening serum droplet falling onto translucent silk surface, beauty dish key, ultra-shallow DOF, pearl white and rose-gold split tone"),
    ("CAT03_BEAUTY_CG", "Cinematic beauty CG. Liquid serum streams swirling around a frosted glass bottle in a void, particle bokeh, neutral pearl backdrop"),
    ("CAT03_BEAUTY_KV", "Cinematic beauty key visual poster. Symmetrical hero shot of a luxe lipstick on a marble pedestal, soft golden hour rim light"),
    ("CAT03_BEAUTY_PHOTO", "Cinematic beauty e-commerce product photography. Single skincare bottle on a soft beige paper backdrop, even diffuse light, ultra-sharp label"),

    # --- CAT 04 3C ---
    ("CAT04_3C_TVC", "Cinematic 3C tech TVC still. Floating smartphone with holographic UI streams erupting from screen in a glass void, deep teal grade"),
    ("CAT04_3C_CG", "Cinematic 3C CG render. Exploded view of a smartphone showing internal components rotating in glass space, wireframe accents"),
    ("CAT04_3C_KV", "Cinematic 3C key visual poster. Hero shot of a flagship laptop floating against deep gradient backdrop, single hard rim"),
    ("CAT04_3C_PHOTO", "Cinematic 3C product photography. Macro on the camera module of a premium smartphone, brushed aluminum reflections, dark gradient backdrop"),

    # --- CAT 05 FINANCE ---
    ("CAT05_FINANCE_TVC", "Cinematic finance TVC still. Modernist glass tower lobby with faceless executives walking past, low-angle architectural framing, slate-blue and bronze accents"),
    ("CAT05_FINANCE_CG", "Cinematic finance CG infographic. Abstract data architecture of glowing nodes and bars over a dark cityscape, holographic overlays"),
    ("CAT05_FINANCE_KV", "Cinematic finance key visual poster. Black-tie professional standing before a wall of glowing world clocks, slate and warm bronze grade"),
    ("CAT05_FINANCE_PHOTO", "Cinematic finance editorial photography. Hands signing a leather portfolio on a dark marble desk, soft window light"),

    # --- CAT 06 GAMES ---
    ("CAT06_GAMES_TVC", "Cinematic AAA game TVC trailer still. Heroic warrior in dark ornate armor on cliffside under stormy skies, dramatic god rays, Unreal Engine 5 photorealism"),
    ("CAT06_GAMES_CG", "Cinematic AAA game CG. Dragon swooping over a ruined gothic city, embers and smoke, Unreal Engine 5 photoreal, deep teal and ember orange grade"),
    ("CAT06_GAMES_KV", "Cinematic AAA game key visual poster. Heroic ensemble silhouette against a colossal moon, dust and embers"),
    ("CAT06_GAMES_PHOTO", "Cinematic game collector edition product photography. Premium boxed game with metal coin and art book on a slate surface, dramatic side light"),
]


def main() -> None:
    for name, prompt in PLAN:
        full = f"{prompt}, {BASE_TAIL}"
        print(json.dumps({"name": name, "prompt": full, "aspect_ratio": ASPECT},
                         ensure_ascii=False))
    print(f"# 共 {len(PLAN)} 条，已输出为 JSONL。", file=sys.stderr)
    print(f"# 提交节奏：小批 ≤4 个 / 批，批间隔 12 秒。", file=sys.stderr)


if __name__ == "__main__":
    main()
