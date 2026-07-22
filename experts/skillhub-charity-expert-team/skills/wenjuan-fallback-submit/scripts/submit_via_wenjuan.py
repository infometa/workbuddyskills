#!/usr/bin/env python3
"""
submit_via_wenjuan.py — SkillHub 运维专家 · MCP Backup 通道自动提交脚本

用途：当 MCP（ssvSkillHub 连接器 / request_upload）提交失败 1 次后，
      自动打开腾讯问卷、上传 Meta/Material/Skill 三个 zip 字段并提交，
      作为过渡期兜底通道（详见 charity/skillhub.md 3.9 节设计）。

用法：
  python3 submit_via_wenjuan.py \
    --skill-zip <技能包.zip> \
    --material-zip <材料包.zip> \
    --meta-json <meta.json> \
    [--url https://wj.qq.com/s2/27257161/9f38/] \
    [--output-dir ~/.workbuddy/skillhub-outputs] \
    [--headless / --no-headless]

输出：JSON 单行打印到 stdout，供 Agent 直接解析：
  成功：{"status":"success","submitted_at":...,"screenshot":...,"meta_zip":...}
  需人工介入（如意外出现手机验证等）：{"status":"manual_required","reason":...,"screenshot":...}
  失败：{"status":"failed","error":...,"screenshot":...}

设计原则（对齐项目既有铁律）：
- 单次尝试，不在脚本内重试（U5：失败降级由调用方决定，不在此处无意义重试）
- 所有关键动作留存截图证据，便于运维专家/人工排查
- 提交前用**已存在的**材料/技能 zip，本脚本只负责把 meta.json 打包为 zip + 自动填表提交
  （不重新打包技能包/材料包，那是 pack_and_hash.sh 的职责）
"""

import argparse
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB —— 与问卷"单个文件大小不超过10MB"限制一致
SUCCESS_TEXT = "问卷到此结束"
SUBMIT_BUTTON_TEXT = "提交"
DEFAULT_URL = "https://wj.qq.com/s2/27257161/9f38/"
# 三个字段在问卷中的固定展示顺序：01 Meta -> 02 Material -> 03 Skill
FIELD_LABELS_IN_ORDER = ["Meta", "Material", "Skill"]
UPLOAD_TRIGGER_TEXT = "点击上传或拖拽文件至此处"


def log(msg: str) -> None:
    print(f"[submit_via_wenjuan] {msg}", file=sys.stderr, flush=True)


def zip_meta_json(meta_json_path: Path, output_dir: Path) -> Path:
    """把 meta.json 打包为 zip（不改变原始 json 内容），产物名固定为 meta.zip"""
    if not meta_json_path.is_file():
        raise FileNotFoundError(f"meta.json 不存在：{meta_json_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    meta_zip_path = output_dir / "meta.zip"
    with zipfile.ZipFile(meta_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(meta_json_path, arcname=meta_json_path.name)
    return meta_zip_path


def validate_file(path: Path, field_name: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{field_name} 文件不存在：{path}")
    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        raise ValueError(
            f"{field_name} 文件过大（{size / 1024 / 1024:.2f}MB），"
            f"超过问卷单文件 10MB 限制：{path}"
        )
    if size == 0:
        raise ValueError(f"{field_name} 文件为空：{path}")


def run_submission(
    skill_zip: Path,
    material_zip: Path,
    meta_zip: Path,
    url: str,
    output_dir: Path,
    headless: bool,
) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
    except ImportError:
        return {
            "status": "failed",
            "error": (
                "缺少 playwright 依赖，请先执行：\n"
                "  pip install playwright && python3 -m playwright install chromium\n"
                "（Windows 上 python3 命令可能不可用，改用 python -m playwright install chromium）\n"
                "安装完成后重新运行本脚本。"
            ),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    files_in_order = [meta_zip, material_zip, skill_zip]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="load", timeout=30000)

            # 腾讯问卷是前端 React 渲染的 SPA，`load` 事件早于题目渲染完成，
            # 必须显式等待第一个上传触发元素出现，不能只依赖 load/networkidle。
            try:
                page.get_by_text(UPLOAD_TRIGGER_TEXT).first.wait_for(state="visible", timeout=15000)
            except PWTimeoutError:
                shot = output_dir / f"wenjuan-render-timeout-{ts}.png"
                page.screenshot(path=str(shot), full_page=True)
                return {
                    "status": "failed",
                    "error": "等待问卷题目渲染超时（15s 内未出现上传字段），问卷可能加载失败或网络异常。",
                    "screenshot": str(shot),
                }

            # ── 校验字段数量与标签顺序是否与预期一致（防止问卷被改动导致误填）──
            triggers = page.get_by_text(UPLOAD_TRIGGER_TEXT)
            trigger_count = triggers.count()
            if trigger_count != len(FIELD_LABELS_IN_ORDER):
                shot = output_dir / f"wenjuan-mismatch-{ts}.png"
                page.screenshot(path=str(shot), full_page=True)
                return {
                    "status": "failed",
                    "error": (
                        f"问卷上传字段数量为 {trigger_count}，"
                        f"与预期的 {len(FIELD_LABELS_IN_ORDER)}（Meta/Material/Skill）不一致，"
                        "问卷可能已被修改，请人工核实字段结构后再处理。"
                    ),
                    "screenshot": str(shot),
                }

            headings_text = page.locator("h2, [role=heading]").all_inner_texts()
            for idx, label in enumerate(FIELD_LABELS_IN_ORDER):
                matched = any(label in h for h in headings_text)
                if not matched:
                    log(f"⚠️ 未在页面标题中找到字段「{label}」，仍按第 {idx+1} 个上传区域顺序上传，请留意结果")

            # ── 依次上传三个 zip（严格按 Meta → Material → Skill 顺序）──
            for idx, file_path in enumerate(files_in_order):
                trigger = triggers.nth(idx)
                with page.expect_file_chooser(timeout=10000) as fc_info:
                    trigger.click()
                file_chooser = fc_info.value
                file_chooser.set_files(str(file_path))
                log(f"已上传第 {idx+1}/3 个文件（{FIELD_LABELS_IN_ORDER[idx]}）：{file_path.name}")
                page.wait_for_timeout(800)

            # 给异步上传留出缓冲时间（问卷侧文件较小，通常秒级完成）
            page.wait_for_timeout(2000)

            pre_submit_shot = output_dir / f"wenjuan-filled-{ts}.png"
            page.screenshot(path=str(pre_submit_shot), full_page=True)

            # ── 点击提交 ──
            submit_btn = page.get_by_role("button", name=SUBMIT_BUTTON_TEXT)
            submit_btn.click(timeout=10000)

            # ── 结果判定：成功 / 意外出现验证环节 / 失败 ──
            try:
                page.get_by_text(SUCCESS_TEXT).wait_for(timeout=15000)
                page.wait_for_timeout(800)  # 等待转场动画/图标绘制完成，避免截图为过渡态空白帧
                shot = output_dir / f"wenjuan-success-{ts}.png"
                page.screenshot(path=str(shot), full_page=True)
                return {
                    "status": "success",
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                    "screenshot": str(shot),
                    "meta_zip": str(meta_zip),
                    "material_zip": str(material_zip),
                    "skill_zip": str(skill_zip),
                }
            except PWTimeoutError:
                page_text = page.inner_text("body")
                shot = output_dir / f"wenjuan-blocked-{ts}.png"
                page.screenshot(path=str(shot), full_page=True)
                if any(kw in page_text for kw in ["验证码", "手机号验证", "请输入手机号"]):
                    return {
                        "status": "manual_required",
                        "reason": "提交时触发了手机号/验证码校验环节，需人工手动完成验证后再提交。",
                        "screenshot": str(shot),
                    }
                return {
                    "status": "failed",
                    "error": "点击提交后未出现「问卷到此结束」确认文案，可能提交失败或页面结构有变化。",
                    "screenshot": str(shot),
                }
        except Exception as e:  # noqa: BLE001 — 顶层兜底，保证任何异常都留证据不裸抛
            shot = output_dir / f"wenjuan-error-{ts}.png"
            try:
                page.screenshot(path=str(shot), full_page=True)
            except Exception:
                shot = None
            return {
                "status": "failed",
                "error": f"{type(e).__name__}: {e}",
                "screenshot": str(shot) if shot else None,
            }
        finally:
            browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="自动填写并提交 SkillHub MCP Backup 腾讯问卷")
    parser.add_argument("--skill-zip", required=True, type=Path, help="技能包 zip 路径（已由 pack_and_hash.sh 生成）")
    parser.add_argument("--material-zip", required=True, type=Path, help="材料包 zip 路径（已由 pack_and_hash.sh 生成）")
    parser.add_argument("--meta-json", required=True, type=Path, help="meta.json 路径（本脚本会打包为 zip 后上传）")
    parser.add_argument("--url", default=DEFAULT_URL, help="腾讯问卷地址")
    parser.add_argument("--output-dir", default=Path.home() / ".workbuddy" / "skillhub-outputs" / "wenjuan", type=Path)
    parser.add_argument("--headless", dest="headless", action="store_true", default=True)
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    args = parser.parse_args()

    try:
        validate_file(args.skill_zip, "Skill")
        validate_file(args.material_zip, "Material")
        meta_zip = zip_meta_json(args.meta_json, args.output_dir)
        validate_file(meta_zip, "Meta")
    except (FileNotFoundError, ValueError) as e:
        print(json.dumps({"status": "failed", "error": str(e)}, ensure_ascii=False))
        return 1

    result = run_submission(
        skill_zip=args.skill_zip,
        material_zip=args.material_zip,
        meta_zip=meta_zip,
        url=args.url,
        output_dir=args.output_dir,
        headless=args.headless,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
